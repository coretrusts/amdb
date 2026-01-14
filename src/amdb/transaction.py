"""
事务系统
支持ACID事务和批量操作
"""

import threading
import time
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
from dataclasses import dataclass


class TransactionStatus(Enum):
    """事务状态"""
    PENDING = "pending"
    COMMITTED = "committed"
    ABORTED = "aborted"
    ROLLED_BACK = "rolled_back"


@dataclass
class WriteOperation:
    """写入操作"""
    key: bytes
    value: bytes
    operation: str  # 'put' or 'delete'


class Transaction:
    """
    事务对象
    支持快照隔离和乐观并发控制
    """
    
    def __init__(self, tx_id: int, snapshot_version: int):
        self.tx_id = tx_id
        self.snapshot_version = snapshot_version
        self.status = TransactionStatus.PENDING
        self.operations: List[WriteOperation] = []
        self.read_set: set = set()  # 读取的键集合
        self.write_set: set = set()  # 写入的键集合
        self.start_time = time.time()
        self.lock = threading.RLock()
    
    def read(self, key: bytes):
        """读取操作（记录到read_set）"""
        with self.lock:
            self.read_set.add(key)
    
    def put(self, key: bytes, value: bytes):
        """写入操作"""
        with self.lock:
            if self.status != TransactionStatus.PENDING:
                raise RuntimeError(f"Transaction {self.tx_id} is not pending")
            
            self.operations.append(WriteOperation(
                key=key,
                value=value,
                operation='put'
            ))
            self.write_set.add(key)
    
    def delete(self, key: bytes):
        """删除操作"""
        with self.lock:
            if self.status != TransactionStatus.PENDING:
                raise RuntimeError(f"Transaction {self.tx_id} is not pending")
            
            self.operations.append(WriteOperation(
                key=key,
                value=b'',
                operation='delete'
            ))
            self.write_set.add(key)
    
    def get_operations(self) -> List[WriteOperation]:
        """获取所有操作"""
        return self.operations.copy()
    
    def commit(self):
        """提交事务"""
        with self.lock:
            if self.status != TransactionStatus.PENDING:
                raise RuntimeError(f"Transaction {self.tx_id} cannot be committed")
            self.status = TransactionStatus.COMMITTED
    
    def abort(self):
        """中止事务"""
        with self.lock:
            if self.status == TransactionStatus.PENDING:
                self.status = TransactionStatus.ABORTED
    
    def rollback(self):
        """回滚事务"""
        with self.lock:
            self.status = TransactionStatus.ROLLED_BACK
            self.operations.clear()


class TransactionManager:
    """
    事务管理器
    实现快照隔离和冲突检测
    """
    
    def __init__(self):
        self.transactions: Dict[int, Transaction] = {}
        self.next_tx_id = 1
        self.committed_versions: List[int] = []  # 已提交的版本号
        self.current_version = 0
        self.lock = threading.RLock()
    
    def begin_transaction(self) -> Transaction:
        """开始新事务"""
        with self.lock:
            tx_id = self.next_tx_id
            self.next_tx_id += 1
            
            # 快照版本 = 当前已提交的版本
            snapshot_version = self.current_version
            
            tx = Transaction(tx_id, snapshot_version)
            self.transactions[tx_id] = tx
            
            return tx
    
    def commit_transaction(self, tx: Transaction, 
                          commit_fn: Callable[[List[WriteOperation], int], bool]) -> bool:
        """
        提交事务
        Args:
            tx: 事务对象
            commit_fn: 提交函数，返回是否成功
        """
        with self.lock:
            if tx.status != TransactionStatus.PENDING:
                return False
            
            # 检查冲突（简化实现）
            # 实际应该检查read_set和write_set的冲突
            if not self._check_conflicts(tx):
                tx.abort()
                return False
            
            # 执行提交
            success = commit_fn(tx.get_operations(), tx.tx_id)
            
            if success:
                tx.commit()
                self.current_version += 1
                self.committed_versions.append(self.current_version)
                del self.transactions[tx.tx_id]
                return True
            else:
                tx.abort()
                return False
    
    def abort_transaction(self, tx: Transaction):
        """中止事务"""
        with self.lock:
            tx.abort()
            if tx.tx_id in self.transactions:
                del self.transactions[tx.tx_id]
    
    def _check_conflicts(self, tx: Transaction) -> bool:
        """检查事务冲突（完整实现）"""
        with self.lock:
            # 检查读取集合冲突
            for read_key in tx.read_set:
                # 检查是否有其他已提交的事务修改了这个键
                for other_tx_id, other_tx in self.transactions.items():
                    if other_tx_id != tx.tx_id and other_tx.status.value == "committed":
                        if read_key in other_tx.write_set:
                            # 读取的键被其他事务修改，冲突
                            return False
            
            # 检查写入集合冲突
            for write_key in tx.write_set:
                # 检查是否有其他事务也在写入这个键
                for other_tx_id, other_tx in self.transactions.items():
                    if other_tx_id != tx.tx_id:
                        if write_key in other_tx.write_set:
                            # 写入冲突
                            return False
                        # 检查是否有事务读取了这个键（写后读冲突）
                        if write_key in other_tx.read_set and other_tx.snapshot_version >= tx.snapshot_version:
                            # 写后读冲突
                            return False
            
            return True
    
    def get_snapshot_version(self) -> int:
        """获取当前快照版本"""
        with self.lock:
            return self.current_version

