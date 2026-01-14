"""
查询优化器模块
分析查询计划，优化执行策略
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class QueryType(Enum):
    """查询类型"""
    GET = "get"
    RANGE = "range"
    INDEX = "index"
    HISTORY = "history"
    AGGREGATE = "aggregate"


@dataclass
class QueryPlan:
    """查询计划"""
    query_type: QueryType
    estimated_cost: float
    execution_steps: List[str]
    use_index: bool = False
    index_name: Optional[str] = None
    parallel: bool = False


class QueryOptimizer:
    """查询优化器"""
    
    def __init__(self):
        self.stats: Dict[str, Any] = {}  # 统计信息
    
    def optimize(self, query_type: QueryType, **kwargs) -> QueryPlan:
        """优化查询"""
        if query_type == QueryType.GET:
            return self._optimize_get(**kwargs)
        elif query_type == QueryType.RANGE:
            return self._optimize_range(**kwargs)
        elif query_type == QueryType.INDEX:
            return self._optimize_index(**kwargs)
        elif query_type == QueryType.HISTORY:
            return self._optimize_history(**kwargs)
        else:
            return QueryPlan(
                query_type=query_type,
                estimated_cost=1.0,
                execution_steps=["default_execution"]
            )
    
    def _optimize_get(self, key: bytes, use_cache: bool = True) -> QueryPlan:
        """优化GET查询"""
        # 检查是否有索引
        # 估算成本
        cost = 1.0  # 基础成本
        
        if use_cache:
            cost *= 0.1  # 缓存命中成本更低
        
        return QueryPlan(
            query_type=QueryType.GET,
            estimated_cost=cost,
            execution_steps=[
                "check_cache" if use_cache else "skip_cache",
                "query_storage"
            ],
            use_index=False
        )
    
    def _optimize_range(self, start_key: bytes, end_key: bytes) -> QueryPlan:
        """优化范围查询"""
        # 估算范围大小
        range_size = self._estimate_range_size(start_key, end_key)
        
        # 决定是否使用索引
        use_index = range_size > 1000
        
        cost = range_size * 0.001
        
        return QueryPlan(
            query_type=QueryType.RANGE,
            estimated_cost=cost,
            execution_steps=[
                "use_bplus_tree" if use_index else "scan_storage",
                "filter_results"
            ],
            use_index=use_index
        )
    
    def _optimize_index(self, index_name: str, index_value: Any) -> QueryPlan:
        """优化索引查询"""
        return QueryPlan(
            query_type=QueryType.INDEX,
            estimated_cost=0.5,  # 索引查询成本较低
            execution_steps=[
                "query_index",
                "fetch_values"
            ],
            use_index=True,
            index_name=index_name
        )
    
    def _optimize_history(self, key: bytes, start_version: Optional[int] = None,
                         end_version: Optional[int] = None) -> QueryPlan:
        """优化历史查询"""
        # 估算版本数量
        version_count = self._estimate_version_count(key, start_version, end_version)
        
        cost = version_count * 0.01
        
        return QueryPlan(
            query_type=QueryType.HISTORY,
            estimated_cost=cost,
            execution_steps=[
                "query_version_index",
                "fetch_version_data"
            ],
            use_index=True
        )
    
    def _estimate_range_size(self, start_key: bytes, end_key: bytes) -> int:
        """估算范围大小（基于统计信息）"""
        # 从统计信息获取
        if 'range_queries' in self.stats:
            avg_size = self.stats['range_queries'].get('avg_size', 1000)
            return int(avg_size)
        
        # 基于key范围估算（简化但更准确）
        key_diff = int.from_bytes(end_key[:8] if len(end_key) >= 8 else end_key + b'\x00' * (8 - len(end_key)), 'big') - \
                   int.from_bytes(start_key[:8] if len(start_key) >= 8 else start_key + b'\x00' * (8 - len(start_key)), 'big')
        # 假设每256个key值对应一个实际key
        estimated = max(1, key_diff // 256)
        return min(estimated, 1000000)  # 限制最大估算值
    
    def _estimate_version_count(self, key: bytes, start_version: Optional[int],
                               end_version: Optional[int]) -> int:
        """估算版本数量（基于统计信息）"""
        # 从统计信息获取
        if 'version_queries' in self.stats:
            avg_count = self.stats['version_queries'].get('avg_count', 100)
            return int(avg_count)
        
        # 基于版本范围估算
        if start_version is not None and end_version is not None:
            return end_version - start_version + 1
        elif start_version is not None:
            # 假设最多1000个版本
            return min(1000, 1000 - start_version)
        else:
            return 100  # 默认估算
    
    def update_stats(self, query_type: QueryType, duration: float, result_count: int):
        """更新统计信息"""
        if query_type.value not in self.stats:
            self.stats[query_type.value] = {
                'count': 0,
                'total_duration': 0.0,
                'total_results': 0
            }
        
        stats = self.stats[query_type.value]
        stats['count'] += 1
        stats['total_duration'] += duration
        stats['total_results'] += result_count

