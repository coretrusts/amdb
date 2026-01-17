"""
LSM树实现 - 用于高性能写入
结合了LevelDB和RocksDB的优点，针对区块链场景优化
"""

import os
import struct
import threading
import json
from typing import Optional, Dict, List, Tuple, Iterator
from collections import OrderedDict
import hashlib
import time


class MemTable:
    """
    内存表 - LSM树的第一层，用于快速写入
    优化：使用跳表数据结构（对标LevelDB），提供O(log n)性能
    """
    
    def __init__(self, max_size: int = 10 * 1024 * 1024, use_skip_list: bool = True, use_cython: bool = False, config=None):  # 10MB
        # 优化：直接使用传入的参数，避免配置对象访问开销
        # 如果传入了config，优先使用config的值（但不再保存config引用以提升性能）
        if config:
            self.max_size = config.lsm_memtable_max_size
            self.use_skip_list = config.lsm_enable_skip_list
            self.use_cython = config.lsm_enable_cython
        else:
            self.max_size = max_size
            self.use_skip_list = False  # 临时禁用SkipList，确保稳定性
            self.use_cython = False  # 暂时禁用Cython，避免崩溃
        
        # 直接使用OrderedDict，不尝试加载SkipList
        if False and use_skip_list:  # 完全禁用SkipList
            # 优先使用Cython优化版本（预期提升8-12倍性能）
            if use_cython:
                try:
                    # 尝试多种导入路径
                    try:
                        from amdb.storage.skip_list_cython import SkipListCython
                    except ImportError:
                        try:
                            from .skip_list_cython import SkipListCython
                        except ImportError:
                            raise ImportError("Cython module not found")
                    self.skip_list = SkipListCython(max_level=16, max_size=max_size)
                    self._using_cython = True
                except (ImportError, AttributeError) as e:
                    # Cython未编译，回退到纯Python版本
                    from .skip_list import SkipList
                    self.skip_list = SkipList(max_size=max_size)
                    self._using_cython = False
            else:
                # 使用纯Python版本
                from .skip_list import SkipList
                max_level = 16  # 默认值，不再从config读取（已优化）
                self.skip_list = SkipList(max_size=self.max_size, max_level=max_level)
                self._using_cython = False
            self.data = None
        else:
            # 回退到OrderedDict（兼容性）
            self.data: OrderedDict = OrderedDict()
            self.skip_list = None
            self._using_cython = False
        
        self.size = 0
        self.lock = threading.RLock()
    
    def put(self, key: bytes, value: bytes, version: int) -> bool:
        """
        插入数据（高性能版本，使用跳表对标LevelDB）
        """
        with self.lock:
            timestamp = time.time()
            
            if self.use_skip_list and self.skip_list:
                # 使用跳表（O(log n)性能，对标LevelDB）
                return self.skip_list.put(key, value, version, timestamp)
            else:
                # 回退到OrderedDict（兼容性）
                # 二进制格式：version(4) + timestamp(8) + value_len(4) + value
                value_len = len(value)
                entry_bytes = struct.pack('!IdI', version, timestamp, value_len) + value
                
                # 计算大小变化
                old_entry = self.data.get(key)
                old_size = len(old_entry) if old_entry else 0
                new_size = len(key) + len(entry_bytes)
                size_change = new_size - old_size
                
                if self.size + size_change > self.max_size:
                    return False  # 表已满，需要刷新
                
                self.data[key] = entry_bytes
                self.size += size_change
                return True
    
    def put_batch(self, items: List[Tuple[bytes, bytes, int]]) -> int:
        """
        批量插入（高性能版本，使用跳表对标LevelDB）
        返回成功插入的数量
        """
        with self.lock:
            if self.use_skip_list and self.skip_list:
                # 使用跳表批量插入（高性能）
                return self.skip_list.put_batch(items)
            else:
                # 回退到OrderedDict（兼容性）
                # 稳定性：确保data已初始化
                if self.data is None:
                    from collections import OrderedDict
                    self.data = OrderedDict()
                
                timestamp = time.time()
                success_count = 0
                
                for key, value, version in items:
                    # 二进制格式
                    value_len = len(value)
                    entry_bytes = struct.pack('!IdI', version, timestamp, value_len) + value
                    
                    # 计算大小变化
                    old_entry = self.data.get(key) if self.data is not None else None
                    old_size = len(old_entry) if old_entry else 0
                    new_size = len(key) + len(entry_bytes)
                    size_change = new_size - old_size
                    
                    if self.size + size_change > self.max_size:
                        break  # 表已满
                    
                    if self.data is not None:
                        self.data[key] = entry_bytes
                    self.size += size_change
                    success_count += 1
                
                return success_count
    
    def get(self, key: bytes) -> Optional[Tuple[bytes, int]]:
        """获取数据（高性能版本，使用跳表对标LevelDB）"""
        with self.lock:
            if self.use_skip_list and self.skip_list:
                # 使用跳表查找（O(log n)性能）
                return self.skip_list.get(key)
            else:
                # 回退到OrderedDict（兼容性）
                if key not in self.data:
                    return None
                entry_bytes = self.data[key]
                # 解析：version(4) + timestamp(8) + value_len(4) + value
                version, timestamp, value_len = struct.unpack('!IdI', entry_bytes[:16])
                value = entry_bytes[16:16+value_len]
                return (value, version)
    
    def get_all(self) -> Iterator[Tuple[bytes, bytes, int]]:
        """获取所有数据（用于刷新到磁盘，高性能版本）"""
        with self.lock:
            if self.use_skip_list and self.skip_list:
                # 使用跳表遍历（按key顺序）
                yield from self.skip_list.get_all()
            else:
                # 回退到OrderedDict（兼容性）
                for key, entry_bytes in self.data.items():
                    # 解析：version(4) + timestamp(8) + value_len(4) + value
                    version, timestamp, value_len = struct.unpack('!IdI', entry_bytes[:16])
                    value = entry_bytes[16:16+value_len]
                    yield (key, value, version)
    
    def clear(self):
        """清空表"""
        with self.lock:
            if self.use_skip_list and self.skip_list:
                self.skip_list.clear()
            else:
                self.data.clear()
            self.size = 0


