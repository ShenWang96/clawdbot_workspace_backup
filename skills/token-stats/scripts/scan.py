#!/usr/bin/env python3
"""
Token Stats Scanner
扫描所有最近有变更的 session 日志，提取模型调用信息
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone

WORKSPACE = Path("/root/.openclaw/workspace")
MEMORY_DIR = WORKSPACE / "memory"
SESSIONS_DIR = Path("/root/.openclaw/agents/main/sessions")
TRACKER_FILE = MEMORY_DIR / "token-scan-tracker.json"
LOG_FILE = MEMORY_DIR / "token-usage.jsonl"


def load_tracker():
    """加载 tracker 文件，获取上次扫描时间和已记录的时间戳"""
    try:
        with open(TRACKER_FILE, 'r') as f:
            data = json.load(f)
            return {
                'lastScanTime': data.get('lastScanTime'),
                'loggedTimestamps': set(data.get('loggedTimestamps', []))
            }
    except (FileNotFoundError, json.JSONDecodeError):
        return {'lastScanTime': None, 'loggedTimestamps': set()}


def save_tracker(tracker_data):
    """保存 tracker 文件"""
    data = {
        'lastScanTime': datetime.now(timezone.utc).isoformat(),
        'loggedTimestamps': list(tracker_data['loggedTimestamps']),
        'lastUpdated': datetime.now(timezone.utc).isoformat()
    }
    TRACKER_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TRACKER_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def get_all_session_files():
    """获取所有 session 文件"""
    session_files = []
    
    # 从 sessions.json 获取会话信息
    sessions_index = SESSIONS_DIR / "sessions.json"
    if sessions_index.exists():
        with open(sessions_index, 'r') as f:
            try:
                sessions = json.load(f)
                for session_key, session_info in sessions.items():
                    session_file = Path(session_info.get('sessionFile', ''))
                    if session_file.exists():
                        session_files.append(session_file)
            except json.JSONDecodeError:
                pass
    
    # 后备：扫描 sessions 目录下的所有 .jsonl 文件
    if not session_files:
        for file in SESSIONS_DIR.glob("*.jsonl"):
            if file.name != "sessions.json" and not file.name.endswith(".deleted"):
                if file.stat().st_size > 0:
                    session_files.append(file)
    
    return session_files


def extract_token_data_from_session(session_file, tracker_data):
    """从 session 文件中提取所有 assistant 消息的 token 数据"""
    entries = []
    last_scan_time = tracker_data.get('lastScanTime')
    logged_timestamps = tracker_data.get('loggedTimestamps', set())
    
    try:
        with open(session_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    
                    # 查找 assistant 消息且包含 usage 信息
                    message = entry.get('message', {})
                    if (entry.get('role') == 'assistant' or message.get('role') == 'assistant'):
                        usage = message.get('usage') or entry.get('usage')
                        timestamp = entry.get('timestamp') or message.get('timestamp')
                        
                        if usage and timestamp:
                            # 检查是否已记录
                            if timestamp in logged_timestamps:
                                continue
                            
                            # 检查是否在上次扫描之后
                            if last_scan_time and timestamp <= last_scan_time:
                                continue
                            
                            # 构建记录
                            record = {
                                'timestamp': timestamp,
                                'date': timestamp.split('T')[0] if 'T' in timestamp else timestamp[:10],
                                'provider': message.get('provider') or entry.get('provider', 'unknown'),
                                'model': message.get('model') or entry.get('model', 'unknown'),
                                'input': usage.get('input', 0),
                                'output': usage.get('output', 0),
                                'cacheRead': usage.get('cacheRead', 0),
                                'cacheWrite': usage.get('cacheWrite', 0),
                                'totalTokens': usage.get('totalTokens', 0),
                                'cost': usage.get('cost', {})
                            }
                            entries.append(record)
                            
                except json.JSONDecodeError:
                    continue
                    
    except Exception as e:
        print(f"[scan] Error reading {session_file}: {e}", file=sys.stderr)
    
    return entries


def scan_all_sessions():
    """扫描所有 session 文件，提取新的 token 数据"""
    print("[token-stats] Starting scan...")
    
    # 获取所有 session 文件
    session_files = get_all_session_files()
    valid_files = [f for f in session_files if f.is_file() and f.stat().st_size > 0]
    print(f"[token-stats] Found {len(valid_files)} valid session files")
    
    if not valid_files:
        print("[token-stats] No session files found")
        return 0
    
    # 加载 tracker
    tracker_data = load_tracker()
    
    newly_logged = []
    
    # 扫描每个 session 文件
    for session_file in valid_files:
        entries = extract_token_data_from_session(session_file, tracker_data)
        if entries:
            print(f"[token-stats] {session_file.name}: found {len(entries)} new entries")
            newly_logged.extend(entries)
            for entry in entries:
                tracker_data['loggedTimestamps'].add(entry['timestamp'])
        else:
            print(f"[token-stats] {session_file.name}: no new entries")
    
    # 写入日志文件
    if newly_logged:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            for entry in newly_logged:
                f.write(json.dumps(entry) + '\n')
    
    # 保存 tracker
    save_tracker(tracker_data)
    
    print(f"[token-stats] Scan completed: {len(newly_logged)} new entries, {len(tracker_data['loggedTimestamps'])} total")
    
    return len(newly_logged)


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='Token Stats Scanner')
    parser.add_argument('--silent', '-s', action='store_true',
                        help='静默模式，不输出任何信息')
    args = parser.parse_args()
    
    # 如果是静默模式，重定向 stdout
    if args.silent:
        sys.stdout = open('/dev/null', 'w')
    
    result = scan_all_sessions()
    return 0 if result >= 0 else 1


if __name__ == '__main__':
    sys.exit(main())
