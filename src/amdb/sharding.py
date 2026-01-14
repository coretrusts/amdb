"""
数据分片模块
支持大数据量的分片存储，避免单文件过大
"""

import hashlib
import os
import threading
from typing import Optional, Tuple, List, Dict
from pathlib import Path
from enum import Enum


class ShardingStrategy(Enum):
    """分片策略"""
    HASH = "hash"  # 基于哈希值分片
    RANGE = "range"  # 基于范围分片
    DIRECTORY = "directory"  # 基于目录分片
    CUSTOM = "custom"  # 自定义分片函数


class ShardManager:
    """分片管理器"""
    
    def __init__(self, 
                 data_dir: str,
                 shard_count: int = 256,  # 默认256个分片
                 strategy: ShardingStrategy = ShardingStrategy.HASH,
                 max_file_size: int = 256 * 1024 * 1024,  # 256MB
                 shard_func: Optional[callable] = None):
        """
        Args:
            data_dir: 数据目录
            shard_count: 分片数量
            strategy: 分片策略
            max_file_size: 单个文件最大大小（字节）
            shard_func: 自定义分片函数
        """
        self.data_dir = Path(data_dir)
        self.shard_count = shard_count
        self.strategy = strategy
        self.max_file_size = max_file_size
        self.shard_func = shard_func
        self.lock = threading.RLock()
        
        # 创建分片目录结构
        self._init_shard_directories()
        
        # 分片统计信息
        self.shard_stats: Dict[int, Dict] = {}
        self._load_shard_stats()
    
    def _init_shard_directories(self):
        """初始化分片目录结构"""
        # 创建两级目录结构：shard_XX/shard_YY
        # 例如：shard_00/shard_00, shard_00/shard_01, ...
        for i in range(self.shard_count):
            # 第一级：shard_XX (XX = i // 16)
            level1 = i // 16
            # 第二级：shard_YY (YY = i % 16)
            level2 = i % 16
            
            shard_dir = self.data_dir / f"shard_{level1:02d}" / f"shard_{level2:02d}"
            shard_dir.mkdir(parents=True, exist_ok=True)
    
    def get_shard_id(self, key: bytes) -> int:
        """根据key获取分片ID（优化版本，使用快速哈希）"""
        if self.shard_func:
            return self.shard_func(key) % self.shard_count
        
        if self.strategy == ShardingStrategy.HASH:
            # 优化：使用内置hash函数（比SHA256快10-20倍）
            # 对于分片场景，内置hash的分布性足够好
            hash_value = hash(key)
            # 确保非负数
            if hash_value < 0:
                hash_value = -hash_value
            return hash_value % self.shard_count
        
        elif self.strategy == ShardingStrategy.RANGE:
            # 基于key的第一个字节范围分片
            if len(key) > 0:
                return key[0] % self.shard_count
            return 0
        
        elif self.strategy == ShardingStrategy.DIRECTORY:
            # 基于key的前缀分片
            if len(key) >= 2:
                return (key[0] * 256 + key[1]) % self.shard_count
            return 0
        
        return 0
    
    def get_shard_path(self, shard_id: int) -> Path:
        """获取分片路径"""
        level1 = shard_id // 16
        level2 = shard_id % 16
        return self.data_dir / f"shard_{level1:02d}" / f"shard_{level2:02d}"
    
    def get_shard_path_for_key(self, key: bytes) -> Path:
        """根据key获取分片路径"""
        shard_id = self.get_shard_id(key)
        return self.get_shard_path(shard_id)
    
    def should_split_file(self, shard_id: int, current_size: int) -> bool:
        """检查文件是否需要分割"""
        return current_size >= self.max_file_size
    
    def get_next_file_id(self, shard_id: int) -> int:
        """获取下一个文件ID（用于文件分割）"""
        with self.lock:
            if shard_id not in self.shard_stats:
                self.shard_stats[shard_id] = {'file_count': 0, 'total_size': 0}
            
            file_id = self.shard_stats[shard_id]['file_count']
            self.shard_stats[shard_id]['file_count'] += 1
            return file_id
    
    def get_file_path(self, shard_id: int, file_id: Optional[int] = None) -> Path:
        """获取文件路径"""
        shard_path = self.get_shard_path(shard_id)
        
        if file_id is None:
            # 获取当前文件ID
            file_id = self.shard_stats.get(shard_id, {}).get('file_count', 0)
        
        return shard_path / f"data_{file_id:06d}.sst"
    
    def update_shard_stats(self, shard_id: int, file_size: int):
        """更新分片统计信息"""
        with self.lock:
            if shard_id not in self.shard_stats:
                self.shard_stats[shard_id] = {'file_count': 0, 'total_size': 0}
            
            self.shard_stats[shard_id]['total_size'] += file_size
    
    def get_shard_stats(self, shard_id: Optional[int] = None) -> Dict:
        """获取分片统计信息"""
        with self.lock:
            if shard_id is not None:
                return self.shard_stats.get(shard_id, {})
            return self.shard_stats.copy()
    
    def _load_shard_stats(self):
        """加载分片统计信息"""
        stats_file = self.data_dir / "shard_stats.json"
        if stats_file.exists():
            import json
            try:
                with open(stats_file, 'r') as f:
                    self.shard_stats = json.load(f)
                    # 转换key为int
                    self.shard_stats = {int(k): v for k, v in self.shard_stats.items()}
            except Exception:
                self.shard_stats = {}
        else:
            self.shard_stats = {}
    
    def save_shard_stats(self):
        """保存分片统计信息"""
        stats_file = self.data_dir / "shard_stats.json"
        import json
        with open(stats_file, 'w') as f:
            json.dump(self.shard_stats, f, indent=2)
    
    def get_all_shards(self) -> List[int]:
        """获取所有分片ID"""
        return list(range(self.shard_count))
    
    def get_shard_keys(self, shard_id: int) -> List[bytes]:
        """获取分片中的所有键（用于迁移/合并）"""
        shard_path = self.get_shard_path(shard_id)
        keys = []
        seen_keys = set()
        
        # 遍历分片目录中的所有文件
        for file_path in shard_path.glob("*.sst"):
            # 读取SSTable文件获取所有key
            try:
                with open(file_path, 'rb') as f:
                    # 检查文件头
                    magic = f.read(4)
                    if magic != b"SST\0":
                        continue
                    
                    # 读取文件头信息
                    version = struct.unpack('H', f.read(2))[0]
                    key_count = struct.unpack('Q', f.read(8))[0]
                    data_offset = struct.unpack('Q', f.read(8))[0]
                    index_offset = struct.unpack('Q', f.read(8))[0]
                    footer_offset = struct.unpack('Q', f.read(8))[0]
                    
                    # 读取索引
                    f.seek(index_offset)
                    index_len = struct.unpack('I', f.read(4))[0]
                    index_json = json.loads(f.read(index_len).decode())
                    
                    # 提取所有key
                    for key_hex in index_json.keys():
                        key = bytes.fromhex(key_hex)
                        if key not in seen_keys:
                            keys.append(key)
                            seen_keys.add(key)
            except Exception:
                continue
        
        return keys


