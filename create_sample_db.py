#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建示例数据库并写入演示数据
用于测试GUI管理器
"""

import sys
import os
import time
import json
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.amdb import Database

def create_sample_database():
    """创建示例数据库并写入演示数据"""
    
    # 创建示例数据库
    sample_dir = "./data/sample_db"
    print(f'创建示例数据库: {sample_dir}')
    
    # 清理旧数据（如果存在）
    if os.path.exists(sample_dir):
        import shutil
        shutil.rmtree(sample_dir)
        print('✓ 已清理旧数据')
    
    # 创建数据库实例
    db = Database(data_dir=sample_dir, config_path='./amdb.ini')
    print('✓ 数据库初始化成功')
    print()
    
    print('=' * 80)
    print('写入演示数据')
    print('=' * 80)
    print()
    
    # 1. 写入用户数据
    print('1. 写入用户数据...')
    users = [
        ("user_001", {"name": "张三", "email": "zhangsan@example.com", "balance": 1000.50}),
        ("user_002", {"name": "李四", "email": "lisi@example.com", "balance": 2500.75}),
        ("user_003", {"name": "王五", "email": "wangwu@example.com", "balance": 500.00}),
        ("user_004", {"name": "赵六", "email": "zhaoliu@example.com", "balance": 3000.25}),
        ("user_005", {"name": "钱七", "email": "qianqi@example.com", "balance": 1500.00}),
    ]
    
    user_items = []
    for user_id, user_data in users:
        key = f"user:{user_id}".encode()
        value = json.dumps(user_data, ensure_ascii=False).encode()
        user_items.append((key, value))
    
    success, _ = db.batch_put(user_items)
    if success:
        print(f'  ✓ 写入 {len(users)} 个用户')
    else:
        print('  ✗ 写入失败')
    
    # 2. 写入交易数据
    print()
    print('2. 写入交易数据...')
    transactions = []
    for i in range(1, 101):  # 100笔交易
        tx_id = f"tx_{i:06d}"
        tx_data = {
            "from": f"user_{(i % 5) + 1:03d}",
            "to": f"user_{((i + 1) % 5) + 1:03d}",
            "amount": round(10.0 + (i * 0.5), 2),
            "timestamp": time.time() - (100 - i) * 60,  # 模拟时间序列
            "status": "completed" if i % 10 != 0 else "pending"
        }
        key = f"transaction:{tx_id}".encode()
        value = json.dumps(tx_data, ensure_ascii=False).encode()
        transactions.append((key, value))
    
    # 分批写入交易
    batch_size = 20
    for i in range(0, len(transactions), batch_size):
        batch = transactions[i:i+batch_size]
        success, _ = db.batch_put(batch)
        if success:
            print(f'  ✓ 写入交易 {i+1}-{min(i+batch_size, len(transactions))}/{len(transactions)}')
    
    # 3. 写入区块数据
    print()
    print('3. 写入区块数据...')
    blocks = []
    for i in range(1, 21):  # 20个区块
        block_id = f"block_{i:06d}"
        block_data = {
            "block_number": i,
            "previous_hash": f"hash_{i-1:06d}" if i > 1 else "0" * 64,
            "merkle_root": f"merkle_{i:06d}",
            "timestamp": time.time() - (20 - i) * 300,  # 每5分钟一个区块
            "transaction_count": 5,
            "miner": f"miner_{i % 3 + 1}"
        }
        key = f"block:{block_id}".encode()
        value = json.dumps(block_data, ensure_ascii=False).encode()
        blocks.append((key, value))
    
    success, _ = db.batch_put(blocks)
    if success:
        print(f'  ✓ 写入 {len(blocks)} 个区块')
    
    # 4. 写入智能合约数据
    print()
    print('4. 写入智能合约数据...')
    contracts = [
        ("contract_001", {"name": "TokenContract", "address": "0x1234...", "balance": 1000000}),
        ("contract_002", {"name": "NFTContract", "address": "0x5678...", "balance": 500000}),
        ("contract_003", {"name": "DeFiContract", "address": "0x9abc...", "balance": 2000000}),
    ]
    
    contract_items = []
    for contract_id, contract_data in contracts:
        key = f"contract:{contract_id}".encode()
        value = json.dumps(contract_data, ensure_ascii=False).encode()
        contract_items.append((key, value))
    
    success, _ = db.batch_put(contract_items)
    if success:
        print(f'  ✓ 写入 {len(contracts)} 个智能合约')
    
    # 5. 写入配置数据
    print()
    print('5. 写入配置数据...')
    configs = [
        ("config:network", {"host": "0.0.0.0", "port": 3888, "max_connections": 100}),
        ("config:performance", {"batch_size": 3000, "cache_size": 100000000}),
        ("config:security", {"enable_auth": False, "enable_encryption": False}),
    ]
    
    config_items = []
    for config_key, config_data in configs:
        key = f"{config_key}".encode()
        value = json.dumps(config_data, ensure_ascii=False).encode()
        config_items.append((key, value))
    
    success, _ = db.batch_put(config_items)
    if success:
        print(f'  ✓ 写入 {len(configs)} 个配置项')
    
    # 获取统计信息
    print()
    print('=' * 80)
    print('数据库统计信息')
    print('=' * 80)
    stats = db.get_stats()
    print(f'总键数: {stats.get("total_keys", 0)}')
    print(f'当前版本: {stats.get("current_version", 0)}')
    print(f'Merkle根哈希: {stats.get("merkle_root", "N/A")[:16]}...')
    print(f'存储目录: {stats.get("storage_dir", "N/A")}')
    print(f'分片启用: {stats.get("sharding_enabled", False)}')
    if stats.get("sharding_enabled"):
        print(f'分片数量: {stats.get("shard_count", 0)}')
    
    print()
    print('=' * 80)
    print('演示数据创建完成！')
    print('=' * 80)
    print()
    print('数据概览:')
    print(f'  - 用户数据: {len(users)} 条')
    print(f'  - 交易数据: {len(transactions)} 条')
    print(f'  - 区块数据: {len(blocks)} 条')
    print(f'  - 智能合约: {len(contracts)} 条')
    print(f'  - 配置数据: {len(configs)} 条')
    print(f'  - 总计: {len(users) + len(transactions) + len(blocks) + len(contracts) + len(configs)} 条')
    print()
    print('可以使用以下方式访问:')
    print('  1. GUI管理器: python amdb_manager.py')
    print('  2. Python代码:')
    print('     from src.amdb import Database')
    print('     db = Database(data_dir="./data/sample_db")')
    print('     value = db.get(b"user:user_001")')
    print()
    
    return db

if __name__ == "__main__":
    try:
        db = create_sample_database()
        print('✓ 示例数据库创建成功！')
    except Exception as e:
        print(f'✗ 创建失败: {type(e).__name__}: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)

