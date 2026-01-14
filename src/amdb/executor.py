"""
执行引擎模块
执行查询计划，支持并行执行
"""

import time
import threading
from typing import List, Dict, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from .query_optimizer import QueryPlan, QueryType
from .database import Database


class ExecutionContext:
    """执行上下文"""
    
    def __init__(self, db: Database):
        self.db = db
        self.start_time = time.time()
        self.steps_completed: List[str] = []
        self.results: Dict[str, Any] = {}


class QueryExecutor:
    """查询执行器"""
    
    def __init__(self, db: Database, max_workers: Optional[int] = None):
        """
        Args:
            db: 数据库实例
            max_workers: 最大工作线程数（如果为None，从配置读取）
        """
        self.db = db
        # 从配置读取最大工作线程数
        if max_workers is None:
            if hasattr(db, 'config') and db.config:
                self.max_workers = db.config.threading_max_workers if db.config.threading_enable else 1
            else:
                self.max_workers = 4
        else:
            self.max_workers = max_workers
        
        # 如果禁用多线程，使用单线程
        if hasattr(db, 'config') and db.config and not db.config.threading_enable:
            self.max_workers = 1
        
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
    
    def execute(self, plan: QueryPlan, **kwargs) -> Any:
        """执行查询计划"""
        context = ExecutionContext(self.db)
        
        try:
            for step in plan.execution_steps:
                context.steps_completed.append(step)
                result = self._execute_step(step, context, plan, **kwargs)
                context.results[step] = result
            
            return context.results.get('final_result')
        except Exception as e:
            raise RuntimeError(f"Query execution failed: {e}")
    
    def _execute_step(self, step: str, context: ExecutionContext, 
                     plan: QueryPlan, **kwargs) -> Any:
        """执行单个步骤"""
        if step == "check_cache":
            # 检查缓存（完整实现）
            from ..cache import CacheManager, CachePolicy
            if not hasattr(self, '_cache'):
                self._cache = CacheManager(CachePolicy.LRU, max_size=10000)
            
            key = kwargs.get('key')
            if key:
                cached_value = self._cache.get(key)
                if cached_value:
                    context.results['cached'] = True
                    context.results['final_result'] = cached_value
                    return cached_value
            context.results['cached'] = False
            return None
        
        elif step == "query_storage":
            if plan.query_type == QueryType.GET:
                return self.db.get(kwargs.get('key'))
            return None
        
        elif step == "use_bplus_tree":
            if plan.query_type == QueryType.RANGE:
                return self.db.range_query(
                    kwargs.get('start_key'),
                    kwargs.get('end_key')
                )
            return None
        
        elif step == "scan_storage":
            # 扫描存储（完整实现）
            if plan.query_type == QueryType.RANGE:
                start_key = kwargs.get('start_key')
                end_key = kwargs.get('end_key')
                if start_key and end_key:
                    # 使用范围查询
                    return self.db.range_query(start_key, end_key)
            # 否则返回空列表
            return []
        
        elif step == "filter_results":
            # 过滤结果
            results = context.results.get('use_bplus_tree') or context.results.get('scan_storage')
            return results or []
        
        elif step == "query_index":
            if plan.index_name:
                return self.db.query_index(plan.index_name, kwargs.get('index_value'))
            return []
        
        elif step == "fetch_values":
            keys = context.results.get('query_index', [])
            results = {}
            for key in keys:
                value = self.db.get(key)
                if value:
                    results[key] = value
            context.results['final_result'] = results
            return results
        
        elif step == "query_version_index":
            history = self.db.get_history(
                kwargs.get('key'),
                kwargs.get('start_version'),
                kwargs.get('end_version')
            )
            context.results['final_result'] = history
            return history
        
        elif step == "fetch_version_data":
            # 获取版本数据
            return context.results.get('query_version_index')
        
        return None
    
    def execute_parallel(self, plans: List[QueryPlan], **kwargs) -> List[Any]:
        """并行执行多个查询计划"""
        futures = []
        for plan in plans:
            future = self.executor.submit(self.execute, plan, **kwargs)
            futures.append((future, plan))
        
        results = []
        for future, plan in futures:
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append(None)
        
        return results
    
    def shutdown(self):
        """关闭执行器"""
        self.executor.shutdown(wait=True)

