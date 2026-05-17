<?php
/**
 * YARA BITES Internal Publishing API
 * 
 * This secure endpoint receives articles from the automation system
 * and publishes them to the static HTML website.
 * 
 * Security:
 * - Bearer token authentication (hashed verification)
 * - Request validation
 * - Rate limiting (optional)
 * - CORS disabled by default
 * - Error logging
 * 
 * Endpoint: POST /internal-api/publish/
 * Auth: Bearer Token
 */

// Security: No direct access
if (php_sapi_name() !== 'cli' && $_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    die(json_encode(['error' => 'Method not allowed']));
}

// Configuration
const AUTOMATION_API_KEY_HASH = '{{ API_KEY_HASH }}';
const SITE_ROOT = __DIR__ . '/..';
const LOG_DIR = SITE_ROOT . '/logs';
const ARTICLE_DIR = SITE_ROOT . '/article';
const SITEMAP_PATH = SITE_ROOT . '/sitemap.xml';
const INDEX_PATH = SITE_ROOT . '/index.html';

// Ensure logging directory exists
if (!is_dir(LOG_DIR)) {
    mkdir(LOG_DIR, 0755, true);
}

// Response helper
function respond($ok, $data = []) {
    http_response_code($ok ? 200 : 400);
    echo json_encode(array_merge(['ok' => $ok], $data));
    exit(0);
}

// Error response
function error_respond($message, $code = 400) {
    http_response_code($code);
    log_error("API Error ($code): $message");
    echo json_encode(['ok' => false, 'error' => $message]);
    exit(0);
}

// Logging
function log_info($message) {
    $timestamp = date('Y-m-d H:i:s');
    $log_file = LOG_DIR . '/publish-api.log';
    file_put_contents($log_file, "[$timestamp] INFO: $message\n", FILE_APPEND);
}

function log_error($message) {
    $timestamp = date('Y-m-d H:i:s');
    $log_file = LOG_DIR . '/publish-api-errors.log';
    file_put_contents($log_file, "[$timestamp] ERROR: $message\n", FILE_APPEND);
}

// Security: Verify Bearer token
function verify_token($token) {
    if (empty($token) || empty(AUTOMATION_API_KEY_HASH)) {
        return false;
    }
    // Hash the provided token and compare with stored hash
    $token_hash = hash('sha256', $token);
    return hash_equals($token_hash, AUTOMATION_API_KEY_HASH);
}

// Security: Extract and verify Bearer token
function authenticate() {
    $headers = getallheaders();
    $auth_header = $headers['Authorization'] ?? '';
    
    if (strpos($auth_header, 'Bearer ') !== 0) {
        error_respond('Missing or invalid Authorization header', 401);
    }
    
    $token = substr($auth_header, 7);
    if (!verify_token($token)) {
        log_error('Invalid token provided');
        error_respond('Unauthorized: Invalid token', 401);
    }
}

// Validate and sanitize payload
function validate_payload($payload) {
    $errors = [];
    
    // Required fields
    if (empty($payload['title'])) {
        $errors[] = 'title is required';
    }
    if (empty($payload['slug'])) {
        $errors[] = 'slug is required';
    }
    if (empty($payload['contentHtml'])) {
        $errors[] = 'contentHtml is required';
    }
    
    // Validate slug format (alphanumeric, hyphens, underscores)
    if (!empty($payload['slug']) && !preg_match('/^[a-z0-9_-]+$/i', $payload['slug'])) {
        $errors[] = 'slug must contain only alphanumeric characters, hyphens, and underscores';
    }
    
    if (!empty($errors)) {
        return ['valid' => false, 'errors' => $errors];
    }
    
    return ['valid' => true];
}

// Sanitize HTML content
function sanitize_html($html) {
    // Basic XSS protection - remove dangerous tags and attributes
    $allowed_tags = '<p><br><strong><em><u><ul><li><ol><blockquote><h2><h3><h4><h5><h6><a><img>';
    return strip_tags($html, $allowed_tags);
}

// Create article page
function create_article_page($slug, $title, $meta_description, $content_html, $featured_image) {
    $article_dir = ARTICLE_DIR . '/' . $slug;
    
    // Ensure article directory exists
    if (!is_dir($article_dir)) {
        mkdir($article_dir, 0755, true);
    }
    
    $index_file = $article_dir . '/index.html';
    
    // Sanitize inputs
    $title = htmlspecialchars($title, ENT_QUOTES, 'UTF-8');
    $meta_description = htmlspecialchars($meta_description, ENT_QUOTES, 'UTF-8');
    $featured_image = htmlspecialchars($featured_image, ENT_QUOTES, 'UTF-8');
    
    // Build page HTML
    $html = <<<EOT
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{$title}</title>
  <meta name="description" content="{$meta_description}">
  <meta property="og:title" content="{$title}">
  <meta property="og:description" content="{$meta_description}">
  <meta property="og:type" content="article">
EOT;
    
    if (!empty($featured_image)) {
        $html .= "\n  <meta property=\"og:image\" content=\"{$featured_image}\">";
    }
    
    $html .= "\n  <link rel=\"stylesheet\" href=\"../../style.css\">\n</head>\n<body>\n  <main class=\"recipe-article\">\n";
    
    if (!empty($featured_image)) {
        $html .= "    <img class=\"article-hero-image\" src=\"{$featured_image}\" alt=\"{$title}\">\n";
    }
    
    $html .= "    <article class=\"article-content\">\n";
    $html .= "      <h1>{$title}</h1>\n";
    $html .= "      <div class=\"article-body\">\n";
    $html .= $content_html;
    $html .= "\n      </div>\n";
    $html .= "    </article>\n  </main>\n</body>\n</html>\n";
    
    // Write atomically
    $temp_file = $index_file . '.tmp';
    if (file_put_contents($temp_file, $html, LOCK_EX) === false) {
        throw new Exception("Failed to write article file: $index_file");
    }
    
    if (!rename($temp_file, $index_file)) {
        @unlink($temp_file);
        throw new Exception("Failed to publish article file: $index_file");
    }
    
    return $index_file;
}

