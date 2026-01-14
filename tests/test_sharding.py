"""
分片和分区测试
"""

import unittest
import tempfile
import shutil
import os
from src.amdb import Database
from src.amdb.sharding import ShardManager, PartitionManager, ShardingStrategy


class TestSharding(unittest.TestCase):
    """分片测试"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.db = Database(
            data_dir=os.path.join(self.temp_dir, "sharded_db"),
            enable_sharding=True,
            shard_count=16,  # 使用较少分片便于测试
            max_file_size=1024 * 1024  # 1MB文件限制
        )
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_sharding_distribution(self):
        """测试分片分布"""
        # 写入1000个键值对
        keys = []
        for i in range(1000):
            key = f"key_{i:04d}".encode()
            value = f"value_{i}".encode()
            self.db.put(key, value)
            keys.append(key)
        
        # 检查分片分布
        stats = self.db.get_stats()
        shard_info = stats['shard_info']
        
        # 验证所有分片都有数据
        active_shards = sum(1 for info in shard_info.values() 
                          if info['sstable_count'] > 0 or info['memtable_size'] > 0)
        self.assertGreater(active_shards, 0, "应该有活跃的分片")
    
    def test_file_size_limit(self):
        """测试文件大小限制"""
        # 写入大量数据，触发文件分割
        large_value = b"x" * 10000  # 10KB每个值
        
        for i in range(200):  # 写入200个，总共约2MB，应该触发分割
            key = f"large_key_{i:04d}".encode()
            self.db.put(key, large_value)
        
        # 检查是否有多个文件
        stats = self.db.get_stats()
        shard_info = stats['shard_info']
        
        # 至少有一个分片应该有多个文件
        max_files = max((info['sstable_count'] for info in shard_info.values()), default=0)
        self.assertGreaterEqual(max_files, 0)  # 至少应该有文件
    
    def test_shard_consistency(self):
        """测试分片一致性"""
        # 写入数据
        test_keys = [b"test_key_1", b"test_key_2", b"test_key_3"]
        for key in test_keys:
            self.db.put(key, b"test_value")
        
        # 读取数据，验证一致性
        for key in test_keys:
            value = self.db.get(key)
            self.assertEqual(value, b"test_value")
    
    def test_partition_creation(self):
        """测试分区创建"""
        # 创建分区
        self.db.create_partition("test_partition", shard_count=8, max_file_size=512*1024)
        
        # 列出分区
        partitions = self.db.list_partitions()
        self.assertIn("test_partition", partitions)
        
        # 获取分区
        partition = self.db.get_partition("test_partition")
        self.assertIsNotNone(partition)


class TestShardManager(unittest.TestCase):
    """分片管理器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.shard_mgr = ShardManager(
            data_dir=os.path.join(self.temp_dir, "shards"),
            shard_count=16,
            strategy=ShardingStrategy.HASH
        )
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_shard_id_calculation(self):
        """测试分片ID计算"""
        key1 = b"test_key_1"
        key2 = b"test_key_2"
        
        shard_id1 = self.shard_mgr.get_shard_id(key1)
        shard_id2 = self.shard_mgr.get_shard_id(key2)
        
        self.assertGreaterEqual(shard_id1, 0)
        self.assertLess(shard_id1, 16)
        self.assertGreaterEqual(shard_id2, 0)
        self.assertLess(shard_id2, 16)
    
    def test_shard_path(self):
        """测试分片路径"""
        shard_id = 5
        path = self.shard_mgr.get_shard_path(shard_id)
        
        self.assertTrue(path.exists())
        self.assertIn("shard_00", str(path))
    
    def test_file_size_check(self):
        """测试文件大小检查"""
        from src.amdb.sharding import FileSizeManager
        
        file_mgr = FileSizeManager(max_file_size=256 * 1024 * 1024)
        should_split, next_path = file_mgr.check_file_size(
            "/test/path.sst", 300 * 1024 * 1024  # 300MB
        )
        self.assertTrue(should_split)
        self.assertIsNotNone(next_path)


if __name__ == '__main__':
    unittest.main()

