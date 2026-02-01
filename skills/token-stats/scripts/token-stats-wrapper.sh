#!/bin/bash
#
# Token Usage Statistics Script
# Wraps Python script for easy access
#

SCRIPT_DIR="/root/.openclaw/workspace/skills/token-monitor/scripts"
PYTHON_SCRIPT="$SCRIPT_DIR/token_stats.py"

# Pass all arguments to Python script
python3 "$PYTHON_SCRIPT" "$@"
