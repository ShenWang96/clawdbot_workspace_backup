#!/bin/bash
"""
Enhanced Read File Command Wrapper for OpenClaw
作为Telegram命令 /read_file 的入口点
"""

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/enhanced_read_file.py"

# 检查Python脚本是否存在
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "错误: Python脚本不存在 - $PYTHON_SCRIPT"
    exit 1
fi

# 运行Python脚本
python3 "$PYTHON_SCRIPT" "$@"