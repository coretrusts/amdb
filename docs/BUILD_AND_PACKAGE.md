# AmDb 跨平台打包和编译指南

## 概述

本文档说明如何将AmDb打包为不同平台的可执行文件，以及如何编译原生扩展。

## 支持平台

- **Windows**: x86_64, ARM64
- **macOS**: x86_64, ARM64 (Apple Silicon)
- **Linux**: x86_64, ARM64

## 打包工具

### 1. CLI命令行工具打包

#### Linux/macOS
```bash
./build_all_platforms.sh
```

#### Windows
```cmd
build_all_platforms.bat
```

#### Python脚本
```bash
python3 build_package.py
```

### 2. GUI管理器打包

GUI管理器使用相同的打包脚本，会自动检测并打包GUI版本。

### 3. 原生扩展编译

```bash
./build_native.sh
```

## 详细步骤

### 前置要求

1. **Python 3.7+**
   ```bash
   python3 --version
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   pip install pyinstaller
   ```

3. **安装Cython（用于编译原生扩展）**
   ```bash
   pip install Cython
   ```

### 打包CLI

#### 方法1: 使用打包脚本（推荐）

**Linux/macOS:**
```bash
chmod +x build_all_platforms.sh
./build_all_platforms.sh
```

**Windows:**
```cmd
build_all_platforms.bat
```

#### 方法2: 使用PyInstaller直接打包

```bash
pyinstaller --name amdb-cli \
    --onefile \
    --console \
    --add-data "src:src" \
    --hidden-import src.amdb \
    --hidden-import src.amdb.cli \
    --hidden-import src.amdb.database \
    --clean \
    --noconfirm \
    amdb-cli
```

### 打包GUI

```bash
pyinstaller --name amdb-manager \
    --onefile \
    --windowed \
    --add-data "src:src" \
    --hidden-import src.amdb \
    --hidden-import src.amdb.gui_manager \
    --hidden-import tkinter \
    --clean \
    --noconfirm \
    amdb_manager.py
```

### 编译原生扩展

```bash
# 编译Cython扩展
python3 setup_cython.py build_ext --inplace

# 或使用脚本
./build_native.sh
```

## 输出目录

打包完成后，可执行文件位于：

- **Linux/macOS**: `dist/linux_<arch>/` 或 `dist/macos_<arch>/`
- **Windows**: `dist/windows_<arch>/`

文件列表：
- `amdb-cli` / `amdb-cli.exe` - 命令行工具
- `amdb-manager` / `amdb-manager.exe` / `amdb-manager.app` - GUI管理器

## 性能测试

### 运行性能基准测试

```bash
python3 tests/performance_benchmark.py
```

### 测试项目

1. **顺序写入** - 对标LevelDB: 550,000 ops/s
2. **随机写入** - 对标LevelDB: 52,000 ops/s
3. **随机读取** - 对标LevelDB: 156,000 ops/s
4. **并发写入** - 多线程性能测试
5. **TPC-C类似** - 对标PolarDB: 2.055亿 tpmC

### 性能优化建议

1. **启用多线程**
   ```ini
   [threading]
   enable = true
   max_workers = 8
   ```

2. **优化批量大小**
   ```ini
   [batch]
   max_size = 10000
   ```

3. **启用分片**
   ```ini
   [sharding]
   enable = true
   shard_count = 256
   ```

## 跨平台编译

### Windows

```cmd
REM 使用Visual Studio或MinGW
python setup_cython.py build_ext --inplace
```

### macOS

```bash
# 使用Xcode Command Line Tools
xcode-select --install
python3 setup_cython.py build_ext --inplace
```

### Linux

```bash
# 安装编译工具
sudo apt-get install build-essential python3-dev
python3 setup_cython.py build_ext --inplace
```

## 打包选项

### PyInstaller选项说明

- `--onefile`: 打包为单个可执行文件
- `--console`: CLI模式（显示控制台）
- `--windowed`: GUI模式（不显示控制台）
- `--add-data`: 添加数据文件
- `--hidden-import`: 添加隐藏导入
- `--clean`: 清理临时文件
- `--noconfirm`: 不确认覆盖

### 自定义图标

```bash
pyinstaller --icon=icon.ico amdb-cli
```

## 验证打包结果

### 测试CLI

```bash
# Linux/macOS
./dist/linux_x86_64/amdb-cli --help

# Windows
dist\windows_x86_64\amdb-cli.exe --help
```

### 测试GUI

```bash
# Linux/macOS
./dist/linux_x86_64/amdb-manager

# Windows
dist\windows_x86_64\amdb-manager.exe

# macOS
open dist/macos_arm64/amdb-manager.app
```

## 性能测试报告

运行性能测试后，会生成详细的性能报告，包括：

- 各项测试的性能指标
- 与目标性能的对比
- 达成率百分比
- 优化建议

## 常见问题

### 1. PyInstaller打包失败

**问题**: 缺少隐藏导入

**解决**: 在spec文件中添加所有需要的模块

### 2. GUI打包后无法运行

**问题**: 缺少tkinter依赖

**解决**: 确保系统安装了tkinter，或使用`--hidden-import tkinter`

### 3. 原生扩展编译失败

**问题**: 缺少C编译器

**解决**: 安装对应平台的编译工具（gcc, clang, Visual Studio）

### 4. 打包文件过大

**问题**: 包含不必要的依赖

**解决**: 使用`--exclude-module`排除不需要的模块

## 更新日期

2026-01-13

