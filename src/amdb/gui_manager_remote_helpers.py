# -*- coding: utf-8 -*-
"""
GUI管理器远程连接辅助方法
提供统一的接口，自动处理本地和远程连接
"""

from typing import Optional, Dict, List, Tuple, Any
from .database import Database
from .network import RemoteDatabase


class DatabaseWrapper:
    """数据库包装器，统一本地和远程接口"""
    
    def __init__(self, db: Optional[Database] = None, remote_db: Optional[RemoteDatabase] = None):
        self.db = db
        self.remote_db = remote_db
        self.is_remote = remote_db is not None
    
    def get(self, key: bytes) -> Optional[bytes]:
        """获取值"""
        if self.is_remote:
            return self.remote_db.get(key)
        else:
            return self.db.get(key)
    
    def put(self, key: bytes, value: bytes) -> Tuple[bool, Optional[bytes]]:
        """写入值"""
        if self.is_remote:
            success = self.remote_db.put(key, value)
            return success, None
        else:
            return self.db.put(key, value)
    
    def batch_put(self, items: List[Tuple[bytes, bytes]]) -> Tuple[bool, Optional[bytes]]:
        """批量写入"""
        if self.is_remote:
            return self.remote_db.batch_put(items)
        else:
            return self.db.batch_put(items)
    
    def delete(self, key: bytes) -> bool:
        """删除键"""
        if self.is_remote:
            return self.remote_db.delete(key)
        else:
            return self.db.delete(key)
    
    def get_stats(self) -> Optional[Dict]:
        """获取统计信息"""
        if self.is_remote:
            return self.remote_db.get_stats()
        else:
            return self.db.get_stats()
    
    def get_all_keys(self) -> List[bytes]:
        """获取所有键"""
        if self.is_remote:
            return self.remote_db.get_all_keys()
        else:
            return self.db.version_manager.get_all_keys()
    
    def get_config(self) -> Optional[Dict]:
        """获取配置"""
        if self.is_remote:
            return self.remote_db.get_config()
        else:
            config = self.db.config
            return {
                'data_dir': config.data_dir,
                'network_host': config.network_host,
                'network_port': config.network_port,
                'batch_max_size': config.batch_max_size,
                'enable_sharding': config.enable_sharding,
                'shard_count': config.shard_count,
                'threading_enable': config.threading_enable,
                'threading_max_workers': config.threading_max_workers,
            }
    
    def flush(self, async_mode: bool = False):
        """刷新（仅本地）"""
        if not self.is_remote and self.db:
            self.db.flush(async_mode=async_mode)

