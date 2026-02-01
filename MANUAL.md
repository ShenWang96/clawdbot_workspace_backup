# clawdbot Workspace 备份恢复手册

本手册详细说明如何从 GitHub 仓库恢复 clawdbot 工作空间，以及恢复后需要的配置步骤。

---

## 📋 目录

### 第一步：恢复准备

1. **确认当前 workspace**
   - 当前 workspace 位置：`/root/.openclaw/workspace`
   - 检查是否需要备份

2. **准备恢复位置**
   ```bash
   # 创建临时目录用于恢复
   mkdir -p /root/.openclaw/workspace.backup.$(date +%Y%m%d_%H%M%S)
   ```

3. **停止 OpenClaw Gateway**
   ```bash
   # 防止恢复过程中有文件被写入
   openclaw gateway stop
   ```

---

## 📁 第一步：从 GitHub 克隆备份

### 拉取仓库

```bash
# 进入父目录
cd /root/.openclaw

# 克隆仓库
git clone https://github.com/ShenWang96/clawdbot_workspace_backup.git clawdbot-restore
```

### 验证克隆内容

```bash
# 查看目录结构
ls -la clawdbot-restore
```

---

## 🔧 第三步：恢复文件

### 方案 A：直接覆盖（推荐，如果确认数据丢失）

```bash
# 1. 备份现有 workspace
cd /root/.openclaw
mv workspace workspace.backup.$(date +%Y%m%d_%H%M%S)

# 2. 复制恢复文件
cp -r clawdbot-restore/* /root/.openclaw/workspace/

# 3. 验证关键文件
ls -la /root/.openclaw/workspace/AGENTS.md
ls -la /root/.openclaw/workspace/SOUL.md
ls -la /root/.openclaw/workspace/memory/token-logger-tracker.json
ls -la /root/.openclaw/workspace/skills/token-stats-cron/scripts/extract.sh
```

**⚠️ 重要警告：**

- **Token Tracker 文件会被覆盖**
  - 备份仓库中的 `memory/token-logger-tracker.json` 会覆盖本地的 tracker
  - 如果本地的 tracker 更新（记录了新的对话），覆盖后会导致丢失
  - **解决方案 A**：删除备份的 tracker 文件，恢复后让系统重新生成
  - **解决方案 B**：保留本地的 tracker 文件

### 方案 B：选择性恢复（推荐）

```bash
# 1. 进入克隆的仓库
cd clawdbot-restore

# 2. 查看文件列表
ls -la

# 3. 选择性复制文件
# 例如：只恢复配置和记忆，不覆盖 skills
cp AGENTS.md /root/.openclaw/workspace/
cp SOUL.md /root/.openclaw/workspace/
cp -r memory/ /root/.openclaw/workspace/memory/
```

---

## 🔄 第四步：恢复后配置

### 1. 重启 Gateway

```bash
# Gateway 会重新加载配置文件
openclaw gateway restart
```

### 2. 重新设置 token-stats Cron 任务

由于 crontab 配置存储在服务器本地文件中，**不会自动同步**。恢复后需要手动重新设置：

```bash
# 查看当前 crontab 配置
crontab -l | grep backup

# 如果显示，记录下来
crontab -l > /tmp/crontab-backup.txt
```

#### 重新添加 cron 任务

```bash
# 添加每小时提取任务
(crontab -l 2>/dev/null; echo "0 * * * * /root/.openclaw/workspace/skills/token-stats-cron/scripts/extract.sh extract >> /tmp/token-extract-cron.log 2>&1") | crontab -

# 验证
crontab -l | grep backup
```

### 3. 设置 Git 用户（如使用 HTTPS 推送）

如果使用 Token 方式，恢复后需要重新设置：

```bash
git config user.name "clawdbot"
git config user.email "clawdbot@openclaw.ai"
```

---

## 🎯 第五步：验证恢复

### 验证关键文件

```bash
# 1. 检查身份
cat /root/.openclaw/workspace/IDENTITY.md

# 2. 检查核心文件
ls -la /root/.openclaw/workspace/{SOUL.md,AGENTS.md,TOOLS.md}

# 3. 检查记忆
ls -la /root/.openclaw/workspace/memory/

# 4. 检查 skills
ls -la /root/.openclaw/workspace/skills/

# 5. 检查 token 统计
/root/.local/bin/token-stats
token-stats
```

### 验证 token 功能

```bash
# 手动触发一次提取
/root/.openclaw/workspace/skills/token-stats-cron/scripts/extract.sh extract

# 查看结果
token-stats --recent 5
```

---

## ⚠️ 常见问题和解决方案

### 问题 1：Token Tracker 覆盖

**现象：**恢复后 `token-stats` 统计从零开始或显示错误数据

**原因：**备份仓库中的 `memory/token-logger-tracker.json` 覆盖了本地的 tracker

**解决方案 A**：删除备份的 tracker 文件
```bash
rm clawdbot-restore/memory/token-logger-tracker.json
cd /root/.openclaw/workspace
/root/.openclaw/workspace/skills/token-stats-cron/scripts/extract.sh extract
```

**解决方案 B**：恢复后让系统重新生成
```bash
# 删除本地 tracker 文件，让系统从 session 文件重新生成
rm /root/.openclaw/workspace/memory/token-logger-tracker.json

# 系统会在下次对话时自动生成新的 tracker
```

