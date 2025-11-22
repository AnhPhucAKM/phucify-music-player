<?php
// functions.php - Quản lý nhạc và playlist với thumbnail support

$audioDir = __DIR__ . '/audio';
$coversDir = __DIR__ . '/covers';
$playlistFile = __DIR__ . '/playlists.json';

// Tạo thư mục nếu chưa có
if (!is_dir($audioDir)) mkdir($audioDir, 0755, true);
if (!is_dir($coversDir)) mkdir($coversDir, 0755, true);

// Lấy danh sách file nhạc
$files = glob($audioDir . '/*.mp3');

// Hàm lấy cover art
function getCover($filename) {
    global $coversDir;
    
    $baseName = pathinfo($filename, PATHINFO_FILENAME);
    
    // Các extension có thể có
    $extensions = ['jpg', 'jpeg', 'png', 'webp'];
    
    foreach ($extensions as $ext) {
        $coverPath = $coversDir . '/' . $baseName . '.' . $ext;
        if (file_exists($coverPath)) {
            return 'covers/' . $baseName . '.' . $ext;
        }
    }
    
    // Fallback về default cover
    return 'assets/default.jpg';
}

// Load playlists
$playlistsData = ['Tất cả nhạc' => array_map('basename', $files)];

if (file_exists($playlistFile)) {
    $loaded = json_decode(file_get_contents($playlistFile), true);
    if ($loaded) {
        $playlistsData = array_merge($playlistsData, $loaded);
    }
}
?>