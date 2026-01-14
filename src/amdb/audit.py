"""
操作审计日志模块
专门为区块链应用设计，记录所有操作，确保不可篡改
"""

import time
import hashlib
import json
import threading
from typing import List, Dict, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum


class OperationType(Enum):
    """操作类型"""
    PUT = "put"
    GET = "get"
    DELETE = "delete"
    BATCH_PUT = "batch_put"
    TRANSACTION = "transaction"
    BACKUP = "backup"
    RESTORE = "restore"
    CONFIG_CHANGE = "config_change"


@dataclass
class AuditLogEntry:
    """审计日志条目"""
    timestamp: float
    operation: str
    operator: Optional[str] = None  # 操作者（节点ID或用户）
    key: Optional[bytes] = None
    value_hash: Optional[str] = None  # 值的哈希（不存储实际值）
    success: bool = True
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    prev_hash: Optional[str] = None  # 前一个日志条目的哈希（形成链）
    hash: Optional[str] = None  # 当前条目的哈希
    
    def compute_hash(self) -> str:
        """计算日志条目哈希（确保不可篡改）"""
        content = (
            str(self.timestamp) +
            self.operation +
            (self.operator or "") +
            (self.key.hex() if self.key else "") +
            (self.value_hash or "") +
            str(self.success) +
            (self.error or "") +
            json.dumps(self.metadata or {}, sort_keys=True) +
            (self.prev_hash or "")
        )
        return hashlib.sha256(content.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        if self.key:
            result['key'] = self.key.hex()
        return result


class AuditLogger:
    """审计日志记录器（区块链优化版本）"""
    
    def __init__(self, audit_dir: str = "./audit_logs"):
        """
        Args:
            audit_dir: 审计日志目录
        """
        self.audit_dir = Path(audit_dir)
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.last_hash: Optional[str] = None
        self.log_file = self.audit_dir / f"audit_{int(time.time())}.log"
        self._ensure_log_file()
    
    def _ensure_log_file(self):
        """确保日志文件存在"""
        if not self.log_file.exists():
            with open(self.log_file, 'w') as f:
                # 写入文件头
                header = {
                    'type': 'audit_log',
                    'created_at': time.time(),
                    'version': '1.0'
                }
                f.write(json.dumps(header) + '\n')
    
    def log_operation(self, 
                     operation: OperationType,
                     operator: Optional[str] = None,
                     key: Optional[bytes] = None,
                     value: Optional[bytes] = None,
                     success: bool = True,
                     error: Optional[str] = None,
                     metadata: Optional[Dict[str, Any]] = None):
        """记录操作（优化：减少锁持有时间）"""
        try:
            with self.lock:
                # 计算值的哈希（不存储实际值，保护隐私）
                value_hash = None
                if value:
                    value_hash = hashlib.sha256(value).hexdigest()
                
                # 创建日志条目
                entry = AuditLogEntry(
                    timestamp=time.time(),
                    operation=operation.value,
                    operator=operator,
                    key=key,
                    value_hash=value_hash,
                    success=success,
                    error=error,
                    metadata=metadata,
                    prev_hash=self.last_hash
                )
                
                # 计算哈希
                entry.hash = entry.compute_hash()
                
                # 写入日志文件（优化：使用追加模式，减少文件操作开销）
                try:
                    with open(self.log_file, 'a') as f:
                        f.write(json.dumps(entry.to_dict()) + '\n')
                except Exception:
                    pass  # 文件写入失败不应影响主操作
                
                # 更新最后一个哈希
                self.last_hash = entry.hash
        except Exception:
            pass  # 审计日志失败不应影响主操作
    
    def log_put(self, key: bytes, value: bytes, operator: Optional[str] = None):
        """记录PUT操作"""
        self.log_operation(
            OperationType.PUT,
            operator=operator,
            key=key,
            value=value,
            success=True
        )
    
    def log_batch_put(self, count: int, operator: Optional[str] = None):
        """记录批量PUT操作"""
        self.log_operation(
            OperationType.BATCH_PUT,
            operator=operator,
            metadata={'count': count},
            success=True
        )
    
    def log_get(self, key: bytes, found: bool, operator: Optional[str] = None):
        """记录GET操作"""
        self.log_operation(
            OperationType.GET,
            operator=operator,
            key=key,
            metadata={'found': found},
            success=True
        )
    
    def log_delete(self, key: bytes, operator: Optional[str] = None):
        """记录DELETE操作"""
        self.log_operation(
            OperationType.DELETE,
            operator=operator,
            key=key,
            success=True
        )
    
    def log_error(self, operation: OperationType, error: str, operator: Optional[str] = None):
        """记录错误"""
        self.log_operation(
            operation,
            operator=operator,
            success=False,
            error=error
        )
    
    def verify_integrity(self) -> Dict[str, Any]:
        """验证审计日志完整性（检查哈希链）"""
        issues = []
        last_hash = None
        
        # 读取所有日志文件
        log_files = sorted(self.audit_dir.glob("audit_*.log"))
        
        for log_file in log_files:
            with open(log_file, 'r') as f:
                # 跳过文件头
                first_line = f.readline()
                if first_line.startswith('{"type":'):
                    continue
                
                # 读取所有条目
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        entry_dict = json.loads(line)
                        entry = AuditLogEntry(**entry_dict)
                        
                        # 验证哈希链
                        if last_hash and entry.prev_hash != last_hash:
                            issues.append(f"Hash chain broken at {entry.timestamp}")
                        
                        # 验证条目哈希
                        computed_hash = entry.compute_hash()
                        if entry.hash != computed_hash:
                            issues.append(f"Entry hash mismatch at {entry.timestamp}")
                        
                        last_hash = entry.hash
                    except Exception as e:
                        issues.append(f"Failed to parse entry: {e}")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'last_hash': last_hash
        }
    
    def get_audit_trail(self, 
                       start_time: Optional[float] = None,
                       end_time: Optional[float] = None,
                       operation: Optional[OperationType] = None,
                       operator: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取审计轨迹"""
        results = []
        
        log_files = sorted(self.audit_dir.glob("audit_*.log"))
        
        for log_file in log_files:
            with open(log_file, 'r') as f:
                # 跳过文件头
                first_line = f.readline()
                if first_line.startswith('{"type":'):
                    continue
                
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        entry_dict = json.loads(line)
                        entry = AuditLogEntry(**entry_dict)
                        
                        # 过滤
                        if start_time and entry.timestamp < start_time:
                            continue
                        if end_time and entry.timestamp > end_time:
                            continue
                        if operation and entry.operation != operation.value:
                            continue
                        if operator and entry.operator != operator:
                            continue
                        
                        results.append(entry_dict)
                    except Exception:
                        continue
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取审计统计信息"""
        stats = {
            'total_operations': 0,
            'operations_by_type': {},
            'operations_by_operator': {},
            'success_rate': 0.0,
            'error_count': 0
        }
        
        log_files = sorted(self.audit_dir.glob("audit_*.log"))
        total_success = 0
        
        for log_file in log_files:
            with open(log_file, 'r') as f:
                # 跳过文件头
                first_line = f.readline()
                if first_line.startswith('{"type":'):
                    continue
                
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        entry_dict = json.loads(line)
                        entry = AuditLogEntry(**entry_dict)
                        
                        stats['total_operations'] += 1
                        
                        # 按类型统计
                        op_type = entry.operation
                        stats['operations_by_type'][op_type] = \
                            stats['operations_by_type'].get(op_type, 0) + 1
                        
                        # 按操作者统计
                        if entry.operator:
                            stats['operations_by_operator'][entry.operator] = \
                                stats['operations_by_operator'].get(entry.operator, 0) + 1
                        
                        # 成功/失败统计
                        if entry.success:
                            total_success += 1
                        else:
                            stats['error_count'] += 1
                    except Exception:
                        continue
        
        if stats['total_operations'] > 0:
            stats['success_rate'] = total_success / stats['total_operations']
        
        return stats

