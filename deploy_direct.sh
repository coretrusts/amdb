#!/bin/bash
# -*- coding: utf-8 -*-
# 直接使用SSH推送（假设仓库已存在或通过其他方式创建）

set -e

ORG="coretrusts"
REPO_SOURCE="amdb"
REPO_DOCS="amdb-docs"
REPO_RELEASES="amdb-releases"

PROJECT_DIR="/Users/mac/Documents/Project Manager/renew/AI Talk/AmDb"
GIT_BASE="git@github.com:$ORG"

cd "$PROJECT_DIR"

echo "=== AmDb 直接SSH推送 ==="
echo ""

# 函数：推送仓库
push_repo_ssh() {
    local repo_name=$1
    local temp_dir=$2
    
    echo "=== 推送 $repo_name ==="
    
    cd "$temp_dir"
    git init
    git remote add origin "$GIT_BASE/$repo_name.git" 2>/dev/null || \
        git remote set-url origin "$GIT_BASE/$repo_name.git"
    
    git add .
    git commit -m "Initial commit: $(date +%Y-%m-%d)" 2>/dev/null || true
    git branch -M main
    
    echo "推送到: $GIT_BASE/$repo_name.git"
    if git push -u origin main 2>&1; then
        echo "✓ $repo_name 推送成功"
        return 0
    else
        echo "✗ $repo_name 推送失败（仓库可能不存在）"
        return 1
    fi
}

# 1. 源代码
TEMP_SOURCE=$(mktemp -d)
mkdir -p "$TEMP_SOURCE/src" "$TEMP_SOURCE/tests" "$TEMP_SOURCE/examples"
cp -r src/* "$TEMP_SOURCE/src/" 2>/dev/null || true
cp -r tests/* "$TEMP_SOURCE/tests/" 2>/dev/null || true
cp -r examples/* "$TEMP_SOURCE/examples/" 2>/dev/null || true
for f in setup.py setup_cython.py requirements.txt pyproject.toml README.md LICENSE .gitignore amdb-cli amdb_manager.py create_*.py verify_*.py; do
    [ -f "$f" ] && cp "$f" "$TEMP_SOURCE/" 2>/dev/null || true
done
push_repo_ssh "$REPO_SOURCE" "$TEMP_SOURCE"
rm -rf "$TEMP_SOURCE"

# 2. 文档
TEMP_DOCS=$(mktemp -d)
cp -r docs/* "$TEMP_DOCS/" 2>/dev/null || true
cat > "$TEMP_DOCS/README.md" << 'EOF'
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
push_repo_ssh "$REPO_DOCS" "$TEMP_DOCS"
rm -rf "$TEMP_DOCS"

# 3. 发行版
TEMP_RELEASES=$(mktemp -d)
mkdir -p "$TEMP_RELEASES/dist"
cp dist/*.tar.gz "$TEMP_RELEASES/dist/" 2>/dev/null || true
cp dist/*.dmg "$TEMP_RELEASES/dist/" 2>/dev/null || true
cat > "$TEMP_RELEASES/README.md" << 'EOF'
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
cat > "$TEMP_RELEASES/CHANGELOG.md" << 'EOF'
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
push_repo_ssh "$REPO_RELEASES" "$TEMP_RELEASES"
rm -rf "$TEMP_RELEASES"

echo ""
echo "=== 完成 ==="

