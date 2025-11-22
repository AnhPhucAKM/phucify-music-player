<?php
// download.php - Async version with proper background execution
header('Content-Type: application/json; charset=utf-8');

$query = trim($_POST['query'] ?? '');

if (empty($query)) {
    echo json_encode(['success' => false, 'message' => 'URL rỗng']);
    exit;
}

$audioDir = __DIR__ . "/audio";
$logFile = $audioDir . "/download.log";

// Tạo thư mục
if (!is_dir($audioDir)) {
    mkdir($audioDir, 0755, true);
}

// Log request
$timestamp = date("Y-m-d H:i:s");
file_put_contents($logFile, "\n[$timestamp] ===== REQUEST START =====\n", FILE_APPEND);
file_put_contents($logFile, "Query: $query\n", FILE_APPEND);

// Script path
$pythonScript = __DIR__ . "/download_system.py";
$pythonPath = trim(shell_exec('which python3 2>/dev/null')) ?: 'python3';

// Make executable
chmod($pythonScript, 0755);

// Dùng nohup để chạy background đúng cách
// Redirect stderr vào log file
$cmd = "nohup $pythonPath " . escapeshellarg($pythonScript) . 
       " " . escapeshellarg($query) . 
       " >> " . escapeshellarg($logFile) . 
       " 2>&1 &";

file_put_contents($logFile, "Command: $cmd\n", FILE_APPEND);

// Execute
exec($cmd);

// Wait 1 giây để check script có chạy không
sleep(1);

// Check lock file để verify script đã chạy
$lockFile = __DIR__ . '/.download.lock';
$isRunning = file_exists($lockFile);

file_put_contents($logFile, "Lock file exists: " . ($isRunning ? 'YES' : 'NO') . "\n", FILE_APPEND);

echo json_encode([
    'success' => true,
    'message' => 'Download started',
    'is_running' => $isRunning,
    'query' => $query
]);
?>
