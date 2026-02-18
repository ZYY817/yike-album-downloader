# File: tools/yike-album/config.py
"""一刻相册下载工具 - 配置"""
import os
from pathlib import Path

DOWNLOAD_DIR = Path(os.environ.get(
    "YIKE_DOWNLOAD_DIR", r"E:\照片"
))
ORGANIZED_DIR = Path(os.environ.get(
    "YIKE_ORGANIZED_DIR", r"E:\照片_整理"
))
CONCURRENT_DOWNLOADS = int(os.environ.get("YIKE_CONCURRENT", "15"))
DOWNLOAD_TIMEOUT = int(os.environ.get("YIKE_TIMEOUT", "180"))
REQUEST_DELAY = float(os.environ.get("YIKE_DELAY", "0.2"))

PROBE_RESULT_FILE = Path(__file__).parent / "probe_result.json"
PROGRESS_FILE = Path(__file__).parent / "download_progress.json"

YIKE_HOME = "https://photo.baidu.com/photo/web/home"
API_BASE = "https://photo.baidu.com"
LIST_API = "/youai/file/v1/list"
DOWNLOAD_API = "/youai/file/v2/download"
LIST_PAGE_SIZE = 100

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]


def find_chrome() -> str:
    for p in CHROME_CANDIDATES:
        if os.path.isfile(p):
            return p
    raise FileNotFoundError("未找到 Chrome，请安装或修改 CHROME_CANDIDATES")
