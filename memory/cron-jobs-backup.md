# 🔄 定时任务备份 - 系统重装恢复用
# 备份时间: 2026-02-18
# 注意: 系统重装后，读取此文件并重新创建cron任务

## 当前定时任务列表 (共3个)

---

### 任务 1: Token Stats 扫描

```json
{
  "name": "token-stats-scan",
  "enabled": true,
  "schedule": {
    "kind": "every",
    "everyMs": 1800000
  },
  "sessionTarget": "main",
  "payload": {
    "kind": "systemEvent",
    "text": "执行 token-stats 扫描任务 (静默模式): /root/.openclaw/workspace/skills/token-stats/scripts/scan.py --silent"
  }
}
```

**说明**: 
- 每30分钟自动扫描token使用统计
- 静默模式运行，不输出结果
- 用户主动发送 `/token_stats` 查看统计

**恢复命令**:
```bash
cron add --json '{
  "name": "token-stats-scan",
  "enabled": true,
  "schedule": {"kind": "every", "everyMs": 1800000},
  "sessionTarget": "main",
  "payload": {"kind": "systemEvent", "text": "执行 token-stats 扫描任务 (静默模式): /root/.openclaw/workspace/skills/token-stats/scripts/scan.py --silent"}
}'
```

---

### 任务 2: 港股基金经理-每日数据采集

```json
{
  "name": "港股基金经理-每日数据采集",
  "enabled": true,
  "schedule": {
    "kind": "cron",
    "expr": "30 16 * * 1-5",
    "tz": "Asia/Shanghai"
  },
  "sessionTarget": "isolated",
  "payload": {
    "kind": "agentTurn",
    "message": "执行港股基金经理每日数据采集和分析任务。\n\n任务步骤：\n1. 获取港股收盘价数据（28只核心股票，使用新浪财经实时数据）\n2. 搜索相关新闻和公告\n3. 分析涨跌原因（因果性分析）\n4. 验证历史预测\n5. 生成每日报告\n6. 更新dashboard.md\n7. 推送到GitHub\n\n具体操作：\n- 使用 /root/.openclaw/workspace/hk-fund-manager/scripts/collector.py 采集新浪实时股价数据\n- 使用 web_search 搜索当日港股新闻\n- 更新 /root/.openclaw/workspace/hk-fund-manager/data/daily/YYYY-MM-DD/ 目录\n- 更新 /root/.openclaw/workspace/hk-fund-manager/dashboard.md\n- 生成报告到 /root/.openclaw/workspace/hk-fund-manager/reports/YYYY-MM-DD.md\n- 执行 ./scripts/git_push.sh 推送到GitHub\n- 发送简要汇报到 Telegram (channel=telegram, to=6480281338)\n\n股价数据采集命令：\ncd /root/.openclaw/workspace/hk-fund-manager && python3 scripts/collector.py\n\n汇报内容格式：\n📈 港股日报 - YYYY-MM-DD\n\n【市场概览】\n- 恒指涨跌\n- 核心股票表现\n- 涨跌分布统计\n\n【重点事件】\n- 重要新闻/公告\n\n【预测更新】\n- 验证结果\n- 新增预测\n\n详细报告: https://github.com/ShenWang96/hk-fund-manager"
  }
}
```

**说明**:
- 周一至周五 16:30 (GMT+8) 执行
- 使用新浪财经API获取实时股价
- 覆盖28只港股
- 推送到GitHub并发送Telegram通知

