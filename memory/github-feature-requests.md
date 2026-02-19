# Feature Request Record

## 2026-02-03 提交

### Issue #7985: Support bypass-AI mode for custom commands to reduce token consumption
- **URL**: https://github.com/openclaw/openclaw/issues/7985
- **状态**: OPEN
- **创建时间**: 2026-02-03
- **内容**: 请求支持自定义命令绕过 AI 模型，直接执行以减少 token 消耗

### 背景
用户发现 `/token_stats`、`/token_stats_show` 等自定义命令每次都要经过 AI 会话，产生不必要的 token 消耗。希望像原生命令（`/status`、`/model`）一样直接执行。

### 进展 (2026-02-19)
- **PR #20785**: feat: add bypass-model support for skill commands
  - 状态: OPEN
  - 作者: @MichaelC001
  - 功能: 添加 `bypass-model: true` 和 `exec-command: "..."` frontmatter 支持
  - 示例:
    ```yaml
    ---
    name: ip
    description: Get public IP address
    user-invocable: true
    bypass-model: true
    exec-command: "curl -s ipinfo.io/ip"
    ---
    ```
  - 优势: 零 token 消耗、即时响应、100% 准确率
  - 向后兼容: 默认不变，需要显式设置 `bypass-model: true`

### 相关 Issue
- #4280 - Plugin callback handler (bypass LLM for callbacks)
- #7533 - Gateway-level /switch command
- #7597 - Tool execution hook events

