"""
大数据量使用示例
演示如何处理千万级甚至上亿级数据
"""

from src.amdb import Database
import time
import random


def simulate_large_dataset():
    """模拟大数据量场景"""
    print("=== 大数据量场景示例 ===\n")
    
    # 创建支持大数据的数据库配置
    db = Database(
        data_dir="./data/bigdata",
        enable_sharding=True,  # 启用分片
        shard_count=1024,  # 1024个分片，适合千万级数据
        max_file_size=128 * 1024 * 1024  # 128MB文件限制
    )
    
    print("1. 批量写入1000万条数据...")
    start_time = time.time()
    
    batch_size = 10000
    total_records = 10000000
    
    for batch_start in range(0, total_records, batch_size):
        items = []
        for i in range(batch_start, min(batch_start + batch_size, total_records)):
            key = f"user_{i:08d}".encode()
            value = f"data_{i}_{random.randint(1000, 9999)}".encode()
            items.append((key, value))
        
        db.batch_put(items)
        
        if (batch_start + batch_size) % 100000 == 0:
            elapsed = time.time() - start_time
            progress = (batch_start + batch_size) / total_records * 100
            print(f"   进度: {progress:.1f}% ({batch_start + batch_size:,} 条), "
                  f"耗时: {elapsed:.2f}秒, "
                  f"速度: {(batch_start + batch_size) / elapsed:.0f} 条/秒")
    
    elapsed = time.time() - start_time
    print(f"   完成！总耗时: {elapsed:.2f}秒")
    print(f"   平均速度: {total_records / elapsed:.0f} 条/秒\n")
    
    # 查看分片统计
    print("2. 分片统计信息...")
    stats = db.get_stats()
    print(f"   总键数: {stats['total_keys']:,}")
    print(f"   分片数量: {stats['shard_count']}")
    print(f"   分片启用: {stats['sharding_enabled']}")
    
    # 显示部分分片信息
    shard_info = stats['shard_info']
    sample_shards = list(shard_info.items())[:5]
    print(f"\n   示例分片信息（前5个）:")
    for shard_id, info in sample_shards:
        total_size_mb = info['stats'].get('total_size', 0) / 1024 / 1024
        print(f"     分片 {shard_id}: {info['sstable_count']} 个文件, "
              f"{total_size_mb:.2f} MB")
    
    # 随机读取测试
    print("\n3. 随机读取性能测试...")
    read_count = 1000
    start_time = time.time()
    
    for _ in range(read_count):
        random_key = f"user_{random.randint(0, total_records-1):08d}".encode()
        value = db.get(random_key)
    
    elapsed = time.time() - start_time
    print(f"   读取 {read_count} 次，耗时: {elapsed:.2f}秒")
    print(f"   平均读取速度: {read_count / elapsed:.0f} 次/秒")
    
    # 范围查询测试
    print("\n4. 范围查询测试...")
    start_key = b"user_00001000"
    end_key = b"user_00002000"
    
    start_time = time.time()
    results = db.range_query(start_key, end_key)
    elapsed = time.time() - start_time
    
    print(f"   范围查询结果: {len(results)} 条")
    print(f"   查询耗时: {elapsed:.2f}秒")
    
    db.flush()
    print("\n=== 大数据量示例完成 ===")


def demonstrate_partitioning():
    """演示分区管理（分表分库）"""
    print("\n=== 分区管理示例 ===\n")
    
    db = Database(
        data_dir="./data/partitioned",
        enable_sharding=True,
        shard_count=256
    )
    
    # 创建不同业务的分区
    print("1. 创建业务分区...")
    db.create_partition("users", shard_count=128, max_file_size=128*1024*1024)
    db.create_partition("orders", shard_count=256, max_file_size=256*1024*1024)
    db.create_partition("products", shard_count=64, max_file_size=64*1024*1024)
    
    partitions = db.list_partitions()
    print(f"   已创建分区: {partitions}")
    
    # 在不同分区写入数据
    print("\n2. 在不同分区写入数据...")
    
    # 用户分区
    user_partition = db.get_partition("users")
    if user_partition:
        print("   写入用户数据...")
        for i in range(1000):
            key = f"user_{i}".encode()
            value = f"user_data_{i}".encode()
            # 这里需要通过分区写入，简化示例
            pass
    
    print("\n=== 分区管理示例完成 ===")


if __name__ == "__main__":
    # 大数据量示例
    simulate_large_dataset()
    
    # 分区管理示例
    demonstrate_partitioning()

