# Complete Testing & Deployment Guide

## Pre-Deployment Verification

### Backend Components Check

```bash
# 1. Verify PHP API template exists and is readable
ls -la content-automation-system/templates/internal-api-publish.php
# Expected: -rw-r--r-- 186 lines

# 2. Verify Python modules exist
ls -la content-automation-system/services/website_manager.py
ls -la content-automation-system/services/website_endpoints.py

# 3. Check database schema
sqlite3 content-automation-system/data/state.db \
  "SELECT name FROM sqlite_master WHERE type='table' AND name='websites';"
# Expected: websites

# 4. Verify columns exist for dual-site support
sqlite3 content-automation-system/data/state.db \
  "PRAGMA table_info(websites);" | grep -E "site_type|api_key_hash|publish_endpoint"
```

### Frontend Component Check

```bash
# 1. Verify React component exists
ls -la content-automation-system/components/AddWebsiteModal.tsx
# Expected: should exist

# 2. Verify TypeScript syntax
npx tsc --noEmit components/AddWebsiteModal.tsx 2>&1 | head -20
```

### Dependencies Check

```bash
# 1. Verify Python packages in venv
source venv/bin/activate
pip list | grep -E "fastapi|pydantic"
# Expected: fastapi, pydantic present

# 2. Verify main.py imports work
python -c "from services.website_manager import TokenManager; print('OK')"
# Expected: OK (no errors)

# 3. Check PHP version
php -v
# Expected: PHP 7.4+ 
```

---

## Unit Testing

### Test 1: API Key Generation & Hashing

```python
# test_token_manager.py

from services.website_manager import TokenManager
import hashlib

# Generate key
key = TokenManager.generate_api_key()
assert len(key) > 32, "Generated key too short"
print(f"✓ Generated API key: {key[:20]}...")

# Hash key
key_hash = TokenManager.hash_token(key)
assert len(key_hash) == 64, "Hash not 64 hex characters (not SHA-256)"
assert all(c in '0123456789abcdef' for c in key_hash), "Hash contains non-hex characters"
print(f"✓ Hash generated: {key_hash[:20]}...")

# Verify key
is_valid = TokenManager.verify_token(key, key_hash)
assert is_valid, "Valid key failed verification"
print("✓ Token verification passed")

# Test with wrong key
wrong_key = TokenManager.generate_api_key()
is_valid = TokenManager.verify_token(wrong_key, key_hash)
assert not is_valid, "Invalid key incorrectly verified"
print("✓ Wrong token correctly rejected")

print("\n✅ All token manager tests passed!")
```

**Run test**:
```bash
cd content-automation-system
python -m pytest test_token_manager.py -v
# or
python test_token_manager.py
```

### Test 2: Website Validator

```python
# test_validators.py

from services.website_manager import WebsiteValidator

# Valid URLs
valid_urls = [
    "https://example.com",
    "http://localhost:8000",
    "https://site.co.uk/blog",
]

for url in valid_urls:
    is_valid, error = WebsiteValidator.validate_url(url)
    assert is_valid, f"Valid URL rejected: {url} - {error}"
    print(f"✓ Valid: {url}")

# Invalid URLs
invalid_urls = [
    "example.com",  # missing protocol
    "ftp://example.com",  # unsupported protocol
    "https://",  # incomplete URL
]

for url in invalid_urls:
    is_valid, error = WebsiteValidator.validate_url(url)
    assert not is_valid, f"Invalid URL accepted: {url}"
    print(f"✓ Rejected: {url} - {error}")

# Valid credentials
is_valid, error = WebsiteValidator.validate_wordpress_credentials("admin", "password123")
assert is_valid, f"Valid credentials rejected: {error}"
print("✓ Valid WordPress credentials")

# Invalid credentials
is_valid, error = WebsiteValidator.validate_wordpress_credentials("a", "b")
assert not is_valid, "Invalid credentials accepted"
print(f"✓ Rejected: {error}")

print("\n✅ All validator tests passed!")
```

### Test 3: PHP API Template

```bash
# Verify PHP syntax
php -l content-automation-system/templates/internal-api-publish.php
# Expected: No syntax errors detected

# Test PHP file structure
grep -c "function authenticate" content-automation-system/templates/internal-api-publish.php
grep -c "function validate_payload" content-automation-system/templates/internal-api-publish.php
grep -c "function create_article_page" content-automation-system/templates/internal-api-publish.php
# Expected: Each should return 1

echo "✓ PHP template structure verified"
```

