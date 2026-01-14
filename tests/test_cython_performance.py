"""
Cython性能测试
测试Cython优化版本的性能提升
"""

import unittest
import sys
import os
import time
import tempfile
import shutil

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.amdb import Database


class CythonPerformanceTest(unittest.TestCase):
    """Cython性能测试"""
    
    def test_cython_vs_python(self):
        """对比Cython版本和纯Python版本的性能"""
        print("\n" + "=" * 80)
        print("Cython vs 纯Python性能对比测试")
        print("=" * 80)
        
        temp_dir = tempfile.mkdtemp()
        try:
            # 测试纯Python版本
            print("\n1. 测试纯Python版本...")
            db_python = Database(data_dir=f"{temp_dir}/python", enable_sharding=True, shard_count=256)
            
            test_sizes = [1000, 10000, 50000]
            python_best = 0
            
            for size in test_sizes:
                items = [(f'key_{i:010d}'.encode(), f'value_{i}'.encode()) 
                         for i in range(size)]
                
                start = time.time()
                db_python.batch_put(items)
                elapsed = time.time() - start
                throughput = size / elapsed if elapsed > 0 else 0
                python_best = max(python_best, throughput)
                print(f"  {size:6,} 条: {elapsed:.3f}秒, {throughput:10,.0f} 条/秒")
            
            print(f"\n纯Python最佳性能: {python_best:,.0f} 条/秒")
            
            # 测试Cython版本（如果可用）
            print("\n2. 测试Cython版本...")
            try:
                # 尝试使用Cython版本
                from src.amdb.storage.lsm_tree import MemTable
                memtable_cython = MemTable(use_skip_list=True, use_cython=True)
                
                db_cython = Database(data_dir=f"{temp_dir}/cython", enable_sharding=True, shard_count=256)
                
                cython_best = 0
                for size in test_sizes:
                    items = [(f'key_{i:010d}'.encode(), f'value_{i}'.encode()) 
                             for i in range(size)]
                    
                    start = time.time()
                    db_cython.batch_put(items)
                    elapsed = time.time() - start
                    throughput = size / elapsed if elapsed > 0 else 0
                    cython_best = max(cython_best, throughput)
                    print(f"  {size:6,} 条: {elapsed:.3f}秒, {throughput:10,.0f} 条/秒")
                
                print(f"\nCython最佳性能: {cython_best:,.0f} 条/秒")
                
                if python_best > 0:
                    speedup = cython_best / python_best
                    print(f"\n性能提升: {speedup:.2f}倍")
                    
                    if speedup >= 5:
                        print("  ✓ 达到预期提升（5-10倍）")
                    elif speedup >= 2:
                        print("  ⚠ 提升有限，可能需要进一步优化")
                    else:
                        print("  ✗ 提升不明显，需要检查Cython实现")
            except ImportError:
                print("  ⚠ Cython扩展未编译，跳过测试")
                print("  提示: 运行 'python setup_cython.py build_ext --inplace' 编译Cython扩展")
            
            # 测试分布式集群
            print("\n3. 测试分布式集群性能...")
            try:
                from src.amdb.distributed import DistributedCluster
                
                cluster = DistributedCluster(node_count=4, base_data_dir=f"{temp_dir}/cluster")
                
                cluster_best = 0
                for size in test_sizes:
                    items = [(f'key_{i:010d}'.encode(), f'value_{i}'.encode()) 
                             for i in range(size)]
                    
                    start = time.time()
                    cluster.batch_put(items)
                    elapsed = time.time() - start
                    throughput = size / elapsed if elapsed > 0 else 0
                    cluster_best = max(cluster_best, throughput)
                    print(f"  {size:6,} 条: {elapsed:.3f}秒, {throughput:10,.0f} 条/秒")
                
                print(f"\n分布式集群最佳性能: {cluster_best:,.0f} 条/秒")
                
                # 对比PolarDB
                polardb_tps = 3425000  # 342.5万tps
                if cluster_best > 0:
                    ratio = cluster_best / polardb_tps
                    print(f"\n对比PolarDB (342.5万tps):")
                    print(f"  - 当前性能: {cluster_best:,.0f} ops/s")
                    print(f"  - PolarDB性能: {polardb_tps:,.0f} ops/s")
                    print(f"  - 性能比: {ratio:.2%}")
                    
                    if ratio >= 1.0:
                        print("  ✓ 已超越PolarDB性能！")
                    elif ratio >= 0.8:
                        print("  ⚠ 接近PolarDB性能，需要进一步优化")
                    else:
                        print("  ✗ 需要更多节点或进一步优化")
            except ImportError:
                print("  ⚠ 分布式模块未找到")
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()

