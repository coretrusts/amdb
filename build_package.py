# -*- coding: utf-8 -*-
"""
跨平台打包脚本
支持Windows、macOS、Linux平台的CLI和GUI打包
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path

def get_platform_info():
    """获取平台信息"""
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    if system == 'windows':
        return 'win', 'exe'
    elif system == 'darwin':
        return 'macos', 'app' if machine == 'arm64' else 'app'
    elif system == 'linux':
        return 'linux', 'bin'
    else:
        return 'unknown', 'bin'

def check_pyinstaller():
    """检查PyInstaller是否安装"""
    try:
        import PyInstaller
        return True
    except ImportError:
        return False

def install_pyinstaller():
    """安装PyInstaller"""
    print("正在安装PyInstaller...")
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
    print("✓ PyInstaller安装完成")

def build_cli(platform_name, ext):
    """打包CLI"""
    print(f"\n{'='*80}")
    print(f"打包CLI ({platform_name})")
    print(f"{'='*80}\n")
    
    spec_file = f"amdb_cli_{platform_name}.spec"
    
    # 创建spec文件
    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['amdb-cli'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'src.amdb',
        'src.amdb.cli',
        'src.amdb.database',
        'src.amdb.config',
        'src.amdb.storage',
        'src.amdb.storage.lsm_tree',
        'src.amdb.storage.bplus_tree',
        'src.amdb.storage.merkle_tree',
        'src.amdb.storage.skip_list',
        'src.amdb.storage.file_format',
        'src.amdb.storage.storage_engine',
        'src.amdb.storage.sharded_lsm_tree',
        'src.amdb.version',
        'src.amdb.index',
        'src.amdb.value_formatter',
        'src.amdb.db_scanner',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='amdb-cli',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
"""
    
    with open(spec_file, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    # 执行打包
    try:
        subprocess.check_call([
            'pyinstaller',
            '--clean',
            '--noconfirm',
            spec_file
        ])
        print(f"✓ CLI打包完成: dist/amdb-cli.{ext}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ CLI打包失败: {e}")
        return False

def build_gui(platform_name, ext):
    """打包GUI"""
    print(f"\n{'='*80}")
    print(f"打包GUI ({platform_name})")
    print(f"{'='*80}\n")
    
    spec_file = f"amdb_gui_{platform_name}.spec"
    
    # 创建spec文件
    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['amdb_manager.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'src.amdb',
        'src.amdb.gui_manager',
        'src.amdb.database',
        'src.amdb.config',
        'src.amdb.storage',
        'src.amdb.storage.lsm_tree',
        'src.amdb.storage.bplus_tree',
        'src.amdb.storage.merkle_tree',
        'src.amdb.storage.skip_list',
        'src.amdb.storage.file_format',
        'src.amdb.storage.storage_engine',
        'src.amdb.storage.sharded_lsm_tree',
        'src.amdb.version',
        'src.amdb.index',
        'src.amdb.value_formatter',
        'src.amdb.db_scanner',
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'tkinter.filedialog',
        'tkinter.scrolledtext',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='amdb-manager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
"""
    
    with open(spec_file, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    # 执行打包
    try:
        subprocess.check_call([
            'pyinstaller',
            '--clean',
            '--noconfirm',
            spec_file
        ])
        print(f"✓ GUI打包完成: dist/amdb-manager.{ext}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ GUI打包失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 80)
    print("AmDb 跨平台打包工具")
    print("=" * 80)
    print()
    
    # 检查PyInstaller
    if not check_pyinstaller():
        print("PyInstaller未安装，正在安装...")
        install_pyinstaller()
    
    # 获取平台信息
    platform_name, ext = get_platform_info()
    print(f"当前平台: {platform_name} ({ext})")
    print()
    
    # 选择打包目标
    print("请选择打包目标:")
    print("1. CLI (命令行工具)")
    print("2. GUI (图形界面管理器)")
    print("3. 全部")
    print()
    
    choice = input("请输入选择 (1/2/3): ").strip()
    
    success = True
    
    if choice == '1' or choice == '3':
        success = build_cli(platform_name, ext) and success
    
    if choice == '2' or choice == '3':
        success = build_gui(platform_name, ext) and success
    
    if success:
        print("\n" + "=" * 80)
        print("打包完成！")
        print("=" * 80)
        print(f"\n输出目录: dist/")
        print(f"平台: {platform_name}")
    else:
        print("\n" + "=" * 80)
        print("打包过程中出现错误，请检查输出")
        print("=" * 80)
        sys.exit(1)

if __name__ == "__main__":
    main()

