"""
完整的性能基准测试
生成详细的性能报告
"""

import time
import os
import tempfile
import shutil
import json
import statistics
from typing import Dict, List
from src.amdb import Database
from src.amdb.metrics import get_metrics, PerformanceMonitor
import sys
sys.path.insert(0, os.path.dirname(__file__))
from test_timeout_utils import assert_performance_with_timeout


class ComprehensiveBenchmark:
    """完整性能基准测试"""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        self.results = {}
        self.metrics = get_metrics()
        self.monitor = PerformanceMonitor(self.metrics)
    
    def cleanup(self):
        """清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def run_write_benchmark(self, sizes: List[int]) -> Dict:
        """写入性能基准"""
        print("\n=== 写入性能基准 ===")
        results = []
        
        for size in sizes:
            db = Database(
                data_dir=os.path.join(self.temp_dir, f"write_{size}"),
                enable_sharding=True,
                shard_count=256
            )
            
            items = [(f"key_{i}".encode(), f"value_{i}".encode()) for i in range(size)]
            
            # 批量写入（带超时检查）
            def batch_write_operation():
                return db.batch_put(items)
            
            # 根据数据量设置超时时间（至少100条/秒）
            max_timeout = max(30.0, size / 100.0)
            
            start = time.time()
            assert_performance_with_timeout(
                batch_write_operation,
                max_seconds=max_timeout,
                operation_name=f"写入基准({size:,}条)",
                min_throughput=100.0,
                item_count=size
            )
            elapsed = time.time() - start
            
            throughput = size / elapsed
            results.append({
                'size': size,
                'time': elapsed,
                'throughput': throughput
            })
            
            print(f"{size:8,} 条: {elapsed:6.3f}秒, {throughput:10,.0f} 写入/秒")
            
            db.flush()
            shutil.rmtree(os.path.join(self.temp_dir, f"write_{size}"), ignore_errors=True)
        
        return results
    
    def run_read_benchmark(self, sizes: List[int]) -> Dict:
        """读取性能基准"""
        print("\n=== 读取性能基准 ===")
        
        # 准备数据
        db = Database(
            data_dir=os.path.join(self.temp_dir, "read_bench"),
            enable_sharding=True,
            shard_count=256
        )
        
        max_size = max(sizes)
        items = [(f"read_key_{i}".encode(), f"read_value_{i}".encode()) 
                 for i in range(max_size)]
        db.batch_put(items)
        db.flush()
        
        results = []
        for size in sizes:
            # 读取（带超时检查）
            def read_operation():
                for i in range(size):
                    db.get(f"read_key_{i}".encode())
            
            # 根据读取量设置超时时间（至少200次/秒）
            max_timeout = max(10.0, size / 200.0)
            
            start = time.time()
            assert_performance_with_timeout(
                read_operation,
                max_seconds=max_timeout,
                operation_name=f"读取基准({size:,}次)",
                min_throughput=200.0,
                item_count=size
            )
            elapsed = time.time() - start
            
            throughput = size / elapsed
            results.append({
                'size': size,
                'time': elapsed,
                'throughput': throughput
            })
            
            print(f"{size:8,} 次: {elapsed:6.3f}秒, {throughput:10,.0f} 读取/秒")
        
        return results
    
    def run_latency_benchmark(self, iterations: int = 10000) -> Dict:
        """延迟基准"""
        print("\n=== 延迟基准 ===")
        
        db = Database(
            data_dir=os.path.join(self.temp_dir, "latency_bench"),
            enable_sharding=True
        )
        
        # 准备数据
        for i in range(1000):
            db.put(f"lat_key_{i}".encode(), f"lat_value_{i}".encode())
        
        # 写入延迟
        write_latencies = []
        for i in range(iterations):
            start = time.perf_counter()
            db.put(f"lat_write_{i}".encode(), f"lat_value_{i}".encode())
            latency = (time.perf_counter() - start) * 1000  # 毫秒
            write_latencies.append(latency)
        
        # 读取延迟
        read_latencies = []
        for i in range(iterations):
            key = f"lat_key_{i % 1000}".encode()
            start = time.perf_counter()
            db.get(key)
            latency = (time.perf_counter() - start) * 1000
            read_latencies.append(latency)
        
        def calc_stats(latencies):
            return {
                'min': min(latencies),
                'max': max(latencies),
                'mean': statistics.mean(latencies),
                'median': statistics.median(latencies),
                'p50': statistics.median(latencies),
                'p95': self._percentile(latencies, 95),
                'p99': self._percentile(latencies, 99),
                'p999': self._percentile(latencies, 99.9),
                'stddev': statistics.stdev(latencies) if len(latencies) > 1 else 0
            }
        
        write_stats = calc_stats(write_latencies)
        read_stats = calc_stats(read_latencies)
        
        print("写入延迟 (毫秒):")
        print(f"  平均: {write_stats['mean']:.2f}, 中位数: {write_stats['median']:.2f}")
        print(f"  P95: {write_stats['p95']:.2f}, P99: {write_stats['p99']:.2f}")
        
        print("读取延迟 (毫秒):")
        print(f"  平均: {read_stats['mean']:.2f}, 中位数: {read_stats['median']:.2f}")
        print(f"  P95: {read_stats['p95']:.2f}, P99: {read_stats['p99']:.2f}")
        
        return {'write': write_stats, 'read': read_stats}
    
    def run_concurrent_benchmark(self, thread_counts: List[int], ops_per_thread: int = 1000) -> Dict:
        """并发性能基准"""
        print("\n=== 并发性能基准 ===")
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        results = []
        
        for thread_count in thread_counts:
            db = Database(
                data_dir=os.path.join(self.temp_dir, f"concurrent_{thread_count}"),
                enable_sharding=True
            )
            
            def worker(tid):
                success = 0
                for i in range(ops_per_thread):
                    key = f"concurrent_{tid}_{i}".encode()
                    try:
                        db.put(key, f"value_{i}".encode())
                        if db.get(key):
                            success += 1
                    except Exception:
                        pass
                return success
            
            start = time.time()
            with ThreadPoolExecutor(max_workers=thread_count) as executor:
                futures = [executor.submit(worker, i) for i in range(thread_count)]
                results_list = [f.result() for f in as_completed(futures)]
            elapsed = time.time() - start
            
            total_ops = thread_count * ops_per_thread
            total_success = sum(results_list)
            throughput = total_ops / elapsed
            
            results.append({
                'threads': thread_count,
                'ops': total_ops,
                'success': total_success,
                'time': elapsed,
                'throughput': throughput
            })
            
            print(f"{thread_count:3d} 线程: {elapsed:6.2f}秒, "
                  f"{throughput:10,.0f} 操作/秒, "
                  f"成功率: {total_success/total_ops*100:.1f}%")
        
        return results
    
    def run_all(self):
        """运行所有基准测试"""
        print("=" * 80)
        print("AmDb 完整性能基准测试")
        print("=" * 80)
        
        # 写入基准
        write_results = self.run_write_benchmark([1000, 10000, 100000, 1000000])
        
        # 读取基准
        read_results = self.run_read_benchmark([1000, 10000, 100000, 1000000])
        
        # 延迟基准
        latency_results = self.run_latency_benchmark(10000)
        
        # 并发基准
        concurrent_results = self.run_concurrent_benchmark([1, 5, 10, 20, 50], 1000)
        
        # 生成报告
        self.generate_report({
            'write': write_results,
            'read': read_results,
            'latency': latency_results,
            'concurrent': concurrent_results
        })
    
    def _percentile(self, data: List[float], p: float) -> float:
        """计算百分位数"""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * p / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def generate_report(self, results: Dict):
        """生成性能报告"""
        report = {
            'timestamp': time.time(),
            'results': results,
            'metrics': self.metrics.get_all_metrics()
        }
        
        report_file = "./test_reports/comprehensive_benchmark.json"
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n完整报告已保存: {report_file}")


if __name__ == '__main__':
    benchmark = ComprehensiveBenchmark()
    try:
        benchmark.run_all()
    finally:
        benchmark.cleanup()

