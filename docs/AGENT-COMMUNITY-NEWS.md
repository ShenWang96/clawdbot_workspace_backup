# 智能体社区新闻订阅系统

自动搜集并总结moltbot及类似AI agent社区的新闻动态。

## 功能

- 自动搜集多个智能体社区的最新新闻
- 生成结构化的Markdown报告
- 每日自动运行（北京时间每天早上8点）
- 支持手动一键触发（在Telegram中使用 `/news` 命令）
- 报告自动积累，可查看历史记录

## 使用方法

### 📱 在Telegram中使用

发送命令：
```
/news_agents
```

这会立即触发新闻搜集任务，任务在后台运行。完成后会通知你报告已生成。

### 🖥️ 命令行手动触发

```bash
/root/.openclaw/workspace/scripts/run-news-collection.sh
```

### 查看最新报告

```bash
cat /root/.openclaw/workspace/reports/agent-community-news/latest.md
```

### 查看所有历史报告

```bash
ls -lth /root/.openclaw/workspace/reports/agent-community-news/
```

## 自动运行

系统已配置为每天北京时间早上8点自动运行，无需手动干预。

## 报告位置

- 最新报告：`/root/.openclaw/workspace/reports/agent-community-news/latest.md`
- 历史报告：`/root/.openclaw/workspace/reports/agent-community-news/news_YYYYMMDD_HHMMSS.md`
- 任务配置：`/root/.openclaw/workspace/agent-community-news-prompt.md`

## Telegram命令配置

Telegram bot已注册自定义命令：
- `/news_agents` - 搜集智能体社区最新新闻

当你在Telegram中输入 `/news_agents` 时，系统会自动触发新闻搜集任务。

## 工作原理（手动触发）

1. 用户在Telegram中发送 `/news_agents` 命令
2. 主agent识别命令，直接在当前session中执行任务（同步模式，不使用spawn）
3. 阅读任务配置文件
4. 使用web_search工具搜索各社区最新新闻
5. AI整理和总结关键信息
6. 生成Markdown格式报告
7. 保存到指定目录并创建最新副本
8. 告知用户报告位置和关键信息

**同步执行的优势：**
- 避免并发API调用导致的429错误
- 只有一个进程在运行，不会触发并发限制
- 用户需要等待（5-10分钟），但任务更稳定

## Cron任务信息

- 任务ID：`9743a6d3-44c0-4588-a0f9-adad0f401ded`
- 任务名称：智能体社区新闻每日搜集
- 运行时间：每天 08:00 (Asia/Shanghai)
- 状态：已启用

## Cron管理命令

查看所有cron任务：
```bash
openclaw cron list
```

查看任务运行历史：
```bash
openclaw cron runs 9743a6d3-44c0-4588-a0f9-adad0f401ded
```

手动运行任务：
```bash
openclaw cron run 9743a6d3-44c0-4588-a0f9-adad0f401ded
```

## 注意事项

- 报告内容由AI自动生成，可能需要人工审核
- 搜索结果依赖网络和搜索引擎的实时数据
- 建议定期查看报告质量，必要时调整任务配置

## 并发控制（避免429错误）

当前配置下，`/news_agents` 采用**同步执行模式**，避免与子agent并发调用API导致429错误。

如果想进一步控制并发，可以：

### 选项1：降低子agent并发数
```bash
# 编辑配置，将子agent并发数降为1
openclaw config set agents.defaults.subagents.maxConcurrent 1
```

### 选项2：降级主agent并发数
```bash
openclaw config set agents.defaults.maxConcurrent 2
```

### 选项3：使用不同的API profile
如果有多个API key，可以为不同的agent配置不同的profile：
```json
{
  "auth": {
    "profiles": {
      "zai:default": {
        "provider": "zai",
        "mode": "api_key",
        "apiKey": "key1"
      },
      "zai:subagents": {
        "provider": "zai",
        "mode": "api_key",
        "apiKey": "key2"
      }
    }
  }
}
```
