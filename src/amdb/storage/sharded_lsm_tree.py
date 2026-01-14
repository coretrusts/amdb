"""
支持分片的LSM树
支持大数据量、文件大小限制、自动分割
"""

import os
import json
import struct
import threading
import time
from typing import Optional, Dict, List, Tuple, Iterator
from collections import OrderedDict
from pathlib import Path
from ..sharding import ShardManager, FileSizeManager
from .lsm_tree import MemTable, SSTable


class ShardedSSTable:
    """支持分片的SSTable"""
    
    def __init__(self, filepath: str, max_file_size: int = 256 * 1024 * 1024):
        """
        Args:
            filepath: 文件路径
            max_file_size: 最大文件大小（256MB）
        """
        self.filepath = Path(filepath)
        self.max_file_size = max_file_size
        self.index: Dict[bytes, Tuple[int, int]] = {}  # key -> (file_id, offset)
        self.file_sizes: Dict[int, int] = {}  # file_id -> size
        self.current_file_id = 0
        self._loaded = False
    
    def write(self, entries: List[Tuple[bytes, bytes, int]]) -> None:
        """写入数据（支持文件分割）"""
        os.makedirs(self.filepath.parent, exist_ok=True)
        
        current_file_id = 0
        current_file_size = 0
        current_entries: List[Tuple[bytes, bytes, int]] = []
        
        for key, value, version in sorted(entries, key=lambda x: x[0]):
            entry_size = 4 + len(key) + 4 + len(value) + 4 + 8  # key_len + key + value_len + value + version + timestamp
            
            # 检查是否需要创建新文件
            if current_file_size + entry_size > self.max_file_size and current_entries:
                # 写入当前文件
                self._write_file(current_file_id, current_entries)
                current_file_id += 1
                current_file_size = 0
                current_entries = []
            
            current_entries.append((key, value, version))
            current_file_size += entry_size
        
        # 写入最后一个文件
        if current_entries:
            self._write_file(current_file_id, current_entries)
        
        self.current_file_id = current_file_id + 1
    
    def _write_file(self, file_id: int, entries: List[Tuple[bytes, bytes, int]]):
        """写入单个文件（使用标准格式，包含文件魔数）"""
        from .file_format import SSTableFormat, FileMagic
        
        filepath = self.filepath.parent / f"{self.filepath.stem}_{file_id:06d}.sst"
        
        # 先收集所有数据，然后一次性写入
        index_data = {}
        data_parts = []
        
        # 准备数据部分
        timestamp = time.time()
        for key, value, version in entries:
            offset = len(b''.join(data_parts)) + SSTableFormat.HEADER_SIZE
            index_data[key] = (file_id, offset)
            
            # 准备条目数据
            entry_data = struct.pack('I', len(key)) + key
            entry_data += struct.pack('I', len(value)) + value
            entry_data += struct.pack('I', version)
            entry_data += struct.pack('d', timestamp)
            data_parts.append(entry_data)
        
        # 写入文件
        with open(filepath, 'wb') as f:
            # 写入文件头
            key_count = len(entries)
            data_offset = SSTableFormat.HEADER_SIZE
            index_offset = 0  # 稍后填充
            
            SSTableFormat.write_header(f, key_count, data_offset, index_offset)
            
            # 写入数据
            for entry_data in data_parts:
                f.write(entry_data)
            
            # 写入索引
            index_offset = f.tell()
            index_bytes = json.dumps(
                {k.hex(): (fid, off) for k, (fid, off) in index_data.items()},
                default=str
            ).encode()
            f.write(struct.pack('I', len(index_bytes)))
            f.write(index_bytes)
            
            # 写入footer（使用标准格式）
            # 先关闭文件，重新打开读取数据部分用于计算checksum
            file_size = f.tell()
        
        # 重新打开文件读取数据部分用于计算checksum
        with open(filepath, 'r+b') as f:
            f.seek(0)
            data = f.read(index_offset)
            f.seek(file_size)  # 回到文件末尾
            SSTableFormat.write_footer(f, index_offset, data)
            
            self.file_sizes[file_id] = f.tell()
            self.index.update(index_data)
    
    def get(self, key: bytes) -> Optional[Tuple[bytes, int]]:
        """从分片SSTable读取数据（支持标准格式和旧格式）"""
        if not self._loaded:
            self._load_index()
        
        if key not in self.index:
            return None
        
        from .file_format import SSTableFormat, FileMagic
        
        file_id, offset = self.index[key]
        filepath = self.filepath.parent / f"{self.filepath.stem}_{file_id:06d}.sst"
        
        if not filepath.exists():
            return None
        
        with open(filepath, 'rb') as f:
            # 检查文件格式
            magic = f.read(4)
            f.seek(0)
            
            if magic == FileMagic.SST:
                # 标准格式：使用SSTableFormat读取
                f.seek(offset)
                entry = SSTableFormat.read_entry(f)
                if entry:
                    read_key, value, version, timestamp = entry
                    if read_key == key:
                        return (value, version)
            else:
                # 旧格式：直接读取
                f.seek(offset)
                key_len = struct.unpack('I', f.read(4))[0]
                read_key = f.read(key_len)
                
                if read_key != key:
                    return None
                
                value_len = struct.unpack('I', f.read(4))[0]
                value = f.read(value_len)
                version = struct.unpack('I', f.read(4))[0]
                
                return (value, version)
        
        return None
    
    def _load_index(self):
        """加载所有文件的索引"""
        # 查找所有相关文件（文件名格式：sstable_{timestamp}_{file_id:06d}.sst）
        # 或者：{base_name}_{file_id:06d}.sst
        base_name = self.filepath.stem
        
        # 尝试两种模式
        patterns = [
            f"{base_name}_*.sst",  # 如果base_name已经是完整名称
            f"sstable_*_{base_name.rsplit('_', 1)[-1] if '_' in base_name else ''}.sst"  # 如果base_name是时间戳
        ]
        
        found_files = []
        for pattern in patterns:
            for filepath in self.filepath.parent.glob(pattern):
                if filepath not in found_files:
                    found_files.append(filepath)
        
        # 如果没找到，尝试直接使用当前文件
        if not found_files and self.filepath.exists():
            found_files = [self.filepath]
        
        for filepath in found_files:
            # 提取文件ID（从文件名最后一部分）
            try:
                # 文件名格式：sstable_{timestamp}_{file_id:06d}.sst
                parts = filepath.stem.split('_')
                if len(parts) >= 3:
                    # 最后一部分是file_id
                    file_id = int(parts[-1])
                else:
                    file_id = 0
            except (ValueError, IndexError):
                file_id = 0
            
            self._load_file_index(filepath, file_id)
        
        self._loaded = True
    
    def _load_file_index(self, filepath: Path, file_id: int):
        """加载单个文件的索引（支持标准格式和旧格式）"""
        if not filepath.exists():
            return
        
        from .file_format import SSTableFormat, FileMagic
        
        with open(filepath, 'rb') as f:
            # 检查文件魔数
            magic = f.read(4)
            f.seek(0)
            
            if magic == FileMagic.SST:
                # 标准格式：从header读取
                try:
                    key_count, index_offset, footer_offset = SSTableFormat.read_header(f)
                    # 读取索引
                    f.seek(index_offset)
                    index_len = struct.unpack('I', f.read(4))[0]
                    if index_len == 0:
                        return
                    index_json = json.loads(f.read(index_len).decode())
                    
                    # 更新索引（支持列表和元组格式）
                    for k_hex, value in index_json.items():
                        # 支持 [file_id, offset] 或 (file_id, offset) 格式
                        if isinstance(value, (list, tuple)) and len(value) >= 2:
                            fid, offset = value[0], value[1]
                            # 使用传入的file_id（从文件名提取），而不是索引中的fid
                            self.index[bytes.fromhex(k_hex)] = (file_id, offset)
                        elif isinstance(value, (int, float)):
                            # 旧格式：只有offset
                            self.index[bytes.fromhex(k_hex)] = (file_id, int(value))
                except Exception:
                    # 如果标准格式读取失败，尝试旧格式
                    self._load_file_index_legacy(f, file_id)
            else:
                # 旧格式：从文件末尾读取
                self._load_file_index_legacy(f, file_id)
    
    def _load_file_index_legacy(self, f, file_id: int):
        """加载旧格式索引（向后兼容）"""
        f.seek(-8, 2)
        index_offset = struct.unpack('Q', f.read(8))[0]
        
        if index_offset == 0 or index_offset >= f.tell():
            return
        
        f.seek(index_offset)
        index_len = struct.unpack('I', f.read(4))[0]
        if index_len == 0:
            return
        
        index_json = json.loads(f.read(index_len).decode())
        
        for k_hex, value in index_json.items():
            if isinstance(value, (list, tuple)) and len(value) >= 2:
                fid, offset = value[0], value[1]
                self.index[bytes.fromhex(k_hex)] = (file_id, offset)
            elif isinstance(value, (int, float)):
                self.index[bytes.fromhex(k_hex)] = (file_id, int(value))


