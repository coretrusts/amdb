# AmDb 使用模式说明

## 问题解答

### Q: 配置中的IP+端口作用是什么？

**A**: IP+端口用于**网络服务模式**，允许客户端通过网络连接访问数据库服务器。

### Q: 在哪里运行数据库服务器并开启监听？

**A**: 使用以下命令启动数据库服务器：

```bash
# 方式1: 使用默认配置
python -m src.amdb.server

# 方式2: 指定配置文件
python -m src.amdb.server --config amdb.ini

# 方式3: 指定参数
python -m src.amdb.server --host 0.0.0.0 --port 3888 --data-dir ./data
```

服务器启动后会：
- 监听配置的IP和端口（默认：0.0.0.0:3888）
- 接受客户端连接
- 处理数据库操作请求

### Q: 管理器（GUI/CLI）如何通过IP+端口和数据库名称管理？

**A**: 目前GUI/CLI默认使用**本地文件模式**，但已支持网络连接。两种模式如下：

## 使用模式对比

### 模式1: 本地文件模式（当前默认）

**特点**：
- 直接访问本地文件系统
- 无需启动服务器
- 适合单机开发

**使用方式**：
```python
from src.amdb import Database

# 直接访问本地文件
db = Database(data_dir='./data/my_database')
db.put(b'key', b'value')
```

**CLI使用**：
```bash
amdb-cli --connect ./data/my_database
```

**GUI使用**：
- 选择"连接数据库"
- 选择数据目录
- 直接访问本地文件

### 模式2: 网络服务模式（已实现）

**特点**：
- 通过IP+端口连接服务器
- 支持多客户端同时访问
- 支持多数据库（通过数据库名称区分）
- 适合生产环境

**使用方式**：

1. **启动服务器**：
```bash
python -m src.amdb.server --host 0.0.0.0 --port 3888
```

2. **客户端连接**：
```python
from src.amdb.network import RemoteDatabase

# 通过网络连接
db = RemoteDatabase(
    host='127.0.0.1', 
    port=3888, 
    database='my_database'  # 数据库名称
)
db.connect()
db.put(b'key', b'value')
db.disconnect()
```

**CLI使用**（待实现）：
```bash
amdb-cli --host 127.0.0.1 --port 3888 --database my_database
```

**GUI使用**（待实现）：
- 选择"网络连接"
- 输入服务器IP和端口
- 选择数据库名称
- 通过网络协议访问

## 数据库名称管理

### 数据库注册表

AmDb使用数据库注册表管理多个数据库实例：

```python
from src.amdb.db_registry import DatabaseRegistry

registry = DatabaseRegistry()

# 注册数据库
registry.register_database(
    db_name='blockchain',           # 数据库名称
    data_dir='./data/blockchain',   # 数据目录
    description='区块链数据库'      # 描述
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

## 完整使用流程

### 场景1: 单机开发（本地文件模式）

```bash
# 1. 直接使用CLI
amdb-cli --connect ./data/my_database

# 2. 或使用GUI
python amdb_manager.py
# 选择数据目录连接
```

### 场景2: 多客户端访问（网络服务模式）

```bash
# 1. 启动服务器
python -m src.amdb.server --host 0.0.0.0 --port 3888

# 2. 客户端1连接
python -c "
from src.amdb.network import RemoteDatabase
db = RemoteDatabase('127.0.0.1', 3888, 'blockchain')
db.connect()
db.put(b'key1', b'value1')
"

# 3. 客户端2连接
python -c "
from src.amdb.network import RemoteDatabase
db = RemoteDatabase('127.0.0.1', 3888, 'blockchain')
db.connect()
value = db.get(b'key1')
print(value)
"
```

### 场景3: 区块链节点（网络服务模式）

每个节点运行自己的服务器：

```bash
# 节点1
python -m src.amdb.server --data-dir ./data/node1 --port 3888

# 节点2
python -m src.amdb.server --data-dir ./data/node2 --port 3889
```

## 配置说明

### 服务器配置（amdb.ini）

```ini
[network]
# 监听地址
host = 0.0.0.0          # 0.0.0.0表示监听所有网络接口
                        # 127.0.0.1表示仅本地访问

# 监听端口
port = 3888            # 使用不常用端口

# 最大连接数
max_connections = 100

# 超时时间（秒）
timeout = 30.0
```

## 总结

1. **IP+端口的作用**：用于网络服务模式，允许客户端通过网络连接数据库服务器

2. **服务器启动**：使用 `python -m src.amdb.server` 启动，监听配置的IP和端口

3. **管理器连接方式**：
   - **当前**：本地文件模式（直接访问文件系统）
   - **已实现**：网络服务模式（通过IP+端口+数据库名称）

4. **数据库名称**：通过数据库注册表管理，支持多数据库实例

## 更新日期

2026-01-13

