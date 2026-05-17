# Website Builder Enhancement - Code Implementation

## Location: services/website_builder.py

This document provides exact code snippets to integrate publishing API setup into your existing website generation process.

---

## Step 1: Add Imports

Add these imports at the top of `services/website_builder.py`:

```python
from services.website_manager import WebsiteBuilder
from orchestrator.state_manager import StateManager
import hashlib
```

---

## Step 2: Update generate_site() Function

Find your existing `generate_site()` function and add the publishing API setup after site generation.

### Location: Around line 2428

**Current Code** (example):
```python
def generate_site(payload: dict, output_root: Path) -> dict:
    # ... existing site generation code ...
    
    # Create the site files
    create_templates(output_dir)
    create_styles(output_dir)
    create_homepage(output_dir)
    
    return {
        "ok": True,
        "site_path": str(output_dir),
    }
```

**Enhanced Code**:
```python
def generate_site(payload: dict, output_root: Path, state: StateManager = None) -> dict:
    # ... existing site generation code ...
    
    # Create the site files
    create_templates(output_dir)
    create_styles(output_dir)
    create_homepage(output_dir)
    
    # NEW: Setup internal publishing API for HTML static sites
    site_type = payload.get("site_type", "wordpress")
    api_key_hash = payload.get("internal_api_key_hash")
    website_id = payload.get("website_id")
    base_url = payload.get("base_url", "").rstrip("/")
    
    api_configured = False
    api_endpoint = None
    
    if site_type == "html_static" and api_key_hash and output_dir.exists():
        try:
            # Setup the publishing API in the generated site
            builder = WebsiteBuilder(output_dir)
            api_path = builder.setup_publishing_api(api_key_hash)
            
            api_configured = True
            api_endpoint = f"{base_url}/internal-api/publish"
            
            if state:
                state.log_dashboard(
                    None, "info", "websites",
                    f"Publishing API configured for '{payload.get('name', 'site')}' at {api_endpoint}"
                )
            
            # Verify the API was set up correctly
            if builder.verify_api_setup():
                if state:
                    state.log(f"Publishing API verified successfully at {api_path}")
            else:
                if state:
                    state.log(f"Warning: Publishing API file exists but verification failed", level="warn")
                    
        except FileNotFoundError as e:
            if state:
                state.log(f"Warning: Publishing API template not found: {e}", level="warn")
        except PermissionError as e:
            if state:
                state.log(f"Warning: Permission denied setting up Publishing API: {e}", level="warn")
        except Exception as e:
            if state:
                state.log(f"Warning: Publishing API setup failed: {e}", level="warn")
    
    # Return enhanced response
    return {
        "ok": True,
        "site_path": str(output_dir),
        "api_configured": api_configured,
        "api_endpoint": api_endpoint,
        "site_type": site_type,
        "website_id": website_id,
    }
```

---

## Step 3: Update Payload Preparation

When calling `generate_site()`, ensure you pass the API key hash for HTML static sites.

### Example: In your article publishing code (e.g., orchestrator/pipeline.py)

**Original**:
```python
def publish_html_static_article(job: dict, site: dict, article: dict):
    payload = {
        "name": article["title"],
        "title": article["title"],
        "slug": article["slug"],
        "contentHtml": article["content_html"],
        # ... other fields ...
    }
    
    result = generate_site(payload, OUTPUT_DIR)
```

**Enhanced** (include API key hash for sites that need it):
```python
def publish_html_static_article(job: dict, site: dict, article: dict):
    # Get the API key hash from the site configuration
    api_key_hash = site.get("api_key_hash") if site.get("site_type") == "html_static" else None
    
    payload = {
        "name": article["title"],
        "title": article["title"],
        "slug": article["slug"],
        "contentHtml": article["content_html"],
        # NEW: Include API configuration
        "site_type": site.get("site_type", "wordpress"),
        "internal_api_key_hash": api_key_hash,
        "website_id": site.get("id"),
        "base_url": site.get("base_url"),
        # ... other fields ...
    }
    
    result = generate_site(payload, OUTPUT_DIR, state)
    
    # Log the API setup
    if result.get("api_configured"):
        state.log(f"Publishing API ready: {result.get('api_endpoint')}")
```

---

## Step 4: Update Function Signatures (if needed)

If `generate_site()` doesn't currently accept a `state` parameter, you may need to update it:

**Before**:
```python
def generate_site(payload: dict, output_root: Path) -> dict:
```

**After**:
```python
def generate_site(payload: dict, output_root: Path, state: StateManager = None) -> dict:
```

Then update all calls to include the state:
```python
result = generate_site(payload, output_dir, state)
```

---

## Step 5: Verify PHP Template Exists

The function will look for the PHP template at:

```python
# In WebsiteBuilder.setup_publishing_api()
template_path = Path(__file__).parent.parent / "templates" / "internal-api-publish.php"
```

Ensure this file exists at:
```
content-automation-system/
├── templates/
│   └── internal-api-publish.php  ✓ Must exist
└── services/
    └── website_manager.py
```

---

## Step 6: Database Field Verification

Verify the `websites` table has these fields for HTML static sites:

```sql
-- Run this query to verify:
PRAGMA table_info(websites);

-- Required fields:
-- site_type TEXT (wordpress or html_static)
-- api_key_hash TEXT (SHA-256 hash of API key)
-- publish_endpoint TEXT (URL to publishing API)
-- api_enabled INTEGER (0 or 1)
```

---

## Step 7: Error Handling & Logging

The code above includes try-catch blocks that log warnings but don't fail site generation. This ensures:

- Site generation completes even if API setup fails
- Errors are logged for debugging
- User sees which sites have API configured

