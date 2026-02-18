# Token Monitor 和 Token Stats 工具调研分析报告

## 🔍 调研时间
2026-02-03 11:32 GMT+8

## 📋 用户问题总结

### 主要问题
1. **token_monitor 好像根本不起作用**
2. **token_stats 统计缺失**：
   - 完全没有统计最近所有基于 Kimi 模型的对话记录
   - 2月2日的部分基于 GLM-4.5-Air 的请求记录缺失
3. **实现方式担忧**：
   - 当前是基于定时脚本从 session-log 里提取请求记录
   - 用户频繁使用 /new 创建多个 session，担心收集脚本是否能正确收集信息

## 🔧 当前系统架构分析

### Token 数据收集机制
根据代码分析，当前系统采用以下架构：

#### 1. 数据源
- **Session 文件**: `/root/.openclaw/agents/main/sessions/*.jsonl`
- **Token 缓存**: `/root/.openclaw/workspace/memory/token-usage.jsonl`

#### 2. 收集流程
```bash
# 定时脚本工作流程
Session文件 → token-logger钩子 → token-usage.jsonl → token-stats.py → 统计报告
```

#### 3. Token Monitor 技能
- **位置**: `/root/.openclaw/workspace/skills/token-monitor/`
- **脚本**: `scripts/token_stats.py`
- **功能**: 每次对话后自动提取并记录 token 使用情况

## 🐛 问题诊断

### 问题 1: Token Monitor 不工作的原因

通过分析发现：
1. **Hook 机制**: 系统依赖 `token-logger` hook 自动记录每个会话的 token 使用情况
2. **Hook 配置**: 需要在 OpenClaw 配置中启用 `internal.hooks.entries.token-logger`
3. **触发条件**: 仅在 session 结束时触发，如果异常中断可能丢失数据

### 问题 2: Token 统计缺失的原因

#### Kimi 模型缺失
- 当前数据显示只有 `glm-4.7` 模型被记录
- 检查配置发现只配置了 `zai:default` profile
- **原因**: Kimi 模型（moonshot）没有相应的认证配置

#### GLM-4.5-Air 部分缺失
- 检查 session 文件发现模型调用记录完整
- **原因**: token-logger 可能存在解析问题，或者某些情况下没有正确提取 token 数据

### 问题 3: Session 收集可靠性

#### /new 频繁使用的影响
- 每次创建新 session 都会生成新的 session 文件
- 定时脚本需要扫描所有 session 文件
- **风险点**: 
  - 竞争条件（多个 session 同时写入）
  - 大量 session 文件影响扫描性能
  - 部分未完成的 session 可能被遗漏

## 💡 改进建议

### 方案 1: 增强 Token Monitor (短期)

#### 1.1 验证和修复 Hook 机制
```bash
# 检查 hook 配置
openclaw config get hooks.internal.entries

# 确保 token-logger 已启用
{
  "hooks": {
    "internal": {
      "enabled": true,
      "entries": {
        "token-logger": {
          "enabled": true
        }
      }
    }
  }
}
```

#### 1.2 添加模型支持
```json
{
  "auth": {
    "profiles": {
      "moonshot:default": {
        "provider": "moonshot",
        "mode": "api_key"
      }
    }
  }
}
```

#### 1.3 增强错误处理
- 添加 token-logger 的调试日志
- 实现断点续传机制
- 增加数据完整性检查

### 方案 2: 重构收集系统 (中期)

#### 2.1 实时收集架构
```
Session事件 → 实时流处理 → 内存缓存 → 持久化存储 → 统计分析
```

#### 2.2 关键改进
- **实时处理**: 使用 hook 系统实时捕获 token 数据
- **增量更新**: 避免重复扫描，只处理新增数据
- **错误恢复**: 实现自动修复和数据补充机制

#### 2.3 监控和告警
- 添加数据完整性监控
- 实现异常情况自动告警
- 提供数据修复工具

### 方案 3: 优化 Session 管理 (长期)

#### 3.1 Session 文件管理
- 自动清理过期的 session 文件
- 实现会话归档机制
- 优化文件存储结构

#### 3.2 并发控制
- 实现文件锁机制
- 添加并发写入保护
- 优化大量文件的扫描性能

## 🚀 立即可执行的修复步骤

### 步骤 1: 诊断当前状态
```bash
# 检查 token-logger hook 状态
openclaw config get hooks.internal.entries

# 检查未处理的 session 文件
find /root/.openclaw/agents/main/sessions -name "*.jsonl" -newer /root/.openclaw/workspace/memory/token-usage.jsonl

# 手动运行一次收集脚本
python3 /root/.openclaw/workspace/skills/token-monitor/scripts/token_stats.py
```

### 步骤 2: 补充缺失的 Kimi 配置
```bash
# 添加 moonshot 认证配置
openclaw config patch '{
  "auth": {
    "profiles": {
      "moonshot:default": {
        "provider": "moonshot",
        "mode": "api_key"
      }
    }
  }
}'
```

### 步骤 3: 增强监控能力
- 添加 token 数据的实时监控
- 实现自动化的数据质量检查
- 提供手动数据修复工具

## 📊 预期改进效果

### 短期 (1-2周)
- ✅ 修复 token-logger 不工作的问题
- ✅ 补充 Kimi 模型的 token 统计
- ✅ 提高数据收集的可靠性

### 中期 (1个月)
- ✅ 实现实时数据收集
- ✅ 支持多种模型的完整统计
- ✅ 增强错误恢复能力

### 长期 (3个月)
- ✅ 完整的数据分析系统
- ✅ 自动化监控和告警
- ✅ 高性能的 Session 管理

## 🎯 建议优先级

1. **立即执行**: 诊断和修复 token-logger 问题
2. **本周内**: 添加 Kimi 模型支持
3. **下月内**: 重构收集系统架构
4. **季度内**: 优化 Session 管理机制

---

**结论**: 当前系统的基础架构是可行的，但存在一些配置和可靠性问题。通过分阶段改进，可以显著提升 token 统计的准确性和可靠性。

建议优先解决 token-logger 不工作的问题和补充 Kimi 模型配置，这将立即解决大部分用户的痛点问题。