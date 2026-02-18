#!/usr/bin/env python3
"""
每日信息收集脚本 - OpenClaw 版本 V2
基于 daily_info_collection 项目架构
数据源：GitHub Trending + Hacker News + Reddit + 技术资讯
"""

import requests
import json
from datetime import datetime
import os
import time
import re
from typing import Dict, List, Any, Optional


class DailyInfoCollectorV2:
    """每日信息收集器 V2 - 国际科技资讯为主"""
    
    def __init__(self, output_dir: str = None):
        self.date = datetime.now().strftime('%Y-%m-%d')
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.output_dir = output_dir or f"/root/.openclaw/workspace/reports/daily-info/{self.date}"
        self.results = []
        self.valid_items = []
    
    def prepare_output_directory(self):
        os.makedirs(self.output_dir, exist_ok=True)
    
    def normalize_common(self, title: str, url: str, source: str, category: str, 
                        platform: str, rank: int = 0, **kwargs) -> Dict:
        """通用数据标准化"""
        return {
            "id": kwargs.get('id') or f"{platform}_{rank}",
            "title": title,
            "content": {
                "summary": kwargs.get('summary') or kwargs.get('description'),
                "full_text": None
            },
            "media": {
                "image": {"url": kwargs.get('image_url'), "thumbnail": None},
                "video": None
            },
            "links": {
                "main": url,
                "mobile": None,
                "share": kwargs.get('share_url')
            },
            "metrics": {
                "hot": {"value": kwargs.get('stars') or kwargs.get('score'), "label": kwargs.get('metric_label', '热度')},
                "views": kwargs.get('views'),
                "interactions": {
                    "likes": kwargs.get('likes'),
                    "comments": kwargs.get('comments'),
                    "shares": kwargs.get('shares')
                }
            },
            "author": {
                "name": kwargs.get('author'),
                "avatar": kwargs.get('author_avatar')
            },
            "time": {
                "published": kwargs.get('published_at'),
                "collected": datetime.now().isoformat()
            },
            "category": category,
            "tags": kwargs.get('tags', []),
            "meta": {
                "source": source,
                "platform": platform,
                "category": category,
                "rank": rank,
                "collection_time": datetime.now().isoformat()
            }
        }
    
    def fetch_github_trending(self) -> Dict:
        """获取 GitHub Trending (使用 search API)"""
        print("  Fetching GitHub Trending...", end=' ')
        
        try:
            # 获取最近一周创建的优质仓库
            one_week_ago = (datetime.now() - __import__('datetime').timedelta(days=7)).strftime('%Y-%m-%d')
            url = f"https://api.github.com/search/repositories?q=created:>{one_week_ago}&sort=stars&order=desc&per_page=20"
            
            response = requests.get(url, timeout=30)
            if response.status_code != 200:
                print(f"FAILED (HTTP {response.status_code})")
                return self._error_result("GitHub Trending", "tech", "github", f"HTTP {response.status_code}")
            
            data = response.json()
            items = []
            
            for rank, repo in enumerate(data.get('items', [])[:20], 1):
                item = self.normalize_common(
                    title=repo.get('name', ''),
                    url=repo.get('html_url', ''),
                    source="GitHub Trending",
                    category="tech",
                    platform="github",
                    rank=rank,
                    id=str(repo.get('id')),
                    summary=repo.get('description'),
                    author=repo.get('owner', {}).get('login'),
                    author_avatar=repo.get('owner', {}).get('avatar_url'),
                    stars=repo.get('stargazers_count'),
                    metric_label="Stars",
                    tags=repo.get('topics', []),
                    published_at=repo.get('created_at')
                )
                items.append(item)
            
            print(f"OK ({len(items)} repos)")
            return self._success_result("GitHub Trending", "tech", "github", len(items), items)
            
        except Exception as e:
            print(f"ERROR ({str(e)})")
            return self._error_result("GitHub Trending", "tech", "github", str(e))
    
    def fetch_hackernews(self) -> Dict:
        """获取 Hacker News 热门"""
        print("  Fetching Hacker News...", end=' ')
        
        try:
            # 先获取 Top Stories ID 列表
            top_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
            response = requests.get(top_url, timeout=30)
            
            if response.status_code != 200:
                print(f"FAILED (HTTP {response.status_code})")
                return self._error_result("Hacker News", "tech", "hackernews", f"HTTP {response.status_code}")
            
            story_ids = response.json()[:20]  # 取前20个
            items = []
            
            for rank, story_id in enumerate(story_ids, 1):
                try:
                    story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                    story_resp = requests.get(story_url, timeout=10)
                    
                    if story_resp.status_code == 200:
                        story = story_resp.json()
                        if story:
                            item = self.normalize_common(
                                title=story.get('title', ''),
                                url=story.get('url') or f"https://news.ycombinator.com/item?id={story_id}",
                                source="Hacker News",
                                category="tech",
                                platform="hackernews",
                                rank=rank,
                                id=str(story_id),
                                summary=None,
                                author=story.get('by'),
                                score=story.get('score'),
                                metric_label="Points",
                                comments=story.get('descendants')
                            )
                            items.append(item)
                    time.sleep(0.1)  # 礼貌延迟
                except:
                    continue
            
            print(f"OK ({len(items)} stories)")
            return self._success_result("Hacker News", "tech", "hackernews", len(items), items)
            
        except Exception as e:
            print(f"ERROR ({str(e)})")
            return self._error_result("Hacker News", "tech", "hackernews", str(e))
    
    def fetch_producthunt(self) -> Dict:
        """获取 Product Hunt 热门（通过非官方方式）"""
        print("  Fetching Product Hunt...", end=' ')
        
        try:
            # Product Hunt 需要认证，这里尝试获取今日热门（可能会失败）
            url = "https://www.producthunt.com/feed"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                # 简化处理 - 实际上需要解析 HTML
                print("OK (fallback)")
                return self._success_result("Product Hunt", "tech", "producthunt", 0, [])
            else:
                print(f"FAILED (HTTP {response.status_code})")
                return self._error_result("Product Hunt", "tech", "producthunt", f"HTTP {response.status_code}")
                
        except Exception as e:
            print(f"ERROR ({str(e)})")
            return self._error_result("Product Hunt", "tech", "producthunt", str(e))
    
    def fetch_devto(self) -> Dict:
        """获取 Dev.to 热门文章"""
        print("  Fetching Dev.to...", end=' ')
        
        try:
            url = "https://dev.to/api/articles?per_page=20&top=7"
            response = requests.get(url, timeout=30)
            
            if response.status_code != 200:
                print(f"FAILED (HTTP {response.status_code})")
                return self._error_result("Dev.to", "tech", "devto", f"HTTP {response.status_code}")
            
            articles = response.json()
            items = []
            
            for rank, article in enumerate(articles[:20], 1):
                item = self.normalize_common(
                    title=article.get('title', ''),
                    url=article.get('url', ''),
                    source="Dev.to",
                    category="tech",
                    platform="devto",
                    rank=rank,
                    id=str(article.get('id')),
                    summary=article.get('description'),
                    author=article.get('user', {}).get('name'),
                    author_avatar=article.get('user', {}).get('profile_image'),
                    likes=article.get('positive_reactions_count'),
                    comments=article.get('comments_count'),
                    tags=article.get('tag_list', []),
                    published_at=article.get('published_at')
                )
                items.append(item)
            
            print(f"OK ({len(items)} articles)")
            return self._success_result("Dev.to", "tech", "devto", len(items), items)
            
        except Exception as e:
            print(f"ERROR ({str(e)})")
            return self._error_result("Dev.to", "tech", "devto", str(e))
    
    def _success_result(self, source, category, platform, count, items):
        return {
            "source": source,
            "category": category,
            "platform": platform,
            "status": "success",
            "count": count,
            "valid_count": len(items),
            "items": items
        }
    
    def _error_result(self, source, category, platform, error):
        return {
            "source": source,
            "category": category,
            "platform": platform,
            "status": "error",
            "error": str(error),
            "count": 0,
            "valid_count": 0,
            "items": []
        }
    
    def collect_all(self):
        """收集所有数据源"""
        self.prepare_output_directory()
        
        print(f"\n{'='*60}")
        print(f"📰 Daily Info Collector V2 - {self.date}")
        print(f"{'='*60}\n")
        
        # 执行各数据源收集
        collectors = [
            self.fetch_github_trending,
            self.fetch_hackernews,
            self.fetch_devto,
            # self.fetch_producthunt  # 可能需要认证，暂时跳过
        ]
        
        for collector in collectors:
            result = collector()
            self.results.append(result)
            self.valid_items.extend(result.get('items', []))
            time.sleep(1)
        
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
        
        # 构建分类统计
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
        
        # 保存 latest.json
        latest_json = os.path.join(self.output_dir, "latest.json")
        with open(latest_json, 'w', encoding='utf-8') as f:
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
                "latest_json": latest_json,
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
            "### 按来源统计",
            ""
        ]
        
        # 按来源统计
        for result in self.results:
            if result['status'] == 'success':
                emoji = {"github": "⭐", "hackernews": "📰", "devto": "💻", "producthunt": "🚀"}.get(result['platform'], "📄")
                lines.append(f"- {emoji} **{result['source']}**: {result['valid_count']} 条")
        
        lines.extend(["", "## 📑 热门内容", ""])
        
        # GitHub Trending
        github_items = [i for i in data['items'] if i.get('meta', {}).get('platform') == 'github'][:10]
        if github_items:
            lines.extend(["### ⭐ GitHub Trending", ""])
            for i, item in enumerate(github_items, 1):
                title = item.get('title', 'N/A')
                url = item.get('links', {}).get('main', '')
                stars = item.get('metrics', {}).get('hot', {}).get('value', '')
                summary = item.get('content', {}).get('summary', '')
                lines.append(f"{i}. **[{title}]({url})** ⭐{stars}")
                if summary:
                    lines.append(f"   > {summary[:100]}..." if len(summary) > 100 else f"   > {summary}")
                lines.append("")
        
        # Hacker News
        hn_items = [i for i in data['items'] if i.get('meta', {}).get('platform') == 'hackernews'][:10]
        if hn_items:
            lines.extend(["### 📰 Hacker News", ""])
            for i, item in enumerate(hn_items, 1):
                title = item.get('title', 'N/A')
                url = item.get('links', {}).get('main', '')
                score = item.get('metrics', {}).get('hot', {}).get('value', '')
                comments = item.get('metrics', {}).get('interactions', {}).get('comments', '')
                comment_str = f" 💬{comments}" if comments else ""
                lines.append(f"{i}. [{title}]({url}) 🔺{score}{comment_str}")
            lines.append("")
        
        # Dev.to
        devto_items = [i for i in data['items'] if i.get('meta', {}).get('platform') == 'devto'][:10]
        if devto_items:
            lines.extend(["### 💻 Dev.to 热门", ""])
            for i, item in enumerate(devto_items, 1):
                title = item.get('title', 'N/A')
                url = item.get('links', {}).get('main', '')
                likes = item.get('metrics', {}).get('interactions', {}).get('likes', '')
                like_str = f" ❤️{likes}" if likes else ""
                lines.append(f"{i}. [{title}]({url}){like_str}")
            lines.append("")
        
        lines.extend(["---", "", "*Generated by OpenClaw Daily Info Collector V2*"])
        return "\n".join(lines)


def main():
    collector = DailyInfoCollectorV2()
    result = collector.collect_all()
    
    # 输出简要汇报
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
