"""
区块链场景使用示例
演示如何在区块链应用中使用AmDb
"""

from src.amdb import Database
import time


def simulate_blockchain_transactions():
    """模拟区块链交易"""
    db = Database(data_dir="./data/blockchain")
    
    print("=== 区块链场景示例 ===\n")
    
    # 初始化账户
    print("1. 初始化账户余额...")
    accounts = {
        b"account:0x1111": b"1000",
        b"account:0x2222": b"2000",
        b"account:0x3333": b"3000",
    }
    
    # 批量初始化
    items = list(accounts.items())
    success, root_hash = db.batch_put(items)
    print(f"   初始化完成，Merkle根: {root_hash.hex()[:16]}...")
    
    # 模拟交易
    print("\n2. 模拟交易...")
    
    # 交易1: 0x1111 转账 100 给 0x2222
    print("   交易1: 0x1111 -> 0x2222 (100)")
    balance1 = int(db.get(b"account:0x1111").decode())
    balance2 = int(db.get(b"account:0x2222").decode())
    
    db.put(b"account:0x1111", str(balance1 - 100).encode())
    db.put(b"account:0x2222", str(balance2 + 100).encode())
    
    # 交易2: 0x2222 转账 50 给 0x3333
    print("   交易2: 0x2222 -> 0x3333 (50)")
    balance2 = int(db.get(b"account:0x2222").decode())
    balance3 = int(db.get(b"account:0x3333").decode())
    
    db.put(b"account:0x2222", str(balance2 - 50).encode())
    db.put(b"account:0x3333", str(balance3 + 50).encode())
    
    # 获取当前状态
    print("\n3. 当前账户余额:")
    for account in accounts.keys():
        balance = db.get(account)
        version = db.version_manager.get_current_version(account)
        print(f"   {account.decode()}: {balance.decode()} (版本: {version})")
    
    # 获取Merkle根（用于区块头）
    root_hash = db.get_root_hash()
    print(f"\n4. 当前状态Merkle根: {root_hash.hex()}")
    
    # 查询历史状态（回滚到交易1之前）
    print("\n5. 查询历史状态（交易1之前）...")
    history1 = db.get_history(b"account:0x1111")
    if len(history1) >= 2:
        prev_version = history1[0]['version']
        prev_balance = db.get(b"account:0x1111", version=prev_version)
        print(f"   账户0x1111在版本{prev_version}的余额: {prev_balance.decode()}")
    
    # 验证数据完整性
    print("\n6. 验证数据完整性...")
    value, proof, root = db.get_with_proof(b"account:0x1111")
    is_valid = db.verify(b"account:0x1111", value, proof)
    print(f"   验证结果: {is_valid}")
    
    # 模拟区块提交
    print("\n7. 模拟区块提交...")
    block_number = 1
    block_hash = db.get_root_hash().hex()
    print(f"   区块 #{block_number}")
    print(f"   区块哈希: {block_hash[:32]}...")
    print(f"   包含交易: 2笔")
    
    # 保存区块信息
    block_key = f"block:{block_number}".encode()
    block_data = f"hash:{block_hash},tx_count:2".encode()
    db.put(block_key, block_data)
    
    print("\n=== 区块链示例完成 ===")
    
    # 刷新
    db.flush()


def demonstrate_consensus_simulation():
    """演示共识模拟"""
    print("\n=== 共识机制模拟 ===\n")
    
    # 创建多个节点（简化模拟）
    nodes = []
    for i in range(3):
        db = Database(data_dir=f"./data/node_{i}")
        nodes.append(db)
    
    # 节点1写入数据
    nodes[0].put(b"shared:data", b"value1")
    root1 = nodes[0].get_root_hash()
    print(f"节点1写入数据，Merkle根: {root1.hex()[:16]}...")
    
    # 同步到其他节点（简化：实际需要网络通信）
    # 这里只是演示概念
    print("同步Merkle根到其他节点...")
    for i in range(1, 3):
        # 实际应该通过网络同步
        print(f"  节点{i+1}收到Merkle根: {root1.hex()[:16]}...")
    
    print("\n所有节点达成共识（相同的Merkle根）")


if __name__ == "__main__":
    simulate_blockchain_transactions()
    demonstrate_consensus_simulation()

