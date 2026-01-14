# 区块链数据库演示和压力测试

## 概述

本文档演示如何使用AmDb存储和查询区块链数据，包括区块、交易和账户状态。

## 快速开始

### 1. 创建区块链数据库

```bash
python3 create_blockchain_db.py
```

这将创建：
- 11个区块（包括创世区块）
- 10个账户状态
- 50个交易索引

### 2. 运行压力测试

```bash
python3 blockchain_stress_test.py
```

压力测试将：
- 创建1000个区块
- 每个区块包含10笔交易
- 100个账户
- 总计11,100条记录

## 数据存储结构

### 键值设计

```
block:{block_number:010d}      # 区块数据
account:{account_id}            # 账户状态
tx:{tx_id}                     # 交易索引
```

### 示例数据

**区块数据** (`block:0000000001`):
```json
{
  "block_number": 1,
  "timestamp": 1768286107,
  "previous_hash": "10d852e0bc9c320b...",
  "merkle_root": "abc123...",
  "transactions": [
    {
      "tx_id": "tx_00001_000",
      "from": "account_000",
      "to": "account_001",
      "amount": 100,
      "fee": 1
    }
  ],
  "nonce": 1000,
  "difficulty": 2,
  "hash": "31b9f22c2b47535c..."
}
```

**账户数据** (`account:account_001`):
```json
{
  "account_id": "account_001",
  "balance": 11000,
  "nonce": 0,
  "last_transaction": null
}
```

**交易索引** (`tx:tx_00005_001`):
```json
{
  "tx_id": "tx_00005_001",
  "block_number": 5,
  "block_hash": "31b9f22c2b47535c...",
  "index_in_block": 1
}
```

## 文件存储结构

```
blockchain_db/
├── database.amdb          # 数据库元数据
├── shards/                # 分片目录（LSM树）
│   └── shard_00/
│       └── shard_00/
│           └── sstable_*.sst  # SSTable数据文件
├── bplus/                 # B+树索引
│   ├── tree.meta
│   └── node_*.bpt
├── merkle/                # Merkle树（数据完整性）
│   └── merkle_tree.mpt
├── wal/                   # 预写日志（崩溃恢复）
│   └── wal_*.wal
├── versions/              # 版本管理
│   └── versions.ver
└── indexes/               # 索引文件
    └── indexes.idx
```

### 文件类型说明

- **`.sst`**: SSTable数据文件（LSM树存储引擎）
- **`.bpt`**: B+树节点文件（快速随机读取索引）
- **`.mpt`**: Merkle树文件（数据完整性验证）
- **`.wal`**: 预写日志（Write-Ahead Log，崩溃恢复）
- **`.ver`**: 版本管理文件（数据版本历史）
- **`.idx`**: 索引文件（各种索引）
- **`.amdb`**: 数据库元数据文件

## 性能测试结果

### 写入性能

- **账户写入**: 27,330 记录/秒
- **区块+交易写入**: 11,787 记录/秒
- **总写入时间**: 0.937秒（11,100条记录）

### 读取性能

- **随机读取区块**: 172,506 次/秒
- **顺序读取区块**: 191,959 次/秒
- **随机读取账户**: 145,691 次/秒

### 数据规模

- **区块数**: 1,000
- **交易数**: 10,000
- **账户数**: 100
- **总记录数**: 11,100

## 使用示例

### Python API

```python
from src.amdb import Database
import json

# 连接数据库
db = Database(data_dir='./data/blockchain_db')

# 读取区块
block_key = b"block:0000000001"
block_data = db.get(block_key)
if block_data:
    block = json.loads(block_data.decode('utf-8'))
    print(f"区块号: {block['block_number']}")
    print(f"区块哈希: {block['hash']}")

# 读取账户
account_key = b"account:account_001"
account_data = db.get(account_key)
if account_data:
    account = json.loads(account_data.decode('utf-8'))
    print(f"账户余额: {account['balance']}")

# 查询所有区块
all_keys = db.version_manager.get_all_keys()
block_keys = [k for k in all_keys if k.startswith(b'block:')]
print(f"共有 {len(block_keys)} 个区块")
```

