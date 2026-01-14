# -*- coding: utf-8 -*-
"""
区块链项目集成AmDb完整示例
展示如何在真实的区块链项目中使用AmDb
"""

import sys
from pathlib import Path

# 方式1: 如果AmDb在项目目录中
amdb_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(amdb_path))

# 方式2: 如果已安装AmDb包
# from amdb import Database

from amdb import Database
import json
import hashlib
import time
from typing import Dict, List, Optional

class Blockchain:
    """简单的区块链实现，使用AmDb存储"""
    
    def __init__(self, data_dir='./data/my_blockchain'):
        # 初始化AmDb数据库
        self.db = Database(data_dir=data_dir)
        self.current_height = 0
        
        # 加载最新区块
        latest = self._get_latest_block()
        if latest:
            self.current_height = latest['height']
    
    def _get_latest_block(self) -> Optional[Dict]:
        """获取最新区块"""
        latest_hash = self.db.get(b"latest:block")
        if latest_hash:
            block_hash = latest_hash.decode()
            return self.get_block(block_hash)
        return None
    
    def create_genesis_block(self):
        """创建创世区块"""
        if self.current_height > 0:
            print("区块链已存在，跳过创世区块创建")
            return
        
        genesis = {
            "height": 0,
            "timestamp": int(time.time()),
            "prev_hash": "0" * 64,
            "merkle_root": "0" * 64,
            "transactions": [],
            "nonce": 0,
            "difficulty": 4
        }
        
        block_hash = self._store_block(genesis)
        print(f"✓ 创世区块已创建: {block_hash}")
        self.current_height = 0
    
    def _store_block(self, block_data: Dict) -> str:
        """存储区块到数据库"""
        block_json = json.dumps(block_data, sort_keys=True).encode()
        block_hash = hashlib.sha256(block_json).hexdigest()
        
        # 存储区块
        block_key = f"block:{block_hash}".encode()
        self.db.put(block_key, block_json)
        
        # 存储高度索引
        height_key = f"height:{block_data['height']}".encode()
        self.db.put(height_key, block_hash.encode())
        
        # 更新最新区块
        self.db.put(b"latest:block", block_hash.encode())
        
        # 存储Merkle根（用于验证）
        merkle_key = f"merkle:{block_data['height']}".encode()
        self.db.put(merkle_key, block_data['merkle_root'].encode())
        
        return block_hash
    
    def add_transaction(self, tx_data: Dict) -> str:
        """添加交易"""
        tx_json = json.dumps(tx_data, sort_keys=True).encode()
        tx_hash = hashlib.sha256(tx_json).hexdigest()
        
        # 存储交易
        tx_key = f"tx:{tx_hash}".encode()
        self.db.put(tx_key, tx_json)
        
        # 存储待处理交易（pending）
        pending_key = f"pending:tx:{tx_hash}".encode()
        self.db.put(pending_key, tx_json)
        
        return tx_hash
    
    def mine_block(self, transactions: List[str]) -> str:
        """挖矿（创建新区块）"""
        # 获取待处理交易
        pending_txs = []
        for tx_hash in transactions:
            pending_key = f"pending:tx:{tx_hash}".encode()
            tx_data = self.db.get(pending_key)
            if tx_data:
                pending_txs.append(tx_hash)
        
        # 计算Merkle根
        if pending_txs:
            merkle_root = self._calculate_merkle_root(pending_txs)
        else:
            merkle_root = "0" * 64
        
        # 获取上一个区块
        prev_block = self._get_latest_block()
        prev_hash = prev_block['block_hash'] if prev_block else "0" * 64
        
        # 创建新区块
        new_height = self.current_height + 1
        block = {
            "height": new_height,
            "timestamp": int(time.time()),
            "prev_hash": prev_hash,
            "merkle_root": merkle_root,
            "transactions": pending_txs,
            "nonce": 0,
            "difficulty": 4
        }
        
        # 简单挖矿（找到满足难度的nonce）
        block_hash = self._mine(block)
        
        # 存储区块
        block['block_hash'] = block_hash
        stored_hash = self._store_block(block)
        
        # 从pending中移除已打包的交易
        for tx_hash in pending_txs:
            pending_key = f"pending:tx:{tx_hash}".encode()
            self.db.delete(pending_key)
        
        self.current_height = new_height
        
        # 刷新到磁盘
        self.db.flush()
        
        return block_hash
    
    def _mine(self, block: Dict) -> str:
        """简单挖矿算法"""
        difficulty = block.get('difficulty', 4)
        target = "0" * difficulty
        
        nonce = 0
        while True:
            block['nonce'] = nonce
            block_json = json.dumps(block, sort_keys=True).encode()
            block_hash = hashlib.sha256(block_json).hexdigest()
            
            if block_hash[:difficulty] == target:
                return block_hash
            
            nonce += 1
            if nonce % 10000 == 0:
                print(f"挖矿中... nonce: {nonce}")
    
    def _calculate_merkle_root(self, transactions: List[str]) -> str:
        """计算Merkle根"""
        if not transactions:
            return "0" * 64
        
        # 简化的Merkle根计算
        combined = "".join(transactions)
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def get_block(self, block_hash: str) -> Optional[Dict]:
        """获取区块"""
        block_key = f"block:{block_hash}".encode()
        block_data = self.db.get(block_key)
        if block_data:
            block = json.loads(block_data.decode())
            block['block_hash'] = block_hash
            return block
        return None
    
    def get_block_by_height(self, height: int) -> Optional[Dict]:
        """按高度获取区块"""
        height_key = f"height:{height}".encode()
        block_hash = self.db.get(height_key)
        if block_hash:
            return self.get_block(block_hash.decode())
        return None
    
    def get_transaction(self, tx_hash: str) -> Optional[Dict]:
        """获取交易"""
        tx_key = f"tx:{tx_hash}".encode()
        tx_data = self.db.get(tx_key)
        if tx_data:
            return json.loads(tx_data.decode())
        return None
    
    def get_pending_transactions(self) -> List[Dict]:
        """获取待处理交易"""
        all_keys = self.db.version_manager.get_all_keys()
        pending_txs = []
        
        for key in all_keys:
            if key.startswith(b"pending:tx:"):
                tx_data = self.db.get(key)
                if tx_data:
                    pending_txs.append(json.loads(tx_data.decode()))
        
        return pending_txs
    
    def get_chain_info(self) -> Dict:
        """获取链信息"""
        stats = self.db.get_stats()
        latest = self._get_latest_block()
        
        return {
            "current_height": self.current_height,
            "total_keys": stats['total_keys'],
            "merkle_root": stats['merkle_root'],
            "latest_block": latest['block_hash'] if latest else None,
            "pending_transactions": len(self.get_pending_transactions())
        }

