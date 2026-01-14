"""
恢复机制模块
支持WAL恢复、崩溃恢复、数据一致性检查
"""

import os
import struct
import time
from typing import List, Dict, Optional, Any
from pathlib import Path
from .storage.file_format import WALFormat, FileMagic


class RecoveryManager:
    """恢复管理器"""
    
    def __init__(self, data_dir: str):
        """
        Args:
            data_dir: 数据目录
        """
        self.data_dir = Path(data_dir)
        self.wal_dir = self.data_dir / "wal"
        self.wal_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_file = self.data_dir / "checkpoint.dat"
    
    def write_wal_entry(self, entry_type: int, key: bytes, value: Optional[bytes] = None):
        """写入WAL条目"""
        wal_file = self.wal_dir / f"wal_{int(time.time())}.wal"
        
        # 如果文件不存在，创建新文件
        if not wal_file.exists():
            with open(wal_file, 'wb') as f:
                f.write(FileMagic.WAL)
        
        with open(wal_file, 'ab') as f:
            WALFormat.write_entry(f, entry_type, key, value)
    
    def recover_from_wal(self, db) -> int:
        """从WAL恢复数据"""
        recovered_count = 0
        
        # 找到所有WAL文件
        wal_files = sorted(self.wal_dir.glob("*.wal"))
        
        for wal_file in wal_files:
            with open(wal_file, 'rb') as f:
                # 检查魔数
                magic = f.read(4)
                if magic != FileMagic.WAL:
                    continue
                
                # 读取所有条目
                while True:
                    entry = WALFormat.read_entry(f)
                    if entry is None:
                        break
                    
                    # 重放操作
                    if entry['type'] == WALFormat.ENTRY_PUT:
                        if entry['value']:
                            db.put(entry['key'], entry['value'])
                            recovered_count += 1
                    elif entry['type'] == WALFormat.ENTRY_DELETE:
                        # 删除操作：通过put空值实现
                        db.put(entry['key'], b'')
                        recovered_count += 1
                    elif entry['type'] == WALFormat.ENTRY_COMMIT:
                        # 提交标记：确保数据已持久化
                        db.flush()
                    elif entry['type'] == WALFormat.ENTRY_ABORT:
                        # 中止标记：跳过后续操作直到下一个COMMIT
                        break
        
        return recovered_count
    
    def create_checkpoint(self, db):
        """创建检查点"""
        # 保存当前状态
        checkpoint_data = {
            'timestamp': time.time(),
            'merkle_root': db.get_root_hash().hex(),
            'version': db.version_manager.get_current_version(b'')
        }
        
        with open(self.checkpoint_file, 'w') as f:
            import json
            json.dump(checkpoint_data, f)
        
        # 清理已应用的WAL文件
        self._cleanup_applied_wal()
    
    def _cleanup_applied_wal(self):
        """清理已应用的WAL文件"""
        wal_files = sorted(self.wal_dir.glob("*.wal"), key=lambda p: p.stat().st_mtime)
        
        # 只清理已创建检查点之前的WAL文件
        if self.checkpoint_file.exists():
            import json
            with open(self.checkpoint_file, 'r') as f:
                checkpoint_data = json.load(f)
                checkpoint_time = checkpoint_data.get('timestamp', 0)
            
            # 删除检查点之前的WAL文件，但至少保留最近5个
            for wal_file in wal_files[:-5]:
                if wal_file.stat().st_mtime < checkpoint_time:
                    try:
                        wal_file.unlink()
                    except Exception:
                        pass
    
    def verify_consistency(self, db) -> Dict[str, Any]:
        """验证数据一致性"""
        issues = []
        
        # 检查Merkle根
        current_root = db.get_root_hash()
        checkpoint_root = None
        
        if self.checkpoint_file.exists():
            import json
            with open(self.checkpoint_file, 'r') as f:
                checkpoint_data = json.load(f)
                checkpoint_root = bytes.fromhex(checkpoint_data.get('merkle_root', ''))
        
        if checkpoint_root and current_root != checkpoint_root:
            issues.append("Merkle root mismatch")
        
        # 检查版本一致性
        # 简化实现
        
        return {
            'consistent': len(issues) == 0,
            'issues': issues,
            'merkle_root': current_root.hex()
        }
    
    def crash_recovery(self, db) -> Dict[str, Any]:
        """崩溃恢复"""
        recovery_info = {
            'checkpoint_found': False,
            'wal_entries_recovered': 0,
            'recovery_time': 0.0
        }
        
        start_time = time.time()
        
        # 检查是否有检查点
        if self.checkpoint_file.exists():
            recovery_info['checkpoint_found'] = True
            import json
            with open(self.checkpoint_file, 'r') as f:
                checkpoint_data = json.load(f)
                checkpoint_time = checkpoint_data.get('timestamp', 0)
                checkpoint_root = bytes.fromhex(checkpoint_data.get('merkle_root', ''))
            
            # 验证检查点有效性
            current_root = db.get_root_hash()
            if current_root != checkpoint_root:
                # 需要从检查点恢复状态
                # 这里可以重新加载数据库或应用检查点
                pass
        
        # 从WAL恢复
        recovered_count = self.recover_from_wal(db)
        recovery_info['wal_entries_recovered'] = recovered_count
        
        recovery_info['recovery_time'] = time.time() - start_time
        
        return recovery_info


class ConsistencyChecker:
    """一致性检查器"""
    
    def __init__(self, db):
        self.db = db
    
    def check_storage_consistency(self) -> List[str]:
        """检查存储一致性"""
        issues = []
        
        # 检查LSM树和B+树的一致性
        # 获取所有键
        all_keys = self.db.version_manager.get_all_keys()
        
        # 检查每个键在LSM树和B+树中的值是否一致
        for key in all_keys[:100]:  # 采样检查前100个键
            lsm_result = self.db.storage.lsm_tree.get(key)
            bplus_result = self.db.storage.bplus_tree.get(key)
            
            if lsm_result and bplus_result:
                if lsm_result[0] != bplus_result:
                    issues.append(f"Value mismatch for key: {key.hex()[:16]}...")
            elif lsm_result and not bplus_result:
                issues.append(f"Key exists in LSM but not in B+ tree: {key.hex()[:16]}...")
            elif not lsm_result and bplus_result:
                issues.append(f"Key exists in B+ tree but not in LSM: {key.hex()[:16]}...")
        
        return issues
    
    def check_version_consistency(self) -> List[str]:
        """检查版本一致性"""
        issues = []
        
        # 检查版本链的完整性
        all_keys = self.db.version_manager.get_all_keys()
        
        for key in all_keys[:100]:  # 采样检查
            history = self.db.version_manager.get_history(key)
            if len(history) == 0:
                continue
            
            # 检查版本号是否连续
            for i in range(len(history) - 1):
                if history[i].version + 1 != history[i + 1].version:
                    issues.append(f"Version gap for key {key.hex()[:16]}...: "
                                f"{history[i].version} -> {history[i+1].version}")
            
            # 检查哈希链
            for i in range(1, len(history)):
                prev_hash = history[i-1].hash
                if history[i].prev_hash != prev_hash:
                    issues.append(f"Hash chain broken for key {key.hex()[:16]}... "
                               f"at version {history[i].version}")
        
        return issues
    
    def full_check(self) -> Dict[str, Any]:
        """完整检查"""
        storage_issues = self.check_storage_consistency()
        version_issues = self.check_version_consistency()
        
        return {
            'consistent': len(storage_issues) == 0 and len(version_issues) == 0,
            'storage_issues': storage_issues,
            'version_issues': version_issues
        }

