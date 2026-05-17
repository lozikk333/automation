"""
Website Management Models and Utilities

Handles both WordPress and HTML static website creation, registration,
and publishing configuration.
"""

import secrets
import re
import hashlib
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime


class SiteType(str, Enum):
    """Supported website types"""
    WORDPRESS = "wordpress"
    HTML_STATIC = "html_static"


class PublishMethod(str, Enum):
    """Publishing methods for each site type"""
    WORDPRESS_REST = "wordpress_rest"
    HTML_STATIC_API = "html_static_api"
    HTML_LOCAL = "html_local"


@dataclass
class WebsiteCredentials:
    """Website credentials - different for each type"""
    site_type: SiteType
    
    # WordPress credentials
    wp_username: Optional[str] = None
    wp_app_password: Optional[str] = None
    
    # HTML static credentials
    api_key: Optional[str] = None
    api_key_hash: Optional[str] = None
    publish_endpoint: Optional[str] = None
    api_enabled: bool = False
    
    # Local path (for generated sites)
    local_path: Optional[str] = None


@dataclass
class WebsiteRegistration:
    """Website registration payload for database"""
    id: Optional[int] = None
    name: str = ""
    base_url: str = ""
    site_type: SiteType = SiteType.WORDPRESS
    publish_method: PublishMethod = PublishMethod.WORDPRESS_REST
    status: str = "active"
    
    # WordPress
    username: Optional[str] = None
    password: Optional[str] = None
    
    # HTML Static
    publish_endpoint: Optional[str] = None
    api_key_hash: Optional[str] = None
    api_enabled: bool = False
    
    # Metadata
    local_path: Optional[str] = None
    categories_json: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class TokenManager:
    """Secure token generation and hashing"""
    
    @staticmethod
    def generate_api_key(length: int = 32) -> str:
        """Generate a secure random API key"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def hash_token(token: str) -> str:
        """Hash a token using SHA-256"""
        return hashlib.sha256(str(token or "").encode("utf-8")).hexdigest()
    
    @staticmethod
    def verify_token(provided_token: str, stored_hash: str) -> bool:
        """Verify token matches hash using constant-time comparison"""
        if not provided_token or not stored_hash:
            return False
        token_hash = TokenManager.hash_token(provided_token)
        return secrets.compare_digest(token_hash, stored_hash)


class WebsiteValidator:
    """Validate website configurations"""
    
    @staticmethod
    def validate_url(url: str) -> tuple[bool, Optional[str]]:
        """Validate URL format"""
        if not url or not isinstance(url, str):
            return False, "URL is required"
        
        url = url.strip()
        if not url.startswith("http://") and not url.startswith("https://"):
            return False, "URL must start with http:// or https://"
        
        # Basic URL validation
        try:
            import urllib.parse
            parsed = urllib.parse.urlparse(url)
            if not parsed.netloc:
                return False, "Invalid URL format"
        except Exception:
            return False, "Invalid URL format"
        
        return True, None
    
    @staticmethod
    def validate_wordpress_credentials(username: str, password: str) -> tuple[bool, Optional[str]]:
        """Validate WordPress credentials"""
        if not username or not isinstance(username, str):
            return False, "WordPress username is required"
        if not password or not isinstance(password, str):
            return False, "WordPress app password is required"
        
        if len(username) < 3:
            return False, "Username too short"
        if len(password) < 10:
            return False, "App password too short"
        
        return True, None
    
    @staticmethod
    def validate_site_config(config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate complete site configuration"""
        site_type = config.get("site_type", "").lower()
        
        try:
            site_type = SiteType(site_type)
        except ValueError:
            return False, f"Invalid site type: {site_type}"
        
        name = config.get("name", "").strip()
        if not name:
            return False, "Site name is required"
        
        base_url = config.get("base_url", "").strip()
        valid_url, url_error = WebsiteValidator.validate_url(base_url)
        if not valid_url:
            return False, url_error
        
        if site_type == SiteType.WORDPRESS:
            username = config.get("username", "").strip()
            password = config.get("password", "").strip()
            valid, error = WebsiteValidator.validate_wordpress_credentials(username, password)
            if not valid:
                return False, error
        
        return True, None


