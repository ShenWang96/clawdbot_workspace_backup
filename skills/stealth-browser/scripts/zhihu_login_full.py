#!/usr/bin/env python3
"""
知乎登录 - 创建已登录的会话
使用完整的反检测配置
"""
import json
import time
from pathlib import Path
from DrissionPage import ChromiumPage, ChromiumOptions

SESSIONS_DIR = Path.home() / ".clawdbot" / "browser-sessions"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

def create_logged_in_session():
    """创建已登录的知乎会话"""
    options = ChromiumOptions()
    options.headless()
    
    # 反检测配置
    options.set_argument('--disable-blink-features=AutomationControlled')
    options.set_argument('--disable-dev-shm-usage')
    options.set_argument('--no-sandbox')
    options.set_argument('--disable-gpu')
    options.set_argument('--disable-infobars')
    options.set_argument('--disable-extensions')
    options.set_argument('--lang=zh-CN')
    options.set_argument('--window-size=1920,1080')
    options.set_user_agent(
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    )
    
    page = ChromiumPage(options)
    
    try:
        # 步骤1: 访问登录页
        print("步骤1: 访问知乎登录页...")
        page.get("https://www.zhihu.com/signin")
        page.wait.doc_loaded()
        time.sleep(3)
        
        # 获取初始二维码
        print("步骤2: 获取二维码...")
        try:
            qr_img = page.ele('xpath://img[contains(@class, "qrcode") or contains(@alt, "二维码")]', timeout=5)
            if qr_img:
                qr_path = Path('/tmp/zhihu_qr_new.png')
                qr_img.save(qr_path)
                print(f"✅ 二维码已保存: {qr_path}")
        except:
            print("⚠️ 未找到二维码元素")
        
        # 步骤3: 等待用户扫码并确认
        print("\n" + "="*60)
        print("请现在扫描二维码并确认登录！")
        print("="*60)
        print("等待30秒让你完成扫码...")
        time.sleep(30)
        
        # 步骤4: 刷新页面获取登录状态
        print("\n步骤4: 刷新页面获取登录状态...")
        page.refresh()
        page.wait.doc_loaded()
        time.sleep(5)
        
        print(f"当前URL: {page.url}")
        print(f"当前标题: {page.title}")
        
        # 步骤5: 检查登录状态
        if 'signin' not in page.url:
            print("✅ URL显示已登录!")
        
        # 步骤6: 获取并保存 cookies
        cookies = page.cookies()
        cookies_dict = {c['name']: c['value'] for c in cookies} if isinstance(cookies, list) else dict(cookies)
        
        try:
            ls = page.run_js("return JSON.stringify(localStorage);")
            local_storage = json.loads(ls) if ls else {}
        except:
            local_storage = {}
        
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
        if 'z_c0' in cookies_dict:
            print("✅ 检测到 z_c0 - 登录成功!")
            return True
        elif '_xsrf' in cookies_dict and len(cookies_dict) > 5:
            print("⚠️ 找到部分登录凭证，可能已登录")
            return True
        else:
            print("❌ 未检测到完整登录凭证")
            return False
            
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        page.quit()

if __name__ == "__main__":
    success = create_logged_in_session()
    print("\n" + "="*60)
    if success:
        print("✅ 知乎登录会话保存成功!")
    else:
        print("❌ 登录会话保存失败，请重试")
    print("="*60)
