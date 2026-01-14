# AmDb 打包和编译指南

## 快速开始

### 1. 安装依赖

```bash
# 安装Python依赖
pip install -r requirements.txt

# 安装打包工具
pip install pyinstaller cython
```

### 2. 打包CLI和GUI

#### Linux/macOS
```bash
chmod +x build_all_platforms.sh
./build_all_platforms.sh
```

#### Windows
```cmd
build_all_platforms.bat
```

#### 使用Makefile
```bash
make all
```

### 3. 编译原生扩展

```bash
./build_native.sh
# 或
python3 setup_cython.py build_ext --inplace
```

### 4. 运行性能测试

```bash
# 快速测试
python3 quick_performance_test.py

# 完整测试
python3 tests/performance_benchmark.py
```

## 打包输出

打包完成后，可执行文件位于 `dist/<platform>_<arch>/` 目录：

- **CLI**: `amdb-cli` (Linux/macOS) 或 `amdb-cli.exe` (Windows)
- **GUI**: `amdb-manager` (Linux/macOS) 或 `amdb-manager.exe` (Windows) 或 `amdb-manager.app` (macOS)

## 性能目标

- **顺序写入**: 550,000 ops/s (LevelDB)
- **随机写入**: 52,000 ops/s (LevelDB)
- **随机读取**: 156,000 ops/s (LevelDB)
- **TPC-C**: 2.055亿 tpmC (PolarDB)

## 更多信息

详细说明请参考 `docs/BUILD_AND_PACKAGE.md`

