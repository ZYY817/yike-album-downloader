# File: tools/yike-album/stats.py
"""统计下载的照片和视频"""
from pathlib import Path
from config import DOWNLOAD_DIR

def main():
    if not DOWNLOAD_DIR.exists():
        print(f"目录不存在: {DOWNLOAD_DIR}")
        return
    
    photo_exts = {'.jpg', '.jpeg', '.png', '.heic', '.gif', '.bmp', '.webp', '.heif'}
    video_exts = {'.mp4', '.mov', '.avi', '.mkv', '.m4v'}
    
    photos = []
    videos = []
    other = []
    
    for f in DOWNLOAD_DIR.glob('*'):
        if not f.is_file() or f.name.startswith('_'):
            continue
        ext = f.suffix.lower()
        if ext in photo_exts:
            photos.append(f)
        elif ext in video_exts:
            videos.append(f)
        else:
            other.append(f)
    
    total_size = sum(f.stat().st_size for f in photos + videos + other)
    
    print("=" * 60)
    print("  一刻相册下载统计")
    print("=" * 60)
    print(f"\n照片: {len(photos):,} 张")
    print(f"视频: {len(videos):,} 个")
    if other:
        print(f"其他: {len(other):,} 个")
    print(f"\n总计: {len(photos) + len(videos) + len(other):,} 个文件")
    print(f"总大小: {total_size / 1024 / 1024 / 1024:.2f} GB")
    print(f"\n保存位置: {DOWNLOAD_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    main()
