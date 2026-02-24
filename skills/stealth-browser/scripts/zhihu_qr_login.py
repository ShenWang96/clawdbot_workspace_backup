#!/usr/bin/env python3
"""
知乎二维码登录脚本
"""
import sys
import time
import json
from pathlib import Path
from DrissionPage import ChromiumPage, ChromiumOptions

SESSIONS_DIR = Path.home() / ".clawdbot" / "browser-sessions"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

def get_zhihu_qrcode():
    """获取知乎登录二维码"""
    options = ChromiumOptions()
    options.headless()  # 无头模式
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
        
        # 尝试点击二维码登录选项
        print("查找二维码登录选项...")
        
        # 先检查是否已经是二维码登录页面
        qr_img = page.ele('xpath://img[contains(@class, "qrcode") or contains(@src, "qr") or contains(@alt, "二维码")]', timeout=5)
        
        if not qr_img:
            # 尝试点击切换到二维码登录的按钮
            try:
                # 查找包含"二维码"文字的按钮或链接
                qr_tab = page.ele('text=二维码', timeout=3)
                if qr_tab:
                    print("点击二维码登录选项...")
                    qr_tab.click()
                    time.sleep(2)
            except:
                pass
            
            # 再次查找二维码图片
            qr_img = page.ele('xpath://img[contains(@class, "qrcode") or contains(@src, "qr") or contains(@alt, "二维码")]', timeout=5)
        
        if qr_img:
            # 获取二维码图片的 src
            qr_src = qr_img.attr('src')
            if qr_src:
                print(f"找到二维码图片: {qr_src[:100]}...")
                
                # 保存二维码截图
                qr_path = Path('/tmp/zhihu_qrcode.png')
                qr_img.save(qr_path)
                print(f"二维码已保存: {qr_path}")
                
                # 同时截取整个页面
                screenshot_path = Path('/tmp/zhihu_login_page.png')
                page.get_screenshot(screenshot_path)
                print(f"登录页面截图已保存: {screenshot_path}")
                
                # 等待用户扫描二维码并登录
                print("\n" + "="*50)
                print("请使用手机知乎APP扫描二维码登录")
                print("二维码位置: /tmp/zhihu_qrcode.png")
                print("="*50)
                print("等待登录中... (最多等待120秒)")
                
                # 循环检查登录状态
                initial_url = page.url
                for i in range(24):  # 120秒 = 24 * 5秒
                    time.sleep(5)
                    current_url = page.url
                    current_title = page.title
                    print(f"检查登录状态... [{i+1}/24] URL: {current_url[:60]}")
                    
                    # 如果URL改变且不是登录页，说明登录成功
                    if 'signin' not in current_url and current_url != initial_url:
                        print(f"\n✅ 登录成功!")
                        print(f"当前页面: {current_title}")
                        print(f"当前URL: {current_url}")
                        
                        # 保存会话
                        save_session(page, "zhihu")
                        return True
                
                print("\n⚠️ 登录超时，请重试")
                return False
            else:
                print("无法获取二维码图片地址")
                # 保存页面截图供调试
                page.get_screenshot('/tmp/zhihu_debug.png')
                print("调试截图已保存: /tmp/zhihu_debug.png")
                return False
        else:
            print("未找到二维码元素，保存页面截图...")
            page.get_screenshot('/tmp/zhihu_debug.png')
            print("调试截图已保存: /tmp/zhihu_debug.png")
            
            # 打印页面源代码供调试
            html_path = Path('/tmp/zhihu_page.html')
            html_path.write_text(page.html)
            print(f"页面HTML已保存: {html_path}")
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

if __name__ == "__main__":
    success = get_zhihu_qrcode()
    sys.exit(0 if success else 1)