### 问题 2：Cron 任务未生效

**现象：**每小时不会自动提取 token 统计

**原因：**crontab 配置存储在服务器本地文件中，不会自动同步

**解决方案：**重新添加 cron 任务（见第四步第 2 点）

```bash
# 查看当前配置
crontab -l

# 重新添加
(crontab -l 2>/dev/null; echo "0 * * * * /root/.openclaw/workspace/skills/token-stats-cron/scripts/extract.sh extract >> /tmp/token-extract-cron.log 2>&1") | crontab -

# 验证
crontab -l | grep extract.sh
```

### 问题 3：Gateway 配置未生效

**现象：**修改配置后 Gateway 未重新加载

**原因：**Gateway 需要重启才能加载新配置

**解决方案：**
```bash
openclaw gateway restart
```

### 问题 4：敏感信息丢失

**现象：**恢复后 `openclaw.json` 中的 appSecret 和 token 被清空

**原因：**备份仓库中 `.gitignore` 排除了这些文件

**解决方案：**
- 如果有备份记录，手动恢复这些信息
- 或者重新运行 `openclaw onboard` 或 `openclaw configure`

---

## 📊 恢复后检查清单

### 核心功能验证

- [ ] 身份信息正确（IDENTITY.md）
- [ ] 核心文件完整（SOUL.md, AGENTS.md, TOOLS.md, USER.md）
- [ ] 记忆目录存在（memory/）
- [ ] Token 数据存在（token-usage.jsonl）
- [ ] Tracker 文件存在（token-logger-tracker.json）
- [ ] Skills 目录完整（skills/）
- [ ] Token 统计命令可用（token-stats）
- [ ] 自动备份脚本可用（backup.sh）

### 配置验证

- [ ] Gateway 运行中（`openclaw gateway status`）
- [ ] 飞书通道连接正常
- [ ] crontab 配置正确（`crontab -l | grep extract.sh`）

### 功能测试

- [ ] 可以与 clawdbot 正常对话
- [ ] `token-stats` 命令正常输出
- [ ] 手动触发提取成功（`extract.sh extract`）
- [ ] 自动备份运行正常（backup.sh 或 cron）

---

## 🆘 快速恢复命令（一键脚本）

### 自动化恢复脚本

创建一个脚本，一键执行所有恢复步骤：

```bash
#!/bin/bash
# clawdbot 一键恢复脚本

set -e

REPO_URL="https://github.com/ShenWang96/clawdbot_workspace_backup.git"
WORKSPACE="/root/.openclaw/workspace"
BACKUP_DIR="/root/.openclaw/clawdbot-restore"

echo "=========================================="
echo "clawdbot Workspace 恢复工具"
echo "=========================================="
echo ""

echo "警告：此操作将覆盖当前 workspace！"
echo "建议：如果当前 workspace 正常，请先备份"
echo ""
read -p "确认恢复？(yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "已取消恢复"
    exit 0
fi

echo ""
echo "[1/6] 停止 Gateway..."
openclaw gateway stop
sleep 3

echo "[2/6] 拉取备份仓库..."
cd /root/.openclaw
git clone "$REPO_URL" clawdbot-restore

echo "[3/6] 备份当前 workspace..."
mv "$WORKSPACE" "$WORKSPACE.backup.$(date +%Y%m%d_%H%M%S)"

echo "[4/6] 恢复文件..."
cp -r "$BACKUP_DIR"/* "$WORKSPACE/"

echo "[5/6] 重启 Gateway..."
openclaw gateway restart

echo ""
echo "=========================================="
echo "恢复完成！"
echo "=========================================="
echo ""
echo "下一步："
echo "1. 检查关键文件：cat $WORKSPACE/IDENTITY.md"
echo "2. 验证统计：token-stats"
echo "3. 重新设置 cron（如需要）"
echo ""
echo "注意事项："
echo "- Token Tracker 文件可能需要删除或手动管理"
echo "- Cron 任务可能需要重新添加"
```

保存为：`/root/.openclaw/workspace/restore.sh`
```bash
cat > /root/.openclaw/workspace/restore.sh << 'EOF'
# 上面的脚本内容
EOF

chmod +x /root/.openclaw/workspace/restore.sh
```

---

## 📝 更新记录

每次恢复后，建议更新 `README.md` 的"版本历史"部分：

```markdown
## 版本历史

- v1.0 (2026-02-01) - 初始备份，包含完整的 workspace 结构和恢复手册
```

---

## 🛡️ 安全建议

1. **定期验证备份**
   - 每月检查一次 GitHub 仓库
   - 验证最新的备份成功推送

2. **测试恢复流程**
   - 在非生产环境先测试恢复流程
   - 确认所有功能正常

3. **Token Tracker 管理**
   - 定期备份 `token-logger-tracker.json`
   - 恢复后根据情况决定是否删除备份的 tracker

4. **敏感信息备份**
   - 不要将 `openclaw.json` 的敏感信息手动备份到 GitHub
   - 使用环境变量或单独的密钥管理系统

---

## 📞 联系与支持

- **OpenClaw 文档**：https://docs.openclaw.ai
- **GitHub Issues**：https://github.com/openclaw/openclaw/issues
- **社区支持**：https://discord.gg/clawd

---

**最后更新**：2026-02-01
