"""
全面的压力测试
包括各项性能指标的测试和报告
"""

import unittest
import time
import os
import tempfile
import shutil
import random
import string
import statistics
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple
from src.amdb import Database
from src.amdb.metrics import get_metrics, PerformanceMonitor


class ComprehensiveStressTest(unittest.TestCase):
    """全面压力测试"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.db = Database(
            data_dir=os.path.join(self.temp_dir, "stress_db"),
            enable_sharding=True,
            shard_count=256,
            max_file_size=128 * 1024 * 1024
        )
        self.metrics = get_metrics()
        self.monitor = PerformanceMonitor(self.metrics)
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _random_string(self, length: int = 10) -> str:
        """生成随机字符串"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    def test_write_throughput(self):
        """写入吞吐量测试"""
        print("\n=== 写入吞吐量测试 ===")
        
        test_sizes = [1000, 10000, 100000, 1000000]
        results = []
        
        for size in test_sizes:
            print(f"\n测试规模: {size:,} 条记录")
            
            # 预热
            for i in range(100):
                self.db.put(f"warmup_{i}".encode(), f"warmup_value_{i}".encode())
            
            # 正式测试
            start_time = time.time()
            items = []
            for i in range(size):
                key = f"write_test_{i:08d}".encode()
                value = f"value_{i}_{self._random_string(100)}".encode()
                items.append((key, value))
            
            # 批量写入（带超时检查）
            def batch_write_operation():
                return self.db.batch_put(items)
            
            # 根据数据量设置超时时间（至少100条/秒）
            max_timeout = max(30.0, size / 100.0)  # 至少100条/秒，最少30秒
            
            batch_start = time.time()
            assert_performance_with_timeout(
                batch_write_operation,
                max_seconds=max_timeout,
                operation_name=f"批量写入({size:,}条)",
                min_throughput=100.0,  # 至少100条/秒
                item_count=size
            )
            batch_time = time.time() - batch_start
            
            total_time = time.time() - start_time
            throughput = size / total_time
            
            results.append({
                'size': size,
                'total_time': total_time,
                'batch_time': batch_time,
                'throughput': throughput,
                'throughput_per_sec': f"{throughput:,.0f}"
            })
            
            print(f"  总时间: {total_time:.2f}秒")
            print(f"  批量写入时间: {batch_time:.2f}秒")
            print(f"  吞吐量: {throughput:,.0f} 写入/秒")
            
            # 记录指标
            self.monitor.record_write(len(b''.join([k+v for k, v in items])), total_time)
        
        # 生成报告
        self._generate_report("写入吞吐量", results)
    
    def test_read_throughput(self):
        """读取吞吐量测试"""
        print("\n=== 读取吞吐量测试 ===")
        
        # 预先写入数据
        data_size = 100000
        print(f"准备数据: {data_size:,} 条记录")
        items = []
        for i in range(data_size):
            key = f"read_test_{i:08d}".encode()
            value = f"value_{i}".encode()
            items.append((key, value))
        self.db.batch_put(items)
        
        # 读取测试
        read_sizes = [1000, 10000, 100000]
        results = []
        
        for read_size in read_sizes:
            print(f"\n读取规模: {read_size:,} 次")
            
            # 随机读取（带超时检查）
            def read_operation():
                read_count = 0
                for _ in range(read_size):
                    random_key = f"read_test_{random.randint(0, data_size-1):08d}".encode()
                    value = self.db.get(random_key)
                    if value:
                        read_count += 1
                return read_count
            
            # 根据读取量设置超时时间（至少200次/秒）
            max_timeout = max(10.0, read_size / 200.0)  # 至少200次/秒，最少10秒
            
            start_time = time.time()
            read_count = assert_performance_with_timeout(
                read_operation,
                max_seconds=max_timeout,
                operation_name=f"随机读取({read_size:,}次)",
                min_throughput=200.0,  # 至少200次/秒
                item_count=read_size
            )
            elapsed = time.time() - start_time
            throughput = read_size / elapsed
            
            results.append({
                'size': read_size,
                'time': elapsed,
                'throughput': throughput,
                'success_rate': read_count / read_size * 100
            })
            
            print(f"  耗时: {elapsed:.2f}秒")
            print(f"  吞吐量: {throughput:,.0f} 读取/秒")
            print(f"  成功率: {read_count/read_size*100:.2f}%")
            
            self.monitor.record_read(elapsed)
        
        self._generate_report("读取吞吐量", results)
    
    def test_concurrent_operations(self):
        """并发操作测试"""
        print("\n=== 并发操作测试 ===")
        
        num_threads = [1, 5, 10, 20, 50]
        operations_per_thread = 1000
        results = []
        
        for thread_count in num_threads:
            print(f"\n线程数: {thread_count}")
            
            def worker(thread_id: int):
                success_count = 0
                for i in range(operations_per_thread):
                    key = f"concurrent_{thread_id}_{i:04d}".encode()
                    value = f"value_{thread_id}_{i}".encode()
                    try:
                        self.db.put(key, value)
                        retrieved = self.db.get(key)
                        if retrieved == value:
                            success_count += 1
                    except Exception:
                        pass
                return success_count
            
            start_time = time.time()
            with ThreadPoolExecutor(max_workers=thread_count) as executor:
                futures = [executor.submit(worker, i) for i in range(thread_count)]
                results_list = [f.result() for f in as_completed(futures)]
            elapsed = time.time() - start_time
            
            total_ops = thread_count * operations_per_thread
            total_success = sum(results_list)
            throughput = total_ops / elapsed
            
            results.append({
                'threads': thread_count,
                'time': elapsed,
                'total_ops': total_ops,
                'success_ops': total_success,
                'throughput': throughput,
                'success_rate': total_success / total_ops * 100
            })
            
            print(f"  总操作: {total_ops:,}")
            print(f"  成功操作: {total_success:,}")
            print(f"  耗时: {elapsed:.2f}秒")
            print(f"  吞吐量: {throughput:,.0f} 操作/秒")
            print(f"  成功率: {total_success/total_ops*100:.2f}%")
        
        self._generate_report("并发操作", results)
    
    def test_mixed_workload(self):
        """混合工作负载测试"""
        print("\n=== 混合工作负载测试 ===")
        
        # 50%写入，50%读取
        total_ops = 100000
        write_ops = total_ops // 2
        read_ops = total_ops // 2
        
        # 预先写入一些数据用于读取
        pre_write_items = []
        for i in range(10000):
            key = f"mixed_{i:05d}".encode()
            value = f"pre_value_{i}".encode()
            pre_write_items.append((key, value))
        self.db.batch_put(pre_write_items)
        
        def write_worker():
            success = 0
            for i in range(write_ops):
                key = f"mixed_write_{i:06d}".encode()
                value = f"write_value_{i}".encode()
                try:
                    self.db.put(key, value)
                    success += 1
                except Exception:
                    pass
            return success
        
        def read_worker():
            success = 0
            for i in range(read_ops):
                random_key = f"mixed_{random.randint(0, 9999):05d}".encode()
                try:
                    value = self.db.get(random_key)
                    if value:
                        success += 1
                except Exception:
                    pass
            return success
        
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=10) as executor:
            write_future = executor.submit(write_worker)
            read_future = executor.submit(read_worker)
            
            write_success = write_future.result()
            read_success = read_future.result()
        
        elapsed = time.time() - start_time
        total_throughput = total_ops / elapsed
        
        result = {
            'total_ops': total_ops,
            'write_ops': write_ops,
            'read_ops': read_ops,
            'write_success': write_success,
            'read_success': read_success,
            'time': elapsed,
            'throughput': total_throughput
        }
        
        print(f"  总操作: {total_ops:,}")
        print(f"  写入成功: {write_success:,}/{write_ops:,}")
        print(f"  读取成功: {read_success:,}/{read_ops:,}")
        print(f"  总耗时: {elapsed:.2f}秒")
        print(f"  总吞吐量: {total_throughput:,.0f} 操作/秒")
        
        self._generate_report("混合工作负载", [result])
    
    def test_latency_distribution(self):
        """延迟分布测试"""
        print("\n=== 延迟分布测试 ===")
        
        # 写入延迟
        write_latencies = []
        for i in range(10000):
            key = f"latency_write_{i:05d}".encode()
            value = f"value_{i}".encode()
            start = time.time()
            self.db.put(key, value)
            latency = (time.time() - start) * 1000  # 转换为毫秒
            write_latencies.append(latency)
        
        # 读取延迟
        read_latencies = []
        for i in range(10000):
            key = f"latency_write_{random.randint(0, 9999):05d}".encode()
            start = time.time()
            self.db.get(key)
            latency = (time.time() - start) * 1000
            read_latencies.append(latency)
        
        def calculate_stats(latencies: List[float]) -> Dict:
            return {
                'min': min(latencies),
                'max': max(latencies),
                'mean': statistics.mean(latencies),
                'median': statistics.median(latencies),
                'p50': statistics.median(latencies),
                'p95': self._percentile(latencies, 95),
                'p99': self._percentile(latencies, 99),
                'p999': self._percentile(latencies, 99.9)
            }
        
        write_stats = calculate_stats(write_latencies)
        read_stats = calculate_stats(read_latencies)
        
        print("\n写入延迟统计 (毫秒):")
        print(f"  最小值: {write_stats['min']:.2f}ms")
        print(f"  最大值: {write_stats['max']:.2f}ms")
        print(f"  平均值: {write_stats['mean']:.2f}ms")
        print(f"  中位数: {write_stats['median']:.2f}ms")
        print(f"  P95: {write_stats['p95']:.2f}ms")
        print(f"  P99: {write_stats['p99']:.2f}ms")
        print(f"  P99.9: {write_stats['p999']:.2f}ms")
        
        print("\n读取延迟统计 (毫秒):")
        print(f"  最小值: {read_stats['min']:.2f}ms")
        print(f"  最大值: {read_stats['max']:.2f}ms")
        print(f"  平均值: {read_stats['mean']:.2f}ms")
        print(f"  中位数: {read_stats['median']:.2f}ms")
        print(f"  P95: {read_stats['p95']:.2f}ms")
        print(f"  P99: {read_stats['p99']:.2f}ms")
        print(f"  P99.9: {read_stats['p999']:.2f}ms")
        
        self._generate_report("延迟分布", {
            'write': write_stats,
            'read': read_stats
        })
    
    def test_memory_usage(self):
        """内存使用测试"""
        print("\n=== 内存使用测试 ===")
        
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 写入数据
        data_sizes = [10000, 100000, 1000000]
        results = []
        
        for size in data_sizes:
            print(f"\n数据量: {size:,} 条记录")
            
            items = []
            for i in range(size):
                key = f"mem_test_{i:08d}".encode()
                value = f"value_{i}_{'x'*100}".encode()  # 100字节值
                items.append((key, value))
            
            self.db.batch_put(items)
            
            current_memory = process.memory_info().rss / 1024 / 1024
            memory_increase = current_memory - initial_memory
            memory_per_record = memory_increase / size * 1024  # KB per record
            
            results.append({
                'size': size,
                'memory_mb': current_memory,
                'increase_mb': memory_increase,
                'per_record_kb': memory_per_record
            })
            
            print(f"  内存使用: {current_memory:.2f} MB")
            print(f"  内存增长: {memory_increase:.2f} MB")
            print(f"  每条记录: {memory_per_record:.2f} KB")
        
        self._generate_report("内存使用", results)
    
    def test_disk_usage(self):
        """磁盘使用测试"""
        print("\n=== 磁盘使用测试 ===")
        
        import shutil
        
        initial_size = self._get_dir_size(self.temp_dir)
        
        data_sizes = [10000, 100000, 1000000]
        results = []
        
        for size in data_sizes:
            print(f"\n数据量: {size:,} 条记录")
            
            items = []
            for i in range(size):
                key = f"disk_test_{i:08d}".encode()
                value = f"value_{i}_{'x'*200}".encode()  # 200字节值
                items.append((key, value))
            
            self.db.batch_put(items)
            self.db.flush()
            
            current_size = self._get_dir_size(self.temp_dir)
            size_increase = current_size - initial_size
            size_per_record = size_increase / size  # bytes per record
            
            results.append({
                'size': size,
                'total_size_mb': current_size / 1024 / 1024,
                'increase_mb': size_increase / 1024 / 1024,
                'per_record_bytes': size_per_record
            })
            
            print(f"  总大小: {current_size / 1024 / 1024:.2f} MB")
            print(f"  增长: {size_increase / 1024 / 1024:.2f} MB")
            print(f"  每条记录: {size_per_record:.2f} 字节")
        
        self._generate_report("磁盘使用", results)
    
    def test_shard_distribution(self):
        """分片分布测试"""
        print("\n=== 分片分布测试 ===")
        
        # 写入大量数据
        data_size = 100000
        items = []
        for i in range(data_size):
            key = f"shard_test_{i:08d}".encode()
            value = f"value_{i}".encode()
            items.append((key, value))
        
        self.db.batch_put(items)
        self.db.flush()
        
        # 获取分片统计
        stats = self.db.get_stats()
        shard_info = stats.get('shard_info', {})
        
        # 分析分布
        shard_sizes = []
        shard_file_counts = []
        
        for shard_id, info in shard_info.items():
            total_size = info['stats'].get('total_size', 0)
            file_count = info['sstable_count']
            shard_sizes.append(total_size)
            shard_file_counts.append(file_count)
        
        if shard_sizes:
            print(f"\n分片统计:")
            print(f"  活跃分片数: {len(shard_sizes)}")
            print(f"  平均分片大小: {statistics.mean(shard_sizes) / 1024 / 1024:.2f} MB")
            print(f"  最大分片大小: {max(shard_sizes) / 1024 / 1024:.2f} MB")
            print(f"  最小分片大小: {min(shard_sizes) / 1024 / 1024:.2f} MB")
            print(f"  标准差: {statistics.stdev(shard_sizes) / 1024 / 1024:.2f} MB")
            
            print(f"\n文件统计:")
            print(f"  平均文件数: {statistics.mean(shard_file_counts):.1f}")
            print(f"  最大文件数: {max(shard_file_counts)}")
            print(f"  最小文件数: {min(shard_file_counts)}")
            
            # 计算分布均匀度
            if len(shard_sizes) > 1:
                cv = statistics.stdev(shard_sizes) / statistics.mean(shard_sizes)  # 变异系数
                print(f"\n分布均匀度 (CV): {cv:.3f}")
                if cv < 0.3:
                    print("  ✓ 分布均匀")
                elif cv < 0.5:
                    print("  ⚠ 分布较均匀")
                else:
                    print("  ✗ 分布不均匀")
    
    def test_version_history_performance(self):
        """版本历史性能测试"""
        print("\n=== 版本历史性能测试 ===")
        
        key = b"version_perf_test"
        num_versions = 10000
        
        # 创建版本
        print(f"创建 {num_versions:,} 个版本...")
        start_time = time.time()
        for i in range(num_versions):
            self.db.put(key, f"version_{i}".encode())
        create_time = time.time() - start_time
        
        # 查询所有历史
        print("查询所有历史版本...")
        start_time = time.time()
        history = self.db.get_history(key)
        query_time = time.time() - start_time
        
        # 查询特定版本
        print("查询特定版本...")
        start_time = time.time()
        for version in [1, 100, 1000, 5000, 9999]:
            value = self.db.get(key, version=version)
        specific_time = time.time() - start_time
        
        result = {
            'num_versions': num_versions,
            'create_time': create_time,
            'query_all_time': query_time,
            'query_specific_time': specific_time,
            'create_throughput': num_versions / create_time,
            'query_all_throughput': len(history) / query_time if history else 0
        }
        
        print(f"  创建时间: {create_time:.2f}秒")
        print(f"  创建吞吐量: {result['create_throughput']:,.0f} 版本/秒")
        print(f"  查询所有历史: {query_time:.2f}秒")
        print(f"  查询特定版本: {specific_time:.2f}秒")
        
        self._generate_report("版本历史性能", [result])
    
    def test_range_query_performance(self):
        """范围查询性能测试"""
        print("\n=== 范围查询性能测试 ===")
        
        # 写入有序数据
        data_size = 100000
        print(f"准备数据: {data_size:,} 条记录")
        items = []
        for i in range(data_size):
            key = f"range_test_{i:08d}".encode()
            value = f"value_{i}".encode()
            items.append((key, value))
        self.db.batch_put(items)
        self.db.flush()
        
        # 不同范围大小的查询
        range_sizes = [100, 1000, 10000, 100000]
        results = []
        
        for range_size in range_sizes:
            start_idx = data_size // 4
            end_idx = start_idx + range_size
            
            start_key = f"range_test_{start_idx:08d}".encode()
            end_key = f"range_test_{end_idx:08d}".encode()
            
            start_time = time.time()
            results_list = self.db.range_query(start_key, end_key)
            elapsed = time.time() - start_time
            
            result = {
                'range_size': range_size,
                'result_count': len(results_list),
                'time': elapsed,
                'throughput': len(results_list) / elapsed if elapsed > 0 else 0
            }
            results.append(result)
            
            print(f"\n范围大小: {range_size:,}")
            print(f"  结果数量: {len(results_list):,}")
            print(f"  查询时间: {elapsed:.2f}秒")
            print(f"  吞吐量: {result['throughput']:,.0f} 结果/秒")
        
        self._generate_report("范围查询性能", results)
    
    def test_merkle_proof_performance(self):
        """Merkle证明性能测试"""
        print("\n=== Merkle证明性能测试 ===")
        
        # 写入数据
        data_size = 10000
        items = []
        for i in range(data_size):
            key = f"merkle_test_{i:05d}".encode()
            value = f"value_{i}".encode()
            items.append((key, value))
        self.db.batch_put(items)
        
        # 生成证明
        print("生成Merkle证明...")
        proof_times = []
        for i in range(100):
            key = f"merkle_test_{random.randint(0, data_size-1):05d}".encode()
            start = time.time()
            value, proof, root = self.db.get_with_proof(key)
            proof_times.append((time.time() - start) * 1000)
        
        # 验证证明
        print("验证Merkle证明...")
        verify_times = []
        for i in range(100):
            key = f"merkle_test_{random.randint(0, data_size-1):05d}".encode()
            value, proof, root = self.db.get_with_proof(key)
            if value and proof:
                start = time.time()
                is_valid = self.db.verify(key, value, proof)
                verify_times.append((time.time() - start) * 1000)
        
        print(f"\n生成证明统计 (毫秒):")
        print(f"  平均: {statistics.mean(proof_times):.2f}ms")
        print(f"  P95: {self._percentile(proof_times, 95):.2f}ms")
        print(f"  P99: {self._percentile(proof_times, 99):.2f}ms")
        
        if verify_times:
            print(f"\n验证证明统计 (毫秒):")
            print(f"  平均: {statistics.mean(verify_times):.2f}ms")
            print(f"  P95: {self._percentile(verify_times, 95):.2f}ms")
            print(f"  P99: {self._percentile(verify_times, 99):.2f}ms")
    
    def _percentile(self, data: List[float], p: float) -> float:
        """计算百分位数"""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * p / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def _get_dir_size(self, path: str) -> int:
        """获取目录大小"""
        total = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total += os.path.getsize(filepath)
        return total
    
    def _generate_report(self, test_name: str, results: any):
        """生成测试报告"""
        report_dir = "./test_reports"
        os.makedirs(report_dir, exist_ok=True)
        
        report_file = os.path.join(report_dir, f"{test_name.replace(' ', '_')}.json")
        with open(report_file, 'w') as f:
            json.dump({
                'test_name': test_name,
                'timestamp': time.time(),
                'results': results
            }, f, indent=2, default=str)
        
        print(f"\n报告已保存: {report_file}")


