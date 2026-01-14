#!/bin/bash
# -*- coding: utf-8 -*-
# 创建仓库并部署（需要GitHub Token或GitHub CLI）

set -e

ORG="coretrusts"
REPO_SOURCE="amdb"
REPO_DOCS="amdb-docs"
REPO_RELEASES="amdb-releases"

PROJECT_DIR="/Users/mac/Documents/Project Manager/renew/AI Talk/AmDb"
GIT_BASE="git@github.com:$ORG"

cd "$PROJECT_DIR"

echo "=== AmDb 创建仓库并部署 ==="
echo ""

# 检查GitHub CLI
if command -v gh &> /dev/null && gh auth status &>/dev/null; then
    echo "使用GitHub CLI创建仓库..."
    gh repo create "coretrusts/$REPO_SOURCE" --public --description "AmDb - 区块链优化数据库系统（源代码）" --clone=false 2>&1 | grep -v "already exists" || true
    gh repo create "coretrusts/$REPO_DOCS" --public --description "AmDb - 文档和API参考" --clone=false 2>&1 | grep -v "already exists" || true
    gh repo create "coretrusts/$REPO_RELEASES" --public --description "AmDb - 发行版和可执行文件" --clone=false 2>&1 | grep -v "already exists" || true
    echo "✓ 仓库创建完成"
    sleep 2
else
    # 检查GitHub Token
    if [ -z "$GITHUB_TOKEN" ]; then
        echo "⚠️  未找到GitHub CLI或Token"
        echo ""
        echo "请选择以下方式之一："
        echo "  1. 安装GitHub CLI: brew install gh && gh auth login"
        echo "  2. 设置Token: export GITHUB_TOKEN=your_token"
        echo "  3. 手动创建仓库后运行: ./deploy_direct.sh"
        echo ""
        read -p "是否手动创建仓库？(y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
        echo "请访问: https://github.com/organizations/$ORG/repositories/new"
        echo "创建以下仓库："
        echo "  1. $REPO_SOURCE - AmDb - 区块链优化数据库系统（源代码）"
        echo "  2. $REPO_DOCS - AmDb - 文档和API参考"
        echo "  3. $REPO_RELEASES - AmDb - 发行版和可执行文件"
        read -p "创建完成后按Enter继续..."
    else
        echo "使用GitHub API创建仓库..."
        for repo in "$REPO_SOURCE:AmDb - 区块链优化数据库系统（源代码）" "$REPO_DOCS:AmDb - 文档和API参考" "$REPO_RELEASES:AmDb - 发行版和可执行文件"; do
            name=$(echo $repo | cut -d: -f1)
            desc=$(echo $repo | cut -d: -f2-)
            curl -X POST \
                -H "Authorization: token $GITHUB_TOKEN" \
                -H "Accept: application/vnd.github.v3+json" \
                "https://api.github.com/orgs/$ORG/repos" \
                -d "{\"name\":\"$name\",\"description\":\"$desc\",\"private\":false}" \
                2>/dev/null | grep -q "created_at" && echo "✓ $name 创建成功" || echo "⚠️  $name 可能已存在"
        done
        sleep 2
    fi
fi

# 现在推送
echo ""
echo "=== 开始推送 ==="
./deploy_direct.sh

