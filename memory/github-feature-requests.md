# Feature Request Record

## 2026-02-03 提交

### Issue #7985: Support bypass-AI mode for custom commands to reduce token consumption
- **URL**: https://github.com/openclaw/openclaw/issues/7985
- **状态**: OPEN
- **创建时间**: 2026-02-03
- **内容**: 请求支持自定义命令绕过 AI 模型，直接执行以减少 token 消耗

### 背景
用户发现 `/token_stats`、`/token_stats_show` 等自定义命令每次都要经过 AI 会话，产生不必要的 token 消耗。希望像原生命令（`/status`、`/model`）一样直接执行。

### 相关 Issue
- #4280 - Plugin callback handler (bypass LLM for callbacks)
- #7533 - Gateway-level /switch command
- #7597 - Tool execution hook events

