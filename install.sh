#!/bin/bash
# AmDb 安装脚本
# 支持Linux和macOS

set -e

echo "=================================================================================="
echo "AmDb 数据库系统安装脚本"
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
    echo "请先安装Python 3.7或更高版本"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo -e "${GREEN}✓ 检测到Python版本: $PYTHON_VERSION${NC}"

# 检查pip
if ! command -v pip3 &> /dev/null; then
    echo -e "${YELLOW}警告: 未找到pip3，尝试安装...${NC}"
    python3 -m ensurepip --upgrade
fi

# 获取安装目录
INSTALL_DIR="${INSTALL_DIR:-/usr/local/amdb}"
BIN_DIR="${BIN_DIR:-/usr/local/bin}"

echo ""
echo "安装配置:"
echo "  安装目录: $INSTALL_DIR"
echo "  二进制目录: $BIN_DIR"
echo ""

# 确认安装
read -p "是否继续安装? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "安装已取消"
    exit 0
fi

# 创建安装目录
echo "创建安装目录..."
sudo mkdir -p "$INSTALL_DIR"
sudo mkdir -p "$INSTALL_DIR/bin"
sudo mkdir -p "$INSTALL_DIR/lib"
sudo mkdir -p "$INSTALL_DIR/data"
sudo mkdir -p "$INSTALL_DIR/config"
sudo mkdir -p "$INSTALL_DIR/logs"

# 复制文件
echo "复制文件..."
sudo cp -r src "$INSTALL_DIR/"
sudo cp -r bindings "$INSTALL_DIR/" 2>/dev/null || true
sudo cp amdb.ini "$INSTALL_DIR/config/" 2>/dev/null || true
sudo cp README.md "$INSTALL_DIR/" 2>/dev/null || true

# 安装Python依赖
echo "安装Python依赖..."
sudo python3 -m pip install --upgrade pip
sudo python3 -m pip install -r requirements.txt

# 编译原生扩展
echo "编译原生扩展..."
if [ -f "setup_cython.py" ]; then
    sudo python3 setup_cython.py build_ext --inplace
    sudo cp -r src/amdb/storage/*.so "$INSTALL_DIR/lib/" 2>/dev/null || true
    sudo cp -r src/amdb/*.so "$INSTALL_DIR/lib/" 2>/dev/null || true
fi

# 创建启动脚本
echo "创建启动脚本..."
sudo tee "$INSTALL_DIR/bin/amdb-server" > /dev/null << 'EOF'
#!/bin/bash
# AmDb 数据库服务器启动脚本

INSTALL_DIR="/usr/local/amdb"
export PYTHONPATH="$INSTALL_DIR/src:$PYTHONPATH"

cd "$INSTALL_DIR" || exit 1
python3 -m src.amdb.server "$@"
EOF

sudo chmod +x "$INSTALL_DIR/bin/amdb-server"

# 创建CLI启动脚本
sudo tee "$INSTALL_DIR/bin/amdb-cli" > /dev/null << 'EOF'
#!/bin/bash
# AmDb 命令行工具启动脚本

INSTALL_DIR="/usr/local/amdb"
export PYTHONPATH="$INSTALL_DIR/src:$PYTHONPATH"

cd "$INSTALL_DIR" || exit 1
python3 -m src.amdb.cli "$@"
EOF

sudo chmod +x "$INSTALL_DIR/bin/amdb-cli"

# 创建GUI启动脚本
sudo tee "$INSTALL_DIR/bin/amdb-manager" > /dev/null << 'EOF'
#!/bin/bash
# AmDb GUI管理器启动脚本

INSTALL_DIR="/usr/local/amdb"
export PYTHONPATH="$INSTALL_DIR/src:$PYTHONPATH"

cd "$INSTALL_DIR" || exit 1
python3 amdb_manager.py "$@"
EOF

sudo chmod +x "$INSTALL_DIR/bin/amdb-manager"

# 创建符号链接到系统PATH
echo "创建系统链接..."
sudo ln -sf "$INSTALL_DIR/bin/amdb-server" "$BIN_DIR/amdb-server"
sudo ln -sf "$INSTALL_DIR/bin/amdb-cli" "$BIN_DIR/amdb-cli"
sudo ln -sf "$INSTALL_DIR/bin/amdb-manager" "$BIN_DIR/amdb-manager"

# 创建systemd服务文件（Linux）
if [ -d "/etc/systemd/system" ]; then
    echo "创建systemd服务..."
    sudo tee /etc/systemd/system/amdb.service > /dev/null << EOF
[Unit]
Description=AmDb Database Server
After=network.target

[Service]
Type=simple
User=amdb
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/bin/amdb-server
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    echo "  服务文件已创建: /etc/systemd/system/amdb.service"
    echo "  使用以下命令管理服务:"
    echo "    sudo systemctl start amdb"
    echo "    sudo systemctl stop amdb"
    echo "    sudo systemctl enable amdb"
fi

# 创建启动配置文件
sudo tee "$INSTALL_DIR/config/startup.conf" > /dev/null << EOF
# AmDb 启动配置
INSTALL_DIR=$INSTALL_DIR
DATA_DIR=$INSTALL_DIR/data
LOG_DIR=$INSTALL_DIR/logs
CONFIG_FILE=$INSTALL_DIR/config/amdb.ini
EOF

echo ""
echo -e "${GREEN}=================================================================================="
echo "安装完成！"
echo "==================================================================================${NC}"
echo ""
echo "安装位置: $INSTALL_DIR"
echo ""
echo "使用方法:"
echo "  启动服务器: amdb-server"
echo "  命令行工具: amdb-cli"
echo "  GUI管理器: amdb-manager"
echo ""
echo "配置文件: $INSTALL_DIR/config/amdb.ini"
echo "数据目录: $INSTALL_DIR/data"
echo "日志目录: $INSTALL_DIR/logs"
echo ""

