#!/usr/bin/env python3
"""
Token Stats Extractor - Python version for reliability
Extracts token usage from session files and appends to token-usage.jsonl
"""

import json
import sys
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
MEMORY_DIR = WORKSPACE / "memory"
SESSIONS_DIR = Path("/root/.openclaw/agents/main/sessions")
TRACKER_FILE = MEMORY_DIR / "token-logger-tracker.json"
LOG_FILE = MEMORY_DIR / "token-usage.jsonl"

MEMORY_DIR.mkdir(parents=True, exist_ok=True)


def load_tracker():
    """Load tracker file with logged timestamps"""
    try:
        with open(TRACKER_FILE, 'r') as f:
            data = json.load(f)
            return set(data.get('loggedTimestamps', []))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def save_tracker(logged_timestamps):
    """Save tracker file with logged timestamps"""
    data = {
        'loggedTimestamps': list(logged_timestamps),
        'lastUpdated': Path('/root/.openclaw/workspace/memory/token-logger-tracker.json').exists() and '2026-02-01' or '2026-02-01T07:15:43.953Z'
    }
    with open(TRACKER_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def find_session_file():
    """Find the current session file"""
    sessions_index = SESSIONS_DIR / "sessions.json"
    
    if not sessions_index.exists():
        print("[token-stats-cron] Sessions index not found")
        return None
    
    with open(sessions_index, 'r') as f:
        sessions = json.load(f)
    
    # Find feishu:default session
    for key, entry in sessions.items():
        if key.startswith("feishu:default:"):
            session_file = entry.get('sessionFile')
            if session_file and Path(session_file).exists():
                return Path(session_file)
    
    print("[token-stats-cron] No feishu session found")
    return None


def extract_last_token_data(session_file):
    """Extract last assistant message with token usage"""
    try:
        # Read last 100 lines
        with open(session_file, 'r') as f:
            lines = f.readlines()[-100:]
        
        # Find last assistant message with token data
        for line in reversed(lines):
            try:
                entry = json.loads(line.strip())
                if entry.get('type') == 'message':
                    msg = entry.get('message', {})
                    if msg.get('role') == 'assistant':
                        usage = msg.get('usage', {})
                        if usage.get('totalTokens', 0) > 0:
                            return {
                                'timestamp': entry.get('timestamp'),
                                'date': entry.get('timestamp', '').split('T')[0],
                                'provider': msg.get('provider', 'unknown'),
                                'model': msg.get('model', 'unknown'),
                                'input': usage.get('input', 0),
                                'output': usage.get('output', 0),
                                'cacheRead': usage.get('cacheRead', 0),
                                'cacheWrite': usage.get('cacheWrite', 0),
                                'totalTokens': usage.get('totalTokens', 0),
                                'cost': {
                                    'input': usage.get('cost', {}).get('input', 0),
                                    'output': usage.get('cost', {}).get('output', 0),
                                    'cacheRead': usage.get('cost', {}).get('cacheRead', 0),
                                    'cacheWrite': usage.get('cost', {}).get('cacheWrite', 0),
                                    'total': usage.get('cost', {}).get('total', 0),
                                }
                            }
            except json.JSONDecodeError:
                continue
        
        return None
    except Exception as e:
        print(f"[token-stats-cron] Error reading session file: {e}")
        return None


def main():
    """Main extraction logic"""
    print("[token-stats-cron] Checking for new token usage...")
    
    # Find session file
    session_file = find_session_file()
    if not session_file:
        return 1
    
    print(f"[token-stats-cron] Session file: {session_file}")
    
    # Extract last token data
    token_data = extract_last_token_data(session_file)
    if not token_data:
        print("[token-stats-cron] No assistant message with token data")
        return 0
    
    timestamp = token_data['timestamp']
    print(f"[token-stats-cron] Last timestamp: {timestamp}")
    
    # Load tracker
    logged_timestamps = load_tracker()
    
    # Check if already logged
    if timestamp in logged_timestamps:
        print(f"[token-stats-cron] Already logged: {timestamp}")
        return 0
    
    # Append to log file
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(token_data) + '\n')
    
    # Update tracker
    logged_timestamps.add(timestamp)
    save_tracker(logged_timestamps)
    
    total = token_data['totalTokens']
    print(f"[token-stats-cron] Logged: {total} tokens")
    print(f"[token-stats-cron] Log file: {LOG_FILE}")
    
    return 0


if __name__ == '__main__':
    command = sys.argv[1] if len(sys.argv) > 1 else 'extract'
    
    if command == 'extract':
        sys.exit(main())
    elif command == 'status':
        print(f"Sessions dir: {SESSIONS_DIR}")
        print(f"Log file: {LOG_FILE}")
        print(f"Tracker file: {TRACKER_FILE}")
        print("")
        if LOG_FILE.exists():
            with open(LOG_FILE, 'r') as f:
                print(f"Total logged entries: {sum(1 for _ in f)}")
        else:
            print("Total logged entries: 0")
    else:
        print(f"Usage: {sys.argv[0]} {{extract|status}}")
        sys.exit(1)
