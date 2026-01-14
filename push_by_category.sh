#!/bin/bash
# -*- coding: utf-8 -*-
# 按类型分类推送到不同仓库

set -e

ORG="coretrusts"
PROJECT_DIR="/Users/mac/Documents/Project Manager/renew/AI Talk/AmDb"
GIT_BASE="git@github.com:$ORG"

cd "$PROJECT_DIR"

echo "=== 按类型分类推送到GitHub ==="
echo ""

# 函数：推送更新
push_update() {
    local repo=$1
    local temp_dir=$2
    local commit_msg=$3
    
    cd "$temp_dir"
    git init
    git remote add origin "$GIT_BASE/$repo.git" 2>/dev/null || \
        git remote set-url origin "$GIT_BASE/$repo.git"
    
    git add .
    if ! git diff --staged --quiet; then
        git commit -m "$commit_msg" 2>/dev/null || true
        git branch -M main
        git push -u origin main --force 2>&1 | tail -3
        echo "✓ $repo 更新成功"
    else
        echo "  $repo 无更改"
    fi
}

# 1. 文档仓库（只包含docs目录）
echo "=========================================="
echo "1. 更新文档仓库 (amdb-docs)"
echo "=========================================="

TEMP_DOCS=$(mktemp -d)
cp -r docs/* "$TEMP_DOCS/" 2>/dev/null || true
cat > "$TEMP_DOCS/README.md" << 'DOCS_EOF'
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
DOCS_EOF

push_update "amdb-docs" "$TEMP_DOCS" "Update: All documentation files - $(date +%Y-%m-%d)"
rm -rf "$TEMP_DOCS"

# 2. 创建脚本仓库（如果不存在）
echo ""
echo "=========================================="
echo "2. 更新脚本仓库 (amdb-scripts)"
echo "=========================================="

# 检查仓库是否存在
if ! git ls-remote "$GIT_BASE/amdb-scripts.git" &>/dev/null 2>&1; then
    echo "创建脚本仓库..."
    if [ -n "$GITHUB_TOKEN" ]; then
        curl -s -X POST \
            -H "Authorization: token $GITHUB_TOKEN" \
            -H "Accept: application/vnd.github.v3+json" \
            "https://api.github.com/orgs/$ORG/repos" \
            -d '{"name":"amdb-scripts","description":"AmDb - 构建、部署和维护脚本","private":false}' \
            > /dev/null && echo "✓ 仓库创建成功" || echo "⚠️  创建失败"
        sleep 2
    else
        echo "⚠️  需要GITHUB_TOKEN创建仓库，或手动创建: https://github.com/organizations/$ORG/repositories/new"
    fi
fi

TEMP_SCRIPTS=$(mktemp -d)

# 复制构建脚本
for f in build_*.sh build_*.bat Makefile rebuild_all.sh; do
    [ -f "$f" ] && cp "$f" "$TEMP_SCRIPTS/" 2>/dev/null || true
done

# 复制部署脚本
for f in deploy_*.sh deploy_*.md quick_push.sh final_deploy.sh create_and_deploy.sh; do
    [ -f "$f" ] && cp "$f" "$TEMP_SCRIPTS/" 2>/dev/null || true
done

# 复制安装脚本
for f in install.sh install.bat; do
    [ -f "$f" ] && cp "$f" "$TEMP_SCRIPTS/" 2>/dev/null || true
done

# 复制其他脚本
for f in setup.py setup_cython.py; do
    [ -f "$f" ] && cp "$f" "$TEMP_SCRIPTS/" 2>/dev/null || true
done

cat > "$TEMP_SCRIPTS/README.md" << 'SCRIPTS_EOF'
# AmDb 脚本工具

本仓库包含AmDb的构建、部署和维护脚本。

## 脚本分类

### 构建脚本
- `build_all_platforms.sh` - 跨平台构建脚本
- `build_distribution.sh` - 创建分发包
- `build_dmg.sh` - 创建macOS DMG
- `build_windows.bat` - Windows构建脚本
- `rebuild_all.sh` - 完整重建脚本
- `Makefile` - Make构建文件

### 部署脚本
- `deploy_direct.sh` - 直接SSH推送
- `deploy_simple.sh` - 简化部署脚本
- `deploy_ssh.sh` - SSH方式部署
- `final_deploy.sh` - 最终部署脚本
- `create_and_deploy.sh` - 创建并部署

### 安装脚本
- `install.sh` - Linux/macOS安装脚本
- `install.bat` - Windows安装脚本

### 构建配置
- `setup.py` - Python包配置
- `setup_cython.py` - Cython编译配置

## 使用

查看各个脚本的注释了解使用方法。

## 其他资源

- **源代码**: https://github.com/coretrusts/amdb
- **文档**: https://github.com/coretrusts/amdb-docs
- **发行版**: https://github.com/coretrusts/amdb-releases
SCRIPTS_EOF

if git ls-remote "$GIT_BASE/amdb-scripts.git" &>/dev/null 2>&1; then
    push_update "amdb-scripts" "$TEMP_SCRIPTS" "Update: All build and deployment scripts - $(date +%Y-%m-%d)"
else
    echo "⚠️  仓库不存在，跳过推送"
fi
rm -rf "$TEMP_SCRIPTS"

# 3. 多语言绑定仓库
echo ""
echo "=========================================="
echo "3. 更新多语言绑定仓库 (amdb-bindings)"
echo "=========================================="

# 检查仓库是否存在
if ! git ls-remote "$GIT_BASE/amdb-bindings.git" &>/dev/null 2>&1; then
    echo "创建绑定仓库..."
    if [ -n "$GITHUB_TOKEN" ]; then
        curl -s -X POST \
            -H "Authorization: token $GITHUB_TOKEN" \
            -H "Accept: application/vnd.github.v3+json" \
            "https://api.github.com/orgs/$ORG/repos" \
            -d '{"name":"amdb-bindings","description":"AmDb - 多语言开发绑定","private":false}' \
            > /dev/null && echo "✓ 仓库创建成功" || echo "⚠️  创建失败"
        sleep 2
    else
        echo "⚠️  需要GITHUB_TOKEN创建仓库，或手动创建: https://github.com/organizations/$ORG/repositories/new"
    fi
fi

TEMP_BINDINGS=$(mktemp -d)
cp -r bindings/* "$TEMP_BINDINGS/" 2>/dev/null || true

cat > "$TEMP_BINDINGS/README.md" << 'BINDINGS_EOF'
# AmDb 多语言绑定

本仓库包含AmDb数据库系统的多语言开发绑定。

## 支持的语言

- **C** (`c/`) - C语言绑定
- **C++** (`cpp/`) - C++语言绑定
- **Go** (`go/`) - Go语言绑定
- **Java** (`java/`) - Java语言绑定
- **Kotlin** (`kotlin/`) - Kotlin语言绑定
- **Node.js** (`nodejs/`) - JavaScript/Node.js绑定
- **PHP** (`php/`) - PHP语言绑定
- **Ruby** (`ruby/`) - Ruby语言绑定
- **Rust** (`rust/`) - Rust语言绑定
- **Swift** (`swift/`) - Swift语言绑定

## 使用

每个语言目录包含对应的绑定代码和使用示例。请参考各语言的README或示例代码。

## 其他资源

- **源代码**: https://github.com/coretrusts/amdb
- **文档**: https://github.com/coretrusts/amdb-docs
- **发行版**: https://github.com/coretrusts/amdb-releases
BINDINGS_EOF

if git ls-remote "$GIT_BASE/amdb-bindings.git" &>/dev/null 2>&1; then
    push_update "amdb-bindings" "$TEMP_BINDINGS" "Update: All language bindings - $(date +%Y-%m-%d)"
else
    echo "⚠️  仓库不存在，跳过推送"
fi
rm -rf "$TEMP_BINDINGS"

# 4. 更新源代码仓库（不包含bindings，因为bindings有独立仓库）
echo ""
echo "=========================================="
echo "4. 更新源代码仓库 (amdb) - 排除bindings"
echo "=========================================="

TEMP_SOURCE=$(mktemp -d)
mkdir -p "$TEMP_SOURCE/src" "$TEMP_SOURCE/tests" "$TEMP_SOURCE/examples"
cp -r src/* "$TEMP_SOURCE/src/" 2>/dev/null || true
cp -r tests/* "$TEMP_SOURCE/tests/" 2>/dev/null || true
cp -r examples/* "$TEMP_SOURCE/examples/" 2>/dev/null || true

# 复制配置文件（不包含bindings）
for f in setup.py setup_cython.py requirements.txt pyproject.toml README.md LICENSE .gitignore amdb-cli amdb_manager.py create_*.py verify_*.py; do
    [ -f "$f" ] && cp "$f" "$TEMP_SOURCE/" 2>/dev/null || true
done

# 更新README，说明bindings在独立仓库
cat > "$TEMP_SOURCE/README.md" << 'SOURCE_EOF'
# AmDb - 区块链优化数据库系统

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)

AmDb是一个专为区块链应用优化的高性能数据库系统。

## 仓库结构

本项目分为多个仓库：

- **amdb** (本仓库) - 核心源代码
- **amdb-docs** - 文档和API参考
- **amdb-bindings** - 多语言开发绑定
- **amdb-scripts** - 构建和部署脚本
- **amdb-releases** - 发行版和安装包

## 快速开始

### 安装

```bash
pip install -r requirements.txt
python3 setup.py install
```

### 使用

```python
from src.amdb.database import Database

db = Database('./data/mydb')
db.put(b'key1', b'value1')
value = db.get(b'key1')
```

## 多语言支持

多语言绑定请访问: https://github.com/coretrusts/amdb-bindings

## 文档

完整文档请访问: https://github.com/coretrusts/amdb-docs

## 发行版

预编译版本请访问: https://github.com/coretrusts/amdb-releases

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件
SOURCE_EOF

push_update "amdb" "$TEMP_SOURCE" "Update: Core source code (bindings moved to separate repo) - $(date +%Y-%m-%d)"
rm -rf "$TEMP_SOURCE"

echo ""
echo "=========================================="
echo "分类推送完成！"
echo "=========================================="
echo ""
echo "仓库地址:"
echo "  源代码: https://github.com/$ORG/amdb"
echo "  文档:   https://github.com/$ORG/amdb-docs"
echo "  绑定:   https://github.com/$ORG/amdb-bindings"
echo "  脚本:   https://github.com/$ORG/amdb-scripts"
echo "  发行版: https://github.com/$ORG/amdb-releases"
echo ""
