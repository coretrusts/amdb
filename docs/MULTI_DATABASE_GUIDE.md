# AmDb 多数据库管理指南

## 概述

AmDb支持创建和管理多个独立的数据库实例，每个数据库实例都有自己独立的数据目录、配置和存储空间。这对于以下场景非常有用：

- **数据隔离**：不同业务使用不同的数据库
- **性能优化**：将不同类型的数据分开存储
- **备份管理**：可以单独备份和恢复某个数据库
- **开发测试**：开发、测试、生产环境使用不同的数据库

## 创建多个数据库

### 方法1：使用脚本创建（推荐）

运行提供的脚本创建多个示例数据库：

```bash
python create_multiple_databases.py
```

这将创建以下数据库：
- **用户数据库** (`./data/user_db`) - 存储用户账户信息
- **交易数据库** (`./data/transaction_db`) - 存储所有交易记录
- **区块数据库** (`./data/block_db`) - 存储区块链区块数据
- **智能合约数据库** (`./data/contract_db`) - 存储智能合约信息
- **日志数据库** (`./data/log_db`) - 存储系统日志和审计记录

### 方法2：手动创建

在Python代码中创建：

```python
from src.amdb import Database

# 创建用户数据库
user_db = Database(data_dir="./data/user_db", config_path="./amdb.ini")

# 创建交易数据库
transaction_db = Database(data_dir="./data/transaction_db", config_path="./amdb.ini")

# 创建区块数据库
block_db = Database(data_dir="./data/block_db", config_path="./amdb.ini")
```

### 方法3：使用不同配置

每个数据库可以使用不同的配置文件：

```python
# 开发环境数据库（使用开发配置）
dev_db = Database(
    data_dir="./data/dev_db",
    config_path="./amdb_dev.ini"  # 开发环境配置
)

# 生产环境数据库（使用生产配置）
prod_db = Database(
    data_dir="./data/prod_db",
    config_path="./amdb_prod.ini"  # 生产环境配置
)
```

## 连接数据库

### 在GUI管理器中连接

1. **启动管理器**：
   ```bash
   python amdb_manager.py
   ```

2. **连接数据库**：
   - 点击"文件" → "连接数据库"
   - 在"快速选择"列表中选择预设的数据库
   - 或手动输入数据目录路径
   - 点击"浏览..."按钮选择数据目录
   - 点击"连接"按钮

3. **切换数据库**：
   - 先断开当前连接（"文件" → "断开连接"）
   - 然后连接新的数据库

### 在Python代码中连接

```python
from src.amdb import Database

# 连接用户数据库
user_db = Database(data_dir="./data/user_db")

# 连接交易数据库
transaction_db = Database(data_dir="./data/transaction_db")

# 同时使用多个数据库
user_db.put(b"user:001", b"user_data")
transaction_db.put(b"tx:001", b"transaction_data")
```

## 数据库管理最佳实践

### 1. 目录结构建议

```
data/
├── user_db/          # 用户数据库
├── transaction_db/   # 交易数据库
├── block_db/         # 区块数据库
├── contract_db/      # 智能合约数据库
├── log_db/           # 日志数据库
├── dev_db/           # 开发环境数据库
└── prod_db/          # 生产环境数据库
```

### 2. 配置文件管理

为不同环境创建不同的配置文件：

```
amdb.ini              # 默认配置
amdb_dev.ini          # 开发环境配置
amdb_prod.ini         # 生产环境配置
amdb_test.ini         # 测试环境配置
```

### 3. 数据隔离

确保不同数据库的数据完全隔离：

```python
# 用户数据库 - 只存储用户相关数据
user_db = Database(data_dir="./data/user_db")
user_db.put(b"user:001", b"user_data")

# 交易数据库 - 只存储交易相关数据
transaction_db = Database(data_dir="./data/transaction_db")
transaction_db.put(b"tx:001", b"transaction_data")

# 两个数据库完全独立，互不影响
```

### 4. 备份和恢复

每个数据库可以单独备份和恢复：

```python
from src.amdb.backup import BackupManager

# 备份用户数据库
user_backup = BackupManager("./data/user_db")
user_backup.create_full_backup("./backups/user_db_backup.backup")

# 恢复用户数据库
user_backup.restore_from_backup("./backups/user_db_backup.backup")
```

## 使用场景示例

### 场景1：区块链应用

```python
from src.amdb import Database

# 区块数据库 - 存储区块数据
block_db = Database(data_dir="./data/blockchain/blocks")

# 交易数据库 - 存储交易数据
transaction_db = Database(data_dir="./data/blockchain/transactions")

# 状态数据库 - 存储账户状态
state_db = Database(data_dir="./data/blockchain/state")

# 合约数据库 - 存储智能合约
contract_db = Database(data_dir="./data/blockchain/contracts")
```

### 场景2：多租户应用

```python
from src.amdb import Database

# 为每个租户创建独立的数据库
tenant1_db = Database(data_dir="./data/tenants/tenant1")
tenant2_db = Database(data_dir="./data/tenants/tenant2")
tenant3_db = Database(data_dir="./data/tenants/tenant3")
```

### 场景3：开发/测试/生产环境

```python
from src.amdb import Database

# 开发环境
dev_db = Database(
    data_dir="./data/dev",
    config_path="./amdb_dev.ini"
)

# 测试环境
test_db = Database(
    data_dir="./data/test",
    config_path="./amdb_test.ini"
)

# 生产环境
prod_db = Database(
    data_dir="./data/prod",
    config_path="./amdb_prod.ini"
)
```

## 注意事项

1. **数据目录唯一性**：每个数据库必须使用不同的数据目录
2. **配置共享**：多个数据库可以共享同一个配置文件，也可以使用不同的配置
3. **资源管理**：同时打开多个数据库会占用更多内存和文件句柄
4. **性能考虑**：如果数据量很大，建议将不同类型的数据分开存储
5. **备份策略**：为每个数据库制定独立的备份策略

## 常见问题

### Q: 可以在同一个程序中同时使用多个数据库吗？

A: 可以。每个数据库实例都是独立的，可以同时创建和使用多个：

```python
user_db = Database(data_dir="./data/user_db")
transaction_db = Database(data_dir="./data/transaction_db")

# 同时使用
user_db.put(b"user:001", b"data1")
transaction_db.put(b"tx:001", b"data2")
```

### Q: 如何查看所有已创建的数据库？

A: 查看数据目录下的所有子目录：

```bash
ls -la ./data/
```

或在Python中：

```python
import os
data_dir = "./data"
databases = [d for d in os.listdir(data_dir) 
             if os.path.isdir(os.path.join(data_dir, d))]
print("已创建的数据库:", databases)
```

### Q: 如何删除一个数据库？

A: 直接删除对应的数据目录：

```bash
rm -rf ./data/user_db
```

或在Python中：

```python
import shutil
shutil.rmtree("./data/user_db")
```

### Q: 数据库之间可以共享数据吗？

A: 不可以。每个数据库实例完全独立，数据不共享。如果需要共享数据，需要手动从一个数据库读取并写入另一个数据库。

## 参考

- [配置指南](CONFIG_GUIDE.md) - 配置文件详细说明
- [GUI管理器](GUI_MANAGER.md) - 桌面版管理器使用说明
- [备份和恢复](../src/amdb/backup.py) - 数据库备份恢复功能