---

## Integration Testing

### Test Scenario 1: WordPress Site Creation & Publishing

```bash
# 1. Add WordPress site via API
curl -X POST http://localhost:8000/api/websites \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test WordPress",
    "base_url": "https://your-wordpress-site.com",
    "site_type": "wordpress",
    "username": "admin@example.com",
    "password": "xxxx xxxx xxxx xxxx xxxx xxxx"
  }'

# Expected response:
{
  "id": 1,
  "name": "Test WordPress",
  "site_type": "wordpress",
  "categories": [
    {"id": 1, "name": "Uncategorized", "slug": "uncategorized"},
    ...
  ],
  "api_key": ""
}

# 2. Test connection
curl -X POST http://localhost:8000/api/websites/1/test

# Expected: {"ok": true, "message": "Connected..."}

# 3. Publish article
curl -X POST http://localhost:8000/api/publish \
  -H "Content-Type: application/json" \
  -d '{
    "website_id": 1,
    "title": "Test Article",
    "slug": "test-article",
    "content": "Article content"
  }'

# Expected: {"ok": true, "post_id": 123}

# 4. Verify in WordPress
# Check WordPress admin panel for draft post
```

### Test Scenario 2: HTML Static Site Creation & Publishing

```bash
# 1. Add HTML static site via API
curl -X POST http://localhost:8000/api/websites \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Static Site",
    "base_url": "https://example.com",
    "site_type": "html_static"
  }'

# Expected response:
{
  "id": 2,
  "name": "Test Static Site",
  "site_type": "html_static",
  "api_key": "rABCDEF1234567890abcdefghijklmnopqrst-w",
  "publish_endpoint": "https://example.com/internal-api/publish"
}

# IMPORTANT: Copy the api_key for next steps!

# 2. Generate site with API configuration
curl -X POST http://localhost:8000/api/generate-site \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-site",
    "website_id": 2,
    "site_type": "html_static",
    "internal_api_key_hash": "<hash-from-database>"
  }'

# 3. Verify API file exists
ls -la generated_sites/test-site/internal-api/publish/index.php
# Expected: -rw-r--r-- (readable by web server)

# 4. Test API endpoint locally
curl -X POST http://localhost:8000/generated-sites/test-site/internal-api/publish/ \
  -H "Authorization: Bearer rABCDEF1234567890abcdefghijklmnopqrst-w" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Article",
    "slug": "test-article",
    "contentHtml": "<p>Article content</p>"
  }'

# Expected: {"ok": true, "message": "Article published"}

# 5. Verify article file created
ls -la generated_sites/test-site/article/test-article/
# Expected: index.html exists

# 6. Verify homepage updated
grep "test-article" generated_sites/test-site/index.html
# Expected: finds automation card entry
```

### Test Scenario 3: Frontend Modal Integration

```bash
# 1. Start the dev server
npm run dev
# or
python main.py

# 2. Navigate to websites page
# In browser: http://localhost:3000/websites

# 3. Click "+ Add Website" button
# Expected: Modal opens with type selection

# 4. Select "WordPress"
# Expected: Form shows username/password fields

# 5. Select "HTML Static"
# Expected: Form shows publish_endpoint/api_key fields

# 6. Fill form and submit
# Expected: Modal shows success with generated API key

# 7. Copy API key and verify
# Expected: Can copy to clipboard
```

---

## End-to-End Testing Checklist

```
WORDPRESS PUBLISHING FLOW
─────────────────────────
□ Create WordPress site in UI
  └─ Verify auth test passes
  └─ Verify categories synced
  └─ Verify site appears in list

□ Generate article in pipeline
  └─ Verify routes to WordPress publisher
  └─ Verify featured image uploads
  └─ Verify post created as draft
  └─ Verify categories assigned

□ Publish article
  └─ Verify post appears on WordPress
  └─ Verify images display correctly
  └─ Verify SEO fields populated

□ Error handling
  └─ Verify invalid credentials rejected
  └─ Verify network errors handled
  └─ Verify logs captured


HTML STATIC PUBLISHING FLOW
───────────────────────────
□ Create HTML static site in UI
  └─ Verify API key generated/displayed
  └─ Verify can copy API key
  └─ Verify site added to list

□ Generate website
  └─ Verify internal-api-publish.php included
  └─ Verify API key hash embedded
  └─ Verify file permissions correct
  └─ Verify /internal-api/publish accessible

□ Deploy generated site
  └─ Deploy to hosting provider
  └─ Verify SSL certificate valid
  └─ Verify API endpoint accessible

□ Publish article
  └─ Verify article file created
  └─ Verify article on homepage
  └─ Verify sitemap updated
  └─ Verify images served correctly

□ Error handling
  └─ Verify invalid token rejected
  └─ Verify malformed requests rejected
  └─ Verify rate limiting works
  └─ Verify errors logged

□ API key management
  └─ Verify can regenerate key
  └─ Verify old key stops working
  └─ Verify new key works immediately
```

