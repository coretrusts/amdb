@echo off
REM AmDb 跨平台打包脚本 (Windows)
REM 支持打包CLI和GUI

setlocal enabledelayedexpansion

echo ==================================================================================
echo AmDb 跨平台打包脚本 (Windows)
echo ==================================================================================
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python
    exit /b 1
)

REM 检查PyInstaller
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller未安装，正在安装...
    python -m pip install pyinstaller
)

REM 获取平台信息
set PLATFORM=windows
for /f "tokens=2 delims==" %%I in ('wmic os get osarchitecture /value') do set ARCH=%%I
set ARCH=%ARCH:~0,-1%

echo 平台: %PLATFORM%
echo 架构: %ARCH%
echo.

REM 创建输出目录
set OUTPUT_DIR=dist\%PLATFORM%_%ARCH%
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

REM 打包CLI
echo ==================================================================================
echo 打包CLI...
echo ==================================================================================
echo.

python -m PyInstaller ^
    --name amdb-cli ^
    --onefile ^
    --console ^
    --add-data "src;src" ^
    --hidden-import src.amdb ^
    --hidden-import src.amdb.cli ^
    --hidden-import src.amdb.database ^
    --hidden-import src.amdb.config ^
    --hidden-import src.amdb.storage ^
    --hidden-import src.amdb.storage.lsm_tree ^
    --hidden-import src.amdb.storage.bplus_tree ^
    --hidden-import src.amdb.storage.merkle_tree ^
    --hidden-import src.amdb.storage.skip_list ^
    --hidden-import src.amdb.storage.file_format ^
    --hidden-import src.amdb.storage.storage_engine ^
    --hidden-import src.amdb.storage.sharded_lsm_tree ^
    --hidden-import src.amdb.version ^
    --hidden-import src.amdb.index ^
    --hidden-import src.amdb.value_formatter ^
    --hidden-import src.amdb.db_scanner ^
    --clean ^
    --noconfirm ^
    amdb-cli

if exist "dist\amdb-cli.exe" (
    echo ✓ CLI打包成功
    copy dist\amdb-cli.exe "%OUTPUT_DIR%\"
) else (
    echo ✗ CLI打包失败
    exit /b 1
)

REM 打包GUI
echo.
echo ==================================================================================
echo 打包GUI...
echo ==================================================================================
echo.

python -m PyInstaller ^
    --name amdb-manager ^
    --onefile ^
    --windowed ^
    --add-data "src;src" ^
    --hidden-import src.amdb ^
    --hidden-import src.amdb.gui_manager ^
    --hidden-import src.amdb.database ^
    --hidden-import src.amdb.config ^
    --hidden-import src.amdb.storage ^
    --hidden-import src.amdb.storage.lsm_tree ^
    --hidden-import src.amdb.storage.bplus_tree ^
    --hidden-import src.amdb.storage.merkle_tree ^
    --hidden-import src.amdb.storage.skip_list ^
    --hidden-import src.amdb.storage.file_format ^
    --hidden-import src.amdb.storage.storage_engine ^
    --hidden-import src.amdb.storage.sharded_lsm_tree ^
    --hidden-import src.amdb.version ^
    --hidden-import src.amdb.index ^
    --hidden-import src.amdb.value_formatter ^
    --hidden-import src.amdb.db_scanner ^
    --hidden-import tkinter ^
    --hidden-import tkinter.ttk ^
    --hidden-import tkinter.messagebox ^
    --hidden-import tkinter.filedialog ^
    --hidden-import tkinter.scrolledtext ^
    --clean ^
    --noconfirm ^
    amdb_manager.py

if exist "dist\amdb-manager.exe" (
    echo ✓ GUI打包成功
    copy dist\amdb-manager.exe "%OUTPUT_DIR%\"
) else (
    echo ✗ GUI打包失败
    exit /b 1
)

echo.
echo ==================================================================================
echo 打包完成！
echo ==================================================================================
echo.
echo 输出目录: %OUTPUT_DIR%
echo.
dir "%OUTPUT_DIR%"

