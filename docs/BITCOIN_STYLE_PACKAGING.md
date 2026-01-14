# 类似比特币的打包方案

## 概述

参考比特币将LevelDB打包到安装包的方式，AmDb采用相同的策略，将数据库核心库（包括原生扩展）打包到分发包中。

## 比特币的LevelDB打包方式

比特币的做法：
1. **静态链接**: LevelDB编译为静态库，链接到bitcoind
2. **自包含**: 不依赖系统安装的LevelDB
3. **版本控制**: 确保使用特定版本的LevelDB
4. **跨平台**: 为每个平台编译对应的版本

## AmDb的实现方案

### 1. 目录结构

```
amdb-1.0.0-linux-x86_64/
├── src/              # Python源代码（类似bitcoin的src目录）
│   └── amdb/
│       ├── storage/  # 存储引擎
│       ├── database.py
│       └── ...
├── lib/              # 编译好的原生扩展（类似bitcoin的lib目录）
│   ├── skip_list_cython.cpython-313-x86_64-linux-gnu.so
│   ├── version_cython.cpython-313-x86_64-linux-gnu.so
│   └── ...
├── config/           # 配置文件
│   └── amdb.ini
├── bindings/         # 多语言绑定
├── docs/             # 文档
├── examples/         # 示例代码
├── amdb-server       # 服务器启动脚本
├── amdb-cli          # CLI启动脚本
├── amdb-manager      # GUI启动脚本
├── install.sh        # 安装脚本
└── README_DIST.txt    # 分发说明
```

### 2. 原生扩展打包

#### 编译阶段
```bash
# 编译Cython扩展
python3 setup_cython.py build_ext --inplace

# 生成的文件：
# - src/amdb/storage/skip_list_cython.cpython-313-x86_64-linux-gnu.so
# - src/amdb/version_cython.cpython-313-x86_64-linux-gnu.so
```

#### 打包阶段
```bash
# 收集所有.so文件到lib目录
find src/amdb -name "*.so" -exec cp {} lib/ \;
```

### 3. 启动脚本设计

启动脚本自动设置环境变量，确保能找到原生扩展：

```bash
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 设置Python路径
export PYTHONPATH="$SCRIPT_DIR/src:$PYTHONPATH"

# 设置库路径（加载原生扩展）
if [ -d "$SCRIPT_DIR/lib" ]; then
    export LD_LIBRARY_PATH="$SCRIPT_DIR/lib:$LD_LIBRARY_PATH"
    export DYLD_LIBRARY_PATH="$SCRIPT_DIR/lib:$DYLD_LIBRARY_PATH"
fi

# 启动服务
cd "$SCRIPT_DIR" || exit 1
python3 -m src.amdb.server "$@"
```

### 4. 构建流程

```bash
# 完整构建流程
./build_complete_package.sh

# 或分步执行：
# 1. 编译原生扩展
python3 setup_cython.py build_ext --inplace

# 2. 打包CLI/GUI
./build_all_platforms.sh

# 3. 创建分发包
./build_distribution.sh
```

### 5. 优势对比

| 特性 | 比特币方式 | AmDb方式 | 优势 |
|------|-----------|---------|------|
| 自包含 | ✅ 静态链接LevelDB | ✅ 打包原生扩展 | 无需外部依赖 |
| 版本控制 | ✅ 固定LevelDB版本 | ✅ 固定扩展版本 | 确保兼容性 |
| 跨平台 | ✅ 多平台编译 | ✅ 多平台编译 | 支持所有平台 |
| 易部署 | ✅ 单文件可执行 | ✅ 解压即用 | 简化部署 |

### 6. 使用方式

#### 方式1: 直接使用（无需安装）

```bash
# 解压分发包
tar -xzf amdb-1.0.0-linux-x86_64.tar.gz
cd amdb-1.0.0-linux-x86_64

# 直接运行（自动加载lib目录中的扩展）
./amdb-server
./amdb-cli
./amdb-manager
```

#### 方式2: 安装到系统

```bash
# 解压分发包
tar -xzf amdb-1.0.0-linux-x86_64.tar.gz
cd amdb-1.0.0-linux-x86_64

# 运行安装脚本
sudo ./install.sh

# 安装后可直接使用命令
amdb-server
amdb-cli
amdb-manager
```

### 7. 与比特币的对比

#### 比特币的LevelDB集成
- **位置**: `src/leveldb/` (源码) 或静态链接
- **编译**: 在构建bitcoind时一起编译
- **使用**: 直接链接，无需运行时加载

#### AmDb的原生扩展集成
- **位置**: `lib/` (编译好的.so/.pyd文件)
- **编译**: 使用Cython编译为Python扩展
- **使用**: 运行时动态加载，通过PYTHONPATH和LD_LIBRARY_PATH

### 8. 维护和更新

#### 更新原生扩展
```bash
# 重新编译
python3 setup_cython.py build_ext --inplace

# 重新打包
./build_distribution.sh
```

#### 版本管理
- 版本号在 `src/amdb/__init__.py` 中定义
- 分发包文件名包含版本号
- 确保版本一致性

### 9. 多平台支持

为每个平台构建独立的分发包：

```bash
# Linux x86_64
./build_distribution.sh  # 在Linux上运行

# macOS (Intel)
./build_distribution.sh  # 在macOS Intel上运行

# macOS (Apple Silicon)
./build_distribution.sh  # 在macOS ARM上运行

# Windows
build_distribution.bat   # 在Windows上运行
```

### 10. 最佳实践

1. **版本一致性**: 确保所有组件使用相同版本
2. **测试验证**: 打包后测试所有功能
3. **文档完整**: 包含使用说明和安装指南
4. **签名验证**: 对分发包进行签名（可选）
5. **依赖最小化**: 只包含必要的文件

## 总结

AmDb采用类似比特币的打包方式，将数据库核心库（原生扩展）打包到分发包中，实现：

- ✅ **自包含**: 不依赖外部数据库库
- ✅ **可移植**: 包含所有必要的二进制文件
- ✅ **易部署**: 解压即用，无需额外安装
- ✅ **版本控制**: 确保使用正确的扩展版本

这使得AmDb可以像比特币一样，作为一个完整的、自包含的数据库系统进行分发和部署。

