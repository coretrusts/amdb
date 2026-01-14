#!/bin/bash
# -*- coding: utf-8 -*-
# 创建并推送amdb-bindings仓库

set -e

ORG="coretrusts"
PROJECT_DIR="/Users/mac/Documents/Project Manager/renew/AI Talk/AmDb"
GIT_BASE="git@github.com:$ORG"

cd "$PROJECT_DIR"

echo "=========================================="
echo "创建 amdb-bindings 仓库"
echo "=========================================="
echo ""

# 检查bindings目录
if [ ! -d "bindings" ]; then
    echo "✗ bindings目录不存在"
    exit 1
fi

echo "步骤1: 请在GitHub上手动创建仓库"
echo "----------------------------------------"
echo "访问: https://github.com/organizations/$ORG/repositories/new"
echo "仓库名称: amdb-bindings"
echo "描述: AmDb - 多语言开发绑定 (C, C++, Go, Java, Kotlin, Node.js, PHP, Ruby, Rust, Swift)"
echo "可见性: Public"
echo ""
read -p "按回车键继续（确认已创建仓库）..."

echo ""
echo "步骤2: 推送bindings内容"
echo "----------------------------------------"

TEMP=$(mktemp -d)
cp -r bindings/* "$TEMP/" 2>/dev/null || true

cat > "$TEMP/README.md" << 'BINDINGS_EOF'
# AmDb 多语言绑定

本仓库包含AmDb数据库系统的多语言开发绑定。

## 支持的语言

- **C** (`c/`) - C语言绑定
- **C++** (`cpp/`) - C++语言绑定
- **Go** (`go/`) - Go语言绑定
- **Java** (`java/`) - Java语言绑定
- **Kotlin** (`kotlin/`) - Kotlin语言绑定
- **Node.js** (`nodejs/`) - JavaScript/Node.js绑定
- **PHP** (`php/`) - PHP语言绑定
- **Ruby** (`ruby/`) - Ruby语言绑定
- **Rust** (`rust/`) - Rust语言绑定
- **Swift** (`swift/`) - Swift语言绑定

## 使用

每个语言目录包含对应的绑定代码和使用示例。请参考各语言的README或示例代码。

## 快速开始

### C/C++

```c
#include "amdb.h"

// 创建数据库连接
AmDbHandle* db = amdb_open("./data/mydb");

// 写入数据
amdb_put(db, "key1", "value1");

// 读取数据
char* value = amdb_get(db, "key1");
```

### Go

```go
import "github.com/coretrusts/amdb-bindings/go"

db := amdb.Open("./data/mydb")
defer db.Close()

db.Put("key1", "value1")
value := db.Get("key1")
```

### Node.js

```javascript
const amdb = require('@coretrusts/amdb');

const db = amdb.open('./data/mydb');
db.put('key1', 'value1');
const value = db.get('key1');
```

### PHP

```php
<?php
require_once 'amdb.php';

$db = new AmDb('./data/mydb');
$db->put('key1', 'value1');
$value = $db->get('key1');
```

## 其他资源

- **源代码**: https://github.com/coretrusts/amdb
- **文档**: https://github.com/coretrusts/amdb-docs
- **发行版**: https://github.com/coretrusts/amdb-releases
BINDINGS_EOF

cd "$TEMP"
git init
git remote add origin "$GIT_BASE/amdb-bindings.git" 2>/dev/null || \
    git remote set-url origin "$GIT_BASE/amdb-bindings.git"

git add .
git commit -m "Initial commit: All language bindings - $(date +%Y-%m-%d)"
git branch -M main

echo ""
echo "推送中..."
git push -u origin main --force

cd "$PROJECT_DIR"
rm -rf "$TEMP"

echo ""
echo "=========================================="
echo "✓ 完成！"
echo "=========================================="
echo ""
echo "仓库地址: https://github.com/$ORG/amdb-bindings"
echo ""
