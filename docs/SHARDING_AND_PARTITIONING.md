# AmDb 分片和分区文档

## 概述

AmDb支持大数据量的分片存储和分区管理，可以处理千万级甚至上亿级的数据，避免单文件过大导致的性能问题。

## 核心特性

### 1. 数据分片（Sharding）

- **自动分片**: 根据key的哈希值自动分配到不同分片
- **文件大小限制**: 单个文件最大256MB（可配置）
- **自动分割**: 文件超过大小限制时自动创建新文件
- **文件夹索引**: 使用两级目录结构组织分片数据

### 2. 分区管理（Partitioning）

- **分表分库**: 支持创建多个分区（类似表/库）
- **独立配置**: 每个分区可以有不同的分片数量和文件大小限制
- **隔离存储**: 不同分区的数据完全隔离

### 3. 大数据适配

- **支持千万级数据**: 通过分片将数据分散到多个文件
- **支持上亿级数据**: 通过增加分片数量支持更大数据量
- **性能优化**: 分片后查询只需访问相关分片，提升性能

## 架构设计

### 分片目录结构

```
data/
├── lsm/
│   ├── shard_00/
│   │   ├── shard_00/
│   │   │   ├── sstable_1234567890_000001.sst
│   │   │   ├── sstable_1234567890_000002.sst
│   │   │   └── sstable_1234567891_000001.sst
│   │   ├── shard_01/
│   │   └── ...
│   ├── shard_01/
│   └── ...
└── partitions/
    ├── partition1/
    │   └── shard_00/
    └── partition2/
        └── shard_00/
```

### 分片策略

1. **哈希分片（默认）**
   - 使用SHA256哈希key
   - 均匀分布到256个分片
   - 适合大多数场景

2. **范围分片**
   - 基于key的第一个字节
   - 适合有序key的场景

3. **目录分片**
   - 基于key的前缀
   - 适合有明确前缀的场景

4. **自定义分片**
   - 提供自定义分片函数
   - 完全控制分片逻辑

## 使用示例

### 基本使用（自动分片）

```python
from src.amdb import Database

# 创建数据库（默认启用分片，256个分片，256MB文件限制）
db = Database(
    data_dir="./data/mydb",
    enable_sharding=True,
    shard_count=256,
    max_file_size=256 * 1024 * 1024
)

# 写入数据（自动分片）
db.put(b"key1", b"value1")
db.put(b"key2", b"value2")

# 读取数据（自动定位分片）
value = db.get(b"key1")

# 查看分片信息
stats = db.get_stats()
print(f"分片数量: {stats['shard_count']}")
print(f"分片信息: {stats['shard_info']}")
```

### 创建分区（分表分库）

```python
# 创建分区1（用户表）
db.create_partition("users", shard_count=128, max_file_size=128*1024*1024)

# 创建分区2（订单表）
db.create_partition("orders", shard_count=256, max_file_size=256*1024*1024)

# 列出所有分区
partitions = db.list_partitions()
print(f"分区列表: {partitions}")

# 获取分区
user_partition = db.get_partition("users")
```

### 大数据量场景

```python
# 处理千万级数据
db = Database(
    data_dir="./data/bigdata",
    enable_sharding=True,
    shard_count=1024,  # 增加分片数量
    max_file_size=128 * 1024 * 1024  # 减小单个文件大小
)

# 批量写入
items = [(f"key_{i}".encode(), f"value_{i}".encode()) for i in range(10000000)]
db.batch_put(items)

# 查看分片统计
stats = db.get_stats()
for shard_id, info in stats['shard_info'].items():
    print(f"分片 {shard_id}: {info['sstable_count']} 个文件, "
          f"总大小: {info['stats'].get('total_size', 0) / 1024 / 1024:.2f} MB")
```

## 配置参数

### 分片配置

- `shard_count`: 分片数量（默认256）
  - 256: 适合百万级数据
  - 1024: 适合千万级数据
  - 4096: 适合上亿级数据

- `max_file_size`: 单个文件最大大小（默认256MB）
  - 128MB: 适合SSD存储
  - 256MB: 适合HDD存储
  - 512MB: 适合大容量存储

### 性能优化建议

1. **分片数量选择**
   - 数据量 < 100万: 64-128个分片
   - 数据量 100万-1000万: 256-512个分片
   - 数据量 > 1000万: 1024+个分片

2. **文件大小选择**
   - SSD存储: 128-256MB
   - HDD存储: 256-512MB
   - 网络存储: 64-128MB

3. **分区策略**
   - 按业务模块分区（用户、订单、商品等）
   - 按时间分区（按月、按年）
   - 按地域分区（按地区、按国家）

## 文件分割机制

### 自动分割

当单个文件大小超过限制时：

1. 当前文件继续写入直到达到限制
2. 自动创建新文件（文件名递增）
3. 新数据写入新文件
4. 索引自动更新

### 文件命名规则

```
sstable_{timestamp}_{file_id:06d}.sst
```

- `timestamp`: 创建时间戳（微秒）
- `file_id`: 文件编号（6位数字，自动递增）

### 索引管理

- 每个分片维护独立的索引
- 索引包含所有文件的key映射
- 支持快速定位key所在文件

## 性能特性

### 写入性能

- **并行写入**: 不同分片可以并行写入
- **批量优化**: 同一分片的数据批量写入
- **减少I/O**: 分片后减少单文件I/O压力

### 读取性能

- **分片定位**: O(1)时间定位key所在分片
- **并行读取**: 可以并行读取多个分片
- **缓存优化**: 每个分片独立缓存

### 查询性能

- **范围查询**: 只查询相关分片
- **索引优化**: 分片索引减少查找范围
- **并行查询**: 多分片并行查询

## 监控和统计

### 分片统计信息

```python
stats = db.get_stats()
shard_info = stats['shard_info']

for shard_id, info in shard_info.items():
    print(f"分片 {shard_id}:")
    print(f"  MemTable大小: {info['memtable_size']} bytes")
    print(f"  SSTable数量: {info['sstable_count']}")
    print(f"  总大小: {info['stats']['total_size']} bytes")
    print(f"  文件数量: {info['stats']['file_count']}")
```

### 分区统计

```python
partitions = db.list_partitions()
for partition_name in partitions:
    partition = db.get_partition(partition_name)
    if partition:
        stats = partition.get_shard_stats()
        print(f"分区 {partition_name}: {len(stats)} 个分片")
```

## 最佳实践

1. **合理设置分片数量**
   - 根据数据量选择，不要过多或过少
   - 建议是2的幂次（64, 128, 256, 512, 1024等）

2. **文件大小限制**
   - 根据存储类型选择
   - 考虑备份和恢复的时间

3. **分区设计**
   - 按业务逻辑分区
   - 避免跨分区查询

4. **监控分片分布**
   - 定期检查分片数据分布
   - 确保数据均匀分布

5. **备份策略**
   - 可以按分片备份
   - 支持增量备份

## 限制和注意事项

1. **分片数量限制**
   - 建议不超过4096个分片
   - 过多分片会增加管理开销

2. **文件数量**
   - 单个分片文件数量建议不超过1000个
   - 过多文件会影响查询性能

3. **跨分片查询**
   - 范围查询可能需要查询多个分片
   - 性能取决于涉及的分片数量

4. **数据迁移**
   - 支持分片数据迁移
   - 需要重新计算分片ID

## 未来改进

- [ ] 动态分片调整
- [ ] 自动负载均衡
- [ ] 跨分片事务支持
- [ ] 分片合并和分裂
- [ ] 更智能的分片策略

