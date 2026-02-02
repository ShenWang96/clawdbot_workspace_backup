#!/bin/bash
# 手动触发智能体社区新闻搜集

echo "📰 正在触发智能体社区新闻搜集任务..."
echo "任务将在后台运行，完成后会报告结果。"

# 触发已配置的cron任务
openclaw cron run 9743a6d3-44c0-4588-a0f9-adad0f401ded

echo ""
echo "✅ 任务已触发！"
echo "📄 报告将保存到: /root/.openclaw/workspace/reports/agent-community-news/"
echo "📝 查看最新报告: cat /root/.openclaw/workspace/reports/agent-community-news/latest.md"