---

## Performance Testing

### Load Test: Publishing 100 Articles

```bash
# Test script: load_test.sh

#!/bin/bash

SITE_ID=2  # HTML static site ID
API_KEY="your-api-key"
BASE_URL="https://example.com"
ENDPOINT="$BASE_URL/internal-api/publish"

echo "Starting load test: 100 articles"
echo "Endpoint: $ENDPOINT"
echo "API Key: ${API_KEY:0:20}..."
echo ""

for i in {1..100}; do
  SLUG="test-article-$i"
  TITLE="Test Article $i"
  
  RESPONSE=$(curl -s -X POST "$ENDPOINT" \
    -H "Authorization: Bearer $API_KEY" \
    -H "Content-Type: application/json" \
    -d "{
      \"title\": \"$TITLE\",
      \"slug\": \"$SLUG\",
      \"contentHtml\": \"<p>Article $i content</p>\"
    }")
  
  OK=$(echo $RESPONSE | grep -o '"ok":true' | wc -l)
  
  if [ $OK -eq 1 ]; then
    echo "✓ Article $i published"
  else
    echo "✗ Article $i failed: $RESPONSE"
  fi
  
  # Rate limit: 1 article per second
  sleep 1
done

echo ""
echo "Load test complete!"
```

**Run test**:
```bash
chmod +x load_test.sh
./load_test.sh

# Expected: 100% success rate, ~100 seconds total
```

---

## Deployment Steps

### Pre-Deployment Backup

```bash
# 1. Backup database
cp content-automation-system/data/state.db \
   content-automation-system/data/state.db.backup.$(date +%Y%m%d_%H%M%S)

# 2. Backup current main.py
cp content-automation-system/main.py \
   content-automation-system/main.py.backup.$(date +%Y%m%d_%H%M%S)

# 3. Create deployment log
touch deployment.log
date >> deployment.log
```

### File Deployment

```bash
# 1. Backend Python files
cp templates/internal-api-publish.php \
   content-automation-system/templates/

cp services/website_manager.py \
   content-automation-system/services/

cp services/website_endpoints.py \
   content-automation-system/services/

# 2. Frontend React component
cp components/AddWebsiteModal.tsx \
   content-automation-system/components/

# 3. Documentation
cp HTML_STATIC_INTEGRATION_GUIDE.md \
   content-automation-system/

cp WEBSITE_BUILDER_ENHANCEMENT.md \
   content-automation-system/

cp IMPLEMENTATION_CHECKLIST.md \
   content-automation-system/

# 4. Update main.py with website_builder.py enhancements
# (Manual integration - see WEBSITE_BUILDER_ENHANCEMENT.md)
```

### Post-Deployment Verification

```bash
# 1. Restart services
systemctl restart myapp  # or your service manager

# 2. Check logs for errors
tail -f logs/app.log | grep -i "error\|warning" &

# 3. Test API health
curl http://localhost:8000/health
# Expected: {"status": "ok"}

# 4. Test website endpoints
curl http://localhost:8000/api/websites
# Expected: JSON array of websites

# 5. Monitor for 30 minutes
# Watch for:
# - Error rate increases
# - Slow response times  
# - Failed publishes
# - API errors

# 6. Run smoke tests
python test_token_manager.py
python test_validators.py

# 7. Verify frontend works
# Navigate to: http://localhost:3000/websites
# Click: + Add Website
# Verify: Modal opens correctly

# 8. Test publishing (manually)
# Create test article
# Publish to WordPress site
# Publish to HTML static site
# Verify both work
```

---

## Monitoring & Logs

### Application Logs

