"""
版本管理模块
为每个键维护版本历史链，支持时间点查询
"""

import time
import hashlib
from typing import Optional, List, Tuple, Dict
from dataclasses import dataclass
from collections import defaultdict
import threading


@dataclass
class Version:
    """版本对象"""
    version: int
    timestamp: float
    value: bytes
    prev_hash: Optional[bytes] = None
    hash: Optional[bytes] = None
    
    def _compute_hash(self):
        """计算版本哈希（延迟计算）"""
        if self.hash is not None:
            return
        content = (
            str(self.version).encode() +
            str(self.timestamp).encode() +
            self.value +
            (self.prev_hash or b'')
        )
        self.hash = hashlib.sha256(content).digest()


class VersionManager:
    """
    版本管理器
    为每个键维护版本历史链
    """
    
    def __init__(self, config=None):
        self.versions: Dict[bytes, List[Version]] = defaultdict(list)
        self.current_versions: Dict[bytes, int] = {}
        self.lock = threading.RLock()
        self._config = config  # 保存配置引用
        # 优化：缓存配置值，避免重复访问（性能关键路径）
        if config:
            self._batch_max_size = config.version_batch_max_size
            self._skip_prev_hash_threshold = config.version_skip_prev_hash_threshold
        else:
            self._batch_max_size = 1000
            self._skip_prev_hash_threshold = 100
    
    def create_version(self, key: bytes, value: bytes) -> Version:
        """创建新版本"""
        with self.lock:
            current_ver = self.current_versions.get(key, 0)
            new_ver = current_ver + 1
            
            # 获取前一个版本的哈希
            prev_hash = None
            if key in self.versions and self.versions[key]:
                last_version = self.versions[key][-1]
                if last_version.hash is None:
                    last_version._compute_hash()
                prev_hash = last_version.hash
            
            version = Version(
                version=new_ver,
                timestamp=time.time(),
                value=value,
                prev_hash=prev_hash
            )
            
            self.versions[key].append(version)
            self.current_versions[key] = new_ver
            
            return version
    
    def create_versions_batch(self, items: List[Tuple[bytes, bytes]]) -> List[Version]:
        """
        批量创建版本（简化稳定版本）
        优化：批量字典操作，减少单次查找和更新
        Args:
            items: [(key, value), ...]
        Returns:
            List[Version]
        """
        # 优化：限制批量大小，避免内存问题和崩溃
        # 使用缓存的配置值（避免重复访问配置对象）
        MAX_BATCH_SIZE = self._batch_max_size
        if len(items) > MAX_BATCH_SIZE:
            # 分批处理
            all_versions = []
            for i in range(0, len(items), MAX_BATCH_SIZE):
                batch = items[i:i+MAX_BATCH_SIZE]
                versions = self._create_versions_batch_internal(batch)
                all_versions.extend(versions)
            return all_versions
        else:
            return self._create_versions_batch_internal(items)
    
    def _create_versions_batch_internal(self, items: List[Tuple[bytes, bytes]]) -> List[Version]:
        """内部批量创建版本方法（简化稳定版本）"""
        try:
            with self.lock:
                current_time = time.time()
                versions = []
                updates_dict = {}
                
                # 优化：批量处理，减少字典查找开销
                # 对于大批量，跳过prev_hash计算以提升性能
                # 使用缓存的配置值（避免重复访问配置对象）
                skip_prev_hash = len(items) > self._skip_prev_hash_threshold
                
                for key, value in items:
                    try:
                        # 获取当前版本号
                        current_ver = self.current_versions.get(key, 0)
                        new_ver = current_ver + 1
                        updates_dict[key] = new_ver
                        
                        # 获取前一个版本的哈希（大批量时跳过）
                        prev_hash = None
                        if not skip_prev_hash:
                            version_list = self.versions.get(key)
                            if version_list and len(version_list) > 0:
                                last_version = version_list[-1]
                                if last_version and last_version.hash is None:
                                    last_version._compute_hash()
                                if last_version:
                                    prev_hash = last_version.hash
                        
                        # 创建版本对象
                        version = Version(
                            version=new_ver,
                            timestamp=current_time,
                            value=value,
                            prev_hash=prev_hash
                        )
                        
                        # 添加到版本列表
                        if key not in self.versions:
                            self.versions[key] = []
                        self.versions[key].append(version)
                        versions.append(version)
                    except Exception as e:
                        import traceback
                        print(f"创建单个版本失败: {e}")
                        traceback.print_exc()
                        # 继续处理下一个
                        continue
                
                # 批量更新current_versions
                self.current_versions.update(updates_dict)
                
                return versions
        except Exception as e:
            import traceback
            print(f"版本创建内部方法失败: {e}")
            traceback.print_exc()
            return []
    
    def get_latest(self, key: bytes) -> Optional[Version]:
        """获取最新版本"""
        with self.lock:
            if key not in self.versions or not self.versions[key]:
                return None
            return self.versions[key][-1]
    
    def get_version(self, key: bytes, version: int) -> Optional[Version]:
        """获取指定版本"""
        with self.lock:
            if key not in self.versions:
                return None
            
            # 二分查找（版本是有序的）
            versions = self.versions[key]
            left, right = 0, len(versions) - 1
            
            while left <= right:
                mid = (left + right) // 2
                if versions[mid].version == version:
                    return versions[mid]
                elif versions[mid].version < version:
                    left = mid + 1
                else:
                    right = mid - 1
            
            return None
    
    def get_at_time(self, key: bytes, timestamp: float) -> Optional[Version]:
        """获取指定时间点的版本"""
        with self.lock:
            if key not in self.versions:
                return None
            
            # 找到时间戳小于等于指定时间的最后一个版本
            versions = self.versions[key]
            result = None
            
            for version in versions:
                if version.timestamp <= timestamp:
                    result = version
                else:
                    break
            
            return result
    
    def get_history(self, key: bytes, start_version: Optional[int] = None,
                   end_version: Optional[int] = None) -> List[Version]:
        """获取版本历史"""
        with self.lock:
            if key not in self.versions:
                return []
            
            versions = self.versions[key]
            
            if start_version is None:
                start_version = 0
            if end_version is None:
                end_version = float('inf')
            
            return [
                v for v in versions
                if start_version <= v.version <= end_version
            ]
    
    def get_all_keys(self) -> List[bytes]:
        """获取所有键"""
        with self.lock:
            return list(self.current_versions.keys())
    
    def get_current_version(self, key: bytes) -> int:
        """获取当前版本号"""
        with self.lock:
            return self.current_versions.get(key, 0)
    
    def save_to_disk(self, data_dir: str):
        """保存版本数据到磁盘（.ver文件）"""
        import os
        import struct
        from pathlib import Path
        from .storage.file_format import FileMagic
        
        versions_dir = Path(data_dir) / "versions"
        os.makedirs(versions_dir, exist_ok=True)
        
        version_file = versions_dir / "versions.ver"
        
        try:
            with self.lock:
                with open(version_file, 'wb') as f:
                    # 写入文件魔数
                    f.write(FileMagic.VER)  # 4 bytes
                    
                    # 写入版本号
                    f.write(struct.pack('H', 1))  # 2 bytes
                    
                    # 写入键数量
                    f.write(struct.pack('Q', len(self.current_versions)))  # 8 bytes
                    
                    # 写入所有键的版本信息
                    for key, current_ver in self.current_versions.items():
                        # 键
                        f.write(struct.pack('I', len(key)))  # 4 bytes
                        f.write(key)
                        
                        # 当前版本号
                        f.write(struct.pack('I', current_ver))  # 4 bytes
                        
                        # 版本历史数量
                        version_list = self.versions.get(key, [])
                        f.write(struct.pack('I', len(version_list)))  # 4 bytes
                        
                        # 写入版本历史
                        for version_obj in version_list:
                            # version, timestamp, value_len, value, prev_hash
                            f.write(struct.pack('I', version_obj.version))  # 4 bytes
                            f.write(struct.pack('d', version_obj.timestamp))  # 8 bytes
                            f.write(struct.pack('I', len(version_obj.value)))  # 4 bytes
                            f.write(version_obj.value)
                            
                            # prev_hash
                            if version_obj.prev_hash:
                                f.write(struct.pack('I', len(version_obj.prev_hash)))  # 4 bytes
                                f.write(version_obj.prev_hash)  # 32 bytes
                            else:
                                f.write(struct.pack('I', 0))  # 4 bytes
                    
                    # 写入checksum
                    current_pos = f.tell()
                
                # 重新打开文件读取数据并计算checksum
                with open(version_file, 'rb') as rf:
                    data = rf.read()
                
                # 追加checksum
                with open(version_file, 'ab') as af:
                    checksum = hashlib.sha256(data).digest()
                    af.write(checksum)  # 32 bytes
        except Exception as e:
            import traceback
            print(f"保存版本数据失败: {e}")
            traceback.print_exc()
    
    def load_from_disk(self, data_dir: str):
        """从磁盘加载版本数据（.ver文件）"""
        import os
        import struct
        from pathlib import Path
        from .storage.file_format import FileMagic
        
        versions_dir = Path(data_dir) / "versions"
        version_file = versions_dir / "versions.ver"
        
        if not version_file.exists():
            return
        
        try:
            with self.lock:
                with open(version_file, 'rb') as f:
                    # 读取文件魔数
                    magic = f.read(4)
                    if magic != FileMagic.VER:
                        return  # 无效文件
                    
                    # 读取版本号
                    version = struct.unpack('H', f.read(2))[0]
                    
                    # 读取键数量
                    key_count = struct.unpack('Q', f.read(8))[0]
                    
                    # 读取所有键的版本信息
                    for _ in range(key_count):
                        # 键
                        key_len = struct.unpack('I', f.read(4))[0]
                        key = f.read(key_len)
                        
                        # 当前版本号
                        current_ver = struct.unpack('I', f.read(4))[0]
                        self.current_versions[key] = current_ver
                        
                        # 版本历史数量
                        version_count = struct.unpack('I', f.read(4))[0]
                        
                        # 读取版本历史
                        version_list = []
                        for _ in range(version_count):
                            ver = struct.unpack('I', f.read(4))[0]
                            timestamp = struct.unpack('d', f.read(8))[0]
                            value_len = struct.unpack('I', f.read(4))[0]
                            value = f.read(value_len)
                            
                            prev_hash_len = struct.unpack('I', f.read(4))[0]
                            prev_hash = f.read(prev_hash_len) if prev_hash_len > 0 else None
                            
                            version_obj = Version(
                                version=ver,
                                timestamp=timestamp,
                                value=value,
                                prev_hash=prev_hash
                            )
                            version_list.append(version_obj)
                        
                        self.versions[key] = version_list
        except Exception as e:
            import traceback
            print(f"加载版本数据失败: {e}")
            traceback.print_exc()
