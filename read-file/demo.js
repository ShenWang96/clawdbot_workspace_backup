const { handleReadFileCommand, listAvailableFiles } = require('./commands.js');

// 模拟命令上下文
const mockContext = {
    user: 'demo-user',
    channel: 'telegram'
};

// 测试不同命令场景
console.log('🎭 演示 /read_file 命令使用场景\n');

// 1. 测试帮助信息
console.log('1️⃣ 无参数时的帮助信息:');
console.log(handleReadFileCommand(mockContext, ''));

console.log('\n' + '='.repeat(50) + '\n');

// 2. 测试文件列表
console.log('2️⃣ 可用文件列表:');
console.log(listAvailableFiles());

console.log('\n' + '='.repeat(50) + '\n');

// 3. 测试读取实际文件
console.log('3️⃣ 读取现有文件:');
console.log(handleReadFileCommand(mockContext, 'docs/AGENT-COMMUNITY-NEWS.md'));

console.log('\n' + '='.repeat(50) + '\n');

// 4. 测试读取不存在的文件
console.log('4️⃣ 读取不存在的文件:');
console.log(handleReadFileCommand(mockContext, 'docs/nonexistent.md'));

console.log('\n' + '='.repeat(50) + '\n');

// 5. 测试不安全的路径
console.log('5️⃣ 测试不安全路径:');
console.log(handleReadFileCommand(mockContext, '../etc/passwd'));

console.log('\n' + '='.repeat(50) + '\n');

// 6. 测试错误的文件扩展名
console.log('6️⃣ 测试非 MD 文件:');
console.log(handleReadFileCommand(mockContext, 'AGENTS.md'));

console.log('\n✅ 演示完成!');