class ShardedLSMTree:
    """
    支持分片的LSM树
    支持大数据量、文件大小限制、自动分割
    """
    
    def __init__(self, 
                 data_dir: str = "./data/lsm",
                 shard_count: int = 256,
                 max_file_size: int = 256 * 1024 * 1024,
                 config=None):  # 256MB
        """
        Args:
            data_dir: 数据目录
            shard_count: 分片数量
            max_file_size: 单个文件最大大小
            config: 配置对象（DatabaseConfig）
        """
        self.data_dir = Path(data_dir)
        self.config = config
        os.makedirs(data_dir, exist_ok=True)
        
        # 优化：缓存配置值，避免重复访问（性能关键路径）
        if config:
            self._memtable_max_size = config.lsm_memtable_max_size
            self._enable_skip_list = config.lsm_enable_skip_list
            self._enable_cython = config.lsm_enable_cython
        else:
            self._memtable_max_size = 10 * 1024 * 1024
            self._enable_skip_list = False
            self._enable_cython = False
        
        # 分片管理器
        from ..sharding import ShardManager
        self.shard_manager = ShardManager(
            data_dir=str(self.data_dir),
            shard_count=shard_count,
            max_file_size=max_file_size
        )
        
        # 每个分片的MemTable
        self.memtables: Dict[int, MemTable] = {}
        self.immutable_memtables: Dict[int, List[MemTable]] = {}
        self.sstables: Dict[int, List[ShardedSSTable]] = {}
        
        self.lock = threading.RLock()
        self.max_file_size = max_file_size
        
        # 加载已有的SSTable
        self._load_sstables()
    
    def put(self, key: bytes, value: bytes, version: int) -> bool:
        """写入数据（自动分片）"""
        with self.lock:
            shard_id = self.shard_manager.get_shard_id(key)
            
            # 获取或创建MemTable（从配置读取）
            if shard_id not in self.memtables:
                # 从缓存的配置值创建MemTable（优化：不传递config对象，直接传值）
                self.memtables[shard_id] = MemTable(
                    max_size=self._memtable_max_size,
                    use_skip_list=self._enable_skip_list,
                    use_cython=self._enable_cython,
                    config=None  # 不传递config对象，避免开销
                )
            
            memtable = self.memtables[shard_id]
            
            if not memtable.put(key, value, version):
                # MemTable满了，刷新到磁盘
                self._flush_memtable(shard_id)
                # 创建新的MemTable（使用缓存的配置值）
                self.memtables[shard_id] = MemTable(
                    max_size=self._memtable_max_size,
                    use_skip_list=self._enable_skip_list,
                    use_cython=self._enable_cython,
                    config=None  # 不传递config对象，避免开销
                )
                self.memtables[shard_id].put(key, value, version)
            
            return True
    
    def batch_put(self, items: List[Tuple[bytes, bytes, int]]) -> bool:
        """
        批量写入（高性能版本，对标LevelDB，按分片分组，减少锁竞争）
        优化：减少锁获取次数，批量处理
        Args:
            items: [(key, value, version), ...]
        """
        # 按分片分组（不加锁，提高性能）
        # 优化：减少函数调用和字典查找开销
        # 优化：批量计算分片ID，减少函数调用开销
        shard_groups = {}
        shard_count = self.shard_manager.shard_count
        
        # 优化：对于HASH策略，使用内置hash批量计算
        from ..sharding import ShardingStrategy
        if self.shard_manager.strategy == ShardingStrategy.HASH and not self.shard_manager.shard_func:
            # 使用内置hash（更快）
            # 优化：批量计算，减少函数调用开销
            items_len = len(items)
            for idx in range(items_len):
                key, value, version = items[idx]
                hash_value = hash(key)
                if hash_value < 0:
                    hash_value = -hash_value
                shard_id = hash_value % shard_count
                # 优化：直接检查并初始化，避免setdefault的开销
                if shard_id not in shard_groups:
                    shard_groups[shard_id] = []
                shard_groups[shard_id].append((key, value, version))
        else:
            # 其他策略使用原方法
            get_shard_id = self.shard_manager.get_shard_id
            items_len = len(items)
            for idx in range(items_len):
                key, value, version = items[idx]
                shard_id = get_shard_id(key)
                if shard_id not in shard_groups:
                    shard_groups[shard_id] = []
                shard_groups[shard_id].append((key, value, version))
        
        # 优化：对于大批量数据，一次性处理所有分片，减少锁获取次数
        # 优化：降低阈值，2K以上使用大批量策略，减少锁竞争（匹配批量大小）
        items_len = len(items)
        if items_len >= 2000:
            # 大批量：一次性处理所有分片
            # 优化：减少锁持有时间，只在需要时获取锁
            memtables_dict = self.memtables
            setdefault_memtables = memtables_dict.setdefault
            
            with self.lock:
                for shard_id, shard_items in shard_groups.items():
                    # 确保MemTable存在（优化：使用缓存的配置值）
                    if shard_id not in memtables_dict:
                        memtables_dict[shard_id] = MemTable(
                            max_size=self._memtable_max_size,
                            use_skip_list=self._enable_skip_list,
                            use_cython=self._enable_cython,
                            config=None  # 不传递config对象，避免开销
                        )
                    memtable = memtables_dict[shard_id]
                    
                    # 使用批量插入接口
                    remaining = shard_items
                    while remaining:
                        success_count = memtable.put_batch(remaining)
                        
                        if success_count == 0:
                            # MemTable满了，刷新
                            self._flush_memtable(shard_id)
                            # 从缓存的配置值创建MemTable
                            memtable = MemTable(
                                max_size=self._memtable_max_size,
                                use_skip_list=self._enable_skip_list,
                                use_cython=self._enable_cython,
                                config=None  # 不传递config对象，避免开销
                            )
                            memtables_dict[shard_id] = memtable
                            success_count = memtable.put_batch(remaining)
                            if success_count == 0:
                                break  # 单个条目太大
                        
                        remaining = remaining[success_count:]
        else:
            # 小批量：对每个分片批量写入（减少锁竞争，对标LevelDB）
            for shard_id, shard_items in shard_groups.items():
                # 确保MemTable存在（一次锁，使用跳表优化）
                with self.lock:
                    if shard_id not in self.memtables:
                        # 从缓存的配置值创建MemTable
                        self.memtables[shard_id] = MemTable(
                            max_size=self._memtable_max_size,
                            use_skip_list=self._enable_skip_list,
                            use_cython=self._enable_cython,
                            config=None  # 不传递config对象，避免开销
                        )
                    memtable = self.memtables[shard_id]
                
                # 使用批量插入接口（减少锁开销）
                remaining = shard_items
                while remaining:
                    with self.lock:
                        memtable = self.memtables[shard_id]
                        success_count = memtable.put_batch(remaining)
                    
                    if success_count == 0:
                        # MemTable满了，刷新
                        with self.lock:
                            self._flush_memtable(shard_id)
                            # 从缓存的配置值创建MemTable
                            self.memtables[shard_id] = MemTable(
                                max_size=self._memtable_max_size,
                                use_skip_list=self._enable_skip_list,
                                use_cython=self._enable_cython,
                                config=None  # 不传递config对象，避免开销
                            )
                            memtable = self.memtables[shard_id]
                            success_count = memtable.put_batch(remaining)
                            if success_count == 0:
                                break  # 单个条目太大
                    
                    remaining = remaining[success_count:]
        
        return True
    
    def get(self, key: bytes) -> Optional[Tuple[bytes, int]]:
        """读取数据（自动定位分片）"""
        with self.lock:
            shard_id = self.shard_manager.get_shard_id(key)
            
            # 1. 先查MemTable
            if shard_id in self.memtables:
                result = self.memtables[shard_id].get(key)
                if result:
                    return result
            
            # 2. 查不可变MemTable
            if shard_id in self.immutable_memtables:
                for imm_memtable in reversed(self.immutable_memtables[shard_id]):
                    result = imm_memtable.get(key)
                    if result:
                        return result
            
            # 3. 查SSTable
            if shard_id in self.sstables:
                for sstable in reversed(self.sstables[shard_id]):
                    result = sstable.get(key)
                    if result:
                        return result
            
            return None
    
    def _flush_memtable(self, shard_id: int, sync: bool = False):
        """
        将MemTable刷新到磁盘（支持文件分割）
        Args:
            shard_id: 分片ID
            sync: 是否同步刷新（True=等待完成，False=异步）
        """
        if shard_id not in self.memtables:
            return
        
        memtable = self.memtables[shard_id]
        if memtable.size == 0:
            return
        
        # 将当前MemTable标记为不可变
        immutable = memtable
        if shard_id not in self.immutable_memtables:
            self.immutable_memtables[shard_id] = []
        self.immutable_memtables[shard_id].append(immutable)
        # 从缓存的配置值创建MemTable
        self.memtables[shard_id] = MemTable(
            max_size=self._memtable_max_size,
            use_skip_list=self._enable_skip_list,
            use_cython=self._enable_cython,
            config=None  # 不传递config对象，避免开销
        )
        
        # 刷新到磁盘
        def do_flush():
            try:
                # 获取分片路径
                shard_path = self.shard_manager.get_shard_path(shard_id)
                file_id = self.shard_manager.get_next_file_id(shard_id)
                sstable_path = shard_path / f"sstable_{int(time.time() * 1000000)}_{file_id:06d}.sst"
                
                # 创建分片SSTable
                entries = list(immutable.get_all())
                if entries:
                    sstable = ShardedSSTable(str(sstable_path), self.max_file_size)
                    sstable.write(entries)
                    
                    with self.lock:
                        if shard_id not in self.sstables:
                            self.sstables[shard_id] = []
                        self.sstables[shard_id].append(sstable)
                        
                        # 更新统计
                        total_size = sum(sstable.file_sizes.values())
                        self.shard_manager.update_shard_stats(shard_id, total_size)
                        
                        # 清理不可变MemTable
                        if immutable in self.immutable_memtables.get(shard_id, []):
                            immutable.clear()
                            self.immutable_memtables[shard_id].remove(immutable)
            except Exception as e:
                import traceback
                print(f"刷新分片{shard_id}的MemTable失败: {e}")
                traceback.print_exc()
        
        if sync:
            # 同步刷新：直接执行，等待完成
            do_flush()
        else:
            # 异步刷新：启动线程，不阻塞
            flush_thread = threading.Thread(target=do_flush, daemon=True)
            flush_thread.start()
    
    def _load_sstables(self):
        """加载已有的SSTable（按分片组织）"""
        for shard_id in range(self.shard_manager.shard_count):
            shard_path = self.shard_manager.get_shard_path(shard_id)
            
            if not shard_path.exists():
                continue
            
            sstable_files = sorted(shard_path.glob("sstable_*.sst"))
            
            if sstable_files:
                if shard_id not in self.sstables:
                    self.sstables[shard_id] = []
                
                # 按时间戳分组（相同时间戳的文件属于同一个SSTable）
                file_groups: Dict[int, List[Path]] = {}
                for file_path in sstable_files:
                    # 提取时间戳
                    parts = file_path.stem.split('_')
                    if len(parts) >= 2:
                        try:
                            timestamp = int(parts[1])
                            if timestamp not in file_groups:
                                file_groups[timestamp] = []
                            file_groups[timestamp].append(file_path)
                        except ValueError:
                            continue
                
                # 为每个时间戳创建ShardedSSTable
                for timestamp, files in file_groups.items():
                    if files:
                        # 使用第一个文件作为基础路径
                        base_path = files[0]
                        sstable = ShardedSSTable(str(base_path), self.max_file_size)
                        sstable._load_index()
                        self.sstables[shard_id].append(sstable)
    
    def flush(self):
        """强制刷新所有MemTable到磁盘（同步，确保数据持久化）"""
        with self.lock:
            # 强制刷新所有有数据的MemTable（同步刷新）
            flushed_shards = set()
            for shard_id in list(self.memtables.keys()):
                memtable = self.memtables[shard_id]
                if memtable.size > 0:  # 只刷新有数据的MemTable
                    self._flush_memtable(shard_id, sync=True)  # 同步刷新
                    flushed_shards.add(shard_id)
            
            # 保存分片统计
            self.shard_manager.save_shard_stats()
    
    def get_shard_info(self) -> Dict[int, Dict]:
        """获取所有分片信息"""
        with self.lock:
            info = {}
            for shard_id in range(self.shard_manager.shard_count):
                info[shard_id] = {
                    'memtable_size': self.memtables.get(shard_id, MemTable()).size,
                    'sstable_count': len(self.sstables.get(shard_id, [])),
                    'stats': self.shard_manager.get_shard_stats(shard_id)
                }
            return info

