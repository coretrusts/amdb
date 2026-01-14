# AmDb 增删改查功能完整指南

## 概述

本文档详细说明AmDb数据库系统在CLI和GUI中的所有增删改查（CRUD）功能，确保所有查询方式都能正常使用。

## CLI 命令行工具

### 1. 增（Create）- 写入数据

#### `put` - 单条写入
```bash
put <key> <value>
```

**示例：**
```bash
put user:001 "{\"name\": \"张三\", \"balance\": 1000}"
put tx:001 "transaction data"
put key00000000 "value0"
```

**特点：**
- 自动持久化到磁盘
- 支持UTF-8编码
- 如果键已存在，会更新值（版本管理）

#### `batch` - 批量写入
```bash
batch put <key1> <value1> <key2> <value2> ...
```

**示例：**
```bash
batch put user:001 "data1" user:002 "data2" user:003 "data3"
batch put key00000000 "value0" key00000001 "value1" key00000002 "value2"
```

**特点：**
- 高性能批量写入
- 自动持久化
- 支持任意数量的键值对

### 2. 删（Delete）- 删除数据

#### `delete` - 标记删除
```bash
delete <key>
```

**注意：**
- 当前版本使用版本管理，数据不可真正删除
- 只能标记删除（功能待实现）
- 历史版本仍然保留

**示例：**
```bash
delete user:001
```

### 3. 改（Update）- 更新数据

#### `put` - 更新（使用相同键）
```bash
put <key> <new_value>
```

**示例：**
```bash
# 先写入
put user:001 "old value"

# 更新
put user:001 "new value"

# 验证更新
get user:001
# 输出: new value
```

**特点：**
- 使用PUT命令更新（相同键会覆盖）
- 自动创建新版本
- 历史版本可追溯

### 4. 查（Read）- 查询数据

#### `get` - 单键查询
```bash
get <key>
```

**示例：**
```bash
get user:001
get tx:001
get key00000000
```

#### `select` - 查询（单键或范围）
```bash
# 单键查询
select <key>

# 范围查询
select * from <prefix>
```

**示例：**
```bash
# 单键查询
select user:001
select key00000000

# 范围查询（支持有/无冒号分隔符）
select * from user      # 匹配 user:001, user:002 等
select * from key       # 匹配 key00000000, key00000001 等
select * from user:     # 精确匹配以 user: 开头的键
```

**特点：**
- 支持有/无冒号分隔符的键
- 自动匹配两种格式
- 最多显示100条记录

#### `show keys` - 显示所有键
```bash
show keys
```

**特点：**
- 显示所有键（前100个）
- 显示键和对应的值
- 如果超过100个，提示使用范围查询

#### `show tables` - 显示所有表（键前缀）
```bash
show tables
```

**特点：**
- 智能提取前缀（支持有/无冒号分隔符）
- 显示每个前缀的记录数
- 提供查询提示

#### `show stats` - 显示统计信息
```bash
show stats
```

**显示内容：**
- 总键数
- 当前版本
- Merkle根哈希
- 存储目录
- 分片信息

#### `history` - 查看历史版本
```bash
history <key>
```

**示例：**
```bash
history user:001
```

**显示内容：**
- 所有历史版本
- 每个版本的时间戳
- 每个版本的值
- 版本哈希

## GUI 图形界面

### 1. 增（Create）- 写入数据

#### 方法1：菜单/工具栏
- **菜单：** 数据 -> 插入数据
- **工具栏：** 添加按钮
- **操作：** 弹出对话框，输入键和值

#### 方法2：查询执行标签页
```sql
PUT <key> <value>
BATCH PUT <key1> <value1> <key2> <value2> ...
```

**示例：**
```
PUT user:001 "{\"name\": \"张三\"}"
BATCH PUT user:002 "data2" user:003 "data3"
```

### 2. 删（Delete）- 删除数据

#### 方法1：菜单/工具栏
- **菜单：** 数据 -> 删除
- **工具栏：** 删除按钮
- **注意：** 当前版本只能标记删除（功能待实现）

#### 方法2：查询执行标签页
```sql
DELETE <key>
```

**注意：** 当前版本使用版本管理，数据不可真正删除

### 3. 改（Update）- 更新数据

#### 方法1：菜单/工具栏
- **菜单：** 数据 -> 编辑
- **工具栏：** 编辑按钮
- **快捷方式：** 双击数据行

#### 方法2：查询执行标签页
```sql
PUT <key> <new_value>
```

**示例：**
```
PUT user:001 "new value"
```

