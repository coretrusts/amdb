"""
运行所有多语言绑定测试
"""

import sys
import os
import unittest
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tests.test_bindings import BindingsTest, BindingCompilationTest, BindingIntegrationTest
from tests.test_bindings_integration import BindingIntegrationTest as IntegrationTest


def run_all_binding_tests():
    """运行所有绑定测试"""
    print("=" * 80)
    print("AmDb 多语言绑定完整测试套件")
    print("=" * 80)
    print()
    
    # 运行绑定文件存在性测试
    print("1. 绑定文件存在性测试...")
    loader = unittest.TestLoader()
    suite1 = unittest.TestSuite()
    suite1.addTests(loader.loadTestsFromTestCase(BindingsTest))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result1 = runner.run(suite1)
    
    # 运行绑定编译测试
    print("\n2. 绑定编译测试...")
    suite2 = unittest.TestSuite()
    suite2.addTests(loader.loadTestsFromTestCase(BindingCompilationTest))
    result2 = runner.run(suite2)
    
    # 运行绑定集成测试
    print("\n3. 绑定集成测试...")
    suite3 = unittest.TestSuite()
    suite3.addTests(loader.loadTestsFromTestCase(IntegrationTest))
    result3 = runner.run(suite3)
    
    # 总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    print(f"绑定文件测试: {'通过' if result1.wasSuccessful() else '失败'}")
    print(f"绑定编译测试: {'通过' if result2.wasSuccessful() else '失败'}")
    print(f"绑定集成测试: {'通过' if result3.wasSuccessful() else '失败'}")
    
    all_success = result1.wasSuccessful() and result2.wasSuccessful() and result3.wasSuccessful()
    
    if all_success:
        print("\n✓ 所有绑定测试通过！")
    else:
        print("\n⚠ 部分测试失败，请检查报告")
    
    return all_success


if __name__ == '__main__':
    success = run_all_binding_tests()
    sys.exit(0 if success else 1)

