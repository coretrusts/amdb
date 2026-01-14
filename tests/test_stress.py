"""
压力测试和性能基准测试
"""

import unittest
import time
import os
import tempfile
import shutil
import random
import string
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.amdb import Database
from .test_timeout_utils import assert_performance_with_timeout


class StressTest(unittest.TestCase):
    """压力测试"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.db = Database(data_dir=os.path.join(self.temp_dir, "stress_db"))
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _random_string(self, length: int = 10) -> str:
        """生成随机字符串"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    def test_bulk_write(self):
        """批量写入压力测试（带超时）"""
        num_keys = 10000
        print(f"\n开始批量写入测试: {num_keys} 个键")
        
        # 准备数据
        items = [
            (f"key_{i}".encode(), f"value_{i}_{self._random_string(100)}".encode())
            for i in range(num_keys)
        ]
        
        # 批量写入（超时：10000条应在30秒内完成，即至少333条/秒）
        def write_operation():
            return self.db.batch_put(items)
        
        success, root_hash = assert_performance_with_timeout(
            write_operation,
            max_seconds=30.0,  # 30秒超时
            operation_name="批量写入",
            min_throughput=333.0,  # 至少333条/秒
            item_count=num_keys
        )
        
        self.assertTrue(success)
        print(f"批量写入完成（通过超时检查）")
        
        # 验证数据（读取验证也加超时）
        def verify_operation():
            for i in range(min(100, num_keys)):
                key = f"key_{i}".encode()
                value = self.db.get(key)
                self.assertIsNotNone(value)
        
        assert_performance_with_timeout(
            verify_operation,
            max_seconds=5.0,  # 100次读取应在5秒内完成
            operation_name="数据验证"
        )
        print(f"  数据验证完成（通过超时检查）")
    
    def test_concurrent_write(self):
        """并发写入测试（带超时）"""
        num_threads = 10
        writes_per_thread = 1000
        total_writes = num_threads * writes_per_thread
        
        print(f"\n开始并发写入测试: {num_threads} 线程, 每线程 {writes_per_thread} 次写入")
        
        def write_worker(thread_id: int):
            """写入工作线程"""
            success_count = 0
            for i in range(writes_per_thread):
                key = f"thread_{thread_id}_key_{i}".encode()
                value = f"value_{thread_id}_{i}".encode()
                success, _ = self.db.put(key, value)
                if success:
                    success_count += 1
            return success_count
        
        def concurrent_write_operation():
            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = [
                    executor.submit(write_worker, i)
                    for i in range(num_threads)
                ]
                return [f.result() for f in as_completed(futures)]
        
        # 并发写入（超时：10000次写入应在60秒内完成，即至少166条/秒）
        results = assert_performance_with_timeout(
            concurrent_write_operation,
            max_seconds=60.0,  # 60秒超时
            operation_name="并发写入",
            min_throughput=166.0,  # 至少166条/秒
            item_count=total_writes
        )
        
        total_success = sum(results)
        print(f"并发写入完成:")
        print(f"  成功写入: {total_success}/{total_writes}")
        
        self.assertGreater(total_success, total_writes * 0.95)  # 至少95%成功
    
    def test_concurrent_read_write(self):
        """并发读写测试"""
        num_readers = 5
        num_writers = 5
        operations_per_thread = 500
        
        print(f"\n开始并发读写测试: {num_readers} 读线程, {num_writers} 写线程")
        
        # 预先写入一些数据
        for i in range(100):
            self.db.put(f"pre_key_{i}".encode(), f"pre_value_{i}".encode())
        
        def read_worker(thread_id: int):
            """读取工作线程"""
            read_count = 0
            for i in range(operations_per_thread):
                key = f"pre_key_{i % 100}".encode()
                value = self.db.get(key)
                if value is not None:
                    read_count += 1
            return read_count
        
        def write_worker(thread_id: int):
            """写入工作线程"""
            write_count = 0
            for i in range(operations_per_thread):
                key = f"write_key_{thread_id}_{i}".encode()
                value = f"write_value_{thread_id}_{i}".encode()
                success, _ = self.db.put(key, value)
                if success:
                    write_count += 1
            return write_count
        
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=num_readers + num_writers) as executor:
            read_futures = [
                executor.submit(read_worker, i)
                for i in range(num_readers)
            ]
            write_futures = [
                executor.submit(write_worker, i)
                for i in range(num_writers)
            ]
            
            read_results = [f.result() for f in as_completed(read_futures)]
            write_results = [f.result() for f in as_completed(write_futures)]
        end_time = time.time()
        
        total_reads = sum(read_results)
        total_writes = sum(write_results)
        elapsed = end_time - start_time
        
        print(f"并发读写完成:")
        print(f"  总读取: {total_reads}")
        print(f"  总写入: {total_writes}")
        print(f"  总时间: {elapsed:.2f} 秒")
        print(f"  总操作: {(total_reads + total_writes) / elapsed:.2f} 操作/秒")
    
    def test_version_history_performance(self):
        """版本历史性能测试"""
        num_versions = 1000
        key = b"version_perf_test"
        
        print(f"\n开始版本历史测试: {num_versions} 个版本")
        
        start_time = time.time()
        for i in range(num_versions):
            self.db.put(key, f"value_{i}".encode())
        write_time = time.time() - start_time
        
        # 读取所有历史
        start_time = time.time()
        history = self.db.get_history(key)
        read_time = time.time() - start_time
        
        self.assertEqual(len(history), num_versions)
        
        print(f"版本历史测试完成:")
        print(f"  写入时间: {write_time:.2f} 秒")
        print(f"  读取历史时间: {read_time:.2f} 秒")
        print(f"  平均每版本: {write_time/num_versions*1000:.2f} 毫秒")
    
    def test_range_query_performance(self):
        """范围查询性能测试"""
        num_keys = 10000
        prefix = "range_test"
        
        print(f"\n开始范围查询测试: {num_keys} 个键")
        
        # 写入数据
        start_time = time.time()
        for i in range(num_keys):
            self.db.put(f"{prefix}_{i:05d}".encode(), f"value_{i}".encode())
        write_time = time.time() - start_time
        
        # 范围查询
        start_time = time.time()
        results = self.db.range_query(
            f"{prefix}_0100".encode(),
            f"{prefix}_0200".encode()
        )
        query_time = time.time() - start_time
        
        print(f"范围查询测试完成:")
        print(f"  写入时间: {write_time:.2f} 秒")
        print(f"  查询时间: {query_time:.2f} 秒")
        print(f"  结果数量: {len(results)}")
        print(f"  查询速度: {len(results)/query_time:.2f} 结果/秒")
    
    def test_merkle_proof_performance(self):
        """Merkle证明性能测试"""
        num_keys = 1000
        
        print(f"\n开始Merkle证明测试: {num_keys} 个键")
        
        # 写入数据
        keys = []
        for i in range(num_keys):
            key = f"merkle_key_{i}".encode()
            self.db.put(key, f"merkle_value_{i}".encode())
            keys.append(key)
        
        # 生成证明
        start_time = time.time()
        proofs = []
        for key in keys[:100]:  # 测试前100个
            value, proof, root = self.db.get_with_proof(key)
            proofs.append((key, value, proof))
        proof_time = time.time() - start_time
        
        # 验证证明
        start_time = time.time()
        valid_count = 0
        for key, value, proof in proofs:
            if self.db.verify(key, value, proof):
                valid_count += 1
        verify_time = time.time() - start_time
        
        print(f"Merkle证明测试完成:")
        print(f"  生成证明时间: {proof_time:.2f} 秒")
        print(f"  验证证明时间: {verify_time:.2f} 秒")
        print(f"  有效证明: {valid_count}/{len(proofs)}")
        print(f"  平均生成时间: {proof_time/len(proofs)*1000:.2f} 毫秒/证明")
        print(f"  平均验证时间: {verify_time/len(proofs)*1000:.2f} 毫秒/验证")


