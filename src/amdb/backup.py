"""
备份和恢复模块
支持全量备份、增量备份、快照恢复
"""

import os
import shutil
import json
import tarfile
import hashlib
import time
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime


class BackupManager:
    """备份管理器"""
    
    def __init__(self, data_dir: str, backup_dir: str = "./backups"):
        """
        Args:
            data_dir: 数据目录
            backup_dir: 备份目录
        """
        self.data_dir = Path(data_dir)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.backup_dir / "backup_metadata.json"
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict:
        """加载备份元数据"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {'backups': []}
    
    def _save_metadata(self):
        """保存备份元数据"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def create_full_backup(self, name: Optional[str] = None) -> str:
        """创建全量备份"""
        if name is None:
            name = f"full_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_path = self.backup_dir / f"{name}.tar.gz"
        
        # 创建tar.gz压缩包
        with tarfile.open(backup_path, 'w:gz') as tar:
            tar.add(self.data_dir, arcname=os.path.basename(self.data_dir))
        
        # 计算校验和
        checksum = self._calculate_checksum(backup_path)
        
        # 保存元数据
        backup_info = {
            'name': name,
            'type': 'full',
            'path': str(backup_path),
            'checksum': checksum,
            'timestamp': time.time(),
            'size': backup_path.stat().st_size
        }
        self.metadata['backups'].append(backup_info)
        self._save_metadata()
        
        return str(backup_path)
    
    def create_incremental_backup(self, base_backup_name: str, 
                                   name: Optional[str] = None) -> str:
        """创建增量备份"""
        if name is None:
            name = f"incr_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 找到基础备份
        base_backup = None
        for backup in self.metadata['backups']:
            if backup['name'] == base_backup_name:
                base_backup = backup
                break
        
        if not base_backup:
            raise ValueError(f"Base backup not found: {base_backup_name}")
        
        backup_path = self.backup_dir / f"{name}.tar.gz"
        
        # 创建增量备份（只备份变更的文件）
        base_timestamp = base_backup.get('timestamp', 0)
        
        with tarfile.open(backup_path, 'w:gz') as tar:
            changed_files = []
            for root, dirs, files in os.walk(self.data_dir):
                for file in files:
                    file_path = Path(root) / file
                    # 检查文件修改时间
                    file_mtime = file_path.stat().st_mtime
                    # 只备份在基础备份之后修改的文件
                    if file_mtime > base_timestamp:
                        tar.add(file_path, arcname=file_path.relative_to(self.data_dir.parent))
                        changed_files.append(str(file_path))
            
            # 记录变更文件列表
            changes_manifest = {
                'base_backup': base_backup_name,
                'changed_files': changed_files,
                'timestamp': time.time()
            }
            manifest_data = json.dumps(changes_manifest).encode()
            manifest_path = self.backup_dir / f"{name}_manifest.json"
            with open(manifest_path, 'wb') as f:
                f.write(manifest_data)
        
        checksum = self._calculate_checksum(backup_path)
        
        backup_info = {
            'name': name,
            'type': 'incremental',
            'base_backup': base_backup_name,
            'path': str(backup_path),
            'checksum': checksum,
            'timestamp': time.time(),
            'size': backup_path.stat().st_size
        }
        self.metadata['backups'].append(backup_info)
        self._save_metadata()
        
        return str(backup_path)
    
    def restore_backup(self, backup_name: str, target_dir: Optional[str] = None):
        """恢复备份"""
        # 找到备份
        backup_info = None
        for backup in self.metadata['backups']:
            if backup['name'] == backup_name:
                backup_info = backup
                break
        
        if not backup_info:
            raise ValueError(f"Backup not found: {backup_name}")
        
        backup_path = Path(backup_info['path'])
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        
        # 验证校验和
        if not self._verify_checksum(backup_path, backup_info['checksum']):
            raise ValueError("Backup checksum verification failed")
        
        # 恢复目标目录
        if target_dir is None:
            target_dir = self.data_dir
        else:
            target_dir = Path(target_dir)
        
        # 清空目标目录
        if target_dir.exists():
            shutil.rmtree(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # 解压备份
        with tarfile.open(backup_path, 'r:gz') as tar:
            tar.extractall(target_dir.parent)
    
    def list_backups(self) -> List[Dict]:
        """列出所有备份"""
        return self.metadata.get('backups', [])
    
    def delete_backup(self, backup_name: str):
        """删除备份"""
        backup_info = None
        for i, backup in enumerate(self.metadata['backups']):
            if backup['name'] == backup_name:
                backup_info = backup
                # 删除文件
                backup_path = Path(backup['path'])
                if backup_path.exists():
                    backup_path.unlink()
                # 从元数据中删除
                self.metadata['backups'].pop(i)
                break
        
        if backup_info:
            self._save_metadata()
        else:
            raise ValueError(f"Backup not found: {backup_name}")
    
    def _calculate_checksum(self, filepath: Path) -> str:
        """计算文件校验和"""
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def _verify_checksum(self, filepath: Path, expected_checksum: str) -> bool:
        """验证文件校验和"""
        actual_checksum = self._calculate_checksum(filepath)
        return actual_checksum == expected_checksum


class SnapshotManager:
    """快照管理器"""
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.snapshots_dir = self.data_dir / "snapshots"
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
    
    def create_snapshot(self, name: str, db) -> str:
        """创建快照"""
        snapshot_path = self.snapshots_dir / name
        snapshot_path.mkdir(parents=True, exist_ok=True)
        
        # 获取当前Merkle根
        root_hash = db.get_root_hash()
        
        # 保存快照元数据
        snapshot_meta = {
            'name': name,
            'timestamp': time.time(),
            'merkle_root': root_hash.hex() if root_hash else '',
            'data_dir': str(self.data_dir)
        }
        
        meta_file = snapshot_path / "snapshot_meta.json"
        with open(meta_file, 'w') as f:
            json.dump(snapshot_meta, f, indent=2)
        
        # 创建数据快照（复制关键文件）
        import shutil
        for item in ['lsm', 'bplus', 'wal']:
            src = self.data_dir / item
            if src.exists():
                dst = snapshot_path / item
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
        
        return str(snapshot_path)
    
    def restore_snapshot(self, name: str, db):
        """恢复快照"""
        snapshot_path = self.snapshots_dir / name
        if not snapshot_path.exists():
            raise ValueError(f"Snapshot not found: {name}")
        
        # 读取快照元数据
        meta_file = snapshot_path / "snapshot_meta.json"
        if not meta_file.exists():
            raise ValueError(f"Snapshot metadata not found: {name}")
        
        with open(meta_file, 'r') as f:
            snapshot_meta = json.load(f)
        
        # 恢复数据文件
        import shutil
        for item in ['lsm', 'bplus', 'wal']:
            src = snapshot_path / item
            if src.exists():
                dst = self.data_dir / item
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
        
        # 验证Merkle根
        current_root = db.get_root_hash()
        expected_root = bytes.fromhex(snapshot_meta.get('merkle_root', ''))
        if current_root != expected_root:
            # 重新加载数据库以应用快照
            pass

