# File: tools/yike-album/probe.py
"""探测脚本：Playwright 打开 Chrome 登录，抓取 Cookie 保存"""
import json
import sys
import time
from playwright.sync_api import sync_playwright
from config import find_chrome, YIKE_HOME, PROBE_RESULT_FILE


def wait_for_login(page) -> bool:
    """等待用户扫码登录，最多5分钟"""
    print("[probe] 请在浏览器中扫码登录...")
    for i in range(300):
        time.sleep(1)
        try:
            url = page.url
            if "home" in url and "login" not in url:
                cookies = page.context.cookies()
                if any("BDUSS" in c.get("name", "") for c in cookies):
                    print(f"[probe] 登录成功! ({i+1}秒)")
                    return True
        except Exception:
            pass
        if i > 0 and i % 30 == 0:
            print(f"[probe] 等待中... ({i}秒)")
    print("[probe] 登录超时")
    return False


def verify_api(page) -> int:
    """登录后调一次 list API 验证能用，返回照片总数估算"""
    result = page.evaluate("""async () => {
        const r = await fetch('/youai/file/v1/list?clienttype=70&need_thumbnail=0&num=1');
        return await r.json();
    }""")
    if result.get("errno") != 0:
        print(f"[probe] API 验证失败: errno={result.get('errno')}")
        return 0
    has_more = result.get("has_more", 0)
    count = len(result.get("list", []))
    print(f"[probe] API 验证成功, has_more={has_more}")
    return count


def save_cookies(page):
    """保存 Cookie 到文件"""
    cookies = page.context.cookies()
    data = {"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "cookies": cookies}
    PROBE_RESULT_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[probe] Cookie 已保存到: {PROBE_RESULT_FILE}")


def main():
    print("=" * 50)
    print("  一刻相册 Cookie 提取工具")
    print("  浏览器会打开，请扫码登录")
    print("=" * 50)
    chrome = find_chrome()
    print(f"[probe] Chrome: {chrome}")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            executable_path=chrome, headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        ctx = browser.new_context(viewport={"width": 1280, "height": 800})
        page = ctx.new_page()
        page.goto(YIKE_HOME, wait_until="domcontentloaded")
        if not wait_for_login(page):
            browser.close()
            sys.exit(1)
        verify_api(page)
        save_cookies(page)
        print("[probe] 完成! 可以关闭浏览器了")
        try:
            page.wait_for_event("close", timeout=300000)
        except Exception:
            pass
        browser.close()


if __name__ == "__main__":
    main()
