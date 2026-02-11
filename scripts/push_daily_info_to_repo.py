#!/usr/bin/env python3
"""
将每日信息数据转换为 DATA_SCHEMA 格式并推送到 daily_info_collection 仓库
"""
import json
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

# 配置
SOURCE_DIR = "/root/.openclaw/workspace/reports/daily-info"
TARGET_REPO = "/tmp/daily_info_collection"
DATA_DIR = f"{TARGET_REPO}/data"

def convert_to_schema_format(source_data):
    """将 V3 数据转换为 DATA_SCHEMA 格式"""
    
    # 转换分类统计
    categories = {}
    for cat_key, cat_data in source_data.get("summary", {}).get("categories", {}).items():
        categories[cat_key] = {
            "count": cat_data.get("count", 0),
            "sources": cat_data.get("sources", [])
        }
    
    # 转换 items
    items = []
    for item in source_data.get("items", []):
        converted = {
            "id": item.get("id"),
            "title": item.get("title"),
            "content": item.get("content", {}),
            "media": item.get("media", {}),
            "links": item.get("links", {}),
            "metrics": item.get("metrics", {}),
            "author": item.get("author", {}),
            "time": {
                "published": item.get("time", {}).get("published"),
                "collected": item.get("time", {}).get("collected")
            },
            "category": item.get("category"),
            "tags": item.get("tags", []),
            "meta": {
                "source": item.get("meta", {}).get("source"),
                "platform": item.get("meta", {}).get("platform"),
                "rank": item.get("meta", {}).get("rank"),
                "is_hot": item.get("meta", {}).get("is_hot", False),
                "collection_time": item.get("meta", {}).get("collection_time")
            }
        }
        items.append(converted)
    
    # 构建标准格式
    result = {
        "schema_version": "2.0",
        "date": source_data.get("date"),
        "collection_time": source_data.get("collection_time", "").replace("T", " ")[:19],
        "summary": {
            "total_items": source_data.get("summary", {}).get("total_items", 0),
            "total_sources": source_data.get("summary", {}).get("successful_sources", 0),
            "failed_sources": source_data.get("summary", {}).get("failed_sources", 0),
            "categories": categories
        },
        "items": items
    }
    
    return result

def push_to_repo(date_str):
    """将指定日期的数据推送到仓库"""
    
    # 读取源数据
    source_file = f"{SOURCE_DIR}/{date_str}/daily_info_{date_str.replace('-', '')}_*.json"
    import glob
    files = glob.glob(source_file)
    
    if not files:
        print(f"❌ 未找到 {date_str} 的数据文件")
        return False
    
    source_path = files[0]
    print(f"📖 读取源数据: {source_path}")
    
    with open(source_path, 'r', encoding='utf-8') as f:
        source_data = json.load(f)
    
    # 转换格式
    converted = convert_to_schema_format(source_data)
    
    # 确保数据目录存在
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # 写入目标文件
    target_file = f"{DATA_DIR}/{date_str}.json"
    with open(target_file, 'w', encoding='utf-8') as f:
        json.dump(converted, f, ensure_ascii=False, indent=2)
    
    print(f"💾 已保存: {target_file}")
    
    # Git 操作
    os.chdir(TARGET_REPO)
    
    # 配置 git（如果还没有）
    subprocess.run(["git", "config", "user.email", "clawdbot@openclaw.ai"], capture_output=True)
    subprocess.run(["git", "config", "user.name", "ClawdBot"], capture_output=True)
    
    # 添加、提交、推送
    subprocess.run(["git", "add", f"data/{date_str}.json"], check=True)
    
    # 检查是否有变更
    result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    if not result.stdout.strip():
        print("ℹ️ 没有新变更需要提交")
        return True
    
    # 提交
    commit_msg = f"📰 Daily info: {date_str} ({converted['summary']['total_items']} items) [from clawdbot]"
    subprocess.run(["git", "commit", "-m", commit_msg], check=True)
    
    # 推送
    subprocess.run(["git", "push", "origin", "master"], check=True)
    
    print(f"✅ 已成功推送到仓库: https://github.com/ShenWang96/daily_info_collection")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        date_str = sys.argv[1]
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    print(f"🚀 开始推送 {date_str} 的数据...")
    success = push_to_repo(date_str)
    sys.exit(0 if success else 1)
