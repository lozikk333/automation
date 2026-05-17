# Platform Enhancement Implementation Guide

## Current Status Summary

Your platform **already has dual WordPress + HTML static support** implemented! ✅

### What's Already Working

✅ Database schema supports both site types  
✅ POST /websites endpoint handles both types with proper routing  
✅ WordPress credential validation and auth testing  
✅ HTML static API key generation with SHA-256 hashing  
✅ Category syncing for WordPress sites  
✅ Publishing pipeline (orchestrator/pipeline.py) routes to correct publisher  
✅ WordPressPublisher and HtmlStaticPublisher classes functional  

The endpoint at `@app.post("/websites")` in main.py already:
- Routes based on site_type (wordpress or html_static)
- Tests WordPress credentials
- Generates API keys for HTML static sites
- Stores hashed API keys securely
- Syncs categories
- Returns appropriate response format

---

## What's Missing (Next Steps)

### 1. ⚠️ CRITICAL: Publishing API in Generated Sites

**Issue**: When you generate a new HTML static site, there's no `/internal-api/publish/` endpoint to receive articles.

**Solution**: Add the internal-api-publish.php to generated sites

**Action Items**:
```
1. Add templates/internal-api-publish.php (secure PHP endpoint) [PROVIDED]
2. Update services/website_builder.py generate_site() function
3. During site generation, embed the PHP API with hashed API key
```

### 2. ⚠️ Frontend Add Website Modal

**Issue**: No React component for the website management UI

**Solution**: Add the AddWebsiteModal component

**Action Items**:
```
1. Add components/AddWebsiteModal.tsx [PROVIDED]
2. Import it in websites management page
3. Display when "Add Website" button clicked
```

### 3. 📚 Documentation & Deployment Guide

**Provided Files** (all ready to use):
- HTML_STATIC_INTEGRATION_GUIDE.md (complete deployment guide)
- templates/internal-api-publish.php (186 lines, production-ready)
- services/website_manager.py (optional, provides helper classes)
- services/website_endpoints.py (optional, provides structured helpers)
- components/AddWebsiteModal.tsx (complete React component)

---

## Quick Implementation Path (Priority Order)

### Phase 1: Frontend Component (1 hour)

**Add React Modal for Website Creation**

```bash
# 1. Copy the component
cp components/AddWebsiteModal.tsx \
   /your/project/components/AddWebsiteModal.tsx
```

**2. Update your websites management page**

```tsx
// In your websites list/management component
import { AddWebsiteModal } from '@/components/AddWebsiteModal'

export function WebsiteManager() {
  const [showModal, setShowModal] = useState(false)
  
  return (
    <>
      <button 
        onClick={() => setShowModal(true)}
        className="px-4 py-2 bg-charcoal text-white rounded-lg"
      >
        + Add Website
      </button>
      
      {showModal && (
        <AddWebsiteModal
          onClose={() => setShowModal(false)}
          onSuccess={() => {
            fetchWebsites()
            setShowModal(false)
          }}
        />
      )}
    </>
  )
}
```

✅ **Result**: Users can now add WordPress and HTML static sites through UI

---

### Phase 2: Publishing API in Generated Sites (2 hours)

**Critical for HTML static sites to accept articles**

**Step 1**: Copy the PHP API template
```bash
cp templates/internal-api-publish.php \
   /your/project/templates/internal-api-publish.php
```

**Step 2**: Update website_builder.py

Find the `generate_site()` function (around line 2428) and add:

```python
from services.website_manager import WebsiteBuilder

def generate_site(payload: dict, output_root: Path) -> dict:
    # ... existing site generation code ...
    
    # NEW: Setup internal publishing API for HTML static sites
    site_type = payload.get("site_type", "wordpress")
    api_key_hash = payload.get("internal_api_key_hash")
    
    if site_type == "html_static" and api_key_hash and output_dir.exists():
        try:
            builder = WebsiteBuilder(output_dir)
            api_path = builder.setup_publishing_api(api_key_hash)
            state.log(f"Publishing API created: {api_path}")
        except Exception as e:
            state.log(f"Warning: Publishing API setup failed: {e}", level="warn")
    
    return {
        "ok": True,
        "site_path": str(output_dir),
        "api_endpoint": f"{payload.get('base_url', '').rstrip('/')}/internal-api/publish"
        "api_configured": bool(api_key_hash and site_type == "html_static"),
    }
```

**Step 3**: Update the payload when creating HTML static sites

In the function that prepares site generation payload:
```python
# When site_type is html_static, include the hashed key
payload = {
    "name": website["name"],
    "base_url": website["base_url"],
    "site_type": website["site_type"],
    "internal_api_key_hash": website["api_key_hash"],  # NEW
    # ... other fields ...
}
```

✅ **Result**: Generated sites now have `/internal-api/publish/` endpoint ready to accept articles

---

### Phase 3: Test End-to-End (1 hour)

**Test WordPress Publishing**
```bash
# 1. Add a WordPress site in the UI
# 2. Click "Test Connection" - should verify auth
# 3. Generate article and publish
# 4. Verify post appears in WordPress
```

