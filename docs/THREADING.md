# AmDb 多线程功能说明

## 概述

AmDb 已实现完整的多线程支持，包括：
- **并行批量写入**：大批量数据自动使用多线程并行处理
- **查询执行器**：支持并行查询执行
- **分布式集群**：多节点并行处理
- **异步刷新**：MemTable异步刷新到磁盘
- **网络服务器**：每个连接一个线程处理

## 多线程配置

所有多线程相关配置都在 `amdb.ini` 文件的 `[threading]` 部分：

```ini
[threading]
# 是否启用多线程
enable = true

# 最大工作线程数（用于查询执行器、并行查询等）
max_workers = 4

# 异步刷新线程数（用于MemTable异步刷新到磁盘）
async_flush_workers = 2

# 压缩合并线程数（用于SSTable压缩合并）
compaction_workers = 2

# 网络处理线程数（每个连接一个线程，建议设置为max_connections的10-20%）
network_workers = 10

# 是否启用并行批量写入（多线程并行处理批量写入，提升性能）
enable_parallel_batch = true
```

## 多线程功能详解

### 1. 并行批量写入

**功能**：当批量写入数据量超过 `batch_max_size * 2` 时，自动启用多线程并行处理。

**实现位置**：`src/amdb/database.py` 的 `batch_put` 方法

**工作原理**：
- 将大批量数据分成多个批次
- 使用 `ThreadPoolExecutor` 并行处理各个批次
- 线程数根据数据量和 `threading_max_workers` 自动调整

**性能提升**：对于大批量数据（>10,000条），可以显著提升写入性能。

### 2. 查询执行器

**功能**：支持并行执行多个查询计划。

**实现位置**：`src/amdb/executor.py`

**配置**：`threading_max_workers` 控制最大工作线程数

**使用示例**：
```python
from src.amdb.executor import QueryExecutor
from src.amdb import Database

db = Database(config_path='./amdb.ini')
executor = QueryExecutor(db)  # 自动从配置读取max_workers

# 并行执行多个查询
results = executor.execute_parallel(plans, **kwargs)
```

### 3. 分布式集群

**功能**：多节点并行处理，支持水平扩展。

**实现位置**：`src/amdb/distributed.py`

**工作原理**：
- 将数据按节点分组
- 使用 `ThreadPoolExecutor` 并行写入各个节点
- 线程数等于节点数

**性能提升**：线性扩展，节点数越多，性能越高。

### 4. 异步刷新

**功能**：MemTable异步刷新到磁盘，不阻塞写入操作。

**实现位置**：`src/amdb/storage/lsm_tree.py`

**工作原理**：
- 当MemTable满时，创建后台线程异步刷新
- 使用 `threading.Thread` 创建守护线程
- 不阻塞主写入路径

**配置**：`threading_async_flush_workers` 控制异步刷新线程数（预留，当前为每个刷新创建独立线程）

### 5. 网络服务器

**功能**：每个客户端连接使用一个线程处理。

**实现位置**：`src/amdb/network.py`

**配置**：`threading_network_workers` 控制网络处理线程数

## 性能优化建议

1. **CPU密集型任务**：
   - `max_workers` 建议设置为 CPU 核心数
   - 对于I/O密集型任务，可以设置为 CPU 核心数的 2-4 倍

2. **大批量写入**：
   - 启用 `enable_parallel_batch = true`
   - 调整 `batch_max_size` 以平衡内存和性能

3. **网络服务器**：
   - `network_workers` 建议设置为 `max_connections` 的 10-20%
   - 如果连接数较少，可以设置为连接数

4. **内存考虑**：
   - 多线程会增加内存使用
   - 建议监控内存使用情况，适当调整线程数

## 禁用多线程

如果需要禁用多线程（单线程模式），可以在配置文件中设置：

```ini
[threading]
enable = false
```

禁用后，所有多线程功能将被禁用，系统将使用单线程模式运行。

## 线程安全

AmDb 的所有组件都经过线程安全设计：
- 使用 `threading.RLock` 保护共享资源
- 使用 `ReadWriteLock` 优化读多写少场景
- 所有数据结构都考虑了并发访问

## 性能测试

当前性能（启用多线程）：
- **最佳顺序写入性能**：129,472条/秒（20,000条，并行批量写入）
- **对比LevelDB**：达到LevelDB顺序写入的23.5%

## 注意事项

1. **GIL限制**：Python的GIL可能限制多线程性能，对于CPU密集型任务，建议使用多进程或Cython优化
2. **内存使用**：多线程会增加内存使用，需要适当调整线程数
3. **调试难度**：多线程环境下调试较困难，建议在开发时禁用多线程进行调试

