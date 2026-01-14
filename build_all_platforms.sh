#!/bin/bash
# AmDb 跨平台打包脚本 (Linux/macOS)
# 支持打包CLI和GUI到不同平台

set -e

echo "=================================================================================="
echo "AmDb 跨平台打包脚本"
echo "=================================================================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到python3${NC}"
    exit 1
fi

PYTHON=python3

# 检查PyInstaller
if ! $PYTHON -c "import PyInstaller" 2>/dev/null; then
    echo -e "${YELLOW}PyInstaller未安装，正在安装...${NC}"
    $PYTHON -m pip install pyinstaller
fi

# 获取平台信息
PLATFORM=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

echo "平台: $PLATFORM"
echo "架构: $ARCH"
echo ""

# 创建输出目录
OUTPUT_DIR="dist/${PLATFORM}_${ARCH}"
mkdir -p "$OUTPUT_DIR"

# 打包CLI
echo "=================================================================================="
echo "打包CLI..."
echo "=================================================================================="
echo ""

$PYTHON -m PyInstaller \
    --name amdb-cli \
    --onefile \
    --console \
    --add-data "src:src" \
    --hidden-import src.amdb \
    --hidden-import src.amdb.cli \
    --hidden-import src.amdb.database \
    --hidden-import src.amdb.config \
    --hidden-import src.amdb.storage \
    --hidden-import src.amdb.storage.lsm_tree \
    --hidden-import src.amdb.storage.bplus_tree \
    --hidden-import src.amdb.storage.merkle_tree \
    --hidden-import src.amdb.storage.skip_list \
    --hidden-import src.amdb.storage.file_format \
    --hidden-import src.amdb.storage.storage_engine \
    --hidden-import src.amdb.storage.sharded_lsm_tree \
    --hidden-import src.amdb.version \
    --hidden-import src.amdb.index \
    --hidden-import src.amdb.value_formatter \
    --hidden-import src.amdb.db_scanner \
    --clean \
    --noconfirm \
    amdb-cli

if [ -f "dist/amdb-cli" ] || [ -f "dist/amdb-cli.exe" ]; then
    echo -e "${GREEN}✓ CLI打包成功${NC}"
    if [ -f "dist/amdb-cli" ]; then
        cp dist/amdb-cli "$OUTPUT_DIR/"
    elif [ -f "dist/amdb-cli.exe" ]; then
        cp dist/amdb-cli.exe "$OUTPUT_DIR/"
    fi
else
    echo -e "${RED}✗ CLI打包失败${NC}"
    exit 1
fi

# 打包服务器
echo ""
echo "=================================================================================="
echo "打包服务器..."
echo "=================================================================================="
echo ""

$PYTHON -m PyInstaller \
    --name amdb-server \
    --onefile \
    --console \
    --add-data "src:src" \
    --hidden-import src.amdb \
    --hidden-import src.amdb.server \
    --hidden-import src.amdb.database \
    --hidden-import src.amdb.config \
    --hidden-import src.amdb.network \
    --hidden-import src.amdb.storage \
    --hidden-import src.amdb.storage.lsm_tree \
    --hidden-import src.amdb.storage.bplus_tree \
    --hidden-import src.amdb.storage.merkle_tree \
    --hidden-import src.amdb.storage.skip_list \
    --hidden-import src.amdb.storage.file_format \
    --hidden-import src.amdb.storage.storage_engine \
    --hidden-import src.amdb.storage.sharded_lsm_tree \
    --hidden-import src.amdb.version \
    --hidden-import src.amdb.index \
    --hidden-import src.amdb.db_registry \
    --clean \
    --noconfirm \
    amdb-server

if [ -f "dist/amdb-server" ] || [ -f "dist/amdb-server.exe" ]; then
    echo -e "${GREEN}✓ 服务器打包成功${NC}"
    if [ -f "dist/amdb-server" ]; then
        cp dist/amdb-server "$OUTPUT_DIR/"
        chmod +x "$OUTPUT_DIR/amdb-server"
    elif [ -f "dist/amdb-server.exe" ]; then
        cp dist/amdb-server.exe "$OUTPUT_DIR/"
    fi
else
    echo -e "${RED}✗ 服务器打包失败${NC}"
    exit 1
fi

# 打包GUI
echo ""
echo "=================================================================================="
echo "打包GUI..."
echo "=================================================================================="
echo ""

$PYTHON -m PyInstaller \
    --name amdb-manager \
    --onefile \
    --windowed \
    --add-data "src:src" \
    --hidden-import src.amdb \
    --hidden-import src.amdb.gui_manager \
    --hidden-import src.amdb.database \
    --hidden-import src.amdb.config \
    --hidden-import src.amdb.storage \
    --hidden-import src.amdb.storage.lsm_tree \
    --hidden-import src.amdb.storage.bplus_tree \
    --hidden-import src.amdb.storage.merkle_tree \
    --hidden-import src.amdb.storage.skip_list \
    --hidden-import src.amdb.storage.file_format \
    --hidden-import src.amdb.storage.storage_engine \
    --hidden-import src.amdb.storage.sharded_lsm_tree \
    --hidden-import src.amdb.version \
    --hidden-import src.amdb.index \
    --hidden-import src.amdb.value_formatter \
    --hidden-import src.amdb.db_scanner \
    --hidden-import tkinter \
    --hidden-import tkinter.ttk \
    --hidden-import tkinter.messagebox \
    --hidden-import tkinter.filedialog \
    --hidden-import tkinter.scrolledtext \
    --clean \
    --noconfirm \
    amdb_manager.py

if [ -f "dist/amdb-manager" ] || [ -f "dist/amdb-manager.exe" ] || [ -d "dist/amdb-manager.app" ]; then
    echo -e "${GREEN}✓ GUI打包成功${NC}"
    if [ -f "dist/amdb-manager" ]; then
        cp dist/amdb-manager "$OUTPUT_DIR/"
    elif [ -f "dist/amdb-manager.exe" ]; then
        cp dist/amdb-manager.exe "$OUTPUT_DIR/"
    elif [ -d "dist/amdb-manager.app" ]; then
        cp -r dist/amdb-manager.app "$OUTPUT_DIR/"
    fi
else
    echo -e "${RED}✗ GUI打包失败${NC}"
    exit 1
fi

echo ""
echo "=================================================================================="
echo -e "${GREEN}打包完成！${NC}"
echo "=================================================================================="
echo ""
echo "输出目录: $OUTPUT_DIR"
echo ""
ls -lh "$OUTPUT_DIR"

