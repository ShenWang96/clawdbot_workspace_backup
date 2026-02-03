/**
 * Safe read file command with context overflow protection
 * This version is optimized to avoid context overflow errors
 */

const path = require('path');
const { readMarkdownFile, formatContentForDisplay, validateFilePath } = require('./index.js');

/**
 * Safe wrapper for read file command
 * @param {string} filePath - File path to read
 * @returns {string} Safe response
 */
function safeReadFile(filePath) {
    try {
        // First validate the path
        const validation = validateFilePath(path.resolve('/root/.openclaw/workspace', filePath));
        
        if (!validation.valid) {
            return `❌ 安全警告: ${validation.error}`;
        }
        
        // Read the file with additional size checks
        const result = readMarkdownFile(filePath);
        
        if (!result.success) {
            return `❌ ${result.message}`;
        }
        
        // If file is too large, provide a summary instead
        if (result.size > 8 * 1024) { // 8KB
            const relativePath = path.relative('/root/.openclaw/workspace', result.filePath);
            return `
📄 **文件**: ${relativePath}
📏 **大小**: ${Math.round(result.size / 1024)}KB
⚠️ **提示**: 文件过大 (${Math.round(result.size / 1024)}KB)，完整内容可能导致上下文溢出。

🔧 **建议**:
1. 请查看文件的前几行内容
2. 或者直接在文件系统中查看文件:
   \`cat ${result.filePath}\`
3. 或者指定要查看的具体章节
            `.trim();
        }
        
        // Format content with truncation
        return formatContentForDisplay(result);
        
    } catch (error) {
        return `❌ 读取文件时出错: ${error.message}`;
    }
}

// Test the safe version
if (require.main === module) {
    const testFiles = [
        'docs/AGENT-COMMUNITY-NEWS.md',
        'reports/agent-community-news/latest.md'
    ];
    
    console.log('🔒 测试安全读取功能...\n');
    
    testFiles.forEach(filePath => {
        console.log(`📖 尝试读取: ${filePath}`);
        console.log(safeReadFile(filePath));
        console.log('\n' + '='.repeat(50) + '\n');
    });
}

module.exports = { safeReadFile };