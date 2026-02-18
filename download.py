# File: tools/yike-album/download.py
"""一刻相册批量下载 - 基于实际验证的 API"""
import json
import time
import sys
import threading
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx

from config import (
    DOWNLOAD_DIR, PROBE_RESULT_FILE, PROGRESS_FILE,
    API_BASE, LIST_API, DOWNLOAD_API,
    LIST_PAGE_SIZE, DOWNLOAD_TIMEOUT, REQUEST_DELAY,
    CONCURRENT_DOWNLOADS,
)


def load_cookies() -> dict:
    """加载 probe 保存的 Cookie"""
    if not PROBE_RESULT_FILE.exists():
        print("[下载] 未找到 Cookie，请先运行: python probe.py")
        sys.exit(1)
    data = json.loads(PROBE_RESULT_FILE.read_text(encoding="utf-8"))
    cookies = {}
    for c in data.get("cookies", []):
        cookies[c["name"]] = c["value"]
    if not cookies:
        print("[下载] Cookie 为空，请重新运行 probe.py")
        sys.exit(1)
    return cookies


def load_progress() -> set:
    if not PROGRESS_FILE.exists():
        return set()
    data = json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
    return set(data.get("downloaded", []))


def save_progress(downloaded: set):
    PROGRESS_FILE.write_text(
        json.dumps({"downloaded": sorted(downloaded)}, ensure_ascii=False),
        encoding="utf-8",
    )


def fetch_all_photos(client: httpx.Client) -> list:
    """分页拉取全部照片元数据"""
    all_photos = []
    cursor = None
    page_num = 0
    while True:
        params = {
            "clienttype": "70",
            "need_thumbnail": "0",
            "need_filter_hidden": "0",
            "num": str(LIST_PAGE_SIZE),
        }
        if cursor:
            params["cursor"] = cursor
        resp = client.get(API_BASE + LIST_API, params=params, timeout=30)
        data = resp.json()
        if data.get("errno") != 0:
            print(f"[下载] 列表API错误: errno={data.get('errno')}")
            break
        items = data.get("list", [])
        all_photos.extend(items)
        page_num += 1
        print(f"[下载] 第{page_num}页: 获取{len(items)}张, 累计{len(all_photos)}张")
        if not data.get("has_more"):
            break
        cursor = data.get("cursor")
        if not cursor:
            break
        time.sleep(REQUEST_DELAY)
    return all_photos


def get_download_link(client: httpx.Client, fsid: str) -> str:
    """获取单张照片的下载直链（有效期约8小时）"""
    params = {"clienttype": "70", "fsid": fsid}
    resp = client.get(
        API_BASE + DOWNLOAD_API, params=params, timeout=30
    )
    data = resp.json()
    if data.get("errno") != 0:
        raise RuntimeError(f"下载链接获取失败: errno={data.get('errno')}")
    dlink = data.get("dlink", "")
    if not dlink:
        raise RuntimeError(f"dlink 为空, fsid={fsid}")
    return dlink


def make_filename(photo: dict) -> str:
    """根据拍摄时间生成文件名，避免重名"""
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


def download_single_photo(
    client: httpx.Client, photo: dict, download_dir: Path
) -> bool:
    """下载单张照片，成功返回 True。用文件大小校验完整性"""
    fsid = str(photo["fsid"])
    filename = make_filename(photo)
    expected_size = photo.get("size", 0)
    dest = download_dir / filename
    # 已存在且大小匹配 → 跳过
    if dest.exists() and expected_size and dest.stat().st_size == expected_size:
        return True
    # 已存在但大小不对 → 删掉重下
    if dest.exists() and expected_size and dest.stat().st_size != expected_size:
        print(f"  [重下] {filename}: 大小不匹配 {dest.stat().st_size} vs {expected_size}")
        dest.unlink(missing_ok=True)
    try:
        dlink = get_download_link(client, fsid)
        time.sleep(REQUEST_DELAY)
    except RuntimeError as e:
        print(f"  [跳过] {filename}: {e}")
        return False
    try:
        with client.stream(
            "GET", dlink, timeout=DOWNLOAD_TIMEOUT,
            headers={"User-Agent": "pan.baidu.com"},
        ) as resp:
            resp.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in resp.iter_bytes(8192):
                    f.write(chunk)
    except Exception as e:
        print(f"  [失败] {filename}: {e}")
        if dest.exists():
            dest.unlink(missing_ok=True)
        return False
    # 下载后校验大小
    if expected_size and dest.stat().st_size != expected_size:
        print(f"  [校验失败] {filename}: 下载{dest.stat().st_size} 期望{expected_size}")
        dest.unlink(missing_ok=True)
        return False
    return True


