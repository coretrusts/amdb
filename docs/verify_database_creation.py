#!/usr/bin/env python3
"""
数据库创建验证脚本
用于诊断数据库创建问题
"""

import sys
from pathlib import Path
import os
import shutil

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.amdb import Database

def verify_database_creation(data_dir: str):
    """验证数据库创建"""
    print(f"\n{'='*60}")
    print(f"验证数据库创建: {data_dir}")
    print(f"{'='*60}\n")
    
    # 清理旧数据
    if os.path.exists(data_dir):
        shutil.rmtree(data_dir)
        print(f"✓ 已清理旧数据: {data_dir}")
    
    # 步骤1: 导入测试
    print("\n步骤1: 测试导入...")
    try:
        from src.amdb import Database
        print("✓ Database 类导入成功")
    except Exception as e:
        print(f"✗ 导入失败: {e}")
        return False
    
    # 步骤2: 初始化测试
    print("\n步骤2: 测试初始化...")
    try:
        db = Database(data_dir=data_dir)
        print("✓ Database 初始化成功")
        print(f"  数据目录: {db.data_dir}")
        print(f"  分片启用: {db.enable_sharding}")
    except Exception as e:
        print(f"✗ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 步骤3: 检查文件结构
    print("\n步骤3: 检查文件结构...")
    data_path = Path(data_dir)
    
    # 检查 database.amdb
    amdb_file = data_path / 'database.amdb'
    if amdb_file.exists():
        size = amdb_file.stat().st_size
        print(f"✓ database.amdb 存在 ({size} 字节)")
    else:
        print("✗ database.amdb 不存在")
        return False
    
    # 检查目录
    required_dirs = ['versions', 'lsm', 'wal', 'bplus', 'merkle', 'indexes']
    all_exist = True
    for d in required_dirs:
        dir_path = data_path / d
        if dir_path.exists():
            print(f"✓ {d}/ 目录存在")
        else:
            print(f"✗ {d}/ 目录不存在")
            all_exist = False
    
    if not all_exist:
        print("\n⚠ 警告: 部分目录未创建")
        return False
    
    # 步骤4: 测试读写
    print("\n步骤4: 测试读写...")
    try:
        # 写入
        db.put(b'test_key', b'test_value')
        print("✓ 写入成功")
        
        # 读取
        value = db.get(b'test_key')
        if value == b'test_value':
            print("✓ 读取成功")
        else:
            print(f"✗ 读取失败: 期望 b'test_value', 得到 {value}")
            return False
        
        # 持久化
        db.flush()
        print("✓ 持久化成功")
        
    except Exception as e:
        print(f"✗ 读写测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 步骤5: 验证数据文件
    print("\n步骤5: 验证数据文件...")
    versions_file = data_path / 'versions' / 'versions.ver'
    indexes_file = data_path / 'indexes' / 'indexes.idx'
    
    if versions_file.exists():
        print(f"✓ versions.ver 存在 ({versions_file.stat().st_size} 字节)")
    else:
        print("⚠ versions.ver 不存在（可能还未写入数据）")
    
    if indexes_file.exists():
        print(f"✓ indexes.idx 存在 ({indexes_file.stat().st_size} 字节)")
    else:
        print("⚠ indexes.idx 不存在（可能还未写入数据）")
    
    print(f"\n{'='*60}")
    print("✓ 数据库创建验证通过！")
    print(f"{'='*60}\n")
    
    return True

if __name__ == '__main__':
    test_dir = './data/verification_test'
    success = verify_database_creation(test_dir)
    
    # 清理
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    
    if not success:
        print("\n✗ 验证失败，请检查上述错误信息")
        exit(1)
    else:
        print("\n✓ 所有验证通过！")

