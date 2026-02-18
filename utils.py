# File: tools/yike-album/utils.py
"""公共工具模块"""
import json
import sys
from pathlib import Path
from datetime import datetime
import httpx
from config import PROBE_RESULT_FILE, API_BASE, DOWNLOAD_API


def load_cookies() -> dict:
    """加载 probe 保存的 Cookie"""
    if not PROBE_RESULT_FILE.exists():
        print("[错误] 未找到 Cookie，请先运行: python probe.py")
        sys.exit(1)
    data = json.loads(PROBE_RESULT_FILE.read_text(encoding="utf-8"))
    cookies = {}
    for c in data.get("cookies", []):
        cookies[c["name"]] = c["value"]
    if not cookies:
        print("[错误] Cookie 为空，请重新运行 probe.py")
        sys.exit(1)
    return cookies


def make_client(cookies: dict) -> httpx.Client:
    """创建 httpx Client，完全模仿浏览器"""
    return httpx.Client(
        cookies=cookies,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Referer": "https://photo.baidu.com/",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        },
        follow_redirects=True,
        timeout=30,
    )


def get_download_link(client: httpx.Client, fsid: str) -> str:
    """获取下载直链（VIP用户可下载大文件）"""
    params = {"clienttype": "70", "fsid": fsid}
    resp = client.get(API_BASE + DOWNLOAD_API, params=params, timeout=30)
    data = resp.json()
    if data.get("errno") != 0:
        errno = data.get("errno")
        if errno == 50007:
            raise RuntimeError("需要VIP会员")
        raise RuntimeError(f"获取链接失败: errno={errno}")
    dlink = data.get("dlink", "")
    if not dlink:
        raise RuntimeError("dlink为空")
    return dlink


def make_filename(photo: dict) -> str:
    """根据拍摄时间生成文件名"""
    ext = Path(photo.get("path", ".jpg")).suffix or ".jpg"
    exif_dt = (photo.get("extra_info") or {}).get("date_time", "")
    if exif_dt:
        try:
            dt = datetime.strptime(exif_dt, "%Y:%m:%d %H:%M:%S")
            return dt.strftime("%Y%m%d_%H%M%S") + f"_{photo['fsid']}{ext}"
        except ValueError:
            pass
    ts = photo.get("shoot_time", 0)
    if ts:
        dt = datetime.fromtimestamp(ts)
        return dt.strftime("%Y%m%d_%H%M%S") + f"_{photo['fsid']}{ext}"
    return f"unknown_{photo['fsid']}{ext}"


def format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f}KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / 1024 / 1024:.1f}MB"
    else:
        return f"{size_bytes / 1024 / 1024 / 1024:.2f}GB"


def load_progress(progress_file: Path) -> set:
    """加载进度文件"""
    if not progress_file.exists():
        return set()
    data = json.loads(progress_file.read_text(encoding="utf-8"))
    return set(data.get("downloaded", []))


def save_progress(progress_file: Path, downloaded: set):
    """保存进度文件"""
    progress_file.write_text(
        json.dumps({"downloaded": sorted(downloaded)}, ensure_ascii=False),
        encoding="utf-8",
    )
