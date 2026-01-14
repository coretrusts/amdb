# AmDb 多语言支持文档

## 概述

AmDb提供了完整的多语言绑定支持，让不同编程语言的开发者都能方便地使用AmDb数据库。所有绑定都基于统一的C API，确保功能一致性和性能。

## 架构设计

```
Python核心实现 (src/amdb/)
         ↓
    C API层 (bindings/c/)
         ↓
    ┌────┴────┬────────┬────────┬────────┬────────┐
    ↓         ↓        ↓        ↓        ↓        ↓
  C++      Go      Node.js   PHP     Rust    Java
```

## 各语言绑定详情

### 1. C/C++ 绑定

**位置**: `bindings/c/`

**特点**:
- 基础API，所有其他绑定的基础
- 通过Python C API调用Python实现
- 提供完整的C接口

**使用**:
```c
#include "amdb.h"

amdb_handle_t db;
amdb_init("./data", &db);
amdb_put(db, key, key_len, value, value_len, root_hash);
amdb_close(db);
```

### 2. C++ 绑定

**位置**: `bindings/cpp/`

**特点**:
- 面向对象的C++封装
- 自动内存管理
- 支持移动语义

**使用**:
```cpp
#include "amdb.hpp"
using namespace amdb;

Database db("./data");
db.put("key", "value");
auto value = db.get("key");
```

### 3. Go 绑定

**位置**: `bindings/go/`

**特点**:
- 通过CGO调用C API
- 完整的Go接口
- 自动垃圾回收

**使用**:
```go
import "github.com/amdb/bindings/go/amdb"

db, _ := amdb.NewDatabase("./data")
defer db.Close()
db.Put([]byte("key"), []byte("value"))
```

### 4. Node.js 绑定

**位置**: `bindings/nodejs/`

**特点**:
- 使用node-ffi调用C库
- 支持异步操作
- TypeScript类型定义

**使用**:
```javascript
const { Database } = require('amdb');
const db = new Database('./data');
db.put('key', 'value');
```

### 5. PHP 绑定

**位置**: `bindings/php/`

**特点**:
- 使用PHP 7.4+ FFI
- 原生PHP接口
- 自动资源管理

**使用**:
```php
$db = new AmDb('./data');
$db->put('key', 'value');
$value = $db->get('key');
```

### 6. Rust 绑定

**位置**: `bindings/rust/`

**特点**:
- 使用FFI调用C API
- 内存安全保证
- 零成本抽象

**使用**:
```rust
use amdb::Database;
let db = Database::new("./data")?;
db.put(b"key", b"value")?;
```

### 7. Java 绑定

**位置**: `bindings/java/`

**特点**:
- 使用JNI调用C API
- 完整的Java接口
- 自动资源管理

**使用**:
```java
import com.amdb.AmDb;
AmDb db = new AmDb("./data");
db.put("key".getBytes(), "value".getBytes());
```

## API一致性

所有语言绑定都提供相同的核心功能：

| 功能 | C | C++ | Go | Node.js | PHP | Rust | Java |
|------|---|---|---|--------|-----|------|------|
| 初始化 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 写入 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 读取 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 删除 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 批量写入 | ✅ | ✅ | ✅ | ✅ | 🔄 | 🔄 | 🔄 |
| 范围查询 | 🔄 | 🔄 | 🔄 | 🔄 | 🔄 | 🔄 | 🔄 |
| 版本历史 | 🔄 | 🔄 | 🔄 | 🔄 | 🔄 | 🔄 | 🔄 |
| Merkle验证 | 🔄 | 🔄 | 🔄 | 🔄 | 🔄 | 🔄 | 🔄 |

## 性能对比

| 语言 | 调用开销 | 性能 | 内存管理 |
|------|---------|------|---------|
| C/C++ | 最低 | 最优 | 手动 |
| Go | 低 | 优秀 | 自动GC |
| Rust | 低 | 优秀 | 自动（零成本） |
| Node.js | 中等 | 良好 | 自动GC |
| PHP | 中等 | 良好 | 自动GC |
| Java | 中等 | 良好 | 自动GC |

## 编译和安装

### 编译C库

```bash
cd bindings/c
gcc -shared -fPIC -o libamdb.so amdb.c \
    $(python3-config --cflags --ldflags)
```

### 编译各语言绑定

**Go**:
```bash
cd bindings/go
go build
```

**Rust**:
```bash
cd bindings/rust
cargo build --release
```

**Java**:
```bash
cd bindings/java
javac -h src/main/c src/main/java/com/amdb/AmDb.java
gcc -shared -o libamdb_jni.so -I$JAVA_HOME/include \
    -I$JAVA_HOME/include/linux src/main/c/amdb_jni.c
```

## 最佳实践

1. **选择合适语言**: 根据项目需求选择绑定
2. **性能优先**: 对性能要求高的场景使用C/C++/Go/Rust
3. **开发效率**: 快速开发可使用Node.js/PHP/Java
4. **内存管理**: 注意各语言的内存管理特性

## 贡献

欢迎为其他语言创建绑定！请参考现有绑定的实现方式。

