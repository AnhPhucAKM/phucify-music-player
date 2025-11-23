#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto Download System - Fixed UTF-8 encoding cho tiếng Việt
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

# Force UTF-8 encoding
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

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
    """Làm sạch tên file - GIỮ NGUYÊN tiếng Việt, chỉ xóa ký tự không hợp lệ"""
    # Normalize Unicode về dạng NFC (composed form)
    name = unicodedata.normalize("NFC", name)
    
    # Chỉ loại bỏ các ký tự không hợp lệ trong filesystem
    # GIỮ NGUYÊN: tiếng Việt, chữ cái, số, khoảng trắng, dấu gạch ngang
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', name)
    
    # Trim whitespace
    name = name.strip()
    
    # Thay thế nhiều khoảng trắng liên tiếp thành 1
    name = re.sub(r'\s+', ' ', name)
    
    # Giới hạn độ dài (filesystem limit)
    if len(name.encode('utf-8')) > 200:
        # Cắt theo bytes để tránh cắt giữa ký tự UTF-8
        name_bytes = name.encode('utf-8')[:200]
        # Decode an toàn
        name = name_bytes.decode('utf-8', errors='ignore').strip()
    
    # Nếu tên rỗng sau khi clean thì dùng timestamp
    if not name:
        name = f"audio_{int(time.time())}"
    
    return name

def set_file_permissions(filepath):
    """Set quyền cho file"""
    try:
        if os.name != 'posix':
            return
        
        subprocess.run(
            ['chown', 'phuc:www-data', filepath],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5
        )
        
        subprocess.run(
            ['chmod', '664', filepath],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5
        )
        
        log(f"✓ Set permissions: {os.path.basename(filepath)}")
        
    except Exception as e:
        log(f"⚠ Cannot set permissions: {str(e)}")

def log(msg):
    """Ghi log với UTF-8 encoding"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}\n"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception as e:
        print(f"Log error: {e}", file=sys.stderr)
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
    """Lấy thông tin video với UTF-8 encoding"""
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
            encoding='utf-8',
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
    """Download thumbnail với UTF-8 filename"""
    try:
        thumb_path = os.path.join(COVERS_DIR, f"{clean_title}.jpg")
        
        # Nếu đã có thumbnail thì skip
        if os.path.exists(thumb_path):
            log(f"✓ Thumbnail exists: {clean_title}")
            set_file_permissions(thumb_path)
            return True
        
        # Download vào temp file trước
        temp_name = f"temp_{int(time.time())}"
        temp_path = os.path.join(COVERS_DIR, temp_name)
        
        cmd = [
            "yt-dlp",
            "--skip-download",
            "--write-thumbnail",
            "--convert-thumbnails", "jpg",
            "--no-warnings",
            "-o", f"{temp_path}.%(ext)s",
            f"https://www.youtube.com/watch?v={video_id}"
        ]
        
        subprocess.run(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            timeout=30
        )
        
        # Tìm file temp thumbnail
        temp_jpg = f"{temp_path}.jpg"
        if os.path.exists(temp_jpg):
            # Rename thành tên đúng
            shutil.move(temp_jpg, thumb_path)
            log(f"✓ Thumbnail downloaded: {clean_title}")
            set_file_permissions(thumb_path)
            return True
        
        log(f"⚠ Thumbnail failed: {clean_title}")
        return False
            
    except Exception as e:
        log(f"ERROR thumbnail: {str(e)}")
        return False

def download_audio(target, clean_title):
    """Download audio với UTF-8 filename"""
    try:
        # Tên file output
        audio_path = os.path.join(AUDIO_DIR, f"{clean_title}.mp3")
        
        # Check if file already exists
        if os.path.exists(audio_path):
            log(f"✓ Audio exists: {clean_title}")
            set_file_permissions(audio_path)
            return True
        
        # Download vào temp file trước
        temp_name = f"temp_{int(time.time())}"
        temp_output = os.path.join(AUDIO_DIR, f"{temp_name}.%(ext)s")
        
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
            text=True,
            encoding='utf-8'
        )

        stdout, stderr = proc.communicate(timeout=300)

        # Tìm file temp đã download
        temp_files = [f for f in os.listdir(AUDIO_DIR) if f.startswith(temp_name) and f.endswith('.mp3')]
        
        if proc.returncode == 0 and temp_files:
            # Rename file temp thành tên đúng (UTF-8)
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
    """Download với UTF-8 support"""
    
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
