const { readMarkdownFile, formatContentForDisplay, ALLOWED_BASE_DIRS } = require('./index.js');

/**
 * Handle /read_file command
 * @param {Object} context - Command context
 * @param {string} args - Command arguments
 * @returns {string} Response message
 */
function handleReadFileCommand(context, args) {
    if (!args || args.trim() === '') {
        return `
📋 **使用说明**:
/read_file <文件路径>

**示例**:
/read_file docs/AGENT-COMMUNITY-NEWS.md
/read_file reports/agent-community-news/latest.md

**安全限制**:
• 只能访问 docs 和 reports 目录
• 只能读取 .md 文件
• 文件大小限制: 50KB
        `.trim();
    }
    
    const filePath = args.trim();
    
    // Log the access attempt (for security audit)
    console.log(`[READ_FILE] Attempt to access: ${filePath}`);
    
    // Read the file with security checks
    const result = readMarkdownFile(filePath);
    
    // Format and return the response
    return formatContentForDisplay(result);
}

/**
 * List available markdown files
 * @returns {string} Formatted list of available files
 */
function listAvailableFiles() {
    const fs = require('fs');
    const path = require('path');
    
    let fileList = '📁 **可用文件列表**:\n\n';
    
    ALLOWED_BASE_DIRS.forEach(baseDir => {
        const dirName = path.basename(baseDir);
        fileList += `**${dirName}/**:\n`;
        
        try {
            const files = fs.readdirSync(baseDir, { recursive: true });
            const mdFiles = files.filter(file => 
                file.endsWith('.md') && fs.statSync(path.join(baseDir, file)).isFile()
            );
            
            if (mdFiles.length > 0) {
                mdFiles.forEach(file => {
                    const fullPath = path.join(baseDir, file);
                    const stats = fs.statSync(fullPath);
                    const relativePath = path.relative('/root/.openclaw/workspace', fullPath);
                    fileList += `  • ${relativePath} (${Math.round(stats.size / 1024)}KB)\n`;
                });
            } else {
                fileList += `  无 .md 文件\n`;
            }
        } catch (error) {
            fileList += `  无法读取目录: ${error.message}\n`;
        }
        
        fileList += '\n';
    });
    
    return fileList;
}

module.exports = {
    handleReadFileCommand,
    listAvailableFiles
};