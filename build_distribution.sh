#!/bin/bash
# AmDb 完整分发包构建脚本
# 类似比特币的方式，将数据库核心库打包到安装包中

set -e

echo "=================================================================================="
echo "AmDb 完整分发包构建脚本"
echo "=================================================================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 获取版本号
VERSION=$(python3 -c "import sys; sys.path.insert(0, 'src'); from amdb import __version__; print(__version__)" 2>/dev/null || echo "1.0.0")
PLATFORM=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

echo "版本: $VERSION"
echo "平台: $PLATFORM"
echo "架构: $ARCH"
echo ""

# 创建分发目录
DIST_DIR="dist/amdb-${VERSION}-${PLATFORM}-${ARCH}"
echo "创建分发目录: $DIST_DIR"
rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR"

# 1. 复制源代码（类似比特币的src目录）
echo "1. 复制源代码..."
mkdir -p "$DIST_DIR/src"
cp -r src/* "$DIST_DIR/src/"

# 2. 复制编译好的原生扩展（类似比特币的lib目录）
echo "2. 复制原生扩展..."
mkdir -p "$DIST_DIR/lib"

# 从amdb目录复制（编译后的位置）
if [ -d "amdb/storage" ]; then
    find amdb/storage -name "*.so" -o -name "*.pyd" | while read -r file; do
        cp "$file" "$DIST_DIR/lib/" 2>/dev/null || true
    done
fi
if [ -d "amdb" ]; then
    find amdb -maxdepth 1 -name "*.so" -o -name "*.pyd" | while read -r file; do
        cp "$file" "$DIST_DIR/lib/" 2>/dev/null || true
    done
fi

# 也从src目录复制（如果存在）
if [ -d "src/amdb/storage" ]; then
    find src/amdb/storage -name "*.so" -o -name "*.pyd" | while read -r file; do
        cp "$file" "$DIST_DIR/lib/" 2>/dev/null || true
    done
fi
if [ -d "src/amdb" ]; then
    find src/amdb -maxdepth 1 -name "*.so" -o -name "*.pyd" | while read -r file; do
        cp "$file" "$DIST_DIR/lib/" 2>/dev/null || true
    done
fi

# 3. 复制配置文件
echo "3. 复制配置文件..."
mkdir -p "$DIST_DIR/config"
cp amdb.ini "$DIST_DIR/config/" 2>/dev/null || true
cp -r examples "$DIST_DIR/" 2>/dev/null || true

# 4. 复制文档
echo "4. 复制文档..."
cp README.md "$DIST_DIR/" 2>/dev/null || true
cp LICENSE "$DIST_DIR/" 2>/dev/null || true
cp -r docs "$DIST_DIR/" 2>/dev/null || true

# 5. 复制多语言绑定
echo "5. 复制多语言绑定..."
cp -r bindings "$DIST_DIR/" 2>/dev/null || true

# 6. 复制可执行文件（如果已打包）
echo "6. 复制可执行文件..."
PLATFORM_DIR="dist/${PLATFORM}_${ARCH}"
if [ -d "$PLATFORM_DIR" ]; then
    # 复制服务器可执行文件
    if [ -f "$PLATFORM_DIR/amdb-server" ]; then
        cp "$PLATFORM_DIR/amdb-server" "$DIST_DIR/"
        chmod +x "$DIST_DIR/amdb-server"
        echo "  ✓ 已复制 amdb-server"
    fi
    # 复制CLI可执行文件
    if [ -f "$PLATFORM_DIR/amdb-cli" ]; then
        cp "$PLATFORM_DIR/amdb-cli" "$DIST_DIR/"
        chmod +x "$DIST_DIR/amdb-cli"
        echo "  ✓ 已复制 amdb-cli"
    fi
    # 复制GUI可执行文件
    if [ -f "$PLATFORM_DIR/amdb-manager" ]; then
        cp "$PLATFORM_DIR/amdb-manager" "$DIST_DIR/"
        chmod +x "$DIST_DIR/amdb-manager"
        echo "  ✓ 已复制 amdb-manager"
    fi
fi

# 7. 创建启动脚本（如果可执行文件不存在，使用Python脚本）
echo "7. 创建启动脚本..."

# 服务器启动脚本（如果可执行文件不存在时使用）
if [ ! -f "$DIST_DIR/amdb-server" ]; then
    cat > "$DIST_DIR/amdb-server" << 'EOF'
#!/bin/bash
# AmDb 数据库服务器启动脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$SCRIPT_DIR/src:$PYTHONPATH"

# 加载原生扩展
if [ -d "$SCRIPT_DIR/lib" ]; then
    export LD_LIBRARY_PATH="$SCRIPT_DIR/lib:$LD_LIBRARY_PATH"
    export DYLD_LIBRARY_PATH="$SCRIPT_DIR/lib:$DYLD_LIBRARY_PATH"
fi

cd "$SCRIPT_DIR" || exit 1
python3 -m src.amdb.server "$@"
EOF
    chmod +x "$DIST_DIR/amdb-server"
fi

# CLI启动脚本（如果可执行文件不存在时使用）
if [ ! -f "$DIST_DIR/amdb-cli" ]; then
    cat > "$DIST_DIR/amdb-cli" << 'EOF'
#!/bin/bash
# AmDb 命令行工具启动脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$SCRIPT_DIR/src:$PYTHONPATH"

# 加载原生扩展
if [ -d "$SCRIPT_DIR/lib" ]; then
    export LD_LIBRARY_PATH="$SCRIPT_DIR/lib:$LD_LIBRARY_PATH"
    export DYLD_LIBRARY_PATH="$SCRIPT_DIR/lib:$DYLD_LIBRARY_PATH"
fi

cd "$SCRIPT_DIR" || exit 1
python3 -m src.amdb.cli "$@"
EOF
    chmod +x "$DIST_DIR/amdb-cli"
fi

# GUI启动脚本（如果可执行文件不存在时使用）
if [ ! -f "$DIST_DIR/amdb-manager" ]; then
    cat > "$DIST_DIR/amdb-manager" << 'EOF'
#!/bin/bash
# AmDb GUI管理器启动脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$SCRIPT_DIR/src:$PYTHONPATH"

# 加载原生扩展
if [ -d "$SCRIPT_DIR/lib" ]; then
    export LD_LIBRARY_PATH="$SCRIPT_DIR/lib:$LD_LIBRARY_PATH"
    export DYLD_LIBRARY_PATH="$SCRIPT_DIR/lib:$DYLD_LIBRARY_PATH"
fi

cd "$SCRIPT_DIR" || exit 1
python3 amdb_manager.py "$@"
EOF
    chmod +x "$DIST_DIR/amdb-manager"
fi

# 8. 创建安装脚本
echo "8. 创建安装脚本..."
cp install.sh "$DIST_DIR/" 2>/dev/null || true
cp install.bat "$DIST_DIR/" 2>/dev/null || true

# 9. 创建requirements.txt（仅运行时依赖）
echo "9. 创建运行时依赖文件..."
cat > "$DIST_DIR/requirements.txt" << 'EOF'
# AmDb 运行时依赖
# 注意：原生扩展已包含在lib目录中，无需安装Cython

# 基础依赖
# 如果需要网络功能，取消下面的注释
# requests>=2.25.0

# 如果需要GUI功能，取消下面的注释
# tkinter 通常已包含在Python标准库中
EOF

# 10. 创建README
echo "10. 创建分发README..."
cat > "$DIST_DIR/README_DIST.txt" << EOF
AmDb 数据库系统 - 分发包
版本: $VERSION
平台: $PLATFORM-$ARCH

安装说明:
==========

Linux/macOS:
  1. 解压分发包
  2. 运行: ./install.sh
  3. 或直接使用: ./amdb-server, ./amdb-cli, ./amdb-manager

Windows:
  1. 解压分发包
  2. 运行: install.bat
  3. 或直接使用: amdb-server.bat, amdb-cli.bat, amdb-manager.bat

目录结构:
==========
src/          - Python源代码
lib/          - 编译好的原生扩展（.so/.pyd）
config/       - 配置文件
bindings/     - 多语言绑定
docs/         - 文档
examples/     - 示例代码

快速开始:
==========
1. 启动服务器: ./amdb-server
2. 使用CLI: ./amdb-cli
3. 使用GUI: ./amdb-manager

更多信息请参考 README.md 和 docs/ 目录
EOF

# 11. 创建压缩包
echo "11. 创建压缩包..."
cd dist
if [ "$PLATFORM" = "darwin" ]; then
    tar -czf "amdb-${VERSION}-${PLATFORM}-${ARCH}.tar.gz" "amdb-${VERSION}-${PLATFORM}-${ARCH}"
    echo -e "${GREEN}✓ 创建压缩包: amdb-${VERSION}-${PLATFORM}-${ARCH}.tar.gz${NC}"
elif [ "$PLATFORM" = "linux" ]; then
    tar -czf "amdb-${VERSION}-${PLATFORM}-${ARCH}.tar.gz" "amdb-${VERSION}-${PLATFORM}-${ARCH}"
    echo -e "${GREEN}✓ 创建压缩包: amdb-${VERSION}-${PLATFORM}-${ARCH}.tar.gz${NC}"
fi
cd ..

echo ""
echo -e "${GREEN}=================================================================================="
echo "分发包构建完成！"
echo "==================================================================================${NC}"
echo ""
echo "分发目录: $DIST_DIR"
echo "压缩包: dist/amdb-${VERSION}-${PLATFORM}-${ARCH}.tar.gz"
echo ""
echo "分发包包含:"
echo "  - 完整的源代码"
echo "  - 编译好的原生扩展"
echo "  - 配置文件"
echo "  - 启动脚本"
echo "  - 安装脚本"
echo "  - 文档和示例"
echo ""

