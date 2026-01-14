"""
查询引擎
支持复杂查询和查询优化
"""

from typing import List, Dict, Any, Optional, Callable, Tuple
from .database import Database


class QueryEngine:
    """
    查询引擎
    提供高级查询功能
    """
    
    def __init__(self, db: Database):
        self.db = db
    
    def select(self, keys: List[bytes], version: Optional[int] = None) -> Dict[bytes, bytes]:
        """批量选择"""
        result = {}
        for key in keys:
            value = self.db.get(key, version)
            if value is not None:
                result[key] = value
        return result
    
    def select_range(self, start_key: bytes, end_key: bytes, 
                    limit: Optional[int] = None) -> List[Tuple[bytes, bytes]]:
        """范围选择"""
        results = self.db.range_query(start_key, end_key)
        if limit:
            return results[:limit]
        return results
    
    def select_by_index(self, index_name: str, index_value: Any) -> Dict[bytes, bytes]:
        """通过索引选择"""
        keys = self.db.query_index(index_name, index_value)
        return self.select(keys)
    
    def select_history(self, key: bytes, start_version: Optional[int] = None,
                      end_version: Optional[int] = None) -> List[Dict[str, Any]]:
        """选择历史版本"""
        return self.db.get_history(key, start_version, end_version)
    
    def select_at_time(self, keys: List[bytes], timestamp: float) -> Dict[bytes, bytes]:
        """选择指定时间点的值"""
        result = {}
        for key in keys:
            value = self.db.get_at_time(key, timestamp)
            if value is not None:
                result[key] = value
        return result
    
    def filter(self, keys: List[bytes], predicate: Callable[[bytes, bytes], bool],
              version: Optional[int] = None) -> Dict[bytes, bytes]:
        """过滤查询"""
        result = {}
        for key in keys:
            value = self.db.get(key, version)
            if value is not None and predicate(key, value):
                result[key] = value
        return result
    
    def aggregate(self, keys: List[bytes], 
                 aggregator: Callable[[List[bytes]], Any],
                 version: Optional[int] = None) -> Any:
        """聚合查询"""
        values = []
        for key in keys:
            value = self.db.get(key, version)
            if value is not None:
                values.append(value)
        return aggregator(values)