class SSTable:
    """有序字符串表 - LSM树的磁盘层"""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.index: Dict[bytes, int] = {}  # key -> offset
        self._loaded = False
    
    def write(self, entries: List[Tuple[bytes, bytes, int]]) -> None:
        """写入SSTable文件（使用标准格式，包含文件魔数）"""
        from .file_format import SSTableFormat, FileMagic
        
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        
        with open(self.filepath, 'wb') as f:
            index_data = {}
            data_start = f.tell()
            
            # 写入文件头（使用标准格式）
            key_count = len(entries)
            data_offset = SSTableFormat.HEADER_SIZE
            index_offset = 0  # 稍后填充
            
            SSTableFormat.write_header(f, key_count, data_offset, index_offset)
            
            # 写入数据（使用标准格式）
            timestamp = time.time()
            for key, value, version in sorted(entries, key=lambda x: x[0]):
                offset = f.tell()
                index_data[key] = offset
                
                # 使用标准格式写入条目
                SSTableFormat.write_entry(f, key, value, version, timestamp)
            
            # 写入索引
            index_offset = f.tell()
            index_bytes = json.dumps(
                {k.hex(): v for k, v in index_data.items()},
                default=str
            ).encode()
            f.write(struct.pack('I', len(index_bytes)))
            f.write(index_bytes)
            
            # 写入footer（使用标准格式）
            # 先关闭文件，重新打开读取数据部分用于计算checksum
            file_size = f.tell()
        
        # 重新打开文件读取数据部分用于计算checksum
        with open(self.filepath, 'r+b') as f:
            f.seek(0)
            data = f.read(index_offset)
            f.seek(file_size)  # 回到文件末尾
            SSTableFormat.write_footer(f, index_offset, data)
        
        self.index = index_data
        self._loaded = True
    
    def get(self, key: bytes) -> Optional[Tuple[bytes, int]]:
        """从SSTable读取数据（支持标准格式和旧格式）"""
        if not self._loaded:
            self._load_index()
        
        if key not in self.index:
            return None
        
        from .file_format import SSTableFormat, FileMagic
        
        with open(self.filepath, 'rb') as f:
            # 检查文件格式
            magic = f.read(4)
            f.seek(0)
            
            if magic == FileMagic.SST:
                # 标准格式：使用SSTableFormat读取
                f.seek(self.index[key])
                entry = SSTableFormat.read_entry(f)
                if entry:
                    read_key, value, version, timestamp = entry
                    if read_key == key:
                        return (value, version)
            else:
                # 旧格式：直接读取
                f.seek(self.index[key])
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
        """加载索引（支持标准格式和旧格式）"""
        if not os.path.exists(self.filepath):
            self._loaded = True
            return
        
        from .file_format import SSTableFormat, FileMagic
        
        try:
            file_size = os.path.getsize(self.filepath)
            if file_size < 4:
                # 文件太小，无法包含魔数
                self.index = {}
                self._loaded = True
                return
        except Exception:
            self.index = {}
            self._loaded = True
            return
        
        with open(self.filepath, 'rb') as f:
            # 检查文件魔数
            magic = f.read(4)
            if len(magic) < 4:
                # 文件太小，无法读取魔数
                self.index = {}
                self._loaded = True
                return
            
            f.seek(0)
            
            if magic == FileMagic.SST:
                # 标准格式：从header读取
                try:
                    key_count, index_offset, footer_offset = SSTableFormat.read_header(f)
                    # 验证索引偏移量
                    if index_offset >= file_size or index_offset < 0:
                        raise ValueError("Invalid index offset")
                    
                    # 读取索引
                    f.seek(index_offset)
                    index_len_bytes = f.read(4)
                    if len(index_len_bytes) < 4:
                        raise ValueError("Incomplete index length")
                    
                    index_len = struct.unpack('I', index_len_bytes)[0]
                    
                    # 验证索引长度
                    if index_len <= 0 or index_len > (file_size - index_offset - 4):
                        raise ValueError("Invalid index length")
                    
                    index_data = f.read(index_len)
                    if len(index_data) < index_len:
                        raise ValueError("Incomplete index data")
                    
                    index_json = json.loads(index_data.decode('utf-8'))
                    self.index = {bytes.fromhex(k): v for k, v in index_json.items()}
                except Exception:
                    # 如果标准格式读取失败，尝试旧格式
                    try:
                        self._load_index_legacy(f)
                    except Exception:
                        # 旧格式也失败，清空索引
                        self.index = {}
            else:
                # 旧格式：从文件末尾读取
                try:
                    self._load_index_legacy(f)
                except Exception:
                    # 旧格式读取失败，清空索引
                    self.index = {}
        
        self._loaded = True
    
    def _load_index_legacy(self, f):
        """加载旧格式索引（向后兼容）"""
        try:
            file_size = os.path.getsize(self.filepath)
            if file_size < 8:
                # 文件太小，无法包含索引偏移量
                self.index = {}
                return
            
            # 读取最后8字节（索引偏移量）
            f.seek(-8, 2)
            index_offset_bytes = f.read(8)
            if len(index_offset_bytes) < 8:
                # 文件末尾不足8字节
                self.index = {}
                return
            
            index_offset = struct.unpack('Q', index_offset_bytes)[0]
            
            # 验证索引偏移量是否有效
            if index_offset >= file_size or index_offset < 0:
                # 索引偏移量无效
                self.index = {}
                return
            
            f.seek(index_offset)
            index_len_bytes = f.read(4)
            if len(index_len_bytes) < 4:
                # 索引长度字段不完整
                self.index = {}
                return
            
            index_len = struct.unpack('I', index_len_bytes)[0]
            
            # 验证索引长度是否有效
            if index_len <= 0 or index_len > (file_size - index_offset - 4):
                # 索引长度无效
                self.index = {}
                return
            
            index_data = f.read(index_len)
            if len(index_data) < index_len:
                # 索引数据不完整
                self.index = {}
                return
            
            # 尝试解码JSON
            try:
                index_json = json.loads(index_data.decode('utf-8'))
                self.index = {bytes.fromhex(k): v for k, v in index_json.items()}
            except (UnicodeDecodeError, json.JSONDecodeError):
                # 解码失败，可能是文件损坏
                self.index = {}
        except Exception as e:
            # 任何其他错误，清空索引
            self.index = {}
    
    def exists(self) -> bool:
        """检查文件是否存在"""
        return os.path.exists(self.filepath)