**恢复命令**:
```bash
cron add --json '{
  "name": "港股基金经理-每日数据采集",
  "enabled": true,
  "schedule": {"kind": "cron", "expr": "30 16 * * 1-5", "tz": "Asia/Shanghai"},
  "sessionTarget": "isolated",
  "payload": {"kind": "agentTurn", "message": "执行港股基金经理每日数据采集和分析任务。\n\n任务步骤：\n1. 获取港股收盘价数据（28只核心股票，使用新浪财经实时数据）\n2. 搜索相关新闻和公告\n3. 分析涨跌原因（因果性分析）\n4. 验证历史预测\n5. 生成每日报告\n6. 更新dashboard.md\n7. 推送到GitHub\n\n具体操作：\n- 使用 /root/.openclaw/workspace/hk-fund-manager/scripts/collector.py 采集新浪实时股价数据\n- 使用 web_search 搜索当日港股新闻\n- 更新 /root/.openclaw/workspace/hk-fund-manager/data/daily/YYYY-MM-DD/ 目录\n- 更新 /root/.openclaw/workspace/hk-fund-manager/dashboard.md\n- 生成报告到 /root/.openclaw/workspace/hk-fund-manager/reports/YYYY-MM-DD.md\n- 执行 ./scripts/git_push.sh 推送到GitHub\n- 发送简要汇报到 Telegram (channel=telegram, to=6480281338)\n\n股价数据采集命令：\ncd /root/.openclaw/workspace/hk-fund-manager && python3 scripts/collector.py\n\n汇报内容格式：\n📈 港股日报 - YYYY-MM-DD\n\n【市场概览】\n- 恒指涨跌\n- 核心股票表现\n- 涨跌分布统计\n\n【重点事件】\n- 重要新闻/公告\n\n【预测更新】\n- 验证结果\n- 新增预测\n\n详细报告: https://github.com/ShenWang96/hk-fund-manager"}
}'
```

---

### 任务 3: 智能体社区新闻每日搜集

```json
{
  "name": "智能体社区新闻每日搜集",
  "enabled": true,
  "schedule": {
    "kind": "cron",
    "expr": "0 8 * * *",
    "tz": "Asia/Shanghai"
  },
  "sessionTarget": "isolated",
  "payload": {
    "kind": "agentTurn",
    "message": "搜集智能体社区最新新闻并生成报告。\n\n任务说明：\n1. 阅读 /root/.openclaw/workspace/agent-community-news-prompt.md 了解任务要求\n2. 按照要求搜集moltbot、Cloudflare Workers AI、LangChain、AutoGPT、OpenDevin、AutoGen、CrewAI、BabyAGI、OpenAI Agents等社区的最新新闻（最近1-2个月）\n3. 使用web_search工具搜集信息\n4. 整理总结并生成Markdown报告\n5. 保存报告到：/root/.openclaw/workspace/reports/agent-community-news/news_YYYYMMDD_HHMMSS.md\n6. 同时复制一份到：/root/.openclaw/workspace/reports/agent-community-news/latest.md\n7. 生成简要汇报（包含统计信息、1-2个重要亮点、报告位置）\n8. 使用 message 工具发送简要汇报到 Telegram（channel=telegram, to=6480281338）\n\n注意：简要汇报格式参考 agent-community-news-prompt.md 中的说明。"
  }
}
```

**说明**:
- 每天 08:00 (GMT+8) 执行
- 搜集9个AI智能体社区新闻
- 生成报告并发送到Telegram

**恢复命令**:
```bash
cron add --json '{
  "name": "智能体社区新闻每日搜集",
  "enabled": true,
  "schedule": {"kind": "cron", "expr": "0 8 * * *", "tz": "Asia/Shanghai"},
  "sessionTarget": "isolated",
  "payload": {"kind": "agentTurn", "message": "搜集智能体社区最新新闻并生成报告。\n\n任务说明：\n1. 阅读 /root/.openclaw/workspace/agent-community-news-prompt.md 了解任务要求\n2. 按照要求搜集moltbot、Cloudflare Workers AI、LangChain、AutoGPT、OpenDevin、AutoGen、CrewAI、BabyAGI、OpenAI Agents等社区的最新新闻（最近1-2个月）\n3. 使用web_search工具搜集信息\n4. 整理总结并生成Markdown报告\n5. 保存报告到：/root/.openclaw/workspace/reports/agent-community-news/news_YYYYMMDD_HHMMSS.md\n6. 同时复制一份到：/root/.openclaw/workspace/reports/agent-community-news/latest.md\n7. 生成简要汇报（包含统计信息、1-2个重要亮点、报告位置）\n8. 使用 message 工具发送简要汇报到 Telegram（channel=telegram, to=6480281338）\n\n注意：简要汇报格式参考 agent-community-news-prompt.md 中的说明。"}
}'
```

---

## 快速恢复脚本 (全部任务)

系统重装后，执行以下命令恢复所有定时任务：