class BenchmarkSuite:
    """完整的性能基准测试套件"""
    
    def __init__(self, data_dir: str = "./data/benchmark"):
        self.data_dir = data_dir
        self.db = Database(
            data_dir=data_dir,
            enable_sharding=True,
            shard_count=256
        )
        self.metrics = get_metrics()
        self.results = {}
    
    def run_all_benchmarks(self):
        """运行所有基准测试"""
        print("=" * 80)
        print("AmDb 完整性能基准测试套件")
        print("=" * 80)
        
        benchmarks = [
            self.benchmark_write_throughput,
            self.benchmark_read_throughput,
            self.benchmark_concurrent_write,
            self.benchmark_concurrent_read,
            self.benchmark_mixed_workload,
            self.benchmark_latency,
            self.benchmark_memory_efficiency,
            self.benchmark_disk_efficiency,
        ]
        
        for benchmark in benchmarks:
            try:
                benchmark()
            except Exception as e:
                print(f"基准测试失败: {e}")
        
        self.generate_final_report()
    
    def benchmark_write_throughput(self):
        """写入吞吐量基准"""
        print("\n[基准] 写入吞吐量")
        # 实现基准测试
        pass
    
    def benchmark_read_throughput(self):
        """读取吞吐量基准"""
        print("\n[基准] 读取吞吐量")
        # 实现基准测试
        pass
    
    def benchmark_concurrent_write(self):
        """并发写入基准"""
        print("\n[基准] 并发写入")
        # 实现基准测试
        pass
    
    def benchmark_concurrent_read(self):
        """并发读取基准"""
        print("\n[基准] 并发读取")
        # 实现基准测试
        pass
    
    def benchmark_mixed_workload(self):
        """混合工作负载基准"""
        print("\n[基准] 混合工作负载")
        # 实现基准测试
        pass
    
    def benchmark_latency(self):
        """延迟基准"""
        print("\n[基准] 延迟")
        # 实现基准测试
        pass
    
    def benchmark_memory_efficiency(self):
        """内存效率基准"""
        print("\n[基准] 内存效率")
        # 实现基准测试
        pass
    
    def benchmark_disk_efficiency(self):
        """磁盘效率基准"""
        print("\n[基准] 磁盘效率")
        # 实现基准测试
        pass
    
    def generate_final_report(self):
        """生成最终报告"""
        print("\n" + "=" * 80)
        print("性能基准测试报告")
        print("=" * 80)
        
        all_metrics = self.metrics.get_all_metrics()
        print(json.dumps(all_metrics, indent=2, default=str))


if __name__ == '__main__':
    # 运行全面压力测试
    unittest.main(verbosity=2, exit=False)
    
    # 运行完整基准测试套件
    suite = BenchmarkSuite()
    suite.run_all_benchmarks()

