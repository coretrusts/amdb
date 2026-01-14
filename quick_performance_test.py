# -*- coding: utf-8 -*-
"""
快速性能测试脚本
用于快速验证性能优化效果
"""

import sys
import time
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.amdb import Database
import shutil

def quick_test():
    """快速性能测试"""
    print("=" * 80)
    print("AmDb 快速性能测试")
    print("=" * 80)
    print()
    
    # 清理测试数据
    test_dir = './data/quick_perf_test'
    if Path(test_dir).exists():
        shutil.rmtree(test_dir)
    
    # 初始化数据库
    db = Database(data_dir=test_dir)
    print("✓ 数据库初始化完成")
    print()
    
    # 测试1: 顺序写入 (10,000条)
    print("测试1: 顺序写入 (10,000条)")
    print("-" * 80)
    count = 10000
    
    items = []
    for i in range(count):
        key = f"key{i:08d}".encode()
        value = f"value{i:08d}".encode()
        items.append((key, value))
    
    start = time.time()
    db.batch_put(items)
    write_time = time.time() - start
    
    start = time.time()
    db.flush()
    flush_time = time.time() - start
    
    total_time = write_time + flush_time
    ops_per_sec = count / total_time if total_time > 0 else 0
    
    print(f"批量写入时间: {write_time:.3f}秒")
    print(f"刷新时间: {flush_time:.3f}秒")
    print(f"总时间: {total_time:.3f}秒")
    print(f"写入速度: {ops_per_sec:,.0f} 条/秒")
    print(f"目标 (LevelDB): 550,000 条/秒")
    print(f"达成率: {(ops_per_sec / 550000) * 100:.1f}%")
    print()
    
    # 测试2: 随机读取 (1,000次)
    print("测试2: 随机读取 (1,000次)")
    print("-" * 80)
    import random
    
    all_keys = db.version_manager.get_all_keys()
    if all_keys:
        test_keys = random.sample(all_keys, min(1000, len(all_keys)))
        
        start = time.time()
        success = 0
        for key in test_keys:
            value = db.get(key)
            if value:
                success += 1
        read_time = time.time() - start
        
        ops_per_sec = len(test_keys) / read_time if read_time > 0 else 0
        
        print(f"读取时间: {read_time:.3f}秒")
        print(f"成功读取: {success}/{len(test_keys)}")
        print(f"读取速度: {ops_per_sec:,.0f} 次/秒")
        print(f"目标 (LevelDB): 156,000 次/秒")
        print(f"达成率: {(ops_per_sec / 156000) * 100:.1f}%")
        print()
    
    # 清理
    db.flush()
    print("=" * 80)
    print("测试完成")
    print("=" * 80)

if __name__ == "__main__":
    quick_test()

