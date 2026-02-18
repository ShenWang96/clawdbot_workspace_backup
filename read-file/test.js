const { readMarkdownFile, validateFilePath, formatContentForDisplay } = require('./index.js');

// Test security validation
function testSecurityValidation() {
    console.log('🧪 测试安全验证...');
    
    // Test allowed paths
    const allowedTests = [
        '/root/.openclaw/workspace/docs/test.md',
        '/root/.openclaw/workspace/reports/test.md'
    ];
    
    allowedTests.forEach(testPath => {
        const result = validateFilePath(testPath);
        console.log(`✅ ${testPath}: ${result.valid ? '通过' : '失败'}`);
    });
    
    // Test disallowed paths
    const disallowedTests = [
        '/root/.openclaw/workspace/secret.md',
        '/root/.openclaw/workspace/../etc/passwd',
        '/root/.openclaw/workspace/scripts/test.txt',
        '/root/.openclaw/workspace/docs/test.txt'
    ];
    
    disallowedTests.forEach(testPath => {
        const result = validateFilePath(testPath);
        console.log(`❌ ${testPath}: ${result.valid ? '意外通过' : '正确拒绝 - ' + result.error}`);
    });
}

// Test file reading
async function testFileReading() {
    console.log('\n📖 测试文件读取...');
    
    // Test existing files
    const existingFiles = [
        '/root/.openclaw/workspace/docs/AGENT-COMMUNITY-NEWS.md',
        '/root/.openclaw/workspace/reports/agent-community-news/latest.md'
    ];
    
    for (const filePath of existingFiles) {
        const result = readMarkdownFile(filePath);
        if (result.success) {
            console.log(`✅ ${filePath}: 读取成功 (${Math.round(result.size / 1024)}KB)`);
        } else {
            console.log(`❌ ${filePath}: 读取失败 - ${result.message}`);
        }
    }
    
    // Test non-existing files
    const nonExistingFiles = [
        '/root/.openclaw/workspace/docs/nonexistent.md',
        '/root/.openclaw/workspace/reports/nonexistent.md'
    ];
    
    for (const filePath of nonExistingFiles) {
        const result = readMarkdownFile(filePath);
        if (!result.success) {
            console.log(`✅ ${filePath}: 正确拒绝 - ${result.message}`);
        }
    }
}

// Test formatting
function testFormatting() {
    console.log('\n🎨 测试格式化...');
    
    const mockSuccess = {
        success: true,
        content: '# 测试标题\n\n这是测试内容。',
        filePath: '/root/.openclaw/workspace/docs/test.md',
        size: 1024
    };
    
    const mockError = {
        success: false,
        message: '文件不存在'
    };
    
    console.log('成功格式化:');
    console.log(formatContentForDisplay(mockSuccess));
    
    console.log('\n错误格式化:');
    console.log(formatContentForDisplay(mockError));
}

// Run all tests
console.log('🚀 开始测试 Read File 技能...\n');

testSecurityValidation();
testFileReading();
testFormatting();

console.log('\n✅ 测试完成!');