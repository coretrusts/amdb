# AmDb CLI 命令行工具使用指南

## 概述

AmDb提供了功能完整的命令行工具（CLI），类似MySQL的`mysql`命令行客户端，支持交互式命令行界面和数据库连接管理。

## 启动CLI

### 方法1：直接启动（不连接数据库）

```bash
python amdb-cli
```

或

```bash
python -m src.amdb.cli
```

### 方法2：启动时连接数据库

```bash
# 连接到指定数据库
python amdb-cli --data-dir ./data/user_db

# 使用指定配置文件
python amdb-cli --config ./amdb.ini --data-dir ./data/user_db
```

### 方法3：执行单条命令（非交互模式）

```bash
# 执行命令后退出
python amdb-cli --data-dir ./data/user_db --command "show stats"
```

## 可用命令

### 数据库连接管理

#### `connect` - 连接数据库

```
用法: connect [数据目录] [--config 配置文件路径]

示例:
  connect ./data/user_db
  connect ./data/transaction_db --config ./amdb.ini
  connect --config ./amdb.ini
```

#### `disconnect` - 断开连接

```
用法: disconnect
```

#### `use` - 切换数据库（快捷命令）

```
用法: use <数据目录>

示例:
  use ./data/user_db
  use ./data/transaction_db
```

### 信息查询

#### `show databases` - 显示所有数据库

```
显示所有已创建的数据库列表

示例:
  show databases
```

#### `show tables` - 显示所有表（键前缀）

```
显示当前数据库中所有的键前缀（类似表名）

示例:
  show tables
```

#### `show stats` - 显示数据库统计信息

```
显示当前数据库的统计信息，包括：
- 总键数
- 当前版本
- Merkle根哈希
- 存储目录
- 分片信息

示例:
  show stats
```

#### `show config` - 显示当前配置

```
显示当前数据库的配置信息

示例:
  show config
```

#### `show connection` - 显示当前连接信息

```
显示当前连接的数据库信息

示例:
  show connection
```

### 数据操作

#### `put` - 写入数据

```
用法: put <key> <value>

示例:
  put user:001 "{\"name\": \"张三\", \"balance\": 1000}"
  put tx:001 "transaction data"
```

#### `get` - 读取数据

```
用法: get <key>

示例:
  get user:001
  get tx:001
```

#### `select` - 查询数据

```
用法:
  select * from <prefix>    - 查询所有以prefix开头的键
  select <key>               - 查询指定键

示例:
  select * from user
  select user:001
```

#### `batch` - 批量写入

```
用法: batch put <key1> <value1> <key2> <value2> ...

示例:
  batch put user:001 "data1" user:002 "data2" user:003 "data3"
```

#### `history` - 查看历史版本

```
用法: history <key>

示例:
  history user:001
```

#### `delete` - 删除数据

```
用法: delete <key>

注意: 当前版本使用版本管理，数据不可删除（标记删除功能待实现）

示例:
  delete user:001
```

### 系统操作

#### `flush` - 强制刷新到磁盘

```
用法: flush

将内存中的数据强制刷新到磁盘
```

#### `clear` - 清空屏幕

```
用法: clear

清空终端屏幕
```

#### `exit` / `quit` - 退出CLI

```
用法: exit 或 quit

退出命令行工具
```

#### `help` - 显示帮助

```
用法:
  help              - 显示所有命令
  help <命令>        - 显示命令详细说明

示例:
  help
  help connect
  help put
```

## 使用示例

### 示例1：基本使用流程

```bash
# 1. 启动CLI
$ python amdb-cli

# 2. 查看所有数据库
amdb> show databases

# 3. 连接到用户数据库
amdb> connect ./data/user_db
✓ 已连接到数据库: ./data/user_db

# 4. 查看统计信息
amdb [./data/user_db]> show stats

# 5. 查看所有表
amdb [./data/user_db]> show tables

# 6. 查询数据
amdb [./data/user_db]> select * from user

# 7. 写入新数据
amdb [./data/user_db]> put user:006 "{\"name\": \"新用户\", \"balance\": 500}"

# 8. 读取数据
amdb [./data/user_db]> get user:006

# 9. 切换数据库
amdb [./data/user_db]> use ./data/transaction_db
✓ 已连接到数据库: ./data/transaction_db

# 10. 退出
amdb [./data/transaction_db]> exit
```

