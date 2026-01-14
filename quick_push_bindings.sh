#!/bin/bash
# -*- coding: utf-8 -*-
# 快速推送bindings到GitHub（假设仓库已创建）

set -e

cd "$(dirname "$0")/bindings"

echo "=== 推送 bindings 到 GitHub ==="
echo ""

# 检查是否在bindings目录
if [ ! -f "README.md" ]; then
    echo "✗ 错误: 请在项目根目录运行此脚本"
    exit 1
fi

# 初始化Git（如果需要）
if [ ! -d ".git" ]; then
    echo "初始化Git仓库..."
    git init
    git branch -M main
fi

# 配置远程仓库
git remote remove origin 2>/dev/null || true
git remote add origin git@github.com:coretrusts/amdb-bindings.git 2>/dev/null || \
    git remote set-url origin git@github.com:coretrusts/amdb-bindings.git

# 添加所有文件
echo "添加文件..."
git add .

# 提交
echo "提交更改..."
git commit -m "Update: All language bindings - $(date +%Y-%m-%d)" 2>/dev/null || \
    git commit -m "Initial commit: All language bindings - $(date +%Y-%m-%d)"

# 推送
echo "推送到GitHub..."
git push -u origin main --force

echo ""
echo "✓ 完成！"
echo "仓库地址: https://github.com/coretrusts/amdb-bindings"
