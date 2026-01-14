#!/bin/bash
# 跨平台完整打包脚本
# 支持Linux、macOS、Windows

set -e

echo "=================================================================================="
echo "AmDb 跨平台完整打包"
echo "=================================================================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PLATFORM=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

echo "当前平台: $PLATFORM"
echo "架构: $ARCH"
echo ""

# 步骤1: 编译原生扩展
echo -e "${GREEN}步骤1: 编译原生扩展${NC}"
echo "--------------------------------------------------------------------------------"
if [ -f "setup_cython.py" ]; then
    if [ -d "venv_cython" ]; then
        source venv_cython/bin/activate
    fi
    python3 setup_cython.py build_ext --inplace
    echo -e "${GREEN}✓ 原生扩展编译完成${NC}"
else
    echo -e "${YELLOW}⚠ 未找到setup_cython.py${NC}"
fi
echo ""

# 步骤2: 打包CLI和GUI
echo -e "${GREEN}步骤2: 打包CLI和GUI${NC}"
echo "--------------------------------------------------------------------------------"
if [ "$PLATFORM" = "darwin" ]; then
    # macOS: 打包为可执行文件和.app
    ./build_all_platforms.sh
    echo -e "${GREEN}✓ macOS打包完成${NC}"
    
    # 创建DMG
    if [ -f "build_dmg.sh" ]; then
        echo ""
        echo -e "${GREEN}步骤2.5: 创建macOS DMG安装包${NC}"
        echo "--------------------------------------------------------------------------------"
        ./build_dmg.sh
        echo -e "${GREEN}✓ DMG安装包创建完成${NC}"
    fi
elif [ "$PLATFORM" = "linux" ]; then
    # Linux: 打包为可执行文件
    ./build_all_platforms.sh
    echo -e "${GREEN}✓ Linux打包完成${NC}"
else
    echo -e "${YELLOW}⚠ 当前平台不支持自动打包，请使用Windows脚本${NC}"
fi
echo ""

# 步骤3: 创建完整分发包
echo -e "${GREEN}步骤3: 创建完整分发包（类似比特币方式）${NC}"
echo "--------------------------------------------------------------------------------"
if [ -f "build_distribution.sh" ]; then
    ./build_distribution.sh
    echo -e "${GREEN}✓ 完整分发包创建完成${NC}"
else
    echo -e "${YELLOW}⚠ 未找到build_distribution.sh${NC}"
fi
echo ""

echo -e "${GREEN}=================================================================================="
echo "打包完成！"
echo "==================================================================================${NC}"
echo ""
echo "生成的文件:"
echo ""

# 显示生成的文件
if [ "$PLATFORM" = "darwin" ]; then
    echo "macOS平台:"
    echo "  - CLI/GUI: dist/darwin_${ARCH}/"
    if [ -f "dist/AmDb-"*"-macOS.dmg" ]; then
        echo "  - DMG安装包: $(ls dist/AmDb-*-macOS.dmg 2>/dev/null | head -1)"
    fi
    echo "  - 分发包: dist/amdb-*-darwin-${ARCH}.tar.gz"
elif [ "$PLATFORM" = "linux" ]; then
    echo "Linux平台:"
    echo "  - CLI/GUI: dist/linux_${ARCH}/"
    echo "  - 分发包: dist/amdb-*-linux-${ARCH}.tar.gz"
fi

echo ""
echo "Windows平台打包:"
echo "  请在Windows系统上运行: build_windows.bat"
echo "  或使用WSL/Docker进行交叉编译"
echo ""