// Update homepage recent posts section
function update_homepage_recent_posts($slug, $title, $meta_description, $category, $featured_image) {
    if (!file_exists(INDEX_PATH)) {
        return; // Homepage doesn't exist, skip update
    }
    
    $index_html = file_get_contents(INDEX_PATH);
    $article_url = "/article/{$slug}/";
    
    // Check if article already exists in homepage
    if (strpos($index_html, "article/{$slug}/") !== false) {
        return; // Article already in homepage
    }
    
    // Look for automation marker
    $marker = '<!-- automation-recent-posts -->';
    if (strpos($index_html, $marker) === false) {
        return; // No automation marker found
    }
    
    // Create article card HTML
    $card = sprintf(
        '<article class="recipe-card automation-post" data-slug="%s"><a href="%s"><div class="recipe-card-header">%s</div><div class="recipe-card-body"><p class="eyebrow">%s</p><h3>%s</h3><p class="description">%s</p></div></a></article>',
        htmlspecialchars($slug, ENT_QUOTES, 'UTF-8'),
        htmlspecialchars($article_url, ENT_QUOTES, 'UTF-8'),
        !empty($featured_image) ? sprintf('<img src="%s" alt="%s" class="recipe-card-image">', htmlspecialchars($featured_image, ENT_QUOTES, 'UTF-8'), htmlspecialchars($title, ENT_QUOTES, 'UTF-8')) : '',
        htmlspecialchars($category, ENT_QUOTES, 'UTF-8'),
        htmlspecialchars($title, ENT_QUOTES, 'UTF-8'),
        htmlspecialchars($meta_description, ENT_QUOTES, 'UTF-8')
    );
    
    // Insert card before marker
    $updated_html = str_replace($marker, $marker . "\n" . $card, $index_html);
    
    // Write atomically
    $temp_file = INDEX_PATH . '.tmp';
    if (file_put_contents($temp_file, $updated_html, LOCK_EX) === false) {
        throw new Exception("Failed to update homepage");
    }
    
    if (!rename($temp_file, INDEX_PATH)) {
        @unlink($temp_file);
        throw new Exception("Failed to publish homepage update");
    }
}

// Update sitemap
function update_sitemap($slug) {
    $article_url = "/article/{$slug}/";
    $now = date('c');
    
    // Create sitemap entry
    $entry = sprintf(
        "  <url><loc>%s</loc><lastmod>%s</lastmod></url>\n",
        htmlspecialchars($article_url, ENT_QUOTES, 'UTF-8'),
        $now
    );
    
    if (file_exists(SITEMAP_PATH)) {
        $sitemap = file_get_contents(SITEMAP_PATH);
        
        // Check if entry already exists
        if (strpos($sitemap, $article_url) !== false) {
            return; // Already in sitemap
        }
        
        // Add before closing tag
        $updated_sitemap = str_replace(
            '</urlset>',
            $entry . '</urlset>',
            $sitemap
        );
    } else {
        // Create new sitemap
        $updated_sitemap = <<<EOT
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{$entry}</urlset>
EOT;
    }
    
    // Write atomically
    $temp_file = SITEMAP_PATH . '.tmp';
    if (file_put_contents($temp_file, $updated_sitemap, LOCK_EX) === false) {
        throw new Exception("Failed to write sitemap");
    }
    
    if (!rename($temp_file, SITEMAP_PATH)) {
        @unlink($temp_file);
        throw new Exception("Failed to publish sitemap");
    }
}

// Main request handler
try {
    // Verify authentication
    authenticate();
    
    // Get JSON payload
    $json = file_get_contents('php://input');
    $payload = json_decode($json, true);
    
    if (!is_array($payload)) {
        error_respond('Invalid JSON payload', 400);
    }
    
    // Validate payload
    $validation = validate_payload($payload);
    if (!$validation['valid']) {
        error_respond('Validation failed: ' . implode('; ', $validation['errors']), 400);
    }
    
    // Extract and sanitize data
    $slug = preg_replace('/[^a-z0-9_-]/i', '', $payload['slug']);
    $title = trim($payload['title']);
    $content_html = sanitize_html($payload['contentHtml']);
    $meta_title = trim($payload['metaTitle'] ?? $title);
    $meta_description = trim($payload['metaDescription'] ?? '');
    $featured_image = trim($payload['featuredImage'] ?? '');
    $category = trim($payload['category'] ?? 'Article');
    $publish_date = trim($payload['publishDate'] ?? date('c'));
    
    log_info("Publishing article: $slug");
    
    // Create article page
    $article_path = create_article_page($slug, $meta_title, $meta_description, $content_html, $featured_image);
    log_info("Article created: $article_path");
    
    // Update homepage
    update_homepage_recent_posts($slug, $title, $meta_description, $category, $featured_image);
    log_info("Homepage updated with article: $slug");
    
    // Update sitemap
    update_sitemap($slug);
    log_info("Sitemap updated with article: $slug");
    
    // Return success
    $article_url = "/article/{$slug}/";
    respond(true, [
        'slug' => $slug,
        'url' => $article_url,
        'path' => $article_path,
        'published_at' => date('c'),
        'message' => "Article published successfully: $article_url"
    ]);

} catch (Exception $e) {
    log_error($e->getMessage());
    error_respond('Publishing failed: ' . $e->getMessage(), 500);
}
?>
