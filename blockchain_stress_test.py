# -*- coding: utf-8 -*-
"""
区块链数据库压力测试
测试大量区块、交易和账户的读写性能
"""

import sys
import os
from pathlib import Path
import time
import hashlib
import json
import random

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.amdb import Database

def generate_block_hash(block_data: dict) -> str:
    """生成区块哈希"""
    block_str = json.dumps(block_data, sort_keys=True)
    return hashlib.sha256(block_str.encode()).hexdigest()

def blockchain_stress_test():
    """区块链数据库压力测试"""
    
    db_path = './data/blockchain_stress_test'
    
    print("=" * 80)
    print("区块链数据库压力测试")
    print("=" * 80)
    print()
    
    # 清理旧数据库
    if os.path.exists(db_path):
        import shutil
        print("清理旧数据库...")
        shutil.rmtree(db_path)
        print("✓ 清理完成")
        print()
    
    # 创建数据库
    print("1. 初始化数据库...")
    start_time = time.time()
    db = Database(data_dir=db_path, enable_sharding=True, shard_count=8)
    init_time = time.time() - start_time
    print(f"   ✓ 数据库初始化完成 (耗时: {init_time:.3f}秒)")
    print()
    
    # 测试参数
    num_blocks = 1000  # 区块数量
    tx_per_block = 10  # 每个区块的交易数
    num_accounts = 100  # 账户数量
    
    print("2. 写入测试数据...")
    print(f"   区块数: {num_blocks}")
    print(f"   每区块交易数: {tx_per_block}")
    print(f"   账户数: {num_accounts}")
    print(f"   预计总记录数: {num_blocks + num_blocks * tx_per_block + num_accounts}")
    print()
    
    # 写入账户
    print("   2.1 写入账户状态...")
    start_time = time.time()
    account_items = []
    for i in range(num_accounts):
        account_id = f"account_{i:05d}"
        account_data = {
            "account_id": account_id,
            "balance": random.randint(1000, 100000),
            "nonce": 0,
            "created_at": int(time.time())
        }
        account_key = f"account:{account_id}".encode()
        account_value = json.dumps(account_data, ensure_ascii=False).encode('utf-8')
        account_items.append((account_key, account_value))
    
    # 批量写入账户
    success, _ = db.batch_put(account_items)
    account_write_time = time.time() - start_time
    if success:
        print(f"      ✓ 写入 {num_accounts} 个账户 (耗时: {account_write_time:.3f}秒, 速度: {num_accounts/account_write_time:.0f} 记录/秒)")
    else:
        print("      ✗ 账户写入失败")
        return
    print()
    
    # 写入区块和交易
    print("   2.2 写入区块和交易...")
    start_time = time.time()
    previous_hash = "0" * 64
    total_tx = 0
    batch_size = 100  # 每批写入100个区块
    
    for batch_start in range(0, num_blocks, batch_size):
        batch_end = min(batch_start + batch_size, num_blocks)
        batch_items = []
        
        for i in range(batch_start, batch_end):
            # 生成交易
            transactions = []
            for j in range(tx_per_block):
                tx = {
                    "tx_id": f"tx_{i:06d}_{j:03d}",
                    "from": f"account_{random.randint(0, num_accounts-1):05d}",
                    "to": f"account_{random.randint(0, num_accounts-1):05d}",
                    "amount": random.randint(1, 1000),
                    "fee": random.randint(1, 10),
                    "timestamp": int(time.time()) + i * tx_per_block + j
                }
                transactions.append(tx)
            
            # 计算Merkle根
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
            
            # 添加区块到批量列表
            block_key = f"block:{block['block_number']:010d}".encode()
            block_value = json.dumps(block, ensure_ascii=False).encode('utf-8')
            batch_items.append((block_key, block_value))
            
            # 添加交易索引到批量列表
            for tx in transactions:
                tx_key = f"tx:{tx['tx_id']}".encode()
                tx_index = {
                    "tx_id": tx['tx_id'],
                    "block_number": i,
                    "block_hash": block['hash'],
                    "index_in_block": transactions.index(tx)
                }
                tx_value = json.dumps(tx_index, ensure_ascii=False).encode('utf-8')
                batch_items.append((tx_key, tx_value))
                total_tx += 1
            
            previous_hash = block["hash"]
        
        # 批量写入
        success, _ = db.batch_put(batch_items)
        if not success:
            print(f"      ✗ 批量写入失败 (区块 {batch_start}-{batch_end-1})")
            return
        
        # 显示进度
        progress = (batch_end / num_blocks) * 100
        print(f"      进度: {progress:.1f}% ({batch_end}/{num_blocks} 区块, {total_tx} 交易)")
    
    block_write_time = time.time() - start_time
    total_records = num_blocks + total_tx
    print(f"      ✓ 写入 {num_blocks} 个区块和 {total_tx} 个交易索引 (耗时: {block_write_time:.3f}秒, 速度: {total_records/block_write_time:.0f} 记录/秒)")
    print()
    
    # 刷新到磁盘
    print("   2.3 刷新数据到磁盘...")
    start_time = time.time()
    db.flush(async_mode=False)
    flush_time = time.time() - start_time
    print(f"      ✓ 数据已刷新到磁盘 (耗时: {flush_time:.3f}秒)")
    print()
    
    # 读取性能测试
    print("3. 读取性能测试...")
    
    # 3.1 随机读取区块
    print("   3.1 随机读取区块 (1000次)...")
    start_time = time.time()
    read_count = 0
    for _ in range(1000):
        block_num = random.randint(0, num_blocks - 1)
        block_key = f"block:{block_num:010d}".encode()
        value = db.get(block_key)
        if value:
            read_count += 1
    random_read_time = time.time() - start_time
    print(f"      ✓ 随机读取完成 (成功: {read_count}/1000, 耗时: {random_read_time:.3f}秒, 速度: {1000/random_read_time:.0f} 次/秒)")
    print()
    
    # 3.2 顺序读取区块
    print("   3.2 顺序读取区块 (100个)...")
    start_time = time.time()
    read_count = 0
    for i in range(100):
        block_key = f"block:{i:010d}".encode()
        value = db.get(block_key)
        if value:
            read_count += 1
    sequential_read_time = time.time() - start_time
    print(f"      ✓ 顺序读取完成 (成功: {read_count}/100, 耗时: {sequential_read_time:.3f}秒, 速度: {100/sequential_read_time:.0f} 次/秒)")
    print()
    
    # 3.3 读取账户
    print("   3.3 随机读取账户 (1000次)...")
    start_time = time.time()
    read_count = 0
    for _ in range(1000):
        account_id = f"account_{random.randint(0, num_accounts-1):05d}"
        account_key = f"account:{account_id}".encode()
        value = db.get(account_key)
        if value:
            read_count += 1
    account_read_time = time.time() - start_time
    print(f"      ✓ 账户读取完成 (成功: {read_count}/1000, 耗时: {account_read_time:.3f}秒, 速度: {1000/account_read_time:.0f} 次/秒)")
    print()
    
    # 3.4 范围查询
    print("   3.4 范围查询区块 (block:0000000000 到 block:0000000100)...")
    start_time = time.time()
    all_keys = db.version_manager.get_all_keys()
    matching_keys = [k for k in all_keys if k.startswith(b'block:')]
    matching_keys.sort()
    range_keys = [k for k in matching_keys if b'block:0000000000' <= k <= b'block:0000000100']
    range_query_time = time.time() - start_time
    print(f"      ✓ 范围查询完成 (找到 {len(range_keys)} 个区块, 耗时: {range_query_time:.3f}秒)")
    print()
    
    # 显示统计信息
    print("4. 数据库统计信息:")
    stats = db.get_stats()
    print(f"   总键数: {stats.get('total_keys', 0)}")
    print(f"   当前版本: {stats.get('current_version', 0)}")
    print(f"   Merkle根哈希: {stats.get('merkle_root', 'N/A')[:32]}...")
    print(f"   分片启用: {stats.get('sharding_enabled', False)}")
    if stats.get('sharding_enabled'):
        print(f"   分片数量: {stats.get('shard_count', 0)}")
    print()
    
    # 性能总结
    print("=" * 80)
    print("性能测试总结")
    print("=" * 80)
    print()
    print("写入性能:")
    print(f"  账户写入: {num_accounts/account_write_time:.0f} 记录/秒")
    print(f"  区块+交易写入: {total_records/block_write_time:.0f} 记录/秒")
    print(f"  总写入时间: {account_write_time + block_write_time:.3f}秒")
    print()
    print("读取性能:")
    print(f"  随机读取区块: {1000/random_read_time:.0f} 次/秒")
    print(f"  顺序读取区块: {100/sequential_read_time:.0f} 次/秒")
    print(f"  随机读取账户: {1000/account_read_time:.0f} 次/秒")
    print()
    print("数据规模:")
    print(f"  区块数: {num_blocks}")
    print(f"  交易数: {total_tx}")
    print(f"  账户数: {num_accounts}")
    print(f"  总记录数: {stats.get('total_keys', 0)}")
    print()
    print("=" * 80)
    print()

if __name__ == "__main__":
    blockchain_stress_test()

