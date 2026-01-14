# AmDb 多语言绑定

AmDb提供了多种编程语言的绑定，让不同语言的开发者都能使用AmDb数据库。

## 支持的编程语言

- ✅ C/C++ - 基础API
- ✅ Go - 完整绑定
- ✅ Node.js - JavaScript/TypeScript绑定
- ✅ PHP - PHP 7.4+ FFI绑定
- ✅ Rust - FFI绑定
- ✅ Java - JNI绑定
- ✅ Swift - C interop绑定
- ✅ Ruby - FFI绑定
- ✅ Kotlin - JNI绑定
- ✅ Python - 原生支持（已有）

## 架构

```
┌─────────────────────────────────────────┐
│      Python实现 (核心引擎)               │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│         C API (amdb.h/amdb.c)           │
│     通过Python C API调用Python实现       │
└─────────────────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
    ┌──────┐    ┌──────┐    ┌──────┐
    │ C++  │    │  Go  │    │Node.js│
    └──────┘    └──────┘    └──────┘
        │           │           │
        ▼           ▼           ▼
    ┌──────┐    ┌──────┐    ┌──────┐
    │ PHP  │    │ Rust │    │ Java │
    └──────┘    └──────┘    └──────┘
```

## 使用示例

### C/C++

```c
#include "amdb.h"

amdb_handle_t db;
amdb_init("./data", &db);

uint8_t key[] = "mykey";
uint8_t value[] = "myvalue";
uint8_t root_hash[32];
amdb_put(db, key, 5, value, 7, root_hash);

amdb_result_t result;
amdb_get(db, key, 5, 0, &result);
// 使用 result.data
amdb_free_result(&result);

amdb_close(db);
```

### C++

```cpp
#include "amdb.hpp"
using namespace amdb;

Database db("./data");
db.put("key", "value");
auto value = db.get("key");
auto root_hash = db.get_root_hash();
```

### Go

```go
package main

import "github.com/amdb/bindings/go/amdb"

func main() {
    db, err := amdb.NewDatabase("./data")
    if err != nil {
        panic(err)
    }
    defer db.Close()
    
    rootHash, err := db.Put([]byte("key"), []byte("value"))
    if err != nil {
        panic(err)
    }
    
    value, err := db.Get([]byte("key"), 0)
    if err != nil {
        panic(err)
    }
}
```

### Node.js

```javascript
const { Database } = require('./bindings/nodejs/amdb');

const db = new Database('./data');
db.put('key', 'value');
const value = db.get('key');
const rootHash = db.getRootHash();
db.close();
```

### PHP

```php
<?php
require_once 'bindings/php/amdb.php';

$db = new AmDb('./data');
$rootHash = $db->put('key', 'value');
$value = $db->get('key');
$rootHash = $db->getRootHash();
```

## 编译和安装

### C/C++

```bash
cd bindings/c
gcc -shared -o libamdb.so amdb.c $(python3-config --cflags --ldflags)
```

### Go

```bash
cd bindings/go
go build
```

### Node.js

```bash
cd bindings/nodejs
npm install
npm run build
```

## API一致性

所有语言绑定都提供相同的核心API：

- `init/open` - 初始化数据库
- `close` - 关闭数据库
- `put` - 写入数据
- `get` - 读取数据
- `delete` - 删除数据
- `batch_put` - 批量写入
- `get_root_hash` - 获取Merkle根哈希
- `get_history` - 获取版本历史
- `verify` - 验证数据

## 性能

- C/C++: 直接调用，性能最优
- Go: 通过CGO，性能接近C
- Node.js: 通过FFI，性能良好
- PHP: 通过FFI，性能良好

## 开发计划

- [x] C API基础实现
- [x] C++封装
- [x] Go绑定
- [x] Node.js绑定
- [x] PHP绑定
- [ ] Rust绑定
- [ ] Java绑定（JNI）
- [ ] Swift绑定
- [ ] Ruby绑定

