# 港股专用RSS源配置
# 更新日期: 2026-02-11
# 适配工具: rss-agent, news-intel

## ✅ 可用源 (测试通过)

### 国际财经
- **南华早报-港股** (SCMP Stocks)
  - URL: https://www.scmp.com/rss/318198/feed
  - 内容: 香港股市、市场动态、政策影响
  - 语言: 英文
  - 状态: ✅ 可用

- **Reuters财经**
  - URL: https://feeds.feedburner.com/reuters/businessNews
  - 内容: 全球财经新闻、股市动态
  - 语言: 英文
  - 状态: ✅ 可用

- **BBC财经**
  - URL: https://feeds.bbci.co.uk/news/business/rss.xml
  - 内容: 国际财经新闻
  - 语言: 英文
  - 状态: ✅ 可用

- **英为财情** (Investing.com)
  - URL: https://cn.investing.com/rss/news.rss
  - 内容: 全球股市、港股、A股资讯
  - 语言: 中文
  - 状态: ✅ 可用

## ⚠️ 需要自建RSSHub的源

以下源通过RSSHub官方实例被限制访问，建议自建RSSHub:

### 中文财经
- **雪球今日**
  - URL: https://rsshub.app/xueqiu/today
  - 内容: A股、港股、美股社区讨论
  - 语言: 中文
  - 状态: ⚠️ HTTP 403

- **东方财富港股**
  - URL: https://rsshub.app/eastmoney/search/%E6%B8%AF%E8%82%A1
  - 内容: 港股新闻、研报
  - 语言: 中文
  - 状态: ⚠️ HTTP 403

## ❌ 不可用的源

- **财华社港股**: https://www.finet.hk/rss.xml (404)
- **智通财经**: https://www.zhitongcaijing.com/feed (405)
- **阿斯达克英文**: https://www.aastocks.com/en/rss/news.xml (XML格式错误)
- **MarketWatch**: https://www.marketwatch.com/rss/marketwatch (403)

## 🔧 快速添加命令

```bash
# 使用 rss-agent 添加
python3 skills/rss-agent/scripts/rss.py add "https://www.scmp.com/rss/318198/feed" --name "南华早报-港股" --category "港股"
python3 skills/rss-agent/scripts/rss.py add "https://feeds.feedburner.com/reuters/businessNews" --name "Reuters财经" --category "港股"
python3 skills/rss-agent/scripts/rss.py add "https://feeds.bbci.co.uk/news/business/rss.xml" --name "BBC财经" --category "港股"
python3 skills/rss-agent/scripts/rss.py add "https://cn.investing.com/rss/news.rss" --name "英为财情" --category "港股"

# 使用 news-intel 添加
node skills/news-intel/scripts/rss.js add "南华早报" https://www.scmp.com/rss/318198/feed
node skills/news-intel/scripts/rss.js add "Reuters" https://feeds.feedburner.com/reuters/businessNews
```

## 📊 获取今日资讯

```bash
# rss-agent - 获取港股分类最新5条
python3 skills/rss-agent/scripts/rss.py digest -c "港股" --limit 5

# news-intel - 获取所有已保存源
node skills/news-intel/scripts/rss.js all 5
```

## 🏗️ 建议自建RSSHub

对于被限制的中文RSS源，建议自建RSSHub:

```bash
# Docker部署
 docker run -d --name rsshub -p 1200:1200 diygod/rsshub

# 然后使用本地RSSHub地址
# http://localhost:1200/xueqiu/today
# http://localhost:1200/eastmoney/search/港股
```

## 📝 维护建议

1. 定期检查RSS源健康状态:
   ```bash
   python3 skills/rss-agent/scripts/rss.py check
   ```

2. 移除失效源:
   ```bash
   python3 skills/rss-agent/scripts/rss.py remove "失效源名称"
   ```

3. 更新间隔建议:
   - 实时行情: 每5分钟
   - 新闻资讯: 每15分钟
   - 研报数据: 每60分钟

## 🎯 港股信息采集策略

### 数据源组合
| 类型 | 推荐源 | 频率 |
|-----|-------|-----|
| 市场快讯 | 南华早报 + Reuters | 实时 |
| 公司公告 | 港交所披露易 | 日更 |
| 研报数据 | 英为财情 | 日更 |
| 社区讨论 | 雪球 (需自建RSSHub) | 实时 |
| 宏观经济 | BBC财经 | 日更 |

### 自动化脚本
```bash
# 每小时更新港股资讯
cron add --name "HK-Stock-News" \
  --schedule "0 * * * *" \
  --payload '{"kind":"agentTurn","message":"获取港股RSS最新资讯并总结"}' \
  --target isolated
```
