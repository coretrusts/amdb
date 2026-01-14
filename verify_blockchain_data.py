#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证区块链测试数据
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.amdb import Database

def verify_data(data_dir: str = "./data/blockchain_test"):
    """验证区块链测试数据"""
    
    print("=" * 80)
    print("验证区块链测试数据")
    print("=" * 80)
    print()
    
    # 连接数据库
    db = Database(data_dir=data_dir, config_path='./amdb.ini')
    
    # 刷新数据
    db.flush()
    
    # 获取统计信息
    stats = db.get_stats()
    print(f"总键数: {stats.get('total_keys', 0)}")
    print(f"当前版本: {stats.get('current_version', 0)}")
    print()
    
    # 尝试查询区块
    print("1. 查询区块数据:")
    for block_num in range(1, 6):  # 查询前5个区块
        block_key = f"block:{block_num:08d}".encode()
        block_value = db.get(block_key)
        if block_value:
            block_data = json.loads(block_value.decode())
            print(f"   ✓ 区块 #{block_data['block_number']}: {block_data['hash'][:16]}... "
                  f"(交易数: {block_data['transaction_count']})")
        else:
            print(f"   ✗ 区块 #{block_num}: 未找到")
    
    print()
    
    # 尝试查询交易（从第一个区块获取交易哈希）
    print("2. 查询交易数据:")
    block_key = b"block:00000001"
    block_value = db.get(block_key)
    if block_value:
        block_data = json.loads(block_value.decode())
        transactions = block_data.get('transactions', [])
        if transactions:
            for i, tx_hash in enumerate(transactions[:3]):  # 只查询前3个
                tx_key = f"transaction:{tx_hash}".encode()
                tx_value = db.get(tx_key)
                if tx_value:
                    tx_data = json.loads(tx_value.decode())
                    print(f"   ✓ 交易 {i+1}: {tx_data['hash'][:16]}... "
                          f"({tx_data['from'][:10]}... -> {tx_data['to'][:10]}..., "
                          f"金额: {tx_data['value']})")
                else:
                    print(f"   ✗ 交易 {tx_hash[:16]}...: 未找到")
        else:
            print("   ✗ 区块中没有交易")
    else:
        print("   ✗ 无法获取区块数据")
    
    print()
    
    # 尝试查询账户（从交易中获取地址）
    print("3. 查询账户数据:")
    if block_value:
        block_data = json.loads(block_value.decode())
        transactions = block_data.get('transactions', [])
        if transactions:
            tx_hash = transactions[0]
            tx_key = f"transaction:{tx_hash}".encode()
            tx_value = db.get(tx_key)
            if tx_value:
                tx_data = json.loads(tx_value.decode())
                # 查询发送方账户
                account_key = f"account:{tx_data['from']}".encode()
                account_value = db.get(account_key)
                if account_value:
                    account_data = json.loads(account_value.decode())
                    print(f"   ✓ 账户: {account_data['address'][:20]}... "
                          f"(余额: {account_data['balance']}, "
                          f"类型: {account_data['type']}, "
                          f"交易数: {account_data['tx_count']})")
                else:
                    print(f"   ✗ 账户 {tx_data['from'][:20]}...: 未找到")
    
    print()
    print("=" * 80)
    print("验证完成")
    print("=" * 80)
    print()
    print("数据目录:", data_dir)
    print("可以使用 GUI 管理器查看:")
    print("  python amdb_manager.py")
    print("  然后连接数据目录:", data_dir)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="验证区块链测试数据")
    parser.add_argument("--data-dir", type=str, default="./data/blockchain_test",
                       help="数据目录路径（默认: ./data/blockchain_test）")
    
    args = parser.parse_args()
    
    try:
        verify_data(data_dir=args.data_dir)
    except Exception as e:
        print(f"✗ 验证失败: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

