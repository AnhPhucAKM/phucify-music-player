<?php
// delete_file.php - Xóa file audio và cover khỏi server
header('Content-Type: application/json; charset=utf-8');

$file = $_POST['file'] ?? '';

if (empty($file)) {
    echo json_encode(['success' => false, 'message' => 'Tên file rỗng']);
    exit;
}

// Chặn path traversal
if (strpos($file, '..') !== false || strpos($file, '/') !== false) {
    echo json_encode(['success' => false, 'message' => 'Tên file không hợp lệ']);
    exit;
}

$audioDir = __DIR__ . '/audio';
$coversDir = __DIR__ . '/covers';
$playlistFile = __DIR__ . '/playlists.json';

$audioPath = $audioDir . '/' . $file;
$baseName = pathinfo($file, PATHINFO_FILENAME);

$deleted = [];
$errors = [];

// Xóa file audio
if (file_exists($audioPath)) {
    if (unlink($audioPath)) {
        $deleted[] = 'audio: ' . $file;
    } else {
        $errors[] = 'Không thể xóa audio';
    }
} else {
    $errors[] = 'File audio không tồn tại';
}

// Xóa cover (tất cả các extension)
$extensions = ['jpg', 'jpeg', 'png', 'webp'];
foreach ($extensions as $ext) {
    $coverPath = $coversDir . '/' . $baseName . '.' . $ext;
    if (file_exists($coverPath)) {
        if (unlink($coverPath)) {
            $deleted[] = 'cover: ' . $baseName . '.' . $ext;
        }
    }
}

// Xóa khỏi tất cả playlist
if (file_exists($playlistFile)) {
    $playlists = json_decode(file_get_contents($playlistFile), true);
    if (is_array($playlists)) {
        foreach ($playlists as $name => &$songs) {
            $songs = array_values(array_filter($songs, fn($s) => $s !== $file));
        }
        file_put_contents($playlistFile, json_encode($playlists, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
        $deleted[] = 'Đã xóa khỏi playlists';
    }
}

if (count($deleted) > 0) {
    echo json_encode([
        'success' => true,
        'message' => 'Đã xóa: ' . implode(', ', $deleted),
        'deleted' => $deleted
    ]);
} else {
    echo json_encode([
        'success' => false,
        'message' => implode(', ', $errors)
    ]);
}
?>
