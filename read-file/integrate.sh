#!/bin/bash

# Read File Skill Integration Script
# This script helps integrate the read-file skill into OpenClaw

echo "🔧 Read File Skill Integration Script"
echo "====================================="

# Function to display usage
usage() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  test        - Run all tests"
    echo "  demo        - Run demo"
    echo "  install     - Copy skill to OpenClaw skills directory"
    echo "  help        - Show this help message"
    exit 1
}

# Function to run tests
run_tests() {
    echo "🧪 Running tests..."
    node test.js
    echo ""
    echo "✅ Tests completed!"
}

# Function to run demo
run_demo() {
    echo "🎭 Running demo..."
    node demo.js
    echo ""
    echo "✅ Demo completed!"
}

# Function to install skill
install_skill() {
    echo "📦 Installing read-file skill..."
    
    # Check if OpenClaw skills directory exists
    if [ ! -d "/root/.openclaw/workspace/skills" ]; then
        echo "❌ Error: OpenClaw skills directory not found"
        exit 1
    fi
    
    # Create the skill directory
    cp -r "/root/.openclaw/workspace/read-file" "/root/.openclaw/workspace/skills/"
    
    if [ $? -eq 0 ]; then
        echo "✅ Skill installed successfully to: /root/.openclaw/workspace/skills/read-file"
        echo ""
        echo "📋 To use the skill:"
        echo "   • Restart OpenClaw gateway"
        echo "   • Use /read_file command"
    else
        echo "❌ Failed to install skill"
        exit 1
    fi
}

# Main script logic
case "${1:-help}" in
    test)
        run_tests
        ;;
    demo)
        run_demo
        ;;
    install)
        install_skill
        ;;
    help|--help|-h)
        usage
        ;;
    *)
        echo "❌ Unknown command: $1"
        usage
        ;;
esac