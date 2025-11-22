#!/usr/bin/env python3
"""
Script để tải thumbnails cho tất cả bài nhạc đã có trong thư mục audio/
Chạy: python sync_thumbnails.py
"""

import os
import subprocess
from pathlib import Path

BASE_DIR = os.path.dirname(__file__)
AUDIO_DIR = os.path.join(BASE_DIR, 'audio')
COVERS_DIR = os.path.join(BASE_DIR, 'covers')

def download_thumbnail_by_search(song_title):
    """Tìm và tải thumbnail từ YouTube bằng tên bài hát"""
    try:
        if not os.path.exists(COVERS_DIR):
            os.makedirs(COVERS_DIR)
        
        # Tên file thumbnail
        thumb_path = os.path.join(COVERS_DIR, f"{song_title}.jpg")
        
        # Nếu đã có thumbnail thì skip
        if os.path.exists(thumb_path):
            print(f"⏭ Skip (already exists): {song_title}")
            return True
        
        # Search trên YouTube và lấy thumbnail
        cmd = [
            "yt-dlp",
            f"ytsearch1:{song_title}",
            "--skip-download",
            "--write-thumbnail",
            "--convert-thumbnails", "jpg",
            "-o", os.path.join(COVERS_DIR, f"{song_title}.%(ext)s")
        ]
        
        print(f"⬇ Downloading: {song_title}...")
        
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            text=True
        )
        
        if os.path.exists(thumb_path):
            print(f"✓ Success: {song_title}")
            return True
        else:
            print(f"✗ Failed: {song_title}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏱ Timeout: {song_title}")
        return False
    except Exception as e:
        print(f"✗ Error ({song_title}): {str(e)}")
        return False

def main():
    if not os.path.exists(AUDIO_DIR):
        print("❌ Thư mục audio/ không tồn tại!")
        return
    
    # Lấy danh sách file MP3
    mp3_files = [f for f in os.listdir(AUDIO_DIR) if f.endswith('.mp3')]
    
    if not mp3_files:
        print("❌ Không có file MP3 nào trong audio/")
        return
    
    print(f"📂 Tìm thấy {len(mp3_files)} bài hát")
    print(f"📥 Bắt đầu tải thumbnails...\n")
    
    success = 0
    failed = 0
    skipped = 0
    
    for i, mp3_file in enumerate(mp3_files, 1):
        song_title = os.path.splitext(mp3_file)[0]
        print(f"[{i}/{len(mp3_files)}] ", end="")
        
        # Kiểm tra xem đã có thumbnail chưa
        has_thumb = False
        for ext in ['jpg', 'jpeg', 'png', 'webp']:
            if os.path.exists(os.path.join(COVERS_DIR, f"{song_title}.{ext}")):
                has_thumb = True
                break
        
        if has_thumb:
            print(f"⏭ Skip (exists): {song_title}")
            skipped += 1
            continue
        
        if download_thumbnail_by_search(song_title):
            success += 1
        else:
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"✅ Thành công: {success}")
    print(f"⏭ Đã có sẵn: {skipped}")
    print(f"❌ Thất bại: {failed}")
    print(f"📊 Tổng cộng: {len(mp3_files)}")

if __name__ == "__main__":
    main()