const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');

// Configuration
const ALLOWED_BASE_DIRS = [
    '/root/.openclaw/workspace/docs',
    '/root/.openclaw/workspace/reports'
];
const MAX_FILE_SIZE = 10 * 1024; // 10KB (reduced from 50KB to prevent context overflow)
const MAX_DISPLAY_CONTENT = 5000; // 5KB max display content
const ALLOWED_EXTENSIONS = ['.md'];

/**
 * Safely read a markdown file from allowed directories
 * @param {string} filePath - Relative or absolute file path
 * @returns {Object} Result with status, content, and message
 */
function readMarkdownFile(filePath) {
    try {
        // Convert to absolute path
        let absolutePath;
        
        // If it's already an absolute path, use it directly
        if (path.isAbsolute(filePath)) {
            absolutePath = path.resolve(filePath);
        } else {
            // If relative path, resolve from workspace root
            absolutePath = path.resolve('/root/.openclaw/workspace', filePath);
        }
        
        // Security checks
        const validation = validateFilePath(absolutePath);
        if (!validation.valid) {
            return {
                success: false,
                message: validation.error
            };
        }
        
        // Check file exists
        if (!fs.existsSync(absolutePath)) {
            return {
                success: false,
                message: `文件不存在: ${filePath}`
            };
        }
        
        // Check file size
        const stats = fs.statSync(absolutePath);
        if (stats.size > MAX_FILE_SIZE) {
            return {
                success: false,
                message: `文件过大 (${Math.round(stats.size / 1024)}KB)，限制大小: ${Math.round(MAX_FILE_SIZE / 1024)}KB`
            };
        }
        
        // Read file content
        const content = fs.readFileSync(absolutePath, 'utf8');
        
        return {
            success: true,
            content: content,
            filePath: absolutePath,
            size: stats.size
        };
        
    } catch (error) {
        return {
            success: false,
            message: `读取文件时出错: ${error.message}`
        };
    }
}

/**
 * Validate file path for security
 * @param {string} absolutePath - Absolute file path
 * @returns {Object} Validation result
 */
function validateFilePath(absolutePath) {
    // Check if path contains dangerous characters
    if (absolutePath.includes('..') || absolutePath.includes('~')) {
        return {
            valid: false,
            error: '安全警告: 路径包含潜在危险字符'
        };
    }
    
    // Check if path is within allowed directories
    const isAllowed = ALLOWED_BASE_DIRS.some(baseDir => {
        return absolutePath.startsWith(baseDir);
    });
    
    if (!isAllowed) {
        return {
            valid: false,
            error: `安全警告: 只允许访问 docs 和 reports 目录`
        };
    }
    
    // Check file extension
    const ext = path.extname(absolutePath).toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
        return {
            valid: false,
            error: `安全警告: 只允许读取 .md 文件`
        };
    }
    
    return { valid: true };
}

/**
 * Format file content for display
 * @param {Object} result - File read result
 * @returns {string} Formatted content
 */
function formatContentForDisplay(result) {
    if (!result.success) {
        return `❌ ${result.message}`;
    }
    
    const { filePath, size, content } = result;
    const relativePath = path.relative('/root/.openclaw/workspace', filePath);
    
    let formatted = `📄 **文件**: ${relativePath}\n`;
    formatted += `📏 **大小**: ${Math.round(size / 1024)}KB\n`;
    
    // Truncate content if too large
    const truncated = content.length > MAX_DISPLAY_CONTENT;
    let displayContent = content;
    
    if (truncated) {
        displayContent = content.substring(0, MAX_DISPLAY_CONTENT) + '\n\n...\n\n**内容已截断 - 文件过大，只显示前部分内容**';
    }
    
    formatted += `\n---\n\n`;
    formatted += displayContent;
    
    // Add warning if content was truncated
    if (truncated) {
        formatted += `\n\n⚠️ **提示**: 文件内容较大，仅显示了前 ${MAX_DISPLAY_CONTENT} 字符。建议直接查看文件或缩小文件大小。`;
    }
    
    return formatted;
}

// Export functions for external use
module.exports = {
    readMarkdownFile,
    validateFilePath,
    formatContentForDisplay,
    ALLOWED_BASE_DIRS,
    MAX_FILE_SIZE,
    ALLOWED_EXTENSIONS
};