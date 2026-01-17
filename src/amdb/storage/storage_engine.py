"""
混合存储引擎
结合LSM树、B+树和Merkle树的优势
支持大数据量分片存储
"""

import os
import threading
from typing import Optional, Tuple, List
from .lsm_tree import LSMTree
from .sharded_lsm_tree import ShardedLSMTree
from .bplus_tree import BPlusTree
from .merkle_tree import MerkleTree
from ..sharding import ShardManager, PartitionManager


class StorageEngine:
    """
    混合存储引擎
    策略：
    - 写入：使用LSM树（高性能）
    - 读取：优先使用B+树（低延迟），回退到LSM树
    - 验证：使用Merkle树（完整性）
    - 分片：支持大数据量分片存储
    """
    
    def __init__(self, 
                 data_dir: str = "./data",
                 enable_sharding: bool = True,
                 shard_count: int = 256,
                 max_file_size: int = 256 * 1024 * 1024,
                 config = None):  # 256MB
        """
        Args:
            data_dir: 数据目录
            enable_sharding: 是否启用分片
            shard_count: 分片数量
            max_file_size: 单个文件最大大小
            config: 配置对象（DatabaseConfig）
        """
        self.data_dir = data_dir
        self.enable_sharding = enable_sharding
        self.shard_count = shard_count
        self.max_file_size = max_file_size
        self.config = config
        
        # 根据是否启用分片选择不同的LSM树实现
        if enable_sharding:
            self.lsm_tree = ShardedLSMTree(
                f"{data_dir}/lsm",
                shard_count=shard_count,
                max_file_size=max_file_size,
                config=config
            )
        else:
            self.lsm_tree = LSMTree(f"{data_dir}/lsm", config=config)
        
        self.bplus_tree = BPlusTree(data_dir=f"{data_dir}/bplus")
        self.merkle_tree = MerkleTree(data_dir=f"{data_dir}/merkle")
        self.lock = threading.RLock()
        
        # 分片和分区管理器
        if enable_sharding:
            self.shard_manager = ShardManager(
                data_dir=f"{data_dir}/shards",
                shard_count=shard_count,
                max_file_size=max_file_size
            )
            self.partition_manager = PartitionManager(f"{data_dir}/partitions")
        else:
            self.shard_manager = None
            self.partition_manager = None
        
        # 同步标志
        self._bplus_synced = False
    
    def put(self, key: bytes, value: bytes, version: int) -> bytes:
        """
        写入数据
        返回Merkle根哈希
        """
        with self.lock:
            # 1. 写入LSM树（主要存储）
            self.lsm_tree.put(key, value, version)
            
            # 2. 异步更新B+树（用于快速读取）
            # 使用后台线程异步更新，避免阻塞写入
            import threading
            if not hasattr(self, '_bplus_update_thread'):
                self._bplus_update_thread = None
            
            def async_update_bplus():
                try:
                    self.bplus_tree.insert(key, value)
                except Exception:
                    pass  # 忽略更新错误，不影响主流程
            
            if not self._bplus_synced:
                # 首次同步时直接更新
                self.bplus_tree.insert(key, value)
            else:
                # 后续异步更新
                if self._bplus_update_thread is None or not self._bplus_update_thread.is_alive():
                    self._bplus_update_thread = threading.Thread(target=async_update_bplus, daemon=True)
                    self._bplus_update_thread.start()
            
            # 3. 更新Merkle树（用于验证）
            root_hash = self.merkle_tree.put(key, value)
            
            return root_hash
    
    def get(self, key: bytes, use_cache: bool = True) -> Optional[Tuple[bytes, int]]:
        """
        读取数据
        Args:
            key: 键
            use_cache: 是否使用B+树缓存
        Returns:
            (value, version) 或 None
        """
        with self.lock:
            # 1. 优先从B+树读取（如果已同步）
            if use_cache and self._bplus_synced:
                value = self.bplus_tree.get(key)
                if value:
                    # 从LSM树获取版本号
                    result = self.lsm_tree.get(key)
                    if result:
                        return result
            
            # 2. 从LSM树读取
            return self.lsm_tree.get(key)
    
    def get_with_proof(self, key: bytes) -> Tuple[Optional[bytes], List[bytes], bytes]:
        """
        获取值及其Merkle证明
        Returns:
            (value, proof, root_hash)
        """
        with self.lock:
            result = self.get(key)
            value = result[0] if result else None
            proof = self.merkle_tree.get_proof(key)
            root_hash = self.merkle_tree.get_root_hash()
            return (value, proof, root_hash)
    
    def verify(self, key: bytes, value: bytes, proof: List[bytes]) -> bool:
        """验证数据完整性"""
        return self.merkle_tree.verify(key, value, proof)
    
    def get_root_hash(self) -> bytes:
        """获取Merkle根哈希"""
        return self.merkle_tree.get_root_hash()
    
    def range_query(self, start_key: bytes, end_key: bytes) -> List[Tuple[bytes, bytes]]:
        """范围查询"""
        with self.lock:
            if self._bplus_synced:
                return self.bplus_tree.range_query(start_key, end_key)
            # 否则需要扫描LSM树（性能较差）
            return []
    
    def flush(self):
        """强制刷新到磁盘（所有组件）"""
        with self.lock:
            # 1. LSM树刷新（.sst文件）
            self.lsm_tree.flush()
            
            # 2. B+树持久化（.bpt文件）
            self.bplus_tree.flush()
            
            # 3. Merkle树持久化（.mpt文件）
            self.merkle_tree.save_to_disk()
    
    def sync_bplus_tree(self):
        """同步B+树（从LSM树重建）"""
        # 从LSM树读取所有数据并插入B+树
        # 遍历所有SSTable
        from .lsm_tree import SSTable
        if hasattr(self.lsm_tree, 'sstables'):
            for sstable in self.lsm_tree.sstables:
                if hasattr(sstable, 'filepath') and os.path.exists(sstable.filepath):
                    # 读取SSTable中的所有键值对
                    with open(sstable.filepath, 'rb') as f:
                        # 跳过文件头
                        f.seek(0)
                        magic = f.read(4)
                        if magic != b"SST\0":
                            continue
                        
                        # 读取数据区
                        from .file_format import SSTableFormat
                        # 跳过文件头
                        f.seek(SSTableFormat.HEADER_SIZE)
                        while True:
                            entry = SSTableFormat.read_entry(f)
                            if entry is None:
                                break
                            key, value, version, timestamp = entry
                            self.bplus_tree.insert(key, value)
        
        self._bplus_synced = True
    
    def get_shard_info(self) -> dict:
        """获取分片信息"""
        if self.enable_sharding and hasattr(self.lsm_tree, 'get_shard_info'):
            return self.lsm_tree.get_shard_info()
        return {}
    
    def create_partition(self, partition_name: str, 
                        shard_count: int = 256,
                        max_file_size: int = 256 * 1024 * 1024):
        """创建分区（分表分库）"""
        if self.partition_manager:
            self.partition_manager.create_partition(
                partition_name, shard_count, max_file_size
            )
    
    def get_partition(self, partition_name: str):
        """获取分区"""
        if self.partition_manager:
            return self.partition_manager.get_partition(partition_name)
        return None
    
    def list_partitions(self) -> List[str]:
        """列出所有分区"""
        if self.partition_manager:
            return self.partition_manager.list_partitions()
        return []

