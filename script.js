// =============================
// GLOBAL STATE
// =============================

const audio = document.getElementById("audio");
let currentPlaylist = [];
let currentIndex = -1;
let isShuffle = false;

const SONGS_META = window.SONGS_META || {};
let PLAYLISTS = window.PLAYLISTS || {};

// =============================
// PLAYER — FIXED + SHUFFLE
// =============================

function playSong(filename, element = null) {
    const clean = filename.replace("audio/", "");
    const meta = SONGS_META[clean];

    if (!meta) return console.error("Không tìm thấy bài:", clean);

    const indexFound = currentPlaylist.findIndex(s => s.file === clean);

    if (indexFound !== -1) {
        currentIndex = indexFound;
    } else {
        currentPlaylist.push({...meta, file: clean});
        currentIndex = currentPlaylist.length - 1;
    }

    audio.src = meta.path;
    audio.play();

    document.getElementById("playerTitle").textContent = meta.title;
    document.getElementById("playerCover").src = meta.cover;
    document.getElementById("playPauseBtn").textContent = "⏸";

    document.querySelectorAll('.disk').forEach(d => d.classList.remove('selected'));
    if (element) element.classList.add('selected');
}

function togglePlay() {
    if (audio.paused) {
        audio.play();
        document.getElementById("playPauseBtn").textContent = "⏸";
    } else {
        audio.pause();
        document.getElementById("playPauseBtn").textContent = "▶️";
    }
}

function nextSong() {
    if (!currentPlaylist.length) return;

    if (isShuffle) {
        let newIndex;
        do {
            newIndex = Math.floor(Math.random() * currentPlaylist.length);
        } while (newIndex === currentIndex && currentPlaylist.length > 1);
        currentIndex = newIndex;
    } else {
        currentIndex = (currentIndex + 1) % currentPlaylist.length;
    }

    playSong(currentPlaylist[currentIndex].file);
}

function prevSong() {
    if (!currentPlaylist.length) return;
    currentIndex = (currentIndex - 1 + currentPlaylist.length) % currentPlaylist.length;
    playSong(currentPlaylist[currentIndex].file);
}

audio.onended = nextSong;

function toggleShuffle() {
    isShuffle = !isShuffle;
    document.getElementById("shuffleBtn").style.opacity = isShuffle ? "1" : "0.5";
    showToast(isShuffle ? "Bật phát ngẫu nhiên" : "Tắt phát ngẫu nhiên", "info");
}

// =============================
// PROGRESS BAR
// =============================

const progressBar = document.getElementById("progressBar");

audio.ontimeupdate = () => {
    if (!audio.duration) return;
    progressBar.style.width = (audio.currentTime / audio.duration * 100) + "%";
};

function seek(e) {
    const rect = e.currentTarget.getBoundingClientRect();
    const percent = (e.clientX - rect.left) / rect.width;
    audio.currentTime = percent * audio.duration;
}

// =============================
// LOAD PLAYLIST
// =============================

async function reloadPlaylists() {
    const res = await fetch("playlist.php", {
        method: "POST",
        body: new URLSearchParams({action: "load"})
    });

    const j = await res.json();
    if (j.success) {
        PLAYLISTS = {
            "Tất cả nhạc": Object.keys(SONGS_META),
            ...j.playlists
        };
    }
}