**Test HTML Static Publishing**
```bash
# 1. Add an HTML static site in the UI
# 2. Copy the generated API key
# 3. Generate a website with that configuration
# 4. Deploy the generated site
# 5. Generate article and publish
# 6. Verify article appears on website
# 7. Check /internal-api/publish logs
```

---

## File Integration Details

### Current main.py Structure

Your main.py already includes:

```python
# Line 47-58: Helper functions for website management
def _site_type(row_or_value) -> str
def _publish_method(site_type: str) -> str
def _public_website(row) -> dict
def _website_by_base_url(base_url: str, exclude_id: int | None = None)
def _sync_wordpress_categories(row) -> tuple[list[dict], str]
def _check_wordpress_upload_auth(row) -> dict

# Line 917-1000: POST /websites endpoint
@app.post("/websites", status_code=201)
async def create_website(body: WebsiteCreate):
    # Handles both wordpress and html_static types
    # Validates credentials
    # Generates API keys
    # Syncs categories
    
# Line 1015-1094: PUT /websites/{website_id}
@app.put("/websites/{website_id}")
async def update_website(website_id: int, body: WebsiteUpdate):
    
# Line 1095-1125: POST /websites/{website_id}/sync-categories
@app.post("/websites/{website_id}/sync-categories")
async def sync_categories(website_id: int):

# Line 1126-1145: POST /websites/{website_id}/test
@app.post("/websites/{website_id}/test")
async def test_website_connection(website_id: int):

# Line 1146-1175: POST /websites/{website_id}/regenerate-api-key
@app.post("/websites/{website_id}/regenerate-api-key")
async def regenerate_api_key(website_id: int):

# Line 1176-1200: DELETE /websites/{website_id}
@app.delete("/websites/{website_id}", status_code=200)
async def delete_website(website_id: int):
```

✅ **All critical endpoints already implemented!**

---

## Optional Enhancements (Advanced)

If you want to use the provided domain models and utilities:

### Add website_manager.py Usage

```python
# In main.py, add these imports
from services.website_manager import (
    TokenManager,
    WebsiteFactory,
    WebsiteBuilder,
    PublishingManager,
)

# Use TokenManager in custom endpoints
@app.post("/websites/{website_id}/regenerate-key")
async def regenerate_key(website_id: int):
    # Generate new key
    new_key = TokenManager.generate_api_key()
    new_hash = TokenManager.hash_token(new_key)
    
    # Update database
    state.conn.execute(
        "UPDATE websites SET api_key_hash = ? WHERE id = ?",
        (new_hash, website_id)
    )
    state.conn.commit()
    
    return {"api_key": new_key}
```

### Add website_endpoints.py Usage

```python
# Import the type options function for dynamic forms
from services.website_endpoints import get_website_type_options

@app.get("/website-types")
def get_website_types():
    return get_website_type_options()
```

Then in frontend:
```tsx
// Fetch form options dynamically
const response = await fetch('/api/website-types')
const types = await response.json()

// types[0].fields contains form field definitions
types.forEach(type => {
  console.log(type.value, type.fields)
})
```

---

## Implementation Checklist

- [ ] **Frontend (Phase 1 - 1 hour)**
  - [ ] Copy AddWebsiteModal.tsx to components/
  - [ ] Import in website manager page
  - [ ] Test modal opens/closes
  - [ ] Test form displays correctly for WordPress
  - [ ] Test form displays correctly for HTML Static

- [ ] **Publishing API (Phase 2 - 2 hours)**
  - [ ] Copy templates/internal-api-publish.php
  - [ ] Update website_builder.py generate_site()
  - [ ] Test site generation includes API
  - [ ] Verify /internal-api/publish/ accessible
  - [ ] Check permissions on generated files

- [ ] **End-to-End Testing (Phase 3 - 1 hour)**
  - [ ] Add WordPress site via UI
  - [ ] Test WordPress publishing
  - [ ] Add HTML static site via UI
  - [ ] Generate HTML site with API
  - [ ] Deploy generated site
  - [ ] Test HTML static publishing
  - [ ] Verify both article streams work

- [ ] **Production Deployment**
  - [ ] Update requirements.txt if needed
  - [ ] Database backup before changes
  - [ ] Deploy all updated files
  - [ ] Test in staging environment
  - [ ] Monitor error logs after deployment

---

## Common Issues & Solutions

### Issue: "API endpoint not responding"

**Solution**:
1. Verify `/internal-api/publish/index.php` exists in generated site
2. Check PHP execution enabled on hosting
3. Verify API key hash embedded correctly
4. Check file permissions (644 for PHP files)

### Issue: "Publishing to HTML site fails"

**Solution**:
1. Verify Bearer token in Authorization header
2. Test API key matches database hash
3. Check site `/logs/publish-api.log` for errors
4. Verify article payload contains required fields

### Issue: WordPress categories not syncing

**Solution**:
1. Verify WordPress REST API enabled
2. Check application password still valid
3. Test with curl: `curl -u user:pass https://site.com/wp-json/wp/v2/categories`

---

## Next Steps

1. **Copy AddWebsiteModal.tsx** to your project
2. **Update website_builder.py** to set up publishing API
3. **Test end-to-end** with both site types
4. **Deploy to production** with monitoring

All the hard work is done! Just integrate the remaining pieces and you're complete. 🎉
