#!/bin/bash
"""
Quick test script for the enhanced read file command
"""

# 添加到PATH以便OpenClaw能找到命令
export PATH="$PATH:/root/.openclaw/workspace/read-file/scripts"

# 测试基本功能
echo "=== 测试基本功能 ==="
read_file.sh --list

echo -e "\n=== 测试路径补全 ==="
read_file.sh --complete "reports/"

echo -e "\n=== 测试具体文件读取 ==="
read_file.sh reports/session-logs分析报告.md --limit 10

echo -e "\n=== 测试文件预览 ==="
read_file.sh reports/session-logs分析报告.md --preview