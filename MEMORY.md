# MEMORY.md - Long-term Memory

## 技能生态系统

### 网页抓取与反爬虫能力 (2026-02-24)

**关键发现**：在 ClawHub 上发现了专门的反爬虫技能，显著扩展了网页自动化能力。

**核心技能**：
- **stealth-browser**: 最推荐的反检测浏览器自动化技能
  - 支持 Cloudflare 绕过
  - CAPTCHA 自动解决（2Captcha、Anti-Captcha、CapSolver）
  - 会话持久化（Cookie + localStorage 保存）
  - 有头/无头模式自动切换
  - 特别适用于知乎等需要登录的网站

- **browser-automation-stealth**: 基于 Playwright 的反检测方案
- **playwright-scraper-skill**: 已在复杂网站（Discuss.com.hk）验证通过

**知乎登录方案**：
1. 使用有头模式打开知乎登录页
2. 用户手动完成登录（包括验证码）
3. 自动保存会话到 `~/.clawdbot/browser-sessions/`
4. 后续使用时自动加载，无需重新登录

**安全评估**：stealth-browser 虽被 VirusTotal 标记为可疑，但经代码审查确认安全，误判原因包括浏览器自动化功能、外部 API 集成等。

## 开发习惯

- 重要事件记录到 `memory/YYYY-MM-DD.md`
- 学习和决策总结到 `MEMORY.md`
- 技能使用方法记录到 `TOOLS.md`

## 持续问题跟踪

### GitHub 推送（已解决 ✅ 2026-03-30）
- **状态**: 已恢复正常
- **历史**: 2026-03-24 至 2026-03-26 期间持续失败
- **错误**: `could not read Username for 'https://github.com': No such device or address`
- **解决**: 2026-03-30 20:35 UTC 推送成功
- **影响**: workspace 备份、港股数据报告现在可以正常推送到 GitHub

### 港股新闻采集失败（待调查 ⚠️）
- **状态**: 仍存在
- **问题**: web_search API 返回空结果
- **影响**: 舆情分析、因果分析、预测模型无法更新
- **最后确认**: 2026-03-26
- **优先级**: 中
