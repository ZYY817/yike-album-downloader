# File: tools/yike-album/retry_failed.py
"""重新下载大小不符的文件"""
import json
import time
from pathlib import Path

import httpx

from config import DOWNLOAD_DIR, PROBE_RESULT_FILE, API_BASE, DOWNLOAD_API

def load_cookies():
    data = json.loads(PROBE_RESULT_FILE.read_text(encoding="utf-8"))
    cookies = {}
    for c in data.get("cookies", []):
        cookies[c["name"]] = c["value"]
    return cookies

def get_download_link(client, fsid):
    params = {"clienttype": "70", "fsid": fsid}
    resp = client.get(API_BASE + DOWNLOAD_API, params=params, timeout=30)
    data = resp.json()
    if data.get("errno") != 0:
        raise RuntimeError(f"获取链接失败: errno={data.get('errno')}")
    return data.get("dlink", "")

def download_file(client, fsid, name, expected_size):
    print(f"\n下载: {name}")
    print(f"  期望大小: {expected_size:,} bytes ({expected_size/1024/1024:.1f}MB)")
    
    dest = DOWNLOAD_DIR / name
    if dest.exists():
        dest.unlink()
    
    dlink = get_download_link(client, fsid)
    time.sleep(0.2)
    
    with client.stream("GET", dlink, timeout=httpx.Timeout(600, connect=30)) as resp:
        resp.raise_for_status()
        with open(dest, "wb") as f:
            downloaded = 0
            for chunk in resp.iter_bytes(65536):
                f.write(chunk)
                downloaded += len(chunk)
                if downloaded % (100 * 1024 * 1024) == 0:
                    print(f"  已下载: {downloaded:,} bytes ({downloaded/1024/1024:.1f}MB)")
    
    actual_size = dest.stat().st_size
    print(f"  实际大小: {actual_size:,} bytes ({actual_size/1024/1024:.1f}MB)")
    
    if actual_size == expected_size:
        print(f"  ✓ 下载成功")
        return True
    else:
        print(f"  ✗ 大小不符")
        return False

def main():
    mismatch_file = DOWNLOAD_DIR / "_size_mismatch.json"
    if not mismatch_file.exists():
        print("没有大小不符的文件")
        return
    
    files = json.loads(mismatch_file.read_text(encoding="utf-8"))
    print(f"需要重新下载: {len(files)}个文件\n")
    
    cookies = load_cookies()
    client = httpx.Client(
        cookies=cookies,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://photo.baidu.com/",
        },
        follow_redirects=True,
    )
    
    try:
        success = 0
        for f in files:
            try:
                if download_file(client, f["fsid"], f["name"], f["expected"]):
                    success += 1
            except Exception as e:
                print(f"  ✗ 错误: {e}")
        
        print(f"\n完成: 成功{success}/{len(files)}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
