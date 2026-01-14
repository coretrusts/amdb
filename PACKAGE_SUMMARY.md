# AmDb 打包编译总结

## 打包完成 ✅

### 打包结果

#### 1. 原生扩展编译
- ✅ `skip_list_cython.cpython-313-darwin.so` - SkipList优化扩展
- ✅ `version_cython.cpython-313-darwin.so` - 版本管理优化扩展

#### 2. CLI/GUI可执行文件
- ✅ **CLI**: `dist/darwin_x86_64/amdb-cli` (8.6MB)
- ✅ **GUI**: `dist/darwin_x86_64/amdb-manager` (11MB)

#### 3. 完整分发包（类似比特币方式）
- ✅ **分发包**: `dist/amdb-1.0.0-darwin-x86_64.tar.gz` (648KB压缩包)
- ✅ 包含所有源代码、原生扩展、配置文件、启动脚本

## 分发包结构

```
amdb-1.0.0-darwin-x86_64/
├── src/              # Python源代码
├── lib/              # 编译好的原生扩展（类似比特币的lib目录）
│   ├── skip_list_cython.cpython-313-darwin.so
│   └── version_cython.cpython-313-darwin.so
├── config/           # 配置文件
├── bindings/         # 多语言绑定
├── docs/             # 文档
├── examples/         # 示例代码
├── amdb-server       # 服务器启动脚本
├── amdb-cli          # CLI启动脚本
├── amdb-manager      # GUI启动脚本
├── install.sh        # 安装脚本（Linux/macOS）
├── install.bat       # 安装脚本（Windows）
└── README_DIST.txt   # 分发说明
```

## 使用方法

### 方式1: 直接使用（无需安装）

```bash
# 解压分发包
tar -xzf dist/amdb-1.0.0-darwin-x86_64.tar.gz
cd amdb-1.0.0-darwin-x86_64

# 直接运行
./amdb-server    # 启动服务器
./amdb-cli       # 命令行工具
./amdb-manager   # GUI管理器
```

### 方式2: 使用打包的可执行文件

```bash
# 直接运行打包好的可执行文件
./dist/darwin_x86_64/amdb-cli
./dist/darwin_x86_64/amdb-manager
```

### 方式3: 安装到系统

```bash
# 解压分发包
tar -xzf dist/amdb-1.0.0-darwin-x86_64.tar.gz
cd amdb-1.0.0-darwin-x86_64

# 运行安装脚本
sudo ./install.sh
```

## 打包命令

### 完整打包（推荐）

```bash
./build_complete_package.sh
```

### 分步打包

```bash
# 1. 编译原生扩展
./build_native.sh

# 2. 打包CLI/GUI
./build_all_platforms.sh

# 3. 创建分发包
./build_distribution.sh
```

## 类似比特币的打包方案

AmDb采用类似比特币将LevelDB打包的方式：

1. **自包含**: 所有原生扩展打包在`lib/`目录
2. **解压即用**: 无需安装，直接运行启动脚本
3. **版本控制**: 确保使用正确的扩展版本
4. **跨平台**: 为每个平台构建独立分发包

启动脚本自动设置环境变量：
- `PYTHONPATH`: 指向源代码目录
- `LD_LIBRARY_PATH`: 指向原生扩展目录

## 文件位置

- **CLI/GUI可执行文件**: `dist/darwin_x86_64/`
- **完整分发包**: `dist/amdb-1.0.0-darwin-x86_64.tar.gz`
- **原生扩展**: `amdb/storage/` 和 `amdb/` 目录

## 下一步

1. **测试可执行文件**: 运行打包好的CLI和GUI
2. **测试分发包**: 解压并测试分发包
3. **跨平台打包**: 在Linux和Windows上重复打包流程
4. **分发**: 将分发包上传到发布平台

## 更新日期

2026-01-13

