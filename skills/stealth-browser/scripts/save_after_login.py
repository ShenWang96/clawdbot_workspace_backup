#!/usr/bin/env python3
"""
知乎登录 - 扫码后手动刷新保存会话
"""
import json
import time
from pathlib import Path
from DrissionPage import ChromiumPage, ChromiumOptions

SESSIONS_DIR = Path.home() / ".clawdbot" / "browser-sessions"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

def save_after_login():
    """登录后保存会话"""
    options = ChromiumOptions()
    options.headless()
    options.set_argument('--disable-blink-features=AutomationControlled')
    options.set_argument('--disable-dev-shm-usage')
    options.set_argument('--no-sandbox')
    options.set_argument('--disable-gpu')
    
    page = ChromiumPage(options)
    
    try:
        # 打开知乎首页（已登录状态）
        print("正在访问知乎...")
        page.get("https://www.zhihu.com")
        page.wait.doc_loaded()
        time.sleep(2)
        
        # 刷新页面获取最新状态
        print("刷新页面获取登录状态...")
        page.refresh()
        time.sleep(3)
        
        print(f"当前URL: {page.url}")
        print(f"当前标题: {page.title}")
        
        # 获取 cookies
        cookies = page.cookies()
        cookies_dict = {c['name']: c['value'] for c in cookies} if isinstance(cookies, list) else dict(cookies)
        print(f"获取到 {len(cookies_dict)} 个 cookies")
        
        # 获取 localStorage
        try:
            ls = page.run_js("return JSON.stringify(localStorage);")
            local_storage = json.loads(ls) if ls else {}
            print(f"获取到 {len(local_storage)} 个 localStorage 项")
        except Exception as e:
            local_storage = {}
            print(f"获取 localStorage 失败: {e}")
        
        # 保存会话
        session_data = {
            "cookies": cookies_dict,
            "localStorage": local_storage,
            "timestamp": time.time(),
            "url": page.url,
            "title": page.title
        }
        
        session_path = SESSIONS_DIR / "zhihu.json"
        session_path.write_text(json.dumps(session_data, indent=2))
        print(f"\n💾 会话已保存: {session_path}")
        
        # 检查关键 cookie
        key_cookies = ['z_c0', '_xsrf', 'd_c0', 'tgw_l7_route', 'l_cap_id']
        found = [c for c in key_cookies if c in cookies_dict]
        print(f"\n关键 cookies 找到: {found}")
        
        # 截图
        screenshot_path = Path('/tmp/zhihu_final.png')
        page.get_screenshot(screenshot_path)
        print(f"📸 截图已保存: {screenshot_path}")
        
        if 'z_c0' in cookies_dict:
            print("\n✅ 检测到登录凭证 z_c0 - 登录成功!")
            return True
        else:
            print("\n⚠️ 未检测到 z_c0，可能未登录")
            return False
            
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        page.quit()

if __name__ == "__main__":
    save_after_login()
