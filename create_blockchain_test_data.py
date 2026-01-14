#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建区块链测试数据
生成区块信息、交易信息、账户信息等测试数据
"""

import sys
import os
import time
import json
import hashlib
import random
from pathlib import Path
from typing import List, Dict, Any

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.amdb import Database

def generate_address() -> str:
    """生成随机地址（模拟以太坊地址格式）"""
    return "0x" + ''.join(random.choices('0123456789abcdef', k=40))

def generate_hash() -> str:
    """生成随机哈希值（64字符）"""
    return ''.join(random.choices('0123456789abcdef', k=64))

def create_blockchain_test_data(data_dir: str = "./data/blockchain_test", 
                                 num_accounts: int = 100,
                                 num_transactions: int = 1000,
                                 num_blocks: int = 100):
    """创建区块链测试数据"""
    
    print("=" * 80)
    print("创建区块链测试数据")
    print("=" * 80)
    print()
    print(f"数据目录: {data_dir}")
    print(f"账户数量: {num_accounts}")
    print(f"交易数量: {num_transactions}")
    print(f"区块数量: {num_blocks}")
    print()
    
    # 清理旧数据（如果存在）
    if os.path.exists(data_dir):
        import shutil
        shutil.rmtree(data_dir)
        print("✓ 已清理旧数据")
    
    # 创建数据库实例
    db = Database(data_dir=data_dir, config_path='./amdb.ini')
    print("✓ 数据库初始化成功")
    print()
    
    # 1. 生成账户信息
    print("=" * 80)
    print("1. 生成账户信息")
    print("=" * 80)
    accounts = []
    account_addresses = []
    
    for i in range(num_accounts):
        address = generate_address()
        account_addresses.append(address)
        account_data = {
            "address": address,
            "balance": round(random.uniform(0, 100000), 8),  # 0-100000，8位小数
            "nonce": random.randint(0, 1000),
            "code_hash": generate_hash(),
            "storage_root": generate_hash(),
            "created_at": time.time() - random.randint(0, 86400 * 365),  # 一年内随机时间
            "last_active": time.time() - random.randint(0, 86400 * 30),  # 30天内随机时间
            "tx_count": random.randint(0, 500),
            "type": random.choice(["EOA", "Contract", "EOA", "EOA"])  # 大部分是EOA
        }
        key = f"account:{address}".encode()
        value = json.dumps(account_data, ensure_ascii=False).encode()
        accounts.append((key, value))
    
    # 分批写入账户
    batch_size = 50
    for i in range(0, len(accounts), batch_size):
        batch = accounts[i:i+batch_size]
        success, _ = db.batch_put(batch)
        if success:
            print(f"  ✓ 写入账户 {i+1}-{min(i+batch_size, len(accounts))}/{len(accounts)}")
    
    print(f"✓ 完成：共写入 {len(accounts)} 个账户")
    print()
    
    # 2. 生成交易信息
    print("=" * 80)
    print("2. 生成交易信息")
    print("=" * 80)
    transactions = []
    tx_hashes = []
    
    for i in range(num_transactions):
        tx_hash = generate_hash()
        tx_hashes.append(tx_hash)
        
        # 随机选择发送方和接收方
        from_addr = random.choice(account_addresses)
        to_addr = random.choice(account_addresses)
        while to_addr == from_addr:  # 确保接收方不同
            to_addr = random.choice(account_addresses)
        
        tx_data = {
            "hash": tx_hash,
            "from": from_addr,
            "to": to_addr,
            "value": round(random.uniform(0.001, 1000), 8),
            "gas": random.randint(21000, 100000),
            "gas_price": random.randint(1, 100) * 10**9,  # Gwei转Wei
            "nonce": random.randint(0, 100),
            "data": "0x" + ''.join(random.choices('0123456789abcdef', k=random.randint(0, 200))),
            "timestamp": time.time() - (num_transactions - i) * 10,  # 模拟时间序列
            "block_number": None,  # 稍后关联到区块
            "block_hash": None,
            "transaction_index": None,
            "status": random.choice(["pending", "confirmed", "failed"]),
            "receipt": {
                "gas_used": random.randint(21000, 100000),
                "cumulative_gas_used": random.randint(21000, 500000),
                "contract_address": None if random.random() > 0.1 else generate_address(),
                "logs": [],
                "logs_bloom": generate_hash(),
                "status": random.choice([0, 1])  # 0失败，1成功
            }
        }
        key = f"transaction:{tx_hash}".encode()
        value = json.dumps(tx_data, ensure_ascii=False).encode()
        transactions.append((key, value))
    
    # 分批写入交易
    batch_size = 100
    for i in range(0, len(transactions), batch_size):
        batch = transactions[i:i+batch_size]
        success, _ = db.batch_put(batch)
        if success:
            print(f"  ✓ 写入交易 {i+1}-{min(i+batch_size, len(transactions))}/{len(transactions)}")
    
    print(f"✓ 完成：共写入 {len(transactions)} 笔交易")
    print()
    
    # 3. 生成区块信息
    print("=" * 80)
    print("3. 生成区块信息")
    print("=" * 80)
    blocks = []
    previous_hash = "0" * 64  # 创世区块的前一个哈希
    
    # 将交易分配到区块
    tx_per_block = num_transactions // num_blocks
    remaining_txs = num_transactions % num_blocks
    
    tx_index = 0
    for block_num in range(1, num_blocks + 1):
        # 计算这个区块包含的交易数量
        block_tx_count = tx_per_block + (1 if block_num <= remaining_txs else 0)
        
        # 获取这个区块的交易
        block_txs = tx_hashes[tx_index:tx_index + block_tx_count]
        tx_index += block_tx_count
        
        # 计算Merkle根（简化版）
        merkle_root = generate_hash()
        
        # 生成区块哈希
        block_hash = generate_hash()
        
        block_data = {
            "block_number": block_num,
            "hash": block_hash,
            "previous_hash": previous_hash,
            "merkle_root": merkle_root,
            "timestamp": time.time() - (num_blocks - block_num) * 15,  # 每15秒一个区块
            "transaction_count": block_tx_count,
            "transactions": block_txs[:10],  # 只存储前10个交易哈希（避免数据过大）
            "miner": random.choice(account_addresses[:10]),  # 从前10个账户中选择矿工
            "difficulty": random.randint(1000, 100000),
            "gas_limit": random.randint(8000000, 15000000),
            "gas_used": random.randint(5000000, 12000000),
            "base_fee_per_gas": random.randint(1, 100) * 10**9,
            "extra_data": "0x" + ''.join(random.choices('0123456789abcdef', k=32)),
            "size": random.randint(10000, 500000),
            "state_root": generate_hash(),
            "receipts_root": generate_hash(),
            "logs_bloom": generate_hash() * 2,  # 256字节
            "uncles": [],
            "uncle_count": 0
        }
        
        key = f"block:{block_num:08d}".encode()
        value = json.dumps(block_data, ensure_ascii=False).encode()
        blocks.append((key, value))
        
        # 更新前一个哈希
        previous_hash = block_hash
        
        # 更新交易数据中的区块信息
        for idx, tx_hash in enumerate(block_txs):
            tx_key = f"transaction:{tx_hash}".encode()
            tx_value = db.get(tx_key)
            if tx_value:
                tx_data = json.loads(tx_value.decode())
                tx_data["block_number"] = block_num
                tx_data["block_hash"] = block_hash
                tx_data["transaction_index"] = idx
                tx_data["status"] = "confirmed"
                db.put(tx_key, json.dumps(tx_data, ensure_ascii=False).encode())
    
    # 分批写入区块
    batch_size = 20
    for i in range(0, len(blocks), batch_size):
        batch = blocks[i:i+batch_size]
        success, _ = db.batch_put(batch)
        if success:
            print(f"  ✓ 写入区块 {i+1}-{min(i+batch_size, len(blocks))}/{len(blocks)}")
    
    print(f"✓ 完成：共写入 {len(blocks)} 个区块")
    print()
    
    # 4. 生成区块头索引（用于快速查询）
    print("=" * 80)
    print("4. 生成索引数据")
    print("=" * 80)
    
    # 区块号到区块哈希的映射
    block_index = []
    for block_num in range(1, num_blocks + 1):
        block_key = f"block:{block_num:08d}".encode()
        block_value = db.get(block_key)
        if block_value:
            block_data = json.loads(block_value.decode())
            index_key = f"block_index:number:{block_num:08d}".encode()
            index_value = block_data["hash"].encode()
            block_index.append((index_key, index_value))
    
    if block_index:
        success, _ = db.batch_put(block_index)
        if success:
            print(f"  ✓ 写入区块索引 {len(block_index)} 条")
    
    # 5. 生成统计信息
    print()
    print("=" * 80)
    print("数据库统计信息")
    print("=" * 80)
    stats = db.get_stats()
    print(f"总键数: {stats.get('total_keys', 0)}")
    print(f"当前版本: {stats.get('current_version', 0)}")
    print(f"Merkle根哈希: {stats.get('merkle_root', 'N/A')[:32]}...")
    print(f"存储目录: {stats.get('storage_dir', 'N/A')}")
    print(f"分片启用: {stats.get('sharding_enabled', False)}")
    if stats.get("sharding_enabled"):
        print(f"分片数量: {stats.get('shard_count', 0)}")
    
    # 刷新所有数据到磁盘
    print()
    print("=" * 80)
    print("5. 刷新数据到磁盘")
    print("=" * 80)
    db.flush()
    print("✓ 数据已刷新到磁盘")
    print()
    
    print("=" * 80)
    print("测试数据创建完成！")
    print("=" * 80)
    print()
    print("数据概览:")
    print(f"  - 账户数据: {num_accounts} 条")
    print(f"  - 交易数据: {num_transactions} 条")
    print(f"  - 区块数据: {num_blocks} 条")
    print(f"  - 索引数据: {len(block_index)} 条")
    print(f"  - 总计: {num_accounts + num_transactions + num_blocks + len(block_index)} 条")
    print()
    print("数据目录:", data_dir)
    print()
    print("可以使用以下方式访问:")
    print("  1. GUI管理器: python amdb_manager.py")
    print("    连接数据目录:", data_dir)
    print("  2. Python代码:")
    print(f"     from src.amdb import Database")
    print(f"     db = Database(data_dir='{data_dir}')")
    print("     # 查询账户")
    print("     account = db.get(b'account:0x...')")
    print("     # 查询交易")
    print("     tx = db.get(b'transaction:0x...')")
    print("     # 查询区块")
    print("     block = db.get(b'block:00000001')")
    print()
    print("  3. 验证数据:")
    print(f"     python verify_blockchain_data.py --data-dir {data_dir}")
    print()
    
    return db

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="创建区块链测试数据")
    parser.add_argument("--data-dir", type=str, default="./data/blockchain_test",
                       help="数据目录路径（默认: ./data/blockchain_test）")
    parser.add_argument("--accounts", type=int, default=100,
                       help="账户数量（默认: 100）")
    parser.add_argument("--transactions", type=int, default=1000,
                       help="交易数量（默认: 1000）")
    parser.add_argument("--blocks", type=int, default=100,
                       help="区块数量（默认: 100）")
    
    args = parser.parse_args()
    
    try:
        db = create_blockchain_test_data(
            data_dir=args.data_dir,
            num_accounts=args.accounts,
            num_transactions=args.transactions,
            num_blocks=args.blocks
        )
        print("✓ 区块链测试数据创建成功！")
    except Exception as e:
        print(f"✗ 创建失败: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

