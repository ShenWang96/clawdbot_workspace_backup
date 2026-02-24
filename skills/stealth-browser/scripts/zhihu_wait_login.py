#!/usr/bin/env python3
"""
知乎登录监听脚本 - 持续等待用户登录
"""
import sys
import time
import json
from pathlib import Path
from DrissionPage import ChromiumPage, ChromiumOptions

SESSIONS_DIR = Path.home() / ".clawdbot" / "browser-sessions"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

def wait_for_login():
    """等待用户登录并保存会话"""
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
        # 打开知乎登录页
        print("正在打开知乎登录页...")
        page.get("https://www.zhihu.com/signin")
        page.wait.doc_loaded()
        time.sleep(3)
        
        print("\n" + "="*50)
        print("等待登录...")
        print("请在手机上扫描二维码并确认登录")
        print("="*50)
        
        # 持续检查登录状态，最多等待5分钟
        initial_url = page.url
        for i in range(60):  # 5分钟 = 60 * 5秒
            time.sleep(5)
            
            # 刷新页面以获取最新状态
            page.refresh()
            time.sleep(2)
            
            current_url = page.url
            current_title = page.title
            
            print(f"检查中... [{i+1}/60] URL: {current_url[:50]}...")
            
            # 如果URL改变且不在登录页，说明登录成功
            if 'signin' not in current_url:
                print(f"\n✅ 登录成功!")
                print(f"当前页面: {current_title}")
                print(f"当前URL: {current_url}")
                
                # 保存会话
                save_session(page, "zhihu")
                
                # 截图保存
                screenshot_path = Path('/tmp/zhihu_login_success.png')
                page.get_screenshot(screenshot_path)
                print(f"📸 截图已保存: {screenshot_path}")
                
                return True
        
        print("\n⚠️ 登录超时（5分钟），请重试")
        return False
            
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        page.quit()

def save_session(page, session_name):
    """保存会话"""
    session_path = SESSIONS_DIR / f"{session_name}.json"
    
    session_data = {
        "cookies": page.cookies.as_dict(),
        "localStorage": {},
        "timestamp": time.time()
    }
    
    try:
        ls = page.run_js("return JSON.stringify(localStorage);")
        session_data["localStorage"] = json.loads(ls) if ls else {}
    except:
        pass
    
    session_path.write_text(json.dumps(session_data, indent=2))
    print(f"\n💾 会话已保存: {session_path}")
    
    # 同时创建测试文件
    test_path = SESSIONS_DIR / "zhihu_test.txt"
    test_path.write_text(f"Session saved at: {time.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    success = wait_for_login()
    sys.exit(0 if success else 1)
