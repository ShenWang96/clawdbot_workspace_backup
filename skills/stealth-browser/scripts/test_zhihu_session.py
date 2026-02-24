#!/usr/bin/env python3
"""
测试知乎会话是否有效
"""
import json
from pathlib import Path
from DrissionPage import ChromiumPage, ChromiumOptions

def test_session():
    """测试已保存的会话"""
    session_path = Path.home() / ".clawdbot" / "browser-sessions" / "zhihu.json"
    
    if not session_path.exists():
        print("❌ 会话文件不存在")
        return False
    
    session_data = json.loads(session_path.read_text())
    
    options = ChromiumOptions()
    options.headless()
    options.set_argument('--disable-blink-features=AutomationControlled')
    options.set_argument('--disable-dev-shm-usage')
    options.set_argument('--no-sandbox')
    
    page = ChromiumPage(options)
    
    try:
        # 先访问知乎域名
        page.get("https://www.zhihu.com")
        
        # 加载保存的 cookies
        for name, value in session_data.get("cookies", {}).items():
            try:
                page.cookies.set(name, value)
            except:
                pass
        
        # 加载 localStorage
        for k, v in session_data.get("localStorage", {}).items():
            try:
                page.run_js(f"localStorage.setItem('{k}', '{v}');")
            except:
                pass
        
        # 刷新页面
        page.refresh()
        import time
        time.sleep(3)
        
        print(f"当前URL: {page.url}")
        print(f"当前标题: {page.title}")
        
        # 检查是否已登录
        if 'signin' not in page.url:
            print("✅ 会话有效！已登录知乎")
            return True
        else:
            print("⚠️ 会话可能无效，仍在登录页")
            return False
            
    except Exception as e:
        print(f"错误: {e}")
        return False
    finally:
        page.quit()

if __name__ == "__main__":
    test_session()
