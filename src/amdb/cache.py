"""
缓存管理模块
支持LRU、LFU、FIFO等缓存策略
"""

import time
import threading
from typing import Optional, Dict, Any, Callable
from collections import OrderedDict
from enum import Enum


class CachePolicy(Enum):
    """缓存策略"""
    LRU = "lru"  # 最近最少使用
    LFU = "lfu"  # 最不经常使用
    FIFO = "fifo"  # 先进先出


class LRUCache:
    """LRU缓存实现"""
    
    def __init__(self, max_size: int = 1000, ttl: Optional[int] = None):
        """
        Args:
            max_size: 最大缓存项数
            ttl: 过期时间（秒），None表示不过期
        """
        self.max_size = max_size
        self.ttl = ttl
        self.cache: OrderedDict = OrderedDict()
        self.timestamps: Dict[Any, float] = {}
        self.lock = threading.RLock()
    
    def get(self, key: Any) -> Optional[Any]:
        """获取值"""
        with self.lock:
            if key not in self.cache:
                return None
            
            # 检查过期
            if self.ttl and key in self.timestamps:
                if time.time() - self.timestamps[key] > self.ttl:
                    del self.cache[key]
                    del self.timestamps[key]
                    return None
            
            # 移到末尾（最近使用）
            value = self.cache.pop(key)
            self.cache[key] = value
            return value
    
    def put(self, key: Any, value: Any):
        """放入值"""
        with self.lock:
            if key in self.cache:
                # 更新现有项
                self.cache.pop(key)
            elif len(self.cache) >= self.max_size:
                # 移除最旧的项
                self.cache.popitem(last=False)
            
            self.cache[key] = value
            if self.ttl:
                self.timestamps[key] = time.time()
    
    def delete(self, key: Any):
        """删除项"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
            if key in self.timestamps:
                del self.timestamps[key]
    
    def clear(self):
        """清空缓存"""
        with self.lock:
            self.cache.clear()
            self.timestamps.clear()
    
    def size(self) -> int:
        """获取缓存大小"""
        return len(self.cache)


class LFUCache:
    """LFU缓存实现"""
    
    def __init__(self, max_size: int = 1000, ttl: Optional[int] = None):
        self.max_size = max_size
        self.ttl = ttl
        self.cache: Dict[Any, Any] = {}
        self.frequencies: Dict[Any, int] = {}
        self.timestamps: Dict[Any, float] = {}
        self.lock = threading.RLock()
    
    def get(self, key: Any) -> Optional[Any]:
        """获取值"""
        with self.lock:
            if key not in self.cache:
                return None
            
            # 检查过期
            if self.ttl and key in self.timestamps:
                if time.time() - self.timestamps[key] > self.ttl:
                    del self.cache[key]
                    del self.frequencies[key]
                    del self.timestamps[key]
                    return None
            
            # 增加频率
            self.frequencies[key] = self.frequencies.get(key, 0) + 1
            return self.cache[key]
    
    def put(self, key: Any, value: Any):
        """放入值"""
        with self.lock:
            if len(self.cache) >= self.max_size and key not in self.cache:
                # 移除频率最低的项
                if self.frequencies:
                    min_freq_key = min(self.frequencies.items(), key=lambda x: x[1])[0]
                    del self.cache[min_freq_key]
                    del self.frequencies[min_freq_key]
                    if min_freq_key in self.timestamps:
                        del self.timestamps[min_freq_key]
            
            self.cache[key] = value
            self.frequencies[key] = self.frequencies.get(key, 0) + 1
            if self.ttl:
                self.timestamps[key] = time.time()
    
    def delete(self, key: Any):
        """删除项"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
            if key in self.frequencies:
                del self.frequencies[key]
            if key in self.timestamps:
                del self.timestamps[key]
    
    def clear(self):
        """清空缓存"""
        with self.lock:
            self.cache.clear()
            self.frequencies.clear()
            self.timestamps.clear()
    
    def size(self) -> int:
        """获取缓存大小"""
        return len(self.cache)


class FIFOCache:
    """FIFO缓存实现"""
    
    def __init__(self, max_size: int = 1000, ttl: Optional[int] = None):
        self.max_size = max_size
        self.ttl = ttl
        self.cache: OrderedDict = OrderedDict()
        self.timestamps: Dict[Any, float] = {}
        self.lock = threading.RLock()
    
    def get(self, key: Any) -> Optional[Any]:
        """获取值"""
        with self.lock:
            if key not in self.cache:
                return None
            
            # 检查过期
            if self.ttl and key in self.timestamps:
                if time.time() - self.timestamps[key] > self.ttl:
                    del self.cache[key]
                    del self.timestamps[key]
                    return None
            
            return self.cache[key]
    
    def put(self, key: Any, value: Any):
        """放入值（FIFO：先进先出）"""
        with self.lock:
            if key in self.cache:
                # 更新现有项（不改变顺序）
                self.cache[key] = value
            elif len(self.cache) >= self.max_size:
                # 移除最旧的项（FIFO）
                self.cache.popitem(last=False)
                if self.cache:
                    oldest_key = next(iter(self.cache))
                    if oldest_key in self.timestamps:
                        del self.timestamps[oldest_key]
            
            self.cache[key] = value
            if self.ttl:
                self.timestamps[key] = time.time()
    
    def delete(self, key: Any):
        """删除项"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
            if key in self.timestamps:
                del self.timestamps[key]
    
    def clear(self):
        """清空缓存"""
        with self.lock:
            self.cache.clear()
            self.timestamps.clear()
    
    def size(self) -> int:
        """获取缓存大小"""
        return len(self.cache)


class CacheManager:
    """缓存管理器"""
    
    def __init__(self, policy: CachePolicy = CachePolicy.LRU, 
                 max_size: int = 1000, ttl: Optional[int] = None):
        """
        Args:
            policy: 缓存策略
            max_size: 最大缓存项数
            ttl: 过期时间（秒）
        """
        if policy == CachePolicy.LRU:
            self.cache = LRUCache(max_size, ttl)
        elif policy == CachePolicy.LFU:
            self.cache = LFUCache(max_size, ttl)
        else:  # FIFO
            self.cache = FIFOCache(max_size, ttl)
    
    def get(self, key: Any) -> Optional[Any]:
        """获取值"""
        return self.cache.get(key)
    
    def put(self, key: Any, value: Any):
        """放入值"""
        self.cache.put(key, value)
    
    def delete(self, key: Any):
        """删除项"""
        self.cache.delete(key)
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()
    
    def size(self) -> int:
        """获取缓存大小"""
        return self.cache.size()
    
    def get_or_compute(self, key: Any, compute_fn: Callable[[], Any]) -> Any:
        """获取或计算值"""
        value = self.get(key)
        if value is None:
            value = compute_fn()
            self.put(key, value)
        return value

