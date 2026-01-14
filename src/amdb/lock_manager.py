"""
锁管理模块
支持读写锁、死锁检测、超时机制
"""

import threading
import time
from typing import Dict, Set, Optional, Any
from collections import defaultdict
from enum import Enum


class LockType(Enum):
    """锁类型"""
    READ = "read"
    WRITE = "write"


class Lock:
    """锁对象"""
    
    def __init__(self, key: bytes, lock_type: LockType, timeout: Optional[float] = None):
        self.key = key
        self.lock_type = lock_type
        self.timeout = timeout
        self.acquired_at: Optional[float] = None
        self.thread_id = threading.get_ident()


class LockManager:
    """锁管理器"""
    
    def __init__(self, default_timeout: Optional[float] = None):
        """
        Args:
            default_timeout: 默认超时时间（秒）
        """
        self.default_timeout = default_timeout
        self.locks: Dict[bytes, threading.RLock] = {}
        self.read_locks: Dict[bytes, int] = defaultdict(int)  # 读锁计数
        self.write_locks: Dict[bytes, threading.Lock] = {}
        self.lock_holders: Dict[bytes, Set[int]] = defaultdict(set)  # 持有锁的线程
        self.lock_info: Dict[bytes, Lock] = {}  # 锁信息
        self.global_lock = threading.RLock()
        self.deadlock_check_interval = 5.0  # 死锁检测间隔
        self.last_deadlock_check = time.time()
    
    def acquire_read_lock(self, key: bytes, timeout: Optional[float] = None) -> bool:
        """获取读锁"""
        timeout = timeout or self.default_timeout
        start_time = time.time()
        
        with self.global_lock:
            # 检查是否已有写锁
            if key in self.write_locks:
                if timeout and (time.time() - start_time) > timeout:
                    return False
                # 等待写锁释放
                write_lock = self.write_locks[key]
                if not write_lock.acquire(timeout=timeout):
                    return False
                write_lock.release()
            
            # 增加读锁计数
            self.read_locks[key] += 1
            thread_id = threading.get_ident()
            self.lock_holders[key].add(thread_id)
            
            lock = Lock(key, LockType.READ, timeout)
            lock.acquired_at = time.time()
            self.lock_info[key] = lock
            
            return True
    
    def release_read_lock(self, key: bytes):
        """释放读锁"""
        with self.global_lock:
            if key in self.read_locks and self.read_locks[key] > 0:
                self.read_locks[key] -= 1
                if self.read_locks[key] == 0:
                    del self.read_locks[key]
                
                thread_id = threading.get_ident()
                self.lock_holders[key].discard(thread_id)
                
                if key in self.lock_info:
                    del self.lock_info[key]
    
    def acquire_write_lock(self, key: bytes, timeout: Optional[float] = None) -> bool:
        """获取写锁"""
        timeout = timeout or self.default_timeout
        start_time = time.time()
        
        with self.global_lock:
            # 检查是否已有读锁或写锁
            if key in self.read_locks or key in self.write_locks:
                if timeout and (time.time() - start_time) > timeout:
                    return False
                # 等待锁释放
                while (key in self.read_locks or key in self.write_locks):
                    if timeout and (time.time() - start_time) > timeout:
                        return False
                    time.sleep(0.01)  # 短暂等待
            
            # 创建写锁
            if key not in self.write_locks:
                self.write_locks[key] = threading.Lock()
            
            if self.write_locks[key].acquire(timeout=timeout):
                thread_id = threading.get_ident()
                self.lock_holders[key].add(thread_id)
                
                lock = Lock(key, LockType.WRITE, timeout)
                lock.acquired_at = time.time()
                self.lock_info[key] = lock
                
                return True
        
        return False
    
    def release_write_lock(self, key: bytes):
        """释放写锁"""
        with self.global_lock:
            if key in self.write_locks:
                thread_id = threading.get_ident()
                self.lock_holders[key].discard(thread_id)
                self.write_locks[key].release()
                del self.write_locks[key]
                
                if key in self.lock_info:
                    del self.lock_info[key]
    
    def check_deadlock(self) -> bool:
        """检查死锁（完整实现：检测循环等待）"""
        current_time = time.time()
        if current_time - self.last_deadlock_check < self.deadlock_check_interval:
            return False
        
        self.last_deadlock_check = current_time
        
        # 1. 检查超时锁
        for key, lock in list(self.lock_info.items()):
            if lock.timeout and lock.acquired_at:
                if (current_time - lock.acquired_at) > lock.timeout:
                    # 超时，释放锁
                    if lock.lock_type == LockType.READ:
                        self.release_read_lock(key)
                    else:
                        self.release_write_lock(key)
                    return True
        
        # 2. 检测循环等待（死锁检测）
        # 构建等待图：thread -> [等待的keys]
        wait_graph: Dict[int, Set[bytes]] = {}
        lock_holders: Dict[bytes, int] = {}  # key -> thread_id
        
        with self.global_lock:
            # 收集当前锁持有者
            for key, lock in self.lock_info.items():
                lock_holders[key] = lock.thread_id
            
            # 检查其他线程是否在等待这些锁
            for key, holders in self.lock_holders.items():
                if key in lock_holders:
                    holder_thread = lock_holders[key]
                    for waiting_thread in holders:
                        if waiting_thread != holder_thread:
                            if waiting_thread not in wait_graph:
                                wait_graph[waiting_thread] = set()
                            wait_graph[waiting_thread].add(key)
        
        # 3. 检测循环（DFS）
        def has_cycle(thread_id: int, visited: Set[int], rec_stack: Set[int]) -> bool:
            visited.add(thread_id)
            rec_stack.add(thread_id)
            
            if thread_id in wait_graph:
                for key in wait_graph[thread_id]:
                    if key in lock_holders:
                        holder = lock_holders[key]
                        if holder not in visited:
                            if has_cycle(holder, visited, rec_stack):
                                return True
                        elif holder in rec_stack:
                            return True
            
            rec_stack.remove(thread_id)
            return False
        
        # 检查所有线程
        visited = set()
        for thread_id in wait_graph.keys():
            if thread_id not in visited:
                if has_cycle(thread_id, visited, set()):
                    # 发现死锁，释放其中一个锁
                    if thread_id in wait_graph and wait_graph[thread_id]:
                        deadlock_key = next(iter(wait_graph[thread_id]))
                        if deadlock_key in self.lock_info:
                            lock = self.lock_info[deadlock_key]
                            if lock.lock_type == LockType.READ:
                                self.release_read_lock(deadlock_key)
                            else:
                                self.release_write_lock(deadlock_key)
                        return True
        
        return False
    
    def get_lock_info(self) -> Dict[bytes, Dict[str, Any]]:
        """获取锁信息"""
        with self.global_lock:
            return {
                key: {
                    'type': lock.lock_type.value,
                    'thread_id': lock.thread_id,
                    'acquired_at': lock.acquired_at,
                    'timeout': lock.timeout
                }
                for key, lock in self.lock_info.items()
            }

