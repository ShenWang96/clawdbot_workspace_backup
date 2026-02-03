# Read File Skill

一个用于安全读取工作区中 `docs` 和 `reports` 目录下 Markdown 文件的 OpenClaw 技能。

## 功能特性

- ✅ **安全限制**: 仅允许访问 `docs` 和 `reports` 目录
- ✅ **文件类型验证**: 只读取 `.md` 文件
- ✅ **大小限制**: 最大 50KB 防止内存问题
- ✅ **路径保护**: 防止目录遍历攻击
- ✅ **格式化输出**: 优雅的显示格式

## 使用方法

```
/read_file <文件路径>
```

## 示例

```bash
# 读取文档
/read_file docs/AGENT-COMMUNITY-NEWS.md

# 读取报告
/read_file reports/agent-community-news/latest.md
```

## 安全特性

1. **路径验证**: 确保文件在允许的目录内
2. **扩展名检查**: 只允许 `.md` 文件
3. **大小限制**: 防止读取超大文件
4. **错误处理**: 完善的错误提示和异常处理

## 开发

```bash
cd read-file
npm install
npm test
```

## 技术架构

- `index.js`: 核心安全文件读取逻辑
- `commands.js`: 命令处理和格式化
- `SKILL.md`: 技能说明文档
- `package.json`: 包配置文件