async function loadPlaylist(name, element) {
    const grid = document.querySelector(".grid");

    document.querySelectorAll('.playlist-item').forEach(li => li.classList.remove('selected'));
    element?.classList.add('selected');

    if (name === "Tất cả nhạc") {
        currentPlaylist = Object.keys(SONGS_META).map(f => ({
            ...SONGS_META[f],
            file: f
        }));
        currentIndex = 0;

        grid.classList.remove("playlist-active");
        document.querySelectorAll('.disk').forEach(d => d.style.display = "block");

        if (currentPlaylist.length)
            playSong(currentPlaylist[0].file);

        return;
    }

    await reloadPlaylists();

    if (!PLAYLISTS[name]) return showToast("Playlist không tồn tại", "error");

    const files = PLAYLISTS[name];

    currentPlaylist = files.map(f => SONGS_META[f] ? {...SONGS_META[f], file: f} : null)
                           .filter(Boolean);

    currentIndex = 0;

    if (currentPlaylist.length)
        playSong(currentPlaylist[0].file);

    grid.classList.add("playlist-active");

    document.querySelectorAll(".disk").forEach(disk => {
        const file = disk.getAttribute("data-file");
        disk.style.display = files.includes(file) ? "block" : "none";
    });
}

// =============================
// ADD / REMOVE SONG
// =============================

let chosenFile = null;

function openAddToPlaylist(file) {
    chosenFile = file;

    const list = Object.keys(PLAYLISTS).filter(x => x !== "Tất cả nhạc");
    const container = document.getElementById("playlistChoices");

    container.innerHTML = list.map(name => `
        <label><input type="checkbox" value="${name}"> ${name}</label>
    `).join("");

    document.getElementById("playlistModal").style.display = "flex";
}

function closePlaylistModal() {
    document.getElementById("playlistModal").style.display = "none";
}

document.getElementById("addToPlaylistConfirm").onclick = async function () {
    const checks = [...document.querySelectorAll("#playlistChoices input:checked")];
    if (checks.length === 0) return showToast("Chọn ít nhất 1 playlist!", "info");

    for (const c of checks) {
        await fetch("playlist.php", {
            method: "POST",
            body: new URLSearchParams({
                action: "add",
                playlist: c.value,
                file: chosenFile
            })
        });
    }

    showToast("Đã thêm bài vào playlist!");
    closePlaylistModal();
    reloadPlaylists();
};

async function removeFromPlaylist(file) {
    const active = document.querySelector(".playlist-item.selected");
    if (!active) return;

    const playlist = active.textContent.split("(")[0].trim();
    if (playlist === "Tất cả nhạc")
        return showToast("Không thể xóa khỏi playlist mặc định", "info");

    if (!confirm(`Xóa "${file}" khỏi playlist "${playlist}"?`)) return;

    const res = await fetch("playlist.php", {
        method: "POST",
        body: new URLSearchParams({
            action: "remove",
            playlist,
            file
        })
    });

    const j = await res.json();
    if (j.success) {
        await reloadPlaylists();
        loadPlaylist(playlist, active);
    } else {
        showToast(j.message, "error");
    }
}

// =============================
// TOAST
// =============================

function showToast(message, type = "success") {
    const box = document.createElement("div");
    box.className = "toast " +
        (type === "error" ? "error" :
         type === "info" ? "info" : "");
    box.textContent = message;

    document.getElementById("toastContainer").appendChild(box);

    setTimeout(() => box.remove(), 3500);
}

// =============================
// KEYBOARD SHORTCUTS
// =============================

document.addEventListener("keydown", function (e) {
    const tag = document.activeElement.tagName.toLowerCase();
    if (tag === "input" || tag === "textarea") return;

    if (document.getElementById("youtubeModal").style.display === "flex") return;

    if (e.code === "Space") {
        e.preventDefault();
        togglePlay();
    }
});

// =============================
// MOBILE MENU
// =============================

document.getElementById("mobileMenuBtn").onclick = () => {
    document.querySelector(".sidebar").classList.toggle("active");
};

// =============================
// CREATE PLAYLIST
// =============================

function createPlaylist() {
    document.getElementById("createPlaylistModal").style.display = "flex";
    document.getElementById("newPlaylistName").focus();
}

document.getElementById("closeCreateModal").onclick = closeCreateModal;
document.getElementById("createPlaylistCancel").onclick = closeCreateModal;

function closeCreateModal() {
    document.getElementById("createPlaylistModal").style.display = "none";
    document.getElementById("newPlaylistName").value = "";
}

document.getElementById("createPlaylistConfirm").onclick = async function () {
    const name = document.getElementById("newPlaylistName").value.trim();
    if (!name) return showToast("Tên playlist không hợp lệ", "error");

    const res = await fetch("playlist.php", {
        method: "POST",
        body: new URLSearchParams({
            action: "create",
            playlist: name
        })
    });

    const j = await res.json();
    if (j.success) {
        await reloadPlaylists();
        rebuildPlaylistList();
        showToast("Tạo playlist thành công", "success");
        closeCreateModal();
    } else {
        showToast(j.message || "Lỗi tạo playlist", "error");
    }
};

function rebuildPlaylistList() {
    const list = document.getElementById("playlistList");
    list.innerHTML = "";

    Object.keys(PLAYLISTS).forEach(name => {
        const li = document.createElement("li");
        li.className = "playlist-item" + (name === "Tất cả nhạc" ? " selected" : "");
        li.textContent = `${name} (${PLAYLISTS[name].length})`;
        li.onclick = () => loadPlaylist(name, li);
        list.appendChild(li);
    });
}

// =============================
// DOWNLOAD STATUS CARD
// =============================

let downloadCheckInterval = null;

function showDownloadCard(status = 'loading') {
    const card = document.getElementById('downloadStatusCard');
    const spinner = card.querySelector('.download-spinner');
    const successIcon = card.querySelector('.download-icon.success');
    const errorIcon = card.querySelector('.download-icon.error');
    
    // Reset
    spinner.style.display = 'none';
    successIcon.style.display = 'none';
    errorIcon.style.display = 'none';
    
    card.classList.add('show');
    
    if (status === 'loading') {
        spinner.style.display = 'block';
    } else if (status === 'success') {
        successIcon.style.display = 'block';
        setTimeout(() => {
            card.classList.remove('show');
        }, 3000);
    } else if (status === 'error') {
        errorIcon.style.display = 'block';
        setTimeout(() => {
            card.classList.remove('show');
        }, 3000);
    }
}

function hideDownloadCard() {
    document.getElementById('downloadStatusCard').classList.remove('show');
}

async function checkDownloadStatus() {
    try {
        const res = await fetch('check_download.php');
        const data = await res.json();
        
        if (!data.isDownloading && data.status === 'success') {
            // Download xong
            clearInterval(downloadCheckInterval);
            showDownloadCard('success');
            showToast(`✓ Đã tải xong: ${data.title}`, 'success');
            
            setTimeout(() => {
                location.reload();
            }, 2000);
            
        } else if (!data.isDownloading && data.status === 'failed') {
            // Download thất bại
            clearInterval(downloadCheckInterval);
            showDownloadCard('error');
            showToast(`✗ Tải thất bại: ${data.title}`, 'error');
        }
        
    } catch (err) {
        console.error('Error checking download status:', err);
    }
}

function startDownloadMonitor() {
    // Clear interval cũ nếu có
    if (downloadCheckInterval) {
        clearInterval(downloadCheckInterval);
    }
    
    // Kiểm tra mỗi 3 giây
    downloadCheckInterval = setInterval(checkDownloadStatus, 3000);
}

// =============================
// YOUTUBE SEARCH MODAL
// =============================

document.getElementById("openYoutubeSearch").onclick = () => {
    document.getElementById("youtubeModal").style.display = "flex";
};

document.querySelector(".close").onclick = () => {
    document.getElementById("youtubeModal").style.display = "none";
};

document.getElementById("searchForm").onsubmit = async function (e) {
    e.preventDefault();
    const query = document.getElementById("searchQuery").value.trim();
    if (!query) return showToast("Nhập từ khóa tìm kiếm", "info");

    const container = document.getElementById("searchResults");
    container.innerHTML = '<p style="text-align:center;color:#aaa;padding:20px;">Đang tìm kiếm...</p>';

    try {
        const res = await fetch("youtube_search.php", {
            method: "POST",
            body: new URLSearchParams({ query })
        });
        const results = await res.json();

        if (results.error) {
            container.innerHTML = `<p style="color:#e74c3c;text-align:center;padding:20px;">Lỗi: ${results.error}</p>`;
            console.error('YouTube Search Error:', results);
            return;
        }

        if (!results.length) {
            container.innerHTML = '<p style="text-align:center;color:#aaa;padding:20px;">Không tìm thấy kết quả</p>';
            return;
        }

        container.innerHTML = results.map(r => `
            <div class="result-item" onclick="downloadVideo('${r.id}')">
                <img src="${r.thumbnail}" 
                     alt="${r.title}" 
                     style="width:100%;height:180px;object-fit:cover;border-radius:8px 8px 0 0;"
                     onerror="this.src='https://via.placeholder.com/320x180?text=No+Image'">
                <div style="padding:12px;">
                    <p style="font-weight:600;margin-bottom:6px;font-size:14px;line-height:1.4;">${r.title}</p>
                    <p style="color:#aaa;font-size:12px;">${r.duration || 'N/A'}</p>
                </div>
            </div>
        `).join("");
        
    } catch (err) {
        container.innerHTML = `<p style="color:#e74c3c;text-align:center;padding:20px;">Lỗi: ${err.message}</p>`;
        console.error('Fetch error:', err);
    }
};

async function downloadVideo(id) {
    const url = `https://www.youtube.com/watch?v=${id}`;
    
    // Hiện card đang tải
    showDownloadCard('loading');
    showToast("Đang tải bài hát...", "info");
    
    try {
        const res = await fetch("download.php", {
            method: "POST",
            body: new URLSearchParams({ query: url })
        });
        
        const data = await res.json();
        
        if (data.success) {
            document.getElementById("youtubeModal").style.display = "none";
            
            // Bắt đầu monitor để kiểm tra trạng thái
            startDownloadMonitor();
            
        } else {
            showDownloadCard('error');
            showToast(data.message || "Lỗi tải nhạc", "error");
        }
        
    } catch (err) {
        showDownloadCard('error');
        showToast("Lỗi tải: " + err.message, "error");
    }

}
// Update hàm removeFromPlaylist
async function removeFromPlaylist(file) {
    const active = document.querySelector(".playlist-item.selected");
    if (!active) return;

    const playlist = active.textContent.split("(")[0].trim();
    
    // Nếu đang ở "Tất cả nhạc" → XÓA FILE KHỎI SERVER
    if (playlist === "Tất cả nhạc") {
        if (!confirm(`⚠️ XÓA VĨNH VIỄN bài "${file}" khỏi server?\n\nHành động này không thể hoàn tác!`)) {
            return;
        }
        
        const res = await fetch("delete_file.php", {
            method: "POST",
            body: new URLSearchParams({
                file: file
            })
        });
        
        const j = await res.json();
        
        if (j.success) {
            showToast("✓ Đã xóa file khỏi server", "success");
            
            // Xóa khỏi SONGS_META
            delete SONGS_META[file];
            
            // Reload trang sau 1s
            setTimeout(() => location.reload(), 1000);
        } else {
            showToast("✗ " + (j.message || "Lỗi xóa file"), "error");
        }
        
        return;
    }
    
    // Nếu đang ở playlist khác → CHỈ XÓA KHỎI PLAYLIST
    if (!confirm(`Xóa "${file}" khỏi playlist "${playlist}"?`)) return;

    const res = await fetch("playlist.php", {
        method: "POST",
        body: new URLSearchParams({
            action: "remove",
            playlist,
            file
        })
    });

    const j = await res.json();
    if (j.success) {
        await reloadPlaylists();
        loadPlaylist(playlist, active);
        showToast("✓ Đã xóa khỏi playlist", "success");
    } else {
        showToast(j.message, "error");
    }
}
