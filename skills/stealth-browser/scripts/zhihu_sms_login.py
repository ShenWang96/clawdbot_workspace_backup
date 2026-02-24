#!/usr/bin/env python3
"""
知乎短信验证码登录
"""
import json
import time
from pathlib import Path
from DrissionPage import ChromiumPage, ChromiumOptions

SESSIONS_DIR = Path.home() / ".clawdbot" / "browser-sessions"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

def zhihu_sms_login(phone_number):
    """使用短信验证码登录知乎"""
    options = ChromiumOptions()
    options.headless()
    options.set_argument('--disable-blink-features=AutomationControlled')
    options.set_argument('--disable-dev-shm-usage')
    options.set_argument('--no-sandbox')
    options.set_argument('--disable-gpu')
    options.set_argument('--lang=zh-CN')
    options.set_user_agent(
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    )
    
    page = ChromiumPage(options)
    
    try:
        # 访问登录页
        print("正在打开知乎登录页...")
        page.get("https://www.zhihu.com/signin")
        page.wait.doc_loaded()
        time.sleep(3)
        
        # 切换到短信验证码登录
        print("切换到短信验证码登录...")
        try:
            # 查找短信验证码登录选项
            sms_tab = page.ele('text=验证码登录', timeout=5)
            if sms_tab:
                sms_tab.click()
                time.sleep(2)
                print("✅ 已切换到验证码登录")
        except Exception as e:
            print(f"切换登录方式失败: {e}")
        
        # 输入手机号
        print(f"正在输入手机号: {phone_number}")
        try:
            phone_input = page.ele('xpath://input[@placeholder="手机号" or @name="phone" or @type="tel"]', timeout=5)
            if phone_input:
                phone_input.clear()
                phone_input.input(phone_number)
                print("✅ 手机号已输入")
                time.sleep(1)
        except Exception as e:
            print(f"输入手机号失败: {e}")
            return False
        
        # 截图显示当前状态
        screenshot_path = Path('/tmp/zhihu_sms_step1.png')
        page.get_screenshot(screenshot_path)
        print(f"📸 截图已保存: {screenshot_path}")
        
        print("\n" + "="*60)
        print("步骤完成！")
        print("请查看截图，然后手动点击'获取短信验证码'")
        print("收到验证码后告诉我，我会帮你输入")
        print("="*60)
        
        # 等待用户输入验证码
        print("\n⏳ 等待验证码... (最多等待2分钟)")
        # 这里我们不自动获取验证码，而是让用户手动点击并告诉我们
        
        return True
            
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 不关闭浏览器，让用户可以看到页面
        pass

def input_verification_code(page, code):
    """输入验证码并登录"""
    try:
        print(f"正在输入验证码: {code}")
        code_input = page.ele('xpath://input[@placeholder="输入 6 位短信验证码" or contains(@placeholder, "验证码")]', timeout=5)
        if code_input:
            code_input.clear()
            code_input.input(code)
            print("✅ 验证码已输入")
            time.sleep(1)
        
        # 点击登录按钮
        print("点击登录按钮...")
        login_btn = page.ele('xpath://button[contains(text(), "登录") or contains(text(), "注册")]', timeout=5)
        if login_btn:
            login_btn.click()
            print("✅ 已点击登录")
            time.sleep(5)
        
        # 检查登录结果
        print(f"当前URL: {page.url}")
        if 'signin' not in page.url:
            print("✅ 登录成功!")
            
            # 保存会话
            cookies = page.cookies()
            cookies_dict = {c['name']: c['value'] for c in cookies} if isinstance(cookies, list) else dict(cookies)
            
            try:
                ls = page.run_js("return JSON.stringify(localStorage);")
                local_storage = json.loads(ls) if ls else {}
            except:
                local_storage = {}
            
            session_data = {
                "cookies": cookies_dict,
                "localStorage": local_storage,
                "timestamp": time.time(),
                "url": page.url,
                "title": page.title
            }
            
            session_path = SESSIONS_DIR / "zhihu.json"
            session_path.write_text(json.dumps(session_data, indent=2))
            print(f"💾 会话已保存: {session_path}")
            
            # 截图
            page.get_screenshot('/tmp/zhihu_login_success.png')
            print("📸 登录成功截图已保存")
            
            return True
        else:
            print("❌ 登录失败，仍在登录页")
            return False
            
    except Exception as e:
        print(f"输入验证码时出错: {e}")
        return False

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        phone = sys.argv[1]
        zhihu_sms_login(phone)
    else:
        print("用法: python3 zhihu_sms_login.py <手机号>")
