<?php
// test_download.php - Test xem có ch?y du?c download_system.py không
header('Content-Type: text/html; charset=utf-8');
?>
<!DOCTYPE html>
<html>
<head>
    <title>Test Download System</title>
    <style>
        body { 
            font-family: monospace; 
            background: #1a1a1a; 
            color: #0f0; 
            padding: 20px;
        }
        .success { color: #0f0; }
        .error { color: #f00; }
        .info { color: #0af; }
        pre { 
            background: #000; 
            padding: 15px; 
            border-radius: 5px;
            border: 1px solid #333;
            overflow-x: auto;
        }
        button {
            background: #1DB954;
            color: #000;
            border: none;
            padding: 10px 20px;
            font-weight: bold;
            border-radius: 5px;
            cursor: pointer;
            margin: 10px 5px;
        }
        button:hover { opacity: 0.8; }
    </style>
</head>
<body>
    <h1>?? Download System Debug</h1>

<?php
$audioDir = __DIR__ . "/audio";
$logFile = $audioDir . "/download.log";
$pythonScript = __DIR__ . "/download_system.py";
$lockFile = __DIR__ . '/.download.lock';

if (!is_dir($audioDir)) {
    mkdir($audioDir, 0755, true);
}

// TEST 1: Check files
echo "<h2>1. File Check</h2><pre>";
echo "Python script: " . ($pythonScript) . "\n";
echo "Exists: " . (file_exists($pythonScript) ? "<span class='success'>? YES</span>" : "<span class='error'>? NO</span>") . "\n";
if (file_exists($pythonScript)) {
    echo "Readable: " . (is_readable($pythonScript) ? "<span class='success'>? YES</span>" : "<span class='error'>? NO</span>") . "\n";
    echo "Executable: " . (is_executable($pythonScript) ? "<span class='success'>? YES</span>" : "<span class='error'>? NO</span>") . "\n";
    $perms = substr(sprintf('%o', fileperms($pythonScript)), -4);
    echo "Permissions: $perms\n";
}
echo "</pre>";

// TEST 2: Check Python
echo "<h2>2. Python Check</h2><pre>";
$pythonPath = trim(shell_exec('which python3 2>&1'));
echo "Python path: " . ($pythonPath ?: "<span class='error'>NOT FOUND</span>") . "\n";
$pythonVer = trim(shell_exec('python3 --version 2>&1'));
echo "Python version: " . ($pythonVer ?: "<span class='error'>Cannot execute</span>") . "\n";
echo "</pre>";

// TEST 3: Check yt-dlp
echo "<h2>3. yt-dlp Check</h2><pre>";
$ytdlp = trim(shell_exec('which yt-dlp 2>&1'));
echo "yt-dlp path: " . ($ytdlp ?: "<span class='error'>NOT FOUND</span>") . "\n";
$ytdlpVer = trim(shell_exec('yt-dlp --version 2>&1'));
echo "yt-dlp version: " . ($ytdlpVer ?: "<span class='error'>Cannot execute</span>") . "\n";
echo "</pre>";

// TEST 4: Check lock file
echo "<h2>4. Download Status</h2><pre>";
echo "Lock file: " . (file_exists($lockFile) ? "<span class='info'>EXISTS (Download running)</span>" : "<span class='success'>NOT EXISTS (Idle)</span>") . "\n";
if (file_exists($lockFile)) {
    echo "Lock age: " . (time() - filemtime($lockFile)) . " seconds\n";
}
echo "</pre>";

// TEST 5: Check log file
echo "<h2>5. Recent Log (Last 30 lines)</h2>";
echo "<button onclick='location.reload()'>?? Refresh</button>";
echo "<button onclick='clearLog()'>??? Clear Log</button>";
echo "<pre>";
if (file_exists($logFile)) {
    $lines = file($logFile);
    $recent = array_slice($lines, -30);
    echo htmlspecialchars(implode('', $recent));
} else {
    echo "<span class='error'>Log file not found</span>";
}
echo "</pre>";

// TEST 6: Manual test
if (isset($_POST['test_download'])) {
    echo "<h2>6. Manual Download Test</h2><pre>";
    
    $testQuery = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"; // Rick Roll for testing
    
    $timestamp = date("Y-m-d H:i:s");
    file_put_contents($logFile, "\n[$timestamp] ===== MANUAL TEST =====\n", FILE_APPEND);
    
    $cmd = "python3 " . escapeshellarg($pythonScript) . " " . escapeshellarg($testQuery) . " 2>&1";
    
    echo "Command: $cmd\n\n";
    echo "Executing...\n";
    
    exec($cmd, $output, $returnCode);
    
    echo "Return code: $returnCode\n";
    echo "Output:\n" . htmlspecialchars(implode("\n", $output));
    
    echo "</pre>";
}
?>

    <h2>6. Manual Test</h2>
    <form method="POST">
        <button type="submit" name="test_download">?? Run Test Download (Rick Roll)</button>
    </form>
    <p class="info">?? This will actually download a video. Check the log above after clicking.</p>

    <script>
        function clearLog() {
            if (confirm('Clear log file?')) {
                fetch('<?php echo basename(__FILE__); ?>?clear_log=1')
                    .then(() => location.reload());
            }
        }
    </script>
</body>
</html>

<?php
// Handle clear log
if (isset($_GET['clear_log'])) {
    file_put_contents($logFile, '');
    echo json_encode(['success' => true]);
    exit;
}
?>