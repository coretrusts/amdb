# AmDb 快速集成指南

## 可执行文件位置

### 打包后的可执行文件

1. **CLI命令行工具**: `dist/darwin_x86_64/amdb-cli` (macOS) 或 `dist/windows_x86_64/amdb-cli.exe` (Windows)
2. **GUI管理器**: `dist/darwin_x86_64/amdb-manager` (macOS) 或 `dist/windows_x86_64/amdb-manager.exe` (Windows)
3. **服务器**: 在分发包中的 `amdb-server` 脚本

**注意**: 这些可执行文件主要用于**数据库管理**，不是用于在Python程序中调用。

## 在Python程序中使用（推荐）

### 方式1: 直接导入（最简单）

```python
# 在你的区块链项目中
import sys
from pathlib import Path

# 添加AmDb到Python路径
amdb_path = Path(__file__).parent.parent / 'AmDb' / 'src'
sys.path.insert(0, str(amdb_path))

# 导入使用
from amdb import Database

# 创建数据库
db = Database(data_dir='./data/my_blockchain')

# 使用数据库
db.put(b'block:001', b'block_data')
value = db.get(b'block:001')
```

### 方式2: 安装为Python包

```bash
# 在AmDb目录中
pip install -e .

# 然后在你的项目中
from amdb import Database
db = Database(data_dir='./data/my_blockchain')
```

### 方式3: 复制到项目

```bash
# 将AmDb的src目录复制到你的项目
cp -r AmDb/src your_project/amdb_lib

# 在项目中使用
from amdb_lib.amdb import Database
```

## 区块链使用示例

### 完整示例

参考 `examples/blockchain_integration.py`

### 快速开始

```python
from src.amdb import Database
import json
import hashlib

# 1. 创建数据库
db = Database(data_dir='./data/blockchain')

# 2. 存储区块
def store_block(block_data):
    block_json = json.dumps(block_data).encode()
    block_hash = hashlib.sha256(block_json).hexdigest()
    key = f"block:{block_hash}".encode()
    db.put(key, block_json)
    return block_hash

# 3. 存储交易
def store_transaction(tx_data):
    tx_json = json.dumps(tx_data).encode()
    tx_hash = hashlib.sha256(tx_json).hexdigest()
    key = f"tx:{tx_hash}".encode()
    db.put(key, tx_json)
    return tx_hash

# 4. 批量存储（高性能）
def store_batch(items):
    db.batch_put(items)
    db.flush()  # 刷新到磁盘

# 5. 查询数据
def get_block(block_hash):
    key = f"block:{block_hash}".encode()
    data = db.get(key)
    if data:
        return json.loads(data.decode())
    return None
```

## 项目结构建议

```
your_blockchain_project/
├── blockchain/
│   ├── __init__.py
│   ├── block.py
│   ├── transaction.py
│   └── database.py      # 使用AmDb
├── AmDb/                 # AmDb源码（或通过pip安装）
│   └── src/
│       └── amdb/
├── data/                 # 数据库数据目录
│   └── blockchain/
└── main.py
```

## database.py 示例

```python
# blockchain/database.py
from src.amdb import Database
import json
import hashlib

class BlockchainDB:
    def __init__(self, data_dir='./data/blockchain'):
        self.db = Database(data_dir=data_dir)
    
    def save_block(self, block):
        """保存区块"""
        block_data = block.to_dict()
        block_json = json.dumps(block_data).encode()
        block_hash = hashlib.sha256(block_json).hexdigest()
        
        key = f"block:{block_hash}".encode()
        self.db.put(key, block_json)
        
        # 索引
        height_key = f"height:{block.height}".encode()
        self.db.put(height_key, block_hash.encode())
        
        return block_hash
    
    def get_block(self, block_hash):
        """获取区块"""
        key = f"block:{block_hash}".encode()
        data = self.db.get(key)
        if data:
            return json.loads(data.decode())
        return None
    
    def flush(self):
        """刷新到磁盘"""
        self.db.flush()
```

## 性能优化

### 批量写入

```python
# 批量写入（推荐）
items = []
for block in blocks:
    block_json = json.dumps(block.to_dict()).encode()
    block_hash = hashlib.sha256(block_json).hexdigest()
    items.append((f"block:{block_hash}".encode(), block_json))

db.batch_put(items)
db.flush()
```

### 异步刷新

```python
# 异步刷新（不阻塞主流程）
db.put(b'key', b'value')
db.flush(async_mode=True)
```

## 配置

### 创建配置文件

```ini
# blockchain.ini
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

### 使用配置

```python
from src.amdb import Database

db = Database(
    data_dir='./data/blockchain',
    config_path='./blockchain.ini'
)
```

## 运行示例

```bash
# 运行完整示例
python3 examples/blockchain_integration.py

# 运行基础示例
python3 examples/blockchain_usage.py
```

## 更多信息

- 详细集成指南: `docs/INTEGRATION_GUIDE.md`
- 完整示例: `examples/blockchain_integration.py`
- API文档: `docs/API.md`