```bash
# 1. Token Stats 扫描
cron add --json '{"name": "token-stats-scan", "enabled": true, "schedule": {"kind": "every", "everyMs": 1800000}, "sessionTarget": "main", "payload": {"kind": "systemEvent", "text": "执行 token-stats 扫描任务 (静默模式): /root/.openclaw/workspace/skills/token-stats/scripts/scan.py --silent"}}'

# 2. 港股基金经理-每日数据采集
cron add --json '{"name": "港股基金经理-每日数据采集", "enabled": true, "schedule": {"kind": "cron", "expr": "30 16 * * 1-5", "tz": "Asia/Shanghai"}, "sessionTarget": "isolated", "payload": {"kind": "agentTurn", "message": "执行港股基金经理每日数据采集和分析任务。\n\n任务步骤：\n1. 获取港股收盘价数据（28只核心股票，使用新浪财经实时数据）\n2. 搜索相关新闻和公告\n3. 分析涨跌原因（因果性分析）\n4. 验证历史预测\n5. 生成每日报告\n6. 更新dashboard.md\n7. 推送到GitHub\n\n具体操作：\n- 使用 /root/.openclaw/workspace/hk-fund-manager/scripts/collector.py 采集新浪实时股价数据\n- 使用 web_search 搜索当日港股新闻\n- 更新 /root/.openclaw/workspace/hk-fund-manager/data/daily/YYYY-MM-DD/ 目录\n- 更新 /root/.openclaw/workspace/hk-fund-manager/dashboard.md\n- 生成报告到 /root/.openclaw/workspace/hk-fund-manager/reports/YYYY-MM-DD.md\n- 执行 ./scripts/git_push.sh 推送到GitHub\n- 发送简要汇报到 Telegram (channel=telegram, to=6480281338)\n\n股价数据采集命令：\ncd /root/.openclaw/workspace/hk-fund-manager && python3 scripts/collector.py\n\n汇报内容格式：\n📈 港股日报 - YYYY-MM-DD\n\n【市场概览】\n- 恒指涨跌\n- 核心股票表现\n- 涨跌分布统计\n\n【重点事件】\n- 重要新闻/公告\n\n【预测更新】\n- 验证结果\n- 新增预测\n\n详细报告: https://github.com/ShenWang96/hk-fund-manager"}}'

# 3. 智能体社区新闻每日搜集
cron add --json '{"name": "智能体社区新闻每日搜集", "enabled": true, "schedule": {"kind": "cron", "expr": "0 8 * * *", "tz": "Asia/Shanghai"}, "sessionTarget": "isolated", "payload": {"kind": "agentTurn", "message": "搜集智能体社区最新新闻并生成报告。\n\n任务说明：\n1. 阅读 /root/.openclaw/workspace/agent-community-news-prompt.md 了解任务要求\n2. 按照要求搜集moltbot、Cloudflare Workers AI、LangChain、AutoGPT、OpenDevin、AutoGen、CrewAI、BabyAGI、OpenAI Agents等社区的最新新闻（最近1-2个月）\n3. 使用web_search工具搜集信息\n4. 整理总结并生成Markdown报告\n5. 保存报告到：/root/.openclaw/workspace/reports/agent-community-news/news_YYYYMMDD_HHMMSS.md\n6. 同时复制一份到：/root/.openclaw/workspace/reports/agent-community-news/latest.md\n7. 生成简要汇报（包含统计信息、1-2个重要亮点、报告位置）\n8. 使用 message 工具发送简要汇报到 Telegram（channel=telegram, to=6480281338）\n\n注意：简要汇报格式参考 agent-community-news-prompt.md 中的说明。"}}'

# 验证
cron list
```

---

## 任务摘要

| # | 任务名称 | 频率 | 目标 | 状态 |
|---|----------|------|------|------|
| 1 | Token Stats 扫描 | 每30分钟 | main | ✅ |
| 2 | 港股基金经理-每日数据采集 | 周一至周五 16:30 | isolated | ✅ |
| 3 | 智能体社区新闻每日搜集 | 每天 08:00 | isolated | ✅ |

---

*备份时间: 2026-02-18 13:46 GMT+8*
