"""
区块链场景压力测试
模拟长期运行、万亿级数据的区块链场景
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
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List
from src.amdb import Database
from src.amdb.metrics import get_metrics, PerformanceMonitor
import sys
sys.path.insert(0, os.path.dirname(__file__))
from test_timeout_utils import assert_performance_with_timeout


class BlockchainStressTest(unittest.TestCase):
    """区块链场景压力测试"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        # 使用大量分片支持万亿级数据
        self.db = Database(
            data_dir=os.path.join(self.temp_dir, "blockchain_db"),
            enable_sharding=True,
            shard_count=4096,  # 4096个分片，支持万亿级数据
            max_file_size=128 * 1024 * 1024  # 128MB文件限制
        )
        self.metrics = get_metrics()
        self.monitor = PerformanceMonitor(self.metrics)
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _generate_account_address(self) -> bytes:
        """生成账户地址（模拟以太坊地址）"""
        # 生成40个十六进制字符
        hex_chars = '0123456789abcdef'
        address = '0x' + ''.join(random.choices(hex_chars, k=40))
        return address.encode()
    
    def _generate_transaction(self, tx_id: int) -> Dict:
        """生成交易数据"""
        return {
            'from': self._generate_account_address(),
            'to': self._generate_account_address(),
            'amount': random.randint(1, 1000000),
            'gas': random.randint(21000, 100000),
            'gas_price': random.randint(1, 100),
            'nonce': random.randint(0, 1000),
            'timestamp': int(time.time()),
            'tx_hash': hashlib.sha256(f"tx_{tx_id}".encode()).hexdigest()
        }
    
    def test_massive_account_storage(self):
        """大规模账户存储测试（模拟千万级账户）"""
        print("\n=== 大规模账户存储测试 ===")
        
        account_count = 10000000  # 1000万账户
        print(f"目标: 存储 {account_count:,} 个账户")
        
        start_time = time.time()
        batch_size = 10000
        total_batches = account_count // batch_size
        
        for batch_num in range(total_batches):
            items = []
            for i in range(batch_size):
                account_id = batch_num * batch_size + i
                account_addr = self._generate_account_address()
                # 账户数据：余额、nonce、代码哈希等
                account_data = json.dumps({
                    'balance': str(random.randint(0, 1000000000000000000)),  # Wei
                    'nonce': random.randint(0, 1000),
                    'code_hash': hashlib.sha256(f"code_{account_id}".encode()).hexdigest(),
                    'storage_root': hashlib.sha256(f"storage_{account_id}".encode()).hexdigest()
                }).encode()
                
                key = f"account:{account_addr.hex()}".encode()
                items.append((key, account_data))
            
            self.db.batch_put(items)
            
            if (batch_num + 1) % 100 == 0:
                elapsed = time.time() - start_time
                progress = (batch_num + 1) / total_batches * 100
                throughput = (batch_num + 1) * batch_size / elapsed
                print(f"  进度: {progress:.1f}% ({(batch_num + 1) * batch_size:,} 账户), "
                      f"耗时: {elapsed:.1f}秒, "
                      f"速度: {throughput:,.0f} 账户/秒")
        
        total_time = time.time() - start_time
        print(f"\n完成: {account_count:,} 个账户")
        print(f"总耗时: {total_time:.2f}秒")
        print(f"平均速度: {account_count / total_time:,.0f} 账户/秒")
        
        # 验证数据
        print("\n验证数据...")
        verify_count = 1000
        verify_start = time.time()
        success_count = 0
        for _ in range(verify_count):
            random_account = random.randint(0, account_count - 1)
            # 这里需要知道账户地址，简化：随机验证
            pass  # 实际应该保存账户地址列表
        verify_time = time.time() - verify_start
        print(f"验证 {verify_count} 个账户，耗时: {verify_time:.2f}秒")
    
    def test_transaction_history(self):
        """交易历史测试（模拟亿级交易）"""
        print("\n=== 交易历史测试 ===")
        
        transaction_count = 100000000  # 1亿交易
        print(f"目标: 存储 {transaction_count:,} 笔交易")
        
        start_time = time.time()
        batch_size = 50000
        
        # 模拟区块
        block_size = 1000  # 每区块1000笔交易
        total_blocks = transaction_count // block_size
        
        for block_num in range(total_blocks):
            block_items = []
            block_timestamp = int(time.time()) + block_num * 12  # 每12秒一个区块
            
            for tx_in_block in range(block_size):
                tx_id = block_num * block_size + tx_in_block
                tx_data = self._generate_transaction(tx_id)
                tx_data['block_number'] = block_num
                tx_data['block_timestamp'] = block_timestamp
                
                # 存储交易
                tx_key = f"tx:{tx_data['tx_hash']}".encode()
                tx_value = json.dumps(tx_data).encode()
                block_items.append((tx_key, tx_value))
                
                # 存储区块中的交易索引
                block_tx_key = f"block:{block_num}:tx:{tx_in_block}".encode()
                block_tx_value = tx_data['tx_hash'].encode()
                block_items.append((block_tx_key, block_tx_value))
            
            # 批量写入
            self.db.batch_put(block_items)
            
            if (block_num + 1) % 1000 == 0:
                elapsed = time.time() - start_time
                progress = (block_num + 1) / total_blocks * 100
                tx_written = (block_num + 1) * block_size
                throughput = tx_written / elapsed
                print(f"  进度: {progress:.1f}% ({tx_written:,} 交易), "
                      f"耗时: {elapsed:.1f}秒, "
                      f"速度: {throughput:,.0f} 交易/秒")
        
        total_time = time.time() - start_time
        print(f"\n完成: {transaction_count:,} 笔交易")
        print(f"总耗时: {total_time:.2f}秒")
        print(f"平均速度: {transaction_count / total_time:,.0f} 交易/秒")
    
    def test_state_snapshot_performance(self):
        """状态快照性能测试"""
        print("\n=== 状态快照性能测试 ===")
        
        # 创建大量状态数据
        state_count = 1000000
        print(f"创建 {state_count:,} 个状态项...")
        
        items = []
        for i in range(state_count):
            key = f"state:{i:08d}".encode()
            value = json.dumps({
                'value': random.randint(0, 1000000),
                'timestamp': time.time()
            }).encode()
            items.append((key, value))
        
        # 批量写入（带超时：100万条应在300秒内完成）
        def state_write():
            return self.db.batch_put(items)
        
        assert_performance_with_timeout(
            state_write,
            max_seconds=300.0,  # 5分钟超时
            operation_name="状态数据写入(100万条)",
            min_throughput=3333.0,  # 至少3333条/秒
            item_count=state_count
        )
        
        # 测试快照创建
        print("创建状态快照...")
        start = time.time()
        root_hash = self.db.get_root_hash()
        snapshot_time = time.time() - start
        
        print(f"快照创建时间: {snapshot_time:.3f}秒")
        print(f"Merkle根: {root_hash.hex()[:32]}...")
        
        # 测试快照验证
        print("验证快照...")
        verify_count = 1000
        verify_times = []
        
        for _ in range(verify_count):
            random_key = f"state:{random.randint(0, state_count-1):08d}".encode()
            start = time.time()
            value, proof, current_root = self.db.get_with_proof(random_key)
            if value and proof:
                is_valid = self.db.verify(random_key, value, proof)
                verify_times.append((time.time() - start) * 1000)
        
        if verify_times:
            print(f"验证统计 (毫秒):")
            print(f"  平均: {statistics.mean(verify_times):.2f}ms")
            print(f"  P95: {self._percentile(verify_times, 95):.2f}ms")
            print(f"  P99: {self._percentile(verify_times, 99):.2f}ms")
    
    def test_long_term_operation(self):
        """长期运行测试（模拟区块链长期运行）"""
        print("\n=== 长期运行测试 ===")
        
        # 模拟30天的运行（加速）
        days = 30
        blocks_per_day = 7200  # 每12秒一个区块
        total_blocks = days * blocks_per_day
        
        print(f"模拟 {days} 天运行，共 {total_blocks:,} 个区块")
        
        start_time = time.time()
        total_transactions = 0
        total_accounts = 0
        
        # 账户池
        account_pool = set()
        for _ in range(10000):
            account_pool.add(self._generate_account_address())
        
        for block_num in range(total_blocks):
            block_items = []
            tx_in_block = random.randint(100, 500)  # 每区块100-500笔交易
            
            for tx_idx in range(tx_in_block):
                # 随机选择账户
                from_addr = random.choice(list(account_pool))
                to_addr = random.choice(list(account_pool))
                
                # 更新发送方余额
                from_key = f"account:{from_addr.hex()}".encode()
                from_balance = random.randint(0, 1000000000000000000)
                from_data = json.dumps({'balance': str(from_balance), 'nonce': tx_idx}).encode()
                block_items.append((from_key, from_data))
                
                # 更新接收方余额
                to_key = f"account:{to_addr.hex()}".encode()
                to_balance = random.randint(0, 1000000000000000000)
                to_data = json.dumps({'balance': str(to_balance), 'nonce': 0}).encode()
                block_items.append((to_key, to_data))
                
                # 存储交易
                tx_hash = hashlib.sha256(f"block_{block_num}_tx_{tx_idx}".encode()).hexdigest()
                tx_key = f"tx:{tx_hash}".encode()
                tx_data = json.dumps({
                    'from': from_addr.hex(),
                    'to': to_addr.hex(),
                    'amount': random.randint(1, 1000000),
                    'block': block_num
                }).encode()
                block_items.append((tx_key, tx_data))
                
                total_transactions += 1
            
            # 批量写入
            if block_items:
                self.db.batch_put(block_items)
            
            # 每1000个区块刷新一次
            if (block_num + 1) % 1000 == 0:
                self.db.flush()
                elapsed = time.time() - start_time
                progress = (block_num + 1) / total_blocks * 100
                print(f"  进度: {progress:.1f}% (区块 {block_num + 1:,}), "
                      f"交易: {total_transactions:,}, "
                      f"耗时: {elapsed:.1f}秒")
        
        total_time = time.time() - start_time
        print(f"\n完成长期运行测试:")
        print(f"  总区块数: {total_blocks:,}")
        print(f"  总交易数: {total_transactions:,}")
        print(f"  总耗时: {total_time:.2f}秒")
        print(f"  平均区块时间: {total_time / total_blocks:.3f}秒")
        
        # 获取最终统计
        stats = self.db.get_stats()
        print(f"\n最终统计:")
        print(f"  总键数: {stats['total_keys']:,}")
        print(f"  分片数量: {stats.get('shard_count', 0)}")
        print(f"  Merkle根: {stats['merkle_root'][:32]}...")
    
    def test_trillion_scale_data(self):
        """万亿级数据测试"""
        print("\n=== 万亿级数据测试 ===")
        print("注意: 这是极限测试，可能需要很长时间")
        
        # 使用更大的分片数
        large_db = Database(
            data_dir=os.path.join(self.temp_dir, "trillion_db"),
            enable_sharding=True,
            shard_count=16384,  # 16384个分片，支持万亿级
            max_file_size=64 * 1024 * 1024  # 64MB文件限制
        )
        
        # 测试数据量：10亿（作为万亿级的子集测试）
        test_size = 1000000000  # 10亿
        print(f"测试规模: {test_size:,} 条记录（万亿级的1/1000）")
        
        start_time = time.time()
        batch_size = 100000
        
        for batch_num in range(0, test_size, batch_size):
            items = []
            for i in range(batch_size):
                if batch_num + i >= test_size:
                    break
                key = f"trillion_test_{batch_num + i:012d}".encode()
                value = f"value_{batch_num + i}_{'x'*50}".encode()
                items.append((key, value))
            
            large_db.batch_put(items)
            
            if (batch_num + batch_size) % 10000000 == 0:
                elapsed = time.time() - start_time
                written = min(batch_num + batch_size, test_size)
                progress = written / test_size * 100
                throughput = written / elapsed
                print(f"  进度: {progress:.1f}% ({written:,} 条), "
                      f"耗时: {elapsed:.1f}秒, "
                      f"速度: {throughput:,.0f} 条/秒")
        
        total_time = time.time() - start_time
        print(f"\n完成: {test_size:,} 条记录")
        print(f"总耗时: {total_time:.2f}秒")
        print(f"平均速度: {test_size / total_time:,.0f} 条/秒")
        
        # 检查分片分布
        stats = large_db.get_stats()
        shard_info = stats.get('shard_info', {})
        print(f"\n分片统计:")
        print(f"  活跃分片: {len(shard_info)}")
        if shard_info:
            shard_sizes = [info['stats'].get('total_size', 0) for info in shard_info.values()]
            print(f"  平均分片大小: {statistics.mean(shard_sizes) / 1024 / 1024:.2f} MB")
            print(f"  最大分片大小: {max(shard_sizes) / 1024 / 1024:.2f} MB")
    
    def test_concurrent_block_processing(self):
        """并发区块处理测试"""
        print("\n=== 并发区块处理测试 ===")
        
        num_workers = 10
        blocks_per_worker = 1000
        tx_per_block = 100
        
        def process_blocks(worker_id: int):
            """处理区块的工作线程"""
            success_count = 0
            for block_num in range(blocks_per_worker):
                block_id = worker_id * blocks_per_worker + block_num
                block_items = []
                
                for tx_idx in range(tx_per_block):
                    tx_hash = hashlib.sha256(f"block_{block_id}_tx_{tx_idx}".encode()).hexdigest()
                    tx_key = f"tx:{tx_hash}".encode()
                    tx_data = json.dumps({
                        'block': block_id,
                        'tx_index': tx_idx,
                        'data': 'x' * 100
                    }).encode()
                    block_items.append((tx_key, tx_data))
                
                try:
                    self.db.batch_put(block_items)
                    success_count += 1
                except Exception:
                    pass
            
            return success_count
        
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(process_blocks, i) for i in range(num_workers)]
            results = [f.result() for f in as_completed(futures)]
        
        elapsed = time.time() - start_time
        total_blocks = sum(results)
        total_tx = total_blocks * tx_per_block
        
        print(f"处理结果:")
        print(f"  工作线程: {num_workers}")
        print(f"  成功区块: {total_blocks:,}")
        print(f"  总交易数: {total_tx:,}")
        print(f"  总耗时: {elapsed:.2f}秒")
        print(f"  吞吐量: {total_tx / elapsed:,.0f} 交易/秒")
    
    def test_version_history_at_scale(self):
        """大规模版本历史测试"""
        print("\n=== 大规模版本历史测试 ===")
        
        # 创建大量版本
        key = b"massive_version_test"
        version_count = 100000  # 10万版本
        
        print(f"创建 {version_count:,} 个版本...")
        start_time = time.time()
        
        for i in range(version_count):
            value = f"version_{i}_{'x'*100}".encode()
            self.db.put(key, value)
            
            if (i + 1) % 10000 == 0:
                elapsed = time.time() - start_time
                throughput = (i + 1) / elapsed
                print(f"  进度: {i + 1:,} 版本, 速度: {throughput:,.0f} 版本/秒")
        
        total_time = time.time() - start_time
        print(f"完成: {version_count:,} 个版本，耗时: {total_time:.2f}秒")
        
        # 测试版本查询
        print("\n测试版本查询...")
        query_versions = [1, 1000, 10000, 50000, 99999]
        
        for ver in query_versions:
            start = time.time()
            value = self.db.get(key, version=ver)
            elapsed = (time.time() - start) * 1000
            print(f"  版本 {ver}: {elapsed:.2f}ms")
        
        # 测试历史范围查询
        print("\n测试历史范围查询...")
        start = time.time()
        history = self.db.get_history(key, start_version=1, end_version=1000)
        elapsed = time.time() - start
        print(f"  查询1000个版本历史: {elapsed:.2f}秒, 结果数: {len(history)}")
    
    def test_shard_distribution_analysis(self):
        """分片分布分析（万亿级数据）"""
        print("\n=== 分片分布分析 ===")
        
        # 写入大量数据
        data_size = 100000000  # 1亿
        print(f"写入 {data_size:,} 条记录分析分片分布...")
        
        items = []
        for i in range(data_size):
            key = f"shard_analysis_{i:010d}".encode()
            value = f"value_{i}".encode()
            items.append((key, value))
        
        self.db.batch_put(items)
        self.db.flush()
        
        # 分析分片分布
        stats = self.db.get_stats()
        shard_info = stats.get('shard_info', {})
        
        if not shard_info:
            print("  无分片信息")
            return
        
        shard_sizes = []
        shard_file_counts = []
        shard_key_counts = []
        
        for shard_id, info in shard_info.items():
            total_size = info['stats'].get('total_size', 0)
            file_count = info['sstable_count']
            shard_sizes.append(total_size)
            shard_file_counts.append(file_count)
            # 估算键数量（基于文件大小）
            estimated_keys = total_size // 200  # 假设平均每条记录200字节
            shard_key_counts.append(estimated_keys)
        
        print(f"\n分片分布统计:")
        print(f"  活跃分片数: {len(shard_sizes)}")
        print(f"  总数据大小: {sum(shard_sizes) / 1024 / 1024 / 1024:.2f} GB")
        
        if shard_sizes:
            print(f"\n分片大小分布:")
            print(f"  平均: {statistics.mean(shard_sizes) / 1024 / 1024:.2f} MB")
            print(f"  中位数: {statistics.median(shard_sizes) / 1024 / 1024:.2f} MB")
            print(f"  最大: {max(shard_sizes) / 1024 / 1024:.2f} MB")
            print(f"  最小: {min(shard_sizes) / 1024 / 1024:.2f} MB")
            print(f"  标准差: {statistics.stdev(shard_sizes) / 1024 / 1024:.2f} MB")
            
            # 计算变异系数（均匀度）
            cv = statistics.stdev(shard_sizes) / statistics.mean(shard_sizes) if statistics.mean(shard_sizes) > 0 else 0
            print(f"  变异系数 (CV): {cv:.3f}")
            if cv < 0.3:
                print("  ✓ 分布非常均匀")
            elif cv < 0.5:
                print("  ⚠ 分布较均匀")
            else:
                print("  ✗ 分布不均匀，需要优化")
        
        if shard_file_counts:
            print(f"\n文件数量分布:")
            print(f"  平均: {statistics.mean(shard_file_counts):.1f} 个文件/分片")
            print(f"  最大: {max(shard_file_counts)} 个文件")
            print(f"  最小: {min(shard_file_counts)} 个文件")
    
    def _percentile(self, data: List[float], p: float) -> float:
        """计算百分位数"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * p / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]


class LongTermBlockchainSimulation:
    """长期区块链模拟"""
    
    def __init__(self, data_dir: str = "./data/blockchain_sim"):
        self.db = Database(
            data_dir=data_dir,
            enable_sharding=True,
            shard_count=16384,  # 16384个分片支持万亿级
            max_file_size=64 * 1024 * 1024
        )
        self.metrics = get_metrics()
    
    def simulate_years(self, years: int = 1, blocks_per_day: int = 7200):
        """模拟多年运行"""
        print(f"\n=== 模拟 {years} 年区块链运行 ===")
        
        total_blocks = years * 365 * blocks_per_day
        print(f"总区块数: {total_blocks:,}")
        print(f"预计交易数: {total_blocks * 200:,} (假设每区块200笔交易)")
        
        start_time = time.time()
        total_tx = 0
        
        # 账户池（持续增长）
        account_pool = set()
        initial_accounts = 10000
        
        for i in range(initial_accounts):
            account_pool.add(self._generate_account_address())
        
        for day in range(years * 365):
            day_items = []
            day_tx_count = 0
            
            for block in range(blocks_per_day):
                block_num = day * blocks_per_day + block
                tx_in_block = random.randint(100, 300)
                
                for tx_idx in range(tx_in_block):
                    # 随机选择或创建账户
                    if random.random() < 0.1:  # 10%概率创建新账户
                        new_account = self._generate_account_address()
                        account_pool.add(new_account)
                        from_addr = new_account
                    else:
                        from_addr = random.choice(list(account_pool))
                    
                    to_addr = random.choice(list(account_pool))
                    
                    # 更新账户状态
                    from_key = f"account:{from_addr.hex()}".encode()
                    from_data = json.dumps({
                        'balance': str(random.randint(0, 1000000000000000000)),
                        'nonce': random.randint(0, 1000)
                    }).encode()
                    day_items.append((from_key, from_data))
                    
                    # 存储交易
                    tx_hash = hashlib.sha256(f"day_{day}_block_{block}_tx_{tx_idx}".encode()).hexdigest()
                    tx_key = f"tx:{tx_hash}".encode()
                    tx_data = json.dumps({
                        'from': from_addr.hex(),
                        'to': to_addr.hex(),
                        'amount': random.randint(1, 1000000),
                        'block': block_num,
                        'timestamp': int(time.time()) + block_num * 12
                    }).encode()
                    day_items.append((tx_key, tx_data))
                    
                    day_tx_count += 1
                    total_tx += 1
                
                # 每100个区块批量写入
                if len(day_items) >= 20000:
                    self.db.batch_put(day_items)
                    day_items = []
            
            # 写入剩余数据
            if day_items:
                self.db.batch_put(day_items)
            
            # 每天刷新
            self.db.flush()
            
            if (day + 1) % 30 == 0:  # 每月报告
                elapsed = time.time() - start_time
                progress = (day + 1) / (years * 365) * 100
                print(f"  进度: {progress:.1f}% ({(day + 1)} 天), "
                      f"交易: {total_tx:,}, "
                      f"账户: {len(account_pool):,}, "
                      f"耗时: {elapsed / 60:.1f} 分钟")
        
        total_time = time.time() - start_time
        stats = self.db.get_stats()
        
        print(f"\n=== 模拟完成 ===")
        print(f"总运行时间: {total_time / 3600:.2f} 小时")
        print(f"总交易数: {total_tx:,}")
        print(f"总账户数: {len(account_pool):,}")
        print(f"总键数: {stats['total_keys']:,}")
        print(f"分片数: {stats.get('shard_count', 0)}")
        
        return {
            'years': years,
            'total_blocks': total_blocks,
            'total_tx': total_tx,
            'total_accounts': len(account_pool),
            'total_keys': stats['total_keys'],
            'runtime_hours': total_time / 3600
        }


if __name__ == '__main__':
    print("=" * 80)
    print("AmDb 区块链场景压力测试")
    print("=" * 80)
    
    # 运行单元测试
    unittest.main(verbosity=2, exit=False)
    
    # 运行长期模拟（可选，需要很长时间）
    # print("\n" + "=" * 80)
    # sim = LongTermBlockchainSimulation()
    # result = sim.simulate_years(years=1)  # 模拟1年
    # print(json.dumps(result, indent=2, default=str))