class PartitionManager:
    """分区管理器（分表分库）"""
    
    def __init__(self, base_dir: str):
        """
        Args:
            base_dir: 基础目录
        """
        self.base_dir = Path(base_dir)
        self.partitions: Dict[str, Dict] = {}  # partition_name -> config
        self.lock = threading.RLock()
    
    def create_partition(self, partition_name: str, 
                        shard_count: int = 256,
                        max_file_size: int = 256 * 1024 * 1024):
        """创建分区（类似创建表/库）"""
        with self.lock:
            partition_dir = self.base_dir / partition_name
            partition_dir.mkdir(parents=True, exist_ok=True)
            
            # 创建分片管理器
            shard_mgr = ShardManager(
                data_dir=str(partition_dir),
                shard_count=shard_count,
                max_file_size=max_file_size
            )
            
            self.partitions[partition_name] = {
                'dir': partition_dir,
                'shard_manager': shard_mgr,
                'shard_count': shard_count,
                'max_file_size': max_file_size
            }
    
    def get_partition(self, partition_name: str) -> Optional[ShardManager]:
        """获取分区"""
        with self.lock:
            if partition_name in self.partitions:
                return self.partitions[partition_name]['shard_manager']
            return None
    
    def list_partitions(self) -> List[str]:
        """列出所有分区"""
        with self.lock:
            return list(self.partitions.keys())
    
    def delete_partition(self, partition_name: str):
        """删除分区"""
        with self.lock:
            if partition_name in self.partitions:
                import shutil
                partition_dir = self.partitions[partition_name]['dir']
                if partition_dir.exists():
                    shutil.rmtree(partition_dir)
                del self.partitions[partition_name]


class FileSizeManager:
    """文件大小管理器"""
    
    def __init__(self, max_file_size: int = 256 * 1024 * 1024):
        """
        Args:
            max_file_size: 单个文件最大大小（字节）
        """
        self.max_file_size = max_file_size
        self.file_sizes: Dict[str, int] = {}  # filepath -> size
        self.lock = threading.RLock()
    
    def check_file_size(self, filepath: str, current_size: int) -> Tuple[bool, Optional[str]]:
        """
        检查文件大小
        Returns:
            (should_split, next_filepath)
        """
        with self.lock:
            if current_size >= self.max_file_size:
                # 需要分割，生成新文件路径
                path = Path(filepath)
                # 获取文件编号
                stem = path.stem
                if '_' in stem:
                    base, num = stem.rsplit('_', 1)
                    try:
                        file_num = int(num)
                        next_num = file_num + 1
                    except ValueError:
                        next_num = 1
                else:
                    next_num = 1
                
                next_filepath = str(path.parent / f"{path.stem.rsplit('_', 1)[0]}_{next_num:06d}{path.suffix}")
                return (True, next_filepath)
            
            return (False, None)
    
    def update_file_size(self, filepath: str, size: int):
        """更新文件大小"""
        with self.lock:
            self.file_sizes[filepath] = size
    
    def get_file_size(self, filepath: str) -> int:
        """获取文件大小"""
        with self.lock:
            return self.file_sizes.get(filepath, 0)
    
    def get_total_size(self) -> int:
        """获取总大小"""
        with self.lock:
            return sum(self.file_sizes.values())

