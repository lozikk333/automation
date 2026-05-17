# HTML Static Website Publishing Integration Guide

## Complete Backend + Frontend Implementation for Dual Publishing

This guide provides complete instructions for implementing both WordPress and HTML static website support in your automation platform.

---

## Architecture Overview

### Publishing Modes Supported

1. **WordPress REST API**
   - Standard WordPress installation
   - Admin credentials + Application Password
   - Media upload + Post publishing
   - Category management

2. **HTML Static API**
   - Self-hosted static HTML sites
   - Secure Bearer token authentication
   - Direct file system access
   - Embedded PHP publishing endpoint
   - Automatic sitemap updates

### Data Flow

```
Article Generated
    ↓
Publishing Engine (pipeline.py)
    ↓
    ├─→ WordPress? → WordPressPublisher (REST API)
    │                ├─ Upload featured image
    │                ├─ Create post draft
    │                └─ Publish with categories
    │
    └─→ HTML Static? → HtmlStaticPublisher (Bearer Token)
                       ├─ POST to /internal-api/publish/
                       ├─ Create article/slug/index.html
                       ├─ Update homepage (automation marker)
                       └─ Update sitemap.xml
```

---

## Phase 1: Database Schema

### Existing Support ✅

The `websites` table already supports both types:

```sql
CREATE TABLE websites (
    id                  INTEGER PRIMARY KEY,
    name                TEXT NOT NULL,
    base_url            TEXT NOT NULL,
    site_type           TEXT DEFAULT 'wordpress',  -- 'wordpress' or 'html_static'
    publish_method      TEXT DEFAULT 'wordpress_rest',  -- 'wordpress_rest' or 'html_static_api'
    status              TEXT DEFAULT 'active',
    
    -- WordPress fields
    username            TEXT,
    password            TEXT,  -- App password
    
    -- HTML Static fields
    publish_endpoint    TEXT,  -- /internal-api/publish/
    api_key_hash        TEXT,  -- SHA-256 hash of API key
    api_enabled         INTEGER DEFAULT 0,
    
    -- Metadata
    last_publish_at     TIMESTAMP,
    local_path          TEXT,
    categories_json     TEXT,
    categories_synced_at TIMESTAMP,
    publish_status      TEXT DEFAULT 'draft',
    
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Phase 2: Backend Files

### 1. Internal Publishing API (`templates/internal-api-publish.php`)

**Purpose**: Embedded in generated HTML sites to receive and publish articles

**Key Features**:
- Bearer token authentication (hashed verification)
- Atomic file operations (temporary file pattern)
- XSS protection and HTML sanitization
- Automatic sitemap updates
- Homepage recent posts integration
- Request validation and error logging

**Security Measures**:
```php
// Token verification using constant-time comparison
const AUTOMATION_API_KEY_HASH = '{{ API_KEY_HASH }}';  // Replaced during site generation

// Hashed comparison
if (!hash_equals($token_hash, AUTOMATION_API_KEY_HASH)) {
    http_response_code(401);
    die(json_encode(['ok' => false, 'error' => 'Unauthorized']));
}

// Atomic file writing
$temp_file = $path . '.tmp';
file_put_contents($temp_file, $content, LOCK_EX);
rename($temp_file, $path);  // Atomic rename
```

**Endpoint**:
```
POST /internal-api/publish/
Authorization: Bearer {API_KEY}
Content-Type: application/json

{
    "title": "Article Title",
    "slug": "article-slug",
    "contentHtml": "<p>HTML content</p>",
    "metaTitle": "SEO Title",
    "metaDescription": "Description",
    "featuredImage": "https://url/image.jpg",
    "category": "Breakfast",
    "publishDate": "2024-05-10T12:00:00Z"
}
```

### 2. Website Manager (`services/website_manager.py`)

**Purpose**: Unified interface for managing both website types

**Key Classes**:

```python
class SiteType(Enum):
    WORDPRESS = "wordpress"
    HTML_STATIC = "html_static"

class TokenManager:
    @staticmethod
    def generate_api_key(length=32) -> str
    @staticmethod
    def hash_token(token: str) -> str
    @staticmethod
    def verify_token(provided_token: str, stored_hash: str) -> bool

class WebsiteFactory:
    @staticmethod
    def create_wordpress_site(name, base_url, username, password)
    @staticmethod
    def create_html_static_site(name, base_url, api_key, publish_endpoint, local_path)

class WebsiteBuilder:
    def setup_publishing_api(self, api_key_hash: str)
    def verify_api_setup(self) -> bool

class PublishingManager:
    @staticmethod
    def get_publisher_for_site(site: Dict) -> Dict
```

### 3. Website Endpoints (`services/website_endpoints.py`)

**Purpose**: Enhanced API endpoints for website management

**Key Functions**:

```python
async def create_website_enhanced(state, body: WebsiteCreate):
    """Create WordPress or HTML static website"""
    
async def _create_wordpress_website(state, body):
    """WordPress-specific setup with category sync"""
    
async def _create_html_static_website(state, body):
    """HTML static setup with API key generation"""
    
