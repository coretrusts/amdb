"""
AmDb 基本使用示例
演示数据库的基本操作
"""

from src.amdb import Database


def main():
    # 创建数据库实例
    db = Database(data_dir="./data/example")
    
    print("=== AmDb 基本使用示例 ===\n")
    
    # 1. 写入数据
    print("1. 写入数据...")
    key1 = b"account:alice"
    value1 = b"balance:100"
    success, root_hash = db.put(key1, value1)
    print(f"   写入成功: {success}, Merkle根哈希: {root_hash.hex()[:16]}...")
    
    key2 = b"account:bob"
    value2 = b"balance:200"
    db.put(key2, value2)
    print(f"   写入账户Bob")
    
    # 2. 读取数据
    print("\n2. 读取数据...")
    value = db.get(key1)
    print(f"   {key1.decode()}: {value.decode()}")
    
    # 3. 更新数据（创建新版本）
    print("\n3. 更新数据（创建新版本）...")
    value1_new = b"balance:150"
    db.put(key1, value1_new)
    print(f"   更新账户Alice余额为150")
    
    # 4. 读取历史版本
    print("\n4. 读取历史版本...")
    history = db.get_history(key1)
    print(f"   账户Alice的版本历史:")
    for h in history:
        print(f"     版本 {h['version']}: {h['value'].decode()} (时间: {h['timestamp']:.2f})")
    
    # 5. 读取指定版本
    print("\n5. 读取指定版本...")
    old_value = db.get(key1, version=1)
    print(f"   版本1的值: {old_value.decode()}")
    current_value = db.get(key1)
    print(f"   当前版本的值: {current_value.decode()}")
    
    # 6. 获取Merkle证明
    print("\n6. 获取Merkle证明...")
    value, proof, root = db.get_with_proof(key1)
    print(f"   值: {value.decode()}")
    print(f"   证明长度: {len(proof)}")
    print(f"   根哈希: {root.hex()[:16]}...")
    
    # 7. 验证数据
    print("\n7. 验证数据完整性...")
    is_valid = db.verify(key1, value, proof)
    print(f"   验证结果: {is_valid}")
    
    # 8. 批量写入
    print("\n8. 批量写入...")
    items = [
        (b"account:charlie", b"balance:300"),
        (b"account:david", b"balance:400"),
    ]
    success, root_hash = db.batch_put(items)
    print(f"   批量写入成功: {success}")
    
    # 9. 范围查询
    print("\n9. 范围查询...")
    results = db.range_query(b"account:alice", b"account:charlie")
    print(f"   查询结果数量: {len(results)}")
    for key, val in results:
        print(f"   {key.decode()}: {val.decode()}")
    
    # 10. 统计信息
    print("\n10. 数据库统计信息...")
    stats = db.get_stats()
    print(f"   总键数: {stats['total_keys']}")
    print(f"   当前版本: {stats['current_version']}")
    print(f"   Merkle根: {stats['merkle_root'][:16]}...")
    
    # 11. 事务示例
    print("\n11. 事务示例...")
    tx = db.begin_transaction()
    print(f"   开始事务: {tx.tx_id}")
    tx.put(b"account:eve", b"balance:500")
    tx.put(b"account:frank", b"balance:600")
    success = db.commit_transaction(tx)
    print(f"   提交事务: {success}")
    
    # 12. 二级索引示例
    print("\n12. 二级索引示例...")
    db.create_index("balance_range")
    db.update_index("balance_range", "high", key1)  # balance > 100
    db.update_index("balance_range", "high", key2)
    results = db.query_index("balance_range", "high")
    print(f"   高余额账户数量: {len(results)}")
    
    print("\n=== 示例完成 ===")
    
    # 刷新到磁盘
    db.flush()


if __name__ == "__main__":
    main()

