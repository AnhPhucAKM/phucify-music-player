<?php
header('Content-Type: application/json');

$query = trim($_POST['query'] ?? '');

if (empty($query)) {
    echo json_encode(['success' => false, 'message' => 'URL rỗng']);
    exit;
}

$cmd = 'python3 download_system.py ' . escapeshellarg($query) . ' > /dev/null 2>&1 &';
exec($cmd);

echo json_encode(['success' => true, 'message' => 'Đang tải...']);
?>
EOF
