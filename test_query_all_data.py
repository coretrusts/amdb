# -*- coding: utf-8 -*-
"""
测试查询所有数据功能
验证修复后的查询限制问题
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.amdb import Database

def test_query_all_data():
    """测试查询所有数据"""
    
    # 使用压力测试创建的数据库
    db_path = './data/blockchain_stress_test'
    
    print("=" * 80)
    print("测试查询所有数据功能")
    print("=" * 80)
    print()
    
    try:
        db = Database(data_dir=db_path)
        
        # 1. 测试 get_all_keys
        print("1. 测试 get_all_keys...")
        all_keys = db.version_manager.get_all_keys()
        print(f"   ✓ 获取到 {len(all_keys)} 个键")
        print()
        
        # 2. 测试 get 方法
        print("2. 测试 get 方法（随机选择10个键）...")
        import random
        test_keys = random.sample(all_keys, min(10, len(all_keys)))
        success_count = 0
        for key in test_keys:
            value = db.get(key)
            if value:
                success_count += 1
                key_str = key.decode('utf-8', errors='ignore')
                print(f"   ✓ {key_str}: 找到数据 (长度: {len(value)} bytes)")
            else:
                key_str = key.decode('utf-8', errors='ignore')
                print(f"   ✗ {key_str}: 未找到数据")
        print(f"   成功率: {success_count}/{len(test_keys)}")
        print()
        
        # 3. 测试范围查询
        print("3. 测试范围查询（block前缀）...")
        block_keys = [k for k in all_keys if k.startswith(b'block:')]
        print(f"   找到 {len(block_keys)} 个区块键")
        if block_keys:
            # 测试读取前10个和后10个
            test_keys = block_keys[:10] + block_keys[-10:]
            success_count = 0
            for key in test_keys:
                value = db.get(key)
                if value:
                    success_count += 1
            print(f"   测试读取: {success_count}/{len(test_keys)} 成功")
        print()
        
        # 4. 测试账户查询
        print("4. 测试账户查询...")
        account_keys = [k for k in all_keys if k.startswith(b'account:')]
        print(f"   找到 {len(account_keys)} 个账户键")
        if account_keys:
            # 测试读取所有账户
            success_count = 0
            for key in account_keys:
                value = db.get(key)
                if value:
                    success_count += 1
            print(f"   成功读取: {success_count}/{len(account_keys)} 个账户")
        print()
        
        # 5. 测试交易查询
        print("5. 测试交易查询...")
        tx_keys = [k for k in all_keys if k.startswith(b'tx:')]
        print(f"   找到 {len(tx_keys)} 个交易键")
        if tx_keys:
            # 测试读取前100个和后100个
            test_keys = tx_keys[:100] + tx_keys[-100:]
            success_count = 0
            for key in test_keys:
                value = db.get(key)
                if value:
                    success_count += 1
            print(f"   测试读取: {success_count}/{len(test_keys)} 成功")
        print()
        
        # 6. 显示统计信息
        print("6. 数据库统计信息:")
        stats = db.get_stats()
        print(f"   总键数: {stats.get('total_keys', 0)}")
        print(f"   get_all_keys返回: {len(all_keys)}")
        print(f"   差异: {stats.get('total_keys', 0) - len(all_keys)}")
        print()
        
        print("=" * 80)
        print("测试完成")
        print("=" * 80)
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_query_all_data()