### 示例2：批量操作

```bash
$ python amdb-cli --data-dir ./data/user_db

amdb [./data/user_db]> batch put user:007 "data1" user:008 "data2" user:009 "data3"
✓ 批量写入成功: 3 条记录
  Merkle根哈希: a1b2c3d4e5f6...

amdb [./data/user_db]> select * from user
找到 8 条记录:
  user:001: {"name": "张三", "balance": 1000}
  user:002: {"name": "李四", "balance": 2000}
  ...
```

### 示例3：查看历史版本

```bash
$ python amdb-cli --data-dir ./data/user_db

amdb [./data/user_db]> put user:001 "{\"name\": \"张三\", \"balance\": 1500}"
✓ 写入成功

amdb [./data/user_db]> history user:001

键 'user:001' 的历史版本:
  版本 1:
    时间戳: 1705123456.789
    值: {"name": "张三", "balance": 1000}...
  版本 2:
    时间戳: 1705123500.123
    值: {"name": "张三", "balance": 1500}...
```

### 示例4：非交互模式

```bash
# 执行单条命令
$ python amdb-cli --data-dir ./data/user_db --command "show stats"

# 执行多条命令（使用分号分隔）
$ python amdb-cli --data-dir ./data/user_db --command "show stats; select * from user"
```

## 快捷键

- `Ctrl+D` - 退出CLI（同exit命令）
- `Ctrl+C` - 中断当前操作
- `↑` / `↓` - 命令历史（如果系统支持）

## 命令补全

CLI支持基本的命令补全，输入命令的前几个字母后按`Tab`键可以自动补全。

## 输出格式

- `✓` - 成功操作
- `✗` - 错误或失败
- `提示:` - 信息提示

## 注意事项

1. **数据目录路径**：可以使用相对路径或绝对路径
2. **键值格式**：键和值都支持UTF-8编码
3. **批量操作**：批量写入时，值中包含空格需要用引号括起来
4. **历史版本**：只有通过版本管理器创建的键才有历史版本
5. **数据删除**：当前版本不支持真正的删除，只能通过版本管理查看历史

## 与GUI管理器对比

| 功能 | CLI | GUI管理器 |
|------|-----|----------|
| 交互式操作 | ✅ | ✅ |
| 批量操作 | ✅ | ✅ |
| 数据浏览 | ✅（命令行） | ✅（图形界面） |
| 配置管理 | ✅ | ✅ |
| 性能监控 | ✅（命令行） | ✅（图形界面） |
| 脚本化 | ✅ | ❌ |
| 远程使用 | ✅ | ❌ |

## 常见问题

### Q: 如何查看所有可用命令？

A: 在CLI中输入 `help` 或 `?`

### Q: 如何查看命令的详细说明？

A: 输入 `help <命令名>`，例如 `help connect`

### Q: 如何退出CLI？

A: 输入 `exit` 或 `quit`，或按 `Ctrl+D`

### Q: 可以在脚本中使用CLI吗？

A: 可以，使用 `--command` 参数执行单条命令：

```bash
python amdb-cli --data-dir ./data/user_db --command "show stats"
```

### Q: 如何切换数据库？

A: 使用 `use <数据目录>` 命令，例如 `use ./data/transaction_db`

## 参考

- [多数据库管理指南](MULTI_DATABASE_GUIDE.md) - 多数据库创建和管理
- [配置指南](CONFIG_GUIDE.md) - 配置文件详细说明
- [GUI管理器](GUI_MANAGER.md) - 桌面版管理器使用说明

