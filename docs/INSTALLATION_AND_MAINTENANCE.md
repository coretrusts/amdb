# AmDb 安装和维护指南

## 目录

1. [安装方式](#安装方式)
2. [启动脚本](#启动脚本)
3. [打包编译](#打包编译)
4. [使用维护](#使用维护)
5. [类似比特币的打包方案](#类似比特币的打包方案)

## 安装方式

### 方式1: 使用安装脚本（推荐）

#### Linux/macOS
```bash
chmod +x install.sh
sudo ./install.sh
```

#### Windows
```cmd
install.bat
```

### 方式2: 使用Python包管理器

```bash
pip install -e .
```

### 方式3: 从源码安装

```bash
python3 setup.py install
```

## 启动脚本

### 服务器启动脚本

**Linux/macOS**: `/usr/local/amdb/bin/amdb-server`
**Windows**: `C:\Program Files\AmDb\bin\amdb-server.bat`

```bash
# 启动服务器
amdb-server

# 指定配置文件
amdb-server --config /path/to/config.ini

# 指定数据目录
amdb-server --data-dir /path/to/data
```

### CLI启动脚本

**Linux/macOS**: `/usr/local/amdb/bin/amdb-cli`
**Windows**: `C:\Program Files\AmDb\bin\amdb-cli.bat`

```bash
# 启动CLI
amdb-cli

# 连接指定数据库
amdb-cli --connect ./data/my_database
```

### GUI管理器启动脚本

**Linux/macOS**: `/usr/local/amdb/bin/amdb-manager`
**Windows**: `C:\Program Files\AmDb\bin\amdb-manager.bat`

```bash
# 启动GUI
amdb-manager
```

## 打包编译

### 1. 编译原生扩展

```bash
# 编译Cython扩展
python3 setup_cython.py build_ext --inplace

# 或使用脚本
./build_native.sh
```

### 2. 打包CLI和GUI

#### Linux/macOS
```bash
./build_all_platforms.sh
```

#### Windows
```cmd
build_all_platforms.bat
```

#### 使用Python脚本
```bash
python3 build_package.py
```

### 3. 构建完整分发包

```bash
./build_distribution.sh
```

这将创建一个包含所有依赖的完整分发包，类似比特币的方式。

## 使用维护

### 日常维护

#### 1. 数据备份

```bash
# 使用备份工具
python3 -m src.amdb.backup --source ./data/my_database --output ./backup.tar.gz
```

#### 2. 性能监控

```bash
# 查看统计信息
amdb-cli --stats

# 或使用GUI的性能监控标签页
amdb-manager
```

#### 3. 日志管理

日志文件位置：
- Linux/macOS: `/usr/local/amdb/logs/`
- Windows: `C:\Program Files\AmDb\logs\`

```bash
# 查看日志
tail -f /usr/local/amdb/logs/amdb.log

# 清理旧日志（保留最近7天）
find /usr/local/amdb/logs -name "*.log" -mtime +7 -delete
```

#### 4. 配置管理

配置文件位置：
- Linux/macOS: `/usr/local/amdb/config/amdb.ini`
- Windows: `C:\Program Files\AmDb\config\amdb.ini`

```bash
# 编辑配置
vi /usr/local/amdb/config/amdb.ini

# 或使用GUI的配置管理标签页
amdb-manager
```

### 系统服务管理（Linux）

```bash
# 启动服务
sudo systemctl start amdb

# 停止服务
sudo systemctl stop amdb

# 重启服务
sudo systemctl restart amdb

# 查看状态
sudo systemctl status amdb

# 开机自启
sudo systemctl enable amdb
```

### 故障排查

#### 1. 检查服务状态

```bash
# Linux
sudo systemctl status amdb

# 查看日志
journalctl -u amdb -f
```

#### 2. 检查端口占用

```bash
# 检查默认端口3888
netstat -tuln | grep 3888
# 或
lsof -i :3888
```

#### 3. 检查数据完整性

```bash
# 使用CLI验证
amdb-cli --verify ./data/my_database
```

#### 4. 性能问题排查

```bash
# 查看性能指标
amdb-cli --stats --detailed

# 检查磁盘空间
df -h /usr/local/amdb/data

# 检查内存使用
ps aux | grep amdb
```

## 类似比特币的打包方案

### 方案概述

类似比特币将LevelDB打包到安装包的方式，AmDb将数据库核心库（包括原生扩展）打包到分发包中，实现：

1. **自包含**: 不依赖外部数据库库
2. **可移植**: 包含所有必要的二进制文件
3. **易部署**: 解压即用，无需额外安装

### 目录结构

```
amdb-1.0.0-linux-x86_64/
├── src/              # Python源代码
│   └── amdb/
│       ├── storage/  # 存储引擎
│       ├── version.py
│       └── ...
├── lib/              # 编译好的原生扩展（类似比特币的lib目录）
│   ├── skip_list_cython.so
│   ├── version_cython.so
│   └── ...
├── config/           # 配置文件
│   └── amdb.ini
├── bindings/         # 多语言绑定
│   ├── c/
│   ├── cpp/
│   └── ...
├── docs/             # 文档
├── examples/         # 示例代码
├── amdb-server       # 服务器启动脚本
├── amdb-cli          # CLI启动脚本
├── amdb-manager      # GUI启动脚本
├── install.sh        # 安装脚本
└── README_DIST.txt   # 分发说明
```

### 构建流程

1. **编译原生扩展**
   ```bash
   python3 setup_cython.py build_ext --inplace
   ```

2. **收集所有文件**
   - 源代码
   - 编译好的.so/.pyd文件
   - 配置文件
   - 启动脚本

3. **创建分发包**
   ```bash
   ./build_distribution.sh
   ```

4. **打包压缩**
   - Linux/macOS: `.tar.gz`
   - Windows: `.zip`

### 启动脚本设计

启动脚本自动设置环境变量，确保能找到原生扩展：

```bash
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$SCRIPT_DIR/src:$PYTHONPATH"
export LD_LIBRARY_PATH="$SCRIPT_DIR/lib:$LD_LIBRARY_PATH"
python3 -m src.amdb.server "$@"
```

### 优势

1. **无需安装依赖**: 所有原生扩展已编译并包含
2. **版本一致**: 确保使用正确的扩展版本
3. **易于分发**: 单个压缩包包含所有内容
4. **跨平台**: 为每个平台构建独立的分发包

### 使用方式

#### 方式1: 直接使用（无需安装）

```bash
# 解压分发包
tar -xzf amdb-1.0.0-linux-x86_64.tar.gz
cd amdb-1.0.0-linux-x86_64

# 直接运行
./amdb-server
./amdb-cli
./amdb-manager
```

#### 方式2: 安装到系统

```bash
# 解压分发包
tar -xzf amdb-1.0.0-linux-x86_64.tar.gz
cd amdb-1.0.0-linux-x86_64

# 运行安装脚本
sudo ./install.sh
```

### 维护建议

1. **定期备份**: 使用内置备份工具定期备份数据
2. **监控日志**: 定期检查日志文件，及时发现问题
3. **更新配置**: 根据使用情况调整配置文件
4. **性能优化**: 根据数据量调整分片和缓存配置
5. **版本升级**: 升级前先备份数据，测试新版本后再部署

## 更新日期

2026-01-13

