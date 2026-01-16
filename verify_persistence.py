# -*- coding: utf-8 -*-
"""
验证数据持久化到磁盘文件
"""
import sys
from pathlib import Path
import shutil

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.amdb import Database

def verify_persistence():
    """验证数据是否写入磁盘文件"""
    test_dir = './data/persistence_test'
    
    # 清理测试数据
    if Path(test_dir).exists():
        shutil.rmtree(test_dir)
    
    print("=" * 80)
    print("数据持久化验证测试")
    print("=" * 80)
    print()
    
    # 1. 创建数据库并写入数据
    print("1. 创建数据库并写入数据...")
    db = Database(data_dir=test_dir)
    
    # 写入100条数据
    items = []
    for i in range(100):
        key = f"key{i:08d}".encode()
        value = f"value{i:08d}".encode()
        items.append((key, value))
    
    db.batch_put(items)
    print(f"   ✓ 写入 {len(items)} 条数据")
    
    # 2. 同步刷新到磁盘
    print("2. 同步刷新到磁盘...")
    db.flush(async_mode=False, force_sync=True)
    print("   ✓ 刷新完成")
    
    # 3. 检查磁盘文件
    print("3. 检查磁盘文件...")
    data_path = Path(test_dir)
    
    # 检查.sst文件（SSTable）
    sst_files = list(data_path.glob("**/*.sst"))
    print(f"   SSTable文件 (.sst): {len(sst_files)} 个")
    for sst in sst_files[:5]:  # 只显示前5个
        size = sst.stat().st_size
        print(f"     - {sst.name}: {size:,} 字节")
    
    # 检查.ver文件（版本管理）
    ver_files = list(data_path.glob("**/*.ver"))
    print(f"   版本文件 (.ver): {len(ver_files)} 个")
    for ver in ver_files:
        size = ver.stat().st_size
        print(f"     - {ver.name}: {size:,} 字节")
    
    # 检查.wal文件（WAL日志）
    wal_files = list(data_path.glob("**/*.wal"))
    print(f"   WAL文件 (.wal): {len(wal_files)} 个")
    for wal in wal_files:
        size = wal.stat().st_size
        print(f"     - {wal.name}: {size:,} 字节")
    
    # 检查.mpt文件（Merkle树）
    mpt_files = list(data_path.glob("**/*.mpt"))
    print(f"   Merkle树文件 (.mpt): {len(mpt_files)} 个")
    
    # 检查.amdb文件（元数据）
    amdb_files = list(data_path.glob("**/*.amdb"))
    print(f"   元数据文件 (.amdb): {len(amdb_files)} 个")
    
    # 4. 重新打开数据库，验证数据是否可读
    print("4. 重新打开数据库，验证数据...")
    db2 = Database(data_dir=test_dir)
    
    success_count = 0
    for i in range(100):
        key = f"key{i:08d}".encode()
        value = db2.get(key)
        if value and value.decode() == f"value{i:08d}":
            success_count += 1
    
    print(f"   ✓ 成功读取 {success_count}/100 条数据")
    
    if success_count == 100:
        print()
        print("=" * 80)
        print("✓ 数据持久化验证通过！所有数据已写入磁盘文件。")
        print("=" * 80)
    else:
        print()
        print("=" * 80)
        print(f"✗ 数据持久化验证失败！只有 {success_count}/100 条数据可读。")
        print("=" * 80)

if __name__ == "__main__":
    verify_persistence()
