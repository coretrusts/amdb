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