class WebsiteFactory:
    """Factory for creating website registrations"""
    
    @staticmethod
    def create_wordpress_site(
        name: str,
        base_url: str,
        username: str,
        password: str,
    ) -> WebsiteRegistration:
        """Create a WordPress website registration"""
        return WebsiteRegistration(
            name=name,
            base_url=base_url.rstrip("/"),
            site_type=SiteType.WORDPRESS,
            publish_method=PublishMethod.WORDPRESS_REST,
            status="active",
            username=username,
            password=password,
            api_enabled=False,
        )
    
    @staticmethod
    def create_html_static_site(
        name: str,
        base_url: str,
        api_key: Optional[str] = None,
        publish_endpoint: Optional[str] = None,
        local_path: Optional[str] = None,
    ) -> tuple[WebsiteRegistration, str]:
        """
        Create an HTML static website registration
        
        Returns:
            (registration, api_key) tuple
        """
        api_key = api_key or TokenManager.generate_api_key()
        api_key_hash = TokenManager.hash_token(api_key)
        
        if not publish_endpoint:
            publish_endpoint = f"{base_url.rstrip('/')}/internal-api/publish"
        
        return (
            WebsiteRegistration(
                name=name,
                base_url=base_url.rstrip("/"),
                site_type=SiteType.HTML_STATIC,
                publish_method=PublishMethod.HTML_STATIC_API,
                status="active",
                username="",
                password=api_key,  # Store API key in password field for backward compatibility
                publish_endpoint=publish_endpoint.rstrip("/"),
                api_key_hash=api_key_hash,
                api_enabled=True,
                local_path=local_path,
            ),
            api_key,
        )


class WebsiteBuilder:
    """Handle HTML static website generation and publishing API setup"""
    
    def __init__(self, site_root: Path):
        self.site_root = Path(site_root)
        self.api_dir = self.site_root / "internal-api" / "publish"
    
    def setup_publishing_api(self, api_key_hash: str) -> Path:
        """
        Set up the internal publishing API for this static site
        
        Returns:
            Path to the created API index.php
        """
        # Ensure directory exists
        self.api_dir.mkdir(parents=True, exist_ok=True)
        
        # Read template
        template_path = Path(__file__).resolve().parent.parent / "templates" / "internal-api-publish.php"
        if not template_path.exists():
            raise FileNotFoundError(f"API template not found: {template_path}")
        
        api_content = template_path.read_text(encoding="utf-8")
        
        # Replace placeholder with actual hash
        api_content = api_content.replace(
            "const AUTOMATION_API_KEY_HASH = '{{ API_KEY_HASH }}';",
            f"const AUTOMATION_API_KEY_HASH = '{api_key_hash}';"
        )
        
        # Write API file
        api_file = self.api_dir / "index.php"
        api_file.write_text(api_content, encoding="utf-8")
        
        # Make it readable by web server
        api_file.chmod(0o644)
        
        return api_file
    
    def verify_api_setup(self) -> bool:
        """Verify that the API endpoint is properly set up"""
        api_file = self.api_dir / "index.php"
        if not api_file.exists():
            return False
        
        content = api_file.read_text(encoding="utf-8")
        return "AUTOMATION_API_KEY_HASH" in content and "<?php" in content


class PublishingManager:
    """Manage article publishing to different site types"""
    
    @staticmethod
    def get_publisher_for_site(site: Dict[str, Any]):
        """Get the appropriate publisher for a site"""
        site_type = site.get("site_type", "wordpress")
        
        if site_type == SiteType.HTML_STATIC or site_type == "html_static":
            # Return HTML static publisher configuration
            return {
                "type": "html_static",
                "endpoint": site.get("publish_endpoint"),
                "api_key": site.get("password"),  # API key stored in password field
                "local_path": site.get("local_path"),
            }
        else:
            # Return WordPress publisher configuration
            return {
                "type": "wordpress",
                "base_url": site.get("base_url"),
                "username": site.get("username"),
                "password": site.get("password"),
            }


# Export public API
__all__ = [
    "SiteType",
    "PublishMethod",
    "WebsiteCredentials",
    "WebsiteRegistration",
    "TokenManager",
    "WebsiteValidator",
    "WebsiteFactory",
    "WebsiteBuilder",
    "PublishingManager",
]
