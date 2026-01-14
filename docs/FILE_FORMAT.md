# AmDb 文件格式规范

## 文件后缀定义

### 存储文件
- `.amdb` - 主数据库文件（元数据）
- `.sst` - SSTable文件（LSM树磁盘层）
- `.bpt` - B+树节点文件
- `.mpt` - Merkle Patricia Tree节点文件
- `.wal` - 预写日志文件
- `.idx` - 索引文件
- `.ver` - 版本历史文件
- `.meta` - 元数据文件

### 临时文件
- `.tmp` - 临时文件
- `.lock` - 锁文件
- `.compacting` - 压缩中标记文件

## 文件结构

### 1. SSTable文件格式 (.sst)

```
[文件头]
- magic: 4 bytes ("SST\0")
- version: 2 bytes (文件格式版本)
- key_count: 8 bytes (键数量)
- data_offset: 8 bytes (数据区偏移)
- index_offset: 8 bytes (索引区偏移)
- footer_offset: 8 bytes (footer偏移)

[数据区]
- 键值对列表（有序）
  - key_len: 4 bytes
  - key: key_len bytes
  - value_len: 4 bytes
  - value: value_len bytes
  - version: 4 bytes
  - timestamp: 8 bytes (float)

[索引区]
- 稀疏索引（每N个键一个索引）
  - key: variable
  - offset: 8 bytes

[Footer]
- index_offset: 8 bytes
- checksum: 32 bytes (SHA256)
- magic: 4 bytes ("SST\0")
```

### 2. B+树节点文件格式 (.bpt)

```
[节点头]
- magic: 4 bytes ("BPT\0")
- node_id: 8 bytes
- node_type: 1 byte (0=leaf, 1=internal)
- key_count: 2 bytes
- parent_id: 8 bytes (0表示无父节点)
- next_leaf_id: 8 bytes (仅叶子节点)

[键值区]
- keys: variable
  - key_len: 2 bytes
  - key: key_len bytes
- values: variable
  - value_len: 4 bytes (叶子节点)
  - value: value_len bytes
  - child_id: 8 bytes (内部节点)

[Footer]
- checksum: 32 bytes
```

### 3. Merkle树节点文件格式 (.mpt)

```
[节点头]
- magic: 4 bytes ("MPT\0")
- node_hash: 32 bytes
- node_type: 1 byte (0=leaf, 1=extension, 2=branch)
- data_len: 4 bytes

[数据区]
- 根据节点类型不同：
  - Leaf: key + value
  - Extension: prefix + child_hash
  - Branch: 16个child_hash (每个32字节)

[Footer]
- checksum: 32 bytes
```

### 4. WAL文件格式 (.wal)

```
[日志条目]
- entry_type: 1 byte (0=put, 1=delete, 2=commit, 3=abort)
- timestamp: 8 bytes
- key_len: 4 bytes
- key: key_len bytes
- value_len: 4 bytes (仅put操作)
- value: value_len bytes (仅put操作)
- checksum: 32 bytes
```

### 5. 版本历史文件格式 (.ver)

```
[文件头]
- magic: 4 bytes ("VER\0")
- key: variable
- version_count: 8 bytes

[版本条目]
- version: 4 bytes
- timestamp: 8 bytes
- value_hash: 32 bytes
- prev_hash: 32 bytes
- value_offset: 8 bytes (指向值存储位置)
```

### 6. 索引文件格式 (.idx)

```
[文件头]
- magic: 4 bytes ("IDX\0")
- index_name: variable
- index_type: 1 byte
- entry_count: 8 bytes

[索引条目]
- index_value: variable
- key_count: 4 bytes
- keys: variable (key列表)
```

## 数据编码

### 键值编码
- 键：UTF-8编码的字节串
- 值：原始字节串（支持任意二进制数据）

### 数值编码
- 整数：大端序（big-endian）
- 浮点数：IEEE 754标准
- 时间戳：Unix时间戳（秒，float64）

### 字符串编码
- 默认：UTF-8
- 支持多语言字符集

## 压缩格式

### 数据压缩
- 算法：Snappy（快速）或 LZ4（更快）
- 压缩块大小：64KB
- 压缩标记：1 byte（0=未压缩, 1=Snappy, 2=LZ4）

## 校验和

- 算法：SHA256
- 位置：每个文件footer
- 用途：数据完整性验证

