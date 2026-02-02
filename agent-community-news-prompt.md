# 智能体社区新闻搜集任务

## 任务目标

搜集并总结智能体社区（特别是moltbot及相关社区）的最新新闻动态，生成报告并保存到本地。

## 关注的社区

1. moltbot - 个人AI助手
2. Cloudflare Workers AI - AI代理框架
3. LangChain - LLM应用开发框架
4. AutoGPT - 自主AI代理
5. OpenDevin - AI软件开发代理
6. AutoGen - 多智能体对话框架
7. CrewAI - 协作AI代理框架
8. BabyAGI - 任务执行代理
9. OpenAI Agents - OpenAI的代理框架

## 搜集内容

对于每个社区，搜集：
1. 新功能、新玩法或重要更新
2. 新的插件、工具或扩展
3. 广受讨论的issues、话题或争议
4. 社区重要事件或里程碑

## 报告格式

报告保存到：`/root/.openclaw/workspace/reports/agent-community-news/news_YYYYMMDD_HHMMSS.md`

同时复制一份到：`/root/.openclaw/workspace/reports/agent-community-news/latest.md`

**简要汇报格式：**
```
📰 智能体社区新闻搜集完成

【统计】
- 共搜集 X 个社区
- 发现 X 条重要新闻

【亮点】
• [社区1] 简要描述重要新闻（1-2个）
• [社区2] 简要描述重要新闻（1-2个）

详细报告已保存至：/root/.openclaw/workspace/reports/agent-community-news/latest.md
```

**详细报告格式：**
```markdown
# 智能体社区新闻报告

**生成时间:** YYYY-MM-DD HH:MM:SS
**报告编号:** YYYYMMDD_HHMMSS

---

## 社区名称

新闻摘要...

---

## 总结

本报告由 OpenClaw 自动新闻搜集系统生成。
```

## 执行步骤

1. 使用web_search搜索每个社区的最新新闻（关注最近1-2个月）
2. 整理和总结每个社区的关键信息
3. 生成Markdown格式的详细报告
4. 保存报告到指定路径
5. 创建最新报告的副本
6. **生成简要汇报**（包含统计信息、1-2个重要亮点、报告位置）

## 汇报要求

**简要汇报应该包含：**
- 搜集的社区数量
- 发现的重要新闻数量（粗略估计）
- 1-2个最重要的新闻亮点（各1-2句话）
- 详细报告的文件路径

**简要汇报的生成位置：**

**手动调用时（主会话）：**
- 在聊天中直接回复给用户

**cron任务调用时（cron会话）：**
- 使用 `message` 工具发送到 Telegram
- 参数：`channel=telegram`, `to=6480281338`（用户的 Telegram chat ID）
- 示例：
  ```bash
  message send --channel telegram --to 6480281338 --message "📰 智能体社区新闻搜集完成..."
  ```

**如何判断运行环境：**
- 检查当前会话是否以 `cron:` 开头
- 如果是 cron 会话，必须使用 message 工具发送简要汇报
- 如果是普通会话，直接在聊天中回复

注意：简要汇报要简洁明了，用emoji和分段提升可读性。

## 注意事项

- 使用中文总结
- 保持简洁明了
- 重要链接可以附上
- 如果某个社区没有最新动态，可以简略提及或跳过
