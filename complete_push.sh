#!/bin/bash
# -*- coding: utf-8 -*-
# 完整分类推送脚本 - 确保所有文件正确推送到对应仓库

set -e

ORG="coretrusts"
PROJECT_DIR="/Users/mac/Documents/Project Manager/renew/AI Talk/AmDb"
GIT_BASE="git@github.com:$ORG"

cd "$PROJECT_DIR"

echo "=========================================="
echo "AmDb 完整分类推送"
echo "=========================================="
echo ""

# 函数：推送更新
push_update() {
    local repo=$1
    local temp_dir=$2
    local commit_msg=$3
    
    cd "$temp_dir"
    git init
    git remote add origin "$GIT_BASE/$repo.git" 2>/dev/null || \
        git remote set-url origin "$GIT_BASE/$repo.git"
    
    git add .
    if ! git diff --staged --quiet; then
        git commit -m "$commit_msg" 2>/dev/null || true
        git branch -M main
        git push -u origin main --force 2>&1 | tail -3
        echo "✓ $repo 更新成功"
    else
        echo "  $repo 无更改"
    fi
    cd "$PROJECT_DIR"
}

# ==========================================
# 1. 源代码仓库 (amdb)
# ==========================================
echo "1. 更新源代码仓库 (amdb)"
echo "----------------------------------------"

TEMP_SOURCE=$(mktemp -d)
mkdir -p "$TEMP_SOURCE/src" "$TEMP_SOURCE/tests" "$TEMP_SOURCE/examples"

