#!/usr/bin/env python3
"""
OpenClaw Command Integration for read_file
将read_file命令集成到OpenClaw的系统中
"""

import sys
import os
import subprocess

def main():
    """主函数：处理来自OpenClaw的调用"""
    # 获取参数
    args = sys.argv[1:]
    
    if not args:
        # 如果没有参数，显示帮助
        print("可用的文件读取命令：")
        print("  --list: 列出所有可用的文件")
        print("  --complete <路径>: 获取路径补全建议")
        print("  <文件路径>: 读取指定文件的内容")
        return 0
    
    # 获取脚本路径
    script_path = os.path.join(os.path.dirname(__file__), 'enhanced_read_file.py')
    
    # 运行Python脚本
    try:
        result = subprocess.run([sys.executable, script_path] + args, 
                              capture_output=True, text=True, cwd=os.path.dirname(script_path))
        
        # 输出结果
        if result.stdout:
            print(result.stdout)
        
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        return result.returncode
        
    except Exception as e:
        print(f"错误: {str(e)}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())