#!/usr/bin/env python3
"""
Enhanced Read File Script for OpenClaw
安全读取workspace目录下的文件，支持路径验证、自动补全和分段发送
"""

import os
import sys
import argparse
from pathlib import Path
import glob

# 配置常量
WORKSPACE_ROOT = "/root/.openclaw/workspace"
ALLOWED_PATHS = [
    "reports",
    "docs"
]
ALLOWED_EXTENSIONS = [".md"]
TELEGRAM_MAX_LENGTH = 4000

class EnhancedReadFile:
    def __init__(self):
        self.workspace_path = Path(WORKSPACE_ROOT)
        
    def validate_path(self, file_path):
        """验证文件路径安全性"""
        # 转换为绝对路径
        abs_path = self.workspace_path / file_path
        
        # 检查路径是否在workspace内
        if not str(abs_path).startswith(str(self.workspace_path)):
            return False, "错误: 路径不在workspace范围内"
        
        # 检查路径是否在允许的目录内，或者在workspace根目录
        in_allowed_path = False
        for allowed_path in ALLOWED_PATHS:
            if f"{allowed_path}/" in str(abs_path):
                in_allowed_path = True
                break
        
        # 如果不在reports或docs目录，检查是否在workspace根目录且是md文件
        if not in_allowed_path:
            if abs_path.parent == self.workspace_path and abs_path.suffix in ALLOWED_EXTENSIONS:
                in_allowed_path = True
            else:
                return False, f"错误: 只能访问 {', '.join(ALLOWED_PATHS)} 目录下的文件或workspace根目录下的md文件"
        
        # 检查文件是否存在
        if not abs_path.exists():
            return False, f"错误: 文件不存在 - {file_path}"
        
        # 检查文件类型
        if abs_path.suffix not in ALLOWED_EXTENSIONS:
            return False, f"错误: 不支持的文件类型 - 只支持 {', '.join(ALLOWED_EXTENSIONS)} 文件"
        
        return True, str(abs_path)
    
    def list_available_files(self):
        """列出所有可用的文件"""
        available_files = []
        
        for allowed_path in ALLOWED_PATHS:
            path = self.workspace_path / allowed_path
            if path.exists():
                for md_file in path.glob("**/*.md"):
                    # 计算相对路径
                    relative_path = md_file.relative_to(self.workspace_path)
                    available_files.append(str(relative_path))
        
        return sorted(available_files)
    
    def get_completions(self, partial_path):
        """获取路径补全建议"""
        available_files = self.list_available_files()
        completions = []
        
        # 如果是空路径，返回所有文件
        if not partial_path:
            return available_files
        
        # 过滤匹配的文件
        for file_path in available_files:
            if file_path.startswith(partial_path):
                # 如果是目录，添加斜杠
                full_path = self.workspace_path / file_path
                if full_path.is_dir():
                    completions.append(file_path + "/")
                else:
                    completions.append(file_path)
        
        return completions
    
    def read_file_content(self, file_path):
        """读取文件内容"""
        success, abs_path = self.validate_path(file_path)
        if not success:
            return None, abs_path
        
        try:
            with open(abs_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content, None
        except Exception as e:
            return None, f"错误: 读取文件失败 - {str(e)}"
    
    def split_content(self, content, max_length=TELEGRAM_MAX_LENGTH):
        """分割内容为适合Telegram发送的片段"""
        if len(content) <= max_length:
            return [content]
        
        lines = content.split('\n')
        parts = []
        current_part = []
        current_length = 0
        
        for line in lines:
            line_length = len(line) + 1  # +1 for newline
            
            if current_length + line_length > max_length and current_part:
                parts.append('\n'.join(current_part))
                current_part = []
                current_length = 0
            
            current_part.append(line)
            current_length += line_length
        
        if current_part:
            parts.append('\n'.join(current_part))
        
        return parts
    
    def generate_preview(self, content, max_lines=10):
        """生成内容预览"""
        lines = content.split('\n')
        if len(lines) <= max_lines:
            return content
        
        preview_lines = lines[:max_lines]
        return '\n'.join(preview_lines) + f"\n\n... (还有 {len(lines) - max_lines} 行未显示)"
    
    def format_message(self, content, part_num=1, total_parts=1):
        """格式化消息内容"""
        if total_parts > 1:
            header = f"【文件内容 第{part_num}部分/共{total_parts}部分】\n"
            return header + content
        else:
            return content

def main():
    parser = argparse.ArgumentParser(description="Enhanced Read File Command")
    parser.add_argument("path", nargs="?", help="文件路径")
    parser.add_argument("--list", action="store_true", help="列出所有可用文件")
    parser.add_argument("--complete", help="显示路径补全建议")
    parser.add_argument("--limit", type=int, help="限制显示行数")
    parser.add_argument("--preview", action="store_true", help="显示文件预览")
    
    args = parser.parse_args()
    
    reader = EnhancedReadFile()
    
    # 列出可用文件
    if args.list:
        files = reader.list_available_files()
        if files:
            print("可用文件列表：")
            for i, file_path in enumerate(files, 1):
                print(f"{i}. {file_path}")
        else:
            print("没有找到可用的文件")
        return
    
    # 显示补全建议
    if args.complete:
        completions = reader.get_completions(args.complete)
        if completions:
            print("补全建议：")
            for completion in completions:
                print(f"  {completion}")
        return
    
    # 读取文件
    if args.path:
        # 验证路径
        success, validation_result = reader.validate_path(args.path)
        if not success:
            print(validation_result)
            return 1
        
        # 读取内容
        content, error = reader.read_file_content(args.path)
        if error:
            print(error)
            return 1
        
        # 处理限制
        if args.limit and len(content.split('\n')) > args.limit:
            content = '\n'.join(content.split('\n')[:args.limit])
            content += f"\n\n... (已限制为{args.limit}行)"
        
        # 显示预览
        if args.preview:
            preview = reader.generate_preview(content)
            print("文件预览：")
            print(preview)
        else:
            # 分段发送内容
            parts = reader.split_content(content)
            
            for i, part in enumerate(parts, 1):
                formatted = reader.format_message(part, i, len(parts))
                print(formatted)
    
    else:
        print("请提供文件路径，或使用 --list 选项查看可用文件")
        return 1

if __name__ == "__main__":
    sys.exit(main())