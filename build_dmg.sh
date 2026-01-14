#!/bin/bash
# 创建macOS DMG安装包

set -e

echo "=================================================================================="
echo "创建macOS DMG安装包"
echo "=================================================================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 检查是否在macOS上
if [[ "$(uname)" != "Darwin" ]]; then
    echo -e "${RED}错误: 此脚本只能在macOS上运行${NC}"
    exit 1
fi

# 获取版本号
VERSION=$(python3 -c "import sys; sys.path.insert(0, 'src'); from amdb import __version__; print(__version__)" 2>/dev/null || echo "1.0.0")
APP_NAME="AmDb"
DMG_NAME="${APP_NAME}-${VERSION}-macOS"

echo "版本: $VERSION"
echo "DMG名称: ${DMG_NAME}.dmg"
echo ""

# 创建临时目录
TEMP_DIR=$(mktemp -d)
DMG_DIR="$TEMP_DIR/${DMG_NAME}"
mkdir -p "$DMG_DIR"

echo "1. 准备DMG内容..."

# 复制分发包内容
if [ -d "dist/amdb-${VERSION}-darwin-x86_64" ]; then
    cp -r "dist/amdb-${VERSION}-darwin-x86_64"/* "$DMG_DIR/"
elif [ -d "dist/amdb-${VERSION}-darwin-arm64" ]; then
    cp -r "dist/amdb-${VERSION}-darwin-arm64"/* "$DMG_DIR/"
else
    echo -e "${YELLOW}警告: 未找到分发包，使用当前构建${NC}"
    # 创建基本结构
    mkdir -p "$DMG_DIR/src" "$DMG_DIR/lib" "$DMG_DIR/config"
    cp -r src/* "$DMG_DIR/src/" 2>/dev/null || true
    cp amdb.ini "$DMG_DIR/config/" 2>/dev/null || true
fi

# 复制可执行文件
if [ -d "dist/darwin_x86_64" ]; then
    mkdir -p "$DMG_DIR/Applications"
    cp dist/darwin_x86_64/amdb-server "$DMG_DIR/" 2>/dev/null || true
    cp dist/darwin_x86_64/amdb-cli "$DMG_DIR/" 2>/dev/null || true
    cp dist/darwin_x86_64/amdb-manager "$DMG_DIR/" 2>/dev/null || true
    # 确保可执行权限
    chmod +x "$DMG_DIR/amdb-server" 2>/dev/null || true
    chmod +x "$DMG_DIR/amdb-cli" 2>/dev/null || true
    chmod +x "$DMG_DIR/amdb-manager" 2>/dev/null || true
fi

# 创建Applications链接
ln -s /Applications "$DMG_DIR/Applications"

# 创建README
cat > "$DMG_DIR/README.txt" << EOF
AmDb 数据库系统 - macOS安装包
版本: $VERSION

安装说明:
==========

方式1: 拖拽安装
  1. 将 AmDb 拖拽到 Applications 文件夹
  2. 在启动台或应用程序中找到 AmDb
  3. 双击运行

方式2: 命令行安装
  1. 打开终端
  2. 运行: ./install.sh

快速开始:
==========
1. 启动服务器: ./amdb-server
2. 使用CLI: ./amdb-cli
3. 使用GUI: ./amdb-manager

更多信息请参考 README.md
EOF

echo "2. 创建DMG镜像..."

# 创建DMG
DMG_PATH="dist/${DMG_NAME}.dmg"
rm -f "$DMG_PATH"

# 使用hdiutil创建DMG
hdiutil create -volname "$APP_NAME" \
    -srcfolder "$DMG_DIR" \
    -ov -format UDZO \
    "$DMG_PATH"

# 清理临时目录
rm -rf "$TEMP_DIR"

echo ""
echo -e "${GREEN}=================================================================================="
echo "DMG安装包创建完成！"
echo "==================================================================================${NC}"
echo ""
echo "DMG文件: $DMG_PATH"
echo "大小: $(du -sh "$DMG_PATH" | awk '{print $1}')"
echo ""
echo "使用方法:"
echo "  1. 双击DMG文件挂载"
echo "  2. 将AmDb拖拽到Applications文件夹"
echo "  3. 在启动台或应用程序中找到AmDb"
echo ""

