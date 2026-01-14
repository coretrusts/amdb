"""
指标收集测试
"""

import unittest
import time
from src.amdb.metrics import MetricsCollector, PerformanceMonitor


class TestMetrics(unittest.TestCase):
    """指标测试"""
    
    def test_counter(self):
        """测试计数器"""
        metrics = MetricsCollector()
        
        metrics.increment("test.counter")
        metrics.increment("test.counter", 5)
        
        self.assertEqual(metrics.get_counter("test.counter"), 6)
    
    def test_gauge(self):
        """测试仪表"""
        metrics = MetricsCollector()
        
        metrics.set_gauge("test.gauge", 100.5)
        self.assertEqual(metrics.get_gauge("test.gauge"), 100.5)
    
    def test_histogram(self):
        """测试直方图"""
        metrics = MetricsCollector()
        
        for i in range(100):
            metrics.record_histogram("test.histogram", float(i))
        
        stats = metrics.get_histogram_stats("test.histogram")
        self.assertEqual(stats['count'], 100)
        self.assertEqual(stats['min'], 0.0)
        self.assertEqual(stats['max'], 99.0)
        self.assertAlmostEqual(stats['mean'], 49.5, places=1)
    
    def test_performance_monitor(self):
        """测试性能监控"""
        metrics = MetricsCollector()
        monitor = PerformanceMonitor(metrics)
        
        monitor.record_operation("put", 0.1, success=True)
        monitor.record_operation("put", 0.2, success=False)
        
        self.assertEqual(metrics.get_counter("operation.put.success"), 1)
        self.assertEqual(metrics.get_counter("operation.put.error"), 1)

