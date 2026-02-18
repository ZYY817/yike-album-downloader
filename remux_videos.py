# File: tools/yike-album/remux_videos.py
"""将 TS 封装的视频文件无损转封装为正确的 MP4/MOV 容器"""
import subprocess
import shutil
import sys
from pathlib import Path

from config import DOWNLOAD_DIR


def find_ffmpeg() -> str:
    """查找 ffmpeg 可执行文件"""
    path = shutil.which("ffmpeg")
    if path:
        return path
    # winget 安装的常见位置
    candidates = [
        Path.home() / "AppData/Local/Microsoft/WinGet/Links/ffmpeg.exe",
        Path(r"C:\ProgramData\chocolatey\bin\ffmpeg.exe"),
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    return ""


def is_ts_container(filepath: Path) -> bool:
    """检查文件是否为 MPEG-TS 封装（0x47 sync byte）"""
    try:
        with open(filepath, "rb") as f:
            return f.read(1) == b"\x47"
    except (OSError, IOError):
        return False


def remux_one(ffmpeg: str, src: Path) -> bool:
    """无损转封装单个文件: TS → MP4/MOV"""
    ext = src.suffix.lower()
    # MOV 保持 MOV 容器，MP4 保持 MP4 容器
    out_ext = ".mov" if ext == ".mov" else ".mp4"
    tmp = src.with_suffix(f".remux{out_ext}")
    try:
        result = subprocess.run(
            [ffmpeg, "-y", "-i", str(src),
             "-c", "copy", "-movflags", "+faststart",
             str(tmp)],
            capture_output=True, text=True, timeout=300,
        )
        if result.returncode != 0:
            print(f"  [转封装失败] {src.name}: {result.stderr[:200]}")
            tmp.unlink(missing_ok=True)
            return False
        # 验证输出文件有效（ftyp 头）
        with open(tmp, "rb") as f:
            head = f.read(8)
        if head[4:8] != b"ftyp":
            print(f"  [转封装异常] {src.name}: 输出非 MP4/MOV 容器")
            tmp.unlink(missing_ok=True)
            return False
        # 替换原文件
        src.unlink()
        tmp.rename(src)
        return True
    except subprocess.TimeoutExpired:
        print(f"  [超时] {src.name}")
        tmp.unlink(missing_ok=True)
        return False
    except Exception as e:
        print(f"  [异常] {src.name}: {e}")
        tmp.unlink(missing_ok=True)
        return False


def main():
    print("=" * 50)
    print("  视频转封装 (TS → MP4/MOV, 无损)")
    print("=" * 50)

    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        print("[错误] 未找到 ffmpeg，请先安装: winget install Gyan.FFmpeg")
        sys.exit(1)
    print(f"[ffmpeg] {ffmpeg}")

    if not DOWNLOAD_DIR.exists():
        print(f"[错误] 下载目录不存在: {DOWNLOAD_DIR}")
        sys.exit(1)

    # 扫描所有视频文件
    video_exts = {".mp4", ".mov"}
    videos = [
        f for f in DOWNLOAD_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in video_exts
    ]
    print(f"[扫描] 视频文件总数: {len(videos)}")

    # 筛选出 TS 封装的
    ts_videos = [f for f in videos if is_ts_container(f)]
    already_ok = len(videos) - len(ts_videos)
    print(f"[分析] 需转封装: {len(ts_videos)}, 已正常: {already_ok}")

    if not ts_videos:
        print("[完成] 所有视频已是正确容器格式")
        return

    ok, fail = 0, 0
    for i, f in enumerate(ts_videos, 1):
        print(f"[{i}/{len(ts_videos)}] {f.name} ({f.stat().st_size // 1024}KB)")
        if remux_one(ffmpeg, f):
            ok += 1
            print(f"  [完成]")
        else:
            fail += 1

    print(f"\n[转封装结束] 成功={ok} 失败={fail}")


if __name__ == "__main__":
    main()
