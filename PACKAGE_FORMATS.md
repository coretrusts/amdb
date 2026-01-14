# AmDb 安装包格式说明

## 支持的安装包格式

### macOS

#### 1. DMG安装包（推荐）
- **文件**: `AmDb-1.0.0-macOS.dmg`
- **大小**: ~21MB
- **创建方式**: `./build_dmg.sh`
- **使用方法**: 双击挂载，拖拽到Applications文件夹

#### 2. 可执行文件
- **文件**: `dist/darwin_x86_64/amdb-cli`, `amdb-manager`
- **大小**: CLI ~8.6MB, GUI ~11MB
- **创建方式**: `./build_all_platforms.sh`
- **使用方法**: 直接运行

#### 3. 分发包（类似比特币）
- **文件**: `amdb-1.0.0-darwin-x86_64.tar.gz`
- **大小**: ~776KB（压缩）
- **创建方式**: `./build_distribution.sh`
- **使用方法**: 解压后运行启动脚本

### Windows

#### 1. EXE可执行文件
- **文件**: `amdb-cli.exe`, `amdb-manager.exe`
- **创建方式**: `build_windows.bat`
- **使用方法**: 双击运行

#### 2. ZIP安装包
- **文件**: `AmDb-1.0.0-Windows.zip`
- **创建方式**: `build_windows.bat`
- **使用方法**: 解压后运行install.bat或直接使用exe文件

#### 3. MSI安装包（可选）
- **文件**: `AmDb-1.0.0-Windows.msi`
- **创建方式**: 使用WiX Toolset
- **使用方法**: 双击安装

### Linux

#### 1. 可执行文件
- **文件**: `dist/linux_x86_64/amdb-cli`, `amdb-manager`
- **创建方式**: `./build_all_platforms.sh`
- **使用方法**: 直接运行

#### 2. 分发包
- **文件**: `amdb-1.0.0-linux-x86_64.tar.gz`
- **创建方式**: `./build_distribution.sh`
- **使用方法**: 解压后运行启动脚本

#### 3. DEB/RPM包（可选）
- **文件**: `amdb_1.0.0_amd64.deb` 或 `amdb-1.0.0-1.x86_64.rpm`
- **创建方式**: 使用dpkg-deb或rpmbuild
- **使用方法**: `sudo dpkg -i` 或 `sudo rpm -i`

## 打包命令总结

### macOS

```bash
# 完整打包（包括DMG）
./build_complete_package.sh
./build_dmg.sh
```

### Windows

```cmd
REM 完整打包
build_windows.bat
```

### Linux

```bash
# 完整打包
./build_complete_package.sh
```

### 跨平台

```bash
# 自动检测平台并打包
./build_all_platforms_complete.sh
```

## 文件大小对比

| 格式 | 平台 | 大小 | 说明 |
|------|------|------|------|
| DMG | macOS | ~21MB | 包含所有文件 |
| EXE | Windows | CLI: ~8.6MB, GUI: ~11MB | 单文件可执行 |
| tar.gz | 所有平台 | ~776KB | 压缩分发包 |
| ZIP | Windows | ~20MB | 完整安装包 |

## 推荐使用

- **macOS用户**: 使用DMG安装包
- **Windows用户**: 使用EXE文件或ZIP安装包
- **Linux用户**: 使用tar.gz分发包或可执行文件
- **开发者**: 使用分发包（类似比特币方式）

## 更新日期

2026-01-13

