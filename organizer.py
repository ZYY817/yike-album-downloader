# File: tools/yike-album/organizer.py
"""照片整理器：按拍摄日期归类到 YYYY/YYYY-MM/ 文件夹"""
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

from config import DOWNLOAD_DIR, ORGANIZED_DIR


def extract_date_from_filename(name: str):
    """从文件名提取日期（格式 YYYYMMDD_HHMMSS_xxx）"""
    m = re.match(r"(\d{4})(\d{2})(\d{2})_\d{6}_", name)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None, None


def extract_date_from_exif(filepath: Path):
    """尝试从 EXIF 读取拍摄日期"""
    try:
        from PIL import Image
        from PIL.ExifTags import Base as ExifBase
        img = Image.open(filepath)
        exif = img.getexif()
        if not exif:
            return None, None
        dt_str = exif.get(ExifBase.DateTimeOriginal) or exif.get(ExifBase.DateTime)
        if not dt_str:
            return None, None
        dt = datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")
        return dt.year, dt.month
    except Exception:
        return None, None


def extract_date_from_mtime(filepath: Path):
    """回退：用文件修改时间"""
    try:
        ts = filepath.stat().st_mtime
        dt = datetime.fromtimestamp(ts)
        return dt.year, dt.month
    except Exception:
        return None, None


def get_date(filepath: Path):
    """三级回退获取日期：文件名 → EXIF → 修改时间"""
    year, month = extract_date_from_filename(filepath.name)
    if year:
        return year, month
    year, month = extract_date_from_exif(filepath)
    if year:
        return year, month
    return extract_date_from_mtime(filepath)


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp",
              ".webp", ".heic", ".heif", ".mp4", ".mov", ".avi"}


def main():
    print("=" * 50)
    print("  照片整理器 - 按日期归类")
    print("=" * 50)
    if not DOWNLOAD_DIR.exists():
        print(f"[整理] 下载目录不存在: {DOWNLOAD_DIR}")
        sys.exit(1)
    ORGANIZED_DIR.mkdir(parents=True, exist_ok=True)
    files = [f for f in DOWNLOAD_DIR.iterdir()
             if f.is_file() and f.suffix.lower() in IMAGE_EXTS]
    if not files:
        print("[整理] 未找到照片文件")
        return
    print(f"[整理] 找到 {len(files)} 个文件")
    moved, failed = 0, 0
    for i, fp in enumerate(files, 1):
        year, month = get_date(fp)
        if not year:
            dest_dir = ORGANIZED_DIR / "unknown"
        else:
            dest_dir = ORGANIZED_DIR / str(year) / f"{year}-{month:02d}"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / fp.name
        if dest.exists():
            dest = dest_dir / f"{fp.stem}_dup{fp.suffix}"
        try:
            shutil.copy2(fp, dest)
            moved += 1
        except Exception as e:
            print(f"  [失败] {fp.name}: {e}")
            failed += 1
        if i % 100 == 0:
            print(f"[整理] 进度: {i}/{len(files)}")
    print(f"\n[整理] 完成! 移动={moved} 失败={failed}")
    print(f"[整理] 输出目录: {ORGANIZED_DIR}")


if __name__ == "__main__":
    main()
