#!/usr/bin/env python3
"""
验证知乎登录状态并保存会话
"""
import sys
import time
import json
from pathlib import Path
from DrissionPage import ChromiumPage, ChromiumOptions

SESSIONS_DIR = Path.home() / ".clawdbot" / "browser-sessions"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

def check_login_and_save():
    """检查登录状态并保存会话"""
    options = ChromiumOptions()
    options.headless()
    options.set_argument('--disable-blink-features=AutomationControlled')
    options.set_argument('--disable-dev-shm-usage')
    options.set_argument('--no-sandbox')
    options.set_argument('--disable-gpu')
    options.set_user_agent(
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    )
    
    page = ChromiumPage(options)
    
    try:
        # 打开知乎首页
        print("正在打开知乎首页检查登录状态...")
        page.get("https://www.zhihu.com")
        page.wait.doc_loaded()
        time.sleep(3)
        
        # 检查是否已登录
        current_url = page.url
        current_title = page.title
        
        print(f"当前页面: {current_title}")
        print(f"当前URL: {current_url}")
        
        # 检查是否有用户头像或个人中心链接
        is_logged_in = False
        
        # 方法1: 检查URL是否包含signin
        if 'signin' not in current_url:
            is_logged_in = True
            print("✅ 检测到未在登录页，可能已登录")
        
        # 方法2: 检查是否有用户头像
        try:
            avatar = page.ele('xpath://img[contains(@class, "avatar") or contains(@alt, "头像")]', timeout=3)
            if avatar:
                is_logged_in = True
                print("✅ 检测到用户头像，确认已登录")
        except:
            pass
        
        # 方法3: 检查是否有个人中心/我的按钮
        try:
            profile_link = page.ele('text=我的', timeout=2)
            if profile_link:
                is_logged_in = True
                print("✅ 检测到'我的'按钮，确认已登录")
        except:
            pass
        
        if is_logged_in:
            # 保存会话
            session_path = SESSIONS_DIR / "zhihu.json"
            
            session_data = {
                "cookies": page.cookies.as_dict(),
                "localStorage": {},
                "timestamp": time.time(),
                "url": current_url,
                "title": current_title
            }
            
            try:
                ls = page.run_js("return JSON.stringify(localStorage);")
                session_data["localStorage"] = json.loads(ls) if ls else {}
            except:
                pass
            
            session_path.write_text(json.dumps(session_data, indent=2))
            print(f"\n💾 会话已保存: {session_path}")
            
            # 截图保存
            screenshot_path = Path('/tmp/zhihu_logged_in.png')
            page.get_screenshot(screenshot_path)
            print(f"📸 登录状态截图: {screenshot_path}")
            
            return True
        else:
            print("\n❌ 未检测到登录状态，可能登录未成功或已过期")
            screenshot_path = Path('/tmp/zhihu_not_logged_in.png')
            page.get_screenshot(screenshot_path)
            print(f"📸 当前页面截图: {screenshot_path}")
            return False
            
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        page.quit()

if __name__ == "__main__":
    success = check_login_and_save()
    sys.exit(0 if success else 1)
