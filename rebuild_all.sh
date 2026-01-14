#!/bin/bash
# 重新打包所有组件（包括服务器、CLI、GUI）
# 更新所有打包类型：可执行文件、分发包、DMG等

set -e

echo "=================================================================================="
echo "AmDb 完整重新打包"
echo "=================================================================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PLATFORM=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

echo "平台: $PLATFORM"
echo "架构: $ARCH"
echo ""

# 步骤1: 编译原生扩展
echo -e "${GREEN}步骤1: 编译原生扩展${NC}"
echo "--------------------------------------------------------------------------------"
if [ -f "setup_cython.py" ]; then
    if [ -d "venv_cython" ]; then
        source venv_cython/bin/activate 2>/dev/null || true
    fi
    python3 setup_cython.py build_ext --inplace
    echo -e "${GREEN}✓ 原生扩展编译完成${NC}"
else
    echo -e "${YELLOW}⚠ 未找到setup_cython.py，跳过原生扩展编译${NC}"
fi
echo ""

# 步骤2: 打包所有可执行文件（服务器、CLI、GUI）
echo -e "${GREEN}步骤2: 打包所有可执行文件（服务器、CLI、GUI）${NC}"
echo "--------------------------------------------------------------------------------"
if [ -f "build_all_platforms.sh" ]; then
    ./build_all_platforms.sh
    echo -e "${GREEN}✓ 所有可执行文件打包完成${NC}"
    
    # 验证文件
    PLATFORM_DIR="dist/${PLATFORM}_${ARCH}"
    echo ""
    echo "生成的文件:"
    if [ -f "$PLATFORM_DIR/amdb-server" ] || [ -f "$PLATFORM_DIR/amdb-server.exe" ]; then
        echo -e "  ${GREEN}✓ amdb-server${NC}"
    else
        echo -e "  ${RED}✗ amdb-server 未找到${NC}"
    fi
    if [ -f "$PLATFORM_DIR/amdb-cli" ] || [ -f "$PLATFORM_DIR/amdb-cli.exe" ]; then
        echo -e "  ${GREEN}✓ amdb-cli${NC}"
    else
        echo -e "  ${RED}✗ amdb-cli 未找到${NC}"
    fi
    if [ -f "$PLATFORM_DIR/amdb-manager" ] || [ -f "$PLATFORM_DIR/amdb-manager.exe" ] || [ -d "$PLATFORM_DIR/amdb-manager.app" ]; then
        echo -e "  ${GREEN}✓ amdb-manager${NC}"
    else
        echo -e "  ${RED}✗ amdb-manager 未找到${NC}"
    fi
else
    echo -e "${YELLOW}⚠ 未找到build_all_platforms.sh${NC}"
fi
echo ""

# 步骤3: 创建完整分发包
echo -e "${GREEN}步骤3: 创建完整分发包（包含所有可执行文件）${NC}"
echo "--------------------------------------------------------------------------------"
if [ -f "build_distribution.sh" ]; then
    ./build_distribution.sh
    echo -e "${GREEN}✓ 完整分发包创建完成${NC}"
else
    echo -e "${YELLOW}⚠ 未找到build_distribution.sh${NC}"
fi
echo ""

# 步骤4: 创建DMG（仅macOS）
if [ "$PLATFORM" = "darwin" ]; then
    echo -e "${GREEN}步骤4: 创建macOS DMG安装包${NC}"
    echo "--------------------------------------------------------------------------------"
    if [ -f "build_dmg.sh" ]; then
        ./build_dmg.sh
        echo -e "${GREEN}✓ DMG安装包创建完成${NC}"
    else
        echo -e "${YELLOW}⚠ 未找到build_dmg.sh${NC}"
    fi
    echo ""
fi

echo -e "${GREEN}=================================================================================="
echo "所有打包步骤完成！"
echo "==================================================================================${NC}"
echo ""
echo "输出文件:"
echo ""

# 显示生成的文件
PLATFORM_DIR="dist/${PLATFORM}_${ARCH}"
if [ -d "$PLATFORM_DIR" ]; then
    echo "可执行文件 ($PLATFORM_DIR):"
    ls -lh "$PLATFORM_DIR"/* 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}' || echo "  (无)"
fi

echo ""
echo "分发包:"
ls -lh dist/amdb-*.tar.gz 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}' || echo "  (无)"

if [ "$PLATFORM" = "darwin" ]; then
    echo ""
    echo "DMG安装包:"
    ls -lh dist/AmDb-*.dmg 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}' || echo "  (无)"
fi

echo ""

