"""
运行区块链场景压力测试
"""

import sys
import os
import unittest

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tests.test_blockchain_stress import BlockchainStressTest, LongTermBlockchainSimulation


def run_blockchain_stress_tests():
    """运行区块链压力测试"""
    print("=" * 80)
    print("AmDb 区块链场景压力测试套件")
    print("=" * 80)
    print("\n注意: 这些测试可能需要很长时间，特别是大规模数据测试")
    print("建议在性能较好的机器上运行，并确保有足够的磁盘空间\n")
    
    # 运行单元测试
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(BlockchainStressTest))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 询问是否运行长期模拟
    print("\n" + "=" * 80)
    print("长期区块链模拟")
    print("=" * 80)
    print("是否运行长期区块链模拟？(需要很长时间)")
    print("输入 'yes' 运行，其他任意键跳过")
    
    try:
        user_input = input().strip().lower()
        if user_input == 'yes':
            print("\n开始长期模拟...")
            sim = LongTermBlockchainSimulation()
            result = sim.simulate_years(years=1, blocks_per_day=7200)
            print("\n模拟完成！")
        else:
            print("跳过长期模拟")
    except KeyboardInterrupt:
        print("\n用户中断")
    except Exception as e:
        print(f"\n模拟出错: {e}")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_blockchain_stress_tests()
    sys.exit(0 if success else 1)

