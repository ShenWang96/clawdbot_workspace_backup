# clawdbot Workspace Backup

这是 clawdbot（OpenClaw AI 智能体）的工作空间备份仓库。

> **重要**：此仓库包含敏感配置信息，请勿泄露给他人。

---

## 📁 仓库结构

```
clawdbot_workspace_backup/
├── AGENTS.md              # 工作规则和约定
├── BOOTSTRAP.md          # 初始化引导（如存在）
├── HEARTBEAT.md           # 心跳任务列表
├── IDENTITY.md            # clawdbot 的身份信息
├── SOUL.md                # 核心个性和行为准则
├── TOOLS.md               # 本地工具笔记（SSH 别名、摄像头等）
└── USER.md                # 用户信息（姓名、时区等）

memory/                        # 记忆文件
├── token-logger-tracker.json      # Token 使用追踪器
├── token-usage.jsonl           # Token 使用日志
└── YYYY-MM-DD.md               # 每日笔记（如存在）

skills/                         # 技能目录
├── token-monitor/              # Token 监控 skill
│   ├── SKILL.md
│   └── scripts/
│       └── token_stats.py
├── token-stats/                # Token 统计 skill
│   ├── SKILL.md
│   └── scripts/
│       ├── token-stats-wrapper.sh
│       └── token_stats.py
└── token-stats-cron/            # Cron 提取 skill
    ├── SKILL.md
    └── scripts/
        ├── extract.py          # Python 提取器
        └── extract.sh          # Shell 包装器

.gitignore                      # Git 忽略文件（排除敏感信息和临时文件）
backup.sh                        # 自动备份脚本（每天凌晨 2 点执行）
```

---

## 🎯 仓库用途

### 自动备份
此仓库通过 cron 任务每天凌晨 2 点自动备份 workspace 到 GitHub，确保数据安全。

备份内容包括：
- 配置文件
- 记忆文件（MEMORY.md, daily notes）
- Skills（所有技能和脚本）
- 身份和规则（IDENTITY.md, SOUL.md, AGENTS.md）

### 灾难恢复

如果服务器数据丢失，可以从此仓库恢复 clawdbot 的完整状态。

---

## 🚀 快速开始

### 前置条件

1. **目标系统**：Linux（支持 Git）
2. **必需软件**：
   - Git 2.x 或更高版本
   - Python 3.x
   - OpenClaw 已安装

### 恢复步骤

#### 步骤 1：克隆仓库

```bash
# 选择恢复位置（建议使用新路径避免覆盖）
cd /root/.openclaw
git clone https://github.com/ShenWang96/clawdbot_workspace_backup.git clawdbot-restore
```

#### 步骤 2：备份现有 workspace（可选但推荐）

```bash
# 如果当前 workspace 存在，先备份
mv /root/.openclaw/workspace /root/.openclaw/workspace.backup.$(date +%Y%m%d_%H%M%S)
```

#### 步骤 3：复制恢复文件到 workspace

```bash
# 复制所有文件（不包括 .git）
cd clawdbot-restore
cp -r * /root/.openclaw/workspace/

# 保留 .git 配置（如需要）
cd /root/.openclaw/workspace
cp -r ../clawdbot-restore/.git .
```

#### 步骤 4：设置 Git 用户（重要！）

```bash
# 必须设置正确的 Git 用户名和邮箱
git config user.name "clawdbot"
git config user.email "clawdbot@openclaw.ai"
```

#### 步骤 5：配置 token-monitor Cron（需要手动设置）

恢复后，token-stats-cron 的 cron 任务需要重新设置：

```bash
# 1. 编辑 crontab
crontab -e

# 2. 添加每小时提取任务（移除旧的）
0 * * * * /root/.openclaw/workspace/skills/token-stats-cron/scripts/extract.sh extract >> /tmp/token-extract-cron.log 2>&1

# 3. 保存并退出
```

#### 步骤 6：验证恢复

```bash
# 检查重要文件
ls -la /root/.openclaw/workspace/AGENTS.md
ls -la /root/.openclaw/workspace/SOUL.md

# 检查 skills
ls -la /root/.openclaw/workspace/skills/

# 查看统计
/root/.local/bin/token-stats

# 重启 Gateway（自动加载新配置）
openclaw gateway restart
```

#### 步骤 7：清理备份仓库（可选）

```bash
# 删除恢复用的临时目录
rm -rf /root/.openclaw/clawdbot-restore
```

---

## ⚠️ 重要注意事项

### 敏感信息处理

备份仓库**已排除**敏感信息：
- ❌ **不包含**：`openclaw.json`（包含 appSecret、token 等密钥）
- ❌ **不包含**：session 文件（大量日志文件）

### Token Tracker 文件

**重要**：`memory/token-logger-tracker.json` 是增量更新的，恢复后从克隆的仓库中拉取会覆盖本地的追踪器。

**解决方案**：
- 拉取备份后，保留本地 tracker 文件
- 或者删除 tracker 文件，让系统重新生成

### Cron 任务

**重要**：crontab 配置存储在服务器本地，**不在备份仓库中**。

恢复后需要**手动重新设置** cron 任务（见步骤 5）。

### Workspace 路径

OpenClaw 的默认 workspace 路径：`/root/.openclaw/workspace`

恢复时**必须使用此路径**，否则：
- Gateway 无法找到配置文件
- Skills 无法正确加载
- Cron 任务无法执行

---

## 📊 Token 使用统计

恢复后可以通过以下命令查看统计：

```bash
# 查看完整统计
token-stats

# 查看最近 10 次对话
token-stats --recent 10

# 按日期分组
token-stats --group-by date

# 按模型分组
token-stats --group-by model

# JSON 输出
token-stats --format json
```

---

## 🔧 维护说明

### 自动备份

每天凌晨 2 点（UTC）自动运行：
```bash
/root/.openclaw/workspace/backup.sh
```

日志位于：`/tmp/backup-cron.log`

### 手动备份

随时可以手动触发备份：
```bash
cd /root/.openclaw/workspace
git add .
git commit -m "Manual backup: $(date '+%Y-%m-%d %H:%M:%S')"
git push origin master
```

---

## 🛡️ 故障排除

### Git 推送失败

如果推送失败，检查：

1. **Git 用户配置**
   ```bash
   git config user.name
   git config user.email
   ```

2. **远程仓库地址**
   ```bash
   git remote -v
   ```

3. **认证信息**
   ```bash
   # 检查 Token 是否正确配置
   cat ~/.git-credential-helper.sh  # 如存在
   ```

4. **网络连接**
   ```bash
   ping github.com
   ```

### Cron 任务未运行

检查 cron 配置：
```bash
crontab -l | grep backup
```

查看 cron 日志：
```bash
tail -50 /tmp/backup-cron.log
```

---

## 📞 技术支持

- **OpenClaw 文档**：https://docs.openclaw.ai
- **GitHub Issues**：https://github.com/openclaw/openclaw/issues
- **社区支持**：https://discord.gg/clawd

---

## 📝 版本历史

- v1.0 (2026-02-01) - 初始版本，包含完整的 workspace 备份
  - 配置 Git 备份
  - 添加自动备份脚本
  - 创建 .gitignore 排除敏感信息
  - 添加 README.md 和 MANUAL.md

---

**最后更新**：2026-02-01
