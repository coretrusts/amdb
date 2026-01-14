# -*- coding: utf-8 -*-
"""
创建区块链数据库并写入区块数据
演示AmDb如何存储区块链数据
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.amdb import Database
import hashlib
import time
import json

def generate_block_hash(block_data: dict) -> str:
    """生成区块哈希"""
    block_str = json.dumps(block_data, sort_keys=True)
    return hashlib.sha256(block_str.encode()).hexdigest()

def create_blockchain_database():
    """创建区块链数据库并写入区块数据"""
    
    # 数据库路径
    db_path = './data/blockchain_db'
    
    print("=" * 80)
    print("创建区块链数据库")
    print("=" * 80)
    print(f"数据库路径: {db_path}")
    print()
    
    # 创建数据库
    print("1. 初始化数据库...")
    db = Database(data_dir=db_path, enable_sharding=True, shard_count=4)
    print("   ✓ 数据库初始化完成")
    print()
    
    # 创建创世区块
    print("2. 创建创世区块...")
    genesis_block = {
        "block_number": 0,
        "timestamp": int(time.time()),
        "previous_hash": "0" * 64,
        "merkle_root": "0" * 64,
        "transactions": [
            {
                "tx_id": "genesis_001",
                "from": "system",
                "to": "miner_001",
                "amount": 1000000,
                "type": "reward"
            }
        ],
        "nonce": 0,
        "difficulty": 1
    }
    genesis_block["hash"] = generate_block_hash(genesis_block)
    
    # 写入创世区块
    block_key = f"block:{genesis_block['block_number']:010d}".encode()
    block_value = json.dumps(genesis_block, ensure_ascii=False).encode('utf-8')
    success, merkle_root = db.put(block_key, block_value)
    
    if success:
        print(f"   ✓ 创世区块写入成功")
        print(f"   区块号: {genesis_block['block_number']}")
        print(f"   区块哈希: {genesis_block['hash'][:16]}...")
        print(f"   Merkle根: {merkle_root.hex()[:16]}...")
    else:
        print("   ✗ 创世区块写入失败")
        return
    print()
    
    # 创建多个区块
    print("3. 创建并写入多个区块...")
    num_blocks = 10
    previous_hash = genesis_block["hash"]
    
    for i in range(1, num_blocks + 1):
        # 生成一些交易
        transactions = []
        for j in range(5):  # 每个区块5笔交易
            tx = {
                "tx_id": f"tx_{i:05d}_{j:03d}",
                "from": f"account_{j % 10:03d}",
                "to": f"account_{(j + 1) % 10:03d}",
                "amount": (j + 1) * 100,
                "fee": 1,
                "timestamp": int(time.time()) + j
            }
            transactions.append(tx)
        
        # 计算Merkle根（简化版）
        tx_hashes = [hashlib.sha256(json.dumps(tx, sort_keys=True).encode()).hexdigest() for tx in transactions]
        merkle_root_hash = hashlib.sha256(''.join(tx_hashes).encode()).hexdigest()
        
        # 创建区块
        block = {
            "block_number": i,
            "timestamp": int(time.time()) + i,
            "previous_hash": previous_hash,
            "merkle_root": merkle_root_hash,
            "transactions": transactions,
            "nonce": i * 1000,
            "difficulty": 2
        }
        block["hash"] = generate_block_hash(block)
        
        # 写入区块
        block_key = f"block:{block['block_number']:010d}".encode()
        block_value = json.dumps(block, ensure_ascii=False).encode('utf-8')
        success, merkle_root = db.put(block_key, block_value)
        
        if success:
            print(f"   ✓ 区块 {i} 写入成功 (哈希: {block['hash'][:16]}...)")
        else:
            print(f"   ✗ 区块 {i} 写入失败")
        
        previous_hash = block["hash"]
    
    print()
    
    # 写入账户状态
    print("4. 写入账户状态...")
    accounts = {}
    for i in range(10):
        account_id = f"account_{i:03d}"
        account_data = {
            "account_id": account_id,
            "balance": 10000 + i * 1000,
            "nonce": 0,
            "last_transaction": None
        }
        account_key = f"account:{account_id}".encode()
        account_value = json.dumps(account_data, ensure_ascii=False).encode('utf-8')
        success, _ = db.put(account_key, account_value)
        if success:
            accounts[account_id] = account_data
            print(f"   ✓ 账户 {account_id} 写入成功 (余额: {account_data['balance']})")
    
    print()
    
    # 写入交易索引
    print("5. 写入交易索引...")
    tx_count = 0
    for i in range(1, num_blocks + 1):
        block_key = f"block:{i:010d}".encode()
        block_data = db.get(block_key)
        if block_data:
            block = json.loads(block_data.decode('utf-8'))
            for tx in block.get('transactions', []):
                tx_key = f"tx:{tx['tx_id']}".encode()
                tx_index = {
                    "tx_id": tx['tx_id'],
                    "block_number": i,
                    "block_hash": block['hash'],
                    "index_in_block": block['transactions'].index(tx)
                }
                tx_value = json.dumps(tx_index, ensure_ascii=False).encode('utf-8')
                success, _ = db.put(tx_key, tx_value)
                if success:
                    tx_count += 1
    
    print(f"   ✓ 写入 {tx_count} 个交易索引")
    print()
    
    # 刷新数据到磁盘
    print("6. 刷新数据到磁盘...")
    db.flush(async_mode=False)
    print("   ✓ 数据已刷新到磁盘")
    print()
    
    # 显示统计信息
    print("7. 数据库统计信息:")
    stats = db.get_stats()
    print(f"   总键数: {stats.get('total_keys', 0)}")
    print(f"   当前版本: {stats.get('current_version', 0)}")
    print(f"   Merkle根哈希: {stats.get('merkle_root', 'N/A')[:32]}...")
    print(f"   分片启用: {stats.get('sharding_enabled', False)}")
    if stats.get('sharding_enabled'):
        print(f"   分片数量: {stats.get('shard_count', 0)}")
    print()
    
    # 验证数据
    print("8. 验证数据读取...")
    test_keys = [
        b"block:0000000000",  # 创世区块
        b"block:0000000005",  # 第5个区块
        b"block:0000000010",  # 第10个区块
        b"account:account_001",
        b"tx:tx_00005_001"
    ]
    
    for key in test_keys:
        value = db.get(key)
        if value:
            data = json.loads(value.decode('utf-8'))
            if b'block:' in key:
                print(f"   ✓ 读取区块 {data.get('block_number', 'N/A')} (哈希: {data.get('hash', 'N/A')[:16]}...)")
            elif b'account:' in key:
                print(f"   ✓ 读取账户 {data.get('account_id', 'N/A')} (余额: {data.get('balance', 0)})")
            elif b'tx:' in key:
                print(f"   ✓ 读取交易 {data.get('tx_id', 'N/A')} (区块: {data.get('block_number', 'N/A')})")
        else:
            print(f"   ✗ 未找到键: {key.decode('utf-8')}")
    
    print()
    print("=" * 80)
    print("区块链数据库创建完成！")
    print("=" * 80)
    print()
    print("数据库路径:", db_path)
    print("包含数据:")
    print("  - 11 个区块 (包括创世区块)")
    print("  - 10 个账户状态")
    print("  - 50 个交易索引")
    print()
    print("可以使用以下命令查看数据:")
    print("  python3 amdb-cli")
    print("  connect blockchain_db")
    print("  get block:0000000001")
    print("  select * from block")
    print("  select * from account")
    print()

if __name__ == "__main__":
    create_blockchain_database()