def get_website_type_options() -> List[WebsiteTypeOption]:
    """Get configuration options for frontend"""
```

### 4. Enhanced Website Builder

**Location**: `services/website_builder.py` (update `generate_site()`)

**Enhancement**:
```python
def generate_site(payload: dict, output_root: Path) -> dict:
    # ... existing code ...
    
    # NEW: Setup publishing API
    api_key_hash = payload.get("internal_api_key_hash") or ""
    if api_key_hash:
        builder = WebsiteBuilder(output_dir)
        try:
            api_path = builder.setup_publishing_api(api_key_hash)
            state.log(f"Publishing API created: {api_path}")
        except Exception as e:
            state.log(f"Warning: Publishing API setup failed: {e}")
    
    return {
        "ok": True,
        "site_path": str(output_dir),
        "api_configured": bool(api_key_hash),
    }
```

### 5. Publishing Pipeline Updates

**Location**: `orchestrator/pipeline.py` (update `wordpress_publish_task()`)

**Already Implemented** ✅

```python
def _publish_html_static(state: StateManager, job_id: int, site: dict, payload: dict):
    """Publish to HTML static via API or local filesystem"""
    if site.get("local_path") and Path(site["local_path"]).exists():
        # Local publish
        result = publish_to_local_site(site["local_path"], payload)
    else:
        # Remote API publish
        result = HtmlStaticPublisher(
            site["publish_endpoint"],
            site["password"]  # API key stored here
        ).publish(payload)
    return result
```

---

## Phase 3: Frontend React Components

### Add Website Modal (`components/AddWebsiteModal.tsx`)

**Features**:
- Type selector (WordPress / HTML Static)
- Dynamic form fields based on type
- WordPress credential validation
- HTML Static API key display with copy-to-clipboard
- Error handling and loading states
- Success confirmation with generated API key

**Usage**:
```tsx
<AddWebsiteModal 
  onClose={() => setShowModal(false)}
  onSuccess={() => {
    fetchWebsites()  // Refresh list
    setShowModal(false)
  }}
/>
```

### Website List Updates

**Show site type badge**:
```tsx
<span className={`px-2 py-1 rounded text-xs font-medium ${
  website.site_type === 'html_static' 
    ? 'bg-blue-100 text-blue-700' 
    : 'bg-purple-100 text-purple-700'
}`}>
  {website.site_type === 'html_static' ? 'Static' : 'WordPress'}
</span>
```

**API key management for HTML Static**:
```tsx
{website.site_type === 'html_static' && (
  <>
    <button onClick={() => regenerateApiKey(website.id)}>
      Regenerate API Key
    </button>
    <button onClick={() => testConnection(website.id)}>
      Test Connection
    </button>
  </>
)}
```

---

## Phase 4: Integration Steps

### Step 1: Update Database

```bash
# No migration needed - schema already supports both types
# Verify columns exist:
sqlite3 content-automation-system/data/state.db ".schema websites"
```

### Step 2: Install Backend Code

```bash
# Copy files to your project:
cp templates/internal-api-publish.php \
   content-automation-system/templates/

cp services/website_manager.py \
   content-automation-system/services/

cp services/website_endpoints.py \
   content-automation-system/services/
```

### Step 3: Update main.py

Replace `/websites` endpoint implementation:

```python
# In main.py, import new endpoints
from services.website_endpoints import (
    WebsiteCreate,
    WebsiteUpdate,
    create_website_enhanced,
    get_website_type_options,
)

# Replace POST /websites endpoint
@app.post("/websites", status_code=201)
async def create_website(body: WebsiteCreate):
    return await create_website_enhanced(state, body)

# Add new endpoint for type options
@app.get("/website-types")
async def get_website_types():
    return get_website_type_options()
```

### Step 4: Install Frontend Component

```bash
# Copy React component
cp components/AddWebsiteModal.tsx \
   content-automation-system/components/
```

### Step 5: Update Website Manager UI

```tsx
import { AddWebsiteModal } from '@/components/AddWebsiteModal'

export function WebsitesPage() {
  const [showAddModal, setShowAddModal] = useState(false)
  
  return (
    <>
      <button onClick={() => setShowAddModal(true)}>
        + Add Website
      </button>
      
      {showAddModal && (
        <AddWebsiteModal
          onClose={() => setShowAddModal(false)}
          onSuccess={refreshWebsites}
        />
      )}
    </>
  )
}
```

---

## Phase 5: Workflow Examples

### WordPress Publishing Flow

1. User adds WordPress site:
   ```
   Add Website → WordPress type → Enter username/password
   ↓
   Backend tests connection (validate upload permissions)
   ↓
   Create database entry with credentials
   ↓
   Sync categories from WordPress
   ```

2. Article publishing:
   ```
   Generate article → Pipeline checks site_type
   ↓
   Get WordPress credentials → Create WordPressPublisher
   ↓
   Upload featured image → Create post draft
   ↓
   Publish post with category
   ```

### HTML Static Publishing Flow

1. User adds HTML Static site:
   ```
   Add Website → HTML Static type → [Optional: endpoint, API key]
   ↓
   Generate API key (if not provided)
   ↓
   Hash API key → Store hash in database
   ↓
   Return unhashed key to user (display in modal)
   ↓
   User stores key securely in .env or config
   ```

2. User generates website:
   ```
   Build Site → Include internal-api-publish.php
   ↓
   Embed API key hash in index.php
   ↓
   Deploy site to hosting
   ```

3. Article publishing:
   ```
   Generate article → Pipeline checks site_type
   ↓
   Get publish_endpoint + API key
   ↓
   POST to /internal-api/publish/ with Bearer token
   ↓
   Server verifies hash and creates article
   ↓
   Update homepage + sitemap
   ```

---

## Phase 6: Security Considerations

### API Key Management

```python
# Generation
api_key = secrets.token_urlsafe(32)  # Cryptographically secure
api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()

