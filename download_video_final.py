# File: tools/yike-album/download_video_final.py
"""视频批量下载 - 完全模仿照片下载的成功模式"""
import json
import time
import sys
import threading
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx

from config import (
    DOWNLOAD_DIR, PROBE_RESULT_FILE,
    API_BASE, DOWNLOAD_API,
    DOWNLOAD_TIMEOUT, REQUEST_DELAY,
    CONCURRENT_DOWNLOADS,
)


def load_cookies() -> dict:
    """加载 probe 保存的 Cookie"""
    if not PROBE_RESULT_FILE.exists():
        print("[视频] 未找到 Cookie，请先运行: python probe.py")
        sys.exit(1)
    data = json.loads(PROBE_RESULT_FILE.read_text(encoding="utf-8"))
    cookies = {}
    for c in data.get("cookies", []):
        cookies[c["name"]] = c["value"]
    if not cookies:
        print("[视频] Cookie 为空，请重新运行 probe.py")
        sys.exit(1)
    return cookies


def load_failed_videos() -> list:
    """从 _failed.json 加载失败的视频列表"""
    failed_file = DOWNLOAD_DIR / "_failed.json"
    if not failed_file.exists():
        print(f"[视频] 未找到失败列表: {failed_file}")
        return []
    data = json.loads(failed_file.read_text(encoding="utf-8"))
    print(f"[视频] 加载失败列表: {len(data)} 个视频")
    return data


def load_photo_meta() -> dict:
    """加载照片元数据，获取原始大小信息"""
    meta_file = DOWNLOAD_DIR / "_photo_meta.json"
    if not meta_file.exists():
        return {}
    data = json.loads(meta_file.read_text(encoding="utf-8"))
    return {str(item["fsid"]): item for item in data}


def get_download_link(client: httpx.Client, fsid: str) -> str:
    """获取视频的下载直链（VIP用户）"""
    params = {"clienttype": "70", "fsid": fsid}
    resp = client.get(
        API_BASE + DOWNLOAD_API, params=params, timeout=30
    )
    data = resp.json()
    if data.get("errno") != 0:
        errno = data.get("errno")
        if errno == 50007:
            raise RuntimeError(f"需要VIP会员 (errno=50007)")
        raise RuntimeError(f"下载链接获取失败: errno={errno}")
    dlink = data.get("dlink", "")
    if not dlink:
        raise RuntimeError(f"dlink 为空, fsid={fsid}")
    return dlink


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
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
        },
        follow_redirects=True,
        timeout=httpx.Timeout(DOWNLOAD_TIMEOUT, connect=30),
    )


def download_single_video(
    client: httpx.Client, video: dict, download_dir: Path, meta: dict
) -> bool:
    """下载单个视频，成功返回 True"""
    fsid = str(video["fsid"])
    filename = video.get("name", f"{fsid}.mp4")
    dest = download_dir / filename
    
    # 从元数据获取期望大小
    expected_size = 0
    if fsid in meta:
        expected_size = meta[fsid].get("size", 0)
    
    # 已存在且大小匹配 → 跳过
    if dest.exists() and expected_size and dest.stat().st_size == expected_size:
        return True
    
    # 已存在但大小不对 → 删掉重下
    if dest.exists():
        if expected_size and dest.stat().st_size != expected_size:
            print(f"  [重下] {filename}: 大小不匹配")
            dest.unlink(missing_ok=True)
        elif dest.stat().st_size < 1024:  # 小于1KB肯定不对
            print(f"  [重下] {filename}: 文件过小")
            dest.unlink(missing_ok=True)
    
    # 获取下载链接
    try:
        dlink = get_download_link(client, fsid)
        time.sleep(REQUEST_DELAY)
    except RuntimeError as e:
        print(f"  [跳过] {filename}: {e}")
        return False
    
    # 下载文件
    try:
        with client.stream(
            "GET", dlink,
            timeout=httpx.Timeout(DOWNLOAD_TIMEOUT, connect=30),
        ) as resp:
            resp.raise_for_status()
            with open(dest, "wb") as f:
                downloaded = 0
                for chunk in resp.iter_bytes(65536):  # 64KB chunks
                    f.write(chunk)
                    downloaded += len(chunk)
    except Exception as e:
        print(f"  [失败] {filename}: {e}")
        if dest.exists():
            dest.unlink(missing_ok=True)
        return False
    
    # 下载后校验大小
    actual_size = dest.stat().st_size
    if expected_size and actual_size != expected_size:
        print(f"  [校验失败] {filename}: 下载{actual_size} 期望{expected_size}")
        dest.unlink(missing_ok=True)
        return False
    
    if actual_size < 1024:
        print(f"  [校验失败] {filename}: 文件过小 {actual_size}B")
        dest.unlink(missing_ok=True)
        return False
    
    return True


# 线程安全的进度管理
_lock = threading.Lock()
_counter = {"ok": 0, "fail": 0, "done": 0}
_downloaded_set: set = set()
_failed_list: list = []


def _worker(video: dict, cookies: dict, meta: dict, total: int):
    """单个下载任务（线程池调用）"""
    fsid = str(video["fsid"])
    name = video.get("name", f"{fsid}.mp4")
    client = make_client(cookies)
    try:
        ok = download_single_video(client, video, DOWNLOAD_DIR, meta)
    finally:
        client.close()
    
    with _lock:
        _counter["done"] += 1
        done = _counter["done"]
        if ok:
            _counter["ok"] += 1
            _downloaded_set.add(fsid)
            print(f"  [✓] {name}")
        else:
            _counter["fail"] += 1
            _failed_list.append({"fsid": fsid, "name": name})
        
        if done % 5 == 0 or done == total:
            print(f"[视频] 进度: {done}/{total} "
                  f"(成功={_counter['ok']} 失败={_counter['fail']})")
    
    return ok


def main():
    print("=" * 50)
    print("  视频批量下载 (VIP原画质)")
    print("=" * 50)
    
    cookies = load_cookies()
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    # 加载失败列表
    videos = load_failed_videos()
    if not videos:
        print("[视频] 没有待下载的视频")
        return
    
    # 加载元数据
    meta = load_photo_meta()
    print(f"[视频] 加载元数据: {len(meta)} 条")
    
    total = len(videos)
    print(f"[视频] 待下载: {total} 个视频")
    print(f"[视频] 并发线程数: {CONCURRENT_DOWNLOADS}")
    
    _counter["ok"] = 0
    _counter["fail"] = 0
    _counter["done"] = 0
    _downloaded_set.clear()
    _failed_list.clear()
    
    # 并发下载
    with ThreadPoolExecutor(max_workers=CONCURRENT_DOWNLOADS) as pool:
        futures = [pool.submit(_worker, v, cookies, meta, total)
                   for v in videos]
        for f in as_completed(futures):
            try:
                f.result()
            except Exception as e:
                print(f"  [异常] {e}")
    
    ok = _counter["ok"]
    fail = _counter["fail"]
    print(f"\n[视频] 完成! 成功={ok} 失败={fail} 总计={total}")
    print(f"[视频] 保存目录: {DOWNLOAD_DIR}")
    
    # 保存新的失败列表
    if _failed_list:
        fail_file = DOWNLOAD_DIR / "_failed_videos.json"
        fail_file.write_text(json.dumps(
            _failed_list, ensure_ascii=False, indent=2),
            encoding="utf-8")
        print(f"\n  失败列表已保存: {fail_file}")
        for item in _failed_list[:10]:
            print(f"    - {item['name']}")
        if len(_failed_list) > 10:
            print(f"    ... 共 {len(_failed_list)} 条")


if __name__ == "__main__":
    main()