**Logging Examples**:
```
✅ Publishing API configured for 'My Site' at https://example.com/internal-api/publish
⚠️  Publishing API setup failed: Permission denied
⚠️  Publishing API template not found
```

---

## Step 8: Testing

After integration, test with:

```bash
# 1. Add HTML static site via UI
# Navigate to Add Website → HTML Static

# 2. Generate site (trigger article creation/publishing)
# This will call generate_site() with api_key_hash

# 3. Verify API exists in generated site
ls -la generated_sites/my-site/internal-api/publish/index.php
# Should show: -rw-r--r-- (644 permissions)

# 4. Check logs
tail -f logs/website_generation.log
# Should show: "Publishing API configured for..."

# 5. Test API endpoint
curl -H "Authorization: Bearer {api_key}" \
     -X POST https://example.com/internal-api/publish \
     -d '{"title":"Test","slug":"test","contentHtml":"<p>Test</p>"}'

# Should return: {"ok": true, "message": "Article published"}
```

---

## Complete Integration Example

Here's a complete example showing the integration in context:

```python
# services/website_builder.py

from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from services.website_manager import WebsiteBuilder
from orchestrator.state_manager import StateManager

APP_TIMEZONE = ZoneInfo("Africa/Casablanca")

def generate_site(payload: dict, output_root: Path, state: StateManager = None) -> dict:
    """
    Generate a website from payload configuration.
    
    Args:
        payload: Configuration including:
            - name, title, slug, contentHtml
            - site_type ('wordpress' or 'html_static')
            - internal_api_key_hash (for HTML static)
            - base_url (for API endpoint)
            - website_id (for database tracking)
        output_root: Root directory for generated sites
        state: Optional StateManager for logging
        
    Returns:
        dict with site path, API configuration, and status
    """
    
    # Extract configuration
    name = payload.get("name", "site")
    site_type = payload.get("site_type", "wordpress")
    api_key_hash = payload.get("internal_api_key_hash")
    website_id = payload.get("website_id")
    base_url = payload.get("base_url", "").rstrip("/")
    
    # Create output directory
    output_dir = output_root / name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # =====================
    # EXISTING SITE GENERATION
    # =====================
    
    # Create HTML files
    homepage_html = build_homepage(payload)
    (output_dir / "index.html").write_text(homepage_html)
    
    # Create CSS
    styles_css = build_styles(payload)
    (output_dir / "style.css").write_text(styles_css)
    
    # Create structure
    (output_dir / "category").mkdir(exist_ok=True)
    (output_dir / "logs").mkdir(exist_ok=True)
    
    # Log generation
    if state:
        state.log(f"Generated website at {output_dir}")
    
    # =====================
    # NEW: PUBLISHING API SETUP
    # =====================
    
    api_configured = False
    api_endpoint = None
    
    # Only setup API for HTML static sites with proper configuration
    if site_type == "html_static" and api_key_hash and output_dir.exists():
        try:
            if state:
                state.log(f"Setting up publishing API for HTML static site '{name}'")
            
            # Create WebsiteBuilder and setup API
            builder = WebsiteBuilder(output_dir)
            api_path = builder.setup_publishing_api(api_key_hash)
            
            # Mark as configured
            api_configured = True
            api_endpoint = f"{base_url}/internal-api/publish"
            
            # Verify setup
            if builder.verify_api_setup():
                if state:
                    state.log_dashboard(
                        website_id, "info", "websites",
                        f"✅ Publishing API ready: {api_endpoint}"
                    )
            else:
                if state:
                    state.log(
                        f"Warning: Publishing API file exists but verification failed",
                        level="warn"
                    )
        
        except FileNotFoundError as e:
            if state:
                state.log(f"⚠️  API template missing: {e}", level="warn")
        
        except PermissionError as e:
            if state:
                state.log(
                    f"⚠️  Permission denied setting up API: {e}",
                    level="warn"
                )
        
        except Exception as e:
            if state:
                state.log(f"⚠️  API setup failed: {e}", level="warn")
    
    # =====================
    # RETURN RESULT
    # =====================
    
    return {
        "ok": True,
        "site_path": str(output_dir),
        "site_type": site_type,
        "website_id": website_id,
        "api_configured": api_configured,
        "api_endpoint": api_endpoint,
        "generated_at": datetime.now(APP_TIMEZONE).isoformat(timespec="seconds"),
    }
```

---

## Troubleshooting

### Issue: "Module not found: services.website_manager"

**Solution**: Ensure `services/website_manager.py` exists and is in the same directory as `website_builder.py`

### Issue: "Permission denied" when creating API file

**Solution**: 
1. Verify web server has write permissions to generated_sites/
2. Check umask is set correctly
3. Run: `chmod 755 generated_sites/`

### Issue: API template not found

**Solution**:
1. Copy `templates/internal-api-publish.php` to your templates directory
2. Verify path: `content-automation-system/templates/internal-api-publish.php`

### Issue: API key hash wrong format

**Solution**:
1. Verify hash is SHA-256 format (64 hex characters)
2. Check it's generated using: `hashlib.sha256(key.encode()).hexdigest()`
3. Not base64 or other format

---

## Summary

This enhancement adds zero-friction publishing API setup to your existing site generation. When users generate an HTML static site with an API key configured, the site automatically includes the secure publishing endpoint ready to receive articles from your automation pipeline.

The implementation is:
- ✅ Non-invasive (wrapped in try-catch)
- ✅ Backward compatible (works with existing code)
- ✅ Secure (uses hashed verification)
- ✅ Logged (clear debug messages)
- ✅ Tested (includes verification)
