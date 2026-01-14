# 远程操作支持说明

## 概述

AmDb现在完全支持通过IP+端口+数据库名称进行远程连接，所有操作（包括统计信息、配置管理等）都可以通过服务器端获取。

## 已实现的远程操作

### 1. 基础操作
- ✅ `PUT` - 写入数据
- ✅ `GET` - 读取数据
- ✅ `DELETE` - 删除数据
- ✅ `BATCH_PUT` - 批量写入

### 2. 查询操作
- ✅ `GET_ALL_KEYS` - 获取所有键
- ✅ `GET_STATS` - 获取统计信息
- ✅ `GET_CONFIG` - 获取配置信息
- ✅ `MERKLE_ROOT` - 获取Merkle根

## 网络协议扩展

### 新增消息类型

```python
GET_STATS = 10          # 获取统计信息
GET_ALL_KEYS = 11       # 获取所有键
BATCH_PUT = 12          # 批量写入
DELETE = 13             # 删除键
GET_CONFIG = 14         # 获取配置
SET_CONFIG = 15         # 设置配置（预留）
```

## 服务器端实现

服务器端现在可以处理所有远程操作请求：

```python
# 服务器端自动处理
- GET_STATS: 返回数据库统计信息
- GET_ALL_KEYS: 返回所有键列表
- GET_CONFIG: 返回数据库配置
- BATCH_PUT: 批量写入数据
- DELETE: 删除键
```

## 客户端实现

### RemoteDatabase 新增方法

```python
# 统计信息
stats = remote_db.get_stats()
# 返回: {'total_keys': 1000, 'current_version': 5, ...}

# 所有键
all_keys = remote_db.get_all_keys()
# 返回: [b'key1', b'key2', ...]

# 配置信息
config = remote_db.get_config()
# 返回: {'data_dir': '...', 'network_port': 3888, ...}

# 批量写入
success, merkle_root = remote_db.batch_put(items)
# items: [(b'key1', b'value1'), (b'key2', b'value2'), ...]

# 删除
success = remote_db.delete(key)
```

## CLI 支持

CLI现在完全支持远程操作：

```bash
# 连接远程服务器
> connect --host 127.0.0.1 --port 3888 --database blockchain
✓ 已连接到远程数据库: 127.0.0.1:3888/blockchain

# 查看统计信息（从服务器获取）
> show stats
数据库统计信息:
总键数: 10000
当前版本: 100
...

# 查看配置（从服务器获取）
> show config
当前配置:
数据目录: ./data/blockchain
网络端口: 3888
...

# 所有操作都通过服务器
> put key1 "value1"
✓ 写入成功

> get key1
✓ 找到数据: value1

> show keys
显示所有键（从服务器获取）
```

## GUI 支持

GUI现在完全支持远程操作：

1. **连接对话框**：
   - 选择"远程服务器"模式
   - 输入IP、端口、数据库名称
   - 连接后所有操作通过服务器

2. **数据浏览**：
   - 自动从服务器获取所有键
   - 显示统计信息（从服务器获取）
   - 支持搜索、分页等

3. **配置管理**：
   - 从服务器加载配置（只读）
   - 显示服务器端配置信息

4. **性能监控**：
   - 显示服务器端统计信息

## 统一接口包装器

创建了`DatabaseWrapper`类，统一本地和远程接口：

```python
from src.amdb.gui_manager_remote_helpers import DatabaseWrapper

# 自动处理本地/远程
wrapper = DatabaseWrapper(db=local_db)  # 本地
wrapper = DatabaseWrapper(remote_db=remote_db)  # 远程

# 统一接口
stats = wrapper.get_stats()
all_keys = wrapper.get_all_keys()
config = wrapper.get_config()
value = wrapper.get(key)
success, _ = wrapper.put(key, value)
```

## 使用示例

### 完整远程操作流程

```python
from src.amdb.network import RemoteDatabase

# 1. 连接远程服务器
db = RemoteDatabase('127.0.0.1', 3888, database='blockchain')
db.connect()

# 2. 获取统计信息
stats = db.get_stats()
print(f"总键数: {stats['total_keys']}")

# 3. 获取所有键
all_keys = db.get_all_keys()
print(f"共有 {len(all_keys)} 个键")

# 4. 获取配置
config = db.get_config()
print(f"数据目录: {config['data_dir']}")

# 5. 写入数据
db.put(b'key1', b'value1')

# 6. 批量写入
items = [(b'key2', b'value2'), (b'key3', b'value3')]
success, merkle_root = db.batch_put(items)

# 7. 读取数据
value = db.get(b'key1')

# 8. 断开连接
db.disconnect()
```

## 总结

✅ **所有操作都支持远程连接**：
- 统计信息：通过`GET_STATS`从服务器获取
- 配置管理：通过`GET_CONFIG`从服务器获取
- 数据查询：通过`GET_ALL_KEYS`从服务器获取
- 数据操作：通过`PUT`/`GET`/`DELETE`/`BATCH_PUT`操作

✅ **CLI和GUI完全支持**：
- 自动识别本地/远程连接
- 统一接口，无需区分操作方式

✅ **服务器端完整实现**：
- 所有操作都在服务器端处理
- 支持多数据库（通过数据库名称区分）

## 更新日期

2026-01-13

