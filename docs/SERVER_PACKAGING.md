# AmDb 服务器打包说明

## 架构设计

AmDb采用**分离式架构**，包含三个独立的组件：

### 1. amdb-server（服务器端）
- **作用**：独立的数据库服务器进程
- **特点**：常驻内存，监听网络端口
- **用途**：提供网络服务，处理客户端请求
- **打包**：独立的可执行文件

### 2. amdb-cli（命令行客户端）
- **作用**：命令行交互工具
- **特点**：可以连接本地文件或远程服务器
- **用途**：数据库操作、查询、管理
- **打包**：独立的可执行文件

### 3. amdb-manager（GUI管理器）
- **作用**：图形界面管理工具
- **特点**：可以连接本地文件或远程服务器
- **用途**：可视化数据库管理
- **打包**：独立的可执行文件

## 为什么CLI不能作为服务进程？

**CLI是客户端工具，不是服务器**：

1. **职责不同**：
   - CLI：交互式命令行工具，用于用户操作
   - Server：后台服务进程，处理网络请求

2. **运行方式不同**：
   - CLI：用户启动，执行命令后退出或保持交互
   - Server：系统启动，常驻内存，持续监听

3. **使用场景不同**：
   - CLI：开发、调试、手动操作
   - Server：生产环境、多客户端访问

## 打包后的文件结构

### macOS/Linux

```
dist/darwin_x86_64/
├── amdb-server      # 服务器可执行文件（独立）
├── amdb-cli         # CLI客户端（独立）
└── amdb-manager     # GUI管理器（独立）
```

### Windows

```
dist/windows_x86_64/
├── amdb-server.exe  # 服务器可执行文件（独立）
├── amdb-cli.exe     # CLI客户端（独立）
└── amdb-manager.exe # GUI管理器（独立）
```

## 使用方式

### 方式1: 本地文件模式（无需服务器）

```bash
# 直接使用CLI访问本地文件
./amdb-cli --connect ./data/my_database

# 或使用GUI
./amdb-manager
# 选择本地数据目录
```

### 方式2: 网络服务模式（需要服务器）

```bash
# 1. 启动服务器（常驻内存）
./amdb-server --host 0.0.0.0 --port 3888

# 2. 使用CLI连接服务器
./amdb-cli --host 127.0.0.1 --port 3888 --database my_database

# 3. 或使用GUI连接服务器
./amdb-manager
# 选择网络连接，输入IP和端口
```

## 服务器部署

### 作为系统服务（Linux/macOS）

创建systemd服务文件 `/etc/systemd/system/amdb.service`：

```ini
[Unit]
Description=AmDb Database Server
After=network.target

[Service]
Type=simple
User=amdb
WorkingDirectory=/opt/amdb
ExecStart=/opt/amdb/amdb-server --config /etc/amdb/amdb.ini
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl enable amdb
sudo systemctl start amdb
```

### 作为Windows服务

使用NSSM（Non-Sucking Service Manager）：

```cmd
nssm install AmDbServer "C:\Program Files\AmDb\amdb-server.exe"
nssm set AmDbServer AppParameters "--config C:\Program Files\AmDb\amdb.ini"
nssm start AmDbServer
```

### 后台运行（daemon模式）

```bash
# Linux/macOS
nohup ./amdb-server --config amdb.ini > server.log 2>&1 &

# 或使用screen/tmux
screen -S amdb-server
./amdb-server --config amdb.ini
# Ctrl+A+D 分离会话
```

## 打包命令

### 完整打包（包含服务器）

```bash
# Linux/macOS
./build_all_platforms.sh

# Windows
build_windows.bat
```

打包后会生成：
- `amdb-server` / `amdb-server.exe` - 服务器
- `amdb-cli` / `amdb-cli.exe` - CLI客户端
- `amdb-manager` / `amdb-manager.exe` - GUI管理器

## 服务器配置

### 配置文件（amdb.ini）

```ini
[network]
# 监听地址
host = 0.0.0.0          # 0.0.0.0表示监听所有网络接口

# 监听端口
port = 3888            # 使用不常用端口

# 最大连接数
max_connections = 100

# 超时时间（秒）
timeout = 30.0
```

### 启动参数

```bash
./amdb-server \
    --host 0.0.0.0 \
    --port 3888 \
    --data-dir ./data \
    --config amdb.ini
```

## 总结

1. **服务器是独立的可执行文件**：`amdb-server` / `amdb-server.exe`
2. **CLI是客户端工具**：不能作为服务进程
3. **三个组件独立打包**：服务器、CLI、GUI各自独立
4. **支持两种模式**：本地文件模式（无需服务器）和网络服务模式（需要服务器）

## 更新日期

2026-01-13

