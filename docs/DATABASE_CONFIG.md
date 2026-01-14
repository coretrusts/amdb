# 数据库配置管理

## 概述

AmDb支持每个数据库拥有独立的配置文件，配置文件存储在数据库目录中的 `database.ini` 文件。

## 配置文件位置

每个数据库的配置文件位于：
```
<数据库目录>/database.ini
```

例如：
```
./data/my_database/database.ini
```

## 配置优先级

1. **数据库特定配置** (`database.ini`) - 最高优先级
2. **指定的配置文件** (`config_path` 参数)
3. **全局默认配置** (`./amdb.ini`, `~/.amdb/amdb.ini`, `/etc/amdb/amdb.ini`)
4. **环境变量**
5. **代码默认值** - 最低优先级

## 使用方法

### 1. 程序化使用

```python
from src.amdb import Database

# 创建数据库（会自动加载database.ini如果存在）
db = Database(data_dir='./data/my_database')

# 保存当前配置到数据库
db.save_config()

# 从数据库加载配置
db.load_config()

# 导出配置到指定文件
db.export_config('./my_config.ini')

# 更新配置项
db.update_config(
    batch_max_size=5000,
    threading_max_workers=8
)
```

### 2. GUI管理器使用

在GUI管理器的"配置管理"标签页中：

1. **从数据库加载**: 加载当前数据库的 `database.ini` 配置文件
2. **从文件加载**: 从任意位置加载INI配置文件
3. **保存到数据库**: 将编辑的配置保存到当前数据库的 `database.ini`
4. **导出到文件**: 将配置导出到指定文件
5. **重置为默认**: 重置为默认配置
6. **验证配置**: 验证配置格式是否正确

### 3. 配置文件格式

配置文件使用INI格式，示例：

```ini
[database]
data_dir = ./data/my_database
enable_sharding = True
shard_count = 256
max_file_size = 268435456

[lsm]
memtable_max_size = 10485760
level_size_limit = 10
enable_skip_list = False
enable_cython = False

[batch]
max_size = 3000
version_max_size = 3000
skip_prev_hash_threshold = 300

[performance]
enable_async_flush = True
enable_preallocated_memtable = True
flush_interval = 1.0
checkpoint_interval = 60.0

[network]
host = 0.0.0.0
port = 3888
max_connections = 100
timeout = 30.0
enable_ssl = False

[cache]
enable = True
size = 104857600
type = lru

[log]
level = INFO
dir = ./logs
max_file_size = 10485760
backup_count = 5
enable_console = True
enable_file = True

[security]
enable_auth = False
auth_method = token
enable_encryption = False

[audit]
enable = True

[compression]
enable = True
type = snappy

[threading]
enable = True
max_workers = 4
async_flush_workers = 2
compaction_workers = 2
network_workers = 10
enable_parallel_batch = True
```

## 配置项说明

### 基础配置 (database)
- `data_dir`: 数据目录路径
- `enable_sharding`: 是否启用分片
- `shard_count`: 分片数量
- `max_file_size`: 单个文件最大大小（字节）

### LSM树配置 (lsm)
- `memtable_max_size`: MemTable最大大小（字节）
- `level_size_limit`: 每层最多SSTable数量
- `enable_skip_list`: 是否启用SkipList
- `enable_cython`: 是否启用Cython优化

### 批量操作配置 (batch)
- `max_size`: 批量操作最大大小
- `version_max_size`: 版本管理批量操作最大大小
- `skip_prev_hash_threshold`: 跳过prev_hash计算的阈值

### 性能配置 (performance)
- `enable_async_flush`: 是否启用异步刷新
- `enable_preallocated_memtable`: 是否启用预分配MemTable
- `flush_interval`: 刷新间隔（秒）
- `checkpoint_interval`: 检查点间隔（秒）

### 网络配置 (network)
- `host`: 监听地址
- `port`: 监听端口
- `max_connections`: 最大连接数
- `timeout`: 超时时间（秒）
- `enable_ssl`: 是否启用SSL

### 缓存配置 (cache)
- `enable`: 是否启用缓存
- `size`: 缓存大小（字节）
- `type`: 缓存类型（lru, lfu, fifo）
- `ttl`: 过期时间（秒，可选）

### 日志配置 (log)
- `level`: 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
- `file`: 日志文件路径（可选）
- `dir`: 日志目录
- `max_file_size`: 单个日志文件最大大小（字节）
- `backup_count`: 日志备份数量
- `enable_console`: 是否输出到控制台
- `enable_file`: 是否输出到文件

### 安全配置 (security)
- `enable_auth`: 是否启用认证
- `auth_method`: 认证方法（token, password, certificate）
- `token_secret`: Token密钥（可选）
- `enable_encryption`: 是否启用加密
- `encryption_key`: 加密密钥（可选）

### 审计日志配置 (audit)
- `enable`: 是否启用审计日志
- `log_dir`: 审计日志目录（可选，默认使用data_dir/audit_logs）

### 压缩配置 (compression)
- `enable`: 是否启用压缩
- `type`: 压缩类型（none, snappy, lz4）

### 多线程配置 (threading)
- `enable`: 是否启用多线程
- `max_workers`: 最大工作线程数
- `async_flush_workers`: 异步刷新线程数
- `compaction_workers`: 压缩合并线程数
- `network_workers`: 网络处理线程数
- `enable_parallel_batch`: 是否启用并行批量写入

## 注意事项

1. **配置生效**: 部分配置项（如线程数、缓存大小）需要重启数据库才能生效
2. **配置验证**: 修改配置后建议使用"验证配置"功能检查格式
3. **备份配置**: 修改重要配置前建议先导出备份
4. **性能调优**: 根据实际使用场景调整配置项，参考性能测试结果

## 更新日期

2026-01-13

