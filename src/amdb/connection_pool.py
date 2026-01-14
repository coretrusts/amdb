"""
连接池管理模块
管理数据库连接，支持连接复用和负载均衡
"""

import threading
import time
import queue
from typing import Optional, List, Dict
from dataclasses import dataclass
from contextlib import contextmanager
from .database import Database


@dataclass
class Connection:
    """连接对象"""
    db: Database
    created_at: float
    last_used: float
    in_use: bool = False
    use_count: int = 0


class ConnectionPool:
    """连接池"""
    
    def __init__(self, data_dir: str, min_connections: int = 2, 
                 max_connections: int = 10, idle_timeout: float = 300.0):
        """
        Args:
            data_dir: 数据目录
            min_connections: 最小连接数
            max_connections: 最大连接数
            idle_timeout: 空闲超时时间（秒）
        """
        self.data_dir = data_dir
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.idle_timeout = idle_timeout
        
        self.connections: List[Connection] = []
        self.available_connections: queue.Queue = queue.Queue()
        self.lock = threading.RLock()
        
        # 初始化最小连接数
        self._initialize_pool()
    
    def _initialize_pool(self):
        """初始化连接池"""
        for _ in range(self.min_connections):
            conn = self._create_connection()
            self.connections.append(conn)
            self.available_connections.put(conn)
    
    def _create_connection(self) -> Connection:
        """创建新连接"""
        db = Database(data_dir=self.data_dir)
        return Connection(
            db=db,
            created_at=time.time(),
            last_used=time.time()
        )
    
    def _get_available_connection(self) -> Optional[Connection]:
        """获取可用连接"""
        # 先尝试从队列获取
        try:
            conn = self.available_connections.get_nowait()
            if self._is_connection_valid(conn):
                return conn
            else:
                # 连接无效，尝试重新创建
                with self.lock:
                    if conn in self.connections:
                        self.connections.remove(conn)
                        conn.db.flush()
        except queue.Empty:
            pass
        
        # 尝试从现有连接中找空闲的
        with self.lock:
            for conn in self.connections:
                if not conn.in_use and self._is_connection_valid(conn):
                    return conn
        
        # 创建新连接（如果未达到最大连接数）
        with self.lock:
            if len(self.connections) < self.max_connections:
                conn = self._create_connection()
                self.connections.append(conn)
                return conn
        
        return None
    
    def _is_connection_valid(self, conn: Connection) -> bool:
        """检查连接是否有效"""
        if conn.in_use:
            return False
        
        # 检查空闲超时
        if time.time() - conn.last_used > self.idle_timeout:
            return False
        
        return True
    
    def _cleanup_idle_connections(self):
        """清理空闲连接"""
        with self.lock:
            current_time = time.time()
            to_remove = []
            
            for conn in self.connections:
                if (not conn.in_use and 
                    current_time - conn.last_used > self.idle_timeout and
                    len(self.connections) > self.min_connections):
                    to_remove.append(conn)
            
            for conn in to_remove:
                self.connections.remove(conn)
                # 关闭连接
                conn.db.flush()
    
    @contextmanager
    def get_connection(self):
        """获取连接（上下文管理器）"""
        conn = self._get_available_connection()
        if not conn:
            raise RuntimeError("No available connection")
        
        conn.in_use = True
        conn.last_used = time.time()
        conn.use_count += 1
        
        try:
            yield conn.db
        finally:
            conn.in_use = False
            conn.last_used = time.time()
            # 放回队列
            if self._is_connection_valid(conn):
                self.available_connections.put(conn)
            
            # 定期清理空闲连接
            if time.time() % 60 < 1:  # 每分钟清理一次
                self._cleanup_idle_connections()
    
    def get_stats(self) -> Dict:
        """获取连接池统计信息"""
        with self.lock:
            return {
                'total_connections': len(self.connections),
                'available_connections': self.available_connections.qsize(),
                'in_use_connections': sum(1 for c in self.connections if c.in_use),
                'total_uses': sum(c.use_count for c in self.connections)
            }
    
    def close_all(self):
        """关闭所有连接"""
        with self.lock:
            for conn in self.connections:
                conn.db.flush()
            self.connections.clear()
            while not self.available_connections.empty():
                try:
                    self.available_connections.get_nowait()
                except queue.Empty:
                    break

