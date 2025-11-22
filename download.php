<?php
// download.php - Fixed với debug chi tiết
header('Content-Type: application/json; charset=utf-8');

$query = trim($_POST['query'] ?? '');

if (empty($query)) {
    echo json_encode(['success' => false, 'message' => 'URL rỗng']);
    exit;
}

$audioDir = __DIR__ . "/audio";
$logFile = $audioDir . "/download.log";

// Tạo thư mục nếu chưa có
if (!is_dir($audioDir)) {
    mkdir($audioDir, 0755, true);
}

// Log request
$timestamp = date("Y-m-d H:i:s");
file_put_contents($logFile, "\n[$timestamp] ===== NEW REQUEST =====\n", FILE_APPEND);
file_put_contents($logFile, "Query: $query\n", FILE_APPEND);

// Check script exists
$pythonScript = __DIR__ . "/download_system.py";
if (!file_exists($pythonScript)) {
    $msg = "ERROR: Script not found at $pythonScript";
    file_put_contents($logFile, "[$timestamp] $msg\n", FILE_APPEND);
    echo json_encode(['success' => false, 'message' => $msg]);
    exit;
}

// Check python3 exists
$pythonPath = trim(shell_exec('which python3 2>/dev/null'));
if (empty($pythonPath)) {
    $pythonPath = 'python3'; // fallback
}
file_put_contents($logFile, "Python path: $pythonPath\n", FILE_APPEND);

// Make script executable (nếu chưa có quyền)
chmod($pythonScript, 0755);

// Build command - KHÔNG dùng background process, để capture error
$cmd = "$pythonPath " . escapeshellarg($pythonScript) . " " . escapeshellarg($query) . " 2>&1";

file_put_contents($logFile, "Command: $cmd\n", FILE_APPEND);
file_put_contents($logFile, "Starting execution...\n", FILE_APPEND);

// Execute và capture output
$output = [];
$returnCode = 0;
exec($cmd, $output, $returnCode);

// Log kết quả
file_put_contents($logFile, "Return code: $returnCode\n", FILE_APPEND);
file_put_contents($logFile, "Output:\n" . implode("\n", $output) . "\n", FILE_APPEND);

if ($returnCode === 0) {
    echo json_encode([
        'success' => true,
        'message' => 'Download completed',
        'output' => implode("\n", array_slice($output, -5)) // 5 dòng cuối
    ]);
} else {
    echo json_encode([
        'success' => false,
        'message' => 'Download failed',
        'error' => implode("\n", $output),
        'return_code' => $returnCode
    ]);
}
?>
