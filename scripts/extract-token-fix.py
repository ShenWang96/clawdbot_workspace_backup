#!/usr/bin/env python3
"""
修复版 Token 收集器
支持多 session 跟踪和完整历史数据提取
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Set, Optional

class TokenExtractor:
    def __init__(self):
        self.workspace = Path("/root/.openclaw/workspace")
        self.sessions_dir = Path("/root/.openclaw/agents/main/sessions")
        self.memory_dir = self.workspace / "memory"
        self.tracker_file = self.memory_dir / "token-logger-tracker.json"
        self.token_log = self.memory_dir / "token-usage.jsonl"
        
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
    def load_tracker(self) -> Set[str]:
        """加载已记录的时间戳"""
        try:
            with open(self.tracker_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return set(data.get('loggedTimestamps', []))
        except (FileNotFoundError, json.JSONDecodeError):
            return set()
    
    def save_tracker(self, logged_timestamps: Set[str]):
        """保存已记录的时间戳"""
        data = {
            'loggedTimestamps': list(logged_timestamps),
            'lastUpdated': datetime.now(timezone.utc).isoformat(),
            'totalEntries': len(logged_timestamps)
        }
        with open(self.tracker_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load_sessions_config(self) -> Dict:
        """加载 sessions 配置"""
        sessions_index = self.sessions_dir / "sessions.json"
        if not sessions_index.exists():
            return {}
        
        with open(sessions_index, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def extract_token_data_from_session(self, session_file: Path) -> List[Dict]:
        """从 session 文件提取所有未记录的 token 数据"""
        if not session_file.exists():
            return []
        
        token_data_list = []
        logged_timestamps = self.load_tracker()
        
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        entry = json.loads(line)
                        if self._is_valid_token_entry(entry):
                            token_data = self._extract_token_info(entry)
                            if token_data['timestamp'] not in logged_timestamps:
                                token_data_list.append(token_data)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"[ERROR] 读取文件 {session_file} 时出错: {e}")
        
        return token_data_list
    
    def _is_valid_token_entry(self, entry) -> bool:
        """检查是否为有效的 token 条目"""
        if entry.get('type') != 'message':
            return False
        
        message = entry.get('message', {})
        if message.get('role') != 'assistant':
            return False
        
        usage = message.get('usage', {})
        if not usage:
            return False
        
        total_tokens = usage.get('totalTokens', 0)
        if total_tokens <= 0:
            return False
        
        return True
    
    def _extract_token_info(self, entry) -> Dict:
        """提取 token 信息"""
        message = entry['message']
        usage = message['usage']
        
        return {
            'timestamp': entry.get('timestamp'),
            'date': entry.get('timestamp', '').split('T')[0],
            'provider': message.get('provider', 'unknown'),
            'model': message.get('model', 'unknown'),
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
    
    def append_to_log(self, token_data_list: List[Dict]) -> int:
        """将 token 数据追加到日志文件"""
        if not token_data_list:
            return 0
        
        new_count = 0
        try:
            with open(self.token_log, 'a', encoding='utf-8') as f:
                for token_data in token_data_list:
                    f.write(json.dumps(token_data) + '\n')
                    new_count += 1
        except Exception as e:
            print(f"[ERROR] 写入 token 日志时出错: {e}")
            return 0
        
        return new_count
    
    def extract_all_sessions(self) -> Dict:
        """提取所有 session 的 token 数据"""
        print("[TOKEN-EXTRACT] 开始提取所有 sessions 的 token 数据...")
        
        sessions_config = self.load_sessions_config()
        if not sessions_config:
            print("[TOKEN-EXTRACT] ❌ 未找到 sessions 配置")
            return {"success": False, "message": "sessions config not found"}
        
        total_new_entries = 0
        sessions_processed = 0
        session_details = []
        
        # 处理所有 session
        for session_key, session_info in sessions_config.items():
            session_file = session_info.get('sessionFile')
            if not session_file:
                continue
            
            session_file_path = Path(session_file)
            if not session_file_path.exists():
                continue
            
            sessions_processed += 1
            print(f"[TOKEN-EXTRACT] 处理 session: {session_key} -> {session_file_path}")
            
            # 提取 token 数据
            token_data_list = self.extract_token_data_from_session(session_file_path)
            new_entries = len(token_data_list)
            
            if new_entries > 0:
                # 追加到日志
                added = self.append_to_log(token_data_list)
                total_new_entries += added
                
                session_details.append({
                    'session_key': session_key,
                    'session_file': str(session_file_path),
                    'new_entries': added,
                    'file_size': session_file_path.stat().st_size if session_file_path.exists() else 0
                })
                
                print(f"[TOKEN-EXTRACT] ✅ {session_key}: 新增 {added} 条记录")
            else:
                print(f"[TOKEN-EXTRACT] ⏭️ {session_key}: 无新数据")
        
        # 更新 tracker
        all_logged = self.load_tracker()
        for session_detail in session_details:
            for token_data in self.extract_token_data_from_session(Path(session_detail['session_file'])):
                all_logged.add(token_data['timestamp'])
        
        self.save_tracker(all_logged)
        
        result = {
            "success": True,
            "message": "Extraction completed",
            "sessions_processed": sessions_processed,
            "total_new_entries": total_new_entries,
            "session_details": session_details,
            "tracker_updated": len(all_logged)
        }
        
        print(f"[TOKEN-EXTRACT] 📊 处理了 {sessions_processed} 个 sessions")
        print(f"[TOKEN-EXTRACT] 📈 新增 {total_new_entries} 条 token 记录")
        print(f"[TOKEN-EXTRACT] 📝 Tracker 现在有 {len(all_logged)} 条记录")
        
        return result
    
    def run_extraction(self) -> int:
        """运行提取任务，返回状态码"""
        try:
            result = self.extract_all_sessions()
            return 0 if result.get("success", False) else 1
        except Exception as e:
            print(f"[TOKEN-EXTRACT] ❌ 提取过程出错: {e}")
            return 1

def main():
    extractor = TokenExtractor()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "extract":
            sys.exit(extractor.run_extraction())
        elif command == "status":
            print(f"Sessions dir: {extractor.sessions_dir}")
            print(f"Token log: {extractor.token_log}")
            print(f"Tracker file: {extractor.tracker_file}")
            
            if extractor.token_log.exists():
                with open(extractor.token_log, 'r', encoding='utf-8') as f:
                    total_entries = sum(1 for _ in f)
                print(f"Total logged entries: {total_entries}")
            else:
                print("Total logged entries: 0")
            
            if extractor.tracker_file.exists():
                with open(extractor.tracker_file, 'r', encoding='utf-8') as f:
                    tracker_data = json.load(f)
                print(f"Tracker entries: {tracker_data.get('totalEntries', 0)}")
            else:
                print("Tracker entries: 0")
        else:
            print(f"Usage: {sys.argv[0]} {{extract|status}}")
            sys.exit(1)
    else:
        # 默认执行提取
        sys.exit(extractor.run_extraction())

if __name__ == "__main__":
    main()