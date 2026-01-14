#!/usr/bin/env python3
"""
多数据库使用示例
演示如何创建、连接和管理多个独立的数据库实例
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.amdb import Database

def example_1_basic_usage():
    """示例1：基本用法 - 创建多个数据库"""
    print("=" * 80)
    print("示例1：创建多个数据库")
    print("=" * 80)
    
    # 创建用户数据库
    user_db = Database(data_dir="./data/user_db")
    user_db.put(b"user:001", '{"name": "\u5f20\u4e09", "balance": 1000}'.encode())
    print("✓ 用户数据库创建并写入数据")
    
    # 创建交易数据库
    transaction_db = Database(data_dir="./data/transaction_db")
    transaction_db.put(b"tx:001", '{"from": "user:001", "to": "user:002", "amount": 100}'.encode())
    print("✓ 交易数据库创建并写入数据")
    
    # 两个数据库完全独立
    print("✓ 两个数据库完全独立，互不影响")


def example_2_simultaneous_usage():
    """示例2：同时使用多个数据库"""
    print("\n" + "=" * 80)
    print("示例2：同时使用多个数据库")
    print("=" * 80)
    
    # 同时打开多个数据库
    user_db = Database(data_dir="./data/user_db")
    transaction_db = Database(data_dir="./data/transaction_db")
    block_db = Database(data_dir="./data/block_db")
    
    # 同时操作多个数据库
    user_db.put(b"user:002", '{"name": "\u674e\u56db", "balance": 2000}'.encode())
    transaction_db.put(b"tx:002", '{"from": "user:002", "to": "user:001", "amount": 50}'.encode())
    block_db.put(b"block:001", '{"number": 1, "hash": "0x123..."}'.encode())
    
    print("✓ 同时操作3个数据库成功")
    
    # 读取数据
    user_data = user_db.get(b"user:002")
    tx_data = transaction_db.get(b"tx:002")
    block_data = block_db.get(b"block:001")
    
    print(f"✓ 用户数据: {user_data}")
    print(f"✓ 交易数据: {tx_data}")
    print(f"✓ 区块数据: {block_data}")


def example_3_different_configs():
    """示例3：使用不同的配置文件"""
    print("\n" + "=" * 80)
    print("示例3：使用不同的配置文件")
    print("=" * 80)
    
    # 开发环境数据库（使用默认配置）
    dev_db = Database(data_dir="./data/dev_db", config_path="./amdb.ini")
    dev_db.put(b"test:001", b"dev_data")
    print("✓ 开发环境数据库创建成功")
    
    # 生产环境数据库（可以使用不同的配置）
    prod_db = Database(data_dir="./data/prod_db", config_path="./amdb.ini")
    prod_db.put(b"prod:001", b"prod_data")
    print("✓ 生产环境数据库创建成功")
    
    # 注意：这里使用同一个配置文件，实际应用中可以使用不同的配置文件
    print("提示：可以为不同环境创建不同的配置文件")


def example_4_switch_database():
    """示例4：切换数据库连接"""
    print("\n" + "=" * 80)
    print("示例4：切换数据库连接")
    print("=" * 80)
    
    # 连接用户数据库
    db = Database(data_dir="./data/user_db")
    user_count = len(db.version_manager.get_all_keys())
    print(f"✓ 用户数据库: {user_count} 条记录")
    
    # 断开并连接交易数据库
    db = None
    db = Database(data_dir="./data/transaction_db")
    tx_count = len(db.version_manager.get_all_keys())
    print(f"✓ 交易数据库: {tx_count} 条记录")
    
    # 断开并连接区块数据库
    db = None
    db = Database(data_dir="./data/block_db")
    block_count = len(db.version_manager.get_all_keys())
    print(f"✓ 区块数据库: {block_count} 条记录")


def example_5_list_databases():
    """示例5：列出所有数据库"""
    print("\n" + "=" * 80)
    print("示例5：列出所有数据库")
    print("=" * 80)
    
    data_dir = "./data"
    if os.path.exists(data_dir):
        databases = [d for d in os.listdir(data_dir) 
                     if os.path.isdir(os.path.join(data_dir, d)) and d.endswith("_db")]
        
        print(f"✓ 找到 {len(databases)} 个数据库:")
        for db_name in sorted(databases):
            db_path = os.path.join(data_dir, db_name)
            try:
                db = Database(data_dir=db_path)
                stats = db.get_stats()
                key_count = stats.get('total_keys', 0)
                print(f"  - {db_name}: {key_count} 条记录")
            except Exception as e:
                print(f"  - {db_name}: 无法访问 ({e})")
    else:
        print("✗ 数据目录不存在")


def main():
    """运行所有示例"""
    print("\n" + "=" * 80)
    print("AmDb 多数据库使用示例")
    print("=" * 80)
    print()
    print("本示例演示如何创建、连接和管理多个独立的数据库实例")
    print()
    
    try:
        example_1_basic_usage()
        example_2_simultaneous_usage()
        example_3_different_configs()
        example_4_switch_database()
        example_5_list_databases()
        
        print("\n" + "=" * 80)
        print("所有示例运行完成！")
        print("=" * 80)
        print()
        print("在GUI管理器中:")
        print("  1. 启动: python amdb_manager.py")
        print("  2. 点击\"文件\" -> \"连接数据库\"")
        print("  3. 在预设数据库列表中选择要连接的数据库")
        print("  4. 或手动输入数据目录路径")
        print()
        
    except Exception as e:
        print(f"\n✗ 示例运行失败: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

