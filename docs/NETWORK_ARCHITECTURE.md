# AmDb 网络架构说明

## 概述

AmDb支持两种使用模式：
1. **本地文件模式**：直接访问本地文件系统（当前GUI/CLI的默认方式）
2. **网络服务模式**：通过IP+端口连接数据库服务器（类似MySQL）

## 架构设计

### 网络服务模式

```
┌─────────────┐        网络连接          ┌─────────────┐
│  客户端     │ ───────────────────────> │  服务器     │
│ (GUI/CLI)   │   IP:Port + Database     │ (amdb-server)│
└─────────────┘                          └─────────────┘
     │                                          │
     │                                          │
     └──────────────────────────────────────────┘
                   本地文件系统
```

### 数据库服务器

**启动服务器**：
```bash
# 方式1: 使用默认配置
python -m src.amdb.server

# 方式2: 指定配置
python -m src.amdb.server --config amdb.ini

# 方式3: 指定参数
python -m src.amdb.server --host 0.0.0.0 --port 3888 --data-dir ./data
```

**服务器功能**：
- 监听指定IP和端口（默认：0.0.0.0:3888）
- 处理客户端连接请求
- 支持多数据库（通过数据库名称区分）
- 提供PUT、GET、MERKLE_ROOT等操作

### 客户端连接

#### 方式1: 本地文件模式（当前默认）

```python
from src.amdb import Database

# 直接访问本地文件
db = Database(data_dir='./data/my_database')
db.put(b'key', b'value')
```

#### 方式2: 网络连接模式

```python
from src.amdb.network import RemoteDatabase

# 通过网络连接
db = RemoteDatabase(host='127.0.0.1', port=3888, database='my_database')
db.connect()
db.put(b'key', b'value')
db.disconnect()
```

## 配置说明

### 服务器配置（amdb.ini）

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

### 客户端配置

```ini
[client]
# 服务器地址
server_host = 127.0.0.1

# 服务器端口
server_port = 3888

# 默认数据库
default_database = my_database
```

## 数据库名称管理

### 数据库注册表

AmDb使用数据库注册表管理多个数据库实例：

```python
from src.amdb.db_registry import DatabaseRegistry

registry = DatabaseRegistry()

# 注册数据库
registry.register_database(
    db_name='blockchain',
    data_dir='./data/blockchain',
    description='区块链数据库'
)

# 通过名称获取路径
path = registry.get_database_path('blockchain')

# 列出所有数据库
databases = registry.list_databases()
```

### 自动注册

服务器启动时会自动扫描数据目录并注册数据库：

```python
registry.auto_register_from_data_dir('./data')
```

## GUI/CLI 网络连接支持

### CLI网络连接

```bash
# 连接本地服务器
amdb-cli --host 127.0.0.1 --port 3888 --database blockchain

# 连接远程服务器
amdb-cli --host 192.168.1.100 --port 3888 --database blockchain
```

### GUI网络连接

GUI管理器支持两种连接方式：

1. **本地文件模式**（当前）：
   - 选择数据目录
   - 直接访问本地文件

2. **网络连接模式**（待实现）：
   - 输入服务器IP和端口
   - 选择数据库名称
   - 通过网络协议访问

## 使用场景

### 场景1: 单机开发

使用本地文件模式，直接访问文件系统：
```python
db = Database(data_dir='./data/my_db')
```

### 场景2: 多客户端访问

启动服务器，多个客户端通过网络连接：
```bash
# 服务器
python -m src.amdb.server --host 0.0.0.0 --port 3888

# 客户端1
python -m src.amdb.cli --host 192.168.1.100 --port 3888

# 客户端2
python -m src.amdb.cli --host 192.168.1.100 --port 3888
```

### 场景3: 区块链节点

每个节点运行自己的服务器：
```bash
# 节点1
python -m src.amdb.server --data-dir ./data/node1 --port 3888

# 节点2
python -m src.amdb.server --data-dir ./data/node2 --port 3889
```

## 网络协议

### 消息格式

```
[消息长度(4字节)][消息头(9字节)][消息体(变长)]
```

消息头：
- 消息类型(1字节)
- 消息长度(4字节)
- 校验和(4字节)

### 支持的操作

- `PUT`: 写入数据
- `GET`: 读取数据
- `MERKLE_ROOT`: 获取Merkle根
- `PING`: 心跳检测

### 请求格式

```json
{
    "database": "blockchain",  // 数据库名称
    "key": "hex_string",       // 键（hex编码）
    "value": "hex_string"      // 值（hex编码，PUT时）
}
```

### 响应格式

```json
{
    "success": true,           // 操作是否成功
    "found": true,            // 数据是否找到（GET）
    "value": "hex_string",     // 值（GET）
    "root": "hex_string"      // Merkle根（MERKLE_ROOT）
}
```

## 安全考虑

1. **认证**：当前版本未实现，生产环境需要添加
2. **加密**：支持SSL/TLS（配置中已预留）
3. **访问控制**：支持数据库级别的访问控制（待实现）

## 更新日期

2026-01-13