# 复制源代码
echo "  复制源代码..."
cp -r src/* "$TEMP_SOURCE/src/" 2>/dev/null || true
cp -r tests/* "$TEMP_SOURCE/tests/" 2>/dev/null || true
cp -r examples/* "$TEMP_SOURCE/examples/" 2>/dev/null || true

# 复制核心程序文件
echo "  复制核心文件..."
for f in amdb-server amdb-cli amdb.ini Makefile requirements.txt setup.py setup_cython.py README.md LICENSE .gitignore; do
    [ -f "$f" ] && cp "$f" "$TEMP_SOURCE/" 2>/dev/null || true
done

# 复制Python脚本（不包括GUI，GUI在独立仓库）
for f in create_*.py verify_*.py test_*.py quick_performance_test.py blockchain_stress_test.py; do
    [ -f "$f" ] && cp "$f" "$TEMP_SOURCE/" 2>/dev/null || true
done

# 更新README
cat > "$TEMP_SOURCE/README.md" << 'SOURCE_EOF'
# AmDb - 区块链优化数据库系统

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)

AmDb是一个专为区块链应用优化的高性能数据库系统。

## 特性

- 🚀 **高性能**: 优化的存储引擎，支持大规模数据
- 🔒 **数据完整性**: Merkle Tree验证，确保数据不被篡改
- 📦 **版本管理**: 完整的版本历史和时间点查询
- 🌐 **网络支持**: 服务器-客户端架构，支持远程操作
- 🖥️ **多平台**: 支持macOS、Linux、Windows
- 🛠️ **完整工具**: CLI命令行工具和GUI图形界面管理器
- 📚 **多数据库**: 支持创建和管理多个独立数据库实例

## 快速开始

### 安装

```bash
pip install -r requirements.txt
python3 setup.py install
```

### 使用

```python
from src.amdb.database import Database

db = Database('./data/mydb')
db.put(b'key1', b'value1')
value = db.get(b'key1')
```

### 启动服务器

```bash
./amdb-server
# 或
python3 -m src.amdb.server
```

### 使用CLI

```bash
./amdb-cli
# 连接本地数据库
> connect ./data/mydb
# 连接远程数据库
> connect --host 127.0.0.1 --port 3888 --database mydb
```

## 项目结构

```
AmDb/
├── src/amdb/          # 源代码
│   ├── storage/       # 存储引擎
│   ├── network/       # 网络通信
│   └── ...
├── tests/             # 测试代码
├── examples/          # 示例代码
├── amdb-server        # 服务器启动脚本
├── amdb-cli           # CLI启动脚本
├── amdb.ini           # 配置文件
└── Makefile           # 构建文件
```

## 配置

配置文件 `amdb.ini` 包含所有可配置项：

- **网络配置**: 端口3888（默认），监听地址0.0.0.0
- **性能配置**: 批量大小3000，分片256
- **多线程配置**: 启用多线程，最大工作线程4
- **存储配置**: MemTable 10MB，文件大小256MB

详细配置说明请查看 [文档仓库](https://github.com/coretrusts/amdb-docs)。

## 文档

- **文档**: https://github.com/coretrusts/amdb-docs
- **发行版**: https://github.com/coretrusts/amdb-releases
- **多语言绑定**: https://github.com/coretrusts/amdb-bindings
- **脚本工具**: https://github.com/coretrusts/amdb-scripts

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 作者

CoreTrusts Organization
SOURCE_EOF

push_update "amdb" "$TEMP_SOURCE" "Update: Complete source code with all core files - $(date +%Y-%m-%d)"
rm -rf "$TEMP_SOURCE"

# ==========================================
# 2. 文档仓库 (amdb-docs)
# ==========================================
echo ""
echo "2. 更新文档仓库 (amdb-docs)"
echo "----------------------------------------"

TEMP_DOCS=$(mktemp -d)
cp -r docs/* "$TEMP_DOCS/" 2>/dev/null || true

cat > "$TEMP_DOCS/README.md" << 'DOCS_EOF'
# AmDb 文档

本仓库包含AmDb数据库系统的完整文档。

## 文档索引

### 核心文档
- [网络架构](NETWORK_ARCHITECTURE.md) - 服务器-客户端架构说明
- [集成指南](INTEGRATION_GUIDE.md) - 如何在项目中使用AmDb
- [文件格式](FILE_FORMAT.md) - 数据文件格式规范
- [配置指南](CONFIG_GUIDE.md) - 配置文件说明

### 功能文档
- [构建和打包](BUILD_AND_PACKAGE.md) - 编译和打包指南
- [远程操作](REMOTE_OPERATIONS.md) - 远程操作支持说明
- [删除功能](DELETE_FEATURES.md) - 删除功能说明
- [GUI管理器](GUI_MANAGER.md) - GUI管理器使用指南
- [多数据库管理](MULTI_DATABASE_GUIDE.md) - 多数据库管理指南

### 架构文档
- [架构设计](ARCHITECTURE.md) - 系统架构说明
- [大数据架构](BIG_DATA_ARCHITECTURE.md) - 大数据处理架构
- [分布式架构](DISTRIBUTED_ARCHITECTURE.md) - 分布式系统设计
- [分片和分区](SHARDING_AND_PARTITIONING.md) - 数据分片策略

### 性能文档
- [性能基准](PERFORMANCE_BENCHMARK.md) - 性能测试结果
- [性能对比](PERFORMANCE_COMPARISON.md) - 与其他数据库对比
- [多线程](THREADING.md) - 多线程配置和使用

### 其他文档
- [CLI指南](CLI_GUIDE.md) - 命令行工具使用
- [安装和维护](INSTALLATION_AND_MAINTENANCE.md) - 安装和维护指南
- [服务器打包](SERVER_PACKAGING.md) - 服务器打包说明

## 快速开始

查看 [集成指南](INTEGRATION_GUIDE.md) 了解如何在自己的项目中使用AmDb。

## 其他资源

- **源代码**: https://github.com/coretrusts/amdb
- **发行版**: https://github.com/coretrusts/amdb-releases
- **多语言绑定**: https://github.com/coretrusts/amdb-bindings
DOCS_EOF

push_update "amdb-docs" "$TEMP_DOCS" "Update: All documentation files - $(date +%Y-%m-%d)"
rm -rf "$TEMP_DOCS"

echo ""
echo "=========================================="
echo "推送完成！"
echo "=========================================="
echo ""
echo "仓库地址:"
echo "  源代码: https://github.com/$ORG/amdb"
echo "  文档:   https://github.com/$ORG/amdb-docs"
echo ""
