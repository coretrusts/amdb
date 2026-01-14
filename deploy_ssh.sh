#!/bin/bash
# -*- coding: utf-8 -*-
# 使用SSH方式部署到GitHub

set -e

ORG="coretrusts"
REPO_SOURCE="amdb"
REPO_DOCS="amdb-docs"
REPO_RELEASES="amdb-releases"

PROJECT_DIR="/Users/mac/Documents/Project Manager/renew/AI Talk/AmDb"

# 使用SSH URL
GIT_BASE="git@github.com:$ORG"

echo "=== AmDb GitHub部署（SSH方式）==="
echo ""

cd "$PROJECT_DIR"

# 函数：创建仓库（通过GitHub API）
create_repo_api() {
    local repo_name=$1
    local description=$2
    
    if [ -z "$GITHUB_TOKEN" ]; then
        echo "⚠️  未设置GITHUB_TOKEN，跳过API创建"
        return 1
    fi
    
    echo "通过API创建仓库: $repo_name"
    curl -X POST \
        -H "Authorization: token $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        "https://api.github.com/orgs/$ORG/repos" \
        -d "{\"name\":\"$repo_name\",\"description\":\"$description\",\"private\":false}" \
        2>/dev/null | grep -q "created_at" && return 0 || return 1
}

# 函数：检查仓库是否存在
repo_exists() {
    local repo_name=$1
    ssh -o ConnectTimeout=5 git@github.com 2>&1 | grep -q "successfully authenticated" || true
    git ls-remote "$GIT_BASE/$repo_name.git" &>/dev/null && return 0 || return 1
}

# 函数：初始化并推送仓库
init_and_push_ssh() {
    local repo_name=$1
    local description=$2
    local temp_dir=$3
    
    echo ""
    echo "=== 处理 $repo_name ==="
    
    # 检查仓库是否存在
    if ! repo_exists "$repo_name"; then
        echo "仓库不存在，尝试创建..."
        if create_repo_api "$repo_name" "$description"; then
            echo "✓ 仓库创建成功"
            sleep 2  # 等待GitHub同步
        else
            echo "⚠️  无法自动创建仓库，请手动创建："
            echo "   https://github.com/organizations/$ORG/repositories/new"
            echo "   仓库名: $repo_name"
            echo "   描述: $description"
            echo "   可见性: Public"
            read -p "创建完成后按Enter继续..."
        fi
    else
        echo "✓ 仓库已存在"
    fi
    
    # 创建临时目录
    rm -rf "$temp_dir"
    mkdir -p "$temp_dir"
    cd "$temp_dir"
    
    # 初始化Git
    git init
    git remote add origin "$GIT_BASE/$repo_name.git" 2>/dev/null || \
        git remote set-url origin "$GIT_BASE/$repo_name.git"
    
    echo "✓ Git仓库初始化完成"
    
    # 添加文件
    git add .
    if git diff --staged --quiet; then
        echo "  无更改"
    else
        git commit -m "Initial commit: $(date +%Y-%m-%d)" || true
        git branch -M main
        
        echo "推送到: $GIT_BASE/$repo_name.git"
        if git push -u origin main 2>&1; then
            echo "✓ 推送成功"
        else
            echo "⚠️  推送失败，请检查："
            echo "  1. SSH密钥是否正确配置"
            echo "  2. 是否有仓库的写入权限"
            echo "  3. 仓库是否已创建"
            return 1
        fi
    fi
    
    cd "$PROJECT_DIR"
}

# 1. 源代码仓库
echo "=========================================="
echo "步骤 1/3: 准备源代码仓库"
echo "=========================================="

TEMP_SOURCE=$(mktemp -d)
cd "$PROJECT_DIR"

