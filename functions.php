<?php
// functions.php - Fixed UTF-8 with Audio Path Encoding

// Force UTF-8 encoding
mb_internal_encoding('UTF-8');
mb_http_output('UTF-8');
ini_set('default_charset', 'UTF-8');

$audioDir = __DIR__ . '/audio';
$coversDir = __DIR__ . '/covers';
$playlistFile = __DIR__ . '/playlists.json';

// Tạo thư mục nếu chưa có
if (!is_dir($audioDir)) mkdir($audioDir, 0755, true);
if (!is_dir($coversDir)) mkdir($coversDir, 0755, true);

// Lấy danh sách file nhạc với UTF-8 encoding
$files = [];

if (is_dir($audioDir)) {
    // Dùng scandir với UTF-8 locale
    setlocale(LC_ALL, 'en_US.UTF-8');
    
    $allFiles = scandir($audioDir);
    
    foreach ($allFiles as $filename) {
        if (pathinfo($filename, PATHINFO_EXTENSION) === 'mp3') {
            // Đảm bảo filename là UTF-8
            if (!mb_check_encoding($filename, 'UTF-8')) {
                // Try to convert
                $filename = mb_convert_encoding($filename, 'UTF-8', 'auto');
            }
            
            $fullPath = $audioDir . '/' . $filename;
            if (is_file($fullPath)) {
                $files[] = $fullPath;
            }
        }
    }
}

// Hàm lấy cover art với UTF-8 support
function getCover($filename) {
    global $coversDir;
    
    // Đảm bảo filename là UTF-8
    if (!mb_check_encoding($filename, 'UTF-8')) {
        $filename = mb_convert_encoding($filename, 'UTF-8', 'auto');
    }
    
    $baseName = pathinfo($filename, PATHINFO_FILENAME);
    
    // Các extension có thể có
    $extensions = ['jpg', 'jpeg', 'png', 'webp'];
    
    foreach ($extensions as $ext) {
        $coverPath = $coversDir . '/' . $baseName . '.' . $ext;
        if (file_exists($coverPath)) {
            // Encode URL nhưng keep UTF-8
            return 'covers/' . rawurlencode($baseName) . '.' . $ext;
        }
    }
    
    // Fallback về default cover
    return 'assets/default.jpg';
}

// Hàm encode audio path
function getAudioPath($filename) {
    // Encode filename cho URL
    return 'audio/' . rawurlencode($filename);
}

// Load playlists với UTF-8
$playlistsData = ['Tất cả nhạc' => array_map('basename', $files)];

if (file_exists($playlistFile)) {
    $content = file_get_contents($playlistFile);
    $loaded = json_decode($content, true);
    
    if (json_last_error() === JSON_ERROR_NONE && is_array($loaded)) {
        $playlistsData = array_merge($playlistsData, $loaded);
    }
}
?>
