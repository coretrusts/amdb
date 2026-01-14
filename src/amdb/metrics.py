"""
监控和指标模块
收集性能指标、统计信息、健康检查
"""

import time
import threading
from typing import Dict, Any, List, Optional
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Metric:
    """指标"""
    name: str
    value: float
    timestamp: float = field(default_factory=time.time)
    tags: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """指标收集器"""
    
    def __init__(self):
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self.lock = threading.RLock()
        self.start_time = time.time()
    
    def increment(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None):
        """增加计数器"""
        with self.lock:
            self.counters[name] += value
            self._record_metric(name, self.counters[name], tags)
    
    def decrement(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None):
        """减少计数器"""
        with self.lock:
            self.counters[name] = max(0, self.counters[name] - value)
            self._record_metric(name, self.counters[name], tags)
    
    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """设置仪表值"""
        with self.lock:
            self.gauges[name] = value
            self._record_metric(name, value, tags)
    
    def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """记录直方图值"""
        with self.lock:
            self.histograms[name].append(value)
            if len(self.histograms[name]) > 1000:
                self.histograms[name] = self.histograms[name][-1000:]
            self._record_metric(name, value, tags)
    
    def record_timing(self, name: str, duration: float, tags: Optional[Dict[str, str]] = None):
        """记录时间"""
        self.record_histogram(name, duration, tags)
    
    def _record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]]):
        """记录指标"""
        metric = Metric(name=name, value=value, tags=tags or {})
        self.metrics[name].append(metric)
    
    def get_counter(self, name: str) -> int:
        """获取计数器值"""
        with self.lock:
            return self.counters.get(name, 0)
    
    def get_gauge(self, name: str) -> float:
        """获取仪表值"""
        with self.lock:
            return self.gauges.get(name, 0.0)
    
    def get_histogram_stats(self, name: str) -> Dict[str, float]:
        """获取直方图统计"""
        with self.lock:
            values = self.histograms.get(name, [])
            if not values:
                return {}
            return {
                'count': len(values),
                'min': min(values),
                'max': max(values),
                'mean': sum(values) / len(values),
                'p50': self._percentile(values, 50),
                'p95': self._percentile(values, 95),
                'p99': self._percentile(values, 99)
            }
    
    def _percentile(self, values: List[float], p: int) -> float:
        """计算百分位数"""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * p / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """获取所有指标"""
        with self.lock:
            return {
                'counters': dict(self.counters),
                'gauges': dict(self.gauges),
                'histograms': {
                    name: self.get_histogram_stats(name)
                    for name in self.histograms.keys()
                },
                'uptime': time.time() - self.start_time
            }
    
    def reset(self):
        """重置所有指标"""
        with self.lock:
            self.counters.clear()
            self.gauges.clear()
            self.histograms.clear()
            self.metrics.clear()
            self.start_time = time.time()


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, metrics: MetricsCollector):
        self.metrics = metrics
    
    def record_operation(self, operation: str, duration: float, success: bool = True):
        """记录操作"""
        self.metrics.record_timing(f"operation.{operation}.duration", duration)
        if success:
            self.metrics.increment(f"operation.{operation}.success")
        else:
            self.metrics.increment(f"operation.{operation}.error")
    
    def record_query(self, query_type: str, duration: float, result_count: int = 0):
        """记录查询"""
        self.metrics.record_timing(f"query.{query_type}.duration", duration)
        self.metrics.increment(f"query.{query_type}.count")
        if result_count > 0:
            self.metrics.record_histogram(f"query.{query_type}.result_count", result_count)
    
    def record_write(self, size: int, duration: float):
        """记录写入"""
        self.metrics.record_timing("write.duration", duration)
        self.metrics.increment("write.count")
        self.metrics.record_histogram("write.size", size)
    
    def record_read(self, duration: float):
        """记录读取"""
        self.metrics.record_timing("read.duration", duration)
        self.metrics.increment("read.count")


# 全局指标收集器
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics() -> MetricsCollector:
    """获取全局指标收集器"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector

