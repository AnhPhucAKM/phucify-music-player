#!/usr/bin/env python3
"""
Auto Download System - Tự động tải nhạc, không cần worker thủ công
Chỉ 1 process tải tại 1 thời điểm (dùng lock file)
"""

import os
import sys
import subprocess
import json
import time
import datetime
import fcntl
from pathlib import Path
import re
import unicodedata
import shutil

BASE_DIR = os.path.dirname(__file__)
AUDIO_DIR = os.path.join(BASE_DIR, 'audio')
COVERS_DIR = os.path.join(BASE_DIR, 'covers')
LOCK_FILE = os.path.join(BASE_DIR, '.download.lock')
LOG_FILE = os.path.join(AUDIO_DIR, 'download.log')
COOKIE_FILE = os.path.join(BASE_DIR, 'cookies.txt')

# Tạo thư mục
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(COVERS_DIR, exist_ok=True)

def clean_filename(name):
    """Làm sạch tên file - loại bỏ ký tự đặc biệt, giới hạn độ dài"""
    # Normalize Unicode
    name = unicodedata.normalize("NFKC", name)
    
    # Loại bỏ ký tự không hợp lệ
    name = re.sub(r'[\\/*?:"<>|]', '', name)
    name = name.replace("/", "-")
    name = name.strip()
    
    # Giới hạn độ dài (tránh lỗi filesystem)
    if len(name) > 200:
        name = name[:200].strip()
    
    # Nếu tên rỗng sau khi clean thì dùng timestamp
    if not name:
        name = f"audio_{int(time.time())}"
    
    return name

def set_file_permissions(filepath):
    """Set quyền phuc:www-data cho file"""
    try:
        # Chỉ chạy trên Linux
        if os.name != 'posix':
            return
        
        # Set owner thành phuc:www-data
        subprocess.run(
            ['chown', 'phuc:www-data', filepath],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Set permissions 664 (rw-rw-r--)
        subprocess.run(
            ['chmod', '664', filepath],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        log(f"✓ Set permissions: {os.path.basename(filepath)}")
        
    except Exception as e:
        log(f"⚠ Cannot set permissions: {str(e)}")

def log(msg):
    """Ghi log"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}\n"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)
    except:
        pass
    print(msg)

def acquire_lock(lock_fd):
    """Thử lấy lock (non-blocking)"""
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except IOError:
        return False

def release_lock(lock_fd):
    """Nhả lock"""
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
    except:
        pass

def get_video_info(target):
    """Lấy thông tin video"""
    try:
        cmd = [
            "yt-dlp",
            "--dump-json",
            "--no-playlist",
            "--no-warnings",
            target
        ]
        
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=30
        )
        
        if result.returncode == 0:
            info = json.loads(result.stdout)
            return {
                'id': info.get('id'),
                'title': info.get('title'),
                'duration': info.get('duration', 0)
            }
        return None
        
    except Exception as e:
        log(f"ERROR getting video info: {str(e)}")
        return None

def download_thumbnail(video_id, clean_title):
    """Download thumbnail"""
    try:
        thumb_path = os.path.join(COVERS_DIR, f"{clean_title}.jpg")
        
        # Nếu đã có thumbnail thì skip
        if os.path.exists(thumb_path):
            log(f"✓ Thumbnail exists: {clean_title}")
            set_file_permissions(thumb_path)
            return True
        
        cmd = [
            "yt-dlp",
            "--skip-download",
            "--write-thumbnail",
            "--convert-thumbnails", "jpg",
            "--no-warnings",
            "-o", os.path.join(COVERS_DIR, f"{clean_title}.%(ext)s"),
            f"https://www.youtube.com/watch?v={video_id}"
        ]
        
        subprocess.run(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            timeout=30
        )
        
        if os.path.exists(thumb_path):
            log(f"✓ Thumbnail downloaded: {clean_title}")
            set_file_permissions(thumb_path)
            return True
        
        log(f"⚠ Thumbnail failed: {clean_title}")
        return False
            
    except Exception as e:
        log(f"ERROR thumbnail: {str(e)}")
        return False

def download_audio(target, clean_title):
    """Download audio với tên file đã clean"""
    try:
        # Tên file output
        audio_path = os.path.join(AUDIO_DIR, f"{clean_title}.mp3")
        
        # Check if file already exists
        if os.path.exists(audio_path):
            log(f"✓ Audio exists: {clean_title}")
            set_file_permissions(audio_path)
            return True
        
        # Download vào temp file trước
        temp_output = os.path.join(AUDIO_DIR, f"temp_{int(time.time())}.%(ext)s")
        
        cmd = [
            "yt-dlp",
            "--no-cache-dir",
            "-x",
            "--audio-format", "mp3",
            "--audio-quality", "0",
            "--no-playlist",
            "--no-warnings",
            "--socket-timeout", "30",
            "--retries", "3",
            "--no-continue",
            "-o", temp_output,
            target
        ]

        if os.path.exists(COOKIE_FILE):
            cmd.insert(1, f"--cookies={COOKIE_FILE}")

        log(f"⬇ Downloading audio: {clean_title}")
        
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout, stderr = proc.communicate(timeout=300)

        # Tìm file temp đã download
        temp_files = [f for f in os.listdir(AUDIO_DIR) if f.startswith('temp_') and f.endswith('.mp3')]
        
        if proc.returncode == 0 and temp_files:
            # Rename file temp thành tên đúng
            temp_file = os.path.join(AUDIO_DIR, temp_files[0])
            shutil.move(temp_file, audio_path)
            
            log(f"✅ Downloaded: {clean_title}")
            set_file_permissions(audio_path)
            return True
        else:
            err = stderr.strip() or stdout.strip()
            log(f"❌ Failed: {err[:300]}")
            
            # Cleanup temp files
            for tf in temp_files:
                try:
                    os.remove(os.path.join(AUDIO_DIR, tf))
                except:
                    pass
            
            return False

    except subprocess.TimeoutExpired:
        log(f"⏱ Timeout: {clean_title}")
        proc.kill()
        return False
    except Exception as e:
        log(f"❌ Error: {str(e)}")
        return False

def download(query):
    """Download với lock để tránh xung đột"""
    
    # Mở lock file
    lock_fd = open(LOCK_FILE, 'w')
    
    # Thử lấy lock
    if not acquire_lock(lock_fd):
        log("⏳ Another download in progress, exiting...")
        lock_fd.close()
        return False
    
    try:
        log(f"\n{'='*60}")
        log(f"🎵 Processing: {query}")
        
        # Xác định target
        if query.startswith("http://") or query.startswith("https://"):
            target = query
        else:
            target = f"ytsearch1:{query}"
        
        # Lấy thông tin video
        log("📡 Fetching video info...")
        video_info = get_video_info(target)
        
        if not video_info:
            log("❌ Cannot get video info")
            return False
        
        raw_title = video_info['title']
        clean_title = clean_filename(raw_title)
        video_id = video_info['id']
        
        log(f"📌 Original Title: {raw_title}")
        log(f"📌 Clean Title: {clean_title}")
        log(f"📌 Video ID: {video_id}")
        log(f"📌 Duration: {video_info.get('duration', 0)}s")
        
        # Download thumbnail
        download_thumbnail(video_id, clean_title)
        
        # Download audio
        success = download_audio(target, clean_title)
        
        if success:
            log(f"✅ SUCCESS: {clean_title}")
        else:
            log(f"❌ FAILED: {clean_title}")
        
        return success
        
    finally:
        # Nhả lock
        release_lock(lock_fd)
        lock_fd.close()
        try:
            os.remove(LOCK_FILE)
        except:
            pass

def main():
    if len(sys.argv) < 2:
        print("Usage: python download_system.py <URL | search query>")
        sys.exit(1)
    
    query = sys.argv[1]
    success = download(query)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Auto Download System - Tự động tải nhạc, không cần worker thủ công
Chỉ 1 process tải tại 1 thời điểm (dùng lock file)
"""

import os
import sys
import subprocess
import json
import time
import datetime
import fcntl
from pathlib import Path

BASE_DIR = os.path.dirname(__file__)
AUDIO_DIR = os.path.join(BASE_DIR, 'audio')
COVERS_DIR = os.path.join(BASE_DIR, 'covers')
LOCK_FILE = os.path.join(BASE_DIR, '.download.lock')
LOG_FILE = os.path.join(AUDIO_DIR, 'download.log')
COOKIE_FILE = os.path.join(BASE_DIR, 'cookies.txt')

# Tạo thư mục
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(COVERS_DIR, exist_ok=True)

def log(msg):
    """Ghi log"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}\n"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)
    except:
        pass
    print(msg)

def acquire_lock(lock_fd):
    """Thử lấy lock (non-blocking)"""
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except IOError:
        return False

def release_lock(lock_fd):
    """Nhả lock"""
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
    except:
        pass

def get_video_info(target):
    """Lấy thông tin video"""
    try:
        cmd = [
            "yt-dlp",
            "--dump-json",
            "--no-playlist",
            "--no-warnings",
            target
        ]
        
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=30
        )
        
        if result.returncode == 0:
            info = json.loads(result.stdout)
            return {
                'id': info.get('id'),
                'title': info.get('title'),
                'duration': info.get('duration', 0)
            }
        return None
        
    except Exception as e:
        log(f"ERROR getting video info: {str(e)}")
        return None

def download_thumbnail(video_id, title):
    """Download thumbnail"""
    try:
        thumb_path = os.path.join(COVERS_DIR, f"{title}.jpg")
        
        # Nếu đã có thumbnail thì skip
        if os.path.exists(thumb_path):
            log(f"✓ Thumbnail exists: {title}")
            return True
        
        cmd = [
            "yt-dlp",
            "--skip-download",
            "--write-thumbnail",
            "--convert-thumbnails", "jpg",
            "--no-warnings",
            "-o", os.path.join(COVERS_DIR, f"{title}.%(ext)s"),
            f"https://www.youtube.com/watch?v={video_id}"
        ]
        
        subprocess.run(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            timeout=30
        )
        
        if os.path.exists(thumb_path):
            log(f"✓ Thumbnail downloaded: {title}")
            return True
        
        log(f"⚠ Thumbnail failed: {title}")
        return False
            
    except Exception as e:
        log(f"ERROR thumbnail: {str(e)}")
        return False

def download_audio(target, title):
    """Download audio"""
    try:
        # Check if file already exists
        audio_path = os.path.join(AUDIO_DIR, f"{title}.mp3")
        if os.path.exists(audio_path):
            log(f"✓ Audio exists: {title}")
            return True
        
        cmd = [
            "yt-dlp",
            "--no-cache-dir",
            "-x",
            "--audio-format", "mp3",
            "--no-playlist",
            "--no-warnings",
            "--socket-timeout", "30",
            "--retries", "3",
            "-o", os.path.join(AUDIO_DIR, "%(title)s.%(ext)s"),
            target
        ]

        if os.path.exists(COOKIE_FILE):
            cmd.insert(1, f"--cookies={COOKIE_FILE}")

        log(f"⬇ Downloading audio: {title}")
        
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout, stderr = proc.communicate(timeout=300)

        if proc.returncode == 0 and os.path.exists(audio_path):
            log(f"✅ Downloaded: {title}")
            return True
        else:
            err = stderr.strip() or stdout.strip()
            log(f"❌ Failed: {err[:200]}")
            return False

    except subprocess.TimeoutExpired:
        log(f"⏱ Timeout: {title}")
        proc.kill()
        return False
    except Exception as e:
        log(f"❌ Error: {str(e)}")
        return False

def download(query):
    """Download với lock để tránh xung đột"""
    
    # Mở lock file
    lock_fd = open(LOCK_FILE, 'w')
    
    # Thử lấy lock
    if not acquire_lock(lock_fd):
        log("⏳ Another download in progress, exiting...")
        lock_fd.close()
        return False
    
    try:
        log(f"\n{'='*60}")
        log(f"🎵 Processing: {query}")
        
        # Xác định target
        if query.startswith("http://") or query.startswith("https://"):
            target = query
        else:
            target = f"ytsearch1:{query}"
        
        # Lấy thông tin video
        log("📡 Fetching video info...")
        video_info = get_video_info(target)
        
        if not video_info:
            log("❌ Cannot get video info")
            return False
        
        title = video_info['title']
        video_id = video_info['id']
        
        log(f"📌 Title: {title}")
        log(f"📌 Video ID: {video_id}")
        log(f"📌 Duration: {video_info.get('duration', 0)}s")
        
        # Download thumbnail
        download_thumbnail(video_id, title)
        
        # Download audio
        success = download_audio(target, title)
        
        if success:
            log(f"✅ SUCCESS: {title}")
        else:
            log(f"❌ FAILED: {title}")
        
        return success
        
    finally:
        # Nhả lock
        release_lock(lock_fd)
        lock_fd.close()
        try:
            os.remove(LOCK_FILE)
        except:
            pass

def main():
    if len(sys.argv) < 2:
        print("Usage: python download_system.py <URL | search query>")
        sys.exit(1)
    
    query = sys.argv[1]
    success = download(query)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()