#!/usr/bin/env python3
"""
增强版 Token 收集和诊断工具
用于解决 token_monitor 不工作、token_stats 统计缺失的问题
"""

import os
import json
import glob
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set

class TokenDiagnosticTool:
    def __init__(self):
        self.sessions_dir = Path("/root/.openclaw/agents/main/sessions")
        self.token_usage_file = Path("/root/.openclaw/workspace/memory/token-usage.jsonl")
        self.models_config = Path("/root/.openclaw/openclaw.json")
        
    def diagnose_all_sessions(self) -> Dict:
        """诊断所有 session 文件"""
        print("🔍 开始诊断所有 Session 文件...")
        
        results = {
            "total_sessions": 0,
            "sessions_with_tokens": 0,
            "missing_token_data": [],
            "models_found": set(),
            "providers_found": set(),
            "issues_found": []
        }
        
        session_files = list(self.sessions_dir.glob("*.jsonl"))
        results["total_sessions"] = len(session_files)
        
        for session_file in session_files:
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = []
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                entry = json.loads(line)
                                session_data.append(entry)
                            except json.JSONDecodeError:
                                results["issues_found"].append(f"JSON解析错误: {session_file}")
                                continue
                
                # 检查 token 数据
                has_tokens = self._check_session_tokens(session_data)
                if has_tokens:
                    results["sessions_with_tokens"] += 1
                    
                    # 提取模型信息
                    models, providers = self._extract_model_info(session_data)
                    results["models_found"].update(models)
                    results["providers_found"].update(providers)
                else:
                    results["missing_token_data"].append({
                        "file": str(session_file),
                        "timestamp": self._get_session_timestamp(session_data)
                    })
                    
            except Exception as e:
                results["issues_found"].append(f"文件读取错误 {session_file}: {str(e)}")
        
        return results
    
    def _check_session_tokens(self, session_data: List) -> bool:
        """检查 session 是否包含有效的 token 数据"""
        for entry in session_data:
            if entry.get("type") == "message" and "message" in entry:
                message = entry["message"]
                if message.get("role") == "assistant" and "usage" in message:
                    usage = message["usage"]
                    if any(key in usage for key in ["input", "output", "totalTokens"]):
                        return True
        return False
    
    def _extract_model_info(self, session_data: List) -> tuple:
        """提取模型和提供者信息"""
        models = set()
        providers = set()
        
        for entry in session_data:
            if entry.get("type") == "message" and "message" in entry:
                message = entry["message"]
                provider = message.get("provider")
                model = message.get("model")
                
                if provider:
                    providers.add(provider)
                if model:
                    models.add(model)
        
        return models, providers
    
    def _get_session_timestamp(self, session_data: List) -> Optional[str]:
        """获取 session 时间戳"""
        for entry in session_data:
            if entry.get("type") == "session":
                return entry.get("timestamp")
        return None
    
    def diagnose_token_logger(self) -> Dict:
        """诊断 token-logger 配置"""
        print("🔍 检查 token-logger 配置...")
        
        results = {
            "token_logger_enabled": False,
            "config_status": {},
            "hook_issues": []
        }
        
        try:
            # 读取配置文件
            if self.models_config.exists():
                with open(self.models_config, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                hooks = config.get("hooks", {}).get("internal", {})
                entries = hooks.get("entries", {})
                
                token_logger = entries.get("token-logger", {})
                results["token_logger_enabled"] = token_logger.get("enabled", False)
                results["config_status"]["token_logger"] = token_logger
                
                if not results["token_logger_enabled"]:
                    results["hook_issues"].append("token-logger hook 未启用")
            
        except Exception as e:
            results["hook_issues"].append(f"配置读取错误: {str(e)}")
        
        return results
    
    def diagnose_token_usage_file(self) -> Dict:
        """诊断 token-usage.jsonl 文件"""
        print("🔍 检查 token-usage.jsonl 文件...")
        
        results = {
            "file_exists": False,
            "entries_count": 0,
            "file_size": 0,
            "models_found": set(),
            "date_range": {"start": None, "end": None},
            "issues": []
        }
        
        if self.token_usage_file.exists():
            results["file_exists"] = True
            results["file_size"] = self.token_usage_file.stat().st_size
            
            try:
                with open(self.token_usage_file, 'r', encoding='utf-8') as f:
                    entries = []
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                entry = json.loads(line)
                                entries.append(entry)
                                
                                # 提取模型信息
                                model = entry.get("model")
                                if model:
                                    results["models_found"].add(model)
                                
                                # 提取时间信息
                                timestamp = entry.get("timestamp")
                                if timestamp:
                                    if not results["date_range"]["start"] or timestamp < results["date_range"]["start"]:
                                        results["date_range"]["start"] = timestamp
                                    if not results["date_range"]["end"] or timestamp > results["date_range"]["end"]:
                                        results["date_range"]["end"] = timestamp
                                        
                            except json.JSONDecodeError:
                                results["issues"].append("JSON 解析错误")
                                continue
                
                results["entries_count"] = len(entries)
                
            except Exception as e:
                results["issues"].append(f"文件读取错误: {str(e)}")
        else:
            results["issues"].append("token-usage.jsonl 文件不存在")
        
        return results
    
    def diagnose_models_config(self) -> Dict:
        """诊断模型配置"""
        print("🔍 检查模型配置...")
        
        results = {
            "auth_profiles": {},
            "missing_providers": [],
            "models_configured": set()
        }
        
        try:
            if self.models_config.exists():
                with open(self.models_config, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                auth = config.get("auth", {})
                profiles = auth.get("profiles", {})
                
                results["auth_profiles"] = profiles
                
                for profile_id, profile in profiles.items():
                    provider = profile.get("provider")
                    if provider:
                        results["models_configured"].add(provider)
                
                # 检查常见提供商是否缺失
                expected_providers = ["moonshot", "zai", "openai"]
                for provider in expected_providers:
                    if provider not in results["models_configured"]:
                        results["missing_providers"].append(provider)
                        
        except Exception as e:
            results["error"] = str(e)
        
        return results
    
    def run_comprehensive_diagnosis(self):
        """运行全面诊断"""
        print("🚀 开始全面诊断 Token 收集系统...")
        print("=" * 60)
        
        # 执行所有诊断
        session_results = self.diagnose_all_sessions()
        token_logger_results = self.diagnose_token_logger()
        token_usage_results = self.diagnose_token_usage_file()
        models_results = self.diagnose_models_config()
        
        # 生成报告
        print("\n📊 诊断报告")
        print("=" * 60)
        
        print(f"\n📁 Session 文件诊断:")
        print(f"  • 总会话数: {session_results['total_sessions']}")
        print(f"  • 包含 token 数据的会话: {session_results['sessions_with_tokens']}")
        print(f"  • 缺失 token 数据的会话: {len(session_results['missing_token_data'])}")
        
        print(f"\n🏷️  发现的模型和提供商:")
        print(f"  • 模型: {sorted(session_results['models_found'])}")
        print(f"  • 提供商: {sorted(session_results['providers_found'])}")
        
        print(f"\n⚠️  发现的问题:")
        for issue in session_results['issues_found']:
            print(f"  • {issue}")
        
        print(f"\n🔧 Token-Logger 配置:")
        print(f"  • 是否启用: {'✅' if token_logger_results['token_logger_enabled'] else '❌'}")
        if not token_logger_results['token_logger_enabled']:
            print(f"  • 问题: {token_logger_results['hook_issues']}")
        
        print(f"\n📊 Token-Usage 文件:")
        print(f"  • 文件存在: {'✅' if token_usage_results['file_exists'] else '❌'}")
        if token_usage_results['file_exists']:
            print(f"  • 条目数量: {token_usage_results['entries_count']}")
            print(f"  • 文件大小: {token_usage_results['file_size']} bytes")
            print(f"  • 模型覆盖: {sorted(token_usage_results['models_found'])}")
            print(f"  • 时间范围: {token_usage_results['date_range']}")
        
        print(f"\n🔐 认证配置:")
        print(f"  • 配置的提供商: {sorted(models_results['models_configured'])}")
        if models_results['missing_providers']:
            print(f"  • 缺失的提供商: {models_results['missing_providers']}")
        
        # 生成修复建议
        print("\n🔧 修复建议:")
        print("=" * 60)
        
        if not token_logger_results['token_logger_enabled']:
            print("1️⃣ 修复 token-logger hook:")
            print("   编辑配置文件，启用 token-logger:")
            print("   ```json")
            print("   {")
            print('     "hooks": {')
            print('       "internal": {')
            print('         "enabled": true,')
            print('         "entries": {')
            print('           "token-logger": {')
            print('             "enabled": true')
            print('           }')
            print('         }')
            print('       }')
            print('     }')
            print("   }")
            print("   ```")
        
        if models_results['missing_providers']:
            print(f"\n2️⃣ 添加缺失的提供商配置:")
            for provider in models_results['missing_providers']:
                if provider == "moonshot":
                    print(f"   • {provider} (Kimi): 需要添加 MOONSHOT_API_KEY")
                elif provider == "zai":
                    print(f"   • {provider}: 需要添加 ZAI_API_KEY")
                elif provider == "openai":
                    print(f"   • {provider}: 需要添加 OPENAI_API_KEY")
        
        if len(session_results['missing_token_data']) > 0:
            print(f"\n3️⃣ 手动收集缺失的 token 数据:")
            print("   运行以下命令手动处理 session 文件:")
            print("   python3 /root/.openclaw/workspace/skills/token-monitor/scripts/token_stats.py")
        
        print(f"\n4️⃣ 创建自动修复脚本:")
        print("   可以基于诊断结果生成自动修复脚本")
        
        # 保存诊断结果
        diagnosis_report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_diagnosis": session_results,
            "token_logger_diagnosis": token_logger_results,
            "token_usage_diagnosis": token_usage_results,
            "models_diagnosis": models_results,
            "summary": {
                "total_sessions": session_results['total_sessions'],
                "sessions_with_tokens": session_results['sessions_with_tokens'],
                "token_logger_enabled": token_logger_results['token_logger_enabled'],
                "token_usage_exists": token_usage_results['file_exists'],
                "missing_providers": models_results['missing_providers'],
                "issues_count": len(session_results['issues_found']) + len(token_logger_results['hook_issues']) + len(token_usage_results['issues'])
            }
        }
        
        # 保存到文件 (转换sets为lists)
        report_file = Path("/root/.openclaw/workspace/reports/token-diagnosis-report.json")
        
        # 转换sets为lists
        serializable_report = {
            "timestamp": diagnosis_report["timestamp"],
            "session_diagnosis": {
                k: (list(v) if isinstance(v, set) else v) 
                for k, v in diagnosis_report["session_diagnosis"].items()
            },
            "token_logger_diagnosis": diagnosis_report["token_logger_diagnosis"],
            "token_usage_diagnosis": {
                k: (list(v) if isinstance(v, set) else v) 
                for k, v in diagnosis_report["token_usage_diagnosis"].items()
            },
            "models_diagnosis": {
                k: (list(v) if isinstance(v, set) else v) 
                for k, v in diagnosis_report["models_diagnosis"].items()
            },
            "summary": {
                k: (list(v) if isinstance(v, set) else v) 
                for k, v in diagnosis_report["summary"].items()
            }
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_report, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 详细诊断报告已保存到: {report_file}")
        
        return diagnosis_report

def main():
    parser = argparse.ArgumentParser(description="Token 收集系统诊断工具")
    parser.add_argument("--fix", action="store_true", help="尝试自动修复发现的问题")
    parser.add_argument("--output", help="输出报告文件路径")
    
    args = parser.parse_args()
    
    tool = TokenDiagnosticTool()
    
    if args.fix:
        print("⚠️  自动修复功能暂未实现")
        print("   请先运行诊断查看问题，然后手动修复")
    
    # 运行诊断
    report = tool.run_comprehensive_diagnosis()
    
    # 简要总结
    summary = report["summary"]
    print(f"\n📈 诊断总结:")
    print(f"  • 会话覆盖率: {summary['sessions_with_tokens']}/{summary['total_sessions']} ({summary['sessions_with_tokens']/summary['total_sessions']*100:.1f}%)")
    print(f"  • Token-Logger: {'✅' if summary['token_logger_enabled'] else '❌'}")
    print(f"  • Token 数据库: {'✅' if summary['token_usage_exists'] else '❌'}")
    print(f"  • 缺失提供商: {summary['missing_providers']}")
    print(f"  • 发现问题数: {summary['issues_count']}")

if __name__ == "__main__":
    main()