#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建多个示例数据库
演示如何创建和管理多个独立的数据库实例
"""

import sys
import os
import time
import json
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.amdb import Database

def create_database(name: str, data_dir: str, description: str):
    """创建单个数据库并写入示例数据"""
    print(f'\n{"=" * 80}')
    print(f'创建数据库: {name}')
    print(f'{"=" * 80}')
    print(f'描述: {description}')
    print(f'数据目录: {data_dir}')
    
    # 清理旧数据（如果存在）
    if os.path.exists(data_dir):
        import shutil
        shutil.rmtree(data_dir)
        print('✓ 已清理旧数据')
    
    # 创建数据库实例
    db = Database(data_dir=data_dir, config_path='./amdb.ini')
    print('✓ 数据库初始化成功')
    
    # 根据数据库类型写入不同的示例数据
    if name == "用户数据库":
        # 用户数据库：存储用户信息
        users = [
            ("user_001", {"name": "张三", "email": "zhangsan@example.com", "role": "admin", "balance": 1000.50}),
            ("user_002", {"name": "李四", "email": "lisi@example.com", "role": "user", "balance": 2500.75}),
            ("user_003", {"name": "王五", "email": "wangwu@example.com", "role": "user", "balance": 500.00}),
            ("user_004", {"name": "赵六", "email": "zhaoliu@example.com", "role": "vip", "balance": 3000.25}),
            ("user_005", {"name": "钱七", "email": "qianqi@example.com", "role": "user", "balance": 1500.00}),
        ]
        items = [(f"user:{user_id}".encode(), json.dumps(user_data, ensure_ascii=False).encode()) 
                 for user_id, user_data in users]
        db.batch_put(items)
        print(f'✓ 写入 {len(users)} 个用户')
        
    elif name == "交易数据库":
        # 交易数据库：存储交易记录
        transactions = []
        for i in range(1, 51):  # 50笔交易
            tx_id = f"tx_{i:06d}"
            tx_data = {
                "from": f"user_{(i % 5) + 1:03d}",
                "to": f"user_{((i + 1) % 5) + 1:03d}",
                "amount": round(10.0 + (i * 0.5), 2),
                "timestamp": time.time() - (50 - i) * 60,
                "status": "completed" if i % 10 != 0 else "pending",
                "type": "transfer"
            }
            key = f"transaction:{tx_id}".encode()
            value = json.dumps(tx_data, ensure_ascii=False).encode()
            transactions.append((key, value))
        
        # 分批写入
        batch_size = 20
        for i in range(0, len(transactions), batch_size):
            batch = transactions[i:i+batch_size]
            db.batch_put(batch)
        print(f'✓ 写入 {len(transactions)} 笔交易')
        
    elif name == "区块数据库":
        # 区块数据库：存储区块数据
        blocks = []
        for i in range(1, 31):  # 30个区块
            block_id = f"block_{i:06d}"
            block_data = {
                "block_number": i,
                "previous_hash": f"hash_{i-1:06d}" if i > 1 else "0" * 64,
                "merkle_root": f"merkle_{i:06d}",
                "timestamp": time.time() - (30 - i) * 300,
                "transaction_count": 5,
                "miner": f"miner_{i % 3 + 1}",
                "difficulty": 1000 + i * 10
            }
            key = f"block:{block_id}".encode()
            value = json.dumps(block_data, ensure_ascii=False).encode()
            blocks.append((key, value))
        
        db.batch_put(blocks)
        print(f'✓ 写入 {len(blocks)} 个区块')
        
    elif name == "智能合约数据库":
        # 智能合约数据库：存储智能合约
        contracts = [
            ("contract_001", {"name": "TokenContract", "address": "0x1234...", "balance": 1000000, "type": "ERC20"}),
            ("contract_002", {"name": "NFTContract", "address": "0x5678...", "balance": 500000, "type": "ERC721"}),
            ("contract_003", {"name": "DeFiContract", "address": "0x9abc...", "balance": 2000000, "type": "DeFi"}),
            ("contract_004", {"name": "GameContract", "address": "0xdef0...", "balance": 300000, "type": "Game"}),
        ]
        items = [(f"contract:{contract_id}".encode(), json.dumps(contract_data, ensure_ascii=False).encode()) 
                 for contract_id, contract_data in contracts]
        db.batch_put(items)
        print(f'✓ 写入 {len(contracts)} 个智能合约')
        
    elif name == "日志数据库":
        # 日志数据库：存储系统日志
        logs = []
        for i in range(1, 101):  # 100条日志
            log_id = f"log_{i:06d}"
            log_data = {
                "level": ["INFO", "WARNING", "ERROR"][i % 3],
                "message": f"系统日志消息 {i}",
                "timestamp": time.time() - (100 - i) * 10,
                "module": f"module_{i % 5 + 1}",
                "user_id": f"user_{(i % 5) + 1:03d}"
            }
            key = f"log:{log_id}".encode()
            value = json.dumps(log_data, ensure_ascii=False).encode()
            logs.append((key, value))
        
        # 分批写入
        batch_size = 25
        for i in range(0, len(logs), batch_size):
            batch = logs[i:i+batch_size]
            db.batch_put(batch)
        print(f'✓ 写入 {len(logs)} 条日志')
    
    # 获取统计信息
    stats = db.get_stats()
    print(f'✓ 总键数: {stats.get("total_keys", 0)}')
    print(f'✓ Merkle根哈希: {stats.get("merkle_root", "N/A")[:16]}...')
    
    return db

def main():
    """创建多个数据库"""
    print('=' * 80)
    print('创建多个示例数据库')
    print('=' * 80)
    
    # 定义要创建的数据库
    databases = [
        {
            "name": "用户数据库",
            "data_dir": "./data/user_db",
            "description": "存储用户账户信息、余额等"
        },
        {
            "name": "交易数据库",
            "data_dir": "./data/transaction_db",
            "description": "存储所有交易记录"
        },
        {
            "name": "区块数据库",
            "data_dir": "./data/block_db",
            "description": "存储区块链区块数据"
        },
        {
            "name": "智能合约数据库",
            "data_dir": "./data/contract_db",
            "description": "存储智能合约信息"
        },
        {
            "name": "日志数据库",
            "data_dir": "./data/log_db",
            "description": "存储系统日志和审计记录"
        }
    ]
    
    created_dbs = []
    
    for db_info in databases:
        try:
            db = create_database(
                db_info["name"],
                db_info["data_dir"],
                db_info["description"]
            )
            created_dbs.append(db_info)
        except Exception as e:
            print(f'✗ 创建失败: {type(e).__name__}: {e}')
            import traceback
            traceback.print_exc()
    
    # 总结
    print()
    print('=' * 80)
    print('数据库创建完成总结')
    print('=' * 80)
    print()
    print(f'✓ 成功创建 {len(created_dbs)} 个数据库:')
    for db_info in created_dbs:
        print(f'  - {db_info["name"]}: {db_info["data_dir"]}')
    print()
    print('使用方式:')
    print('  1. GUI管理器:')
    print('     - 启动: python amdb_manager.py')
    print('     - 连接时选择对应的数据目录')
    print('  2. Python代码:')
    print('     from src.amdb import Database')
    print('     db = Database(data_dir="./data/user_db")')
    print()
    print('数据库列表:')
    for db_info in created_dbs:
        print(f'  - {db_info["name"]}')
        print(f'    目录: {db_info["data_dir"]}')
        print(f'    说明: {db_info["description"]}')
        print()

if __name__ == "__main__":
    try:
        main()
        print('✓ 所有数据库创建成功！')
    except Exception as e:
        print(f'✗ 创建失败: {type(e).__name__}: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)

