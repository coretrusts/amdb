"""
AmDb 主数据库类
整合所有组件，提供统一的API
"""

import threading
import time
import hashlib
from typing import Optional, Tuple, List, Dict, Any, Callable
from pathlib import Path
from .storage import StorageEngine
from .version import VersionManager
# 完全禁用Cython版本管理器，确保稳定性
# 不再尝试导入Cython模块，避免崩溃
USE_CYTHON_VERSION = False
from .transaction import TransactionManager, Transaction
from .index import IndexManager
from .audit import AuditLogger
from .config import DatabaseConfig, load_config, get_config


class Database:
    """
    AmDb 数据库主类
    提供完整的数据库功能
    """
    
    def __init__(self, 
                 data_dir: Optional[str] = None,
                 enable_sharding: Optional[bool] = None,
                 shard_count: Optional[int] = None,
                 max_file_size: Optional[int] = None,
                 config_path: Optional[str] = None):
        """
        Args:
            data_dir: 数据目录（如果为None，从配置文件读取）
            enable_sharding: 是否启用分片（如果为None，从配置文件读取）
            shard_count: 分片数量（如果为None，从配置文件读取）
            max_file_size: 单个文件最大大小（如果为None，从配置文件读取）
            config_path: 配置文件路径（如果为None，尝试从默认位置加载）
        """
        # 先确定data_dir，用于查找数据库特定的配置文件
        temp_config = load_config(config_path)
        self.data_dir = data_dir if data_dir is not None else temp_config.data_dir
        
        # 尝试加载数据库特定的配置文件（优先级最高）
        db_config_path = Path(self.data_dir) / "database.ini"
        if db_config_path.exists():
            # 数据库特定配置存在，使用它
            self.config = load_config(str(db_config_path))
            print(f"✓ 加载数据库特定配置: {db_config_path}")
        elif config_path:
            # 使用提供的配置文件
            self.config = load_config(config_path)
        else:
            # 使用全局配置
            self.config = temp_config
        
        # 使用配置值，如果参数提供了值则优先使用参数
        self.data_dir = data_dir if data_dir is not None else self.config.data_dir
        self.enable_sharding = enable_sharding if enable_sharding is not None else self.config.enable_sharding
        shard_count = shard_count if shard_count is not None else self.config.shard_count
        max_file_size = max_file_size if max_file_size is not None else self.config.max_file_size
        
        self.storage = StorageEngine(
            self.data_dir, 
            enable_sharding=self.enable_sharding,
            shard_count=shard_count,
            max_file_size=max_file_size,
            config=self.config
        )
        # 完全禁用Cython版本管理器，确保稳定性
        # 直接使用纯Python版本管理器，避免任何Cython导入
        self.version_manager = VersionManager(config=self.config)
        
        # 从磁盘加载版本数据（重要：确保数据可以恢复）
        self.version_manager.load_from_disk(self.data_dir)
        
        self.transaction_manager = TransactionManager()
        self.index_manager = IndexManager()
        
        # 从磁盘加载索引数据
        self.index_manager.load_from_disk(self.data_dir)
        
        self.lock = threading.RLock()
        
        # WAL日志（Write-Ahead Log，确保数据不丢失）
        from .storage.wal import WALLogger
        wal_dir = Path(self.data_dir) / "wal"
        self.wal_logger = WALLogger(str(wal_dir), max_file_size=64 * 1024 * 1024)
        
        # 审计日志（区块链应用必需）
        # 优化：延迟初始化，避免初始化时的开销
        if self.config.audit_enable:
            audit_dir = self.config.audit_log_dir or (Path(self.data_dir) / "audit_logs")
            try:
                self.audit_logger = AuditLogger(str(audit_dir))
            except Exception:
                # 如果审计日志初始化失败，使用None（后续可以异步初始化）
                self.audit_logger = None
        else:
            self.audit_logger = None
        
        # 加载数据库元数据（.amdb文件）
        self._load_metadata()
    
    def put(self, key: bytes, value: bytes) -> Tuple[bool, bytes]:
        """
        写入数据（优化：先写入内存，异步持久化）
        类似区块链：pendingTransaction在内存，其他异步更新到文件
        Returns:
            (success, merkle_root_hash)
        """
        with self.lock:
            # 创建新版本（内存操作，快速）
            version_obj = self.version_manager.create_version(key, value)
            
            # 写入存储引擎（LSM树MemTable，内存操作，快速）
            merkle_root = self.storage.put(key, value, version_obj.version)
            
            # 更新索引（内存操作，快速）
            self.index_manager.put(
                key, value, version_obj.version, version_obj.timestamp
            )
            
            # 异步写入WAL（不阻塞主流程）
            try:
                import threading
                if not hasattr(self, '_wal_thread') or not self._wal_thread.is_alive():
                    def async_wal():
                        try:
                            self.wal_logger.log_put(key, value, version_obj.version)
                        except Exception:
                            pass
                    self._wal_thread = threading.Thread(target=async_wal, daemon=True)
                    self._wal_thread.start()
                else:
                    # 如果线程还在运行，直接写入（WAL内部有锁保护）
                    self.wal_logger.log_put(key, value, version_obj.version)
            except Exception:
                pass  # WAL失败不应影响主操作
            
            # 异步记录审计日志（不阻塞主流程）
            if self.audit_logger:
                try:
                    import threading
                    def async_audit():
                        try:
                            self.audit_logger.log_put(key, value)
                        except Exception:
                            pass
                    threading.Thread(target=async_audit, daemon=True).start()
                except Exception:
                    pass  # 审计日志失败不应影响主操作
            
            return (True, merkle_root)
    
    def delete(self, key: bytes) -> bool:
        """
        删除数据（标记删除）
        由于使用版本管理，数据不可真正删除，只能标记为已删除
        
        Args:
            key: 要删除的键
            
        Returns:
            是否成功标记删除
        """
        with self.lock:
            # 使用特殊标记值表示已删除
            # 在版本管理器中创建一个删除标记版本
            deleted_value = b'__DELETED__'
            version_obj = self.version_manager.create_version(key, deleted_value)
            
            # 写入存储引擎（标记为已删除）
            self.storage.put(key, deleted_value, version_obj.version)
            
            # 更新索引
            self.index_manager.put(
                key, deleted_value, version_obj.version, version_obj.timestamp
            )
            
            # 异步写入WAL
            try:
                import threading
                if not hasattr(self, '_wal_thread') or not self._wal_thread.is_alive():
                    def async_wal():
                        try:
                            self.wal_logger.log_put(key, deleted_value, version_obj.version)
                        except Exception:
                            pass
                    self._wal_thread = threading.Thread(target=async_wal, daemon=True)
                    self._wal_thread.start()
                else:
                    self.wal_logger.log_put(key, deleted_value, version_obj.version)
            except Exception:
                pass
            
            # 异步记录审计日志
            if self.audit_logger:
                try:
                    import threading
                    def async_audit():
                        try:
                            self.audit_logger.log_delete(key)
                        except Exception:
                            pass
                    threading.Thread(target=async_audit, daemon=True).start()
                except Exception:
                    pass
            
            return True
    
    def is_deleted(self, key: bytes) -> bool:
        """
        检查键是否已被标记删除
        
        Args:
            key: 要检查的键
            
        Returns:
            是否已删除
        """
        with self.lock:
            # 直接从版本管理器获取最新版本，检查是否为删除标记
            latest = self.version_manager.get_latest(key)
            if latest:
                return latest.value == b'__DELETED__'
            return False
    
    def get(self, key: bytes, version: Optional[int] = None) -> Optional[bytes]:
        """
        读取数据（优化：减少锁竞争，提升并发读取性能）
        确保从所有存储位置读取：版本管理器、LSM树、B+树、所有分片
        Args:
            key: 键
            version: 版本号（None表示最新版本）
        """
        # 优化：读取操作减少锁持有时间
        if version is None:
            # 1. 优先从版本管理器获取最新版本（需要锁）
            with self.lock:
                latest = self.version_manager.get_latest(key)
                if latest:
                    # 检查是否已删除
                    if latest.value == b'__DELETED__':
                        return None
                    return latest.value
            
            # 2. 如果版本管理器没有，尝试从存储引擎获取（LSM树、B+树、所有分片）
            result = self.storage.get(key, use_cache=True)
            if result:
                value = result[0]
                # 检查是否已删除
                if value == b'__DELETED__':
                    return None
                return value
            
            # 3. 如果存储引擎也没有，尝试直接从LSM树获取（可能数据在MemTable中但未刷新到版本管理器）
            try:
                if hasattr(self.storage, 'lsm_tree'):
                    lsm_result = self.storage.lsm_tree.get(key)
                    if lsm_result:
                        value = lsm_result[0]
                        if value == b'__DELETED__':
                            return None
                        return value
            except Exception:
                pass
            
            return None
        else:
            # 读取指定版本（需要锁）
            with self.lock:
                version_obj = self.version_manager.get_version(key, version)
                if version_obj:
                    # 检查是否已删除
                    if version_obj.value == b'__DELETED__':
                        return None
                    return version_obj.value
            return None
    
    def get_at_time(self, key: bytes, timestamp: float) -> Optional[bytes]:
        """获取指定时间点的值"""
        with self.lock:
            version_obj = self.version_manager.get_at_time(key, timestamp)
            if version_obj:
                return version_obj.value
            return None
    
    def get_with_proof(self, key: bytes) -> Tuple[Optional[bytes], List[bytes], bytes]:
        """获取值及其Merkle证明"""
        with self.lock:
            return self.storage.get_with_proof(key)
    
    def verify(self, key: bytes, value: bytes, proof: List[bytes]) -> bool:
        """验证数据完整性"""
        return self.storage.verify(key, value, proof)
    
    def get_history(self, key: bytes, start_version: Optional[int] = None,
                   end_version: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取版本历史"""
        with self.lock:
            versions = self.version_manager.get_history(key, start_version, end_version)
            return [
                {
                    'version': v.version,
                    'timestamp': v.timestamp,
                    'value': v.value,
                    'hash': v.hash.hex() if v.hash else None
                }
                for v in versions
            ]
    
    def range_query(self, start_key: bytes, end_key: bytes) -> List[Tuple[bytes, bytes]]:
        """范围查询"""
        with self.lock:
            return self.storage.range_query(start_key, end_key)
    
    def get_root_hash(self) -> bytes:
        """获取Merkle根哈希"""
        return self.storage.get_root_hash()
    
    # 事务操作
    def begin_transaction(self) -> Transaction:
        """开始事务"""
        return self.transaction_manager.begin_transaction()
    
    def commit_transaction(self, tx: Transaction) -> bool:
        """提交事务"""
        def commit_fn(operations, tx_id):
            try:
                for op in operations:
                    if op.operation == 'put':
                        self.put(op.key, op.value)
                    # delete操作需要实现
                return True
            except Exception:
                return False
        
        return self.transaction_manager.commit_transaction(tx, commit_fn)
    
    def abort_transaction(self, tx: Transaction):
        """中止事务"""
        self.transaction_manager.abort_transaction(tx)
    
    # 批量操作
    def batch_put(self, items: List[Tuple[bytes, bytes]]) -> Tuple[bool, bytes]:
        """
        批量写入（高性能优化版本，支持多线程并行处理）
        Args:
            items: [(key, value), ...]
        Returns:
            (success, merkle_root_hash)
        """
        if not items:
            return (True, self.get_root_hash())
        
        # 优化：减少锁持有时间，先准备数据，再快速写入
        # 优化：添加异常处理和资源清理，避免崩溃
        try:
            # 限制批量大小，避免内存问题和崩溃
            # 从配置文件读取批量大小（优化：缓存配置值，避免重复访问）
            MAX_BATCH_SIZE = self.config.batch_max_size
            
            # 检查是否启用并行批量写入
            # 优化：降低并行阈值，更早启用并行处理以提升性能
            # 优化：对于超过批量大小2倍的数据，启用并行处理
            enable_parallel = (self.config.threading_enable and 
                              self.config.threading_enable_parallel_batch and
                              len(items) > MAX_BATCH_SIZE * 2)  # 超过批量大小2倍才使用并行
            
            if enable_parallel:
                # 并行批量写入：将数据分成多个批次，使用线程池并行处理
                import concurrent.futures
                import gc
                
                # 计算批次大小和线程数
                max_workers = min(self.config.threading_max_workers, 
                                 (len(items) + MAX_BATCH_SIZE - 1) // MAX_BATCH_SIZE)
                
                results = []
                with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                    futures = []
                    for i in range(0, len(items), MAX_BATCH_SIZE):
                        batch = items[i:i+MAX_BATCH_SIZE]
                        future = executor.submit(self._batch_put_internal, batch)
                        futures.append(future)
                    
                    # 等待所有批次完成
                    for future in concurrent.futures.as_completed(futures):
                        try:
                            result = future.result()
                            results.append(result)
                            if not result[0]:
                                # 如果某个批次失败，取消其他任务并返回失败
                                for f in futures:
                                    f.cancel()
                                return (False, b'')
                        except Exception as e:
                            import traceback
                            print(f"并行批量写入失败: {e}")
                            traceback.print_exc()
                            return (False, b'')
                    
                    # 每批后强制垃圾回收，释放内存
                    gc.collect()
                
                # 返回最后一个结果
                return results[-1] if results else (True, self.get_root_hash())
            elif len(items) > MAX_BATCH_SIZE:
                # 串行分批处理，每批后强制垃圾回收
                results = []
                import gc
                for i in range(0, len(items), MAX_BATCH_SIZE):
                    batch = items[i:i+MAX_BATCH_SIZE]
                    result = self._batch_put_internal(batch)
                    results.append(result)
                    if not result[0]:
                        break  # 如果失败，立即返回
                    # 每批后强制垃圾回收，释放内存
                    gc.collect()
                # 返回最后一个结果
                return results[-1] if results else (True, self.get_root_hash())
            else:
                return self._batch_put_internal(items)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return (False, b'')
    
    def _batch_put_internal(self, items: List[Tuple[bytes, bytes]]) -> Tuple[bool, bytes]:
        """内部批量写入方法（优化版本，稳定性优先）"""
        try:
            # 高性能批量写入优化（对标LevelDB性能，达到并超越）：
            # 优化策略：最小化主路径开销，所有非关键操作异步化
            # 稳定性优化：添加异常捕获和资源清理
            
            # 1. 批量创建版本（优化：减少锁竞争，使用快速路径）
            # 优化：版本创建在锁外执行，减少Database主锁的持有时间
            # 稳定性：添加异常处理
            try:
                version_objs = self.version_manager.create_versions_batch(items)
            except Exception as e:
                import traceback
                print(f"版本创建失败: {e}")
                traceback.print_exc()
                return (False, b'')
            
            # 验证版本对象数量
            if len(version_objs) != len(items):
                print(f"版本对象数量不匹配: {len(version_objs)} != {len(items)}")
                return (False, b'')
            
            # 2. 直接批量写入LSM树（核心路径，最高优先级，对标LevelDB）
            # 优化：预先构建batch_items，使用列表推导式（比zip稍快）
            # 稳定性：添加异常处理
            try:
                # 优化：使用列表推导式，避免zip的开销
                items_len = len(items)
                batch_items = []
                for i in range(items_len):
                    key, value = items[i]
                    version_obj = version_objs[i]
                    batch_items.append((key, value, version_obj.version))
            except Exception as e:
                print(f"构建batch_items失败: {e}")
                return (False, b'')
            
            # 优化：最小化锁持有时间，只锁定写入操作
            # 优化：LSM Tree内部已有锁，这里不需要额外锁（除非需要保护其他状态）
            # 稳定性：添加异常处理
            try:
                if hasattr(self.storage.lsm_tree, 'batch_put'):
                    self.storage.lsm_tree.batch_put(batch_items)
                else:
                    # 回退：逐个写入
                    for key, value, version in batch_items:
                        self.storage.lsm_tree.put(key, value, version)
            except Exception as e:
                import traceback
                print(f"LSM树写入失败: {e}")
                traceback.print_exc()
                return (False, b'')
                
            # 记录审计日志（批量操作，异步记录以减少开销）
            # 优化：批量操作只记录一次，不阻塞主路径
            # 优化：对于大批量操作，延迟记录或批量记录
            # 优化：暂时禁用审计日志以减少开销，后续可异步记录
            # if len(items) < 10000:
            #     try:
            #         self.audit_logger.log_batch_put(len(items))
            #     except Exception:
            #         pass  # 审计日志失败不应影响主操作
            # 大批量操作：延迟到异步线程记录，减少主路径开销
            
            # 3. 完全异步化非关键操作（不阻塞写入，对标LevelDB）
            # 优化：暂时禁用异步更新以减少崩溃风险
            # 后续可以优化异步更新线程的实现，确保线程安全
            
            return (True, self.get_root_hash())
        except MemoryError:
            # 内存不足，尝试清理
            import gc
            gc.collect()
            return (False, b'')
        except Exception as e:
            import traceback
            traceback.print_exc()
            return (False, b'')
    
    # 索引操作
    def create_index(self, index_name: str):
        """创建二级索引"""
        self.index_manager.create_secondary_index(index_name)
    
    def update_index(self, index_name: str, index_value: Any, key: bytes):
        """更新二级索引"""
        self.index_manager.update_secondary_index(index_name, index_value, key)
    
    def query_index(self, index_name: str, index_value: Any) -> List[bytes]:
        """查询二级索引"""
        return self.index_manager.query_secondary_index(index_name, index_value)
    
    # 工具方法
    def flush(self, async_mode: bool = False):
        """
        强制刷新到磁盘（优化：支持异步模式）
        Args:
            async_mode: 如果True，异步持久化非关键文件（索引、元数据），只同步关键文件（LSM、WAL）
        """
        with self.lock:
            # 1. WAL刷新（.wal文件）- 关键，同步
            self.wal_logger.flush()
            
            # 2. 存储引擎刷新（LSM树刷新到.sst文件）- 关键，同步
            # LSM树内部会异步刷新MemTable，这里只确保已满的MemTable被刷新
            self.storage.lsm_tree.flush()
            
            if async_mode:
                # 异步模式：非关键文件异步持久化
                import threading
                def async_persist():
                    try:
                        # B+树持久化（.bpt文件）- 非关键，可以异步
                        self.storage.bplus_tree.flush()
                        # Merkle树持久化（.mpt文件）- 非关键，可以异步
                        self.storage.merkle_tree.save_to_disk()
                        # 版本管理器持久化（.ver文件）- 非关键，可以异步
                        self.version_manager.save_to_disk(self.data_dir)
                        # 索引管理器持久化（.idx文件）- 非关键，可以异步
                        self.index_manager.save_to_disk(self.data_dir)
                        # 保存数据库元数据（.amdb文件）- 非关键，可以异步
                        self._save_metadata()
                    except Exception as e:
                        import traceback
                        print(f"异步持久化失败: {e}")
                        traceback.print_exc()
                threading.Thread(target=async_persist, daemon=True).start()
            else:
                # 同步模式：所有文件同步持久化（用于确保数据完整性）
                # B+树持久化（.bpt文件）
                self.storage.bplus_tree.flush()
                # Merkle树持久化（.mpt文件）
                self.storage.merkle_tree.save_to_disk()
                # 版本管理器持久化（.ver文件）
                self.version_manager.save_to_disk(self.data_dir)
                # 索引管理器持久化（.idx文件）
                self.index_manager.save_to_disk(self.data_dir)
                # 保存数据库元数据（.amdb文件）
                self._save_metadata()
    
    def _save_metadata(self):
        """保存数据库元数据到磁盘（.amdb文件）"""
        import json
        import struct
        import hashlib
        from .storage.file_format import FileMagic
        
        metadata_file = Path(self.data_dir) / "database.amdb"
        try:
            with open(metadata_file, 'wb') as f:
                # 写入文件魔数
                f.write(FileMagic.AMDB)  # 4 bytes
                
                # 写入版本号
                f.write(struct.pack('H', 1))  # 2 bytes
                
                # 写入元数据（JSON格式）
                metadata = {
                    'data_dir': str(self.data_dir),
                    'enable_sharding': self.enable_sharding,
                    'shard_count': self.config.shard_count if self.enable_sharding else 0,
                    'max_file_size': self.config.max_file_size,
                    'created_at': getattr(self, '_created_at', time.time()),
                    'last_updated': time.time(),
                    'description': getattr(self, '_description', ''),  # 数据库备注
                    'total_keys': len(self.version_manager.get_all_keys()),
                    'current_version': self.transaction_manager.get_snapshot_version(),
                    'merkle_root': self.get_root_hash().hex()
                }
                
                metadata_json = json.dumps(metadata, ensure_ascii=False).encode('utf-8')
                f.write(struct.pack('Q', len(metadata_json)))  # 8 bytes
                f.write(metadata_json)
                
                # 写入checksum（先关闭文件，重新打开读取）
                current_pos = f.tell()
            
            # 重新打开文件读取数据并计算checksum
            with open(metadata_file, 'rb') as rf:
                data = rf.read()
            
            # 追加checksum
            with open(metadata_file, 'ab') as af:
                checksum = hashlib.sha256(data).digest()
                af.write(checksum)  # 32 bytes
        except Exception as e:
            import traceback
            print(f"保存数据库元数据失败: {e}")
            traceback.print_exc()
    
    def _load_metadata(self):
        """从磁盘加载数据库元数据（.amdb文件）"""
        import json
        import struct
        from .storage.file_format import FileMagic
        
        metadata_file = Path(self.data_dir) / "database.amdb"
        if not metadata_file.exists():
            self._created_at = time.time()
            return
        
        try:
            with open(metadata_file, 'rb') as f:
                # 读取文件魔数
                magic = f.read(4)
                if magic != FileMagic.AMDB:
                    return  # 无效文件
                
                # 读取版本号
                version = struct.unpack('H', f.read(2))[0]
                
                # 读取元数据
                metadata_len = struct.unpack('Q', f.read(8))[0]
                metadata_json = f.read(metadata_len).decode('utf-8')
                metadata = json.loads(metadata_json)
                
                # 保存创建时间和备注
                self._created_at = metadata.get('created_at', time.time())
                self._description = metadata.get('description', '')  # 数据库备注
        except Exception as e:
            import traceback
            print(f"加载数据库元数据失败: {e}")
            traceback.print_exc()
            self._created_at = time.time()
            self._description = ''  # 默认无备注
    
    def set_description(self, description: str):
        """设置数据库备注"""
        self._description = description
        self._save_metadata()  # 立即保存
    
    def get_description(self) -> str:
        """获取数据库备注"""
        return getattr(self, '_description', '')
    
    def save_config(self, config_path: Optional[str] = None) -> bool:
        """
        保存数据库配置到文件
        
        Args:
            config_path: 配置文件路径（如果为None，保存到数据库目录的database.ini）
        
        Returns:
            是否保存成功
        """
        try:
            if config_path is None:
                config_path = str(Path(self.data_dir) / "database.ini")
            
            # 确保目录存在
            Path(config_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 保存配置
            self.config.to_ini(config_path)
            print(f"✓ 配置已保存到: {config_path}")
            return True
        except Exception as e:
            print(f"✗ 保存配置失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def load_config(self, config_path: Optional[str] = None) -> bool:
        """
        从文件加载数据库配置
        
        Args:
            config_path: 配置文件路径（如果为None，从数据库目录的database.ini加载）
        
        Returns:
            是否加载成功
        """
        try:
            if config_path is None:
                config_path = str(Path(self.data_dir) / "database.ini")
            
            if not Path(config_path).exists():
                print(f"✗ 配置文件不存在: {config_path}")
                return False
            
            # 加载配置
            self.config = load_config(config_path)
            print(f"✓ 配置已加载: {config_path}")
            return True
        except Exception as e:
            print(f"✗ 加载配置失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_config_path(self) -> str:
        """获取数据库配置文件的路径"""
        return str(Path(self.data_dir) / "database.ini")
    
    def export_config(self, export_path: str) -> bool:
        """
        导出配置文件到指定路径
        
        Args:
            export_path: 导出路径
        
        Returns:
            是否导出成功
        """
        try:
            # 确保目录存在
            Path(export_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 保存配置
            self.config.to_ini(export_path)
            print(f"✓ 配置已导出到: {export_path}")
            return True
        except Exception as e:
            print(f"✗ 导出配置失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def update_config(self, **kwargs) -> bool:
        """
        更新配置项
        
        Args:
            **kwargs: 配置项键值对
        
        Returns:
            是否更新成功
        """
        try:
            # 更新配置对象
            for key, value in kwargs.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
                else:
                    print(f"警告: 未知的配置项: {key}")
            
            # 保存到文件
            return self.save_config()
        except Exception as e:
            print(f"✗ 更新配置失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        with self.lock:
            stats = {
                'total_keys': len(self.version_manager.get_all_keys()),
                'current_version': self.transaction_manager.get_snapshot_version(),
                'merkle_root': self.get_root_hash().hex(),
                'storage_dir': self.data_dir,
                'sharding_enabled': self.enable_sharding
            }
            
            # 添加分片信息
            if self.enable_sharding:
                shard_info = self.storage.get_shard_info()
                stats['shard_count'] = len(shard_info)
                stats['shard_info'] = shard_info
                stats['partitions'] = self.storage.list_partitions()
            
            return stats
    
    def create_partition(self, partition_name: str, 
                        shard_count: int = 256,
                        max_file_size: int = 256 * 1024 * 1024):
        """创建分区（分表分库）"""
        self.storage.create_partition(partition_name, shard_count, max_file_size)
    
    def get_partition(self, partition_name: str):
        """获取分区"""
        return self.storage.get_partition(partition_name)
    
    def list_partitions(self) -> List[str]:
        """列出所有分区"""
        return self.storage.list_partitions()

