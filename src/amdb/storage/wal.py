# -*- coding: utf-8 -*-
"""
WAL (Write-Ahead Log) 实现
支持持久化到磁盘（.wal文件）
"""

import os
import struct
import time
import threading
from typing import Optional, List, Dict, Any
from pathlib import Path
from .file_format import WALFormat, FileMagic


class WALLogger:
    """
    WAL日志记录器
    所有写入操作先记录到WAL，确保数据不丢失
    """
    
    def __init__(self, data_dir: str = "./data/wal", max_file_size: int = 64 * 1024 * 1024):
        """
        Args:
            data_dir: WAL文件目录
            max_file_size: 单个WAL文件最大大小（64MB）
        """
        self.data_dir = Path(data_dir)
        os.makedirs(self.data_dir, exist_ok=True)
        self.max_file_size = max_file_size
        self.current_wal_file: Optional[Path] = None
        self.current_file_size = 0
        self.lock = threading.RLock()
        
        # 打开或创建WAL文件
        self._open_wal_file()
    
    def _open_wal_file(self):
        """打开或创建WAL文件"""
        timestamp = int(time.time() * 1000000)
        self.current_wal_file = self.data_dir / f"wal_{timestamp}.wal"
        self.current_file_size = 0
        
        # 创建新文件并写入文件头
        with open(self.current_wal_file, 'wb') as f:
            f.write(FileMagic.WAL)  # 4 bytes
            f.write(struct.pack('H', 1))  # 2 bytes (版本号)
            self.current_file_size = 6
    
    def log_put(self, key: bytes, value: bytes, version: int = 0):
        """记录PUT操作"""
        with self.lock:
            if self.current_file_size >= self.max_file_size:
                # 文件太大，创建新文件
                self._open_wal_file()
            
            with open(self.current_wal_file, 'ab') as f:
                entry_start = f.tell()
                WALFormat.write_entry(f, WALFormat.ENTRY_PUT, key, value, time.time())
                entry_size = f.tell() - entry_start
                self.current_file_size += entry_size
    
    def log_delete(self, key: bytes):
        """记录DELETE操作"""
        with self.lock:
            if self.current_file_size >= self.max_file_size:
                self._open_wal_file()
            
            with open(self.current_wal_file, 'ab') as f:
                entry_start = f.tell()
                WALFormat.write_entry(f, WALFormat.ENTRY_DELETE, key, None, time.time())
                entry_size = f.tell() - entry_start
                self.current_file_size += entry_size
    
    def log_commit(self, tx_id: bytes):
        """记录COMMIT操作"""
        with self.lock:
            if self.current_file_size >= self.max_file_size:
                self._open_wal_file()
            
            with open(self.current_wal_file, 'ab') as f:
                entry_start = f.tell()
                WALFormat.write_entry(f, WALFormat.ENTRY_COMMIT, tx_id, None, time.time())
                entry_size = f.tell() - entry_start
                self.current_file_size += entry_size
    
    def log_abort(self, tx_id: bytes):
        """记录ABORT操作"""
        with self.lock:
            if self.current_file_size >= self.max_file_size:
                self._open_wal_file()
            
            with open(self.current_wal_file, 'ab') as f:
                entry_start = f.tell()
                WALFormat.write_entry(f, WALFormat.ENTRY_ABORT, tx_id, None, time.time())
                entry_size = f.tell() - entry_start
                self.current_file_size += entry_size
    
    def replay(self, callback: callable):
        """重放WAL日志"""
        wal_files = sorted(self.data_dir.glob("wal_*.wal"))
        
        for wal_file in wal_files:
            try:
                with open(wal_file, 'rb') as f:
                    # 读取文件魔数
                    magic = f.read(4)
                    if magic != FileMagic.WAL:
                        continue
                    
                    # 读取版本号
                    version = struct.unpack('H', f.read(2))[0]
                    
                    # 读取所有条目
                    while True:
                        entry = WALFormat.read_entry(f)
                        if entry is None:
                            break
                        
                        entry_type = entry.get('type')
                        if entry_type == WALFormat.ENTRY_PUT:
                            callback('put', entry['key'], entry.get('value'))
                        elif entry_type == WALFormat.ENTRY_DELETE:
                            callback('delete', entry['key'], None)
                        elif entry_type == WALFormat.ENTRY_COMMIT:
                            callback('commit', entry['key'], None)
                        elif entry_type == WALFormat.ENTRY_ABORT:
                            callback('abort', entry['key'], None)
            except Exception as e:
                import traceback
                print(f"重放WAL文件失败 {wal_file}: {e}")
                traceback.print_exc()
    
    def flush(self):
        """刷新WAL到磁盘"""
        try:
            with self.lock:
                # 确保文件已写入（如果文件打开，强制刷新）
                if self.current_wal_file and self.current_wal_file.exists():
                    # 打开文件并强制刷新到磁盘
                    try:
                        with open(self.current_wal_file, 'r+b') as f:
                            f.flush()
                            os.fsync(f.fileno())  # 强制同步到磁盘
                    except Exception as e:
                        print(f"⚠️ WAL文件刷新失败: {e}")
        except Exception as e:
            import traceback
            print(f"⚠️ WAL flush失败: {e}")
            traceback.print_exc()
            # WAL flush失败不应影响主操作

