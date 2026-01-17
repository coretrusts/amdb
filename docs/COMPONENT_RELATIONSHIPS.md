# AmDb 数据库组件关联关系分析

## 组件概述

AmDb 数据库由以下组件构成：

1. **database.amdb** - 数据库元数据文件（版本、描述、统计信息）
2. **wal/** - 预写日志（Write-Ahead Log）
3. **versions/** - 版本管理器数据（版本历史）
4. **shards/** - 分片存储（如果启用分片）
5. **merkle/** - Merkle树数据（数据完整性验证）
6. **lsm/** - LSM树数据（主要存储引擎）
7. **indexes/** - 索引管理器数据（主键、版本、时间索引）
8. **bplus/** - B+树数据（快速读取缓存）
9. **audit_logs/** - 审计日志（如果启用）

## 组件关联关系

### 1. 写入操作流程（put/delete）

```
用户调用 put(key, value)
    ↓
1. version_manager.create_version()  ← 创建版本对象（内存）
    ↓
2. storage.put()  ← 写入存储引擎
   ├─ lsm_tree.put()  ← 写入LSM树（主要存储）
   ├─ bplus_tree.insert()  ← 异步更新B+树（快速读取）
   └─ merkle_tree.put()  ← 更新Merkle树（完整性验证）
    ↓
3. index_manager.put()  ← 更新索引（内存）
   ├─ primary_index[key] = (value, version)
   ├─ version_index[key].append((version, timestamp))
   └─ time_index.append((timestamp, key))
    ↓
4. wal_logger.log_put()  ← 异步写入WAL（持久性保证）
    ↓
5. audit_logger.log_put()  ← 异步记录审计日志（可选）
```

### 2. 读取操作流程（get）

```
用户调用 get(key)
    ↓
1. _check_and_reload_if_updated()  ← 检查文件是否更新
    ↓
2. version_manager.get_latest()  ← 优先从版本管理器获取（内存）
    ↓ (如果失败)
3. storage.get()  ← 从存储引擎获取
   ├─ bplus_tree.get()  ← 优先从B+树读取（如果已同步）
   └─ lsm_tree.get()  ← 从LSM树读取（主要数据源）
```

### 3. 持久化流程（flush）

```
用户调用 flush()
    ↓
1. storage.lsm_tree.flush()  ← 同步刷新LSM树MemTable到磁盘
    ↓
2. 同步模式（force_sync=True）：
   ├─ storage.bplus_tree.flush()  ← 持久化B+树
   ├─ storage.merkle_tree.save_to_disk()  ← 持久化Merkle树
   ├─ version_manager.save_to_disk()  ← 持久化版本数据
   ├─ index_manager.save_to_disk()  ← 持久化索引数据
   └─ _save_metadata()  ← 保存元数据
    ↓
3. 异步模式（async_mode=True）：
   └─ 后台线程异步持久化非关键文件
```

## 组件依赖关系

### 强关联组件（必须同步）

1. **version_manager ↔ storage (lsm_tree)**
   - 版本管理器记录版本号，存储引擎使用版本号存储数据
   - **必须同步**：版本号和存储数据必须一致

2. **index_manager ↔ version_manager**
   - 索引管理器使用版本号和时间戳建立索引
   - **必须同步**：索引必须反映版本管理器的状态

3. **storage (merkle_tree) ↔ storage (lsm_tree)**
   - Merkle树用于验证LSM树的数据完整性
   - **必须同步**：Merkle根哈希必须与LSM树数据一致

### 弱关联组件（可以异步）

1. **wal ↔ storage**
   - WAL用于恢复数据，但数据已存储在LSM树中
   - **可以异步**：WAL失败不影响主操作

2. **bplus_tree ↔ lsm_tree**
   - B+树是LSM树的缓存，用于快速读取
   - **可以异步**：B+树更新失败不影响数据写入

3. **audit_logs ↔ 所有组件**
   - 审计日志仅用于审计，不影响数据操作
   - **可以异步**：审计日志失败不影响主操作

4. **database.amdb ↔ 所有组件**
   - 元数据文件包含统计信息，但不影响数据操作
   - **可以异步**：元数据更新失败不影响数据操作

## 索引更新正确性保证

### 1. 主键索引（primary_index）

**更新时机**：
- 每次 `put()` 或 `delete()` 操作时立即更新
- 在 `index_manager.put()` 中同步更新

**正确性保证**：
- ✅ 使用锁（`self.lock`）保证线程安全
- ✅ 与 `version_manager` 同步更新
- ✅ 在内存中维护，flush时持久化

### 2. 版本索引（version_index）

**更新时机**：
- 每次创建新版本时更新
- 使用二分查找保持有序

**正确性保证**：
- ✅ 使用锁保证线程安全
- ✅ 与 `version_manager` 的版本号一致
- ✅ 保持有序，支持范围查询

### 3. 时间索引（time_index）

**更新时机**：
- 每次 `put()` 或 `delete()` 操作时更新
- 使用二分查找保持有序

**正确性保证**：
- ✅ 使用锁保证线程安全
- ✅ 与 `version_manager` 的时间戳一致
- ✅ 保持有序，支持时间点查询

### 4. 二级索引（secondary_indexes）

**更新时机**：
- 需要手动调用 `update_secondary_index()`
- 不会自动更新

**正确性保证**：
- ⚠️ 需要应用层手动维护
- ⚠️ 如果忘记更新，可能导致查询不准确

## 数据一致性保证

### 1. 写入一致性

**保证机制**：
- ✅ 使用锁（`self.lock`）保证原子性
- ✅ 版本管理器、存储引擎、索引管理器同步更新
- ✅ WAL日志保证持久性（即使崩溃也能恢复）

**潜在问题**：
- ⚠️ B+树更新是异步的，可能短暂不一致（但不影响读取，因为会回退到LSM树）
- ⚠️ 审计日志是异步的，可能丢失（但不影响数据操作）

### 2. 读取一致性

**保证机制**：
- ✅ 优先从版本管理器读取（内存，最新）
- ✅ 如果失败，从存储引擎读取（LSM树或B+树）
- ✅ 自动检测文件更新，重新加载数据

**潜在问题**：
- ⚠️ 如果B+树未同步，可能读取到旧数据（但会回退到LSM树）
- ⚠️ 如果索引未持久化，重启后需要重新构建

### 3. 持久化一致性

**保证机制**：
- ✅ LSM树MemTable同步刷新（关键数据）
- ✅ 版本管理器、索引管理器同步持久化（同步模式）
- ✅ WAL日志保证数据不丢失

**潜在问题**：
- ⚠️ 异步模式下，非关键文件可能未及时持久化
- ⚠️ 如果flush失败，部分数据可能未持久化

## 组件独立性分析

### 可以独立工作的组件

1. **wal/** - 可以删除，不影响数据读取（但影响恢复）
2. **audit_logs/** - 可以删除，不影响数据操作
3. **database.amdb** - 可以删除，不影响数据操作（但影响元数据查询）
4. **bplus/** - 可以删除，不影响数据操作（但影响读取性能）

### 必须存在的组件

1. **versions/** - 必须存在，版本管理器是核心
2. **lsm/** - 必须存在，主要存储引擎
3. **indexes/** - 建议存在，用于快速查询（可以重建）

### 可选组件

1. **merkle/** - 可选，用于数据完整性验证
2. **shards/** - 可选，仅在启用分片时使用
3. **bplus/** - 可选，用于快速读取（可以重建）

## 建议和最佳实践

### 1. 索引更新

- ✅ **主键索引、版本索引、时间索引**：自动更新，无需担心
- ⚠️ **二级索引**：需要手动维护，确保与数据同步

### 2. 数据一致性

- ✅ **写入操作**：使用事务保证原子性
- ✅ **读取操作**：优先从版本管理器读取，确保最新数据
- ✅ **持久化**：定期调用 `flush()` 确保数据持久化

### 3. 组件维护

- ✅ **定期备份**：备份 `versions/` 和 `lsm/` 目录
- ✅ **定期清理**：清理旧的WAL日志和审计日志
- ✅ **监控**：监控各组件的大小和性能

### 4. 故障恢复

- ✅ **WAL恢复**：如果LSM树损坏，可以从WAL恢复
- ✅ **索引重建**：如果索引损坏，可以从版本管理器重建
- ✅ **数据验证**：使用Merkle树验证数据完整性

## 总结

1. **组件关联**：
   - 核心组件（version_manager、storage、index_manager）强关联，必须同步
   - 辅助组件（wal、audit_logs、bplus）弱关联，可以异步

2. **索引正确性**：
   - ✅ 主键索引、版本索引、时间索引自动更新，保证正确性
   - ⚠️ 二级索引需要手动维护

3. **数据一致性**：
   - ✅ 写入时使用锁保证原子性
   - ✅ 读取时优先从版本管理器获取最新数据
   - ✅ 持久化时同步刷新关键数据

4. **组件独立性**：
   - ✅ 核心组件（versions、lsm）必须存在
   - ✅ 辅助组件（wal、audit_logs、bplus）可以独立删除或重建

