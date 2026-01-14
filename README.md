# AmDb - 区块链优化数据库系统

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)

AmDb是一个专为区块链应用优化的高性能数据库系统。

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

```bash
pip install -r requirements.txt
python3 setup.py install
```

### 使用

```python
from src.amdb.database import Database

db = Database('./data/mydb')
db.put(b'key1', b'value1')
value = db.get(b'key1')
```

### 启动服务器

```bash
./amdb-server
# 或
python3 -m src.amdb.server
```

### 使用CLI

```bash
./amdb-cli
# 连接本地数据库
> connect ./data/mydb
# 连接远程数据库
> connect --host 127.0.0.1 --port 3888 --database mydb
```

## 项目结构

```
AmDb/
├── src/amdb/          # 源代码
│   ├── storage/       # 存储引擎
│   ├── network/       # 网络通信
│   └── ...
├── tests/             # 测试代码
├── examples/          # 示例代码
├── amdb-server        # 服务器启动脚本
├── amdb-cli           # CLI启动脚本
├── amdb.ini           # 配置文件
└── Makefile           # 构建文件
```

## 配置

配置文件 `amdb.ini` 包含所有可配置项：

- **网络配置**: 端口3888（默认），监听地址0.0.0.0
- **性能配置**: 批量大小3000，分片256
- **多线程配置**: 启用多线程，最大工作线程4
- **存储配置**: MemTable 10MB，文件大小256MB

详细配置说明请查看 [文档仓库](https://github.com/coretrusts/amdb-docs)。

## 文档

- **文档**: https://github.com/coretrusts/amdb-docs
- **发行版**: https://github.com/coretrusts/amdb-releases
- **多语言绑定**: https://github.com/coretrusts/amdb-bindings
- **脚本工具**: https://github.com/coretrusts/amdb-scripts

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 作者

CoreTrusts Organization
