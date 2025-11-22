<?php
// playlist.php — One-file playlist backend (format A)

header('Content-Type: application/json; charset=utf-8');

$playlistFile = __DIR__ . '/playlists.json';

// Nếu file chưa tồn tại → tạo file trống
if (!file_exists($playlistFile)) {
    file_put_contents($playlistFile, json_encode([], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
}

$data = json_decode(file_get_contents($playlistFile), true);
if (!is_array($data)) $data = [];

// Nhận action
$action = $_POST['action'] ?? '';
$playlist = $_POST['playlist'] ?? '';
$file = $_POST['file'] ?? '';
$files = json_decode($_POST['files'] ?? '[]', true);

// Hàm lưu playlist
function savePlaylist($data, $playlistFile) {
    file_put_contents($playlistFile, json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
}

// ---- ACTIONS ----

// 1) Tạo playlist
if ($action === 'create') {
    if ($playlist && !isset($data[$playlist])) {
        $data[$playlist] = [];
        savePlaylist($data, $playlistFile);
        echo json_encode(['success' => true, 'playlists' => $data]);
        exit;
    }
    echo json_encode(['success' => false, 'message' => 'Tên playlist không hợp lệ hoặc đã tồn tại.']);
    exit;
}

// 2) Xoá playlist
if ($action === 'delete') {
    if ($playlist && isset($data[$playlist])) {
        unset($data[$playlist]);
        savePlaylist($data, $playlistFile);
        echo json_encode(['success' => true, 'playlists' => $data]);
        exit;
    }
    echo json_encode(['success' => false, 'message' => 'Không thể xoá playlist.']);
    exit;
}

// 3) Thêm 1 bài vào playlist
if ($action === 'add') {
    if ($playlist && $file && isset($data[$playlist])) {
        if (!in_array($file, $data[$playlist])) {
            $data[$playlist][] = $file;
            savePlaylist($data, $playlistFile);
        }
        echo json_encode(['success' => true, 'playlists' => $data]);
        exit;
    }
    echo json_encode(['success' => false, 'message' => 'Không thể thêm vào playlist.']);
    exit;
}

// 4) Xoá 1 bài khỏi playlist
if ($action === 'remove') {
    if ($playlist && $file && isset($data[$playlist])) {
        $data[$playlist] = array_values(array_filter($data[$playlist], fn($f) => $f !== $file));
        savePlaylist($data, $playlistFile);
        echo json_encode(['success' => true, 'playlists' => $data]);
        exit;
    }
    echo json_encode(['success' => false, 'message' => 'Không thể xoá bài.']);
    exit;
}

// 5) Cập nhật playlist (ghi đè toàn bộ danh sách)
if ($action === 'update') {
    if ($playlist && isset($data[$playlist]) && is_array($files)) {
        $data[$playlist] = $files;
        savePlaylist($data, $playlistFile);
        echo json_encode(['success' => true, 'playlists' => $data]);
        exit;
    }
    echo json_encode(['success' => false, 'message' => 'Không thể cập nhật playlist.']);
    exit;
}

// 6) Lấy danh sách playlist
if ($action === 'load') {
    echo json_encode(['success' => true, 'playlists' => $data]);
    exit;
}

// Action không hợp lệ
echo json_encode(['success' => false, 'message' => 'Yêu cầu không hợp lệ.']);
exit;
?>