```bash
# Watch for errors in real-time
tail -f logs/app.log | grep -E "ERROR|CRITICAL"

# Check publishing logs
tail -f logs/publishing.log

# Check API logs
tail -f logs/api.log

# Check generated site API logs
tail -f generated_sites/*/logs/publish-api.log
```

### Database Logs

```bash
# Check recent website additions
sqlite3 content-automation-system/data/state.db \
  "SELECT id, name, site_type, created_at FROM websites ORDER BY created_at DESC LIMIT 5;"

# Check API key hashes exist
sqlite3 content-automation-system/data/state.db \
  "SELECT id, name, api_key_hash FROM websites WHERE site_type='html_static';"

# Verify no plaintext passwords
sqlite3 content-automation-system/data/state.db \
  "SELECT COUNT(*) as count FROM websites WHERE password IS NOT NULL AND password LIKE '%_%_%';"
# Expected: Should show count of valid passwords, none obviously wrong
```

### Performance Metrics

```bash
# Response time check
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/websites
# Expected: < 100ms

# Database query performance
sqlite3 content-automation-system/data/state.db "PRAGMA query_only=ON; EXPLAIN QUERY PLAN SELECT * FROM websites WHERE site_type='html_static';"

# API key hash collision check (should have 0 collisions)
sqlite3 content-automation-system/data/state.db \
  "SELECT api_key_hash, COUNT(*) as count FROM websites GROUP BY api_key_hash HAVING count > 1;"
# Expected: Empty result
```

---

## Rollback Procedure

If something goes wrong:

```bash
# 1. Stop application
systemctl stop myapp

# 2. Restore backup files
cp content-automation-system/main.py.backup.* content-automation-system/main.py
cp content-automation-system/data/state.db.backup.* content-automation-system/data/state.db

# 3. Remove new files
rm content-automation-system/services/website_manager.py
rm content-automation-system/services/website_endpoints.py
rm content-automation-system/components/AddWebsiteModal.tsx
rm content-automation-system/templates/internal-api-publish.php

# 4. Restart application
systemctl start myapp

# 5. Verify operation
curl http://localhost:8000/api/websites
# Should work with old code

# 6. Debug and fix issue
# Check logs for what went wrong
tail -f logs/app.log
```

---

## Troubleshooting Common Issues

### Issue: "Module not found: services.website_manager"

```bash
# Check file exists
ls -la content-automation-system/services/website_manager.py

# Verify Python path includes services/
python -c "import sys; print(sys.path)"

# Test import
cd content-automation-system
python -c "from services.website_manager import TokenManager; print('OK')"
```

### Issue: "PHP: Permission denied"

```bash
# Fix permissions
chmod 755 generated_sites/
chmod 644 generated_sites/*/internal-api/publish/index.php

# Verify web server user can execute
ls -la generated_sites/test-site/internal-api/publish/index.php
# Should be: -rw-r--r--
```

### Issue: "API key hash mismatch"

```bash
# Verify hash format (64 hex chars)
sqlite3 content-automation-system/data/state.db \
  "SELECT api_key_hash FROM websites WHERE site_type='html_static' LIMIT 1;"

# Should output something like:
# 5f4dcc3b5aa765d61d8327deb882cf99b0d9e0e9f6b1b5bbf1b9e8f5c8f5a5c7

# Verify it's SHA-256 (not base64 or other format)
echo "test" | sha256sum
# hex output format

# Test hash generation in Python
python -c "import hashlib; print(hashlib.sha256('test'.encode()).hexdigest())"
```

---

## Success Criteria

After deployment, verify these criteria are met:

✅ WordPress sites can be created and tested  
✅ WordPress articles publish successfully  
✅ HTML static sites can be created with API keys  
✅ Generated sites include /internal-api/publish/  
✅ HTML static articles publish successfully  
✅ API key regeneration works  
✅ Category syncing works for WordPress  
✅ Error logging captures all failures  
✅ No plaintext API keys stored  
✅ Rate limiting prevents abuse  
✅ HTTPS enforced for API endpoints  
✅ Cross-site publishing works in one pipeline  

---

## Summary

This testing and deployment guide ensures your dual-site publishing platform is:

- **Reliable**: Comprehensive testing before deployment
- **Secure**: Proper verification of credentials and tokens
- **Monitored**: Logging and metrics collection
- **Recoverable**: Backup and rollback procedures

Follow these steps and you'll have a production-ready platform! 🚀
