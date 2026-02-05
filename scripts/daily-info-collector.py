#!/usr/bin/env python3
"""
每日信息收集脚本 - OpenClaw 版本
基于 daily_info_collection 项目适配
数据源：国内热榜 + 国际科技资讯
"""

import requests
import json
from datetime import datetime
import os
import time
import re
from typing import Dict, List, Any, Optional


class DataValidator:
    """数据校验器"""
    
    @staticmethod
    def is_valid_url(url: Optional[str]) -> bool:
        if not url:
            return False
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return bool(re.match(pattern, url))
    
    @staticmethod
    def validate_url(url: Optional[str]) -> Optional[str]:
        if url and DataValidator.is_valid_url(url):
            return url
        return None


class DailyInfoCollector:
    """每日信息收集器"""
    
    def __init__(self, output_dir: str = None):
        self.date = datetime.now().strftime('%Y-%m-%d')
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.output_dir = output_dir or f"/root/.openclaw/workspace/reports/daily-info/{self.date}"
        self.results = []
        self.valid_items = []
        
        # 数据源配置 - 多源备选
        self.api_sources = {
            "哔哩哔哩热榜": {
                "url": "https://api.bilibili.com/x/web-interface/ranking/v2?rid=0&type=all",
                "category": "social",
                "platform": "bilibili",
                "max_news": 20,
                "parser": "bilibili_ranking"
            },
            "知乎热榜": {
                "url": "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=50",
                "category": "social",
                "platform": "zhihu",
                "max_news": 20,
                "parser": "zhihu_hot"
            },
            "GitHub Trending": {
                "url": "https://api.github.com/search/repositories?q=stars:>100&sort=stars&order=desc&per_page=20",
                "category": "tech",
                "platform": "github",
                "max_news": 20,
                "parser": "github_trending"
            },
            "Hacker News": {
                "url": "https://hacker-news.firebaseio.com/v0/topstories.json",
                "category": "tech",
                "platform": "hackernews",
                "max_news": 20,
                "parser": "hackernews_top"
            }
        }
    
    def prepare_output_directory(self):
        os.makedirs(self.output_dir, exist_ok=True)
    
    def normalize_item(self, raw_item: Dict, source_name: str, category: str, platform: str, rank: int) -> Dict:
        """标准化数据项"""
        return {
            "id": raw_item.get('id') or f"{platform}_{rank}",
            "title": raw_item.get('title', ''),
            "content": {
                "summary": raw_item.get('desc') or raw_item.get('description'),
                "full_text": None
            },
            "media": {
                "image": {
                    "url": DataValidator.validate_url(raw_item.get('pic') or raw_item.get('cover')),
                    "thumbnail": None
                },
                "video": None
            },
            "links": {
                "main": DataValidator.validate_url(raw_item.get('url') or raw_item.get('link')),
                "mobile": DataValidator.validate_url(raw_item.get('mobileUrl')),
                "share": None
            },
            "metrics": {
                "hot": {
                    "value": raw_item.get('hot') or raw_item.get('heat'),
                    "label": "热度"
                },
                "views": None,
                "interactions": {
                    "likes": raw_item.get('likes'),
                    "comments": raw_item.get('comments'),
                    "shares": raw_item.get('shares')
                }
            },
            "author": {
                "name": raw_item.get('author'),
                "avatar": None
            },
            "time": {
                "published": raw_item.get('time') or raw_item.get('publish_time'),
                "collected": datetime.now().isoformat()
            },
            "category": category,
            "tags": [],
            "meta": {
                "source": source_name,
                "platform": platform,
                "category": category,
                "rank": rank,
                "collection_time": datetime.now().isoformat()
            }
        }
    
    def fetch_api_data(self, source_name: str, config: Dict) -> Dict:
        """获取API数据"""
        url = config['url']
        category = config['category']
        platform = config['platform']
        max_news = config.get('max_news', 20)
        
        print(f"  Fetching {source_name}...", end=' ')
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://api.lolimi.cn/'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code != 200:
                print(f"FAILED (HTTP {response.status_code})")
                return self._create_error_result(source_name, category, platform, f"HTTP {response.status_code}")
            
            data = response.json()
            if 'data' not in data or not isinstance(data['data'], list):
                print("FAILED (Invalid structure)")
                return self._create_error_result(source_name, category, platform, "Invalid data structure")
            
            raw_items = data['data'][:max_news]
            normalized_items = []
            
            for rank, raw_item in enumerate(raw_items, 1):
                normalized = self.normalize_item(raw_item, source_name, category, platform, rank)
                if normalized.get('title'):  # 确保有标题
                    normalized_items.append(normalized)
            
            print(f"OK ({len(normalized_items)} items)")
            return {
                "source": source_name,
                "category": category,
                "platform": platform,
                "status": "success",
                "count": len(raw_items),
                "valid_count": len(normalized_items),
                "items": normalized_items
            }
            
        except Exception as e:
            print(f"ERROR ({str(e)})")
            return self._create_error_result(source_name, category, platform, str(e))
    
    def _create_error_result(self, source_name, category, platform, error):
        return {
            "source": source_name,
            "category": category,
            "platform": platform,
            "status": "error",
            "error": error,
            "count": 0,
            "valid_count": 0,
            "items": []
        }
    
    def collect_all(self):
        """收集所有数据源"""
        self.prepare_output_directory()
        
        print(f"\n{'='*60}")
        print(f"📰 Daily Info Collector - {self.date}")
        print(f"{'='*60}\n")
        
        for source_name, config in self.api_sources.items():
            result = self.fetch_api_data(source_name, config)
            self.results.append(result)
            self.valid_items.extend(result.get('items', []))
            time.sleep(1)  # 礼貌延迟
        
        return self.save_and_summarize()
    
    def save_and_summarize(self):
        """保存结果并生成汇总"""
        total_items = len(self.valid_items)
        successful = len([r for r in self.results if r['status'] == 'success'])
        failed = len([r for r in self.results if r['status'] == 'error'])
        
        # 按分类统计
        categories = {}
        for item in self.valid_items:
            cat = item.get('category', 'unknown')
            if cat not in categories:
                categories[cat] = {'count': 0, 'sources': set()}
            categories[cat]['count'] += 1
            categories[cat]['sources'].add(item.get('meta', {}).get('platform', ''))
        
        # 构建分类统计（转换为列表）
        category_summary = {}
        for cat, stats in categories.items():
            category_summary[cat] = {
                'count': stats['count'],
                'sources': list(stats['sources'])
            }
        
        output_data = {
            "schema_version": "2.0",
            "date": self.date,
            "collection_time": datetime.now().isoformat(),
            "summary": {
                "total_items": total_items,
                "total_sources": len(self.results),
                "successful_sources": successful,
                "failed_sources": failed,
                "categories": category_summary
            },
            "items": self.valid_items
        }
        
        # 保存详细数据
        detail_file = os.path.join(self.output_dir, f"daily_info_{self.timestamp}.json")
        with open(detail_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        # 保存最新汇总（供快速查看）
        latest_file = os.path.join(self.output_dir, "latest.json")
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        # 生成 Markdown 报告
        md_content = self.generate_markdown_report(output_data)
        md_file = os.path.join(self.output_dir, f"daily_info_{self.timestamp}.md")
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        # 保存 latest.md
        latest_md = os.path.join(self.output_dir, "latest.md")
        with open(latest_md, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        print(f"\n{'='*60}")
        print(f"✅ Collection Complete")
        print(f"{'='*60}")
        print(f"Total Items: {total_items}")
        print(f"Sources: {successful}/{len(self.results)} successful")
        print(f"Output: {detail_file}")
        print(f"{'='*60}\n")
        
        return {
            "date": self.date,
            "total_items": total_items,
            "successful_sources": successful,
            "failed_sources": failed,
            "output_files": {
                "json": detail_file,
                "markdown": md_file,
                "latest_json": latest_file,
                "latest_md": latest_md
            },
            "summary": output_data["summary"]
        }
    
    def generate_markdown_report(self, data: Dict) -> str:
        """生成 Markdown 报告"""
        lines = [
            f"# 📰 每日信息收集报告 - {self.date}",
            "",
            f"**收集时间**: {data['collection_time']}",
            f"**数据版本**: Schema {data['schema_version']}",
            "",
            "## 📊 汇总统计",
            "",
            f"- **总条目数**: {data['summary']['total_items']}",
            f"- **数据源**: {data['summary']['successful_sources']}/{data['summary']['total_sources']} 成功",
            "",
            "### 按分类统计",
            ""
        ]
        
        for cat, stats in data['summary']['categories'].items():
            cat_emoji = {"social": "📱", "tech": "💻", "economic": "💰"}.get(cat, "📄")
            lines.append(f"- {cat_emoji} **{cat}**: {stats['count']} 条")
        
        lines.extend(["", "## 📑 热门内容", ""])
        
        # 按分类分组显示
        cat_items = {}
        for item in data['items'][:50]:  # 最多显示50条
            cat = item.get('category', 'unknown')
            if cat not in cat_items:
                cat_items[cat] = []
            cat_items[cat].append(item)
        
        for cat, items in cat_items.items():
            cat_name = {"social": "社交媒体", "tech": "科技资讯", "economic": "财经新闻"}.get(cat, cat)
            lines.extend([f"### {cat_name}", ""])
            for i, item in enumerate(items[:10], 1):  # 每类最多10条
                title = item.get('title', 'N/A')
                link = item.get('links', {}).get('main', '')
                hot = item.get('metrics', {}).get('hot', {}).get('value', '')
                hot_str = f" 🔥{hot}" if hot else ""
                
                if link:
                    lines.append(f"{i}. [{title}]({link}){hot_str}")
                else:
                    lines.append(f"{i}. {title}{hot_str}")
            lines.append("")
        
        lines.extend(["---", "", "*Generated by OpenClaw Daily Info Collector*"])
        return "\n".join(lines)


def main():
    collector = DailyInfoCollector()
    result = collector.collect_all()
    
    # 输出简要汇报（供 OpenClaw 读取）
    print("\n" + "="*60)
    print("BRIEF_REPORT_START")
    print(json.dumps({
        "date": result["date"],
        "total_items": result["total_items"],
        "sources_success": result["successful_sources"],
        "sources_failed": result["failed_sources"],
        "output_dir": collector.output_dir
    }, ensure_ascii=False))
    print("BRIEF_REPORT_END")
    print("="*60)


if __name__ == "__main__":
    main()