# Storage
database: api_key_hash (never store plain key)
user: api_key (displayed once, user must copy)

# Verification (constant-time)
provided_hash = hash(provided_token)
secrets.compare_digest(provided_hash, stored_hash)
```

### Token Verification in PHP

```php
// Prevent timing attacks
hash_equals($token_hash, AUTOMATION_API_KEY_HASH)

// Rate limiting
$last_publish = time()
if (time() - $last_publish < 60) {
    http_response_code(429);  // Too Many Requests
}
```

### Request Validation

```php
// HTML sanitization
strip_tags($html, '<p><br><strong><em><u><ul><li>...')

// XSS protection
htmlspecialchars($text, ENT_QUOTES, 'UTF-8')

// Slug validation
preg_match('/^[a-z0-9_-]+$/i', $slug)
```

### File Operations

```php
// Atomic writes (prevent corruption)
file_put_contents($temp, $content, LOCK_EX);
rename($temp, $final);  // Atomic

// Permission management
chmod($api_file, 0o644);  // Web server readable
```

---

## Phase 7: Testing Checklist

### WordPress Integration
- [ ] Add WordPress site with valid credentials
- [ ] Verify connection test passes
- [ ] Sync categories successfully
- [ ] Publish article to WordPress
- [ ] Featured image uploads correctly
- [ ] Post appears as draft in WordPress
- [ ] Post can be published from WordPress

### HTML Static Integration
- [ ] Add HTML static site
- [ ] API key generates automatically
- [ ] API key displays in modal
- [ ] Test connection works (local path)
- [ ] Generate HTML site with API
- [ ] Publish article via API
- [ ] Article appears on homepage
- [ ] Sitemap updates correctly
- [ ] API key regeneration works

### Security Testing
- [ ] Invalid API key rejected
- [ ] XSS payloads sanitized
- [ ] Rate limiting works
- [ ] Atomic file writes tested
- [ ] Error logging functional

### Error Handling
- [ ] Invalid WordPress credentials
- [ ] Network errors during publish
- [ ] Filesystem permission errors
- [ ] Database constraint violations
- [ ] Malformed JSON payloads

---

## Phase 8: Deployment Checklist

### Pre-Deployment
- [ ] All files copied to production
- [ ] Database schema verified
- [ ] Environment variables configured
- [ ] SSL certificates valid
- [ ] File permissions correct (755 for dirs, 644 for files)

### Hosting Requirements

**For Generated HTML Sites**:
- PHP 7.4+ with CLI access
- Write permissions on site root
- Web server (nginx/Apache)
- HTTPS recommended for API

**Environment**:
```bash
# .env or config
WORDPRESS_URL=https://blog.example.com
WORDPRESS_USERNAME=admin@example.com
WORDPRESS_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx

# HTML sites don't need special env vars
# API keys stored in database
```

### Post-Deployment
- [ ] Test WordPress publishing
- [ ] Test HTML static publishing
- [ ] Verify API endpoints accessible
- [ ] Check logging configured
- [ ] Monitor error logs

---

## Phase 9: Troubleshooting Guide

### WordPress Connection Issues

**Error**: "Invalid WordPress username or application password"

**Solution**:
1. Verify username is correct admin account
2. Generate new Application Password in WordPress
3. Delete and regenerate token if needed
4. Check WordPress user has "upload_files" capability

### HTML Static API Issues

**Error**: "API endpoint not responding"

**Solutions**:
1. Check `/internal-api/publish/index.php` exists
2. Verify PHP execution enabled on hosting
3. Check API key hash embedded correctly
4. Review error logs at `/logs/publish-api-errors.log`

**Error**: "Unauthorized: Invalid token"

**Solutions**:
1. Verify API key saved correctly
2. Check token hash matches in database
3. Ensure Bearer prefix in Authorization header
4. Test with manual curl request

### Publishing Failures

**For WordPress**: Check `/logs/publish-api-errors.log`

**For HTML Static**: Check site `/logs/publish-api.log`

---

## Summary

This integration provides:

✅ Unified website management for both WordPress and static sites  
✅ Secure API key generation and verification  
✅ Automatic publishing via appropriate method  
✅ Error handling and logging  
✅ User-friendly UI for configuration  
✅ Production-ready security measures  
✅ Automatic homepage + sitemap updates for static sites  

Both publishing modes work seamlessly with the existing automation pipeline!
