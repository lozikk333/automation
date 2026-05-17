"""
Enhanced Website Management Endpoints

Handles creation and management of both WordPress and HTML static websites
with automatic API generation, registration, and publishing configuration.

Integration Points:
1. Website creation with site type selection
2. Automatic API key generation and storage
3. Publishing method routing (WordPress REST or HTML Static API)
4. Website registration in database with secure credentials
5. API key regeneration and testing
6. Category syncing for WordPress sites
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
from zoneinfo import ZoneInfo
import secrets
import re

# Import website management utilities
from services.website_manager import (
    SiteType,
    PublishMethod,
    TokenManager,
    WebsiteValidator,
    WebsiteFactory,
    WebsiteBuilder,
    PublishingManager,
)

APP_TIMEZONE = ZoneInfo("Africa/Casablanca")


# ==========================================================================
# REQUEST MODELS
# ==========================================================================

class WebsiteCreate(BaseModel):
    """Create a new website"""
    name: str = Field(..., description="Website name")
    base_url: str = Field(..., description="Website base URL")
    site_type: Optional[str] = Field(
        default="wordpress",
        description="Site type: wordpress or html_static"
    )
    
    # WordPress credentials
    username: Optional[str] = Field(
        default=None,
        description="WordPress username or email (for WordPress sites)"
    )
    password: Optional[str] = Field(
        default=None,
        description="WordPress application password (for WordPress sites)"
    )
    
    # HTML static credentials
    publish_endpoint: Optional[str] = Field(
        default=None,
        description="Publishing endpoint URL (for HTML static sites, auto-generated if not provided)"
    )
    api_key: Optional[str] = Field(
        default=None,
        description="API key (for HTML static sites, auto-generated if not provided)"
    )
    api_enabled: Optional[bool] = Field(
        default=True,
        description="Enable publishing API (for HTML static sites)"
    )
    
    # Metadata
    pin_template: Optional[str] = Field(
        default="u1_u2_white_band",
        description="Pinterest pin template ID"
    )
    publish_status: Optional[str] = Field(
        default="draft",
        description="Default publish status: draft or publish"
    )


class WebsiteUpdate(BaseModel):
    """Update website configuration"""
    name: Optional[str] = None
    base_url: Optional[str] = None
    site_type: Optional[str] = None
    
    # WordPress
    username: Optional[str] = None
    password: Optional[str] = None
    
    # HTML static
    publish_endpoint: Optional[str] = None
    api_key: Optional[str] = None
    api_enabled: Optional[bool] = None
    
    # Metadata
    pin_template: Optional[str] = None
    publish_status: Optional[str] = None


# ==========================================================================
# HELPER FUNCTIONS
# ==========================================================================

def _site_type(value: str) -> str:
    """Normalize and validate site type"""
    site_type = (value or "wordpress").strip().lower()
    if site_type not in ("wordpress", "html_static"):
        return "wordpress"
    return site_type


def _publish_method(site_type: str) -> str:
    """Get publishing method for site type"""
    site_type = _site_type(site_type)
    if site_type == "html_static":
        return "html_static_api"
    return "wordpress_rest"


def _website_by_base_url(base_url: str, exclude_id: Optional[int] = None) -> Optional[Dict]:
    """Find website by normalized base URL"""
    normalized = base_url.rstrip("/").lower()
    query = """
        SELECT * FROM websites 
        WHERE lower(rtrim(base_url, '/')) = ?
    """
    params = (normalized,)
    
    if exclude_id:
        query += " AND id != ?"
        params = (normalized, exclude_id)
    
    return state.conn.execute(query, params).fetchone()


def _sync_wordpress_categories(row: Dict) -> tuple[List[Dict], str]:
    """Sync categories from WordPress"""
    if not row or row.get("site_type") == "html_static":
        # Return empty categories for HTML static sites
        return [], datetime.now(APP_TIMEZONE).isoformat(timespec="seconds")
    
    try:
        wp = WordPressPublisher(
            row["base_url"],
            row["username"],
            row["password"]
        )
        categories = wp.get_categories()
        categories_json = json.dumps(categories)
        synced_at = datetime.now(APP_TIMEZONE).isoformat(timespec="seconds")
        
        state.conn.execute(
            "UPDATE websites SET categories_json = ?, categories_synced_at = ? WHERE id = ?",
            (categories_json, synced_at, row["id"])
        )
        state.conn.commit()
        
        return categories, synced_at
    except Exception as e:
        raise Exception(f"Failed to sync WordPress categories: {str(e)}")


def _website_categories(row: Dict) -> List[Dict]:
    """Get website categories"""
    if not row:
        return []
    
    categories_json = row.get("categories_json")
    if not categories_json:
        return []
    
    try:
        return json.loads(categories_json)
    except:
        return []


def _public_website(row: Dict) -> Dict:
    """Convert database row to public website object"""
    return {
        "id": row["id"],
        "name": row["name"],
        "base_url": row["base_url"],
        "site_type": row.get("site_type", "wordpress"),
        "publish_method": row.get("publish_method", "wordpress_rest"),
        "status": row.get("status", "active"),
        "api_enabled": bool(row.get("api_enabled", 0)) if row.get("site_type") == "html_static" else False,
        "publish_endpoint": row.get("publish_endpoint") if row.get("site_type") == "html_static" else None,
        "last_publish_at": row.get("last_publish_at"),
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
    }


async def _create_wordpress_website(state: StateManager, body: WebsiteCreate) -> Dict:
    """Create and register a WordPress website"""
    # Validate credentials
    valid, error = WebsiteValidator.validate_wordpress_credentials(
        body.username or "",
        body.password or ""
    )
    if not valid:
        raise HTTPException(status_code=400, detail=error)
    
    # Test connection
    try:
        auth_result = _check_wordpress_upload_auth({
            "base_url": body.base_url,
            "username": body.username,
            "password": body.password,
        })
        if not auth_result.get("ok"):
            raise HTTPException(
                status_code=401,
                detail=auth_result.get("message", "WordPress authentication failed")
            )
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
    
    # Create registration
    registration = WebsiteFactory.create_wordpress_site(
        name=body.name,
        base_url=body.base_url,
        username=body.username or "",
        password=body.password or "",
    )
    
    # Check for duplicates
    existing = _website_by_base_url(body.base_url)
    if existing:
        # Update existing
        state.conn.execute(
            """
            UPDATE websites
            SET name = ?, status = 'active', username = ?, password = ?, 
                pin_template = ?, publish_status = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                body.name, body.username, body.password,
                body.pin_template or "u1_u2_white_band",
                body.publish_status or "draft",
                datetime.now(APP_TIMEZONE).isoformat(timespec="seconds"),
                existing["id"],
            ),
        )
        state.conn.commit()
        row = state.conn.execute("SELECT * FROM websites WHERE id = ?", (existing["id"],)).fetchone()
    else:
        # Create new
        cursor = state.conn.execute(
            """
            INSERT INTO websites
                (name, base_url, site_type, publish_method, status, username, password,
                 pin_template, publish_status, updated_at)
            VALUES (?, ?, ?, ?, 'active', ?, ?, ?, ?, ?)
            """,
            (
                body.name,
                registration.base_url,
                "wordpress",
                "wordpress_rest",
                body.username,
                body.password,
                body.pin_template or "u1_u2_white_band",
                body.publish_status or "draft",
                datetime.now(APP_TIMEZONE).isoformat(timespec="seconds"),
            ),
        )
        state.conn.commit()
        row = state.conn.execute(
            "SELECT * FROM websites WHERE id = ?",
            (cursor.lastrowid,)
        ).fetchone()
    
    # Sync categories
    categories = []
    try:
        categories, _ = _sync_wordpress_categories(row)
        state.log_dashboard(
            None, "info", "websites",
            f"Created WordPress site '{body.name}' and synced {len(categories)} categories"
        )
    except Exception as e:
        state.log_dashboard(
            None, "warn", "websites",
            f"Created WordPress site '{body.name}' but category sync failed: {e}"
        )
    
    return {
        **_public_website(row),
        "categories": categories,
        "category_count": len(categories),
    }


