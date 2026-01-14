# AmDb - 区块链优化数据库系统

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey.svg)]()

AmDb是一个专为区块链应用优化的高性能数据库系统，结合了LSM Tree、B+ Tree和Merkle Tree的优势，提供数据完整性验证、版本管理和高性能读写能力。

## 特性

- 🚀 **高性能**: 优化的存储引擎，支持大规模数据
- 🔒 **数据完整性**: Merkle Tree验证，确保数据不被篡改
- 📦 **版本管理**: 完整的版本历史和时间点查询
- 🌐 **网络支持**: 服务器-客户端架构，支持远程操作
- 🖥️ **多平台**: 支持macOS、Linux、Windows
- 🛠️ **完整工具**: CLI命令行工具和GUI图形界面管理器
- 📚 **多数据库**: 支持创建和管理多个独立数据库实例

## 快速开始

### 安装

#### macOS
```bash
# 下载DMG安装包
# 双击安装或使用压缩包
tar -xzf amdb-1.0.0-darwin-x86_64.tar.gz
cd amdb-1.0.0-darwin-x86_64
```

#### Linux
```bash
tar -xzf amdb-1.0.0-linux-x86_64.tar.gz
cd amdb-1.0.0-linux-x86_64
```

#### Windows
```bash
# 解压ZIP包
unzip amdb-1.0.0-windows-x86_64.zip
cd amdb-1.0.0-windows-x86_64
```

### 使用

#### 启动服务器
```bash
./amdb-server
# 或
python3 -m src.amdb.server
```

#### 使用CLI
```bash
./amdb-cli
# 或
python3 -m src.amdb.cli

# 连接本地数据库
> connect ./data/mydb

# 连接远程数据库
> connect --host 127.0.0.1 --port 3888 --database mydb

# 写入数据
> put key1 "value1"

# 读取数据
> get key1

# 查看统计信息
> show stats
```

#### 使用GUI管理器
```bash
./amdb-manager
# 或
python3 amdb_manager.py
```

## 项目结构

```
AmDb/
├── src/amdb/          # 源代码
│   ├── storage/       # 存储引擎
│   ├── network/       # 网络通信
│   └── ...
├── docs/              # 文档
├── examples/          # 示例代码
├── tests/             # 测试代码
├── dist/              # 编译输出
└── build/             # 构建临时文件
```

## 文档

- [网络架构](docs/NETWORK_ARCHITECTURE.md) - 服务器-客户端架构说明
- [集成指南](docs/INTEGRATION_GUIDE.md) - 如何在项目中使用AmDb
- [构建和打包](docs/BUILD_AND_PACKAGE.md) - 编译和打包指南
- [远程操作](docs/REMOTE_OPERATIONS.md) - 远程操作支持说明

## 开发

### 环境要求
- Python 3.8+
- Cython (用于性能优化)
- PyInstaller (用于打包)

### 编译
```bash
# 编译原生扩展
python3 setup_cython.py build_ext --inplace

# 打包可执行文件
./build_all_platforms.sh

# 创建分发包
./build_distribution.sh
```

## 性能

- **顺序写入**: ~17,751 记录/秒
- **批量写入**: 支持大规模数据
- **数据完整性**: Merkle Tree验证
- **版本管理**: 完整的历史记录

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 贡献

欢迎贡献代码！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

## 链接

- **源代码**: https://github.com/coretrusts/amdb
- **文档**: https://github.com/coretrusts/amdb-docs
- **发行版**: https://github.com/coretrusts/amdb-releases

## 作者

CoreTrusts Organization

---

**注意**: 这是开发版本，生产环境使用前请充分测试。
