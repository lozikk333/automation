<?php
declare(strict_types=1);

const AUTOMATION_SITE_NAME = 'Choco';
const AUTOMATION_API_KEY_HASH = '441129dd9d6ac52d18f969162138e4d784a08c766536e15f0882721d99bebe08';
const AUTOMATION_RATE_LIMIT_SECONDS = 2;

function respond_json(int $status, array $payload): void {
    http_response_code($status);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($payload, JSON_UNESCAPED_SLASHES);
    exit;
}

function bearer_token(): string {
    $header = $_SERVER['HTTP_AUTHORIZATION'] ?? $_SERVER['REDIRECT_HTTP_AUTHORIZATION'] ?? '';
    if (stripos($header, 'Bearer ') !== 0) {
        return '';
    }
    return trim(substr($header, 7));
}

function slugify_text(string $value): string {
    $value = strtolower(trim($value));
    $value = preg_replace('/[^a-z0-9]+/', '-', $value) ?? '';
    $value = trim($value, '-');
    return $value !== '' ? $value : 'article-' . date('YmdHis');
}

function safe_html(string $html): string {
    $html = preg_replace('#<script\b[^>]*>.*?</script>#is', '', $html) ?? '';
    $html = preg_replace('/\son[a-z]+\s*=\s*(["\']).*?\1/is', '', $html) ?? '';
    return $html;
}

function write_file_atomic(string $path, string $content): void {
    $dir = dirname($path);
    if (!is_dir($dir) && !mkdir($dir, 0755, true)) {
        respond_json(500, ['ok' => false, 'message' => 'Could not create directory']);
    }
    $tmp = $path . '.tmp';
    if (file_put_contents($tmp, $content, LOCK_EX) === false || !rename($tmp, $path)) {
        respond_json(500, ['ok' => false, 'message' => 'Could not write file']);
    }
}

function page_shell(string $title, string $metaDescription, string $body): string {
    $safeTitle = htmlspecialchars($title, ENT_QUOTES, 'UTF-8');
    $safeMeta = htmlspecialchars($metaDescription, ENT_QUOTES, 'UTF-8');
    $siteName = htmlspecialchars(AUTOMATION_SITE_NAME, ENT_QUOTES, 'UTF-8');
    return "<!doctype html>\n<html lang=\"en\">\n<head>\n  <meta charset=\"utf-8\">\n  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n  <title>$safeTitle | $siteName</title>\n  <meta name=\"description\" content=\"$safeMeta\">\n  <link rel=\"stylesheet\" href=\"../../style.css\">\n</head>\n<body>\n  <main class=\"policy-page\">\n    <article class=\"article-section\">\n      <h1>$safeTitle</h1>\n      $body\n    </article>\n  </main>\n</body>\n</html>\n";
}

if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    respond_json(200, ['ok' => true, 'site' => AUTOMATION_SITE_NAME, 'apiEnabled' => true]);
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    respond_json(405, ['ok' => false, 'message' => 'Method not allowed']);
}

$token = bearer_token();
if ($token === '' || !hash_equals(AUTOMATION_API_KEY_HASH, hash('sha256', $token))) {
    respond_json(401, ['ok' => false, 'message' => 'Unauthorized']);
}

$rateFile = __DIR__ . '/.publish-rate';
$now = time();
$last = is_file($rateFile) ? (int) trim((string) file_get_contents($rateFile)) : 0;
if ($last > 0 && ($now - $last) < AUTOMATION_RATE_LIMIT_SECONDS) {
    respond_json(429, ['ok' => false, 'message' => 'Rate limit exceeded']);
}
file_put_contents($rateFile, (string) $now, LOCK_EX);

$raw = file_get_contents('php://input');
$data = json_decode($raw ?: '', true);
if (!is_array($data)) {
    respond_json(400, ['ok' => false, 'message' => 'Invalid JSON payload']);
}

$title = trim((string) ($data['title'] ?? ''));
$contentHtml = trim((string) ($data['contentHtml'] ?? ''));
if ($title === '' || $contentHtml === '') {
    respond_json(422, ['ok' => false, 'message' => 'title and contentHtml are required']);
}

$slug = slugify_text((string) ($data['slug'] ?? $title));
$metaTitle = trim((string) ($data['metaTitle'] ?? $title));
$metaDescription = trim((string) ($data['metaDescription'] ?? ''));
$category = trim((string) ($data['category'] ?? ''));
$publishDate = trim((string) ($data['publishDate'] ?? date('c')));
$featuredImage = trim((string) ($data['featuredImage'] ?? ''));
$body = safe_html($contentHtml);
if ($featuredImage !== '') {
    $safeImage = htmlspecialchars($featuredImage, ENT_QUOTES, 'UTF-8');
    $safeAlt = htmlspecialchars($title, ENT_QUOTES, 'UTF-8');
    $body = "<img class=\"recipe-hero-image\" src=\"$safeImage\" alt=\"$safeAlt\">\n" . $body;
}

$root = realpath(__DIR__ . '/../..');
if ($root === false) {
    respond_json(500, ['ok' => false, 'message' => 'Site root not found']);
}

$articleDir = $root . '/article/' . $slug;
$articlePath = $articleDir . '/index.html';
write_file_atomic($articlePath, page_shell($metaTitle, $metaDescription, $body));

$indexPath = $root . '/index.html';
if (is_file($indexPath)) {
    $indexHtml = (string) file_get_contents($indexPath);
    $safeTitle = htmlspecialchars($title, ENT_QUOTES, 'UTF-8');
    $safeDesc = htmlspecialchars($metaDescription, ENT_QUOTES, 'UTF-8');
    $safeDate = htmlspecialchars($publishDate, ENT_QUOTES, 'UTF-8');
    $safeCategory = htmlspecialchars($category, ENT_QUOTES, 'UTF-8');
    $card = "<article class=\"recipe-card automation-post\"><a href=\"article/$slug/\"><div class=\"recipe-body\"><p class=\"eyebrow\">$safeCategory</p><h3>$safeTitle</h3><p>$safeDesc</p><div class=\"recipe-meta\"><b>$safeDate</b></div></div></a></article>";
    if (strpos($indexHtml, '<!-- automation-recent-posts -->') !== false) {
        $indexHtml = str_replace('<!-- automation-recent-posts -->', "<!-- automation-recent-posts -->\n" . $card, $indexHtml);
        write_file_atomic($indexPath, $indexHtml);
    }
}

$sitemapPath = $root . '/sitemap.xml';
$publicUrl = '/article/' . $slug . '/';
$entry = "  <url><loc>" . htmlspecialchars($publicUrl, ENT_XML1, 'UTF-8') . "</loc><lastmod>" . date('c') . "</lastmod></url>\n";
if (is_file($sitemapPath)) {
    $sitemap = (string) file_get_contents($sitemapPath);
    if (strpos($sitemap, $publicUrl) === false) {
        $sitemap = str_replace('</urlset>', $entry . '</urlset>', $sitemap);
        write_file_atomic($sitemapPath, $sitemap);
    }
} else {
    write_file_atomic($sitemapPath, "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n" . $entry . "</urlset>\n");
}

respond_json(201, ['ok' => true, 'slug' => $slug, 'url' => $publicUrl, 'path' => 'article/' . $slug . '/index.html']);
