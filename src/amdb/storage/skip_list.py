"""
跳表实现（Skip List）
对标LevelDB的MemTable数据结构，提供O(log n)的插入和查找性能
优化：减少锁竞争，提升并发性能
"""

import random
import time
import threading
from typing import Optional, Tuple, Iterator, List


class SkipListNode:
    """跳表节点"""
    
    def __init__(self, key: bytes, value: bytes, version: int, timestamp: float, max_level: int):
        self.key = key
        self.value = value
        self.version = version
        self.timestamp = timestamp
        self.forward = [None] * max_level  # 前向指针数组
        self.level = 0  # 节点层级


class SkipList:
    """
    跳表实现（高性能版本，对标LevelDB）
    提供O(log n)的插入和查找性能
    """
    
    def __init__(self, max_size: int = 10 * 1024 * 1024, max_level: int = None):
        self.max_size = max_size
        self.size = 0
        self.max_level = max_level if max_level is not None else 16  # 最大层级（可从配置读取）
        self.level = 1  # 当前层级
        
        # 创建头节点（哨兵节点）
        self.header = SkipListNode(b'', b'', 0, 0.0, self.max_level)
        
        # 用于插入时的路径记录
        self.update = [None] * self.max_level
        
        # 使用读写锁（减少锁竞争，提升并发性能）
        from .rw_lock import ReadWriteLock
        self.rw_lock = ReadWriteLock()
    
    def _random_level(self) -> int:
        """随机生成节点层级（对标LevelDB）"""
        level = 1
        while random.random() < 0.5 and level < self.max_level:
            level += 1
        return level
    
    def put(self, key: bytes, value: bytes, version: int, timestamp: float) -> bool:
        """
        插入数据（O(log n)，使用写锁）
        返回是否成功
        """
        # 使用写锁
        self.rw_lock.acquire_write()
        try:
            # 计算大小
            key_len = len(key)
            value_len = len(value)
            entry_size = key_len + value_len + 16
            
            if self.size + entry_size > self.max_size:
                return False  # 空间不足
            
            # 查找插入位置
            current = self.header
            for i in range(self.level - 1, -1, -1):
                while current.forward[i] and current.forward[i].key < key:
                    current = current.forward[i]
                self.update[i] = current
            
            current = current.forward[0]
            
            # 如果key已存在，更新值
            if current and current.key == key:
                old_size = len(current.value) + 16
                new_size = value_len + 16
                self.size = self.size - old_size + new_size
                current.value = value
                current.version = version
                current.timestamp = timestamp
                return True
            
            # 创建新节点
            node_level = self._random_level()
            new_node = SkipListNode(key, value, version, timestamp, self.max_level)
            new_node.level = node_level
            
            # 如果新节点层级超过当前层级，扩展
            if node_level > self.level:
                for i in range(self.level, node_level):
                    self.update[i] = self.header
                self.level = node_level
            
            # 插入节点
            for i in range(node_level):
                new_node.forward[i] = self.update[i].forward[i]
                self.update[i].forward[i] = new_node
            
            self.size += entry_size
            return True
        finally:
            self.rw_lock.release_write()
    
    def put_batch(self, items: List[Tuple[bytes, bytes, int]]) -> int:
        """
        批量插入（简化稳定版本）
        优化：一次写锁，逐个处理
        稳定性：简化逻辑，避免复杂优化导致崩溃
        返回成功插入的数量
        """
        if not items:
            return 0
        
        timestamp = time.time()
        success_count = 0
        
        # 使用写锁（批量操作一次锁）
        self.rw_lock.acquire_write()
        try:
            # 简化：逐个处理，避免预计算导致的问题
            for key, value, version in items:
                # 计算大小
                key_len = len(key)
                value_len = len(value)
                entry_size = key_len + value_len + 16
                
                if self.size + entry_size > self.max_size:
                    break  # 空间不足
                
                # 查找插入位置
                # 稳定性：添加边界检查，避免访问无效指针
                current = self.header
                if current is None:
                    break
                
                # 确保update数组足够大
                if len(self.update) < self.level:
                    self.update.extend([None] * (self.level - len(self.update)))
                
                for i in range(self.level - 1, -1, -1):
                    if i >= len(current.forward):
                        break
                    while current.forward[i] is not None and current.forward[i].key < key:
                        current = current.forward[i]
                        if current is None or i >= len(current.forward):
                            break
                    if i < len(self.update):
                        self.update[i] = current
                
                if current is None or len(current.forward) == 0:
                    break
                current = current.forward[0]
                
                # 如果key已存在，更新值
                if current and current.key == key:
                    old_size = len(current.value) + 16
                    new_size = value_len + 16
                    self.size = self.size - old_size + new_size
                    current.value = value
                    current.version = version
                    current.timestamp = timestamp
                    success_count += 1
                    continue
                
                # 创建新节点（简化：使用随机层级）
                node_level = self._random_level()
                new_node = SkipListNode(key, value, version, timestamp, self.max_level)
                new_node.level = node_level
                
                # 如果新节点层级超过当前层级，扩展
                if node_level > self.level:
                    # 确保update数组足够大
                    while len(self.update) < node_level:
                        self.update.append(self.header)
                    for i in range(self.level, node_level):
                        self.update[i] = self.header
                    self.level = node_level
                
                # 插入节点
                # 稳定性：添加边界检查，避免访问无效指针
                for i in range(node_level):
                    if i >= len(self.update) or self.update[i] is None:
                        break
                    if i >= len(self.update[i].forward):
                        break
                    if i >= len(new_node.forward):
                        break
                    new_node.forward[i] = self.update[i].forward[i]
                    self.update[i].forward[i] = new_node
                
                self.size += entry_size
                success_count += 1
            
        except Exception as e:
            import traceback
            print(f"SkipList put_batch失败: {e}")
            traceback.print_exc()
        finally:
            # 确保释放锁
            try:
                self.rw_lock.release_write()
            except:
                pass
        
        return success_count
    
    def get(self, key: bytes) -> Optional[Tuple[bytes, int]]:
        """
        查找数据（O(log n)，使用读锁，允许多个读并发）
        返回(value, version)或None
        """
        # 使用读锁（允许多个读操作并发）
        self.rw_lock.acquire_read()
        try:
            current = self.header
            
            # 从最高层开始查找
            for i in range(self.level - 1, -1, -1):
                while current.forward[i] and current.forward[i].key < key:
                    current = current.forward[i]
            
            current = current.forward[0]
            if current and current.key == key:
                return (current.value, current.version)
            return None
        finally:
            self.rw_lock.release_read()
    
    def get_all(self) -> Iterator[Tuple[bytes, bytes, int]]:
        """获取所有数据（按key顺序，使用读锁）"""
        self.rw_lock.acquire_read()
        try:
            current = self.header.forward[0]
            items = []
            while current:
                items.append((current.key, current.value, current.version))
                current = current.forward[0]
            # 先收集所有数据，再释放锁
            for item in items:
                yield item
        finally:
            self.rw_lock.release_read()
    
    def clear(self):
        """清空跳表（使用写锁）"""
        self.rw_lock.acquire_write()
        try:
            self.size = 0
            self.level = 1
            self.header = SkipListNode(b'', b'', 0, 0.0, self.max_level)
            self.update = [None] * self.max_level
        finally:
            self.rw_lock.release_write()
