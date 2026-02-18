#!/bin/bash
# 智能体社区新闻搜集脚本
# 用途：搜集moltbot及类似AI agent社区的新闻动态

set -e

# 配置
WORKSPACE="/root/.openclaw/workspace"
REPORT_DIR="$WORKSPACE/reports/agent-community-news"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="$REPORT_DIR/news_${TIMESTAMP}.md"

# 创建报告目录
mkdir -p "$REPORT_DIR"

# 记录开始时间
START_TIME=$(date +%s)
DATE=$(date '+%Y-%m-%d %H:%M:%S')

echo "=== 智能体社区新闻报告 ===" > "$REPORT_FILE"
echo "生成时间: $DATE" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# 搜集新闻的函数
collect_news() {
    local topic="$1"
    echo "## $topic" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"

    # 使用web_search搜集相关新闻
    echo "正在搜集: $topic ..." >&2

    # 搜索关键词（主要关注最近一个月的）
    local keywords="$topic $(date '+%Y-%m')"

    # 调用web搜索（通过openclaw命令）
    openclaw agent run -q "搜集并总结关于$topic的最新新闻动态，包括：
1. 新功能或新玩法
2. 新的插件或工具
3. 广受讨论的issues或话题
4. 社区重要事件

请提供简洁的总结，每个点用简洁的语言描述，并附上相关链接（如果有）。搜索范围集中在最近1-2个月。" >> "$REPORT_FILE" 2>&1 || true

    echo "" >> "$REPORT_FILE"
}

# 搜集各个社区的新闻
echo "---" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# 主要关注的社区
collect_news "moltbot"
collect_news "Cloudflare Workers AI"
collect_news "LangChain"
collect_news "AutoGPT"
collect_news "OpenDevin"
collect_news "AutoGen"

# 添加总结部分
echo "## 总结" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "本报告由自动任务生成，涵盖上述智能体社区的最新动态。" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# 计算耗时
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
echo "报告生成耗时: ${DURATION}秒" >> "$REPORT_FILE"

# 输出报告路径
echo "✅ 报告已生成: $REPORT_FILE"

# 同时复制一份到最新
cp "$REPORT_FILE" "$REPORT_DIR/latest.md"
echo "📄 最新报告: $REPORT_DIR/latest.md"

# 输出摘要
echo ""
echo "=== 摘要 ===" >&2
head -n 30 "$REPORT_FILE"
