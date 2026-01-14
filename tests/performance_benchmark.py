# -*- coding: utf-8 -*-
"""
AmDb 性能基准测试
对标LevelDB和PolarDB的性能指标
"""

import sys
import time
import statistics
from pathlib import Path
from typing import List, Tuple, Dict
import random
import threading

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.amdb import Database


class PerformanceBenchmark:
    """性能基准测试类"""
    
    def __init__(self, data_dir: str = './data/benchmark_test'):
        self.data_dir = data_dir
        self.db = None
        self.results = {}
    
    def setup(self):
        """初始化数据库"""
        import shutil
        if Path(self.data_dir).exists():
            shutil.rmtree(self.data_dir)
        
        self.db = Database(data_dir=self.data_dir)
        print(f"✓ 数据库初始化完成: {self.data_dir}")
    
    def cleanup(self):
        """清理"""
        if self.db:
            self.db.flush()
            self.db = None
    
    def test_sequential_write(self, count: int = 100000) -> Dict:
        """测试顺序写入性能（对标LevelDB: 550k/s）"""
        print(f"\n{'='*80}")
        print(f"测试顺序写入性能 ({count:,} 条记录)")
        print(f"{'='*80}")
        
        start_time = time.time()
        
        # 批量写入
        items = []
        for i in range(count):
            key = f"key{i:08d}".encode()
            value = f"value{i:08d}".encode()
            items.append((key, value))
        
        # 执行批量写入
        batch_start = time.time()
        success, _ = self.db.batch_put(items)
        batch_time = time.time() - batch_start
        
        # 刷新到磁盘
        flush_start = time.time()
        self.db.flush()
        flush_time = time.time() - flush_start
        
        total_time = time.time() - start_time
        
        ops_per_sec = count / total_time if total_time > 0 else 0
        batch_ops_per_sec = count / batch_time if batch_time > 0 else 0
        
        result = {
            'test': 'sequential_write',
            'count': count,
            'total_time': total_time,
            'batch_time': batch_time,
            'flush_time': flush_time,
            'ops_per_sec': ops_per_sec,
            'batch_ops_per_sec': batch_ops_per_sec,
            'target': 550000,  # LevelDB目标
            'percentage': (ops_per_sec / 550000) * 100 if ops_per_sec > 0 else 0
        }
        
        print(f"总时间: {total_time:.2f}秒")
        print(f"批量写入时间: {batch_time:.2f}秒")
        print(f"刷新时间: {flush_time:.2f}秒")
        print(f"写入速度: {ops_per_sec:,.0f} 条/秒")
        print(f"批量写入速度: {batch_ops_per_sec:,.0f} 条/秒")
        print(f"目标 (LevelDB): 550,000 条/秒")
        print(f"达成率: {result['percentage']:.1f}%")
        
        return result
    
    def test_random_write(self, count: int = 10000) -> Dict:
        """测试随机写入性能（对标LevelDB: 52k/s）"""
        print(f"\n{'='*80}")
        print(f"测试随机写入性能 ({count:,} 条记录)")
        print(f"{'='*80}")
        
        start_time = time.time()
        
        # 随机写入
        items = []
        for i in range(count):
            key = f"rand{random.randint(0, count*10):08d}".encode()
            value = f"value{random.randint(0, count*10):08d}".encode()
            items.append((key, value))
        
        batch_start = time.time()
        success, _ = self.db.batch_put(items)
        batch_time = time.time() - batch_start
        
        flush_start = time.time()
        self.db.flush()
        flush_time = time.time() - flush_start
        
        total_time = time.time() - start_time
        ops_per_sec = count / total_time if total_time > 0 else 0
        
        result = {
            'test': 'random_write',
            'count': count,
            'total_time': total_time,
            'batch_time': batch_time,
            'flush_time': flush_time,
            'ops_per_sec': ops_per_sec,
            'target': 52000,  # LevelDB目标
            'percentage': (ops_per_sec / 52000) * 100 if ops_per_sec > 0 else 0
        }
        
        print(f"总时间: {total_time:.2f}秒")
        print(f"写入速度: {ops_per_sec:,.0f} 条/秒")
        print(f"目标 (LevelDB): 52,000 条/秒")
        print(f"达成率: {result['percentage']:.1f}%")
        
        return result
    
    def test_random_read(self, count: int = 100000) -> Dict:
        """测试随机读取性能（对标LevelDB: 156k/s）"""
        print(f"\n{'='*80}")
        print(f"测试随机读取性能 ({count:,} 次读取)")
        print(f"{'='*80}")
        
        # 先获取所有键
        all_keys = self.db.version_manager.get_all_keys()
        if not all_keys:
            print("✗ 数据库为空，无法进行读取测试")
            return {'test': 'random_read', 'error': 'database_empty'}
        
        # 随机选择键
        test_keys = random.sample(all_keys, min(count, len(all_keys)))
        
        start_time = time.time()
        success_count = 0
        
        for key in test_keys:
            value = self.db.get(key)
            if value:
                success_count += 1
        
        total_time = time.time() - start_time
        ops_per_sec = len(test_keys) / total_time if total_time > 0 else 0
        
        result = {
            'test': 'random_read',
            'count': len(test_keys),
            'success_count': success_count,
            'total_time': total_time,
            'ops_per_sec': ops_per_sec,
            'target': 156000,  # LevelDB目标
            'percentage': (ops_per_sec / 156000) * 100 if ops_per_sec > 0 else 0
        }
        
        print(f"总时间: {total_time:.2f}秒")
        print(f"成功读取: {success_count}/{len(test_keys)}")
        print(f"读取速度: {ops_per_sec:,.0f} 次/秒")
        print(f"目标 (LevelDB): 156,000 次/秒")
        print(f"达成率: {result['percentage']:.1f}%")
        
        return result
    
    def test_concurrent_write(self, threads: int = 4, count_per_thread: int = 10000) -> Dict:
        """测试并发写入性能"""
        print(f"\n{'='*80}")
        print(f"测试并发写入性能 ({threads} 线程, 每线程 {count_per_thread:,} 条)")
        print(f"{'='*80}")
        
        def write_thread(thread_id: int):
            items = []
            for i in range(count_per_thread):
                key = f"thread{thread_id}_key{i:08d}".encode()
                value = f"thread{thread_id}_value{i:08d}".encode()
                items.append((key, value))
            
            self.db.batch_put(items)
            return len(items)
        
        start_time = time.time()
        
        thread_list = []
        for i in range(threads):
            t = threading.Thread(target=write_thread, args=(i,))
            thread_list.append(t)
            t.start()
        
        for t in thread_list:
            t.join()
        
        self.db.flush()
        total_time = time.time() - start_time
        
        total_count = threads * count_per_thread
        ops_per_sec = total_count / total_time if total_time > 0 else 0
        
        result = {
            'test': 'concurrent_write',
            'threads': threads,
            'count_per_thread': count_per_thread,
            'total_count': total_count,
            'total_time': total_time,
            'ops_per_sec': ops_per_sec
        }
        
        print(f"总时间: {total_time:.2f}秒")
        print(f"总写入: {total_count:,} 条")
        print(f"写入速度: {ops_per_sec:,.0f} 条/秒")
        
        return result
    
    def test_tpcc_like(self, transactions: int = 10000) -> Dict:
        """测试TPC-C类似性能（对标PolarDB: 2.055亿 tpmC）"""
        print(f"\n{'='*80}")
        print(f"测试TPC-C类似性能 ({transactions:,} 事务)")
        print(f"{'='*80}")
        
        start_time = time.time()
        
        # 模拟事务操作
        for i in range(transactions):
            # 模拟多个操作
            items = []
            for j in range(10):  # 每个事务10个操作
                key = f"tx{i:08d}_op{j:02d}".encode()
                value = f"transaction_data_{i}_{j}".encode()
                items.append((key, value))
            
            self.db.batch_put(items)
        
        self.db.flush()
        total_time = time.time() - start_time
        
        # 计算tpmC (transactions per minute)
        tpmc = (transactions / total_time) * 60 if total_time > 0 else 0
        
        result = {
            'test': 'tpcc_like',
            'transactions': transactions,
            'total_time': total_time,
            'tpmc': tpmc,
            'target': 2055000000,  # PolarDB目标 (2.055亿)
            'percentage': (tpmc / 2055000000) * 100 if tpmc > 0 else 0
        }
        
        print(f"总时间: {total_time:.2f}秒")
        print(f"事务数: {transactions:,}")
        print(f"tpmC: {tpmc:,.0f}")
        print(f"目标 (PolarDB): 2,055,000,000 tpmC")
        print(f"达成率: {result['percentage']:.6f}%")
        
        return result
    
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 80)
        print("AmDb 性能基准测试")
        print("=" * 80)
        print()
        
        self.setup()
        
        try:
            # 1. 顺序写入测试
            self.results['sequential_write'] = self.test_sequential_write(100000)
            
            # 2. 随机写入测试
            self.results['random_write'] = self.test_random_write(10000)
            
            # 3. 随机读取测试
            self.results['random_read'] = self.test_random_read(100000)
            
            # 4. 并发写入测试
            self.results['concurrent_write'] = self.test_concurrent_write(4, 10000)
            
            # 5. TPC-C类似测试
            self.results['tpcc_like'] = self.test_tpcc_like(10000)
            
            # 打印总结
            self.print_summary()
            
        finally:
            self.cleanup()
    
    def print_summary(self):
        """打印测试总结"""
        print("\n" + "=" * 80)
        print("测试总结")
        print("=" * 80)
        print()
        
        print(f"{'测试项目':<20} {'性能':<15} {'目标':<15} {'达成率':<10}")
        print("-" * 80)
        
        for test_name, result in self.results.items():
            if 'error' in result:
                continue
            
            if 'ops_per_sec' in result:
                perf = f"{result['ops_per_sec']:,.0f} ops/s"
                target = f"{result.get('target', 0):,.0f} ops/s"
                pct = f"{result.get('percentage', 0):.1f}%"
            elif 'tpmc' in result:
                perf = f"{result['tpmc']:,.0f} tpmC"
                target = f"{result.get('target', 0):,.0f} tpmC"
                pct = f"{result.get('percentage', 0):.6f}%"
            else:
                continue
            
            print(f"{test_name:<20} {perf:<15} {target:<15} {pct:<10}")
        
        print("=" * 80)


def main():
    """主函数"""
    benchmark = PerformanceBenchmark()
    benchmark.run_all_tests()


if __name__ == "__main__":
    main()

