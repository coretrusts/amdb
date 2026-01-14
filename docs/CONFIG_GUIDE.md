# AmDb 配置指南

## 概述

AmDb使用INI格式的配置文件（`amdb.ini`）来管理所有配置项，类似于MySQL的`my.cnf`和PostgreSQL的`postgresql.conf`。

## 配置文件位置

AmDb会按以下顺序查找配置文件：

1. 命令行指定的配置文件路径
2. `./amdb.ini`（当前目录）
3. `~/.amdb/amdb.ini`（用户主目录）
4. `/etc/amdb/amdb.ini`（系统目录）

## 配置优先级

配置项的优先级（从高到低）：

1. **命令行参数**（最高优先级）
2. **环境变量**
3. **配置文件**
4. **代码默认值**（最低优先级）

## 配置示例

### 示例1：开发环境配置

```ini
[database]
data_dir = ./data/amdb
enable_sharding = false
shard_count = 64

[log]
level = DEBUG
enable_console = true
enable_file = false

[performance]
enable_async_flush = false
flush_interval = 5.0

[threading]
enable = false
max_workers = 2
```

### 示例2：生产环境配置（小规模）

```ini
[database]
data_dir = /var/lib/amdb
enable_sharding = true
shard_count = 128
max_file_size = 134217728  # 128MB

[lsm]
memtable_max_size = 5242880  # 5MB

[batch]
max_size = 2000
version_max_size = 2000

[performance]
enable_async_flush = true
enable_preallocated_memtable = true
flush_interval = 1.0
checkpoint_interval = 30.0

[network]
host = 0.0.0.0
port = 3888
max_connections = 50
timeout = 30.0

[cache]
enable = true
size = 52428800  # 50MB
type = lru

[log]
level = INFO
enable_console = false
enable_file = true
dir = /var/log/amdb

[audit]
enable = true
log_dir = /var/log/amdb/audit

[threading]
enable = true
max_workers = 4
enable_parallel_batch = true
```

### 示例3：生产环境配置（大规模）

```ini
[database]
data_dir = /data/amdb
enable_sharding = true
shard_count = 512
max_file_size = 536870912  # 512MB

[lsm]
memtable_max_size = 20971520  # 20MB
level_size_limit = 20

[batch]
max_size = 5000
version_max_size = 5000
skip_prev_hash_threshold = 500

[performance]
enable_async_flush = true
enable_preallocated_memtable = true
flush_interval = 0.5
checkpoint_interval = 60.0

[network]
host = 0.0.0.0
port = 3888
max_connections = 200
timeout = 60.0

[cache]
enable = true
size = 524288000  # 500MB
type = lru
ttl = 3600  # 1小时

[log]
level = INFO
enable_console = false
enable_file = true
dir = /var/log/amdb
max_file_size = 52428800  # 50MB
backup_count = 10

[audit]
enable = true
log_dir = /var/log/amdb/audit

[compression]
enable = true
type = snappy

[threading]
enable = true
max_workers = 8
async_flush_workers = 4
compaction_workers = 4
network_workers = 20
enable_parallel_batch = true
```

### 示例4：高性能配置（追求极致性能）

```ini
[database]
data_dir = /data/amdb
enable_sharding = true
shard_count = 1024
max_file_size = 1073741824  # 1GB

[lsm]
memtable_max_size = 52428800  # 50MB
level_size_limit = 30

[batch]
max_size = 10000
version_max_size = 10000
skip_prev_hash_threshold = 1000

[performance]
enable_async_flush = true
enable_preallocated_memtable = true
flush_interval = 0.3
checkpoint_interval = 120.0

[network]
host = 0.0.0.0
port = 3888
max_connections = 500
timeout = 30.0

[cache]
enable = true
size = 1073741824  # 1GB
type = lru

[log]
level = WARNING
enable_console = false
enable_file = true

[audit]
enable = false  # 禁用审计日志以提升性能

[compression]
enable = false  # 禁用压缩以提升性能

[threading]
enable = true
max_workers = 16
async_flush_workers = 8
compaction_workers = 8
network_workers = 50
enable_parallel_batch = true
```

## 环境变量配置

除了配置文件，还可以通过环境变量设置配置：

```bash
# 数据目录
export AMDB_DATA_DIR=/var/lib/amdb

# 启用分片
export AMDB_ENABLE_SHARDING=true

# 分片数量
export AMDB_SHARD_COUNT=256

# 批量大小
export AMDB_BATCH_MAX_SIZE=3000

# 日志级别
export AMDB_LOG_LEVEL=INFO

# Token密钥
export AMDB_SECURITY_TOKEN_SECRET=your-secret-key-here
```

## 配置验证

使用以下命令验证配置是否正确：

```python
from src.amdb.config import load_config

config = load_config('./amdb.ini')
print(f"数据目录: {config.data_dir}")
print(f"分片数量: {config.shard_count}")
print(f"批量大小: {config.batch_max_size}")
```

## 性能调优建议

### 写入性能优化

1. **增大批量大小**：`batch.max_size = 3000-5000`
2. **启用并行批量写入**：`threading.enable_parallel_batch = true`
3. **增大MemTable大小**：`lsm.memtable_max_size = 20MB-50MB`
4. **启用预分配MemTable**：`performance.enable_preallocated_memtable = true`
5. **禁用审计日志**（如果不需要）：`audit.enable = false`

### 读取性能优化

1. **启用缓存**：`cache.enable = true`
2. **增大缓存大小**：`cache.size = 100MB-1GB`
3. **使用LRU缓存**：`cache.type = lru`
4. **启用分片**：`database.enable_sharding = true`

### 内存优化

1. **减小MemTable大小**：`lsm.memtable_max_size = 5MB-10MB`
2. **减小缓存大小**：`cache.size = 50MB-100MB`
3. **减少分片数量**：`database.shard_count = 64-128`

### 磁盘空间优化

1. **启用压缩**：`compression.enable = true`
2. **使用snappy压缩**：`compression.type = snappy`
3. **减小文件大小**：`database.max_file_size = 128MB-256MB`

## 常见问题

### Q: 如何找到配置文件？

A: AmDb会按以下顺序查找：
1. 命令行指定的路径
2. `./amdb.ini`
3. `~/.amdb/amdb.ini`
4. `/etc/amdb/amdb.ini`

### Q: 配置修改后需要重启吗？

A: 部分配置（如网络端口、数据目录）需要重启才能生效，部分配置（如日志级别）可以动态调整。

### Q: 如何备份配置？

A: 直接复制`amdb.ini`文件即可。

### Q: 配置错误怎么办？

A: AmDb会在启动时验证配置，如果配置错误会抛出异常并提示错误信息。

## 参考

- 完整配置项说明：见`amdb.ini`文件中的注释
- 性能基准测试：见`docs/PERFORMANCE_BENCHMARK.md`
- 架构设计：见`docs/ARCHITECTURE.md`

