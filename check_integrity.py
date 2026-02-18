# File: tools/yike-album/check_integrity.py
"""完整性核对：对比API数据和本地文件"""
import json
from pathlib import Path
from config import DOWNLOAD_DIR

def main():
    print("=" * 70)
    print("  一刻相册下载完整性核对")
    print("=" * 70)
    
    meta_file = DOWNLOAD_DIR / "_photo_meta.json"
    if not meta_file.exists():
        print(f"\n[错误] 未找到元数据文件: {meta_file}")
        return
    
    meta_data = json.loads(meta_file.read_text(encoding="utf-8"))
    print(f"\nAPI返回总数: {len(meta_data):,} 个文件")
    
    video_exts = {'.mp4', '.mov', '.avi', '.mkv', '.m4v'}
    api_photos = []
    api_videos = []
    
    for item in meta_data:
        path = item.get('path', '')
        ext = Path(path).suffix.lower()
        if ext in video_exts:
            api_videos.append(item)
        else:
            api_photos.append(item)
    
    print(f"  - 照片: {len(api_photos):,} 张")
    print(f"  - 视频: {len(api_videos):,} 个")
    
    if not DOWNLOAD_DIR.exists():
        print(f"\n[错误] 下载目录不存在: {DOWNLOAD_DIR}")
        return
    
    local_files = [f for f in DOWNLOAD_DIR.glob('*') 
                   if f.is_file() and not f.name.startswith('_')]
    
    print(f"\n本地文件总数: {len(local_files):,} 个")
    
    photo_exts = {'.jpg', '.jpeg', '.png', '.heic', '.gif', '.bmp', '.webp', '.heif'}
    local_photos = [f for f in local_files if f.suffix.lower() in photo_exts]
    local_videos = [f for f in local_files if f.suffix.lower() in video_exts]
    local_other = [f for f in local_files 
                   if f.suffix.lower() not in photo_exts 
                   and f.suffix.lower() not in video_exts]
    
    print(f"  - 照片: {len(local_photos):,} 张")
    print(f"  - 视频: {len(local_videos):,} 个")
    if local_other:
        print(f"  - 其他: {len(local_other):,} 个")
        ext_counts = {}
        for f in local_other:
            ext = f.suffix.lower()
            ext_counts[ext] = ext_counts.get(ext, 0) + 1
        for ext, count in sorted(ext_counts.items()):
            print(f"      {ext}: {count:,} 个")
    
    print(f"\n{'=' * 70}")
    print("  数量对比")
    print(f"{'=' * 70}")
    
    photo_diff = len(local_photos) - len(api_photos)
    video_diff = len(local_videos) - len(api_videos)
    total_diff = len(local_files) - len(meta_data)
    
    print(f"\n照片: API {len(api_photos):,} vs 本地 {len(local_photos):,} "
          f"(差异: {photo_diff:+,})")
    print(f"视频: API {len(api_videos):,} vs 本地 {len(local_videos):,} "
          f"(差异: {video_diff:+,})")
    print(f"总计: API {len(meta_data):,} vs 本地 {len(local_files):,} "
          f"(差异: {total_diff:+,})")
    
    print(f"\n{'=' * 70}")
    if total_diff == 0:
        print("  ✓ 数量完全一致！")
    elif total_diff > 0:
        print(f"  ⚠ 本地文件比API多 {total_diff:,} 个")
        if local_other:
            print(f"     可能原因: 包含 {len(local_other):,} 个特殊格式文件")
    else:
        print(f"  ✗ 本地文件比API少 {-total_diff:,} 个，可能有文件未下载")
    
    total_size = sum(f.stat().st_size for f in local_files)
    print(f"\n本地文件总大小: {total_size / 1024 / 1024 / 1024:.2f} GB")
    print(f"保存位置: {DOWNLOAD_DIR}")
    print("=" * 70)

if __name__ == "__main__":
    main()
