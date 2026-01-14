#!/bin/bash
# -*- coding: utf-8 -*-
# GitHub部署脚本
# 将项目按类型部署到coretrusts组织下的不同仓库

set -e

ORG="coretrusts"
REPO_SOURCE="amdb"
REPO_DOCS="amdb-docs"
REPO_RELEASES="amdb-releases"

echo "=== AmDb GitHub部署脚本 ==="
echo ""

# 检查GitHub CLI是否安装
if ! command -v gh &> /dev/null; then
    echo "错误: 需要安装GitHub CLI (gh)"
    echo "安装方法: brew install gh"
    echo "或访问: https://cli.github.com/"
    exit 1
fi

# 检查是否已登录
if ! gh auth status &> /dev/null; then
    echo "请先登录GitHub:"
    gh auth login
fi

# 函数：创建仓库（如果不存在）
create_repo() {
    local repo_name=$1
    local description=$2
    local is_private=${3:-false}
    
    if gh repo view "$ORG/$repo_name" &> /dev/null; then
        echo "✓ 仓库 $ORG/$repo_name 已存在"
    else
        echo "创建仓库: $ORG/$repo_name"
        gh repo create "$ORG/$repo_name" \
            --description "$description" \
            --public \
            --clone=false
        echo "✓ 仓库创建成功"
    fi
}

# 函数：部署到仓库
deploy_to_repo() {
    local repo_name=$1
    local repo_path=$2
    local branch=${3:-main}
    
    echo ""
    echo "=== 部署到 $ORG/$repo_name ==="
    
    # 创建临时目录
    TEMP_DIR=$(mktemp -d)
    cd "$TEMP_DIR"
    
    # 克隆仓库（如果存在）
    if gh repo view "$ORG/$repo_name" &> /dev/null; then
        git clone "https://github.com/$ORG/$repo_name.git" . 2>/dev/null || true
    else
        git init
        git remote add origin "https://github.com/$ORG/$repo_name.git"
    fi
    
    # 复制文件
    echo "复制文件..."
    rsync -av --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' \
        "$repo_path/" .
    
    # 提交
    git add .
    if git diff --staged --quiet; then
        echo "  无更改"
    else
        git commit -m "Update: $(date '+%Y-%m-%d %H:%M:%S')" || true
        git branch -M "$branch"
        git push -u origin "$branch" || echo "  推送失败（可能需要手动推送）"
        echo "✓ 部署完成"
    fi
    
    cd - > /dev/null
    rm -rf "$TEMP_DIR"
}

# 主流程
echo "1. 创建仓库..."
create_repo "$REPO_SOURCE" "AmDb - 区块链优化数据库系统（源代码）"
create_repo "$REPO_DOCS" "AmDb - 文档和API参考"
create_repo "$REPO_RELEASES" "AmDb - 发行版和可执行文件"

echo ""
echo "2. 部署源代码..."
SOURCE_FILES=(
    "src/"
    "tests/"
    "examples/"
    "setup.py"
    "setup_cython.py"
    "requirements.txt"
    "pyproject.toml"
    "README.md"
    "LICENSE"
    ".gitignore"
    "amdb-cli"
    "amdb_manager.py"
    "create_*.py"
    "verify_*.py"
)

TEMP_SOURCE=$(mktemp -d)
cd "$(dirname "$0")"
for item in "${SOURCE_FILES[@]}"; do
    if [ -e "$item" ]; then
        cp -r "$item" "$TEMP_SOURCE/" 2>/dev/null || true
    fi
done
deploy_to_repo "$REPO_SOURCE" "$TEMP_SOURCE"
rm -rf "$TEMP_SOURCE"

echo ""
echo "3. 部署文档..."
TEMP_DOCS=$(mktemp -d)
cd "$(dirname "$0")"
if [ -d "docs" ]; then
    cp -r docs/* "$TEMP_DOCS/"
    deploy_to_repo "$REPO_DOCS" "$TEMP_DOCS"
fi
rm -rf "$TEMP_DOCS"

echo ""
echo "4. 部署发行版..."
TEMP_RELEASES=$(mktemp -d)
cd "$(dirname "$0")"
mkdir -p "$TEMP_RELEASES/dist"
if [ -d "dist" ]; then
    # 只复制发行包，不复制中间文件
    cp dist/*.tar.gz "$TEMP_RELEASES/dist/" 2>/dev/null || true
    cp dist/*.dmg "$TEMP_RELEASES/dist/" 2>/dev/null || true
    cp dist/*.zip "$TEMP_RELEASES/dist/" 2>/dev/null || true
    
    # 创建README
    cat > "$TEMP_RELEASES/README.md" << 'RELEASES_EOF'
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
2. 解压: `tar -xzf amdb-*.tar.gz`
3. 运行: `./amdb-cli` 或 `./amdb-server`

## 版本历史

查看 [CHANGELOG.md](CHANGELOG.md) 了解版本更新历史。
RELEASES_EOF
    
    deploy_to_repo "$REPO_RELEASES" "$TEMP_RELEASES"
fi
rm -rf "$TEMP_RELEASES"

echo ""
echo "=== 部署完成 ==="
echo ""
echo "仓库地址:"
echo "  源代码: https://github.com/$ORG/$REPO_SOURCE"
echo "  文档:   https://github.com/$ORG/$REPO_DOCS"
echo "  发行版: https://github.com/$ORG/$REPO_RELEASES"
echo ""

