#!/bin/bash
# -*- coding: utf-8 -*-
# 推送脚本到amdb-scripts仓库

set -e

cd "$(dirname "$0")"

echo "=========================================="
echo "推送脚本到 amdb-scripts 仓库"
echo "=========================================="
echo ""

# 检查仓库是否存在
if ! git ls-remote git@github.com:coretrusts/amdb-scripts.git &>/dev/null 2>&1; then
    echo "⚠️  仓库不存在，请先创建仓库："
    echo "   访问: https://github.com/organizations/coretrusts/repositories/new"
    echo "   名称: amdb-scripts"
    echo "   描述: AmDb - 构建、部署和维护脚本"
    echo "   可见性: Public"
    echo ""
    read -p "按回车键继续（确认已创建仓库）..."
fi

TEMP=$(mktemp -d)

echo "准备文件..."

# 复制所有脚本文件
for f in build_*.sh build_*.bat Makefile rebuild_all.sh deploy_*.sh deploy_*.md quick_push*.sh final_deploy.sh create_and_deploy.sh create_bindings_repo.sh quick_push_bindings.sh install.sh install.bat setup.py setup_cython.py; do
    [ -f "$f" ] && cp "$f" "$TEMP/" 2>/dev/null || true
done

# 创建README
cat > "$TEMP/README.md" << 'SCRIPTS_EOF'
# AmDb 脚本工具

本仓库包含AmDb的构建、部署和维护脚本。

## 脚本分类

### 构建脚本
- `build_all_platforms.sh` - 跨平台构建脚本（Linux/macOS）
- `build_all_platforms.bat` - Windows构建脚本
- `build_distribution.sh` - 创建分发包
- `build_dmg.sh` - 创建macOS DMG安装包
- `build_windows.bat` - Windows构建脚本
- `build_complete_package.sh` - 完整打包脚本
- `rebuild_all.sh` - 完整重建脚本
- `Makefile` - Make构建文件

### 部署脚本
- `deploy_direct.sh` - 直接SSH推送
- `deploy_simple.sh` - 简化部署脚本
- `deploy_ssh.sh` - SSH方式部署
- `final_deploy.sh` - 最终部署脚本
- `create_and_deploy.sh` - 创建并部署
- `quick_push.sh` - 快速推送脚本
- `create_bindings_repo.sh` - 创建bindings仓库脚本
- `quick_push_bindings.sh` - 快速推送bindings脚本

### 安装脚本
- `install.sh` - Linux/macOS安装脚本
- `install.bat` - Windows安装脚本

### 构建配置
- `setup.py` - Python包配置
- `setup_cython.py` - Cython编译配置

## 使用

### 构建

```bash
# 编译原生扩展
make native
# 或
python3 setup_cython.py build_ext --inplace

# 打包CLI和GUI
make cli gui
# 或
./build_all_platforms.sh

# 创建分发包
./build_distribution.sh
```

### 部署

```bash
# 快速推送（假设仓库已存在）
./quick_push.sh

# 完整部署（包括创建仓库）
./final_deploy.sh
```

### 安装

```bash
# Linux/macOS
./install.sh

# Windows
install.bat
```

## 其他资源

- **源代码**: https://github.com/coretrusts/amdb
- **文档**: https://github.com/coretrusts/amdb-docs
- **发行版**: https://github.com/coretrusts/amdb-releases
- **多语言绑定**: https://github.com/coretrusts/amdb-bindings
SCRIPTS_EOF

cd "$TEMP"
echo "初始化Git仓库..."
git init
git remote add origin git@github.com:coretrusts/amdb-scripts.git 2>/dev/null || \
    git remote set-url origin git@github.com:coretrusts/amdb-scripts.git

echo "添加文件..."
git add .

echo "提交更改..."
git commit -m "Initial commit: All build and deployment scripts - $(date +%Y-%m-%d)" 2>/dev/null || \
    git commit -m "Initial commit: All scripts - $(date +%Y-%m-%d)"

echo "设置主分支..."
git branch -M main

echo "推送到GitHub..."
git push -u origin main --force

cd - > /dev/null
rm -rf "$TEMP"

echo ""
echo "=========================================="
echo "✓ 完成！"
echo "=========================================="
echo ""
echo "仓库地址: https://github.com/coretrusts/amdb-scripts"
echo ""
