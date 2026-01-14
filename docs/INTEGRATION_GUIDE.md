# AmDb 集成到Python程序指南

## 概述

AmDb可以作为Python库直接集成到你的区块链项目中，无需使用可执行文件。

## 可执行文件 vs Python库

### 可执行文件（打包后）

- **位置**: `dist/darwin_x86_64/amdb-cli`, `amdb-manager`
- **用途**: 命令行工具和GUI管理器
- **使用场景**: 数据库管理、调试、手动操作

### Python库（开发使用）

- **位置**: `src/amdb/`
- **用途**: 在Python程序中直接使用
- **使用场景**: 区块链应用、自动化脚本、集成到项目

## 在Python程序中使用

### 方式1: 直接导入（开发环境）

```python
from src.amdb import Database

# 创建数据库
db = Database(data_dir='./data/my_blockchain')

# 使用数据库
db.put(b'key', b'value')
value = db.get(b'key')
```

### 方式2: 安装为Python包

```bash
# 安装到Python环境
pip install -e .

# 或
python setup.py install
```

然后使用：

```python
from amdb import Database

db = Database(data_dir='./data/my_blockchain')
```

### 方式3: 添加到项目路径

```python
import sys
from pathlib import Path

# 添加AmDb到Python路径
amdb_path = Path(__file__).parent / 'path/to/AmDb/src'
sys.path.insert(0, str(amdb_path))

from amdb import Database
```

## 区块链集成示例

### 基本使用

```python
from src.amdb import Database
import json
import hashlib

# 创建区块链数据库
db = Database(data_dir='./data/blockchain')

# 存储区块
def store_block(block_data):
    block_json = json.dumps(block_data).encode()
    block_hash = hashlib.sha256(block_json).hexdigest()
    key = f"block:{block_hash}".encode()
    db.put(key, block_json)
    return block_hash

# 存储交易
def store_transaction(tx_data):
    tx_json = json.dumps(tx_data).encode()
    tx_hash = hashlib.sha256(tx_json).hexdigest()
    key = f"tx:{tx_hash}".encode()
    db.put(key, tx_json)
    return tx_hash

# 批量存储（高性能）
def store_blocks_batch(blocks):
    items = []
    for block in blocks:
        block_json = json.dumps(block).encode()
        block_hash = hashlib.sha256(block_json).hexdigest()
        key = f"block:{block_hash}".encode()
        items.append((key, block_json))
    
    success, merkle_root = db.batch_put(items)
    db.flush()  # 刷新到磁盘
    return success
```

### 完整区块链示例

```python
from src.amdb import Database
import json
import hashlib
import time

class BlockchainDB:
    """区块链数据库封装"""
    
    def __init__(self, data_dir='./data/blockchain'):
        self.db = Database(data_dir=data_dir)
    
    def add_block(self, block_data):
        """添加区块"""
        block_json = json.dumps(block_data, sort_keys=True).encode()
        block_hash = hashlib.sha256(block_json).hexdigest()
        
        # 存储区块
        block_key = f"block:{block_hash}".encode()
        self.db.put(block_key, block_json)
        
        # 存储索引
        height_key = f"height:{block_data['height']}".encode()
        self.db.put(height_key, block_hash.encode())
        
        # 更新最新区块
        self.db.put(b"latest:block", block_hash.encode())
        
        return block_hash
    
    def get_block(self, block_hash):
        """获取区块"""
        block_key = f"block:{block_hash}".encode()
        data = self.db.get(block_key)
        if data:
            return json.loads(data.decode())
        return None
    
    def get_latest_block(self):
        """获取最新区块"""
        latest_hash = self.db.get(b"latest:block")
        if latest_hash:
            return self.get_block(latest_hash.decode())
        return None
    
    def add_transaction(self, tx_data):
        """添加交易"""
        tx_json = json.dumps(tx_data, sort_keys=True).encode()
        tx_hash = hashlib.sha256(tx_json).hexdigest()
        
        tx_key = f"tx:{tx_hash}".encode()
        self.db.put(tx_key, tx_json)
        
        return tx_hash
    
    def flush(self):
        """刷新到磁盘"""
        self.db.flush()

# 使用示例
if __name__ == "__main__":
    # 创建区块链数据库
    blockchain = BlockchainDB()
    
    # 添加创世区块
    genesis = {
        "height": 0,
        "timestamp": int(time.time()),
        "prev_hash": "0" * 64,
        "transactions": []
    }
    genesis_hash = blockchain.add_block(genesis)
    print(f"创世区块: {genesis_hash}")
    
    # 添加交易
    tx = {
        "from": "address1",
        "to": "address2",
        "amount": 100
    }
    tx_hash = blockchain.add_transaction(tx)
    print(f"交易: {tx_hash}")
    
    # 刷新到磁盘
    blockchain.flush()
```

