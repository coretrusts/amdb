# -*- coding: utf-8 -*-
"""
区块链应用使用AmDb数据库示例
展示如何在区块链项目中使用AmDb
"""

from src.amdb import Database
import json
import hashlib
import time

def create_blockchain_db():
    """创建区块链数据库"""
    db = Database(data_dir='./data/blockchain')
    return db

def add_block(db, block_data):
    """添加区块到数据库"""
    # 计算区块哈希
    block_json = json.dumps(block_data, sort_keys=True).encode()
    block_hash = hashlib.sha256(block_json).hexdigest()
    
    # 存储区块（使用block:hash作为key）
    block_key = f"block:{block_hash}".encode()
    db.put(block_key, block_json)
    
    # 存储区块索引（按高度索引）
    height_key = f"height:{block_data['height']}".encode()
    db.put(height_key, block_hash.encode())
    
    # 存储最新区块
    db.put(b"latest:block", block_hash.encode())
    
    return block_hash

def add_transaction(db, tx_data):
    """添加交易到数据库"""
    # 计算交易哈希
    tx_json = json.dumps(tx_data, sort_keys=True).encode()
    tx_hash = hashlib.sha256(tx_json).hexdigest()
    
    # 存储交易
    tx_key = f"tx:{tx_hash}".encode()
    db.put(tx_key, tx_json)
    
    # 存储交易索引（按区块索引）
    if 'block_hash' in tx_data:
        block_tx_key = f"block:{tx_data['block_hash']}:tx:{tx_hash}".encode()
        db.put(block_tx_key, b"1")
    
    return tx_hash

def get_block(db, block_hash):
    """获取区块"""
    block_key = f"block:{block_hash}".encode()
    block_data = db.get(block_key)
    if block_data:
        return json.loads(block_data.decode())
    return None

def get_latest_block(db):
    """获取最新区块"""
    latest_hash = db.get(b"latest:block")
    if latest_hash:
        return get_block(db, latest_hash.decode())
    return None

def get_transaction(db, tx_hash):
    """获取交易"""
    tx_key = f"tx:{tx_hash}".encode()
    tx_data = db.get(tx_key)
    if tx_data:
        return json.loads(tx_data.decode())
    return None

def query_blocks_by_range(db, start_height, end_height):
    """按高度范围查询区块"""
    blocks = []
    for height in range(start_height, end_height + 1):
        height_key = f"height:{height}".encode()
        block_hash = db.get(height_key)
        if block_hash:
            block = get_block(db, block_hash.decode())
            if block:
                blocks.append(block)
    return blocks

def example_usage():
    """使用示例"""
    print("=" * 80)
    print("区块链使用AmDb数据库示例")
    print("=" * 80)
    print()
    
    # 1. 创建数据库
    print("1. 创建区块链数据库...")
    db = create_blockchain_db()
    print("✓ 数据库创建成功")
    print()
    
    # 2. 添加创世区块
    print("2. 添加创世区块...")
    genesis_block = {
        "height": 0,
        "timestamp": int(time.time()),
        "prev_hash": "0" * 64,
        "merkle_root": "0" * 64,
        "transactions": [],
        "nonce": 0
    }
    genesis_hash = add_block(db, genesis_block)
    print(f"✓ 创世区块已添加: {genesis_hash}")
    print()
    
    # 3. 添加交易
    print("3. 添加交易...")
    tx1 = {
        "from": "address1",
        "to": "address2",
        "amount": 100,
        "block_hash": genesis_hash
    }
    tx1_hash = add_transaction(db, tx1)
    print(f"✓ 交易已添加: {tx1_hash}")
    print()
    
    # 4. 添加新区块
    print("4. 添加新区块...")
    block1 = {
        "height": 1,
        "timestamp": int(time.time()),
        "prev_hash": genesis_hash,
        "merkle_root": "abc123",
        "transactions": [tx1_hash],
        "nonce": 12345
    }
    block1_hash = add_block(db, block1)
    print(f"✓ 区块已添加: {block1_hash}")
    print()
    
    # 5. 查询区块
    print("5. 查询区块...")
    latest = get_latest_block(db)
    print(f"✓ 最新区块高度: {latest['height']}")
    print(f"  区块哈希: {block1_hash}")
    print()
    
    # 6. 批量添加区块（模拟区块链运行）
    print("6. 批量添加区块（模拟区块链运行）...")
    items = []
    for i in range(2, 10):
        block = {
            "height": i,
            "timestamp": int(time.time()) + i,
            "prev_hash": block1_hash if i == 2 else f"prev_hash_{i-1}",
            "merkle_root": f"merkle_{i}",
            "transactions": [],
            "nonce": i * 1000
        }
        block_json = json.dumps(block, sort_keys=True).encode()
        block_hash = hashlib.sha256(block_json).hexdigest()
        block_key = f"block:{block_hash}".encode()
        height_key = f"height:{i}".encode()
        items.append((block_key, block_json))
        items.append((height_key, block_hash.encode()))
    
    success, _ = db.batch_put(items)
    print(f"✓ 批量添加 {len(items)//2} 个区块: {'成功' if success else '失败'}")
    print()
    
    # 7. 查询区块范围
    print("7. 查询区块范围...")
    blocks = query_blocks_by_range(db, 0, 5)
    print(f"✓ 查询到 {len(blocks)} 个区块")
    for block in blocks:
        print(f"  高度 {block['height']}: {block.get('merkle_root', 'N/A')[:16]}...")
    print()
    
    # 8. 刷新到磁盘
    print("8. 刷新数据到磁盘...")
    db.flush()
    print("✓ 数据已持久化")
    print()
    
    # 9. 获取统计信息
    print("9. 数据库统计信息...")
    stats = db.get_stats()
    print(f"✓ 总键数: {stats['total_keys']}")
    print(f"  Merkle根: {stats['merkle_root'][:32]}...")
    print()
    
    print("=" * 80)
    print("示例完成！")
    print("=" * 80)

if __name__ == "__main__":
    example_usage()