async def _create_html_static_website(state: StateManager, body: WebsiteCreate) -> tuple[Dict, str]:
    """Create and register an HTML static website"""
    # Generate API key if not provided
    api_key = body.api_key or TokenManager.generate_api_key()
    api_key_hash = TokenManager.hash_token(api_key)
    
    # Set default publish endpoint
    publish_endpoint = body.publish_endpoint or f"{body.base_url.rstrip('/')}/internal-api/publish"
    
    # Create registration
    registration, generated_key = WebsiteFactory.create_html_static_site(
        name=body.name,
        base_url=body.base_url,
        api_key=api_key,
        publish_endpoint=publish_endpoint,
    )
    
    # Check for duplicates
    existing = _website_by_base_url(body.base_url)
    if existing:
        # Update existing
        state.conn.execute(
            """
            UPDATE websites
            SET name = ?, site_type = 'html_static', publish_method = 'html_static_api',
                status = 'active', username = '', password = ?, publish_endpoint = ?,
                api_key_hash = ?, api_enabled = ?, pin_template = ?, publish_status = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                body.name,
                api_key,
                registration.publish_endpoint,
                api_key_hash,
                1 if (body.api_enabled is not False) else 0,
                body.pin_template or "u1_u2_white_band",
                body.publish_status or "draft",
                datetime.now(APP_TIMEZONE).isoformat(timespec="seconds"),
                existing["id"],
            ),
        )
        state.conn.commit()
        row = state.conn.execute("SELECT * FROM websites WHERE id = ?", (existing["id"],)).fetchone()
        state.log_dashboard(
            None, "info", "websites",
            f"Updated HTML static site '{body.name}' with new API configuration"
        )
    else:
        # Create new
        cursor = state.conn.execute(
            """
            INSERT INTO websites
                (name, base_url, site_type, publish_method, status, username, password,
                 publish_endpoint, api_key_hash, api_enabled, pin_template,
                 publish_status, updated_at)
            VALUES (?, ?, 'html_static', 'html_static_api', 'active', '', ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                body.name,
                body.base_url.rstrip("/"),
                api_key,
                registration.publish_endpoint,
                api_key_hash,
                1 if (body.api_enabled is not False) else 0,
                body.pin_template or "u1_u2_white_band",
                body.publish_status or "draft",
                datetime.now(APP_TIMEZONE).isoformat(timespec="seconds"),
            ),
        )
        state.conn.commit()
        row = state.conn.execute(
            "SELECT * FROM websites WHERE id = ?",
            (cursor.lastrowid,)
        ).fetchone()
        state.log_dashboard(
            None, "info", "websites",
            f"Created HTML static site '{body.name}' with publishing API"
        )
    
    return _public_website(row), api_key