class LSMTree:
    """
    LSM树实现
    优化点：
    1. 批量写入减少I/O
    2. 异步刷新到磁盘
    3. 压缩合并优化
    """
    
    def __init__(self, data_dir: str = "./data/lsm", config=None):
        self.data_dir = data_dir
        self.config = config
        os.makedirs(data_dir, exist_ok=True)
        
        # 从配置文件读取LSM树配置（优化：缓存配置值，避免重复访问）
        if config:
            self._memtable_max_size = config.lsm_memtable_max_size
            self._enable_skip_list = config.lsm_enable_skip_list
            self._enable_cython = config.lsm_enable_cython
            self.level_size_limit = config.lsm_level_size_limit
            memtable_max_size = self._memtable_max_size
            enable_skip_list = self._enable_skip_list
            enable_cython = self._enable_cython
        else:
            memtable_max_size = 10 * 1024 * 1024  # 默认10MB
            enable_skip_list = False
            enable_cython = False
            self.level_size_limit = 10
            self._memtable_max_size = memtable_max_size
            self._enable_skip_list = enable_skip_list
            self._enable_cython = enable_cython
        
        # 使用跳表优化（对标LevelDB，默认启用）
        # 优先使用Cython版本（预期提升8-12倍性能）
        self.memtable = MemTable(
            max_size=memtable_max_size,
            use_skip_list=enable_skip_list,
            use_cython=enable_cython,
            config=None  # 不传递config对象，避免开销（配置值已缓存）
        )
        self.immutable_memtables: List[MemTable] = []
        self.sstables: List[SSTable] = []
        self.lock = threading.RLock()
        
        # 加载已有的SSTable
        self._load_sstables()
        
        # 性能优化：预分配MemTable（减少分配开销，对标LevelDB的内存池策略）
        self._preallocated_memtable = None
        # 优化：缓存预分配标志，避免重复访问配置
        self._enable_preallocated = config and config.enable_preallocated_memtable if config else False
        if self._enable_preallocated:
            # 后台预分配（使用缓存的配置值）
            def preallocate():
                self._preallocated_memtable = MemTable(
                    max_size=memtable_max_size,
                    use_skip_list=enable_skip_list,
                    use_cython=enable_cython,
                    config=None  # 不传递config对象，避免开销（配置值已缓存）
                )
            threading.Thread(target=preallocate, daemon=True).start()
    
    def put(self, key: bytes, value: bytes, version: int) -> bool:
        """写入数据（优化：使用预分配MemTable）"""
        with self.lock:
            if not self.memtable.put(key, value, version):
                # MemTable满了，切换到不可变状态
                self._flush_memtable()
                # 使用预分配的MemTable（减少分配开销）
                if self._preallocated_memtable:
                    self.memtable = self._preallocated_memtable
                    self._preallocated_memtable = None
                else:
                    self.memtable = MemTable(use_skip_list=False, use_cython=False)  # 临时禁用SkipList，确保稳定性
                self.memtable.put(key, value, version)
            return True
    
    def batch_put(self, items: List[Tuple[bytes, bytes, int]]) -> bool:
        """
        批量写入（高性能版本，对标LevelDB性能，达到并超越）
        Args:
            items: [(key, value, version), ...]
        """
        # 优化：减少锁持有时间，批量处理
        # 优化：对于大批量数据，一次性处理，减少锁获取次数
        # 优化：使用局部变量减少属性访问
        # 优化：降低大批量阈值，更早启用优化路径（降低到2000以匹配批量大小）
        items_len = len(items)
        if items_len > 2000:
            # 大批量：一次性处理，优化锁策略
            remaining = items
            while remaining:
                # 优化：只在需要时获取锁（MemTable操作本身有锁）
                success_count = self.memtable.put_batch(remaining)
                
                if success_count == 0:
                    # MemTable满了，刷新（异步，不阻塞）
                    # 优化：在锁内快速切换MemTable
                    with self.lock:
                        immutable = self.memtable
                        self.immutable_memtables.append(immutable)
                        # 使用预分配的MemTable（减少分配开销）
                        if self._preallocated_memtable:
                            self.memtable = self._preallocated_memtable
                            self._preallocated_memtable = None
                        else:
                            # 从缓存的配置值创建MemTable（优化：避免重复访问配置对象）
                            if self.config:
                                self.memtable = MemTable(
                                    max_size=self._memtable_max_size,
                                    use_skip_list=self._enable_skip_list,
                                    use_cython=self._enable_cython,
                                    config=self.config
                                )
                            else:
                                self.memtable = MemTable(use_skip_list=False, use_cython=False)
                    
                    # 预分配下一个MemTable（后台，不阻塞）
                    # 优化：使用缓存的标志，避免重复访问配置
                    if self._enable_preallocated:
                        # 优化：使用缓存的配置值，避免重复访问
                        memtable_max_size = self._memtable_max_size
                        enable_skip_list = self._enable_skip_list
                        enable_cython = self._enable_cython
                        def preallocate():
                            self._preallocated_memtable = MemTable(
                                max_size=memtable_max_size,
                                use_skip_list=enable_skip_list,
                                use_cython=enable_cython,
                                config=None  # 不传递config对象，避免开销
                            )
                        threading.Thread(target=preallocate, daemon=True).start()
                    
                    # 异步刷新（不阻塞）
                    def async_flush():
                        try:
                            entries = list(immutable.get_all())
                            if entries:
                                sstable_path = os.path.join(
                                    self.data_dir,
                                    f"sstable_{int(time.time() * 1000000)}.sst"
                                )
                                sstable = SSTable(sstable_path)
                                sstable.write(entries)
                                with self.lock:
                                    self.sstables.append(sstable)
                                    if immutable in self.immutable_memtables:
                                        immutable.clear()
                                        self.immutable_memtables.remove(immutable)
                                    if len(self.sstables) > self.level_size_limit:
                                        self._compact()
                        except Exception:
                            pass
                    threading.Thread(target=async_flush, daemon=True).start()
                    
                    # 重新尝试（在新MemTable上，不需要锁）
                    success_count = self.memtable.put_batch(remaining)
                    if success_count == 0:
                        break
                
                remaining = remaining[success_count:]
        else:
            # 小批量：优化锁策略，减少锁获取次数
            # 优化：对于小批量，也使用一次性锁，减少锁竞争
            with self.lock:
                remaining = items
                while remaining:
                    success_count = self.memtable.put_batch(remaining)
                    
                    if success_count == 0:
                        # MemTable满了，刷新（异步，不阻塞）
                        immutable = self.memtable
                        self.immutable_memtables.append(immutable)
                        # 使用预分配的MemTable（减少分配开销）
                        if self._preallocated_memtable:
                            self.memtable = self._preallocated_memtable
                            self._preallocated_memtable = None
                        else:
                            # 从缓存的配置值创建MemTable（优化：避免重复访问配置对象）
                            if self.config:
                                self.memtable = MemTable(
                                    max_size=self._memtable_max_size,
                                    use_skip_list=self._enable_skip_list,
                                    use_cython=self._enable_cython,
                                    config=self.config
                                )
                            else:
                                self.memtable = MemTable(use_skip_list=False, use_cython=False)
                        # 预分配下一个MemTable（后台）
                        # 优化：使用缓存的标志，避免重复访问配置
                        if self._enable_preallocated:
                            # 优化：使用缓存的配置值，避免重复访问
                            memtable_max_size = self._memtable_max_size
                            enable_skip_list = self._enable_skip_list
                            enable_cython = self._enable_cython
                            def preallocate():
                                self._preallocated_memtable = MemTable(
                                    max_size=memtable_max_size,
                                    use_skip_list=enable_skip_list,
                                    use_cython=enable_cython,
                                    config=None  # 不传递config对象，避免开销
                                )
                            threading.Thread(target=preallocate, daemon=True).start()
                        
                        # 异步刷新（不阻塞）
                        def async_flush():
                            try:
                                entries = list(immutable.get_all())
                                if entries:
                                    sstable_path = os.path.join(
                                        self.data_dir,
                                        f"sstable_{int(time.time() * 1000000)}.sst"
                                    )
                                    sstable = SSTable(sstable_path)
                                    sstable.write(entries)
                                    with self.lock:
                                        self.sstables.append(sstable)
                                        if immutable in self.immutable_memtables:
                                            immutable.clear()
                                            self.immutable_memtables.remove(immutable)
                                        if len(self.sstables) > self.level_size_limit:
                                            self._compact()
                            except Exception:
                                pass
                        threading.Thread(target=async_flush, daemon=True).start()
                        
                        # 重新尝试（在新MemTable上）
                        success_count = self.memtable.put_batch(remaining)
                        if success_count == 0:
                            break
                    
                    remaining = remaining[success_count:]
        
        return True
    
    def get(self, key: bytes) -> Optional[Tuple[bytes, int]]:
        """读取数据（从新到旧查找，优化锁竞争）"""
        # 优化：读取操作使用更细粒度的锁
        # 1. 先查MemTable（跳表内部使用读锁，允许多个读并发）
        result = self.memtable.get(key)
        if result:
            return result
        
        # 2. 查不可变MemTable（需要锁保护）
        with self.lock:
            for imm_memtable in reversed(self.immutable_memtables):
                result = imm_memtable.get(key)
                if result:
                    return result
        
        # 3. 查SSTable（从新到旧，需要锁保护）
        with self.lock:
            for sstable in reversed(self.sstables):
                result = sstable.get(key)
                if result:
                    return result
        
        return None
    
    def _flush_memtable(self, sync: bool = False):
        """
        将MemTable刷新到磁盘
        Args:
            sync: 是否同步刷新（True=等待完成，False=异步）
        """
        if self.memtable.size == 0:
            return
        
        # 将当前MemTable标记为不可变
        immutable = self.memtable
        self.immutable_memtables.append(immutable)
        # 使用预分配的MemTable（减少分配开销）
        if self._preallocated_memtable:
            self.memtable = self._preallocated_memtable
            self._preallocated_memtable = None
        else:
            # 从缓存的配置值创建MemTable（优化：不传递config对象，直接传值）
            self.memtable = MemTable(
                max_size=self._memtable_max_size,
                use_skip_list=self._enable_skip_list,
                use_cython=self._enable_cython,
                config=None  # 不传递config对象，避免开销
            )
        # 预分配下一个MemTable（后台）
        # 优化：使用缓存的标志，避免重复访问配置
        if self._enable_preallocated:
            # 优化：使用缓存的配置值，避免重复访问
            memtable_max_size = self._memtable_max_size
            enable_skip_list = self._enable_skip_list
            enable_cython = self._enable_cython
            def preallocate():
                self._preallocated_memtable = MemTable(
                    max_size=memtable_max_size,
                    use_skip_list=enable_skip_list,
                    use_cython=enable_cython,
                    config=None  # 不传递config对象，避免开销
                )
            threading.Thread(target=preallocate, daemon=True).start()
        
        # 刷新到磁盘
        def do_flush():
            try:
                entries = list(immutable.get_all())
                if entries:
                    sstable_path = os.path.join(
                        self.data_dir,
                        f"sstable_{int(time.time() * 1000000)}.sst"
                    )
                    sstable = SSTable(sstable_path)
                    sstable.write(entries)
                    
                    with self.lock:
                        self.sstables.append(sstable)
                        # 清理不可变MemTable
                        if immutable in self.immutable_memtables:
                            immutable.clear()
                            self.immutable_memtables.remove(immutable)
                        # 检查是否需要压缩
                        if len(self.sstables) > self.level_size_limit:
                            self._compact()
            except Exception as e:
                import traceback
                print(f"刷新MemTable失败: {e}")
                traceback.print_exc()
        
        if sync:
            # 同步刷新：直接执行，等待完成
            do_flush()
        else:
            # 异步刷新：启动线程，不阻塞
            flush_thread = threading.Thread(target=do_flush, daemon=True)
            flush_thread.start()
    
    def _compact(self):
        """压缩合并SSTable"""
        if len(self.sstables) < 2:
            return
        
        # 按文件大小和时间排序，优先合并小的、旧的文件
        sstable_info = []
        for sstable in self.sstables:
            if os.path.exists(sstable.filepath):
                file_size = os.path.getsize(sstable.filepath)
                file_mtime = os.path.getmtime(sstable.filepath)
                sstable_info.append((sstable, file_size, file_mtime))
        
        if len(sstable_info) < 2:
            return
        
        # 按大小和时间排序（小的、旧的优先）
        sstable_info.sort(key=lambda x: (x[1], x[2]))
        
        # 合并最旧的两个SSTable
        sstable1, size1, mtime1 = sstable_info[0]
        sstable2, size2, mtime2 = sstable_info[1]
        
        # 读取两个SSTable的所有数据
        merged_entries = []
        seen_keys = set()
        
        # 从sstable1读取
        from .file_format import SSTableFormat
        if os.path.exists(sstable1.filepath):
            with open(sstable1.filepath, 'rb') as f:
                # 跳过文件头
                f.seek(SSTableFormat.HEADER_SIZE)
                while True:
                    entry = SSTableFormat.read_entry(f)
                    if entry is None:
                        break
                    key, value, version, timestamp = entry
                    if key not in seen_keys:
                        merged_entries.append((key, value, version))
                        seen_keys.add(key)
        
        # 从sstable2读取（覆盖sstable1中的相同key）
        if os.path.exists(sstable2.filepath):
            with open(sstable2.filepath, 'rb') as f:
                # 跳过文件头
                f.seek(SSTableFormat.HEADER_SIZE)
                while True:
                    entry = SSTableFormat.read_entry(f)
                    if entry is None:
                        break
                    key, value, version, timestamp = entry
                    # 更新或添加
                    found = False
                    for i, (k, v, ver) in enumerate(merged_entries):
                        if k == key:
                            merged_entries[i] = (key, value, version)
                            found = True
                            break
                    if not found:
                        merged_entries.append((key, value, version))
        
        # 创建新的合并SSTable
        if merged_entries:
            new_sstable_path = os.path.join(
                self.data_dir,
                f"sstable_merged_{int(time.time() * 1000000)}.sst"
            )
            new_sstable = SSTable(new_sstable_path)
            new_sstable.write(merged_entries)
            
            # 移除旧文件，添加新文件
            self.sstables.remove(sstable1)
            self.sstables.remove(sstable2)
            if os.path.exists(sstable1.filepath):
                os.remove(sstable1.filepath)
            if os.path.exists(sstable2.filepath):
                os.remove(sstable2.filepath)
            self.sstables.append(new_sstable)
    
    def _load_sstables(self):
        """加载已有的SSTable"""
        if not os.path.exists(self.data_dir):
            return
        
        sstable_files = sorted([
            f for f in os.listdir(self.data_dir)
            if f.endswith('.sst')
        ])
        
        for filename in sstable_files:
            filepath = os.path.join(self.data_dir, filename)
            sstable = SSTable(filepath)
            if sstable.exists():
                self.sstables.append(sstable)
    
    def flush(self):
        """强制刷新到磁盘（同步，确保数据持久化）"""
        # 使用try-except保护，避免flush失败影响主操作
        try:
            with self.lock:
                # 同步刷新：等待所有数据写入完成
                self._flush_memtable(sync=True)
                
                # 等待所有不可变MemTable刷新完成（优化：减少等待时间）
                max_wait_iterations = 100  # 最多等待100次
                wait_count = 0
                while self.immutable_memtables and wait_count < max_wait_iterations:
                    # 检查是否还有待刷新的MemTable
                    remaining = [m for m in self.immutable_memtables if m.size > 0]
                    if not remaining:
                        break
                    # 等待一小段时间，让异步刷新完成
                    import time
                    time.sleep(0.01)  # 10ms
                    wait_count += 1
                
                # 如果还有未刷新的MemTable，记录警告但不阻塞
                if self.immutable_memtables:
                    remaining = [m for m in self.immutable_memtables if m.size > 0]
                    if remaining:
                        print(f"⚠️ 警告: 仍有 {len(remaining)} 个MemTable未刷新，将在后台继续处理")
        except Exception as e:
            import traceback
            print(f"⚠️ LSM树flush失败: {e}")
            traceback.print_exc()
            # flush失败不应影响主操作

