#!/bin/bash
# -*- coding: utf-8 -*-
# 快速推送脚本 - 在GitHub仓库创建后使用

set -e

ORG="coretrusts"
PROJECT_DIR="/Users/mac/Documents/Project Manager/renew/AI Talk/AmDb"

cd "$PROJECT_DIR"

echo "=== AmDb 快速推送到GitHub ==="
echo ""

# 检查仓库是否存在
check_repo() {
    local repo=$1
    if curl -s -o /dev/null -w "%{http_code}" "https://github.com/$ORG/$repo" | grep -q "200"; then
        return 0
    else
        return 1
    fi
}

# 推送函数
push_repo() {
    local repo_name=$1
    local temp_dir=$2
    
    echo "推送 $repo_name..."
    
    cd "$temp_dir"
    git remote set-url origin "https://github.com/$ORG/$repo_name.git"
    
    if git push -u origin main 2>&1; then
        echo "✓ $repo_name 推送成功"
        return 0
    else
        echo "✗ $repo_name 推送失败"
        return 1
    fi
}

# 1. 源代码
echo "1. 检查源代码仓库..."
if check_repo "amdb"; then
    TEMP=$(mktemp -d)
    mkdir -p "$TEMP/src" "$TEMP/tests" "$TEMP/examples"
    cp -r src/* "$TEMP/src/" 2>/dev/null || true
    cp -r tests/* "$TEMP/tests/" 2>/dev/null || true
    cp -r examples/* "$TEMP/examples/" 2>/dev/null || true
    for f in setup.py setup_cython.py requirements.txt pyproject.toml README.md LICENSE .gitignore amdb-cli amdb_manager.py create_*.py verify_*.py; do
        [ -f "$f" ] && cp "$f" "$TEMP/" 2>/dev/null || true
    done
    cd "$TEMP"
    git init
    git add .
    git commit -m "Initial commit: $(date +%Y-%m-%d)" 2>/dev/null || true
    git branch -M main
    push_repo "amdb" "$TEMP"
    rm -rf "$TEMP"
else
    echo "⚠️  仓库 coretrusts/amdb 尚未创建"
fi

# 2. 文档
echo ""
echo "2. 检查文档仓库..."
if check_repo "amdb-docs"; then
    TEMP=$(mktemp -d)
    cp -r docs/* "$TEMP/" 2>/dev/null || true
    cat > "$TEMP/README.md" << 'EOF'
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
    cd "$TEMP"
    git init
    git add .
    git commit -m "Initial commit: $(date +%Y-%m-%d)" 2>/dev/null || true
    git branch -M main
    push_repo "amdb-docs" "$TEMP"
    rm -rf "$TEMP"
else
    echo "⚠️  仓库 coretrusts/amdb-docs 尚未创建"
fi

# 3. 发行版
echo ""
echo "3. 检查发行版仓库..."
if check_repo "amdb-releases"; then
    TEMP=$(mktemp -d)
    mkdir -p "$TEMP/dist"
    cp dist/*.tar.gz "$TEMP/dist/" 2>/dev/null || true
    cp dist/*.dmg "$TEMP/dist/" 2>/dev/null || true
    cat > "$TEMP/README.md" << 'EOF'
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
    cat > "$TEMP/CHANGELOG.md" << 'EOF'
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
    cd "$TEMP"
    git init
    git add .
    git commit -m "Initial release: v1.0.0" 2>/dev/null || true
    git branch -M main
    push_repo "amdb-releases" "$TEMP"
    rm -rf "$TEMP"
else
    echo "⚠️  仓库 coretrusts/amdb-releases 尚未创建"
fi

echo ""
echo "=== 完成 ==="
echo ""
echo "如果推送失败，请检查："
echo "  1. 仓库是否已在GitHub上创建"
echo "  2. Git认证配置是否正确"
echo "  3. 是否有推送权限"
echo ""
echo "仓库地址："
echo "  https://github.com/coretrusts/amdb"
echo "  https://github.com/coretrusts/amdb-docs"
echo "  https://github.com/coretrusts/amdb-releases"