## 性能优化建议

### 1. 使用批量写入

```python
# 批量写入（高性能）
items = [
    (b'key1', b'value1'),
    (b'key2', b'value2'),
    # ... 更多数据
]
db.batch_put(items)
db.flush()
```

### 2. 异步刷新

```python
# 异步刷新（不阻塞）
db.flush(async_mode=True)
```

### 3. 配置优化

```python
from src.amdb import Database, DatabaseConfig

# 自定义配置
config = DatabaseConfig()
config.batch_max_size = 10000  # 增大批量大小
config.threading_enable = True
config.threading_max_workers = 8

db = Database(data_dir='./data/blockchain', config_path=None)
# 注意：需要在创建Database前设置config
```

## 在区块链项目中的集成

### 项目结构

```
your_blockchain_project/
├── blockchain/
│   ├── __init__.py
│   ├── block.py
│   ├── transaction.py
│   └── database.py      # 使用AmDb
├── src/                 # 或添加AmDb的src目录
│   └── amdb/
├── data/                # 数据库数据目录
└── main.py
```

### database.py 示例

```python
# blockchain/database.py
from src.amdb import Database
import json
import hashlib

class BlockchainDatabase:
    """区块链数据库"""
    
    def __init__(self, data_dir='./data/blockchain'):
        self.db = Database(data_dir=data_dir)
    
    def save_block(self, block):
        """保存区块"""
        block_data = {
            "height": block.height,
            "timestamp": block.timestamp,
            "prev_hash": block.prev_hash,
            "merkle_root": block.merkle_root,
            "transactions": [tx.to_dict() for tx in block.transactions],
            "nonce": block.nonce
        }
        
        block_json = json.dumps(block_data, sort_keys=True).encode()
        block_hash = hashlib.sha256(block_json).hexdigest()
        
        # 存储
        key = f"block:{block_hash}".encode()
        self.db.put(key, block_json)
        
        # 索引
        height_key = f"height:{block.height}".encode()
        self.db.put(height_key, block_hash.encode())
        
        # 最新区块
        self.db.put(b"latest:block", block_hash.encode())
        
        return block_hash
    
    def load_block(self, block_hash):
        """加载区块"""
        key = f"block:{block_hash}".encode()
        data = self.db.get(key)
        if data:
            return json.loads(data.decode())
        return None
    
    def get_latest_block_hash(self):
        """获取最新区块哈希"""
        return self.db.get(b"latest:block")
    
    def save_transaction(self, tx):
        """保存交易"""
        tx_data = tx.to_dict()
        tx_json = json.dumps(tx_data, sort_keys=True).encode()
        tx_hash = hashlib.sha256(tx_json).hexdigest()
        
        key = f"tx:{tx_hash}".encode()
        self.db.put(key, tx_json)
        
        return tx_hash
    
    def flush(self):
        """刷新到磁盘"""
        self.db.flush()
```

## 配置数据库

### 创建配置文件

```ini
# blockchain_config.ini
[database]
data_dir = ./data/blockchain
enable_sharding = True
shard_count = 256

[batch]
max_size = 10000

[threading]
enable = True
max_workers = 8
```

### 使用配置文件

```python
from src.amdb import Database

db = Database(
    data_dir='./data/blockchain',
    config_path='./blockchain_config.ini'
)
```

## 数据持久化

### 自动持久化

```python
# 写入后自动刷新（异步）
db.put(b'key', b'value')
db.flush(async_mode=True)  # 异步刷新，不阻塞
```

### 手动持久化

```python
# 批量写入后统一刷新
db.batch_put(items)
db.flush()  # 同步刷新，确保数据写入磁盘
```

## 查询和检索

### 按前缀查询

```python
# 获取所有区块
all_keys = db.version_manager.get_all_keys()
block_keys = [k for k in all_keys if k.startswith(b'block:')]

# 获取区块数据
for key in block_keys:
    block_data = db.get(key)
    # 处理区块数据
```

### 使用索引

```python
# 按高度获取区块
height = 100
height_key = f"height:{height}".encode()
block_hash = db.get(height_key)
if block_hash:
    block = db.get(f"block:{block_hash.decode()}".encode())
```

## 最佳实践

1. **批量写入**: 使用`batch_put`提高性能
2. **定期刷新**: 重要数据后立即`flush()`
3. **配置优化**: 根据数据量调整分片和批量大小
4. **错误处理**: 添加异常处理确保数据安全
5. **版本管理**: 利用AmDb的版本管理功能追踪历史

## 完整示例

参考 `examples/blockchain_usage.py` 查看完整示例。

## 更新日期

2026-01-13

