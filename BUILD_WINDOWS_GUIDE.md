# Windows打包编译指南

## 概述

在Windows系统上打包AmDb，生成`.exe`可执行文件和安装包。

## 前置要求

1. **Python 3.7+**
   ```cmd
   python --version
   ```

2. **安装依赖**
   ```cmd
   pip install pyinstaller
   pip install -r requirements.txt
   ```

## 打包步骤

### 方式1: 使用批处理脚本（推荐）

```cmd
build_windows.bat
```

这将自动：
1. 打包CLI为 `amdb-cli.exe`
2. 打包GUI为 `amdb-manager.exe`
3. 创建Windows安装包目录
4. 生成ZIP压缩包

### 方式2: 手动打包

#### 打包CLI

```cmd
pyinstaller --name amdb-cli ^
    --onefile ^
    --console ^
    --add-data "src;src" ^
    --hidden-import src.amdb ^
    --hidden-import src.amdb.cli ^
    --clean ^
    --noconfirm ^
    amdb-cli
```

#### 打包GUI

```cmd
pyinstaller --name amdb-manager ^
    --onefile ^
    --windowed ^
    --add-data "src;src" ^
    --hidden-import src.amdb ^
    --hidden-import src.amdb.gui_manager ^
    --hidden-import tkinter ^
    --clean ^
    --noconfirm ^
    amdb_manager.py
```

## 输出文件

打包完成后，生成以下文件：

### 可执行文件

- `dist/windows_x86_64/amdb-cli.exe` - CLI命令行工具
- `dist/windows_x86_64/amdb-manager.exe` - GUI管理器

### 安装包

- `dist/AmDb-1.0.0-Windows/` - Windows安装包目录
- `dist/AmDb-1.0.0-Windows.zip` - ZIP压缩包

## 安装包内容

```
AmDb-1.0.0-Windows/
├── amdb-cli.exe          # CLI可执行文件
├── amdb-manager.exe      # GUI可执行文件
├── amdb-server.bat       # 服务器启动脚本
├── src/                  # Python源代码
├── lib/                  # 原生扩展（.pyd文件）
├── config/               # 配置文件
├── bindings/             # 多语言绑定
├── docs/                 # 文档
├── examples/             # 示例代码
├── install.bat           # 安装脚本
└── README.txt            # 说明文件
```

## 使用方法

### 方式1: 直接运行EXE

```cmd
REM 双击运行
amdb-cli.exe
amdb-manager.exe
```

### 方式2: 使用安装包

```cmd
REM 解压ZIP文件
powershell Expand-Archive -Path AmDb-1.0.0-Windows.zip -DestinationPath .

REM 运行安装脚本
cd AmDb-1.0.0-Windows
install.bat
```

### 方式3: 命令行使用

```cmd
REM 启动服务器
amdb-server.bat

REM 使用CLI
amdb-cli.exe --help

REM 启动GUI
amdb-manager.exe
```

## 创建MSI安装包（可选）

如果需要创建MSI安装包，可以使用WiX Toolset：

```cmd
REM 安装WiX Toolset
choco install wix

REM 使用wix创建MSI
candle amdb.wxs
light amdb.wixobj -out amdb.msi
```

## 代码签名（可选）

```cmd
REM 使用signtool签名
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com amdb-cli.exe
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com amdb-manager.exe
```

## 常见问题

### 1. PyInstaller打包失败

**问题**: 缺少隐藏导入

**解决**: 在spec文件中添加所有需要的模块

### 2. GUI无法启动

**问题**: 缺少tkinter

**解决**: 确保系统安装了tkinter，或使用`--hidden-import tkinter`

### 3. 文件过大

**问题**: 包含不必要的依赖

**解决**: 使用`--exclude-module`排除不需要的模块

## 更新日期

2026-01-13

