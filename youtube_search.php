<?php
// youtube_search.php - Tìm kiếm YouTube sử dụng yt-dlp

header('Content-Type: application/json; charset=utf-8');

$query = trim($_POST['query'] ?? '');

if (empty($query)) {
    echo json_encode(['error' => 'Empty query']);
    exit;
}

// Escape query an toàn hơn
$escaped_query = escapeshellarg("ytsearch10:$query");

// Command với error handling tốt hơn - Lấy thumbnail từ YouTube trực tiếp
$cmd = "yt-dlp $escaped_query --flat-playlist --print \"%(title)s\t%(id)s\t%(duration)s\" 2>&1";

// Log command để debug
error_log("YouTube Search Command: $cmd");

$output = shell_exec($cmd);

// Log output để debug
error_log("YouTube Search Output: " . substr($output, 0, 500));

if (empty($output)) {
    echo json_encode(['error' => 'No output from yt-dlp. Check if yt-dlp is installed.', 'command' => $cmd]);
    exit;
}

$lines = explode("\n", trim($output));
$results = [];

foreach ($lines as $line) {
    $line = trim($line);
    
    // Skip empty lines và error lines
    if (empty($line) || 
        stripos($line, '[ERROR]') !== false || 
        stripos($line, 'WARNING') !== false ||
        stripos($line, 'Extracting') !== false) {
        continue;
    }
    
    $parts = explode("\t", $line);
    
    if (count($parts) >= 2) {
        $videoId = $parts[1] ?? '';
        $results[] = [
            'title' => $parts[0] ?? 'Unknown',
            'id' => $videoId,
            'thumbnail' => "https://img.youtube.com/vi/$videoId/mqdefault.jpg", // YouTube thumbnail URL
            'duration' => $parts[2] ?? 'N/A'
        ];
    }
}

if (empty($results)) {
    echo json_encode([
        'error' => 'No results found',
        'debug_output' => substr($output, 0, 500)
    ]);
} else {
    echo json_encode($results);
}

exit;
?>