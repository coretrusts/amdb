"""
生成测试数据
用于压力测试和性能基准
"""

import random
import string
import json
import os
from typing import List, Tuple


def generate_random_string(length: int = 10) -> str:
    """生成随机字符串"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_key_value_pairs(count: int, key_prefix: str = "key", 
                             value_size: int = 100) -> List[Tuple[bytes, bytes]]:
    """生成键值对列表"""
    pairs = []
    for i in range(count):
        key = f"{key_prefix}_{i:08d}".encode()
        value = generate_random_string(value_size).encode()
        pairs.append((key, value))
    return pairs


def generate_account_data(count: int) -> List[Tuple[bytes, bytes]]:
    """生成账户数据（模拟区块链场景）"""
    pairs = []
    for i in range(count):
        account_id = f"account:0x{i:040x}".encode()
        balance = str(random.randint(0, 1000000)).encode()
        pairs.append((account_id, balance))
    return pairs


def generate_transaction_data(count: int) -> List[Tuple[bytes, bytes]]:
    """生成交易数据"""
    pairs = []
    for i in range(count):
        tx_id = f"tx:{i:016d}".encode()
        tx_data = json.dumps({
            'from': f"0x{random.randint(0, 1000):040x}",
            'to': f"0x{random.randint(0, 1000):040x}",
            'amount': random.randint(1, 10000),
            'timestamp': random.randint(1000000000, 2000000000)
        }).encode()
        pairs.append((tx_id, tx_data))
    return pairs


def save_test_data(filename: str, data: List[Tuple[bytes, bytes]]):
    """保存测试数据到文件"""
    with open(filename, 'wb') as f:
        for key, value in data:
            f.write(struct.pack('I', len(key)))
            f.write(key)
            f.write(struct.pack('I', len(value)))
            f.write(value)


if __name__ == '__main__':
    import struct
    
    print("生成测试数据...")
    
    # 生成不同类型的数据
    os.makedirs("test_data", exist_ok=True)
    
    # 1. 基本键值对
    print("生成基本键值对数据...")
    basic_data = generate_key_value_pairs(10000, "basic", 100)
    save_test_data("test_data/basic_10k.dat", basic_data)
    
    # 2. 账户数据
    print("生成账户数据...")
    account_data = generate_account_data(5000)
    save_test_data("test_data/accounts_5k.dat", account_data)
    
    # 3. 交易数据
    print("生成交易数据...")
    tx_data = generate_transaction_data(10000)
    save_test_data("test_data/transactions_10k.dat", tx_data)
    
    print("测试数据生成完成！")
    print(f"  基本数据: {len(basic_data)} 条")
    print(f"  账户数据: {len(account_data)} 条")
    print(f"  交易数据: {len(tx_data)} 条")