class BenchmarkTest(unittest.TestCase):
    """性能基准测试"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.db = Database(data_dir=os.path.join(self.temp_dir, "benchmark_db"))
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_write_benchmark(self):
        """写入性能基准"""
        sizes = [100, 1000, 10000]
        
        print("\n=== 写入性能基准测试 ===")
        for size in sizes:
            start_time = time.time()
            for i in range(size):
                self.db.put(f"bench_key_{i}".encode(), f"bench_value_{i}".encode())
            elapsed = time.time() - start_time
            throughput = size / elapsed
            print(f"{size:6d} 键: {elapsed:.3f}秒, {throughput:.2f} 键/秒")
    
    def test_read_benchmark(self):
        """读取性能基准"""
        # 预先写入
        for i in range(10000):
            self.db.put(f"read_key_{i}".encode(), f"read_value_{i}".encode())
        
        sizes = [100, 1000, 10000]
        
        print("\n=== 读取性能基准测试 ===")
        for size in sizes:
            start_time = time.time()
            for i in range(size):
                self.db.get(f"read_key_{i}".encode())
            elapsed = time.time() - start_time
            throughput = size / elapsed
            print(f"{size:6d} 读取: {elapsed:.3f}秒, {throughput:.2f} 读取/秒")


if __name__ == '__main__':
    # 运行压力测试
    print("=" * 60)
    print("AmDb 压力测试和性能基准")
    print("=" * 60)
    
    unittest.main(verbosity=2)

