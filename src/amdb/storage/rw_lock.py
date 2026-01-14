"""
读写锁实现（Read-Write Lock）
减少锁竞争，提升并发性能（对标LevelDB）
"""

import threading
from collections import deque


class ReadWriteLock:
    """
    读写锁（高性能版本）
    允许多个读操作并发，写操作独占
    """
    
    def __init__(self):
        self._read_ready = threading.Condition(threading.RLock())
        self._readers = 0
    
    def acquire_read(self):
        """获取读锁"""
        self._read_ready.acquire()
        try:
            self._readers += 1
        finally:
            self._read_ready.release()
    
    def release_read(self):
        """释放读锁"""
        self._read_ready.acquire()
        try:
            self._readers -= 1
            if self._readers == 0:
                self._read_ready.notify_all()  # 修复：使用notify_all()替代已弃用的notifyAll()
        finally:
            self._read_ready.release()
    
    def acquire_write(self):
        """获取写锁"""
        self._read_ready.acquire()
        while self._readers > 0:
            self._read_ready.wait()
    
    def release_write(self):
        """释放写锁"""
        self._read_ready.notify_all()  # 修复：使用notify_all()替代已弃用的notifyAll()
        self._read_ready.release()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class ReadLockContext:
    """读锁上下文管理器"""
    
    def __init__(self, rw_lock: ReadWriteLock):
        self.rw_lock = rw_lock
    
    def __enter__(self):
        self.rw_lock.acquire_read()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.rw_lock.release_read()


class WriteLockContext:
    """写锁上下文管理器"""
    
    def __init__(self, rw_lock: ReadWriteLock):
        self.rw_lock = rw_lock
    
    def __enter__(self):
        self.rw_lock.acquire_write()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.rw_lock.release_write()

