<?php
header('Content-Type: application/json');

$query = trim($_POST['query'] ?? '');

if (empty($query)) {
    echo json_encode(['success' => false, 'message' => 'URL rỗng']);
    exit;
}

$logFile = __DIR__ . "/logs/download.log";
$cmd = "python3 " . __DIR__ . "/download_system.py "
     . escapeshellarg($query)
     . " >> " . escapeshellarg($logFile) . " 2>&1 &";

exec($cmd, $output, $returnVar);

echo json_encode([
    'success' => true,
    'message' => 'Download started',
    'log' => $logFile
]);
exit;
