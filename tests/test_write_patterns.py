"""
写入模式性能测试
区分顺序写入和随机写入的性能
"""

import unittest
import tempfile
import shutil
import time
import random
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.amdb import Database


class WritePatternTest(unittest.TestCase):
    """写入模式测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.db = Database(data_dir=self.temp_dir, enable_sharding=True, shard_count=256)
    
    def tearDown(self):
        """清理测试环境"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_sequential_write(self):
        """
        测试顺序写入性能
        顺序写入：key按顺序生成（如key_0, key_1, key_2...）
        特点：对LSM树友好，可以利用批量写入和预分配的优势
        """
        print("\n" + "=" * 80)
        print("顺序写入性能测试")
        print("=" * 80)
        
        test_sizes = [1000, 10000, 50000, 100000]
        best_throughput = 0
        
        for size in test_sizes:
            # 顺序生成key（顺序写入）
            items = [(f'seq_key_{i:010d}'.encode(), f'seq_value_{i}'.encode()) 
                     for i in range(size)]
            
            start = time.time()
            self.db.batch_put(items)
            elapsed = time.time() - start
            throughput = size / elapsed if elapsed > 0 else 0
            best_throughput = max(best_throughput, throughput)
            
            print(f'  {size:6,} 条: {elapsed:.3f}秒, {throughput:10,.0f} 条/秒')
        
        print(f'\n顺序写入最佳性能: {best_throughput:,.0f} 条/秒')
        print('LevelDB参考: 顺序写入 55万/秒')
        
        return best_throughput
    
    def test_random_write(self):
        """
        测试随机写入性能
        随机写入：key随机生成或随机顺序
        特点：对LSM树不友好，需要更多的查找和插入操作
        """
        print("\n" + "=" * 80)
        print("随机写入性能测试")
        print("=" * 80)
        
        test_sizes = [1000, 10000, 50000, 100000]
        best_throughput = 0
        
        for size in test_sizes:
            # 方法1：随机key（完全随机）
            # 生成随机key
            random_keys = [f'rand_key_{random.randint(0, 2**32):010d}'.encode() 
                          for _ in range(size)]
            items = [(key, f'rand_value_{i}'.encode()) 
                     for i, key in enumerate(random_keys)]
            
            # 打乱顺序（增加随机性）
            random.shuffle(items)
            
            start = time.time()
            self.db.batch_put(items)
            elapsed = time.time() - start
            throughput = size / elapsed if elapsed > 0 else 0
            best_throughput = max(best_throughput, throughput)
            
            print(f'  {size:6,} 条: {elapsed:.3f}秒, {throughput:10,.0f} 条/秒')
        
        print(f'\n随机写入最佳性能: {best_throughput:,.0f} 条/秒')
        print('LevelDB参考: 随机写入 5.2万/秒')
        
        return best_throughput
    
    def test_mixed_write(self):
        """
        测试混合写入性能
        混合写入：部分顺序，部分随机
        """
        print("\n" + "=" * 80)
        print("混合写入性能测试（50%顺序 + 50%随机）")
        print("=" * 80)
        
        test_sizes = [1000, 10000, 50000, 100000]
        best_throughput = 0
        
        for size in test_sizes:
            items = []
            
            # 50%顺序写入
            seq_count = size // 2
            for i in range(seq_count):
                items.append((f'seq_key_{i:010d}'.encode(), f'seq_value_{i}'.encode()))
            
            # 50%随机写入
            rand_count = size - seq_count
            for i in range(rand_count):
                key = f'rand_key_{random.randint(0, 2**32):010d}'.encode()
                items.append((key, f'rand_value_{i}'.encode()))
            
            # 打乱顺序
            random.shuffle(items)
            
            start = time.time()
            self.db.batch_put(items)
            elapsed = time.time() - start
            throughput = size / elapsed if elapsed > 0 else 0
            best_throughput = max(best_throughput, throughput)
            
            print(f'  {size:6,} 条: {elapsed:.3f}秒, {throughput:10,.0f} 条/秒')
        
        print(f'\n混合写入最佳性能: {best_throughput:,.0f} 条/秒')
        
        return best_throughput
    
    def test_write_pattern_comparison(self):
        """对比不同写入模式的性能"""
        print("\n" + "=" * 80)
        print("写入模式性能对比")
        print("=" * 80)
        
        # 测试顺序写入
        seq_throughput = self.test_sequential_write()
        
        # 重新初始化数据库（避免缓存影响）
        self.tearDown()
        self.setUp()
        
        # 测试随机写入
        rand_throughput = self.test_random_write()
        
        # 重新初始化数据库
        self.tearDown()
        self.setUp()
        
        # 测试混合写入
        mixed_throughput = self.test_mixed_write()
        
        # 性能对比
        print("\n" + "=" * 80)
        print("性能对比总结")
        print("=" * 80)
        print(f"顺序写入: {seq_throughput:,.0f} 条/秒")
        print(f"随机写入: {rand_throughput:,.0f} 条/秒")
        print(f"混合写入: {mixed_throughput:,.0f} 条/秒")
        
        if seq_throughput > 0:
            ratio = rand_throughput / seq_throughput
            print(f"\n随机/顺序性能比: {ratio:.2f}")
            print("（通常顺序写入性能更好，因为可以利用批量写入和预分配）")
        
        print("\nLevelDB参考性能:")
        print("  - 顺序写入: 55万/秒")
        print("  - 随机写入: 5.2万/秒")
        print("  - 性能比: 约10.6倍（顺序写入明显优于随机写入）")


if __name__ == '__main__':
    unittest.main(verbosity=2)

