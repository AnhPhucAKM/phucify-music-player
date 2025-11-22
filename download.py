#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path
import datetime
import time
import json

BASE_DIR = os.path.dirname(__file__)
AUDIO_DIR = os.path.join(BASE_DIR, 'audio')
COVERS_DIR = os.path.join(BASE_DIR, 'covers')
COOKIE_FILE = os.path.join(BASE_DIR, 'cookies.txt')

def log(msg):
    log_file = os.path.join(AUDIO_DIR, "download.log")
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}\n"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(line)
    print(msg)

def download_thumbnail(video_id, filename):
    """Download thumbnail từ YouTube"""
    try:
        # Tạo thư mục covers nếu chưa có
        if not os.path.exists(COVERS_DIR):
            os.makedirs(COVERS_DIR)
        
        # Tên file thumbnail
        base_name = os.path.splitext(filename)[0]
        thumb_path = os.path.join(COVERS_DIR, f"{base_name}.jpg")
        
        # Download thumbnail bằng yt-dlp
        cmd = [
            "yt-dlp",
            "--skip-download",
            "--write-thumbnail",
            "--convert-thumbnails", "jpg",
            "-o", os.path.join(COVERS_DIR, f"{base_name}.%(ext)s"),
            f"https://www.youtube.com/watch?v={video_id}"
        ]
        
        log(f"Downloading thumbnail: {thumb_path}")
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        
        # Kiểm tra xem file đã được tạo chưa
        if os.path.exists(thumb_path):
            log(f"✓ Thumbnail saved: {thumb_path}")
            return True
        else:
            log("⚠ Thumbnail download failed")
            return False
            
    except Exception as e:
        log(f"ERROR downloading thumbnail: {str(e)}")
        return False

def get_video_info(target):
    """Lấy thông tin video (ID, title) từ URL hoặc search query"""
    try:
        cmd = [
            "yt-dlp",
            "--dump-json",
            "--no-playlist",
            target
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            info = json.loads(result.stdout)
            return {
                'id': info.get('id'),
                'title': info.get('title'),
                'filename': f"{info.get('title')}.mp3"
            }
        return None
        
    except Exception as e:
        log(f"ERROR getting video info: {str(e)}")
        return None

def build_command(target):
    cmd = [
        "yt-dlp",
        "--no-cache-dir",
        "--force-ipv4",
        "--user-agent",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "-x",
        "--audio-format", "mp3",
        "--no-playlist",
        "--socket-timeout", "30",
        "--retries", "5",
        "-o", os.path.join(AUDIO_DIR, "%(title)s.%(ext)s"),
        target
    ]

    if os.path.exists(COOKIE_FILE):
        cmd.insert(1, f"--cookies={COOKIE_FILE}")

    return cmd

def download(target):
    if not os.path.exists(AUDIO_DIR):
        os.makedirs(AUDIO_DIR)

    log(f"Start: {target}")
    
    # Lấy thông tin video trước
    video_info = get_video_info(target)
    
    if video_info:
        log(f"Video ID: {video_info['id']}")
        log(f"Title: {video_info['title']}")
        
        # Download thumbnail trước
        download_thumbnail(video_info['id'], video_info['filename'])
    
    # Download audio
    cmd = build_command(target)
    log("RUN: " + " ".join(cmd))

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        try:
            stdout, stderr = proc.communicate(timeout=300)

            if proc.returncode == 0:
                log("✓ Download complete")
                return True
            else:
                err = stderr.strip() or stdout.strip()
                log("ERROR: " + err[:300])
                return False

        except subprocess.TimeoutExpired:
            log("ERROR: Timeout 300s — killing yt-dlp")
            proc.kill()
            return False

    except Exception as e:
        log("ERROR: " + str(e))
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        log("Usage: python download.py <URL | search text>")
        sys.exit(1)

    q = sys.argv[1]

    if q.startswith("http://") or q.startswith("https://"):
        target = q
        log(f"URL: {target}")
    else:
        target = f"ytsearch1:{q}"
        log(f"Search: {target}")

    download(target)