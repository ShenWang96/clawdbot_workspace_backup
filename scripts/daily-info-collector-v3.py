#!/usr/bin/env python3
"""
每日信息收集脚本 - OpenClaw 版本 V3
按四大分类组织数据源：政治、经济、科技、社交媒体
每个分类配置多个数据源 + 备选方案
"""

import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import os
import time
import re
import random
from typing import Dict, List, Any, Optional, Callable
from urllib.parse import urljoin


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


class DailyInfoCollectorV3:
    """每日信息收集器 V3 - 四大分类架构"""
    
    CATEGORIES = {
        'political': {'name': '政治', 'emoji': '🏛️', 'priority': 1},
        'economic': {'name': '经济', 'emoji': '💰', 'priority': 2},
        'tech': {'name': '科技', 'emoji': '💻', 'priority': 3},
        'social': {'name': '社交媒体', 'emoji': '📱', 'priority': 4}
    }
    
    # 全局超时配置（秒）
    TIMEOUT_CONFIG = {
        'default': 10,      # 默认超时
        'rss': 10,          # RSS源超时
        'api': 15,          # API超时
        'slow_api': 20,     # 慢API超时
        'between_sources': 0.5,  # 数据源间延迟
    }
    
    def __init__(self, output_dir: str = None):
        self.date = datetime.now().strftime('%Y-%m-%d')
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.output_dir = output_dir or f"/root/.openclaw/workspace/reports/daily-info/{self.date}"
        self.results = []
        self.valid_items = []
        self.validator = DataValidator()
        self.errors = []  # 错误日志
        
        # 请求会话配置
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/xml, application/rss+xml, text/html, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
    
    def log_error(self, source: str, error: str):
        """记录错误"""
        error_entry = {
            "source": source,
            "error": str(error),
            "time": datetime.now().isoformat()
        }
        self.errors.append(error_entry)
        print(f"  ❌ [{source}] ERROR: {str(error)[:80]}")
    
    def safe_request(self, url: str, headers: dict = None, timeout: int = None, method: str = 'get') -> Optional[requests.Response]:
        """安全的HTTP请求，带超时和错误处理"""
        timeout = timeout or self.TIMEOUT_CONFIG['default']
        headers = headers or {}
        
        try:
            if method.lower() == 'get':
                resp = self.session.get(url, headers=headers, timeout=timeout)
            else:
                resp = self.session.post(url, headers=headers, timeout=timeout)
            return resp
        except requests.Timeout:
            raise TimeoutError(f"Request timeout after {timeout}s")
        except requests.RequestException as e:
            raise ConnectionError(f"Request failed: {str(e)}")
    
    def run_collector_safely(self, collector_func, source_name: str) -> Dict:
        """安全运行收集器，确保单个失败不影响整体"""
        try:
            result = collector_func()
            return result
        except Exception as e:
            self.log_error(source_name, str(e))
            return self._error_result(source_name, "unknown", source_name.lower().replace(' ', '_'), str(e))
    
    def prepare_output_directory(self):
        os.makedirs(self.output_dir, exist_ok=True)
    
    def normalize_item(self, title: str, url: str, source: str, category: str, 
                      platform: str, rank: int = 0, **kwargs) -> Optional[Dict]:
        """标准化数据项"""
        if not title or not url:
            return None
            
        return {
            "id": kwargs.get('id') or f"{platform}_{rank}_{int(time.time())}",
            "title": title[:200],  # 限制长度
            "content": {
                "summary": kwargs.get('summary', '')[:500] if kwargs.get('summary') else None,
                "full_text": None
            },
            "media": {
                "image": {"url": self.validator.validate_url(kwargs.get('image_url')), "thumbnail": None},
                "video": None
            },
            "links": {
                "main": url,
                "mobile": self.validator.validate_url(kwargs.get('mobile_url')),
                "share": None
            },
            "metrics": {
                "hot": {
                    "value": kwargs.get('hot') or kwargs.get('score') or kwargs.get('stars'), 
                    "label": kwargs.get('metric_label', '热度')
                },
                "views": kwargs.get('views'),
                "interactions": {
                    "likes": kwargs.get('likes'),
                    "comments": kwargs.get('comments'),
                    "shares": kwargs.get('shares')
                }
            },
            "author": {
                "name": kwargs.get('author', '')[:50] if kwargs.get('author') else None,
                "avatar": self.validator.validate_url(kwargs.get('author_avatar'))
            },
            "time": {
                "published": kwargs.get('published_at'),
                "collected": datetime.now().isoformat()
            },
            "category": category,
            "tags": kwargs.get('tags', [])[:10],  # 限制标签数量
            "meta": {
                "source": source,
                "platform": platform,
                "category": category,
                "rank": rank,
                "collection_time": datetime.now().isoformat()
            }
        }
    
    def _success_result(self, source, category, platform, count, items):
        return {
            "source": source, "category": category, "platform": platform,
            "status": "success", "count": count, "valid_count": len(items), "items": items
        }
    
    def _error_result(self, source, category, platform, error):
        return {
            "source": source, "category": category, "platform": platform,
            "status": "error", "error": str(error), "count": 0, "valid_count": 0, "items": []
        }
    
    # ==================== 政治类数据源 ====================
    
    def fetch_reuters_news(self) -> Dict:
        """Reuters RSS 新闻（国际政治经济）"""
        print("  [政治] Fetching Reuters...", end=' ', flush=True)
        
        try:
            # Reuters RSS feeds
            feeds = [
                "https://www.reutersagency.com/feed/?taxonomy=markets&post_type=reuters-best",
                "https://www.reutersagency.com/feed/?taxonomy=tag:world&post_type=reuters-best"
            ]
            
            items = []
            for feed_url in feeds:
                try:
                    resp = self.safe_request(feed_url, timeout=self.TIMEOUT_CONFIG['rss'])
                    if resp and resp.status_code == 200:
                        root = ET.fromstring(resp.content)
                        channel = root.find('.//channel')
                        if channel is not None:
                            for item in channel.findall('item')[:10]:
                                title = item.findtext('title', '')
                                link = item.findtext('link', '')
                                desc = item.findtext('description', '')
                                pub_date = item.findtext('pubDate', '')
                                
                                if title and link:
                                    normalized = self.normalize_item(
                                        title=title, url=link, source="Reuters",
                                        category="political", platform="reuters",
                                        rank=len(items)+1, summary=desc,
                                        published_at=pub_date
                                    )
                                    if normalized:
                                        items.append(normalized)
                        break  # 成功一个就跳出
                except Exception as e:
                    continue
            
            print(f"OK ({len(items)} items)")
            return self._success_result("Reuters", "political", "reuters", len(items), items)
            
        except Exception as e:
            self.log_error("Reuters", str(e))
            return self._error_result("Reuters", "political", "reuters", str(e))
    
    def fetch_bbc_news(self) -> Dict:
        """BBC News RSS"""
        print("  [政治] Fetching BBC News...", end=' ', flush=True)
        
        try:
            url = "http://feeds.bbci.co.uk/news/world/rss.xml"
            resp = self.safe_request(url, timeout=self.TIMEOUT_CONFIG['rss'])
            
            if not resp or resp.status_code != 200:
                return self._error_result("BBC News", "political", "bbc", f"HTTP {resp.status_code if resp else 'No response'}")
            
            root = ET.fromstring(resp.content)
            items = []
            
            for item in root.findall('.//item')[:15]:
                title = item.findtext('title', '')
                link = item.findtext('link', '')
                desc = item.findtext('description', '')
                
                if title and link:
                    normalized = self.normalize_item(
                        title=title, url=link, source="BBC News",
                        category="political", platform="bbc",
                        rank=len(items)+1, summary=desc
                    )
                    if normalized:
                        items.append(normalized)
            
            print(f"OK ({len(items)} items)")
            return self._success_result("BBC News", "political", "bbc", len(items), items)
            
        except Exception as e:
            self.log_error("BBC News", str(e))
            return self._error_result("BBC News", "political", "bbc", str(e))
    
    # ==================== 经济类数据源 ====================
    
    def fetch_yahoo_finance(self) -> Dict:
        """Yahoo Finance 市场新闻（通过 RSS）"""
        print("  [经济] Fetching Yahoo Finance...", end=' ', flush=True)
        
        try:
            url = "https://finance.yahoo.com/news/rssindex"
            resp = self.safe_request(url, timeout=self.TIMEOUT_CONFIG['rss'])
            
            if not resp or resp.status_code != 200:
                return self._error_result("Yahoo Finance", "economic", "yahoo_finance", f"HTTP {resp.status_code if resp else 'No response'}")
            
            root = ET.fromstring(resp.content)
            items = []
            
            for item in root.findall('.//item')[:15]:
                title = item.findtext('title', '')
                link = item.findtext('link', '')
                desc = item.findtext('description', '')
                
                if title and link:
                    normalized = self.normalize_item(
                        title=title, url=link, source="Yahoo Finance",
                        category="economic", platform="yahoo_finance",
                        rank=len(items)+1, summary=desc
                    )
                    if normalized:
                        items.append(normalized)
            
            print(f"OK ({len(items)} items)")
            return self._success_result("Yahoo Finance", "economic", "yahoo_finance", len(items), items)
            
        except Exception as e:
            self.log_error("Yahoo Finance", str(e))
            return self._error_result("Yahoo Finance", "economic", "yahoo_finance", str(e))
    
    def fetch_cnbc_finance(self) -> Dict:
        """CNBC 财经新闻"""
        print("  [经济] Fetching CNBC...", end=' ', flush=True)
        
        try:
            url = "https://www.cnbc.com/id/100003114/device/rss/rss.html"
            resp = self.safe_request(url, timeout=self.TIMEOUT_CONFIG['rss'])
            
            if not resp or resp.status_code != 200:
                return self._error_result("CNBC", "economic", "cnbc", f"HTTP {resp.status_code if resp else 'No response'}")
            
            root = ET.fromstring(resp.content)
            items = []
            
            for item in root.findall('.//item')[:15]:
                title = item.findtext('title', '')
                link = item.findtext('link', '')
                desc = item.findtext('description', '')
                
                if title and link:
                    normalized = self.normalize_item(
                        title=title, url=link, source="CNBC",
                        category="economic", platform="cnbc",
                        rank=len(items)+1, summary=desc
                    )
                    if normalized:
                        items.append(normalized)
            
            print(f"OK ({len(items)} items)")
            return self._success_result("CNBC", "economic", "cnbc", len(items), items)
            
        except Exception as e:
            self.log_error("CNBC", str(e))
            return self._error_result("CNBC", "economic", "cnbc", str(e))
    
    # ==================== 科技类数据源 ====================
    
    def fetch_github_trending(self) -> Dict:
        """GitHub Trending"""
        print("  [科技] Fetching GitHub Trending...", end=' ', flush=True)
        
        try:
            one_week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            url = f"https://api.github.com/search/repositories?q=created:>{one_week_ago}&sort=stars&order=desc&per_page=20"
            
            resp = self.safe_request(url, timeout=self.TIMEOUT_CONFIG['slow_api'])
            if not resp or resp.status_code != 200:
                return self._error_result("GitHub", "tech", "github", f"HTTP {resp.status_code if resp else 'No response'}")
            
            data = resp.json()
            items = []
            
            for rank, repo in enumerate(data.get('items', [])[:20], 1):
                normalized = self.normalize_item(
                    title=repo.get('name', ''),
                    url=repo.get('html_url', ''),
                    source="GitHub Trending",
                    category="tech", platform="github",
                    rank=rank, id=str(repo.get('id')),
                    summary=repo.get('description'),
                    author=repo.get('owner', {}).get('login'),
                    author_avatar=repo.get('owner', {}).get('avatar_url'),
                    stars=repo.get('stargazers_count'),
                    metric_label="Stars",
                    tags=repo.get('topics', []),
                    published_at=repo.get('created_at')
                )
                if normalized:
                    items.append(normalized)
            
            print(f"OK ({len(items)} repos)")
            return self._success_result("GitHub", "tech", "github", len(items), items)
            
        except Exception as e:
            self.log_error("GitHub", str(e))
            return self._error_result("GitHub", "tech", "github", str(e))
    
    def fetch_hackernews(self) -> Dict:
        """Hacker News"""
        print("  [科技] Fetching Hacker News...", end=' ', flush=True)
        
        try:
            top_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
            resp = self.safe_request(top_url, timeout=self.TIMEOUT_CONFIG['api'])
            
            if not resp or resp.status_code != 200:
                return self._error_result("Hacker News", "tech", "hackernews", f"HTTP {resp.status_code if resp else 'No response'}")
            
            story_ids = resp.json()[:20]
            items = []
            
            for rank, story_id in enumerate(story_ids, 1):
                try:
                    story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                    story_resp = self.safe_request(story_url, timeout=8)
                    
                    if story_resp and story_resp.status_code == 200:
                        story = story_resp.json()
                        if story:
                            normalized = self.normalize_item(
                                title=story.get('title', ''),
                                url=story.get('url') or f"https://news.ycombinator.com/item?id={story_id}",
                                source="Hacker News",
                                category="tech", platform="hackernews",
                                rank=rank, id=str(story_id),
                                author=story.get('by'),
                                score=story.get('score'),
                                metric_label="Points",
                                comments=story.get('descendants')
                            )
                            if normalized:
                                items.append(normalized)
                except:
                    continue
            
            print(f"OK ({len(items)} stories)")
            return self._success_result("Hacker News", "tech", "hackernews", len(items), items)
            
        except Exception as e:
            self.log_error("Hacker News", str(e))
            return self._error_result("Hacker News", "tech", "hackernews", str(e))
    
    def fetch_techcrunch(self) -> Dict:
        """TechCrunch RSS"""
        print("  [科技] Fetching TechCrunch...", end=' ', flush=True)
        
        try:
            url = "https://techcrunch.com/feed/"
            resp = self.safe_request(url, timeout=self.TIMEOUT_CONFIG['rss'])
            
            if not resp or resp.status_code != 200:
                return self._error_result("TechCrunch", "tech", "techcrunch", f"HTTP {resp.status_code if resp else 'No response'}")
            
            root = ET.fromstring(resp.content)
            items = []
            
            for item in root.findall('.//item')[:15]:
                title = item.findtext('title', '')
                link = item.findtext('link', '')
                desc = item.findtext('description', '')
                
                if title and link:
                    normalized = self.normalize_item(
                        title=title, url=link, source="TechCrunch",
                        category="tech", platform="techcrunch",
                        rank=len(items)+1, summary=desc
                    )
                    if normalized:
                        items.append(normalized)
            
            print(f"OK ({len(items)} items)")
            return self._success_result("TechCrunch", "tech", "techcrunch", len(items), items)
            
        except Exception as e:
            self.log_error("TechCrunch", str(e))
            return self._error_result("TechCrunch", "tech", "techcrunch", str(e))
    
    def fetch_devto(self) -> Dict:
        """Dev.to 热门文章"""
        print("  [科技] Fetching Dev.to...", end=' ', flush=True)
        
        try:
            url = "https://dev.to/api/articles?per_page=20&top=7"
            resp = self.safe_request(url, timeout=self.TIMEOUT_CONFIG['api'])
            
            if not resp or resp.status_code != 200:
                return self._error_result("Dev.to", "tech", "devto", f"HTTP {resp.status_code if resp else 'No response'}")
            
            articles = resp.json()
            items = []
            
            for rank, article in enumerate(articles[:20], 1):
                normalized = self.normalize_item(
                    title=article.get('title', ''),
                    url=article.get('url', ''),
                    source="Dev.to",
                    category="tech", platform="devto",
                    rank=rank, id=str(article.get('id')),
                    summary=article.get('description'),
                    author=article.get('user', {}).get('name'),
                    author_avatar=article.get('user', {}).get('profile_image'),
                    likes=article.get('positive_reactions_count'),
                    comments=article.get('comments_count'),
                    tags=article.get('tag_list', []),
                    published_at=article.get('published_at')
                )
                if normalized:
                    items.append(normalized)
            
            print(f"OK ({len(items)} articles)")
            return self._success_result("Dev.to", "tech", "devto", len(items), items)
            
        except Exception as e:
            self.log_error("Dev.to", str(e))
            return self._error_result("Dev.to", "tech", "devto", str(e))
    
    # ==================== 社交媒体类数据源 ====================
    
    def fetch_reddit_hot(self) -> Dict:
        """Reddit 热门（r/technology, r/worldnews）"""
        print("  [社交] Fetching Reddit...", end=' ', flush=True)
        
        try:
            # Reddit JSON API（无需认证，但有限制）
            subreddits = ['technology', 'worldnews', 'programming']
            items = []
            
            for subreddit in subreddits:
                try:
                    url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=10"
                    resp = self.safe_request(url, timeout=self.TIMEOUT_CONFIG['api'])
                    
                    if resp and resp.status_code == 200:
                        data = resp.json()
                        posts = data.get('data', {}).get('children', [])
                        
                        for rank, post in enumerate(posts[:10], 1):
                            post_data = post.get('data', {})
                            title = post_data.get('title', '')
                            permalink = post_data.get('permalink', '')
                            url_link = post_data.get('url', '')
                            
                            # 优先使用外部链接，否则用 Reddit 链接
                            link = url_link if url_link and not url_link.startswith('/r/') else f"https://reddit.com{permalink}"
                            
                            if title:
                                normalized = self.normalize_item(
                                    title=title, url=link, source=f"Reddit r/{subreddit}",
                                    category="social", platform=f"reddit_{subreddit}",
                                    rank=len(items)+1, id=post_data.get('id'),
                                    summary=post_data.get('selftext', '')[:200] if post_data.get('selftext') else None,
                                    author=post_data.get('author'),
                                    score=post_data.get('score'),
                                    metric_label="Upvotes",
                                    comments=post_data.get('num_comments')
                                )
                                if normalized:
                                    items.append(normalized)
                except Exception as e:
                    continue
            
            print(f"OK ({len(items)} posts)")
            return self._success_result("Reddit", "social", "reddit", len(items), items)
            
        except Exception as e:
            self.log_error("Reddit", str(e))
            return self._error_result("Reddit", "social", "reddit", str(e))
    
    # ==================== 国内社交媒体数据源 ====================
    
    def fetch_zhihu_hot(self) -> Dict:
        """知乎热榜 - 使用 Cookie 认证"""
        print("  [社交] Fetching 知乎热榜...", end=' ', flush=True)
        
        try:
            url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=50"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Referer': 'https://www.zhihu.com/hot',
                'Cookie': 'z_c0=2|1:0|10:1770253111|4:z_c0|92:Mi4xQjllU0F3QUFBQUItTlpUWlFsZV9HeVlBQUFCZ0FsVk5OVGx4YWdEMll4bEYxWlNFbklqdGVSZE5YbzlKSVZwYkp3|d70fb725c9b1bc42d29f655cf8595703d352c758fec7e87da45213f2e1ceebfe'
            }
            
            resp = self.safe_request(url, headers=headers, timeout=self.TIMEOUT_CONFIG['api'])
            
            if not resp or resp.status_code != 200:
                return self._error_result("知乎热榜", "social", "zhihu", f"HTTP {resp.status_code if resp else 'No response'}")
            
            data = resp.json()
            items = []
            
            hot_list = data.get('data', [])
            for rank, item in enumerate(hot_list[:20], 1):
                try:
                    target = item.get('target', {})
                    title = target.get('title', '')
                    question_id = target.get('id', '')
                    
                    # 构建知乎问题链接
                    if question_id:
                        link = f"https://www.zhihu.com/question/{question_id}"
                    else:
                        link = target.get('url', '')
                    
                    # 获取热度信息
                    detail_text = item.get('detail_text', '')  # 如 "1234 万热度"
                    hot_value = None
                    if detail_text:
                        match = re.search(r'(\d+(?:\.\d+)?)\s*万', detail_text)
                        if match:
                            hot_value = int(float(match.group(1)) * 10000)
                    
                    if title and link:
                        normalized = self.normalize_item(
                            title=title,
                            url=link,
                            source="知乎热榜",
                            category="social",
                            platform="zhihu",
                            rank=rank,
                            id=str(question_id),
                            hot=hot_value,
                            metric_label="热度",
                            summary=item.get('excerpt', '')
                        )
                        if normalized:
                            items.append(normalized)
                except Exception as e:
                    continue
            
            print(f"OK ({len(items)} items)")
            return self._success_result("知乎热榜", "social", "zhihu", len(items), items)
            
        except Exception as e:
            self.log_error("知乎热榜", str(e))
            return self._error_result("知乎热榜", "social", "zhihu", str(e))
    
    def fetch_bilibili_hot(self) -> Dict:
        """B站热门排行榜（全站）"""
        print("  [社交] Fetching B站热门...", end=' ', flush=True)
        
        try:
            # B站全站热门排行榜
            url = "https://api.bilibili.com/x/web-interface/popular"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Referer': 'https://www.bilibili.com'
            }
            
            resp = self.safe_request(url, headers=headers, timeout=self.TIMEOUT_CONFIG['api'])
            
            if not resp or resp.status_code != 200:
                return self._error_result("B站热门", "social", "bilibili", f"HTTP {resp.status_code if resp else 'No response'}")
            
            data = resp.json()
            items = []
            
            if data.get('code') != 0:
                return self._error_result("B站热门", "social", "bilibili", f"API Error: {data.get('message', 'Unknown')}")
            
            video_list = data.get('data', {}).get('list', [])
            for rank, video in enumerate(video_list[:20], 1):
                try:
                    title = video.get('title', '')
                    bvid = video.get('bvid', '')
                    link = f"https://www.bilibili.com/video/{bvid}" if bvid else video.get('short_link', '')
                    
                    owner = video.get('owner', {})
                    author = owner.get('name', '')
                    
                    stat = video.get('stat', {})
                    views = stat.get('view', 0)
                    likes = stat.get('like', 0)
                    comments = stat.get('reply', 0)
                    
                    # 封面图
                    cover = video.get('pic', '')
                    
                    if title and link:
                        normalized = self.normalize_item(
                            title=title,
                            url=link,
                            source="B站热门",
                            category="social",
                            platform="bilibili",
                            rank=rank,
                            id=str(video.get('aid', '')),
                            views=views,
                            likes=likes,
                            comments=comments,
                            metric_label="播放量",
                            author=author,
                            image_url=cover,
                            summary=video.get('rcmd_reason', {}).get('content', '')
                        )
                        if normalized:
                            items.append(normalized)
                except Exception as e:
                    continue
            
            print(f"OK ({len(items)} videos)")
            return self._success_result("B站热门", "social", "bilibili", len(items), items)
            
        except Exception as e:
            self.log_error("B站热门", str(e))
            return self._error_result("B站热门", "social", "bilibili", str(e))
    
    # ==================== 主控逻辑 ====================
    
    def collect_all(self):
        """按分类收集所有数据源"""
        self.prepare_output_directory()
        
        print(f"\n{'='*70}")
        print(f"📰 Daily Info Collector V3 - {self.date}")
        print(f"   政治 | 经济 | 科技 | 社交媒体")
        print(f"   超时配置: RSS={self.TIMEOUT_CONFIG['rss']}s, API={self.TIMEOUT_CONFIG['api']}s")
        print(f"{'='*70}\n")
        
        # 按分类定义数据源（带优先级和名称映射）
        collectors_by_category = {
            'political': [
                (self.fetch_bbc_news, "BBC News"),
                (self.fetch_reuters_news, "Reuters"),
            ],
            'economic': [
                (self.fetch_yahoo_finance, "Yahoo Finance"),
                (self.fetch_cnbc_finance, "CNBC"),
            ],
            'tech': [
                (self.fetch_github_trending, "GitHub"),
                (self.fetch_hackernews, "Hacker News"),
                (self.fetch_techcrunch, "TechCrunch"),
                (self.fetch_devto, "Dev.to"),
            ],
            'social': [
                (self.fetch_zhihu_hot, "知乎热榜"),
                (self.fetch_bilibili_hot, "B站热门"),
                (self.fetch_reddit_hot, "Reddit"),
            ]
        }
        
        # 执行收集
        for category, collectors in collectors_by_category.items():
            cat_info = self.CATEGORIES.get(category, {})
            emoji = cat_info.get('emoji', '📄')
            name = cat_info.get('name', category)
            
            print(f"\n{emoji} [{name}] 开始收集...")
            
            for collector_func, source_name in collectors:
                # 使用安全包装器运行，确保单个失败不影响整体
                result = self.run_collector_safely(collector_func, source_name)
                self.results.append(result)
                if result['status'] == 'success':
                    self.valid_items.extend(result.get('items', []))
                time.sleep(self.TIMEOUT_CONFIG['between_sources'])  # 数据源间延迟
        
        return self.save_and_summarize()
    
    def save_and_summarize(self):
        """保存结果并生成汇总"""
        total_items = len(self.valid_items)
        successful = len([r for r in self.results if r['status'] == 'success'])
        failed = len([r for r in self.results if r['status'] == 'error'])
        
        # 按分类统计
        category_stats = {}
        for cat_key, cat_info in self.CATEGORIES.items():
            cat_items = [i for i in self.valid_items if i.get('category') == cat_key]
            sources = list(set(i.get('meta', {}).get('source', '') for i in cat_items))
            category_stats[cat_key] = {
                'name': cat_info['name'],
                'emoji': cat_info['emoji'],
                'count': len(cat_items),
                'sources': sources
            }
        
        output_data = {
            "schema_version": "3.0",
            "date": self.date,
            "collection_time": datetime.now().isoformat(),
            "summary": {
                "total_items": total_items,
                "total_sources": len(self.results),
                "successful_sources": successful,
                "failed_sources": failed,
                "categories": category_stats
            },
            "items": self.valid_items
        }
        
        # 保存文件
        detail_file = os.path.join(self.output_dir, f"daily_info_{self.timestamp}.json")
        with open(detail_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        latest_json = os.path.join(self.output_dir, "latest.json")
        with open(latest_json, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        md_content = self.generate_markdown_report(output_data)
        md_file = os.path.join(self.output_dir, f"daily_info_{self.timestamp}.md")
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        latest_md = os.path.join(self.output_dir, "latest.md")
        with open(latest_md, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        # 打印汇总
        print(f"\n{'='*70}")
        print(f"✅ 收集完成汇总")
        print(f"{'='*70}")
        print(f"总条目: {total_items} | 成功源: {successful}/{len(self.results)} | 失败: {failed}")
        print(f"\n按分类统计:")
        for cat_key, stats in category_stats.items():
            print(f"  {stats['emoji']} {stats['name']}: {stats['count']} 条")
        
        # 显示错误汇总（如果有）
        if self.errors:
            print(f"\n⚠️  失败源详情:")
            for err in self.errors[:5]:  # 最多显示5个错误
                print(f"  - {err['source']}: {err['error'][:60]}...")
        
        print(f"{'='*70}\n")
        
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
            "### 按分类统计",
            ""
        ]
        
        # 分类统计
        for cat_key, stats in data['summary']['categories'].items():
            lines.append(f"- {stats['emoji']} **{stats['name']}**: {stats['count']} 条")
        
        # 各分类详细内容
        lines.append("")
        
        for cat_key in ['political', 'economic', 'tech', 'social']:
            cat_stats = data['summary']['categories'].get(cat_key, {})
            cat_name = cat_stats.get('name', cat_key)
            cat_emoji = cat_stats.get('emoji', '📄')
            cat_items = [i for i in data['items'] if i.get('category') == cat_key]
            
            if not cat_items:
                continue
            
            lines.extend([f"## {cat_emoji} {cat_name}", ""])
            
            # 按来源分组
            sources = {}
            for item in cat_items:
                src = item.get('meta', {}).get('source', 'Unknown')
                if src not in sources:
                    sources[src] = []
                sources[src].append(item)
            
            for src_name, src_items in sources.items():
                lines.extend([f"### {src_name}", ""])
                for i, item in enumerate(src_items[:10], 1):  # 每源最多10条
                    title = item.get('title', 'N/A')
                    link = item.get('links', {}).get('main', '')
                    score = item.get('metrics', {}).get('hot', {}).get('value')
                    score_str = f" 🔥{score}" if score else ""
                    
                    if link:
                        lines.append(f"{i}. [{title}]({link}){score_str}")
                    else:
                        lines.append(f"{i}. {title}{score_str}")
                lines.append("")
        
        lines.extend(["---", "", "*Generated by OpenClaw Daily Info Collector V3*"])
        return "\n".join(lines)


def main():
    collector = DailyInfoCollectorV3()
    result = collector.collect_all()
    
    # 输出简要汇报
    print("\n" + "="*70)
    print("BRIEF_REPORT_START")
    print(json.dumps({
        "date": result["date"],
        "total_items": result["total_items"],
        "sources_success": result["successful_sources"],
        "sources_failed": result["failed_sources"],
        "categories": {k: v['count'] for k, v in result["summary"]["categories"].items()},
        "output_dir": collector.output_dir
    }, ensure_ascii=False, indent=2))
    print("BRIEF_REPORT_END")
    print("="*70)


if __name__ == "__main__":
    main()