def dedup_photos(photos: list) -> list:
    """按 fsid 去重，保留第一次出现的"""
    seen = set()
    unique = []
    for p in photos:
        fsid = str(p["fsid"])
        if fsid in seen:
            continue
        seen.add(fsid)
        unique.append(p)
    dup_count = len(photos) - len(unique)
    if dup_count:
        print(f"[下载] 去重: 移除 {dup_count} 条重复记录")
    return unique


def make_client(cookies: dict) -> httpx.Client:
    """创建一个 httpx Client（每线程一个，httpx 非线程安全）"""
    return httpx.Client(
        cookies=cookies,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
            ),
            "Referer": "https://photo.baidu.com/",
        },
        follow_redirects=True, timeout=30,
    )


# 线程安全的进度管理
_lock = threading.Lock()
_counter = {"ok": 0, "fail": 0, "done": 0}
_downloaded_set: set = set()
_failed_list: list = []


def _worker(photo: dict, cookies: dict, total: int):
    """单个下载任务（线程池调用）"""
    fsid = str(photo["fsid"])
    name = make_filename(photo)
    client = make_client(cookies)
    try:
        ok = download_single_photo(client, photo, DOWNLOAD_DIR)
    finally:
        client.close()
    with _lock:
        _counter["done"] += 1
        done = _counter["done"]
        if ok:
            _counter["ok"] += 1
            _downloaded_set.add(fsid)
        else:
            _counter["fail"] += 1
            _failed_list.append({"fsid": fsid, "name": name})
        if done % 20 == 0 or done == total:
            save_progress(_downloaded_set)
            print(f"[下载] 进度: {done}/{total} "
                  f"(成功={_counter['ok']} 失败={_counter['fail']})")
    return ok


def main():
    print("=" * 50)
    print("  一刻相册批量下载 (并发模式)")
    print("=" * 50)
    cookies = load_cookies()
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": "https://photo.baidu.com/",
    }
    client = httpx.Client(
        cookies=cookies, headers=headers,
        follow_redirects=True, timeout=30,
    )
    try:
        print("[下载] 正在获取照片列表...")
        photos = fetch_all_photos(client)
        if not photos:
            print("[下载] 未获取到照片，请检查 Cookie 是否过期")
            return
        print(f"[下载] 共 {len(photos)} 张照片")
        # 去重
        photos = dedup_photos(photos)
        total_api = len(photos)
        # 保存元数据供后续校验
        meta_file = DOWNLOAD_DIR / "_photo_meta.json"
        meta_file.write_text(json.dumps(
            [{"fsid": p["fsid"], "path": p.get("path"), "size": p.get("size")}
             for p in photos], ensure_ascii=False), encoding="utf-8")
        downloaded = load_progress()
        remaining = total_api - len(downloaded)
        print(f"[下载] 已完成 {len(downloaded)} 张，剩余 {remaining} 张")
        print(f"[下载] 并发线程数: {CONCURRENT_DOWNLOADS}")
        _downloaded_set.update(downloaded)
        _counter["ok"] = 0
        _counter["fail"] = 0
        _counter["done"] = 0
        _failed_list.clear()
        todo = [p for p in photos if str(p["fsid"]) not in downloaded]
        total_todo = len(todo)
        print(f"[下载] 待下载: {total_todo} 张")
        with ThreadPoolExecutor(max_workers=CONCURRENT_DOWNLOADS) as pool:
            futures = [pool.submit(_worker, p, cookies, total_todo)
                       for p in todo]
            for f in as_completed(futures):
                try:
                    f.result()
                except Exception as e:
                    print(f"  [异常] {e}")
        save_progress(_downloaded_set)
        ok = _counter["ok"]
        fail = _counter["fail"]
        print(f"\n[下载] 完成! 成功={ok} 失败={fail} 总计={total_api}")
        print(f"[下载] 保存目录: {DOWNLOAD_DIR}")
        # 数量校验
        print(f"\n{'=' * 40}")
        print(f"  数量校验")
        print(f"{'=' * 40}")
        print(f"  API 总数(去重后): {total_api}")
        print(f"  已下载(进度记录): {len(_downloaded_set)}")
        local_files = [f for f in DOWNLOAD_DIR.iterdir()
                       if f.is_file() and not f.name.startswith("_")]
        print(f"  本地文件数:        {len(local_files)}")
        missing = total_api - len(_downloaded_set)
        if missing > 0:
            print(f"  ⚠ 遗漏: {missing} 张未下载")
        else:
            print(f"  ✓ 全部下载完成，无遗漏")
        # 失败列表
        if _failed_list:
            fail_file = DOWNLOAD_DIR / "_failed.json"
            fail_file.write_text(json.dumps(
                _failed_list, ensure_ascii=False, indent=2),
                encoding="utf-8")
            print(f"\n  失败列表已保存: {fail_file}")
            for item in _failed_list[:10]:
                print(f"    - {item['name']}")
            if len(_failed_list) > 10:
                print(f"    ... 共 {len(_failed_list)} 条")
    finally:
        client.close()


if __name__ == "__main__":
    main()
