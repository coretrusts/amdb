# 跨平台编译打包指南

## 概述

AmDb支持跨平台编译打包，为不同平台生成对应的安装包格式。

## 支持的平台和格式

| 平台 | 可执行文件 | 安装包格式 | 脚本 |
|------|-----------|-----------|------|
| **macOS** | `.app`, 可执行文件 | `.dmg` | `build_dmg.sh` |
| **Linux** | 可执行文件 | `.tar.gz` | `build_all_platforms.sh` |
| **Windows** | `.exe` | `.zip`, `.msi` | `build_windows.bat` |

## macOS打包

### 生成DMG安装包

```bash
# 1. 先打包CLI/GUI
./build_all_platforms.sh

# 2. 创建DMG安装包
./build_dmg.sh
```

### DMG安装包特点

- ✅ 双击挂载，拖拽安装
- ✅ 包含所有必要文件
- ✅ 自动创建Applications链接
- ✅ 符合macOS安装规范

### 输出文件

- `dist/AmDb-1.0.0-macOS.dmg` - DMG安装包

## Windows打包

### 生成EXE和安装包

```cmd
REM 在Windows系统上运行
build_windows.bat
```

### Windows安装包特点

- ✅ 独立的`.exe`可执行文件
- ✅ ZIP压缩包格式
- ✅ 包含安装脚本
- ✅ 支持直接运行

### 输出文件

- `dist/windows_x86_64/amdb-cli.exe` - CLI可执行文件
- `dist/windows_x86_64/amdb-manager.exe` - GUI可执行文件
- `dist/AmDb-1.0.0-Windows.zip` - Windows安装包

## Linux打包

### 生成可执行文件和分发包

```bash
# 打包CLI/GUI
./build_all_platforms.sh

# 创建分发包
./build_distribution.sh
```

### 输出文件

- `dist/linux_x86_64/amdb-cli` - CLI可执行文件
- `dist/linux_x86_64/amdb-manager` - GUI可执行文件
- `dist/amdb-1.0.0-linux-x86_64.tar.gz` - Linux分发包

## 跨平台编译方案

### 方案1: 使用Docker（推荐）

```bash
# 为不同平台构建Docker镜像
docker build -f Dockerfile.linux -t amdb-builder:linux .
docker build -f Dockerfile.windows -t amdb-builder:windows .

# 在容器中编译
docker run --rm -v $(pwd):/workspace amdb-builder:linux ./build_all_platforms.sh
```

### 方案2: 使用GitHub Actions

创建`.github/workflows/build.yml`，自动为所有平台构建。

### 方案3: 使用WSL（Windows上编译Linux版本）

```bash
# 在WSL中
wsl
./build_all_platforms.sh
```

### 方案4: 使用虚拟机

在不同平台的虚拟机中分别编译。

## 完整打包流程

### macOS

```bash
# 完整流程
./build_complete_package.sh  # 编译+打包
./build_dmg.sh              # 创建DMG
```

### Windows

```cmd
REM 完整流程
build_windows.bat
```

### Linux

```bash
# 完整流程
./build_complete_package.sh
```

## 安装包内容

### macOS DMG

```
AmDb-1.0.0-macOS.dmg
└── AmDb/
    ├── Applications -> /Applications (链接)
    ├── amdb-cli
    ├── amdb-manager
    ├── amdb-server
    ├── src/
    ├── lib/
    ├── config/
    └── README.txt
```

### Windows ZIP

```
AmDb-1.0.0-Windows.zip
└── AmDb-1.0.0-Windows/
    ├── amdb-cli.exe
    ├── amdb-manager.exe
    ├── amdb-server.bat
    ├── src/
    ├── lib/
    ├── config/
    ├── install.bat
    └── README.txt
```

## 测试安装包

### macOS DMG测试

```bash
# 挂载DMG
hdiutil attach dist/AmDb-1.0.0-macOS.dmg

# 测试安装
cp -R /Volumes/AmDb/AmDb /Applications/

# 卸载DMG
hdiutil detach /Volumes/AmDb
```

### Windows ZIP测试

```cmd
REM 解压测试
powershell Expand-Archive -Path dist\AmDb-1.0.0-Windows.zip -DestinationPath test_install

REM 运行测试
cd test_install\AmDb-1.0.0-Windows
amdb-cli.exe --help
amdb-manager.exe
```

## 签名和公证（可选）

### macOS代码签名

```bash
# 签名DMG
codesign --sign "Developer ID Application: Your Name" dist/AmDb-1.0.0-macOS.dmg

# 公证（需要Apple Developer账号）
xcrun notarytool submit dist/AmDb-1.0.0-macOS.dmg --keychain-profile "notarytool-profile"
```

### Windows代码签名

```cmd
REM 使用signtool签名
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com dist\windows_x86_64\amdb-cli.exe
```

## 分发建议

1. **macOS**: 提供DMG文件，用户双击安装
2. **Windows**: 提供ZIP文件或MSI安装包
3. **Linux**: 提供tar.gz分发包或.deb/.rpm包

## 更新日期

2026-01-13