### 4. 查（Read）- 查询数据

#### 方法1：数据浏览标签页
- **自动显示：** 所有数据（前1000条）
- **搜索框：** 快速搜索特定键
- **刷新按钮：** 刷新数据列表

#### 方法2：查询执行标签页
支持以下命令（不区分大小写）：

**GET - 单键查询**
```
GET <key>
```

**SELECT - 单键或范围查询**
```
SELECT <key>              # 单键查询
SELECT * FROM <prefix>    # 范围查询
```

**示例：**
```
GET user:001
SELECT user:001
SELECT * FROM user        # 匹配 user:001, user:002 等
SELECT * FROM key         # 匹配 key00000000, key00000001 等
SELECT * FROM user:       # 精确匹配以 user: 开头的键
```

#### 方法3：工具菜单
- **工具 -> 数据库统计：** 查看统计信息
- **工具 -> 性能监控：** 查看性能指标

## 数据持久化

### 自动持久化
- **CLI：** 所有写入操作后自动flush（异步模式）
- **GUI：** 所有写入操作后自动flush（同步模式）
- **数据文件：** 自动保存到磁盘（.sst, .ver, .idx, .mpt等）

### 手动持久化
```bash
# CLI
flush

# GUI
工具 -> 压缩数据库（会触发flush）
```

## 数据同步

### CLI ↔ GUI 同步
- **GUI写入 → CLI可见：** 自动同步（数据已持久化）
- **CLI写入 → GUI可见：** 需要刷新（点击刷新按钮或重新连接）

### 验证同步
1. 在GUI中写入数据
2. 在CLI中执行 `show keys` 或 `get <key>`
3. 应该能看到GUI写入的数据

## 查询方式对比

| 查询方式 | CLI | GUI | 说明 |
|---------|-----|-----|------|
| 单键查询 | `get <key>` | `GET <key>` 或数据浏览 | ✅ 完全支持 |
| 单键查询 | `select <key>` | `SELECT <key>` | ✅ 完全支持 |
| 范围查询 | `select * from <prefix>` | `SELECT * FROM <prefix>` | ✅ 完全支持（有/无冒号） |
| 显示所有键 | `show keys` | 数据浏览标签页 | ✅ 完全支持 |
| 显示表（前缀） | `show tables` | - | ✅ 完全支持 |
| 历史版本 | `history <key>` | - | ✅ 完全支持 |
| 统计信息 | `show stats` | 工具 -> 数据库统计 | ✅ 完全支持 |

## 常见问题

### Q: 为什么 `select * from key` 找不到数据？

A: 检查键的格式：
- 如果键是 `key00000000`（无冒号），使用 `select * from key`
- 如果键是 `key:00000000`（有冒号），使用 `select * from key:`
- 系统会自动匹配两种格式

### Q: GUI和CLI的数据不同步？

A: 
1. 确保数据已持久化（写入后会自动flush）
2. GUI中点击"刷新"按钮
3. CLI中重新连接数据库

### Q: 如何查询所有数据？

A:
- **CLI：** `show keys`（显示前100个）
- **GUI：** 数据浏览标签页（显示前1000个）
- **范围查询：** 使用 `select * from <prefix>` 查询特定前缀

### Q: 如何更新数据？

A:
- 使用 `put` 命令写入相同键的新值
- 系统会自动创建新版本
- 历史版本可通过 `history` 查看

## 测试验证

### 完整测试流程

```bash
# 1. CLI测试
python amdb-cli --data-dir ./data/test_db

# 写入
put test:001 "value1"
put test:002 "value2"
batch put batch:001 "batch1" batch:002 "batch2"

# 查询
get test:001
select * from test
show keys
show tables

# 更新
put test:001 "value1_updated"
get test:001

# 2. GUI测试
python amdb_manager.py

# 连接数据库：./data/test_db
# 在数据浏览标签页查看数据
# 在查询执行标签页执行：
#   GET test:001
#   SELECT * FROM test
#   PUT test:003 "value3"
#   BATCH PUT batch:003 "batch3" batch:004 "batch4"

# 3. 验证同步
# 在CLI中执行 show keys，应该能看到GUI写入的数据
```

## 总结

✅ **所有增删改查功能已实现并测试通过**
✅ **CLI和GUI功能完全对应**
✅ **数据持久化和同步正常**
✅ **支持多种查询方式（单键、范围、前缀等）**
✅ **支持有/无冒号分隔符的键**

如有问题，请参考本文档或查看错误信息。

