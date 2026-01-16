# AmDb 使用指南

## 快速开始

### 1. 基本读写操作（推荐方式）

```python
from src.amdb.database import Database

# 连接数据库
db = Database(data_dir="./data/my_db")

# 写入数据
db.put(b"key1", b"value1")
db.put(b"key2", b"value2")

# 读取数据
value = db.get(b"key1")
print(value)  # b'value1'

# 删除数据（标记删除）
db.delete(b"key1")

# 刷新到磁盘（可选，数据会异步持久化）
db.flush(async_mode=True)  # 异步模式，不阻塞
```

### 2. 批量写入（高性能，推荐）

```python
# 批量写入，性能更好
items = [
    (b"key1", b"value1"),
    (b"key2", b"value2"),
    (b"key3", b"value3"),
]

success, merkle_root = db.batch_put(items)
if success:
    print(f"批量写入成功，Merkle根: {merkle_root.hex()[:16]}...")
    
    # 可选：刷新到磁盘
    db.flush(async_mode=True)  # 异步模式，不阻塞
```

### 3. 事务操作（需要ACID保证时使用）

```python
# 开始事务
tx = db.begin_transaction()

try:
    # 在事务中写入数据
    tx.put(b"key1", b"value1")
    tx.put(b"key2", b"value2")
    tx.delete(b"key3")
    
    # 提交事务（会自动flush）
    success = db.commit_transaction(tx, auto_flush=True)
    if success:
        print("事务提交成功")
    else:
        print("事务提交失败")
except Exception as e:
    # 发生错误，中止事务
    db.abort_transaction(tx)
    print(f"事务失败: {e}")
```

**注意**：
- 事务主要用于需要ACID保证的场景
- 对于简单的读写操作，直接使用 `put()` 和 `get()` 即可
- 事务提交时会自动flush，无需手动调用

### 4. Flush策略

#### 异步模式（推荐，不阻塞）

```python
# 异步flush，不阻塞主流程
db.flush(async_mode=True)
```

#### 同步模式（确保完全持久化）

```python
# 同步flush，等待所有数据写入完成
db.flush(async_mode=False, force_sync=True)
```

#### 不调用flush（数据会自动持久化）

```python
# 数据会异步持久化，无需手动flush
db.put(b"key1", b"value1")
# 数据已经在内存中，可以立即读取
value = db.get(b"key1")  # 立即可以读取到
```

**重要提示**：
- 默认情况下，数据写入后会立即在内存中可用
- `flush()` 只是确保数据持久化到磁盘，不影响读取
- 对于高性能场景，建议使用 `async_mode=True`
- 只有在需要确保数据完全持久化时才使用 `force_sync=True`

## 常见问题

### Q1: 为什么需要事务？

**A**: 事务主要用于需要ACID保证的场景：
- 多个操作需要原子性（要么全部成功，要么全部失败）
- 需要隔离性（并发控制）
- 需要一致性保证

**对于简单的读写操作，不需要事务**：
```python
# 简单操作，不需要事务
db.put(b"key1", b"value1")
value = db.get(b"key1")
```

### Q2: flush太慢怎么办？

**A**: 使用异步模式：
```python
# 异步flush，不阻塞
db.flush(async_mode=True)
```

或者不调用flush，数据会自动异步持久化：
```python
# 数据会异步持久化，无需手动flush
db.put(b"key1", b"value1")
```

### Q3: 数据写入后能立即读取吗？

**A**: 可以！数据写入后会立即在内存中可用：
```python
db.put(b"key1", b"value1")
value = db.get(b"key1")  # 立即可以读取到，无需flush
```

### Q4: 多个连接能实时看到数据变更吗？

**A**: 可以！系统会自动检测文件更新：
```python
# 连接1
db1 = Database(data_dir="./data/my_db")
db1.put(b"key1", b"value1")
db1.flush()

# 连接2（无需重新连接）
db2 = Database(data_dir="./data/my_db")
value = db2.get(b"key1")  # 自动检测到文件更新，能读取到最新数据
```

### Q5: 批量写入和事务的区别？

**A**: 
- **批量写入** (`batch_put`): 高性能，适合大量数据写入，但不保证原子性
- **事务** (`begin_transaction`): 保证ACID，适合需要原子性的场景

```python
# 批量写入（高性能）
items = [(b"key1", b"value1"), (b"key2", b"value2")]
db.batch_put(items)

# 事务（ACID保证）
tx = db.begin_transaction()
tx.put(b"key1", b"value1")
tx.put(b"key2", b"value2")
db.commit_transaction(tx)
```

## 最佳实践

### 1. 简单读写场景

```python
# 推荐：直接使用put/get，无需事务
db.put(b"key1", b"value1")
value = db.get(b"key1")
```

### 2. 批量写入场景

```python
# 推荐：使用batch_put，性能更好
items = [(b"key1", b"value1"), (b"key2", b"value2")]
db.batch_put(items)
db.flush(async_mode=True)  # 异步flush
```

### 3. 需要ACID保证的场景

```python
# 推荐：使用事务
tx = db.begin_transaction()
try:
    tx.put(b"key1", b"value1")
    tx.put(b"key2", b"value2")
    db.commit_transaction(tx, auto_flush=True)
except:
    db.abort_transaction(tx)
```

### 4. 高性能场景

```python
# 推荐：批量写入 + 异步flush
items = [(b"key1", b"value1"), (b"key2", b"value2")]
db.batch_put(items)
db.flush(async_mode=True)  # 不阻塞
```

## 区块链应用接入示例

```python
from src.amdb.database import Database

# 连接数据库
db = Database(data_dir="./data/blockchain_db")

# 方式1：简单写入（推荐，无需事务）
def add_transaction(tx_hash, tx_data):
    key = f"tx:{tx_hash}".encode()
    db.put(key, tx_data)
    # 可选：异步flush
    db.flush(async_mode=True)

# 方式2：批量写入（高性能）
def add_transactions_batch(transactions):
    items = [(f"tx:{tx_hash}".encode(), tx_data) 
             for tx_hash, tx_data in transactions]
    db.batch_put(items)
    db.flush(async_mode=True)

# 方式3：事务写入（需要ACID保证时）
def add_transaction_with_tx(tx_hash, tx_data):
    tx = db.begin_transaction()
    try:
        key = f"tx:{tx_hash}".encode()
        tx.put(key, tx_data)
        # 提交事务（会自动flush）
        db.commit_transaction(tx, auto_flush=True)
    except Exception as e:
        db.abort_transaction(tx)
        raise e

# 读取数据
def get_transaction(tx_hash):
    key = f"tx:{tx_hash}".encode()
    return db.get(key)
```

## 总结

1. **简单读写**：直接使用 `put()` 和 `get()`，无需事务
2. **批量写入**：使用 `batch_put()`，性能更好
3. **需要ACID**：使用事务 `begin_transaction()` 和 `commit_transaction()`
4. **flush策略**：使用 `async_mode=True` 避免阻塞
5. **数据实时性**：系统会自动检测文件更新，无需重新连接

