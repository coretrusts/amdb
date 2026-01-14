"""
运行所有测试
"""

import unittest
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tests.test_basic import TestDatabaseBasic
from tests.test_stress import StressTest, BenchmarkTest
from tests.test_network import TestNetwork


def run_all_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestDatabaseBasic))
    suite.addTests(loader.loadTestsFromTestCase(StressTest))
    suite.addTests(loader.loadTestsFromTestCase(BenchmarkTest))
    suite.addTests(loader.loadTestsFromTestCase(TestNetwork))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 返回结果
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)

