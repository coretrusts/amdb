"""
运行所有压力测试
"""

import sys
import os
import unittest

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tests.test_stress import StressTest, BenchmarkTest
from tests.test_comprehensive_stress import ComprehensiveStressTest
from tests.benchmark_comprehensive import ComprehensiveBenchmark


def run_all_stress_tests():
    """运行所有压力测试"""
    print("=" * 80)
    print("AmDb 完整压力测试套件")
    print("=" * 80)
    
    # 运行基础压力测试
    print("\n1. 运行基础压力测试...")
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(StressTest))
    suite.addTests(loader.loadTestsFromTestCase(BenchmarkTest))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 运行全面压力测试
    print("\n2. 运行全面压力测试...")
    suite2 = unittest.TestSuite()
    suite2.addTests(loader.loadTestsFromTestCase(ComprehensiveStressTest))
    result2 = runner.run(suite2)
    
    # 运行完整基准测试
    print("\n3. 运行完整基准测试...")
    benchmark = ComprehensiveBenchmark()
    try:
        benchmark.run_all()
    finally:
        benchmark.cleanup()
    
    # 总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    print(f"基础压力测试: {'通过' if result.wasSuccessful() else '失败'}")
    print(f"全面压力测试: {'通过' if result2.wasSuccessful() else '失败'}")
    print(f"基准测试: 完成")
    
    return result.wasSuccessful() and result2.wasSuccessful()


if __name__ == '__main__':
    success = run_all_stress_tests()
    sys.exit(0 if success else 1)

