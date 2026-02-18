#!/bin/bash
# 手动运行智能体社区新闻搜集

echo "📰 正在启动智能体社区新闻搜集任务..."

# 使用spawn直接运行新闻搜集agent
openclaw agent spawn \
    --task "搜集智能体社区最新新闻并生成报告。

任务说明：
1. 阅读 /root/.openclaw/workspace/agent-community-news-prompt.md 了解任务要求
2. 按照要求搜集moltbot、Cloudflare Workers AI、LangChain、AutoGPT、OpenDevin、AutoGen、CrewAI、BabyAGI、OpenAI Agents等社区的最新新闻（最近1-2个月）
3. 使用web_search工具搜集信息
4. 整理总结并生成Markdown报告
5. 保存报告到：/root/.openclaw/workspace/reports/agent-community-news/news_\$(date +%Y%m%d_%H%M%S).md
6. 同时复制一份到：/root/.openclaw/workspace/reports/agent-community-news/latest.md

完成后，简要报告收集到的关键新闻数量和报告位置。" \
    --label "news-collector-manual" \
    --cleanup delete

echo ""
echo "✅ 任务已提交！任务将在后台独立运行。"
echo "📄 报告将保存到: /root/.openclaw/workspace/reports/agent-community-news/"
echo "📝 查看最新报告: cat /root/.openclaw/workspace/reports/agent-community-news/latest.md"