echo "复制源代码文件..."
mkdir -p "$TEMP_SOURCE/src"
cp -r src/* "$TEMP_SOURCE/src/" 2>/dev/null || true

mkdir -p "$TEMP_SOURCE/tests"
cp -r tests/* "$TEMP_SOURCE/tests/" 2>/dev/null || true

mkdir -p "$TEMP_SOURCE/examples"
cp -r examples/* "$TEMP_SOURCE/examples/" 2>/dev/null || true

# 复制配置文件
for file in setup.py setup_cython.py requirements.txt pyproject.toml README.md LICENSE .gitignore; do
    if [ -f "$file" ]; then
        cp "$file" "$TEMP_SOURCE/"
    fi
done

# 复制脚本文件
for file in amdb-cli amdb_manager.py; do
    if [ -f "$file" ]; then
        cp "$file" "$TEMP_SOURCE/" 2>/dev/null || true
    fi
done

# 复制创建脚本
for file in create_*.py verify_*.py; do
    if [ -f "$file" ]; then
        cp "$file" "$TEMP_SOURCE/" 2>/dev/null || true
    fi
done

init_and_push_ssh "$REPO_SOURCE" "AmDb - 区块链优化数据库系统（源代码）" "$TEMP_SOURCE"
rm -rf "$TEMP_SOURCE"

# 2. 文档仓库
echo ""
echo "=========================================="
echo "步骤 2/3: 准备文档仓库"
echo "=========================================="

TEMP_DOCS=$(mktemp -d)
cd "$PROJECT_DIR"

echo "复制文档文件..."
if [ -d "docs" ]; then
    cp -r docs/* "$TEMP_DOCS/"
    
    # 创建README
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
fi

init_and_push_ssh "$REPO_DOCS" "AmDb - 文档和API参考" "$TEMP_DOCS"
rm -rf "$TEMP_DOCS"

# 3. 发行版仓库
echo ""
echo "=========================================="
echo "步骤 3/3: 准备发行版仓库"
echo "=========================================="

TEMP_RELEASES=$(mktemp -d)
cd "$PROJECT_DIR"

echo "复制发行包..."
mkdir -p "$TEMP_RELEASES/dist"

# 复制发行包
if [ -d "dist" ]; then
    cp dist/*.tar.gz "$TEMP_RELEASES/dist/" 2>/dev/null || true
    cp dist/*.dmg "$TEMP_RELEASES/dist/" 2>/dev/null || true
    cp dist/*.zip "$TEMP_RELEASES/dist/" 2>/dev/null || true
fi

# 创建README
cat > "$TEMP_RELEASES/README.md" << 'EOF'
# AmDb 发行版

本仓库包含AmDb的编译好的可执行文件和安装包。

## 下载

### macOS
- **DMG安装包**: [AmDb-1.0.0-macOS.dmg](dist/AmDb-1.0.0-macOS.dmg)
- **压缩包**: [amdb-1.0.0-darwin-x86_64.tar.gz](dist/amdb-1.0.0-darwin-x86_64.tar.gz)

### Linux
- **压缩包**: [amdb-1.0.0-linux-x86_64.tar.gz](dist/amdb-1.0.0-linux-x86_64.tar.gz)

### Windows
- **ZIP包**: [amdb-1.0.0-windows-x86_64.zip](dist/amdb-1.0.0-windows-x86_64.zip)

## 使用

### macOS DMG
1. 下载并双击DMG文件
2. 将AmDb拖拽到Applications文件夹
3. 在启动台找到AmDb

### 压缩包
1. 下载对应平台的压缩包
2. 解压: `tar -xzf amdb-*.tar.gz` (Linux/macOS) 或 `unzip amdb-*.zip` (Windows)
3. 运行: `./amdb-cli` 或 `./amdb-server`

## 版本历史

查看 [CHANGELOG.md](CHANGELOG.md) 了解版本更新历史。

## 其他资源

- **源代码**: https://github.com/coretrusts/amdb
- **文档**: https://github.com/coretrusts/amdb-docs
EOF

# 创建CHANGELOG
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

### 性能
- 顺序写入: ~17,751 记录/秒
- 批量写入: 支持大规模数据

### 文档
- 网络架构文档
- 集成指南
- 构建和打包指南
- API参考
EOF

init_and_push_ssh "$REPO_RELEASES" "AmDb - 发行版和可执行文件" "$TEMP_RELEASES"
rm -rf "$TEMP_RELEASES"

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