### CLI命令

```bash
# 启动CLI
python3 amdb-cli

# 连接数据库
connect blockchain_db

# 读取区块
get block:0000000001

# 查询所有区块
select * from block

# 查询所有账户
select * from account

# 查看统计信息
show stats
```

### GUI管理器

```bash
# 启动GUI
python3 amdb_manager.py

# 连接数据库
# 文件 -> 连接数据库 -> 选择 ./data/blockchain_db
```

## 数据验证

### 验证区块链完整性

```python
from src.amdb import Database
import json

db = Database(data_dir='./data/blockchain_db')

# 验证区块链
all_keys = db.version_manager.get_all_keys()
block_keys = [k for k in all_keys if k.startswith(b'block:')]
block_keys.sort()

previous_hash = "0" * 64
for block_key in block_keys:
    block_data = db.get(block_key)
    if block_data:
        block = json.loads(block_data.decode('utf-8'))
        if block['previous_hash'] != previous_hash:
            print(f"❌ 区块 {block['block_number']} 的前一个哈希不匹配")
            break
        previous_hash = block['hash']
        print(f"✓ 区块 {block['block_number']} 验证通过")
else:
    print("✓ 所有区块验证通过")
```

### 验证Merkle根

```python
# 获取Merkle根哈希
merkle_root = db.get_root_hash()
print(f"Merkle根: {merkle_root.hex()}")

# 验证数据完整性
key = b"block:0000000001"
value = db.get(key)
proof = db.get_with_proof(key)
is_valid = db.verify(key, value, proof[1])
print(f"数据完整性验证: {'通过' if is_valid else '失败'}")
```

## 最佳实践

### 1. 键命名规范

- 使用前缀区分数据类型：`block:`, `account:`, `tx:`
- 使用固定长度格式：`block:0000000001` 便于排序和范围查询
- 避免特殊字符，使用ASCII字符

### 2. 批量写入

```python
# 使用批量写入提高性能
items = [
    (b"block:0000000001", block1_data),
    (b"block:0000000002", block2_data),
    (b"block:0000000003", block3_data),
]
db.batch_put(items)
```

### 3. 数据刷新

```python
# 重要数据立即刷新
db.flush(async_mode=False)

# 批量数据异步刷新
db.flush(async_mode=True)
```

### 4. 分片配置

```python
# 大数据量启用分片
db = Database(
    data_dir='./data/blockchain_db',
    enable_sharding=True,
    shard_count=8  # 根据数据量调整
)
```

## 故障恢复

### WAL恢复

数据库崩溃后会自动从WAL文件恢复：

```python
# 数据库启动时会自动恢复
db = Database(data_dir='./data/blockchain_db')
# WAL文件会自动重放，恢复未提交的数据
```

### 版本回滚

```python
# 查看版本历史
history = db.get_history(b"block:0000000001")
for version in history:
    print(f"版本 {version['version']}: {version['timestamp']}")

# 读取指定版本
value = db.get(b"block:0000000001", version=5)
```

## 性能优化建议

1. **批量写入**: 使用`batch_put`而不是单个`put`
2. **异步刷新**: 非关键数据使用`flush(async_mode=True)`
3. **分片**: 大数据量启用分片存储
4. **索引**: 为常用查询创建索引
5. **缓存**: 频繁读取的数据可以缓存

## 总结

AmDb提供了完整的区块链数据存储解决方案：

- ✅ **高性能**: 写入11,787记录/秒，读取172,506次/秒
- ✅ **数据完整性**: Merkle树验证
- ✅ **版本管理**: 完整的数据历史
- ✅ **崩溃恢复**: WAL自动恢复
- ✅ **分片存储**: 支持大数据量
- ✅ **多格式支持**: JSON、XML、Binary等

适用于：
- 区块链节点数据存储
- 交易历史记录
- 账户状态管理
- 区块索引
- 智能合约状态

