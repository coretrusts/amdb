# AmDb 数据库创建和使用指南

## 正确的数据库创建方法

### ✅ 标准方法（推荐）

```python
from src.amdb import Database

# 方法1: 指定数据目录
db = Database(data_dir="./data/my_database")

# 方法2: 使用配置文件
db = Database(config_path="./amdb.ini", data_dir="./data/my_database")

# 方法3: 使用默认配置
db = Database()  # 使用配置文件中的默认数据目录
```

### ✅ 数据库创建时会自动创建：

1. **database.amdb** - 数据库元数据文件（**必需**）
2. **versions/** - 版本管理器数据目录
3. **lsm/** - LSM树数据目录
4. **wal/** - WAL日志目录
5. **bplus/** - B+树数据目录
6. **merkle/** - Merkle树数据目录
7. **indexes/** - 索引数据目录

### ⚠️ 重要说明

**database.amdb 文件是必需的！**

- ✅ 数据库创建时会**自动创建** `database.amdb` 文件
- ✅ 该文件包含数据库元数据（描述、统计信息、配置等）
- ✅ 该文件用于数据库识别和扫描
- ✅ 如果文件不存在，数据库会在初始化时自动创建

### ❌ 错误的使用方法

```python
# ❌ 错误：只创建目录，不初始化Database
import os
os.makedirs("./data/my_db", exist_ok=True)
# 这样不会创建 database.amdb 文件！

# ✅ 正确：使用Database类初始化
from src.amdb import Database
db = Database(data_dir="./data/my_db")
# 这样会自动创建所有必需的文件和目录
```

## 数据库文件结构

创建数据库后，目录结构应该是：

```
data/my_database/
├── database.amdb          # 数据库元数据文件（必需）
├── versions/              # 版本管理器数据
│   └── versions.ver        # 版本数据文件（写入数据后创建）
├── lsm/                   # LSM树数据
│   └── *.sst              # SSTable文件（写入数据后创建）
├── wal/                   # WAL日志
│   └── *.wal              # WAL日志文件（写入数据后创建）
├── bplus/                 # B+树数据
│   └── *.bpt              # B+树文件（写入数据后创建）
├── merkle/                # Merkle树数据
│   └── merkle_tree.mpt    # Merkle树文件（写入数据后创建）
└── indexes/               # 索引数据
    └── indexes.idx        # 索引文件（写入数据后创建）
```

## 验证数据库创建

### Python代码验证

```python
from src.amdb import Database
from pathlib import Path

# 创建数据库
db = Database(data_dir="./data/test_db")

# 验证文件结构
data_dir = Path("./data/test_db")

# 检查 database.amdb
amdb_file = data_dir / "database.amdb"
print(f"database.amdb 存在: {amdb_file.exists()}")

# 检查所有目录
required_dirs = ['versions', 'lsm', 'wal', 'bplus', 'merkle', 'indexes']
for d in required_dirs:
    dir_path = data_dir / d
    print(f"{d}/ 存在: {dir_path.exists()}")
```

### CLI验证

```bash
# 创建数据库
python3 amdb-cli
create database test_db

# 检查文件
ls -la data/test_db/
# 应该看到 database.amdb 文件和所有目录
```

### GUI验证

1. 启动GUI：`python3 amdb_manager.py`
2. 文件 → 创建数据库
3. 设置数据库名称和路径
4. 创建后，检查数据目录，应该看到 `database.amdb` 文件和所有目录

## 常见问题

### Q1: database.amdb 文件不存在？

**原因：**
- 没有使用 `Database()` 类初始化
- 只创建了目录，没有初始化数据库

**解决方法：**
```python
# ✅ 正确：使用Database类
from src.amdb import Database
db = Database(data_dir="./data/my_db")
# 会自动创建 database.amdb 文件
```

### Q2: 为什么有些目录是空的？

**原因：**
- 这些目录在创建数据库时就会创建
- 但数据文件（如 `versions.ver`、`indexes.idx`）只有在写入数据后才会创建

**这是正常的！** 目录结构已完整，数据文件会在首次写入时创建。

### Q3: 如何确保数据库结构完整？

**方法：**
```python
from src.amdb import Database

# 创建数据库
db = Database(data_dir="./data/my_db")

# 写入一条测试数据（触发所有文件创建）
db.put(b"test", b"value")
db.flush()  # 确保数据持久化

# 现在所有文件都应该存在了
```

## 使用示例

### 完整示例

```python
from src.amdb import Database
from pathlib import Path

# 1. 创建数据库（自动创建所有文件和目录）
db = Database(data_dir="./data/my_database")

# 2. 验证结构
data_dir = Path("./data/my_database")
print(f"database.amdb 存在: {(data_dir / 'database.amdb').exists()}")

# 3. 写入数据
db.put(b"key1", b"value1")
db.put(b"key2", b"value2")

# 4. 读取数据
value = db.get(b"key1")
print(f"key1: {value}")

# 5. 持久化
db.flush()

# 6. 验证数据文件
print(f"versions.ver 存在: {(data_dir / 'versions' / 'versions.ver').exists()}")
print(f"indexes.idx 存在: {(data_dir / 'indexes' / 'indexes.idx').exists()}")
```

## 总结

1. **✅ 使用 `Database(data_dir=...)` 创建数据库**
2. **✅ 会自动创建 `database.amdb` 文件和所有目录**
3. **✅ 数据文件在首次写入时创建**
4. **✅ 所有文件都是数据库的一部分，必须保持同步**

