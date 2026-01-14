#!/bin/bash
# -*- coding: utf-8 -*-
# 最终部署脚本 - 自动创建仓库并推送

set -e

ORG="coretrusts"
REPO_SOURCE="amdb"
REPO_DOCS="amdb-docs"
REPO_RELEASES="amdb-releases"

PROJECT_DIR="/Users/mac/Documents/Project Manager/renew/AI Talk/AmDb"
GIT_BASE="git@github.com:$ORG"

cd "$PROJECT_DIR"

echo "=== AmDb 最终部署 ==="
echo ""

# 检查并创建仓库
create_repo_if_needed() {
    local repo=$1
    local desc=$2
    
    # 检查仓库是否存在
    if git ls-remote "$GIT_BASE/$repo.git" &>/dev/null 2>&1; then
        echo "✓ 仓库 $repo 已存在"
        return 0
    fi
    
    echo "创建仓库: $repo"
    
    # 方法1: 使用GitHub CLI
    if command -v gh &> /dev/null && gh auth status &>/dev/null 2>&1; then
        gh repo create "coretrusts/$repo" --public --description "$desc" --clone=false 2>&1 | grep -v "already exists" || true
        sleep 2
        return 0
    fi
    
    # 方法2: 使用GitHub API (需要token)
    if [ -n "$GITHUB_TOKEN" ]; then
        response=$(curl -s -X POST \
            -H "Authorization: token $GITHUB_TOKEN" \
            -H "Accept: application/vnd.github.v3+json" \
            "https://api.github.com/orgs/$ORG/repos" \
            -d "{\"name\":\"$repo\",\"description\":\"$desc\",\"private\":false}" 2>/dev/null)
        
        if echo "$response" | grep -q "created_at"; then
            echo "✓ 仓库创建成功"
            sleep 2
            return 0
        elif echo "$response" | grep -q "already exists"; then
            echo "✓ 仓库已存在"
            return 0
        fi
    fi
    
    # 方法3: 提示手动创建
    echo "⚠️  无法自动创建仓库"
    echo "请手动创建: https://github.com/organizations/$ORG/repositories/new"
    echo "  仓库名: $repo"
    echo "  描述: $desc"
    echo "  可见性: Public"
    read -p "创建完成后按Enter继续..."
    return 0
}

# 推送函数
push_repo() {
    local repo=$1
    local temp_dir=$2
    
    echo ""
    echo "=== 推送 $repo ==="
    
    cd "$temp_dir"
    git init
    git remote add origin "$GIT_BASE/$repo.git" 2>/dev/null || \
        git remote set-url origin "$GIT_BASE/$repo.git"
    
    git add .
    git commit -m "Initial commit: $(date +%Y-%m-%d)" 2>/dev/null || true
    git branch -M main
    
    echo "推送到: $GIT_BASE/$repo.git"
    if git push -u origin main 2>&1; then
        echo "✓ $repo 推送成功！"
        return 0
    else
        echo "✗ $repo 推送失败"
        return 1
    fi
}

# 1. 创建并推送源代码
echo "步骤 1/3: 源代码仓库"
create_repo_if_needed "$REPO_SOURCE" "AmDb - 区块链优化数据库系统（源代码）"

TEMP1=$(mktemp -d)
mkdir -p "$TEMP1/src" "$TEMP1/tests" "$TEMP1/examples"
cp -r src/* "$TEMP1/src/" 2>/dev/null || true
cp -r tests/* "$TEMP1/tests/" 2>/dev/null || true
cp -r examples/* "$TEMP1/examples/" 2>/dev/null || true
for f in setup.py setup_cython.py requirements.txt pyproject.toml README.md LICENSE .gitignore amdb-cli amdb_manager.py create_*.py verify_*.py; do
    [ -f "$f" ] && cp "$f" "$TEMP1/" 2>/dev/null || true
done
push_repo "$REPO_SOURCE" "$TEMP1"
rm -rf "$TEMP1"

# 2. 创建并推送文档
echo ""
echo "步骤 2/3: 文档仓库"
create_repo_if_needed "$REPO_DOCS" "AmDb - 文档和API参考"

TEMP2=$(mktemp -d)
cp -r docs/* "$TEMP2/" 2>/dev/null || true
cat > "$TEMP2/README.md" << 'EOF'
# AmDb 文档

本仓库包含AmDb数据库系统的完整文档。

## 文档索引

- [网络架构](NETWORK_ARCHITECTURE.md) - 服务器-客户端架构说明
- [集成指南](INTEGRATION_GUIDE.md) - 如何在项目中使用AmDb
- [构建和打包](BUILD_AND_PACKAGE.md) - 编译和打包指南
- [远程操作](REMOTE_OPERATIONS.md) - 远程操作支持说明
- [删除功能](DELETE_FEATURES.md) - 删除功能说明

## 快速开始

查看 [集成指南](INTEGRATION_GUIDE.md) 了解如何在自己的项目中使用AmDb。

## 其他资源

- **源代码**: https://github.com/coretrusts/amdb
- **发行版**: https://github.com/coretrusts/amdb-releases
EOF
push_repo "$REPO_DOCS" "$TEMP2"
rm -rf "$TEMP2"

# 3. 创建并推送发行版
echo ""
echo "步骤 3/3: 发行版仓库"
create_repo_if_needed "$REPO_RELEASES" "AmDb - 发行版和可执行文件"

TEMP3=$(mktemp -d)
mkdir -p "$TEMP3/dist"
cp dist/*.tar.gz "$TEMP3/dist/" 2>/dev/null || true
cp dist/*.dmg "$TEMP3/dist/" 2>/dev/null || true
cat > "$TEMP3/README.md" << 'EOF'
# AmDb 发行版

本仓库包含AmDb的编译好的可执行文件和安装包。

## 下载

### macOS
- **DMG安装包**: [AmDb-1.0.0-macOS.dmg](dist/AmDb-1.0.0-macOS.dmg)
- **压缩包**: [amdb-1.0.0-darwin-x86_64.tar.gz](dist/amdb-1.0.0-darwin-x86_64.tar.gz)

## 使用

### macOS DMG
1. 下载并双击DMG文件
2. 将AmDb拖拽到Applications文件夹
3. 在启动台找到AmDb

### 压缩包
1. 下载对应平台的压缩包
2. 解压: `tar -xzf amdb-*.tar.gz`
3. 运行: `./amdb-cli` 或 `./amdb-server`

## 其他资源

- **源代码**: https://github.com/coretrusts/amdb
- **文档**: https://github.com/coretrusts/amdb-docs
EOF
cat > "$TEMP3/CHANGELOG.md" << 'EOF'
# 更新日志

## 1.0.0 (2026-01-13)

### 新增功能
- ✅ 完整的数据库系统实现
- ✅ LSM Tree存储引擎
- ✅ Merkle Tree数据完整性验证
- ✅ 版本管理系统
- ✅ 网络服务器和客户端
- ✅ CLI命令行工具
- ✅ GUI图形界面管理器
- ✅ 多数据库支持
- ✅ 远程操作支持（统计信息、配置管理）
- ✅ 跨平台打包（macOS、Linux、Windows）
EOF
push_repo "$REPO_RELEASES" "$TEMP3"
rm -rf "$TEMP3"

echo ""
echo "=========================================="
echo "部署完成！"
echo "=========================================="
echo ""
echo "仓库地址:"
echo "  源代码: https://github.com/$ORG/$REPO_SOURCE"
echo "  文档:   https://github.com/$ORG/$REPO_DOCS"
echo "  发行版: https://github.com/$ORG/$REPO_RELEASES"
echo ""

