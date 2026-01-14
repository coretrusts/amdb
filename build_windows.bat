@echo off
REM AmDb Windows打包脚本
REM 创建Windows安装包和EXE文件

setlocal enabledelayedexpansion

echo ==================================================================================
echo AmDb Windows打包脚本
echo ==================================================================================
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python
    exit /b 1
)

REM 获取版本号
for /f "tokens=*" %%I in ('python -c "import sys; sys.path.insert(0, 'src'); from amdb import __version__; print(__version__)" 2^>nul') do set VERSION=%%I
if "!VERSION!"=="" set VERSION=1.0.0

echo 版本: !VERSION!
echo.

REM 检查PyInstaller
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo 正在安装PyInstaller...
    python -m pip install pyinstaller
)

REM 创建输出目录
set OUTPUT_DIR=dist\windows_x86_64
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

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
    --icon=NONE ^
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

echo.
echo ==================================================================================
echo 打包服务器...
echo ==================================================================================
echo.

python -m PyInstaller ^
    --name amdb-server ^
    --onefile ^
    --console ^
    --add-data "src;src" ^
    --hidden-import src.amdb ^
    --hidden-import src.amdb.server ^
    --hidden-import src.amdb.database ^
    --hidden-import src.amdb.config ^
    --hidden-import src.amdb.network ^
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
    --hidden-import src.amdb.db_registry ^
    --icon=NONE ^
    --clean ^
    --noconfirm ^
    amdb-server

if exist "dist\amdb-server.exe" (
    echo ✓ 服务器打包成功
    copy dist\amdb-server.exe "%OUTPUT_DIR%\"
) else (
    echo ✗ 服务器打包失败
    exit /b 1
)

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
    --icon=NONE ^
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
echo 创建Windows安装包...
echo ==================================================================================
echo.

REM 创建安装包目录
set INSTALLER_DIR=dist\AmDb-!VERSION!-Windows
if exist "%INSTALLER_DIR%" rmdir /s /q "%INSTALLER_DIR%"
mkdir "%INSTALLER_DIR%"

REM 复制文件
xcopy /E /I /Y src "%INSTALLER_DIR%\src\"
xcopy /E /I /Y bindings "%INSTALLER_DIR%\bindings\" 2>nul
copy /Y amdb.ini "%INSTALLER_DIR%\config\" 2>nul
copy /Y README.md "%INSTALLER_DIR%\" 2>nul
xcopy /E /I /Y docs "%INSTALLER_DIR%\docs\" 2>nul
xcopy /E /I /Y examples "%INSTALLER_DIR%\examples\" 2>nul

REM 复制可执行文件
copy /Y "%OUTPUT_DIR%\amdb-cli.exe" "%INSTALLER_DIR%\"
copy /Y "%OUTPUT_DIR%\amdb-server.exe" "%INSTALLER_DIR%\"
copy /Y "%OUTPUT_DIR%\amdb-manager.exe" "%INSTALLER_DIR%\"

REM 创建安装脚本
copy /Y install.bat "%INSTALLER_DIR%\"

REM 创建README
(
echo AmDb 数据库系统 - Windows安装包
echo 版本: !VERSION!
echo.
echo 安装说明:
echo ==========
echo.
echo 方式1: 使用安装脚本
echo   1. 运行 install.bat
echo   2. 按照提示完成安装
echo.
echo 方式2: 直接使用
echo   1. 双击 amdb-server.exe 启动数据库服务器（常驻内存）
echo   2. 双击 amdb-cli.exe 启动命令行客户端
echo   3. 双击 amdb-manager.exe 启动GUI管理器
echo.
echo 快速开始:
echo ==========
echo 1. 启动服务器: amdb-server.exe（或命令行运行）
echo 2. 使用CLI: amdb-cli.exe（可连接本地或远程服务器）
echo 3. 使用GUI: amdb-manager.exe（可连接本地或远程服务器）
echo.
echo 更多信息请参考 README.md
) > "%INSTALLER_DIR%\README.txt"

echo ✓ Windows安装包创建完成
echo.

REM 创建ZIP压缩包
echo 创建ZIP压缩包...
cd dist
if exist "AmDb-!VERSION!-Windows.zip" del "AmDb-!VERSION!-Windows.zip"
powershell -Command "Compress-Archive -Path 'AmDb-!VERSION!-Windows' -DestinationPath 'AmDb-!VERSION!-Windows.zip' -Force"
cd ..

echo.
echo ==================================================================================
echo Windows打包完成！
echo ==================================================================================
echo.
echo 输出文件:
echo   - CLI: %OUTPUT_DIR%\amdb-cli.exe
echo   - GUI: %OUTPUT_DIR%\amdb-manager.exe
echo   - 安装包: %INSTALLER_DIR%
echo   - ZIP压缩包: dist\AmDb-!VERSION!-Windows.zip
echo.

pause

