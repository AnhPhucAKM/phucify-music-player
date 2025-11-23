<?php require 'functions.php'; ?>
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎵 Phucify — Player</title>
    <link rel="stylesheet" href="style.css?v=6">
</head>
<body>

<div class="sidebar">
    <h1>🎵 Phucify</h1>
    <button class="btn" id="openYoutubeSearch">Tải nhạc từ YouTube</button>
    <button class="btn" onclick="createPlaylist()">+ Tạo Playlist mới</button>

    <ul class="playlist-list" id="playlistList">
        <?php foreach($playlistsData as $name => $songs): ?>
            <li class="playlist-item <?= $name==='Tất cả nhạc' ? 'selected' : '' ?>"
                onclick="loadPlaylist('<?= htmlspecialchars($name, ENT_QUOTES) ?>', this)">
                <?= htmlspecialchars($name) ?> (<?= count($songs) ?>)
            </li>
        <?php endforeach; ?>
    </ul>
</div>

<button id="mobileMenuBtn">☰ Playlist</button>

<div class="main">
    <div class="grid" id="diskGrid">
        <?php
        $songsMeta = [];
        foreach($files as $f) {
            $file = basename($f);
            $name = pathinfo($file, PATHINFO_FILENAME);
            $songsMeta[$file] = [
                'path' => "audio/{$file}",
                'title' => $name,
                'cover' => getCover($file)
            ];
        ?>
        <div class="disk" data-file="<?= $file ?>" onclick="playSong('audio/<?= $file ?>', this)">
            <img src="<?= getCover($file) ?>" alt="">
            <p><?= htmlspecialchars($name) ?></p>

            <div class="disk-actions">
                <button class="add-btn" onclick="event.stopPropagation(); openAddToPlaylist('<?= $file ?>')">➕</button>
                <button class="remove-btn" onclick="event.stopPropagation(); removeFromPlaylist('<?= $file ?>')">✖</button>
            </div>
        </div>
        <?php } ?>
    </div>
</div>

<!-- Modal YouTube -->
<div id="youtubeModal" class="modal">
    <div class="modal-content">
        <span class="close">×</span>
        <h2 style="color:#d4af37;text-align:center;">Tìm và tải bài hát từ YouTube</h2>
        <form id="searchForm">
            <input type="text" id="searchQuery" placeholder="Nhập tên bài hát, ca sĩ..." required style="width:70%;padding:12px;border-radius:8px;border:1px solid #8b4513;background:#3d2b1f;color:#f4e4bc;">
            <button type="submit" class="btn" style="width:25%;margin-left:5px;">Tìm kiếm</button>
        </form>
        <div id="searchResults" class="search-results"></div>
        <div id="downloadStatus" style="text-align:center;margin-top:20px;font-size:18px;"></div>
    </div>
</div>

<!-- Progress Bar -->
<div class="progress-container" onclick="seek(event)">
    <div id="progressBar" class="progress"></div>
</div>

<!-- Player bar -->
<div class="player-bar" id="playerBar">
    <img id="playerCover" class="player-cover" src="assets/default.jpg" alt="cover">
    <div class="player-info">
        <div id="playerTitle" class="player-title">Chưa chọn bài</div>
    </div>

    <div class="player-controls">
        <span class="player-btn" onclick="prevSong()">⏮</span>
        <span class="player-btn" id="playPauseBtn" onclick="togglePlay()">▶️</span>
        <span class="player-btn" onclick="nextSong()">⏭</span>
        <span class="player-btn" onclick="toggleShuffle()" id="shuffleBtn">🔀</span>
    </div>

    <audio id="audio"></audio>
</div>

<!-- Modal chọn playlist -->
<div id="playlistModal" class="modal">
    <div class="modal-content" style="max-width:400px;padding:20px;">
        <h2 style="text-align:center;margin-bottom:10px;">Chọn playlist</h2>
        <div id="playlistChoices"></div>

        <button id="addToPlaylistConfirm" class="btn" style="margin-top:15px;width:100%;">
            Thêm
        </button>
        <button onclick="closePlaylistModal()" class="btn" style="background:#555;width:100%;margin-top:8px;">
            Hủy
        </button>
    </div>
</div>

<div id="toastContainer"></div>

<!-- Download Status Card -->
<div id="downloadStatusCard">
    <div class="download-spinner"></div>
    <div class="download-icon success">✓</div>
    <div class="download-icon error">✕</div>
</div>

<!-- Create Playlist Modal -->
<div id="createPlaylistModal" class="modal">
    <div class="modal-content create-modal">
        <span class="close" id="closeCreateModal">&times;</span>
        <h2>Tạo Playlist Mới</h2>
        <input type="text" id="newPlaylistName" placeholder="Nhập tên playlist...">
        <div class="modal-buttons">
            <button id="createPlaylistConfirm" class="btn">Tạo</button>
            <button id="createPlaylistCancel" class="btn cancel">Hủy</button>
        </div>
    </div>
</div>

<!-- Custom Confirm Dialog -->
<div id="confirmDialog" class="confirm-overlay">
    <div class="confirm-dialog">
        <div id="confirmIcon" class="confirm-icon warning">⚠️</div>
        <div id="confirmTitle" class="confirm-title">Xác nhận</div>
        <div id="confirmMessage" class="confirm-message">Bạn có chắc chắn muốn thực hiện hành động này?</div>
        <div class="confirm-buttons">
            <button id="confirmCancel" class="confirm-btn secondary">Hủy</button>
            <button id="confirmOk" class="confirm-btn danger">Xác nhận</button>
        </div>
    </div>
</div>

<script>
    window.SONGS_META = <?= json_encode($songsMeta, JSON_UNESCAPED_UNICODE) ?>;
    window.PLAYLISTS = <?= json_encode($playlistsData, JSON_UNESCAPED_UNICODE) ?>;
</script>

<script src="script.js"></script>
</body>
</html>
