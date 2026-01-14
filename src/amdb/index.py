"""
索引管理器
管理多种索引类型：主键索引、版本索引、Merkle索引、二级索引
支持持久化到磁盘（.idx文件）
"""

import threading
import os
import struct
import json
from typing import Optional, Dict, List, Tuple, Any
from collections import defaultdict
from pathlib import Path
import time
from .storage.file_format import FileMagic


class IndexManager:
    """
    索引管理器
    管理所有索引，支持快速查询
    """
    
    def __init__(self):
        # 主键索引：key -> (value, version)
        self.primary_index: Dict[bytes, Tuple[bytes, int]] = {}
        
        # 版本索引：key -> List[(version, timestamp)]
        self.version_index: Dict[bytes, List[Tuple[int, float]]] = defaultdict(list)
        
        # 时间索引：timestamp -> List[key]
        self.time_index: List[Tuple[float, bytes]] = []  # 应该使用有序结构
        
        # 二级索引：index_name -> {index_value -> List[key]}
        self.secondary_indexes: Dict[str, Dict[Any, List[bytes]]] = {}
        
        self.lock = threading.RLock()
    
    def put(self, key: bytes, value: bytes, version: int, timestamp: float = None):
        """更新索引"""
        with self.lock:
            if timestamp is None:
                timestamp = time.time()
            
            # 更新主键索引
            self.primary_index[key] = (value, version)
            
            # 更新版本索引
            if key not in self.version_index or not self.version_index[key]:
                self.version_index[key] = [(version, timestamp)]
            else:
                # 使用二分查找插入到正确位置（保持有序）
                versions = self.version_index[key]
                if not versions:
                    versions.append((version, timestamp))
                else:
                    left, right = 0, len(versions)
                    while left < right:
                        mid = (left + right) // 2
                        if versions[mid][0] < version:
                            left = mid + 1
                        else:
                            right = mid
                    versions.insert(left, (version, timestamp))
            
            # 更新时间索引（保持有序）
            # 使用二分查找插入到正确位置
            time_entry = (timestamp, key)
            left, right = 0, len(self.time_index)
            while left < right:
                mid = (left + right) // 2
                if self.time_index[mid][0] <= timestamp:
                    left = mid + 1
                else:
                    right = mid
            self.time_index.insert(left, time_entry)
    
    def get(self, key: bytes) -> Optional[Tuple[bytes, int]]:
        """从主键索引获取"""
        with self.lock:
            return self.primary_index.get(key)
    
    def get_version_range(self, key: bytes, start_version: Optional[int] = None,
                         end_version: Optional[int] = None) -> List[Tuple[int, float]]:
        """获取版本范围"""
        with self.lock:
            if key not in self.version_index:
                return []
            
            versions = self.version_index[key]
            
            if start_version is None:
                start_version = 0
            if end_version is None:
                end_version = float('inf')
            
            return [
                (v, t) for v, t in versions
                if start_version <= v <= end_version
            ]
    
    def get_at_time(self, timestamp: float) -> List[bytes]:
        """获取指定时间点的所有键"""
        with self.lock:
            # 使用二分查找优化（需要先排序）
            if not self.time_index:
                return []
            
            # 确保时间索引有序
            sorted_index = sorted(self.time_index, key=lambda x: x[0])
            
            # 二分查找最后一个时间戳 <= timestamp 的位置
            left, right = 0, len(sorted_index)
            while left < right:
                mid = (left + right) // 2
                if sorted_index[mid][0] <= timestamp:
                    left = mid + 1
                else:
                    right = mid
            
            # 返回所有时间戳 <= timestamp 的键
            return [key for t, key in sorted_index[:left]]
    
    def create_secondary_index(self, index_name: str):
        """创建二级索引"""
        with self.lock:
            if index_name not in self.secondary_indexes:
                self.secondary_indexes[index_name] = {}
    
    def update_secondary_index(self, index_name: str, index_value: Any, key: bytes):
        """更新二级索引"""
        with self.lock:
            if index_name not in self.secondary_indexes:
                self.create_secondary_index(index_name)
            
            if index_value not in self.secondary_indexes[index_name]:
                self.secondary_indexes[index_name][index_value] = []
            
            if key not in self.secondary_indexes[index_name][index_value]:
                self.secondary_indexes[index_name][index_value].append(key)
    
    def query_secondary_index(self, index_name: str, index_value: Any) -> List[bytes]:
        """查询二级索引"""
        with self.lock:
            if index_name not in self.secondary_indexes:
                return []
            
            return self.secondary_indexes[index_name].get(index_value, [])
    
    def save_to_disk(self, data_dir: str):
        """保存索引数据到磁盘（.idx文件）"""
        indexes_dir = Path(data_dir) / "indexes"
        os.makedirs(indexes_dir, exist_ok=True)
        
        index_file = indexes_dir / "indexes.idx"
        
        try:
            with self.lock:
                with open(index_file, 'wb') as f:
                    # 写入文件魔数
                    f.write(FileMagic.IDX)  # 4 bytes
                    
                    # 写入版本号
                    f.write(struct.pack('H', 1))  # 2 bytes
                    
                    # 写入主键索引数量
                    f.write(struct.pack('Q', len(self.primary_index)))  # 8 bytes
                    for key, (value, version) in self.primary_index.items():
                        f.write(struct.pack('I', len(key)))  # 4 bytes
                        f.write(key)
                        f.write(struct.pack('I', len(value)))  # 4 bytes
                        f.write(value)
                        f.write(struct.pack('I', version))  # 4 bytes
                    
                    # 写入版本索引数量
                    f.write(struct.pack('Q', len(self.version_index)))  # 8 bytes
                    for key, versions in self.version_index.items():
                        f.write(struct.pack('I', len(key)))  # 4 bytes
                        f.write(key)
                        f.write(struct.pack('I', len(versions)))  # 4 bytes
                        for ver, timestamp in versions:
                            f.write(struct.pack('I', ver))  # 4 bytes
                            f.write(struct.pack('d', timestamp))  # 8 bytes
                    
                    # 写入时间索引数量
                    f.write(struct.pack('Q', len(self.time_index)))  # 8 bytes
                    for timestamp, key in self.time_index:
                        f.write(struct.pack('d', timestamp))  # 8 bytes
                        f.write(struct.pack('I', len(key)))  # 4 bytes
                        f.write(key)
                    
                    # 写入二级索引数量
                    f.write(struct.pack('Q', len(self.secondary_indexes)))  # 8 bytes
                    for index_name, index_dict in self.secondary_indexes.items():
                        index_name_bytes = index_name.encode('utf-8')
                        f.write(struct.pack('I', len(index_name_bytes)))  # 4 bytes
                        f.write(index_name_bytes)
                        f.write(struct.pack('Q', len(index_dict)))  # 8 bytes
                        for index_value, keys in index_dict.items():
                            # 序列化index_value（JSON）
                            index_value_json = json.dumps(index_value, default=str).encode('utf-8')
                            f.write(struct.pack('I', len(index_value_json)))  # 4 bytes
                            f.write(index_value_json)
                            f.write(struct.pack('I', len(keys)))  # 4 bytes
                            for key in keys:
                                f.write(struct.pack('I', len(key)))  # 4 bytes
                                f.write(key)
                    
                    # 写入checksum（先关闭文件，重新打开读取）
                    current_pos = f.tell()
            
            # 重新打开文件读取数据并计算checksum
            with open(index_file, 'rb') as rf:
                data = rf.read()
            
            # 追加checksum
            with open(index_file, 'ab') as af:
                import hashlib
                checksum = hashlib.sha256(data).digest()
                af.write(checksum)  # 32 bytes
        except Exception as e:
            import traceback
            print(f"保存索引数据失败: {e}")
            traceback.print_exc()
    
    def load_from_disk(self, data_dir: str):
        """从磁盘加载索引数据（.idx文件）"""
        indexes_dir = Path(data_dir) / "indexes"
        index_file = indexes_dir / "indexes.idx"
        
        if not index_file.exists():
            return
        
        try:
            with self.lock:
                with open(index_file, 'rb') as f:
                    # 读取文件魔数
                    magic = f.read(4)
                    if magic != FileMagic.IDX:
                        return  # 无效文件
                    
                    # 读取版本号
                    version = struct.unpack('H', f.read(2))[0]
                    
                    # 读取主键索引
                    primary_count = struct.unpack('Q', f.read(8))[0]
                    for _ in range(primary_count):
                        key_len = struct.unpack('I', f.read(4))[0]
                        key = f.read(key_len)
                        value_len = struct.unpack('I', f.read(4))[0]
                        value = f.read(value_len)
                        ver = struct.unpack('I', f.read(4))[0]
                        self.primary_index[key] = (value, ver)
                    
                    # 读取版本索引
                    version_count = struct.unpack('Q', f.read(8))[0]
                    for _ in range(version_count):
                        key_len = struct.unpack('I', f.read(4))[0]
                        key = f.read(key_len)
                        versions_count = struct.unpack('I', f.read(4))[0]
                        versions = []
                        for _ in range(versions_count):
                            ver = struct.unpack('I', f.read(4))[0]
                            timestamp = struct.unpack('d', f.read(8))[0]
                            versions.append((ver, timestamp))
                        self.version_index[key] = versions
                    
                    # 读取时间索引
                    time_count = struct.unpack('Q', f.read(8))[0]
                    for _ in range(time_count):
                        timestamp = struct.unpack('d', f.read(8))[0]
                        key_len = struct.unpack('I', f.read(4))[0]
                        key = f.read(key_len)
                        self.time_index.append((timestamp, key))
                    
                    # 读取二级索引
                    secondary_count = struct.unpack('Q', f.read(8))[0]
                    for _ in range(secondary_count):
                        index_name_len = struct.unpack('I', f.read(4))[0]
                        index_name = f.read(index_name_len).decode('utf-8')
                        index_dict = {}
                        dict_count = struct.unpack('Q', f.read(8))[0]
                        for _ in range(dict_count):
                            index_value_len = struct.unpack('I', f.read(4))[0]
                            index_value_json = f.read(index_value_len).decode('utf-8')
                            index_value = json.loads(index_value_json)
                            keys_count = struct.unpack('I', f.read(4))[0]
                            keys = []
                            for _ in range(keys_count):
                                key_len = struct.unpack('I', f.read(4))[0]
                                key = f.read(key_len)
                                keys.append(key)
                            index_dict[index_value] = keys
                        self.secondary_indexes[index_name] = index_dict
        except Exception as e:
            import traceback
            print(f"加载索引数据失败: {e}")
            traceback.print_exc()

