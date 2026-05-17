# Quick Reference Card

## Implementation at a Glance

### What You're Building
**Dual publishing platform** that automatically sends articles to both WordPress and HTML static sites through one unified interface.

### What's Provided
✅ 1,004 lines of backend code (PHP + Python)  
✅ 440 lines of frontend code (React)  
✅ 1,250 lines of documentation  
✅ Complete testing procedures  
✅ Production deployment guide  

### Time Required
**Phase 1**: 30 min (Frontend modal)  
**Phase 2**: 2 hours (Publishing API setup)  
**Phase 3**: 1 hour (Testing)  
**Total**: 3.5 hours

---

## Phase 1: Frontend (30 minutes)

### Files to Copy
```bash
cp components/AddWebsiteModal.tsx \
   YOUR_PROJECT/components/
```

### Code to Add
```tsx
import { AddWebsiteModal } from '@/components/AddWebsiteModal'

// In your websites page:
<button onClick={() => setShowModal(true)}>
  + Add Website
</button>

{showModal && (
  <AddWebsiteModal 
    onClose={() => setShowModal(false)}
    onSuccess={refreshWebsites}
  />
)}
```

### Test
- Click "+ Add Website" button
- Select WordPress → shows username/password fields
- Select HTML Static → shows endpoint/API key fields
- Fill form and submit → success modal shows

✅ **Phase 1 Complete**: Users can add sites through UI

---

## Phase 2: Publishing API (2 hours)

### Files to Copy
```bash
cp templates/internal-api-publish.php \
   YOUR_PROJECT/templates/
```

### Code to Update
**File**: `services/website_builder.py` 
**Function**: `generate_site()` (around line 2428)
**Action**: Add API setup code (see WEBSITE_BUILDER_ENHANCEMENT.md)

### Key Code Section
```python
# Add after site generation
if site_type == "html_static" and api_key_hash:
    builder = WebsiteBuilder(output_dir)
    builder.setup_publishing_api(api_key_hash)
    state.log(f"Publishing API ready: {base_url}/internal-api/publish")
```

### Test
- Generate HTML site with API key configured
- Verify: `generated_sites/[site]/internal-api/publish/index.php` exists
- Check: File permissions are 644
- Test: `curl -X POST /internal-api/publish/ -H "Authorization: Bearer {key}"`

✅ **Phase 2 Complete**: Generated sites have publishing API

---

## Phase 3: Testing (1 hour)

### WordPress Flow
```bash
1. Add WordPress site
2. Verify: Categories synced
3. Generate article
4. Publish to WordPress
5. Check: Post appears in WordPress dashboard
```

### HTML Static Flow
```bash
1. Add HTML static site
2. Copy generated API key
3. Generate HTML website with API config
4. Deploy generated site
5. Generate article
6. Publish to HTML site
7. Check: Article appears on website
```

### Verification
```bash
# Check logs
tail -f logs/app.log | grep -i "publish"

# Verify database
sqlite3 data/state.db "SELECT name, site_type FROM websites;"

# Test API endpoints
curl http://localhost:8000/api/websites
curl http://localhost:8000/api/website-types
```

✅ **Phase 3 Complete**: Both publishing methods working

---

## File Checklist

### Backend Files
- [ ] `templates/internal-api-publish.php` copied
- [ ] `services/website_manager.py` copied (optional)
- [ ] `services/website_endpoints.py` copied (optional)

### Frontend Files
- [ ] `components/AddWebsiteModal.tsx` copied
- [ ] Imported in website manager page
- [ ] Button wired to show modal

### Updates
- [ ] `services/website_builder.py` updated with API setup code
- [ ] Payload includes `internal_api_key_hash` for HTML sites

### Documentation
- [ ] `README_IMPLEMENTATION.md` saved
- [ ] `PLATFORM_SUMMARY.md` saved
- [ ] `IMPLEMENTATION_CHECKLIST.md` saved
- [ ] `WEBSITE_BUILDER_ENHANCEMENT.md` saved
- [ ] `HTML_STATIC_INTEGRATION_GUIDE.md` saved
- [ ] `TESTING_AND_DEPLOYMENT.md` saved

---

## Common Copy Commands

```bash
# Copy all backend files
cp templates/internal-api-publish.php YOUR_PROJECT/templates/
cp services/website_manager.py YOUR_PROJECT/services/
cp services/website_endpoints.py YOUR_PROJECT/services/

# Copy frontend files
cp components/AddWebsiteModal.tsx YOUR_PROJECT/components/

# Backup before changes
cp YOUR_PROJECT/services/website_builder.py \
   YOUR_PROJECT/services/website_builder.py.backup
```

---

## Database Fields Already Exist

✅ `site_type` (wordpress or html_static)  
✅ `api_key_hash` (SHA-256 hash)  
✅ `publish_endpoint` (API endpoint URL)  
✅ `api_enabled` (0/1 flag)  
✅ `username` (WordPress user or blank)  
✅ `password` (WordPress app password or API key)  
✅ `categories_json` (WordPress categories)  

**No migrations needed!**

---

## Security Summary

| Aspect | Implementation |
|--------|-----------------|
| Key Generation | `secrets.token_urlsafe(32)` |
| Key Storage | SHA-256 hash only |
| Key Verification | `secrets.compare_digest()` |
| API Auth | Bearer token header |
| XSS Protection | HTML sanitization + strip_tags |
| File Writes | Atomic (temp + rename) |
| Transport | HTTPS required |