def main():
    """主函数 - 演示区块链使用"""
    print("=" * 80)
    print("区块链集成AmDb示例")
    print("=" * 80)
    print()
    
    # 1. 创建区块链
    print("1. 创建区块链...")
    blockchain = Blockchain(data_dir='./data/demo_blockchain')
    print("✓ 区块链数据库已创建")
    print()
    
    # 2. 创建创世区块
    print("2. 创建创世区块...")
    blockchain.create_genesis_block()
    print()
    
    # 3. 添加交易
    print("3. 添加交易...")
    tx1 = blockchain.add_transaction({
        "from": "Alice",
        "to": "Bob",
        "amount": 50,
        "fee": 1
    })
    print(f"✓ 交易1已添加: {tx1}")
    
    tx2 = blockchain.add_transaction({
        "from": "Bob",
        "to": "Charlie",
        "amount": 30,
        "fee": 1
    })
    print(f"✓ 交易2已添加: {tx2}")
    print()
    
    # 4. 挖矿（创建区块）
    print("4. 挖矿创建区块...")
    block1_hash = blockchain.mine_block([tx1, tx2])
    print(f"✓ 区块1已创建: {block1_hash}")
    print()
    
    # 5. 添加更多交易和区块
    print("5. 添加更多交易和区块...")
    for i in range(3):
        tx = blockchain.add_transaction({
            "from": f"User{i}",
            "to": f"User{i+1}",
            "amount": 10 * (i + 1),
            "fee": 1
        })
        print(f"  交易已添加: {tx}")
    
    # 批量挖矿
    pending = blockchain.get_pending_transactions()
    if pending:
        tx_hashes = [tx.get('tx_hash', '') for tx in pending]
        block_hash = blockchain.mine_block(tx_hashes[:3])
        print(f"✓ 区块已创建: {block_hash}")
    print()
    
    # 6. 查询区块
    print("6. 查询区块...")
    for height in range(blockchain.current_height + 1):
        block = blockchain.get_block_by_height(height)
        if block:
            print(f"  高度 {height}: {block['block_hash'][:16]}... (包含 {len(block.get('transactions', []))} 笔交易)")
    print()
    
    # 7. 获取链信息
    print("7. 链信息...")
    info = blockchain.get_chain_info()
    print(f"  当前高度: {info['current_height']}")
    print(f"  总键数: {info['total_keys']}")
    print(f"  待处理交易: {info['pending_transactions']}")
    print()
    
    # 8. 验证数据持久化
    print("8. 验证数据持久化...")
    blockchain.db.flush()
    print("✓ 数据已刷新到磁盘")
    print()
    
    print("=" * 80)
    print("示例完成！")
    print("=" * 80)
    print()
    print("数据库位置: ./data/demo_blockchain")
    print("可以使用CLI查看: amdb-cli --connect ./data/demo_blockchain")

if __name__ == "__main__":
    main()

