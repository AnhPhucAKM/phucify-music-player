<?php
// check_download.php - Kiểm tra download status (Fixed JSON encoding)

header('Content-Type: application/json; charset=utf-8');

// Tắt tất cả output khác
ob_clean();

$lockFile = __DIR__ . '/.download.lock';
$logFile = __DIR__ . '/audio/download.log';

try {
    // Kiểm tra lock file
    $isDownloading = file_exists($lockFile);
    
    // Parse log để tìm status
    $lastStatus = 'idle';
    $lastTitle = '';
    
    if (file_exists($logFile)) {
        // Đọc file với UTF-8 encoding
        $content = file_get_contents($logFile);
        
        // Lấy 10 dòng cuối
        $lines = explode("\n", $content);
        $recentLogs = array_slice($lines, -10);
        
        foreach (array_reverse($recentLogs) as $line) {
            // Clean line - remove all non-printable và emoji
            $line = preg_replace('/[^\x20-\x7E]/u', '', $line);
            
            if (stripos($line, 'SUCCESS') !== false) {
                $lastStatus = 'success';
                if (preg_match('/SUCCESS:\s*(.+)$/i', $line, $matches)) {
                    $lastTitle = trim($matches[1]);
                }
                break;
            } elseif (stripos($line, 'FAILED') !== false) {
                $lastStatus = 'failed';
                if (preg_match('/FAILED:\s*(.+)$/i', $line, $matches)) {
                    $lastTitle = trim($matches[1]);
                }
                break;
            } elseif (stripos($line, 'Downloading audio') !== false) {
                $lastStatus = 'downloading';
                if (preg_match('/Downloading audio:\s*(.+)$/i', $line, $matches)) {
                    $lastTitle = trim($matches[1]);
                }
                break;
            }
        }
    }
    
    // Build response - clean all strings
    $response = [
        'isDownloading' => (bool)$isDownloading,
        'status' => $lastStatus,
        'title' => $lastTitle,
        'timestamp' => time()
    ];
    
    // Output JSON với error checking
    $json = json_encode($response, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    
    if (json_last_error() !== JSON_ERROR_NONE) {
        // Nếu vẫn lỗi, trả về response đơn giản
        $json = json_encode([
            'isDownloading' => (bool)$isDownloading,
            'status' => 'idle',
            'title' => '',
            'timestamp' => time(),
            'error' => json_last_error_msg()
        ]);
    }
    
    echo $json;
    
} catch (Exception $e) {
    // Fallback response nếu có lỗi
    echo json_encode([
        'isDownloading' => false,
        'status' => 'error',
        'title' => '',
        'timestamp' => time(),
        'error' => $e->getMessage()
    ]);
}
?>