---

## API Endpoints

### Create Website
```http
POST /websites
{
  "name": "My Site",
  "base_url": "https://example.com",
  "site_type": "wordpress" | "html_static",
  "username": "user" (WordPress only),
  "password": "pass" (WordPress only)
}
```

### Publishing (HTML Static)
```http
POST {publish_endpoint}
Authorization: Bearer {api_key}
{
  "title": "Article Title",
  "slug": "article-slug",
  "contentHtml": "<p>HTML content</p>"
}
```

---

## Troubleshooting Quick Links

| Error | Solution |
|-------|----------|
| "Module not found" | See IMPLEMENTATION_CHECKLIST.md |
| Permission denied | chmod 755 generated_sites/ |
| API not responding | Verify /internal-api/publish/index.php exists |
| Key hash mismatch | Verify SHA-256 format (64 hex chars) |
| Publishing fails | Check /logs/publish-api.log |

---

## Performance Metrics (Expected)

- Website creation: 20-100ms
- List websites: 5ms
- Test WordPress: 500-2000ms
- Publish article: 100-500ms
- Rate limit: 100+ requests/second

---

## Monitoring Commands

```bash
# Watch for errors
tail -f logs/app.log | grep -E "ERROR|CRITICAL"

# Count published articles
sqlite3 data/state.db \
  "SELECT COUNT(*) FROM websites WHERE last_publish_at IS NOT NULL;"

# Verify API keys
sqlite3 data/state.db \
  "SELECT id, name, SUBSTR(api_key_hash,1,10) FROM websites WHERE api_key_hash IS NOT NULL;"

# Check site types
sqlite3 data/state.db \
  "SELECT site_type, COUNT(*) FROM websites GROUP BY site_type;"
```

---

## Success Indicators

✅ Users can add WordPress sites via UI  
✅ Users can add HTML static sites via UI  
✅ API key displays on HTML site creation  
✅ WordPress articles publish successfully  
✅ HTML static articles publish successfully  
✅ Homepage updates on static sites  
✅ Sitemap updates automatically  
✅ All operations logged without errors  
✅ Error cases handled gracefully  
✅ No plaintext credentials in database  

---

## Rollback If Needed

```bash
# Stop application
systemctl stop myapp

# Restore backups
cp *.backup ./

# Remove new files
rm templates/internal-api-publish.php
rm services/website_manager.py
rm services/website_endpoints.py
rm components/AddWebsiteModal.tsx

# Restart
systemctl start myapp
```

---

## Documentation Quick Links

| Document | Purpose | Time |
|----------|---------|------|
| README_IMPLEMENTATION.md | Overview & quick start | 10 min |
| PLATFORM_SUMMARY.md | Status & architecture | 10 min |
| IMPLEMENTATION_CHECKLIST.md | Phase-by-phase guide | 30 min |
| WEBSITE_BUILDER_ENHANCEMENT.md | Code integration details | 1 hour |
| HTML_STATIC_INTEGRATION_GUIDE.md | Complete architecture | 20 min |
| TESTING_AND_DEPLOYMENT.md | Testing & deploy | 1 hour |

---

## Next Steps

**Right Now:**
1. Copy `AddWebsiteModal.tsx` ✓
2. Wire up to your page ✓
3. Test it works ✓

**Today:**
4. Copy `templates/internal-api-publish.php` ✓
5. Update `website_builder.py` ✓
6. Test site generation ✓

**Tomorrow:**
7. Test WordPress publishing ✓
8. Test HTML static publishing ✓
9. Deploy to production ✓

---

## Important URLs

- Main reference: `README_IMPLEMENTATION.md`
- Step-by-step: `IMPLEMENTATION_CHECKLIST.md`
- Code help: `WEBSITE_BUILDER_ENHANCEMENT.md`
- Testing: `TESTING_AND_DEPLOYMENT.md`

---

## Key Concepts

**Site Types**
- `wordpress`: REST API publishing
- `html_static`: Direct file + API publishing

**Publishing Methods**
- `wordpress_rest`: Uses WordPress REST API
- `html_static_api`: Uses /internal-api/publish/

**Security Model**
- API keys: Generated once, hashed, verified via constant-time comparison
- Authentication: Bearer token in Authorization header
- Validation: Required field checks + format validation

**File Operations**
- Atomic writes: Write to temp file, atomic rename
- Permissions: 644 (readable, not executable)
- Logging: All operations logged with timestamps

---

## Before Deployment

```bash
# 1. Backup database
cp data/state.db data/state.db.backup.$(date +%s)

# 2. Verify PHP syntax
php -l templates/internal-api-publish.php

# 3. Test Python imports
python -c "from services.website_manager import TokenManager; print('OK')"

# 4. Check file permissions
ls -la templates/internal-api-publish.php

# 5. Run unit tests (provided in TESTING_AND_DEPLOYMENT.md)
python test_token_manager.py
```

---

## Support

For help with specific issues, see:
- **Code errors**: WEBSITE_BUILDER_ENHANCEMENT.md
- **API errors**: HTML_STATIC_INTEGRATION_GUIDE.md
- **Deployment issues**: TESTING_AND_DEPLOYMENT.md
- **General questions**: PLATFORM_SUMMARY.md

---

**Status**: All files provided, ready for integration! 🚀

**Time estimate**: 3-4 hours to production.

**Difficulty**: Moderate (copy files + integrate code).

**Support**: Complete documentation included.

Good luck! 
