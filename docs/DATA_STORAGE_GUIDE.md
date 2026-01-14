# AmDb 数据存储指南

## 1. 数据持久化问题

### 问题说明
- **GUI插入数据后不保存**：`flush()`方法是异步的，调用后立即返回，数据可能还没写入磁盘
- **CLI读取不到GUI插入的数据**：因为数据还在MemTable中，没有刷新到SSTable文件

### 解决方案
1. **修复flush()方法**：确保同步完成，等待所有数据写入磁盘
2. **GUI自动flush**：在写入数据后自动调用flush并等待完成
3. **CLI连接时刷新**：连接数据库时自动刷新，确保看到最新数据

## 2. "表"的概念

AmDb是**键值存储数据库**，不是关系型数据库，没有传统意义上的"表"。

### 如何模拟"表"
使用**键前缀**来模拟表的概念：

```python
# 用户表
db.put(b'user:001', b'{"name": "张三", "age": 25}')
db.put(b'user:002', b'{"name": "李四", "age": 30}')

# 订单表
db.put(b'order:001', b'{"user_id": "001", "amount": 100.50}')
db.put(b'order:002', b'{"user_id": "002", "amount": 200.00}')

# 查询所有用户
all_keys = db.version_manager.get_all_keys()
user_keys = [k for k in all_keys if k.startswith(b'user:')]
```

### CLI中的"表"
CLI的`show tables`命令显示的是**键前缀**（模拟表）：

```bash
amdb> show tables
表（键前缀）列表:
  user: 100 条记录
  order: 50 条记录
  transaction: 200 条记录
```

## 3. 值的存储格式

### 值可以是任意字节
AmDb存储的是**字节数据**，不是JSON字符串。JSON只是使用方式之一：

```python
# 方式1：纯字符串
db.put(b'key1', b'plain string')

# 方式2：JSON字符串
import json
data = {'name': 'test', 'value': 123}
db.put(b'key2', json.dumps(data).encode())

# 方式3：二进制数据
db.put(b'key3', b'\x00\x01\x02\x03')

# 方式4：序列化对象
import pickle
obj = {'complex': 'object'}
db.put(b'key4', pickle.dumps(obj))
```

### 读取数据
```python
# 读取纯字符串
value = db.get(b'key1')  # b'plain string'

# 读取JSON
value = db.get(b'key2')
data = json.loads(value.decode())  # {'name': 'test', 'value': 123}

# 读取二进制
value = db.get(b'key3')  # b'\x00\x01\x02\x03'

# 读取序列化对象
value = db.get(b'key4')
obj = pickle.loads(value)  # {'complex': 'object'}
```

## 4. 文件后缀和压缩

### 当前状态
- ✅ **文件后缀已定义**：`.sst` (SSTable), `.wal` (WAL), `.bpt` (B+Tree), `.mpt` (Merkle Tree), `.ver` (Version), `.idx` (Index)
- ✅ **压缩类型已定义**：`NONE`, `SNAPPY`, `LZ4`
- ❌ **压缩未实现**：SSTable写入时没有使用压缩
- ❌ **文件格式未使用**：SSTable没有使用`file_format.py`中定义的格式

### 文件格式定义
在`src/amdb/storage/file_format.py`中定义了：
- `FileMagic`：文件魔数（SST, BPT, MPT, WAL, VER, IDX）
- `CompressionType`：压缩类型（NONE, SNAPPY, LZ4）
- `SSTableFormat`：SSTable文件格式（header, entry, footer）

### 需要修复
1. **SSTable使用标准格式**：使用`SSTableFormat`写入文件
2. **实现数据压缩**：在写入SSTable时使用Snappy或LZ4压缩
3. **文件魔数验证**：读取时验证文件魔数，确保文件完整性

## 5. 数据构建和读写

### 写入数据
```python
from src.amdb import Database

# 创建数据库实例
db = Database(data_dir='./data/my_db')

# 单条写入
db.put(b'user:001', b'{"name": "张三"}')

# 批量写入（高性能）
items = [
    (b'user:001', b'{"name": "张三"}'),
    (b'user:002', b'{"name": "李四"}'),
    (b'user:003', b'{"name": "王五"}'),
]
db.batch_put(items)

# 确保数据持久化
db.flush()  # 强制刷新到磁盘
```

### 读取数据
```python
# 单条读取
value = db.get(b'user:001')

# 范围查询
results = db.range_query(b'user:001', b'user:999')

# 版本查询
history = db.get_history(b'user:001')
```

### 数据组织建议
```python
# 1. 使用键前缀组织数据
# 用户数据
db.put(b'user:001:profile', b'{"name": "张三"}')
db.put(b'user:001:settings', b'{"theme": "dark"}')

# 2. 使用复合键
# 订单数据
db.put(b'order:2024:001', b'{"amount": 100.50}')
db.put(b'order:2024:002', b'{"amount": 200.00}')

# 3. 使用索引键
# 用户ID索引
db.put(b'index:user:by_name:张三', b'user:001')
db.put(b'index:user:by_name:李四', b'user:002')
```

## 6. 数据目录结构

```
data/
├── my_db/
│   ├── lsm/                    # LSM树数据
│   │   ├── sstable_*.sst      # SSTable文件（.sst后缀）
│   │   └── shard_00/           # 分片数据
│   ├── bplus/                  # B+树数据
│   │   └── node_*.bpt          # B+树节点文件（.bpt后缀）
│   ├── merkle/                 # Merkle树数据
│   │   └── tree_*.mpt          # Merkle树文件（.mpt后缀）
│   ├── versions/               # 版本数据
│   │   └── version_*.ver        # 版本文件（.ver后缀）
│   ├── indexes/                # 索引数据
│   │   └── index_*.idx         # 索引文件（.idx后缀）
│   └── wal/                    # WAL日志
│       └── wal_*.wal           # WAL文件（.wal后缀）
```

## 7. 下一步修复计划

1. **修复flush()同步问题**
   - 修改`_flush_memtable()`为同步方法
   - 确保flush()等待所有数据写入完成

2. **实现数据压缩**
   - 在SSTable写入时使用Snappy或LZ4压缩
   - 添加压缩配置选项

3. **使用标准文件格式**
   - SSTable使用`SSTableFormat`写入
   - 添加文件魔数验证

4. **改进GUI和CLI**
   - GUI写入后自动flush并等待完成
   - CLI连接时自动刷新数据

