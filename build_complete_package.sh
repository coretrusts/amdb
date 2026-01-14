#!/bin/bash
# AmDb 完整打包脚本
# 包含：编译、打包、创建分发包

set -e

echo "=================================================================================="
echo "AmDb 完整打包流程"
echo "=================================================================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 步骤1: 编译原生扩展
echo -e "${GREEN}步骤1: 编译原生扩展${NC}"
echo "--------------------------------------------------------------------------------"
if [ -f "setup_cython.py" ]; then
    python3 setup_cython.py build_ext --inplace
    echo -e "${GREEN}✓ 原生扩展编译完成${NC}"
else
    echo -e "${YELLOW}⚠ 未找到setup_cython.py，跳过原生扩展编译${NC}"
fi
echo ""

# 步骤2: 打包CLI和GUI
echo -e "${GREEN}步骤2: 打包CLI和GUI${NC}"
echo "--------------------------------------------------------------------------------"
if [ -f "build_all_platforms.sh" ]; then
    ./build_all_platforms.sh
    echo -e "${GREEN}✓ CLI和GUI打包完成${NC}"
else
    echo -e "${YELLOW}⚠ 未找到build_all_platforms.sh，跳过CLI/GUI打包${NC}"
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
echo "所有打包步骤完成！"
echo "==================================================================================${NC}"
echo ""
echo "输出文件:"
echo "  - CLI/GUI可执行文件: dist/<platform>_<arch>/"
echo "  - 完整分发包: dist/amdb-<version>-<platform>-<arch>.tar.gz"
echo ""

