# HEARTBEAT.md - 例行任务清单

## 定时任务 (Cron Jobs)

### 0. Workspace 每日自动备份 ⭐ NEW
| 项目 | 详情 |
|------|------|
| **时间** | 每天 02:00 (GMT+8) |
| **脚本** | `/root/.openclaw/workspace/backup.sh` |
| **日志** | `/tmp/workspace-backup.log` |
| **状态** | ✅ 已配置 |

**任务内容**:
- 自动检测 workspace 变更
- Git 提交并推送到 GitHub 私有仓库
- 保留完整历史记录
- 无变更时跳过执行

**查看日志**:
```bash
tail -f /tmp/workspace-backup.log
```

### 1. Token Stats 扫描
| 项目 | 详情 |
|------|------|
| **任务ID** | 0884a2cd-1a99-4599-bfa9-0b0eb5ba8cfb |
| **频率** | 每30分钟 |
| **目标** | main session |
| **模式** | 静默模式（无输出） |
| **状态** | ✅ 运行中 |

**查看统计**: 发送 `/token_stats` 命令查看完整统计

### 2. 智能体社区新闻每日搜集
| 项目 | 详情 |
|------|------|
| **任务ID** | 9743a6d3-44c0-4588-a0f9-adad0f401ded |
| **时间** | 每天 08:00 (GMT+8) |
| **目标** | isolated session |
| **输出** | reports/agent-community-news/ |
| **状态** | ✅ 运行中 |

### 3. 港股基金经理-每日数据采集 ⭐ NEW
| 项目 | 详情 |
|------|------|
| **任务ID** | f9598082-9f09-4d9c-a5ed-6e86f784e1ba |
| **时间** | 周一至周五 16:30 (GMT+8) |
| **目标** | isolated session |
| **输出** | hk-fund-manager/reports/ |
| **数据源** | 新浪财经 (秒级实时) |
| **状态** | ✅ 已配置 |
| **下次执行** | 下一个交易日 16:30 |

**任务内容**:
- 获取28只港股实时股价数据 (新浪财经API)
- 搜索相关新闻和公告
- 因果性分析（解释涨跌原因）
- 验证历史预测
- 生成每日报告
- 推送到GitHub私有仓库
- Telegram通知

**数据源更新 (2026-02-18)**:
- ✅ Yahoo Finance → **新浪财经** (延迟从15-20分钟降至秒级)
- ✅ 采集脚本: `python3 scripts/collector.py`

---

## 手动触发命令

```bash
# 港股数据采集
./scripts/git_push.sh "Daily update"

# 查看当前任务
cron list
```

---

*最后更新: 2026-02-18*

---

## 系统重装恢复

**定时任务备份**: `memory/cron-jobs-backup.md`

系统重装后，新实例应读取此文件并重新创建所有 cron 任务。

**快速恢复命令**:
```bash
cd /root/.openclaw/workspace
# 执行 memory/cron-jobs-backup.md 中的恢复脚本
```
