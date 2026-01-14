#!/bin/bash
# 编译原生扩展（C/Cython）
# 支持不同平台的编译

set -e

echo "=================================================================================="
echo "AmDb 原生扩展编译脚本"
echo "=================================================================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到python3${NC}"
    exit 1
fi

PYTHON=python3

# 检查Cython
if ! $PYTHON -c "import Cython" 2>/dev/null; then
    echo -e "${YELLOW}Cython未安装，正在安装...${NC}"
    $PYTHON -m pip install Cython
fi

# 获取平台信息
PLATFORM=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

echo "平台: $PLATFORM"
echo "架构: $ARCH"
echo ""

# 编译Cython扩展
echo "=================================================================================="
echo "编译Cython扩展..."
echo "=================================================================================="
echo ""

cd "$(dirname "$0")"

# 编译skip_list
echo "编译 skip_list..."
$PYTHON setup_cython.py build_ext --inplace

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Cython扩展编译成功${NC}"
else
    echo -e "${RED}✗ Cython扩展编译失败${NC}"
    exit 1
fi

# 检查编译结果
if [ -f "src/amdb/storage/skip_list_cython*.so" ] || [ -f "src/amdb/storage/skip_list_cython*.pyd" ]; then
    echo -e "${GREEN}✓ skip_list扩展已生成${NC}"
else
    echo -e "${YELLOW}警告: skip_list扩展未找到${NC}"
fi

if [ -f "src/amdb/version_cython*.so" ] || [ -f "src/amdb/version_cython*.pyd" ]; then
    echo -e "${GREEN}✓ version扩展已生成${NC}"
else
    echo -e "${YELLOW}警告: version扩展未找到${NC}"
fi

echo ""
echo "=================================================================================="
echo -e "${GREEN}编译完成！${NC}"
echo "=================================================================================="

