# AmDb 快速开始指南

## 安装方式

### 方式1: 使用分发包（推荐，类似比特币）

```bash
# 下载分发包
wget https://github.com/amdb/amdb/releases/download/v1.0.0/amdb-1.0.0-linux-x86_64.tar.gz

# 解压
tar -xzf amdb-1.0.0-linux-x86_64.tar.gz
cd amdb-1.0.0-linux-x86_64

# 直接使用（无需安装）
./amdb-server    # 启动服务器
./amdb-cli       # 命令行工具
./amdb-manager   # GUI管理器

# 或安装到系统
sudo ./install.sh
```

### 方式2: 从源码安装

```bash
# 克隆仓库
git clone https://github.com/amdb/amdb.git
cd amdb

# 安装
sudo ./install.sh
```

## 快速使用

### 1. 启动服务器

```bash
# 使用默认配置
amdb-server

# 指定配置
amdb-server --config /path/to/config.ini

# 指定数据目录
amdb-server --data-dir ./data/my_database
```

### 2. 使用命令行工具

```bash
# 启动CLI
amdb-cli

# 连接数据库
amdb-cli --connect ./data/my_database

# 在CLI中执行命令
amdb> put user:001 "{\"name\": \"张三\"}"
amdb> get user:001
amdb> show stats
```

### 3. 使用GUI管理器

```bash
# 启动GUI
amdb-manager

# 或双击图标（如果已安装）
```

## 程序化使用

```python
from src.amdb import Database

# 创建数据库
db = Database(data_dir='./data/my_database')

# 写入数据
db.put(b'user:001', b'{"name": "张三"}')

# 读取数据
value = db.get(b'user:001')
print(value)

# 批量写入
items = [
    (b'user:002', b'{"name": "李四"}'),
    (b'user:003', b'{"name": "王五"}'),
]
db.batch_put(items)

# 刷新到磁盘
db.flush()
```

## 分发包结构（类似比特币）

```
amdb-1.0.0-linux-x86_64/
├── src/              # Python源代码
├── lib/              # 编译好的原生扩展（类似比特币的lib目录）
│   ├── skip_list_cython.so
│   └── version_cython.so
├── config/           # 配置文件
├── bindings/         # 多语言绑定
├── amdb-server       # 服务器启动脚本
├── amdb-cli          # CLI启动脚本
├── amdb-manager      # GUI启动脚本
└── install.sh        # 安装脚本
```

## 维护命令

```bash
# 备份数据库
python3 -m src.amdb.backup --source ./data/my_database --output ./backup.tar.gz

# 查看统计信息
amdb-cli --stats

# 查看日志
tail -f /usr/local/amdb/logs/amdb.log

# 系统服务管理（Linux）
sudo systemctl start amdb
sudo systemctl stop amdb
sudo systemctl status amdb
```

## 更多信息

- 详细文档: `docs/INSTALLATION_AND_MAINTENANCE.md`
- 配置说明: `docs/DATABASE_CONFIG.md`
- API文档: `docs/API.md`