# ==========================================================================
# ENHANCED ENDPOINTS
# ==========================================================================

async def create_website_enhanced(state: StateManager, body: WebsiteCreate) -> Dict:
    """
    Create a new website (WordPress or HTML Static)
    
    Returns:
        - For WordPress: website object with synced categories
        - For HTML Static: website object + api_key for configuration
    """
    # Validate inputs
    if not body.name.strip():
        raise HTTPException(status_code=400, detail="name is required")
    
    valid, error = WebsiteValidator.validate_url(body.base_url)
    if not valid:
        raise HTTPException(status_code=400, detail=error)
    
    site_type = _site_type(body.site_type or "wordpress")
    
    if site_type == "wordpress":
        return await _create_wordpress_website(state, body)
    else:
        website, api_key = await _create_html_static_website(state, body)
        return {
            **website,
            "api_key": api_key,
            "categories": [],
            "category_count": 0,
        }


# ==========================================================================
# MODELS FOR FRONTEND
# ==========================================================================

class WebsiteTypeOption(BaseModel):
    """Website type option for frontend selector"""
    value: str = Field(..., description="Value: wordpress or html_static")
    label: str = Field(..., description="Display label")
    description: str = Field(..., description="Help text")
    icon: str = Field(..., description="Icon name")
    fields: List[Dict[str, Any]] = Field(..., description="Dynamic form fields")


def get_website_type_options() -> List[WebsiteTypeOption]:
    """Get website type options for the Add Website modal"""
    return [
        WebsiteTypeOption(
            value="wordpress",
            label="WordPress",
            description="Publish to existing WordPress blog",
            icon="wordpress",
            fields=[
                {
                    "name": "username",
                    "label": "WordPress Username or Email",
                    "type": "text",
                    "required": True,
                    "placeholder": "admin@example.com or admin_user",
                    "help": "WordPress user account with upload permissions",
                },
                {
                    "name": "password",
                    "label": "Application Password",
                    "type": "password",
                    "required": True,
                    "placeholder": "xxxx xxxx xxxx xxxx xxxx xxxx",
                    "help": "Generate at WordPress Settings → Apps Passwords",
                },
            ],
        ),
        WebsiteTypeOption(
            value="html_static",
            label="HTML Static Site",
            description="Publish to static HTML website with secure API",
            icon="globe",
            fields=[
                {
                    "name": "publish_endpoint",
                    "label": "Publish Endpoint (optional)",
                    "type": "text",
                    "required": False,
                    "placeholder": "https://example.com/internal-api/publish",
                    "help": "Auto-generated if left empty",
                },
                {
                    "name": "api_key",
                    "label": "API Key (optional)",
                    "type": "password",
                    "required": False,
                    "placeholder": "Auto-generated if left empty",
                    "help": "Secure token for publishing requests",
                },
                {
                    "name": "api_enabled",
                    "label": "Enable Publishing API",
                    "type": "checkbox",
                    "required": False,
                    "default": True,
                    "help": "Allow automated publishing to this site",
                },
            ],
        ),
    ]


# Export all enhanced functions
__all__ = [
    "WebsiteCreate",
    "WebsiteUpdate",
    "WebsiteTypeOption",
    "create_website_enhanced",
    "get_website_type_options",
    "_site_type",
    "_publish_method",
    "_website_by_base_url",
    "_sync_wordpress_categories",
    "_website_categories",
    "_public_website",
    "_create_wordpress_website",
    "_create_html_static_website",
]
