# 🤖 AUTOMATED CONTENT SYSTEM - COMPLETE ROADMAP

## Zero to Production: Keyword → Article → Images → WordPress → RSS Feed

**Total Time:** 13-18 days (shorter - no Pinterest scheduling needed)  
**Total Cost:** ~$15 per 100 articles  
**External Image Hosts:** 0 (WordPress Media Library only)  
**Distribution:** RSS Feed (automatic, WordPress native)

---

## ⚡ QUICK SUMMARY

This system automatically:
1. Takes a keyword as input
2. Generates a full SEO-optimized article with recipe card
3. Creates Midjourney images (hero image)
4. Uploads all images to **WordPress Media Library** (not ImgBB, not external)
5. Publishes the article to WordPress with featured image
6. **Automatically updates WordPress RSS feed** (no external service needed)
7. RSS subscribers receive the article in their feed reader
8. Runs completely locally with zero manual intervention

---

## 📋 TABLE OF CONTENTS

1. [Phase 1: Foundation & Environment Setup](#phase-1-foundation--environment-setup)
2. [Phase 2: Database & State Management](#phase-2-database--state-management)
3. [Phase 3: LLM Client & Content Generation](#phase-3-llm-client--content-generation)
4. [Phase 4: Image Generation - Midjourney](#phase-4-image-generation--midjourney)
5. [Phase 5: Image Composition - Featured Image](#phase-5-image-composition--featured-image)
6. [Phase 6: WordPress Media Library Integration](#phase-6-wordpress-media-library-integration)
7. [Phase 7: WordPress Publishing & RSS](#phase-7-wordpress-publishing--rss)
8. [Phase 8: API Server & Web UI](#phase-8-api-server--web-ui)
9. [Master Timeline](#master-timeline)

---

# PHASE 1: FOUNDATION & ENVIRONMENT SETUP

**Duration:** 1-2 Days  
**Deliverables:** APIs connected, Redis running, environment ready

## 1.1 Create Project Structure

```bash
# Create root folder
mkdir content-automation-system && cd content-automation-system

# Create all sub-directories
mkdir -p orchestrator \
         content_engine \
         image_engine \
         compositor \
         publishers \
         utils \
         database \
         templates/fonts \
         data/cache \
         logs \
         tests \
         scripts \
         static

# Initialize Git
git init
echo "venv/
data/
*.env
logs/
__pycache__/
*.pyc" > .gitignore
```

## 1.2 Virtual Environment & Dependencies

```bash
# Create venv
python3 -m venv venv
source venv/bin/activate          # On Windows: venv\Scripts\activate

# Create requirements.txt
cat > requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn==0.24.0
celery==5.3.4
redis==5.0.1
pillow==10.1.0
requests==2.31.0
httpx==0.25.2
python-dotenv==1.0.0
sqlalchemy==2.0.23
pydantic==2.5.2
aiohttp==3.9.1
python-multipart==0.0.6
feedgen==0.9.0
EOF

# Install dependencies
pip install -r requirements.txt
```

## 1.3 Install & Start Redis

```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# Windows - use WSL or download from github.com/microsoftarchive/redis

# Verify Redis is running
redis-cli ping  # Should print: PONG
```

## 1.4 Register API Accounts

### OpenRouter (LLM Access)
- Go to: https://openrouter.ai/
- Sign up and get API key
- Cost: Pay-as-you-go (~$0.10 per 1M tokens for Gemini Flash)
- Save: `OPENROUTER_API_KEY=sk-or-v1-xxxxx`

### UseAPI.ai (Midjourney)
- Go to: https://www.useapi.net/
- Sign up and get API key
- Cost: ~$10 for 100 fast generations (or use relax mode free)
- Save: `USEAPI_KEY=xxxxx`

### WordPress Site
1. Go to WordPress Admin → Users → Profile
2. Scroll to "Application Passwords"
3. Create new password with username
4. Save: `WORDPRESS_APP_PASSWORD=xxxx xxxx xxxx xxxx`

**NOTE:** No Pinterest account needed - RSS is built into WordPress!

## 1.5 Create .env File

```bash
# Create .env file in project root
cat > .env << 'EOF'
# LLM API
OPENROUTER_API_KEY=sk-or-v1-xxxxx

# Image Generation
USEAPI_KEY=xxxxx

# WordPress (for Media Library uploads + post creation)
WORDPRESS_URL=https://yourblog.com
WORDPRESS_USERNAME=admin
WORDPRESS_APP_PASSWORD=xxxx xxxx xxxx xxxx

# NOTE: NO ImgBB, NO Pinterest API, NO Google Drive needed
# RSS feed is automatic with WordPress publishing
EOF

# IMPORTANT: Never commit .env to Git!
```

## 1.5.1 Current Project Setup

- `OPENROUTER_API_KEY` is configured locally for this project.
- `USEAPI_KEY` is intentionally skipped for now while Midjourney is on hold.
- `WORDPRESS_URL` should point to `https://chocokitchen.com/`.
- `WORDPRESS_USERNAME` should use the WordPress account email for this site.
- Keep real credentials only in `content-automation-system/.env`, not in Markdown files.

## 1.6 Verify API Connections

Create `tests/test_apis.py`:

```python
import os
import requests
import redis
from dotenv import load_dotenv

load_dotenv()

def test_openrouter():
    """Test OpenRouter API"""
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
            "Content-Type": "application/json"
        },
        json={
            "model": "google/gemini-2.0-flash-001",
            "messages": [{"role": "user", "content": "Say 'API works!'"}]
        }
    )
    assert response.status_code == 200, f"OpenRouter failed: {response.status_code}"
    print("✅ OpenRouter API connected")

def test_wordpress():
    """Test WordPress API"""
    import base64
    
    username = os.getenv('WORDPRESS_USERNAME')
    password = os.getenv('WORDPRESS_APP_PASSWORD')
    auth = base64.b64encode(f"{username}:{password}".encode()).decode()
    
    response = requests.get(
        f"{os.getenv('WORDPRESS_URL')}/wp-json/wp/v2/posts",
        headers={"Authorization": f"Basic {auth}"}
    )
    assert response.status_code == 200, f"WordPress failed: {response.status_code}"
    print("✅ WordPress API connected")

def test_redis():
    """Test Redis connection"""
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.set('test', 'ok')
    assert r.get('test') == b'ok', "Redis test failed"
    print("✅ Redis connected")

if __name__ == "__main__":
    test_openrouter()
    test_wordpress()
    test_redis()
    print("\n🎉 All APIs connected successfully!")
```

Run verification:

```bash
python tests/test_apis.py
```

## ✅ Phase 1 Completion Checklist

- [x] Project structure created with all folders (`content-automation-system/` with all subdirs)
- [x] `requirements.txt` created with all dependencies
- [x] `tests/test_apis.py` created
- [x] `.env.example` created with 5 required keys (no external image hosts)
- [ ] Python venv active and dependencies installed → `python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
- [ ] Redis installed and running → `brew install redis && brew services start redis` → verify: `redis-cli ping` returns PONG
- [ ] `.env` file created with real API keys → `cp .env.example .env` then fill in values
- [ ] `test_apis.py` passes all three checks → `python tests/test_apis.py` (needs real keys + Redis)

---

# PHASE 2: DATABASE & STATE MANAGEMENT

**Duration:** 1 Day  
**Deliverables:** SQLite schema, StateManager class, state tracking working

## 2.1 Database Schema

Create `database/schema.sql`:

```sql
-- Main job tracking table
CREATE TABLE IF NOT EXISTS content_jobs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword     TEXT NOT NULL,
    status      TEXT NOT NULL CHECK(status IN ('pending', 'processing', 'completed', 'failed', 'retrying')),
    stage       TEXT CHECK(stage IN (
                    'init', 'research', 'content_generation', 'image_generation',
                    'image_composition', 'wordpress_publish', 'rss_ready', 'complete'
                )),
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata    JSON DEFAULT '{}'
);

-- Intermediate artifacts (URLs, JSON, slugs, etc.)
CREATE TABLE IF NOT EXISTS content_artifacts (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id         INTEGER NOT NULL,
    artifact_type  TEXT NOT NULL,
    artifact_data  TEXT NOT NULL,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES content_jobs(id) ON DELETE CASCADE
);

-- Midjourney task tracking
CREATE TABLE IF NOT EXISTS midjourney_tasks (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id     INTEGER NOT NULL,
    task_id    TEXT NOT NULL,
    prompt     TEXT NOT NULL,
    status     TEXT CHECK(status IN ('submitted', 'processing', 'completed', 'failed')),
    image_urls JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES content_jobs(id) ON DELETE CASCADE
);

-- Published articles tracking
CREATE TABLE IF NOT EXISTS published_articles (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id         INTEGER NOT NULL,
    wordpress_id   INTEGER,
    title          TEXT NOT NULL,
    slug           TEXT NOT NULL,
    article_url    TEXT NOT NULL,
    rss_published  BOOLEAN DEFAULT 1,
    published_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES content_jobs(id) ON DELETE CASCADE
);

-- Error log for retry tracking
CREATE TABLE IF NOT EXISTS error_log (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id        INTEGER NOT NULL,
    stage         TEXT,
    error_type    TEXT NOT NULL,
    error_message TEXT NOT NULL,
    retry_count   INTEGER DEFAULT 0,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES content_jobs(id) ON DELETE CASCADE
);

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_jobs_status ON content_jobs(status);
CREATE INDEX IF NOT EXISTS idx_articles_published ON published_articles(rss_published);
```

## 2.2 StateManager Class

Create `orchestrator/state_manager.py`:

```python
import sqlite3
import json
from datetime import datetime
from enum import Enum
from pathlib import Path

class JobStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"

class Stage(Enum):
    INIT = "init"
    RESEARCH = "research"
    CONTENT_GEN = "content_generation"
    IMAGE_GEN = "image_generation"
    IMAGE_COMP = "image_composition"
    WP_PUBLISH = "wordpress_publish"
    RSS_READY = "rss_ready"
    COMPLETE = "complete"

class StateManager:
    def __init__(self, db_path="data/state.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.init_db()
    
    def init_db(self):
        """Initialize database from schema"""
        with open('database/schema.sql', 'r') as f:
            self.conn.executescript(f.read())
        self.conn.commit()
    
    def create_job(self, keyword):
        """Create new job"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO content_jobs (keyword, status, stage, metadata)
            VALUES (?, ?, ?, ?)
        """, (keyword, JobStatus.PENDING.value, Stage.INIT.value, json.dumps({})))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_job(self, job_id, status=None, stage=None, metadata=None):
        """Update job status, stage, or metadata"""
        updates = []
        params = []
        
        if status:
            updates.append("status = ?")
            params.append(status.value if isinstance(status, JobStatus) else status)
        if stage:
            updates.append("stage = ?")
            params.append(stage.value if isinstance(stage, Stage) else stage)
        if metadata:
            existing = self.get_job_metadata(job_id)
            existing.update(metadata)
            updates.append("metadata = ?")
            params.append(json.dumps(existing))
        
        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.append(job_id)
        
        cursor = self.conn.cursor()
        cursor.execute(f"""
            UPDATE content_jobs
            SET {', '.join(updates)}
            WHERE id = ?
        """, params)
        self.conn.commit()
    
    def save_artifact(self, job_id, artifact_type, artifact_data):
        """Store intermediate artifact"""
        cursor = self.conn.cursor()
        data_str = json.dumps(artifact_data) if isinstance(artifact_data, (dict, list)) else str(artifact_data)
        cursor.execute("""
            INSERT INTO content_artifacts (job_id, artifact_type, artifact_data)
            VALUES (?, ?, ?)
        """, (job_id, artifact_type, data_str))
        self.conn.commit()
    
    def save_published_article(self, job_id, wordpress_id, title, slug, article_url):
        """Save published article info"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO published_articles (job_id, wordpress_id, title, slug, article_url, rss_published)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (job_id, wordpress_id, title, slug, article_url))
        self.conn.commit()
    
    def get_job_metadata(self, job_id):
        """Get current metadata JSON"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT metadata FROM content_jobs WHERE id = ?", (job_id,))
        result = cursor.fetchone()
        return json.loads(result[0]) if result else {}
    
    def get_job_status(self, job_id):
        """Get full job row for API response"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT keyword, status, stage, updated_at, metadata
            FROM content_jobs WHERE id = ?
        """, (job_id,))
        return cursor.fetchone()
    
    def log_error(self, job_id, stage, error_type, error_message, retry_count=0):
        """Log error for debugging"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO error_log (job_id, stage, error_type, error_message, retry_count)
            VALUES (?, ?, ?, ?, ?)
        """, (job_id, stage, error_type, error_message, retry_count))
        self.conn.commit()
```

## 2.3 Test StateManager

Create `tests/test_state_manager.py`:

```python
from orchestrator.state_manager import StateManager, JobStatus, Stage

def test_state_manager():
    sm = StateManager("data/test.db")
    
    # Create job
    job_id = sm.create_job("chocolate chip cookies")
    print(f"Created job: {job_id}")
    
    # Update job
    sm.update_job(job_id, status=JobStatus.PROCESSING, stage=Stage.RESEARCH)
    
    # Save artifact
    sm.save_artifact(job_id, "test_artifact", {"key": "value"})
    
    # Get status
    status = sm.get_job_status(job_id)
    print(f"Status: {status}")
    
    # Log error
    sm.log_error(job_id, "test_stage", "TestError", "This is a test", 1)
    
    print("✅ State manager working!")

if __name__ == "__main__":
    test_state_manager()
```

Run test:

```bash
python tests/test_state_manager.py
```

## ✅ Phase 2 Completion Checklist

- [x] `database/schema.sql` creates all tables (content_jobs, content_artifacts, midjourney_tasks, wordpress_posts, error_log) with indexes
- [x] `StateManager` CRUD methods implemented (create, update, save_artifact, get_artifact, list_jobs, log_error)
- [x] `JobStatus` and `Stage` enums defined
- [x] `test_state_manager.py` passes all checks ✅

---

# PHASE 3: LLM CLIENT & CONTENT GENERATION

**Duration:** 2-3 Days  
**Deliverables:** Article generation from keyword, recipe JSON, SEO metadata

## 3.1 LLM Client

Create `content_engine/llm_client.py`:

```python
import httpx
import json
import re
from typing import Dict

class LLMClient:
    def __init__(self, api_key: str, model: str = "google/gemini-2.0-flash-001"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
    
    async def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 4000) -> str:
        """Call LLM and get response"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    
    def parse_json(self, response: str) -> Dict:
        """Parse JSON from LLM response"""
        clean = re.sub(r'```json\s*|\s*```', '', response.strip())
        try:
            return json.loads(clean)
        except json.JSONDecodeError:
            match = re.search(r'[\[{].*[}\]]', clean, re.DOTALL)
            if match:
                return json.loads(match.group())
            raise ValueError(f"Failed to parse JSON from: {response[:200]}")
```

## 3.2 Article Generator

Create `content_engine/article_generator.py`:

```python
import asyncio
from .llm_client import LLMClient

class ArticleGenerator:
    def __init__(self, api_key: str):
        self.llm = LLMClient(api_key)
    
    async def generate_outline(self, keyword: str):
        """Generate article outline"""
        prompt = f"""Create an outline for a recipe article about: {keyword}

Output JSON array with objects like:
[
    {{"level": "h2", "title": "Introduction", "word_count": 200}},
    {{"level": "h2", "title": "Ingredients Overview", "word_count": 150}},
    ...
]"""
        
        response = await self.llm.generate(prompt, temperature=0.6)
        return self.llm.parse_json(response)
    
    async def generate_section(self, section: dict, keyword: str) -> str:
        """Generate content for one section"""
        prompt = f"""Write {section['word_count']} words for section: {section['title']}
Article topic: {keyword}
Level: {section['level']}

Guidelines:
- Conversational tone
- Use "you" and "your"
- Short sentences (15-20 words avg)
- Active voice
- No clichés or overused phrases

Output only the section text (no HTML, no markdown)."""
        
        return await self.llm.generate(prompt, temperature=0.8, max_tokens=600)
    
    async def generate_complete_article(self, keyword: str) -> dict:
        """Full article generation pipeline"""
        print(f"Generating outline for: {keyword}")
        outline = await self.generate_outline(keyword)
        
        print("Generating sections...")
        sections = []
        for section in outline:
            content = await self.generate_section(section, keyword)
            sections.append({
                "level": section["level"],
                "title": section["title"],
                "content": content
            })
        
        # Generate SEO metadata
        title_prompt = f"""Write an SEO title for {keyword} article under 60 characters.
Must include keyword naturally. Include a number and a power word.
Respond with ONLY the title (no quotes, no formatting)."""
        title = await self.llm.generate(title_prompt, temperature=0.5, max_tokens=100)
        
        return {
            "keyword": keyword,
            "title": title.strip(),
            "outline": outline,
            "sections": sections
        }
```

## 3.3 Test Content Generation

Create `tests/test_content_gen.py`:

```python
import asyncio
import os
from dotenv import load_dotenv
from content_engine.article_generator import ArticleGenerator

load_dotenv()

async def test():
    gen = ArticleGenerator(os.getenv('OPENROUTER_API_KEY'))
    result = await gen.generate_complete_article('chocolate chip cookies')
    
    print(f"Title: {result['title']} ({len(result['title'])} chars)")
    assert len(result['title']) <= 60, "Title must be under 60 chars"
    
    print(f"Sections generated: {len(result['sections'])}")
    print("✅ Content generation OK")

if __name__ == "__main__":
    asyncio.run(test())
```

Run test:

```bash
python tests/test_content_gen.py
```

## ✅ Phase 3 Completion Checklist

- [x] `content_engine/llm_client.py` — `generate()` + `parse_json()` implemented
- [x] `content_engine/article_generator.py` — outline, sections, SEO metadata, recipe card, HTML output
- [x] `tests/test_content_gen.py` created with assertions for title length, meta desc, sections, HTML, recipe card
- [ ] Run `python tests/test_content_gen.py` with real `OPENROUTER_API_KEY` in `.env` to confirm all checks pass

---

# PHASE 4: IMAGE GENERATION - MIDJOURNEY

**Duration:** 2 Days  
**Deliverables:** Hero image downloaded from Midjourney

## 4.1 Midjourney Client

Create `image_engine/midjourney_client.py`:

```python
import asyncio
import httpx
from typing import Dict

class MidjourneyClient:
    def __init__(self, api_key: str, provider: str = "useapi"):
        self.api_key = api_key
        self.provider = provider
        self.base_url = "https://api.useapi.net/v2"
        self.imagine_endpoint = f"{self.base_url}/jobs/imagine"
        self.status_endpoint = f"{self.base_url}/jobs"
        self.button_endpoint = f"{self.base_url}/jobs/button"
    
    async def generate_images(self, prompt: str, aspect_ratio: str = "1:1") -> Dict:
        """Submit Midjourney generation request"""
        full_prompt = f"{prompt} --ar {aspect_ratio} --s 100 --v 7"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.imagine_endpoint,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"prompt": full_prompt},
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "task_id": data["jobid"],
                "status": "processing",
                "prompt": full_prompt
            }
    
    async def get_status(self, task_id: str) -> Dict:
        """Poll for job status"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.status_endpoint}/{task_id}",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    
    async def wait_for_completion(self, task_id: str, max_wait: int = 900) -> Dict:
        """Poll until image is ready (max 15 min)"""
        start_time = asyncio.get_event_loop().time()
        
        while True:
            if asyncio.get_event_loop().time() - start_time > max_wait:
                raise TimeoutError(f"Midjourney task {task_id} timed out")
            
            status = await self.get_status(task_id)
            
            if status["status"] == "completed":
                return {
                    "task_id": task_id,
                    "image_url": status["result"]["url"]
                }
            elif status["status"] == "failed":
                raise Exception(f"Generation failed: {status.get('error')}")
            
            await asyncio.sleep(10)
    
    async def generate_hero_image(self, prompt: str) -> Dict:
        """Generate hero image for article"""
        # Step 1: Generate
        task = await self.generate_images(prompt, aspect_ratio="16:9")
        print(f"Midjourney task: {task['task_id']}")
        
        # Step 2: Wait for completion
        result = await self.wait_for_completion(task["task_id"])
        print(f"Hero image ready: {result['image_url']}")
        
        return result
```

## 4.2 Test Midjourney Client

Create `tests/test_midjourney.py`:

```python
import asyncio
import os
from dotenv import load_dotenv
from image_engine.midjourney_client import MidjourneyClient

load_dotenv()

async def test():
    client = MidjourneyClient(os.getenv("USEAPI_KEY"))
    
    # Generate hero image
    prompt = "chocolate chip cookies, food photography, close-up, 16:9 aspect ratio"
    result = await client.generate_hero_image(prompt)
    
    print(f"Hero Image URL: {result['image_url']}")
    print("✅ Midjourney integration OK")

if __name__ == "__main__":
    asyncio.run(test())
```

## ✅ Phase 4 Completion Checklist

- [ ] MidjourneyClient submits job and gets task_id
- [ ] Polling loop returns when status == 'completed'
- [ ] Hero image URL is valid and accessible
- [ ] Image downloads successfully

---

# PHASE 5: IMAGE COMPOSITION - FEATURED IMAGE

**Duration:** 1 Day  
**Deliverables:** Hero image prepared for WordPress featured image

## 5.1 Download Google Fonts (Optional - for enhancement)

```bash
cd templates/fonts

# Optional: Download Montserrat Bold for text overlay
wget 'https://github.com/google/fonts/raw/main/ofl/montserrat/static/Montserrat-Bold.ttf'

ls -lh
```

## 5.2 Featured Image Handler

Create `compositor/featured_image_handler.py`:

```python
import requests
from PIL import Image
from io import BytesIO
from pathlib import Path

class FeaturedImageHandler:
    """Handle hero image from Midjourney"""
    
    @staticmethod
    def download_hero_image(url: str, job_id: int, cache_dir: str = "data/cache") -> str:
        """Download hero image and cache locally"""
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        
        # Download
        print(f"Downloading hero image from Midjourney: {url}")
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        # Save to cache
        cache_path = f"{cache_dir}/{job_id}_hero.jpg"
        with open(cache_path, 'wb') as f:
            f.write(response.content)
        
        print(f"Cached: {cache_path}")
        return cache_path
    
    @staticmethod
    def get_image_info(file_path: str) -> dict:
        """Get image dimensions and info"""
        img = Image.open(file_path)
        return {
            "width": img.width,
            "height": img.height,
            "format": img.format,
            "size_kb": Path(file_path).stat().st_size / 1024
        }
```

## ✅ Phase 5 Completion Checklist

- [x] `compositor/featured_image_handler.py` — download, centre-crop to 1200×800, optimise to ≤300 KB, cleanup
- [x] `tests/test_featured_image.py` — validates dimensions, file size, and cleanup
- [x] Test passes: 1200×800 @ 209 KB ✅

---

# PHASE 6: WORDPRESS MEDIA LIBRARY INTEGRATION

**Duration:** 2 Days  
**Deliverables:** All images uploaded to WordPress, no external hosts

## 6.1 WordPress Publisher - CRITICAL PHASE

Create `publishers/wordpress.py`:

```python
import requests
import base64
from typing import Dict
from pathlib import Path
import mimetypes

class WordPressPublisher:
    def __init__(self, site_url: str, username: str, app_password: str):
        self.site_url = site_url.rstrip('/')
        self.api_base = f"{self.site_url}/wp-json/wp/v2"
        self.auth = self._create_auth(username, app_password)
    
    def _create_auth(self, username: str, password: str) -> str:
        """Create Basic Auth header"""
        credentials = f"{username}:{password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"
    
    def upload_media_from_url(self, image_url: str, filename: str, 
                             alt_text: str = "", title: str = "") -> Dict:
        """
        Download image from URL and upload to WordPress Media Library
        
        Returns: { id, source_url, alt_text, width, height }
        """
        # Download image
        print(f"Downloading image from: {image_url}")
        img_response = requests.get(image_url, timeout=60)
        img_response.raise_for_status()
        image_data = img_response.content
        
        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(filename)
        if not mime_type:
            mime_type = "image/jpeg"
        
        # Upload to WordPress
        print(f"Uploading to WordPress: {filename}")
        headers = {
            "Authorization": self.auth,
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": mime_type
        }
        
        response = requests.post(
            f"{self.api_base}/media",
            headers=headers,
            data=image_data,
            timeout=120
        )
        response.raise_for_status()
        media_data = response.json()
        
        # Update metadata
        media_id = media_data["id"]
        if alt_text or title:
            self.update_media_metadata(media_id, alt_text=alt_text, title=title)
        
        return {
            "id": media_id,
            "source_url": media_data["source_url"],
            "alt_text": alt_text,
            "width": media_data.get("media_details", {}).get("width", 0),
            "height": media_data.get("media_details", {}).get("height", 0)
        }
    
    def upload_media_from_file(self, file_path: str, filename: str = None,
                              alt_text: str = "", title: str = "") -> Dict:
        """Upload local file to WordPress Media Library"""
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not filename:
            filename = file_path_obj.name
        
        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(filename)
        if not mime_type:
            mime_type = "image/jpeg"
        
        # Upload
        print(f"Uploading local file to WordPress: {filename}")
        headers = {
            "Authorization": self.auth,
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": mime_type
        }
        
        response = requests.post(
            f"{self.api_base}/media",
            headers=headers,
            data=file_path_obj.read_bytes(),
            timeout=120
        )
        response.raise_for_status()
        media_data = response.json()
        
        # Update metadata
        media_id = media_data["id"]
        if alt_text or title:
            self.update_media_metadata(media_id, alt_text=alt_text, title=title)
        
        return {
            "id": media_id,
            "source_url": media_data["source_url"],
            "alt_text": alt_text,
            "width": media_data.get("media_details", {}).get("width", 0),
            "height": media_data.get("media_details", {}).get("height", 0)
        }
    
    def update_media_metadata(self, media_id: int, alt_text: str = None, 
                             title: str = None) -> Dict:
        """Update media alt text and title"""
        updates = {}
        
        if alt_text is not None:
            updates["alt_text"] = alt_text
        if title is not None:
            updates["title"] = title
        
        if not updates:
            return {}
        
        headers = {
            "Authorization": self.auth,
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{self.api_base}/media/{media_id}",
            headers=headers,
            json=updates,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    
    def create_post(self, title: str, content: str, slug: str,
                   meta_description: str, featured_image_id: int,
                   categories: list, recipe_json: dict = None,
                   status: str = "draft") -> Dict:
        """Create WordPress post (automatically added to RSS feed)"""
        post_data = {
            "title": title,
            "content": content,
            "slug": slug,
            "status": status,
            "featured_media": featured_image_id,
            "categories": categories,
            "meta": {
                "rank_math_description": meta_description,
                "_yoast_wpseo_metadesc": meta_description,
            }
        }
        
        if recipe_json:
            post_data["meta"]["wprm_recipe"] = recipe_json
        
        headers = {
            "Authorization": self.auth,
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{self.api_base}/posts",
            headers=headers,
            json=post_data,
            timeout=60
        )
        response.raise_for_status()
        return response.json()
    
    def get_category_id(self, category_name: str) -> int:
        """Get category ID by name, create if doesn't exist"""
        # Search existing
        response = requests.get(
            f"{self.api_base}/categories",
            params={"search": category_name},
            timeout=30
        )
        response.raise_for_status()
        categories = response.json()
        
        if categories:
            return categories[0]["id"]
        
        # Create new
        headers = {
            "Authorization": self.auth,
            "Content-Type": "application/json"
        }
        response = requests.post(
            f"{self.api_base}/categories",
            headers=headers,
            json={"name": category_name},
            timeout=30
        )
        response.raise_for_status()
        return response.json()["id"]
    
    def generate_seo_filename(self, slug: str, image_type: str) -> str:
        """Generate SEO-friendly filename"""
        return f"{slug}-{image_type}.jpg"
```

## 6.2 Test WordPress Media Upload

Create `tests/test_wordpress_media.py`:

```python
import os
from dotenv import load_dotenv
from publishers.wordpress import WordPressPublisher
from PIL import Image

load_dotenv()

def test_media_upload():
    wp = WordPressPublisher(
        os.getenv('WORDPRESS_URL'),
        os.getenv('WORDPRESS_USERNAME'),
        os.getenv('WORDPRESS_APP_PASSWORD'),
    )
    
    # Test 1: Upload from URL
    print("Test 1: Upload from URL")
    result = wp.upload_media_from_url(
        image_url='https://picsum.photos/800/600',
        filename='test-hero.jpg',
        alt_text='Test hero image',
        title='Test Hero',
    )
    print(f"Media ID: {result['id']}")
    print(f"URL: {result['source_url']}")
    assert result['source_url'].startswith('https'), "URL must be HTTPS"
    print("✅ upload_media_from_url OK")
    
    # Test 2: Upload local file
    print("\nTest 2: Upload local file")
    Image.new('RGB', (800, 600), 'blue').save('/tmp/test_hero.jpg')
    result2 = wp.upload_media_from_file(
        file_path='/tmp/test_hero.jpg',
        filename='test-hero-local.jpg',
        alt_text='Test hero'
    )
    print(f"Hero URL: {result2['source_url']}")
    assert result2['source_url'].startswith('https')
    print("✅ upload_media_from_file OK")

if __name__ == "__main__":
    test_media_upload()
```

Run test:

```bash
python tests/test_wordpress_media.py
```

## ✅ Phase 6 Completion Checklist

- [x] `publishers/wordpress.py` built — upload from URL, upload from file, update metadata, create post, get/create category, verify connection
- [x] `tests/test_wordpress.py` created — covers connection, both upload methods, draft post creation, SEO filename
- [ ] Run `python tests/test_wordpress.py` with real credentials in `.env` to confirm all checks pass against chocokitchen.com
- [ ] grep -r 'imgbb' . returns ZERO matches

---

# PHASE 7: WORDPRESS PUBLISHING & RSS

**Duration:** 1-2 Days  
**Deliverables:** Articles published, RSS feed automatic

## 7.1 Celery Configuration

Create `celeryconfig.py`:

```python
broker_url = 'redis://localhost:6379/0'
result_backend = 'redis://localhost:6379/0'
task_serializer = 'json'
accept_content = ['json']
result_serializer = 'json'
timezone = 'UTC'
enable_utc = True
task_track_started = True
task_time_limit = 3600    # 1 hour
task_soft_time_limit = 3300  # Soft limit
```

## 7.2 Retry Logic

Create `utils/retry_logic.py`:

```python
import time
import functools
from typing import Callable

def retry_with_backoff(max_retries=3, base_delay=5, max_delay=300, exceptions=(Exception,)):
    """Exponential backoff retry decorator"""
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    retries += 1
                    if retries >= max_retries:
                        raise
                    
                    delay = min(base_delay * (2 ** retries), max_delay)
                    print(f"Retry {retries}/{max_retries} after {delay}s: {e}")
                    time.sleep(delay)
        
        return wrapper
    return decorator
```

## 7.3 RSS Feed Handler

Create `publishers/rss_handler.py`:

```python
"""
RSS Feed Handler - Automatic with WordPress

When you publish a post to WordPress, it is automatically:
1. Added to the WordPress RSS feed
2. Available at: https://yourblog.com/feed/
3. Pickupable by RSS readers (Feedly, Apple Podcasts, etc.)

No additional action needed - WordPress handles this automatically!
"""

class RSSFeedHandler:
    """
    WordPress automatically manages RSS feeds.
    
    Your published posts are automatically available at:
    - Main feed: /feed/
    - Category feeds: /category/dinner/feed/
    - Author feeds: /author/admin/feed/
    - Custom post type feeds (if enabled)
    
    Subscribers will automatically receive new articles in their RSS readers.
    """
    
    @staticmethod
    def get_feed_url(wordpress_url: str, feed_type: str = "main") -> str:
        """Get RSS feed URL"""
        base_url = wordpress_url.rstrip('/')
        
        if feed_type == "main":
            return f"{base_url}/feed/"
        elif feed_type == "recipes":
            return f"{base_url}/category/recipes/feed/"
        elif feed_type == "json":
            return f"{base_url}/wp-json/wp/v2/posts"
        
        return f"{base_url}/feed/"
    
    @staticmethod
    def verify_rss_feed_setup(wordpress_url: str) -> dict:
        """Verify RSS feed is properly configured in WordPress"""
        import requests
        
        base_url = wordpress_url.rstrip('/')
        feed_url = f"{base_url}/feed/"
        
        try:
            response = requests.get(feed_url, timeout=10)
            if response.status_code == 200:
                return {
                    "status": "active",
                    "feed_url": feed_url,
                    "message": "RSS feed is active and working"
                }
            else:
                return {
                    "status": "error",
                    "feed_url": feed_url,
                    "message": f"Feed returned status {response.status_code}"
                }
        except Exception as e:
            return {
                "status": "error",
                "feed_url": feed_url,
                "message": f"Feed check failed: {str(e)}"
            }
```

## 7.4 Pipeline Tasks

Create `orchestrator/pipeline.py`:

```python
from celery import Celery
from orchestrator.state_manager import StateManager, JobStatus, Stage
from utils.retry_logic import retry_with_backoff
import asyncio

app = Celery('content_automation')
app.config_from_object('celeryconfig')

@app.task(bind=True, max_retries=3)
@retry_with_backoff(max_retries=3, base_delay=5)
def research_stage(self, job_id: int, keyword: str, config: dict):
    """Stage 1: Keyword research"""
    state = StateManager(config['db_path'])
    state.update_job(job_id, stage=Stage.RESEARCH)
    
    metadata = {
        "search_intent": "informational",
        "category": "Dinner",
    }
    
    state.save_artifact(job_id, "research_metadata", metadata)
    return {"job_id": job_id, "keyword": keyword, "metadata": metadata}

@app.task(bind=True, max_retries=3)
@retry_with_backoff(max_retries=3, base_delay=10)
def content_generation_stage(self, prev_result: dict, job_id: int, config: dict):
    """Stage 2: Generate article"""
    state = StateManager(config['db_path'])
    state.update_job(job_id, stage=Stage.CONTENT_GEN)
    
    # TODO: Call ArticleGenerator
    article_data = {
        "title": "Chocolate Chip Cookies",
        "slug": "chocolate-chip-cookies",
        "meta_description": "Learn how to make perfect chocolate chip cookies",
        "html_content": "<h2>Recipe</h2>...",
        "recipe_json": {}
    }
    
    state.save_artifact(job_id, "article_title", article_data["title"])
    state.save_artifact(job_id, "article_slug", article_data["slug"])
    
    return {**prev_result, "article": article_data}

@app.task(bind=True, max_retries=3)
@retry_with_backoff(max_retries=3, base_delay=5)
def wordpress_publish_stage(self, prev_result: dict, job_id: int, config: dict):
    """Stage 3: Publish to WordPress (auto-adds to RSS)"""
    state = StateManager(config['db_path'])
    state.update_job(job_id, stage=Stage.WP_PUBLISH)
    
    # TODO: Call WordPressPublisher.create_post()
    
    state.update_job(job_id, stage=Stage.RSS_READY)
    return {**prev_result, "published": True, "rss_active": True}

@app.task(bind=True)
def complete_stage(self, prev_result: dict, job_id: int, config: dict):
    """Stage 4: Mark as complete"""
    state = StateManager(config['db_path'])
    state.update_job(job_id, status=JobStatus.COMPLETED, stage=Stage.COMPLETE)
    
    return {**prev_result, "status": "complete"}
```

## 7.5 How RSS Feed Works

**When you publish a post to WordPress:**

1. Post is created with `/wp-json/wp/v2/posts`
2. WordPress automatically:
   - Adds it to the RSS feed at `/feed/`
   - Makes it available in category feeds (if assigned)
   - Updates the JSON feed at `/wp-json/wp/v2/posts`
   - Notifies any RSS readers subscribed to your blog

**RSS Feed URLs:**

- Main feed: `https://yourblog.com/feed/`
- Category feed: `https://yourblog.com/category/recipes/feed/`
- JSON feed: `https://yourblog.com/wp-json/wp/v2/posts`

**RSS Subscribers Receive:**

- Article title
- Article slug (link to full post)
- Excerpt or full content
- Featured image
- Publication date
- Author

**No Additional Configuration Needed** - it's all built into WordPress!

## ✅ Phase 7 Completion Checklist

- [x] `celeryconfig.py` — broker, backend, timeouts, late-ack configured
- [x] `utils/retry_logic.py` — exponential backoff decorator, tested ✅
- [x] `publishers/rss_handler.py` — feed URL helpers + live verify (handles Yoast disable)
- [x] `orchestrator/pipeline.py` — full 4-task chain wired to Phase 3/5/6 classes
- [x] `tests/test_pipeline.py` — retry logic unit tests pass ✅
- [ ] Start Redis + Celery worker: `celery -A orchestrator.pipeline worker --loglevel=info`
- [ ] Run end-to-end: `python -c "from orchestrator.pipeline import run_pipeline; run_pipeline(1, 'chocolate lava cake')"`
- [ ] Enable RSS in Yoast SEO → Search Appearance → RSS (currently disabled on chocokitchen.com)

---

# PHASE 8: API SERVER & WEB UI

**Duration:** 1-2 Days  
**Deliverables:** Browser UI, full end-to-end testing

## 8.1 FastAPI Server

Create `main.py`:

```python
from fastapi import FastAPI, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from orchestrator.pipeline import process_keyword
from orchestrator.state_manager import StateManager
from config import CONFIG
import json

app = FastAPI(title="Content Automation System")
state_manager = StateManager(CONFIG["db_path"])

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    """Serve web UI"""
    return FileResponse("static/index.html")

@app.post("/generate")
async def generate_content(keyword: str, background_tasks: BackgroundTasks):
    """Start pipeline"""
    job_id = state_manager.create_job(keyword)
    
    # Queue async task
    # background_tasks.add_task(process_keyword.delay, job_id, keyword, CONFIG)
    
    return {
        "job_id": job_id,
        "keyword": keyword,
        "status": "queued",
        "message": f"Pipeline started for '{keyword}'"
    }

@app.get("/status/{job_id}")
async def get_status(job_id: int):
    """Check job status"""
    result = state_manager.get_job_status(job_id)
    if not result:
        return {"error": "Job not found"}
    
    return {
        "job_id": job_id,
        "keyword": result[0],
        "status": result[1],
        "current_stage": result[2],
        "updated_at": result[3],
        "metadata": json.loads(result[4])
    }

@app.get("/artifacts/{job_id}")
async def get_artifacts(job_id: int):
    """Get all generated artifacts"""
    cursor = state_manager.conn.cursor()
    cursor.execute("""
        SELECT artifact_type, artifact_data
        FROM content_artifacts
        WHERE job_id = ?
    """, (job_id,))
    
    artifacts = {}
    for row in cursor.fetchall():
        artifacts[row[0]] = row[1]
    
    return {"job_id": job_id, "artifacts": artifacts}

@app.get("/feed")
async def get_rss_feed_status():
    """Check RSS feed status"""
    from publishers.rss_handler import RSSFeedHandler
    
    status = RSSFeedHandler.verify_rss_feed_setup(CONFIG["wordpress_url"])
    return status

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## 8.2 Web UI

Create `static/index.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Content Automation System</title>
    <style>
        body { font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px; }
        h1 { color: #2563EB; }
        input { padding: 10px; width: 300px; margin: 10px 0; font-size: 16px; border: 1px solid #ccc; border-radius: 4px; }
        button { padding: 10px 20px; background: #2563EB; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; margin: 5px; }
        button:hover { background: #1d4ed8; }
        #status { margin-top: 30px; padding: 15px; background: #f0f0f0; border-radius: 5px; font-family: monospace; white-space: pre-wrap; }
        .success { color: #16a34a; background: #f0fdf4; padding: 15px; border-radius: 5px; margin: 10px 0; }
        .loading { color: #ea580c; background: #fefce8; padding: 15px; border-radius: 5px; margin: 10px 0; }
        .error { color: #dc2626; background: #fef2f2; padding: 15px; border-radius: 5px; margin: 10px 0; }
        .info { background: #eff6ff; padding: 15px; border-left: 4px solid #2563EB; margin: 15px 0; }
    </style>
</head>
<body>
    <h1>🤖 Content Automation System</h1>
    <p>Enter a keyword and the system will automatically generate a full article and publish it to WordPress. The article will automatically appear in your RSS feed!</p>
    
    <div class="info">
        <strong>📡 RSS Feed Enabled</strong><br>
        Published articles automatically appear in your WordPress RSS feed at /feed/
    </div>
    
    <input type="text" id="keyword" placeholder="Enter keyword (e.g., chocolate chip cookies)">
    <button onclick="generate()">🚀 Generate & Publish</button>
    <button onclick="checkFeed()">📡 Check RSS Feed</button>
    
    <div id="status"></div>
    
    <script>
        async function generate() {
            const keyword = document.getElementById('keyword').value;
            if (!keyword) {
                alert('Please enter a keyword');
                return;
            }
            
            document.getElementById('status').innerHTML = '';
            
            const response = await fetch(`/generate?keyword=${encodeURIComponent(keyword)}`, 
                {method: 'POST'});
            const data = await response.json();
            
            document.getElementById('status').innerHTML = 
                `<div class="loading">🔄 Job ID: ${data.job_id}\nStatus: ${data.status}\nGenerating content...</div>`;
            
            checkStatus(data.job_id);
        }
        
        async function checkStatus(jobId) {
            const response = await fetch(`/status/${jobId}`);
            const data = await response.json();
            
            if (data.error) {
                document.getElementById('status').innerHTML = 
                    `<div class="error">❌ Error: ${data.error}</div>`;
                return;
            }
            
            const statusClass = data.status === 'completed' ? 'success' : 'loading';
            const icon = data.status === 'completed' ? '✅' : '🔄';
            
            document.getElementById('status').innerHTML = 
                `<div class="${statusClass}">
${icon} Job: ${jobId}
Keyword: ${data.keyword}
Status: ${data.status}
Stage: ${data.current_stage}
Updated: ${data.updated_at}
                </div>`;
            
            if (data.status !== 'completed' && data.status !== 'failed') {
                setTimeout(() => checkStatus(jobId), 5000);
            } else if (data.status === 'completed') {
                document.getElementById('status').innerHTML += 
                    `<div class="success">✅ Article published to WordPress!
📡 It's automatically in your RSS feed now.</div>`;
            }
        }
        
        async function checkFeed() {
            const response = await fetch('/feed');
            const data = await response.json();
            
            if (data.status === 'active') {
                document.getElementById('status').innerHTML = 
                    `<div class="success">✅ RSS Feed Active
URL: ${data.feed_url}
${data.message}</div>`;
            } else {
                document.getElementById('status').innerHTML = 
                    `<div class="error">❌ RSS Feed Error
${data.message}</div>`;
            }
        }
    </script>
</body>
</html>
```

## 8.3 Start Commands

```bash
# Terminal 1: Redis
redis-server

# Terminal 2: Celery Worker
source venv/bin/activate
celery -A orchestrator.pipeline worker --loglevel=info --concurrency=2

# Terminal 3: FastAPI Server
source venv/bin/activate
python main.py
```

Then open browser: http://localhost:8000

## 8.4 Test via CLI

```bash
# Submit keyword
curl -X POST 'http://localhost:8000/generate?keyword=chocolate%20chip%20cookies'

# Response: { "job_id": 1, "status": "queued" }

# Poll status
curl 'http://localhost:8000/status/1'

# Check RSS feed
curl 'http://localhost:8000/feed'

# Access your WordPress RSS feed
open https://yourblog.com/feed/
```

## ✅ Phase 8 Completion Checklist

- [x] `config.py` — loads all env vars into one CONFIG dict
- [x] `main.py` — FastAPI server with `/generate`, `/status/{id}`, `/jobs`, `/artifacts/{id}`, `/feed`
- [x] `static/index.html` — full UI: keyword input, live status polling, jobs table, RSS check
- [x] Server starts and all endpoints respond correctly ✅
- [x] Graceful 503 when Redis/Celery not running (job still saved to DB)
- [ ] Start Redis + Celery worker, then run `python main.py` and open http://localhost:8000
- [ ] Submit a real keyword and confirm WordPress post is published

---

# MASTER TIMELINE

| Phase | Name | Duration | Deliverable |
|-------|------|----------|-------------|
| 1 | Foundation & Environment | 1-2 days | APIs connected, Redis running |
| 2 | Database & State | 1 day | SQLite schema, StateManager |
| 3 | LLM & Content | 2-3 days | Full article generation |
| 4 | Midjourney | 2 days | Hero image URL |
| 5 | Image Handling | 1 day | Hero image cached |
| 6 | WordPress Media | 2 days | Images uploaded to WP |
| 7 | WordPress & RSS | 1-2 days | Articles published, RSS active |
| 8 | API & Web UI | 1-2 days | Browser UI + integration test |
| **TOTAL** | | **13-18 days** | **Production-ready system** |

## Cost Per 100 Articles

| Service | Usage | Cost |
|---------|-------|------|
| OpenRouter (Gemini Flash) | ~500K tokens | ~$15.00 |
| UseAPI.ai (Midjourney Relax) | 1 job × 100 articles | ~$10.00 |
| WordPress Hosting | Media + bandwidth | $0 (already paid) |
| Redis + Celery + SQLite | Local | $0 |
| RSS Feed | WordPress native | $0 |
| **TOTAL** | | **~$25.00** |

## MVP Fast Track (7-10 Days)

If you want a working system faster:

1. **Phase 1** (Day 1) - Environment setup
2. **Phase 2** (Day 1) - Database
3. **Phase 3** (Days 2-3) - Article generation
4. **Phase 6** (Days 4-5) - WordPress publishing
5. **Phase 8** (Days 6-7) - Web UI + integration

Then add Phases 4-5 (Midjourney images) and Phase 7 (RSS verification) later.

---

# ✅ FINAL VERIFICATION CHECKLIST

Before deploying to production:

## Environment & Security
- [ ] .env file is NOT committed to Git
- [ ] API keys rotated if accidentally exposed
- [ ] Redis runs on localhost only
- [ ] Python venv active before running scripts

## Database
- [ ] All 5 tables created with correct schema
- [ ] Indexes on status exist
- [ ] State transitions work: pending → processing → completed/failed
- [ ] Error log captures all failures with retry_count

## Content Generation
- [ ] Article title always under 60 characters
- [ ] Meta description always 150-160 characters
- [ ] Recipe JSON (if used) validates correctly
- [ ] HTML output has no broken tags

## Image Pipeline
- [ ] Midjourney polling times out gracefully (15 min max)
- [ ] Hero image downloads from Midjourney URL
- [ ] Local cache files deleted after WordPress upload

## WordPress Media - **CRITICAL**
- [ ] upload_media_from_url() returns source_url
- [ ] upload_media_from_file() returns source_url
- [ ] ALL source_url values start with your WordPress domain
- [ ] Hero image set as featured_media on post
- [ ] Alt text populated on every media item
- [ ] Filenames follow slug-based naming

## RSS Feed - **AUTOMATIC**
- [ ] WordPress RSS feed accessible at /feed/
- [ ] New published posts appear in RSS feed immediately
- [ ] RSS feed contains article title, link, excerpt, image
- [ ] RSS subscribers receive new articles automatically

## No External Dependencies
- [ ] IMGBB_API_KEY does NOT exist in .env
- [ ] Pinterest API keys NOT in use
- [ ] Google Drive credentials NOT needed
- [ ] grep -r 'imgbb' . returns ZERO matches
- [ ] grep -r 'pinterest' . returns only test/demo comments

## Error Handling
- [ ] Every Celery task has max_retries=3
- [ ] Exponential backoff working (test with simulated failure)
- [ ] Failed jobs resumable from last stage
- [ ] Pipeline doesn't re-run completed stages

---

# 🎉 YOU ARE READY TO BUILD!

**Start with Phase 1. Build sequentially. Test before advancing.**

This roadmap covers every file, function, API call, and test needed to build a complete, self-contained automated content system running locally with all images hosted exclusively in WordPress Media Library and automatic RSS feed distribution.

**Key Advantages:**
- ✅ No external image hosting (WordPress Media Library)
- ✅ No Pinterest API or scheduling (WordPress RSS is automatic)
- ✅ No Google Drive (unnecessary)
- ✅ Minimal API keys needed (just LLM + Midjourney + WordPress)
- ✅ Automatic distribution via RSS Feed
- ✅ Lower maintenance, fewer dependencies

**Questions?** Refer back to the specific phase section for detailed code examples and step-by-step instructions.

**Happy building!** 🚀
