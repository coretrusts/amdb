"""
缓存管理测试
"""

import unittest
import time
from src.amdb.cache import CacheManager, CachePolicy


class TestCache(unittest.TestCase):
    """缓存测试"""
    
    def test_lru_cache(self):
        """测试LRU缓存"""
        cache = CacheManager(CachePolicy.LRU, max_size=3)
        
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")
        
        self.assertEqual(cache.get("key1"), "value1")
        
        # 添加新项，应该移除key2（最久未使用）
        cache.put("key4", "value4")
        self.assertIsNone(cache.get("key2"))
        self.assertIsNotNone(cache.get("key1"))
    
    def test_cache_ttl(self):
        """测试缓存TTL"""
        cache = CacheManager(CachePolicy.LRU, max_size=10, ttl=1)
        
        cache.put("key1", "value1")
        self.assertEqual(cache.get("key1"), "value1")
        
        time.sleep(1.1)
        self.assertIsNone(cache.get("key1"))
    
    def test_get_or_compute(self):
        """测试获取或计算"""
        cache = CacheManager(CachePolicy.LRU, max_size=10)
        
        call_count = [0]
        def compute():
            call_count[0] += 1
            return f"computed_{call_count[0]}"
        
        # 第一次应该计算
        value1 = cache.get_or_compute("key1", compute)
        self.assertEqual(value1, "computed_1")
        self.assertEqual(call_count[0], 1)
        
        # 第二次应该从缓存获取
        value2 = cache.get_or_compute("key1", compute)
        self.assertEqual(value2, "computed_1")
        self.assertEqual(call_count[0], 1)  # 没有再次调用

