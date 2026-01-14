"""
基本功能测试
"""

import unittest
import os
import tempfile
import shutil
from src.amdb import Database


class TestDatabaseBasic(unittest.TestCase):
    """基本功能测试"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.db = Database(data_dir=os.path.join(self.temp_dir, "test_db"))
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_put_get(self):
        """测试写入和读取"""
        key = b"test_key"
        value = b"test_value"
        
        success, root_hash = self.db.put(key, value)
        self.assertTrue(success)
        self.assertIsNotNone(root_hash)
        
        retrieved = self.db.get(key)
        self.assertEqual(retrieved, value)
    
    def test_update_version(self):
        """测试版本更新"""
        key = b"version_test"
        value1 = b"value1"
        value2 = b"value2"
        
        self.db.put(key, value1)
        v1 = self.db.get(key, version=1)
        self.assertEqual(v1, value1)
        
        self.db.put(key, value2)
        v2 = self.db.get(key, version=2)
        self.assertEqual(v2, value2)
        
        # 最新版本应该是value2
        latest = self.db.get(key)
        self.assertEqual(latest, value2)
    
    def test_history(self):
        """测试版本历史"""
        key = b"history_test"
        
        for i in range(5):
            self.db.put(key, f"value_{i}".encode())
        
        history = self.db.get_history(key)
        self.assertEqual(len(history), 5)
        
        # 检查版本号递增
        for i, h in enumerate(history, 1):
            self.assertEqual(h['version'], i)
    
    def test_merkle_proof(self):
        """测试Merkle证明"""
        key = b"merkle_test"
        value = b"merkle_value"
        
        self.db.put(key, value)
        retrieved_value, proof, root = self.db.get_with_proof(key)
        
        self.assertEqual(retrieved_value, value)
        self.assertIsNotNone(root)
        
        # 验证证明
        is_valid = self.db.verify(key, retrieved_value, proof)
        self.assertTrue(is_valid)
    
    def test_batch_put(self):
        """测试批量写入"""
        items = [
            (b"key1", b"value1"),
            (b"key2", b"value2"),
            (b"key3", b"value3"),
        ]
        
        success, root_hash = self.db.batch_put(items)
        self.assertTrue(success)
        
        for key, value in items:
            self.assertEqual(self.db.get(key), value)
    
    def test_range_query(self):
        """测试范围查询"""
        # 插入有序键
        for i in range(10):
            self.db.put(f"key_{i:03d}".encode(), f"value_{i}".encode())
        
        results = self.db.range_query(b"key_003", b"key_007")
        self.assertGreater(len(results), 0)
        
        # 检查结果在范围内
        for key, value in results:
            self.assertGreaterEqual(key, b"key_003")
            self.assertLessEqual(key, b"key_007")
    
    def test_transaction(self):
        """测试事务"""
        tx = self.db.begin_transaction()
        self.assertIsNotNone(tx)
        
        tx.put(b"tx_key1", b"tx_value1")
        tx.put(b"tx_key2", b"tx_value2")
        
        # 提交前应该读不到
        self.assertIsNone(self.db.get(b"tx_key1"))
        
        # 提交事务
        success = self.db.commit_transaction(tx)
        self.assertTrue(success)
        
        # 提交后应该能读到
        self.assertEqual(self.db.get(b"tx_key1"), b"tx_value1")
        self.assertEqual(self.db.get(b"tx_key2"), b"tx_value2")
    
    def test_index(self):
        """测试二级索引"""
        self.db.create_index("category")
        
        self.db.put(b"item1", b"value1")
        self.db.update_index("category", "electronics", b"item1")
        
        self.db.put(b"item2", b"value2")
        self.db.update_index("category", "electronics", b"item2")
        
        results = self.db.query_index("category", "electronics")
        self.assertEqual(len(results), 2)
        self.assertIn(b"item1", results)
        self.assertIn(b"item2", results)
    
    def test_stats(self):
        """测试统计信息"""
        for i in range(10):
            self.db.put(f"key_{i}".encode(), f"value_{i}".encode())
        
        stats = self.db.get_stats()
        self.assertEqual(stats['total_keys'], 10)
        self.assertIn('merkle_root', stats)


if __name__ == '__main__':
    unittest.main()

