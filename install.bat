@echo off
REM AmDb 安装脚本 (Windows)

setlocal enabledelayedexpansion

echo ==================================================================================
echo AmDb 数据库系统安装脚本 (Windows)
echo ==================================================================================
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python
    echo 请先安装Python 3.7或更高版本
    exit /b 1
)

for /f "tokens=2" %%I in ('python --version 2^>^&1') do set PYTHON_VERSION=%%I
echo ✓ 检测到Python版本: %PYTHON_VERSION%

REM 获取安装目录
set "INSTALL_DIR=%ProgramFiles%\AmDb"
set "BIN_DIR=%ProgramFiles%\AmDb\bin"

echo.
echo 安装配置:
echo   安装目录: %INSTALL_DIR%
echo   二进制目录: %BIN_DIR%
echo.

REM 确认安装
set /p CONFIRM="是否继续安装? (y/N): "
if /i not "%CONFIRM%"=="y" (
    echo 安装已取消
    exit /b 0
)

REM 创建安装目录
echo 创建安装目录...
mkdir "%INSTALL_DIR%" 2>nul
mkdir "%INSTALL_DIR%\bin" 2>nul
mkdir "%INSTALL_DIR%\lib" 2>nul
mkdir "%INSTALL_DIR%\data" 2>nul
mkdir "%INSTALL_DIR%\config" 2>nul
mkdir "%INSTALL_DIR%\logs" 2>nul

REM 复制文件
echo 复制文件...
xcopy /E /I /Y src "%INSTALL_DIR%\src\"
xcopy /E /I /Y bindings "%INSTALL_DIR%\bindings\" 2>nul
copy /Y amdb.ini "%INSTALL_DIR%\config\" 2>nul
copy /Y README.md "%INSTALL_DIR%\" 2>nul

REM 安装Python依赖
echo 安装Python依赖...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

REM 编译原生扩展
echo 编译原生扩展...
if exist setup_cython.py (
    python setup_cython.py build_ext --inplace
    xcopy /Y src\amdb\storage\*.pyd "%INSTALL_DIR%\lib\" 2>nul
    xcopy /Y src\amdb\*.pyd "%INSTALL_DIR%\lib\" 2>nul
)

REM 创建启动脚本
echo 创建启动脚本...

REM 服务器启动脚本
(
echo @echo off
echo REM AmDb 数据库服务器启动脚本
echo.
echo set INSTALL_DIR=%INSTALL_DIR%
echo set PYTHONPATH=%%INSTALL_DIR%%\src;%%PYTHONPATH%%
echo.
echo cd /d "%%INSTALL_DIR%%"
echo python -m src.amdb.server %%*
) > "%INSTALL_DIR%\bin\amdb-server.bat"

REM CLI启动脚本
(
echo @echo off
echo REM AmDb 命令行工具启动脚本
echo.
echo set INSTALL_DIR=%INSTALL_DIR%
echo set PYTHONPATH=%%INSTALL_DIR%%\src;%%PYTHONPATH%%
echo.
echo cd /d "%%INSTALL_DIR%%"
echo python -m src.amdb.cli %%*
) > "%INSTALL_DIR%\bin\amdb-cli.bat"

REM GUI启动脚本
(
echo @echo off
echo REM AmDb GUI管理器启动脚本
echo.
echo set INSTALL_DIR=%INSTALL_DIR%
echo set PYTHONPATH=%%INSTALL_DIR%%\src;%%PYTHONPATH%%
echo.
echo cd /d "%%INSTALL_DIR%%"
echo python amdb_manager.py %%*
) > "%INSTALL_DIR%\bin\amdb-manager.bat"

REM 添加到PATH（需要管理员权限）
echo.
echo 注意: 需要手动将 %BIN_DIR% 添加到系统PATH环境变量
echo 或者使用以下命令（需要管理员权限）:
echo   setx PATH "%%PATH%%;%BIN_DIR%" /M

REM 创建启动配置文件
(
echo # AmDb 启动配置
echo INSTALL_DIR=%INSTALL_DIR%
echo DATA_DIR=%INSTALL_DIR%\data
echo LOG_DIR=%INSTALL_DIR%\logs
echo CONFIG_FILE=%INSTALL_DIR%\config\amdb.ini
) > "%INSTALL_DIR%\config\startup.conf"

echo.
echo ==================================================================================
echo 安装完成！
echo ==================================================================================
echo.
echo 安装位置: %INSTALL_DIR%
echo.
echo 使用方法:
echo   启动服务器: %INSTALL_DIR%\bin\amdb-server.bat
echo   命令行工具: %INSTALL_DIR%\bin\amdb-cli.bat
echo   GUI管理器: %INSTALL_DIR%\bin\amdb-manager.bat
echo.
echo 配置文件: %INSTALL_DIR%\config\amdb.ini
echo 数据目录: %INSTALL_DIR%\data
echo 日志目录: %INSTALL_DIR%\logs
echo.

pause

