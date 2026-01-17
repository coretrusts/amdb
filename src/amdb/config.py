"""
配置管理模块
支持配置文件（INI格式，类似MySQL的my.cnf、PostgreSQL的postgresql.conf）
支持环境变量、命令行参数
"""

import os
import configparser
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class DatabaseConfig:
    """数据库主配置"""
    # 基础配置
    data_root_dir: str = "./data"  # 数据存储根目录（所有数据库的父目录）
    data_dir: str = "./data/amdb"  # 单个数据库目录（已废弃，保留用于向后兼容）
    enable_sharding: bool = True
    shard_count: int = 256
    max_file_size: int = 256 * 1024 * 1024  # 256MB
    
    # LSM树配置
    lsm_memtable_max_size: int = 10 * 1024 * 1024  # 10MB
    lsm_level_size_limit: int = 10  # 每层最多10个SSTable
    lsm_enable_skip_list: bool = False  # 是否启用SkipList（当前禁用以确保稳定性）
    lsm_enable_cython: bool = False  # 是否启用Cython（当前禁用以确保稳定性）
    
    # SkipList配置
    skip_list_max_level: int = 16  # 最大层级
    skip_list_max_size: int = 10 * 1024 * 1024  # 10MB
    
    # 批量操作配置
    batch_max_size: int = 3000  # 批量操作最大大小（优化：测试显示3000性能最佳）
    version_batch_max_size: int = 3000  # 版本管理批量操作最大大小（优化：测试显示3000性能最佳）
    version_skip_prev_hash_threshold: int = 300  # 跳过prev_hash计算的阈值（优化：提高阈值以提升性能）
    
    # 性能配置
    enable_async_flush: bool = True  # 是否启用异步刷新
    enable_preallocated_memtable: bool = True  # 是否启用预分配MemTable
    flush_interval: float = 1.0  # 刷新间隔（秒）
    checkpoint_interval: float = 60.0  # 检查点间隔（秒）
    
    # 网络配置
    network_host: str = "0.0.0.0"
    network_port: int = 3888  # 使用不常用端口，避免与其他软件冲突
    network_max_connections: int = 100
    network_timeout: float = 30.0
    network_enable_ssl: bool = False
    
    # 缓存配置
    cache_enable: bool = True
    cache_size: int = 100 * 1024 * 1024  # 100MB
    cache_type: str = "lru"  # lru, lfu, fifo
    cache_ttl: Optional[int] = None  # 过期时间（秒）
    
    # 日志配置
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_file: Optional[str] = None
    log_dir: str = "./logs"
    log_max_file_size: int = 10 * 1024 * 1024  # 10MB
    log_backup_count: int = 5
    log_enable_console: bool = True
    log_enable_file: bool = True
    
    # 安全配置
    security_enable_auth: bool = False
    security_auth_method: str = "token"  # token, password, certificate
    security_token_secret: Optional[str] = None
    security_enable_encryption: bool = False
    security_encryption_key: Optional[str] = None
    
    # 审计日志配置
    audit_enable: bool = True
    audit_log_dir: Optional[str] = None  # None表示使用data_dir/audit_logs
    
    # 压缩配置
    compression_enable: bool = True
    compression_type: str = "snappy"  # none, snappy, lz4
    
    # 多线程配置
    threading_enable: bool = True  # 是否启用多线程
    threading_max_workers: int = 4  # 最大工作线程数（用于查询执行器）
    threading_async_flush_workers: int = 2  # 异步刷新线程数
    threading_compaction_workers: int = 2  # 压缩合并线程数
    threading_network_workers: int = 10  # 网络处理线程数（每个连接一个线程）
    threading_enable_parallel_batch: bool = True  # 是否启用并行批量写入
    
    @classmethod
    def from_ini(cls, filepath: str) -> 'DatabaseConfig':
        """从INI文件加载配置"""
        config = configparser.ConfigParser()
        config.read(filepath, encoding='utf-8')
        
        db_config = cls()
        
        # 基础配置
        if config.has_section('database'):
            section = config['database']
            db_config.data_root_dir = section.get('data_root_dir', db_config.data_root_dir)
            db_config.data_dir = section.get('data_dir', db_config.data_dir)
            db_config.enable_sharding = section.getboolean('enable_sharding', db_config.enable_sharding)
            db_config.shard_count = section.getint('shard_count', db_config.shard_count)
            db_config.max_file_size = section.getint('max_file_size', db_config.max_file_size)
        
        # LSM树配置
        if config.has_section('lsm'):
            section = config['lsm']
            db_config.lsm_memtable_max_size = section.getint('memtable_max_size', db_config.lsm_memtable_max_size)
            db_config.lsm_level_size_limit = section.getint('level_size_limit', db_config.lsm_level_size_limit)
            db_config.lsm_enable_skip_list = section.getboolean('enable_skip_list', db_config.lsm_enable_skip_list)
            db_config.lsm_enable_cython = section.getboolean('enable_cython', db_config.lsm_enable_cython)
        
        # SkipList配置
        if config.has_section('skip_list'):
            section = config['skip_list']
            db_config.skip_list_max_level = section.getint('max_level', db_config.skip_list_max_level)
            db_config.skip_list_max_size = section.getint('max_size', db_config.skip_list_max_size)
        
        # 批量操作配置
        if config.has_section('batch'):
            section = config['batch']
            db_config.batch_max_size = section.getint('max_size', db_config.batch_max_size)
            db_config.version_batch_max_size = section.getint('version_max_size', db_config.version_batch_max_size)
            db_config.version_skip_prev_hash_threshold = section.getint('skip_prev_hash_threshold', db_config.version_skip_prev_hash_threshold)
        
        # 性能配置
        if config.has_section('performance'):
            section = config['performance']
            db_config.enable_async_flush = section.getboolean('enable_async_flush', db_config.enable_async_flush)
            db_config.enable_preallocated_memtable = section.getboolean('enable_preallocated_memtable', db_config.enable_preallocated_memtable)
            db_config.flush_interval = section.getfloat('flush_interval', db_config.flush_interval)
            db_config.checkpoint_interval = section.getfloat('checkpoint_interval', db_config.checkpoint_interval)
        
        # 网络配置
        if config.has_section('network'):
            section = config['network']
            db_config.network_host = section.get('host', db_config.network_host)
            db_config.network_port = section.getint('port', db_config.network_port)
            db_config.network_max_connections = section.getint('max_connections', db_config.network_max_connections)
            db_config.network_timeout = section.getfloat('timeout', db_config.network_timeout)
            db_config.network_enable_ssl = section.getboolean('enable_ssl', db_config.network_enable_ssl)
        
        # 缓存配置
        if config.has_section('cache'):
            section = config['cache']
            db_config.cache_enable = section.getboolean('enable', db_config.cache_enable)
            db_config.cache_size = section.getint('size', db_config.cache_size)
            db_config.cache_type = section.get('type', db_config.cache_type)
            if section.get('ttl'):
                db_config.cache_ttl = section.getint('ttl')
        
        # 日志配置
        if config.has_section('log'):
            section = config['log']
            db_config.log_level = section.get('level', db_config.log_level)
            db_config.log_file = section.get('file', db_config.log_file) or None
            db_config.log_dir = section.get('dir', db_config.log_dir)
            db_config.log_max_file_size = section.getint('max_file_size', db_config.log_max_file_size)
            db_config.log_backup_count = section.getint('backup_count', db_config.log_backup_count)
            db_config.log_enable_console = section.getboolean('enable_console', db_config.log_enable_console)
            db_config.log_enable_file = section.getboolean('enable_file', db_config.log_enable_file)
        
        # 安全配置
        if config.has_section('security'):
            section = config['security']
            db_config.security_enable_auth = section.getboolean('enable_auth', db_config.security_enable_auth)
            db_config.security_auth_method = section.get('auth_method', db_config.security_auth_method)
            db_config.security_token_secret = section.get('token_secret', db_config.security_token_secret) or None
            db_config.security_enable_encryption = section.getboolean('enable_encryption', db_config.security_enable_encryption)
            db_config.security_encryption_key = section.get('encryption_key', db_config.security_encryption_key) or None
        
        # 审计日志配置
        if config.has_section('audit'):
            section = config['audit']
            db_config.audit_enable = section.getboolean('enable', db_config.audit_enable)
            db_config.audit_log_dir = section.get('log_dir', db_config.audit_log_dir) or None
        
        # 压缩配置
        if config.has_section('compression'):
            section = config['compression']
            db_config.compression_enable = section.getboolean('enable', db_config.compression_enable)
            db_config.compression_type = section.get('type', db_config.compression_type)
        
        # 多线程配置
        if config.has_section('threading'):
            section = config['threading']
            db_config.threading_enable = section.getboolean('enable', db_config.threading_enable)
            db_config.threading_max_workers = section.getint('max_workers', db_config.threading_max_workers)
            db_config.threading_async_flush_workers = section.getint('async_flush_workers', db_config.threading_async_flush_workers)
            db_config.threading_compaction_workers = section.getint('compaction_workers', db_config.threading_compaction_workers)
            db_config.threading_network_workers = section.getint('network_workers', db_config.threading_network_workers)
            db_config.threading_enable_parallel_batch = section.getboolean('enable_parallel_batch', db_config.threading_enable_parallel_batch)
        
        return db_config
    
    def to_ini(self, filepath: str):
        """保存配置到INI文件"""
        config = configparser.ConfigParser()
        
        # 基础配置
        config.add_section('database')
        config['database']['data_root_dir'] = self.data_root_dir
        config['database']['data_dir'] = self.data_dir
        config['database']['enable_sharding'] = str(self.enable_sharding)
        config['database']['shard_count'] = str(self.shard_count)
        config['database']['max_file_size'] = str(self.max_file_size)
        
        # LSM树配置
        config.add_section('lsm')
        config['lsm']['memtable_max_size'] = str(self.lsm_memtable_max_size)
        config['lsm']['level_size_limit'] = str(self.lsm_level_size_limit)
        config['lsm']['enable_skip_list'] = str(self.lsm_enable_skip_list)
        config['lsm']['enable_cython'] = str(self.lsm_enable_cython)
        
        # SkipList配置
        config.add_section('skip_list')
        config['skip_list']['max_level'] = str(self.skip_list_max_level)
        config['skip_list']['max_size'] = str(self.skip_list_max_size)
        
        # 批量操作配置
        config.add_section('batch')
        config['batch']['max_size'] = str(self.batch_max_size)
        config['batch']['version_max_size'] = str(self.version_batch_max_size)
        config['batch']['skip_prev_hash_threshold'] = str(self.version_skip_prev_hash_threshold)
        
        # 性能配置
        config.add_section('performance')
        config['performance']['enable_async_flush'] = str(self.enable_async_flush)
        config['performance']['enable_preallocated_memtable'] = str(self.enable_preallocated_memtable)
        config['performance']['flush_interval'] = str(self.flush_interval)
        config['performance']['checkpoint_interval'] = str(self.checkpoint_interval)
        
        # 网络配置
        config.add_section('network')
        config['network']['host'] = self.network_host
        config['network']['port'] = str(self.network_port)
        config['network']['max_connections'] = str(self.network_max_connections)
        config['network']['timeout'] = str(self.network_timeout)
        config['network']['enable_ssl'] = str(self.network_enable_ssl)
        
        # 缓存配置
        config.add_section('cache')
        config['cache']['enable'] = str(self.cache_enable)
        config['cache']['size'] = str(self.cache_size)
        config['cache']['type'] = self.cache_type
        if self.cache_ttl:
            config['cache']['ttl'] = str(self.cache_ttl)
        
        # 日志配置
        config.add_section('log')
        config['log']['level'] = self.log_level
        if self.log_file:
            config['log']['file'] = self.log_file
        config['log']['dir'] = self.log_dir
        config['log']['max_file_size'] = str(self.log_max_file_size)
        config['log']['backup_count'] = str(self.log_backup_count)
        config['log']['enable_console'] = str(self.log_enable_console)
        config['log']['enable_file'] = str(self.log_enable_file)
        
        # 安全配置
        config.add_section('security')
        config['security']['enable_auth'] = str(self.security_enable_auth)
        config['security']['auth_method'] = self.security_auth_method
        if self.security_token_secret:
            config['security']['token_secret'] = self.security_token_secret
        config['security']['enable_encryption'] = str(self.security_enable_encryption)
        if self.security_encryption_key:
            config['security']['encryption_key'] = self.security_encryption_key
        
        # 审计日志配置
        config.add_section('audit')
        config['audit']['enable'] = str(self.audit_enable)
        if self.audit_log_dir:
            config['audit']['log_dir'] = self.audit_log_dir
        
        # 压缩配置
        config.add_section('compression')
        config['compression']['enable'] = str(self.compression_enable)
        config['compression']['type'] = self.compression_type
        
        # 多线程配置
        config.add_section('threading')
        config['threading']['enable'] = str(self.threading_enable)
        config['threading']['max_workers'] = str(self.threading_max_workers)
        config['threading']['async_flush_workers'] = str(self.threading_async_flush_workers)
        config['threading']['compaction_workers'] = str(self.threading_compaction_workers)
        config['threading']['network_workers'] = str(self.threading_network_workers)
        config['threading']['enable_parallel_batch'] = str(self.threading_enable_parallel_batch)
        
        # 写入文件
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            config.write(f)
    
    def load_from_env(self):
        """从环境变量加载配置"""
        # 基础配置
        if os.getenv('AMDB_DATA_ROOT_DIR'):
            self.data_root_dir = os.getenv('AMDB_DATA_ROOT_DIR')
        if os.getenv('AMDB_DATA_DIR'):
            self.data_dir = os.getenv('AMDB_DATA_DIR')
        if os.getenv('AMDB_ENABLE_SHARDING'):
            self.enable_sharding = os.getenv('AMDB_ENABLE_SHARDING').lower() == 'true'
        if os.getenv('AMDB_SHARD_COUNT'):
            self.shard_count = int(os.getenv('AMDB_SHARD_COUNT'))
        if os.getenv('AMDB_MAX_FILE_SIZE'):
            self.max_file_size = int(os.getenv('AMDB_MAX_FILE_SIZE'))
        
        # LSM树配置
        if os.getenv('AMDB_LSM_MEMTABLE_MAX_SIZE'):
            self.lsm_memtable_max_size = int(os.getenv('AMDB_LSM_MEMTABLE_MAX_SIZE'))
        if os.getenv('AMDB_LSM_ENABLE_SKIP_LIST'):
            self.lsm_enable_skip_list = os.getenv('AMDB_LSM_ENABLE_SKIP_LIST').lower() == 'true'
        
        # 批量操作配置
        if os.getenv('AMDB_BATCH_MAX_SIZE'):
            self.batch_max_size = int(os.getenv('AMDB_BATCH_MAX_SIZE'))
        
        # 日志配置
        if os.getenv('AMDB_LOG_LEVEL'):
            self.log_level = os.getenv('AMDB_LOG_LEVEL')
        if os.getenv('AMDB_LOG_FILE'):
            self.log_file = os.getenv('AMDB_LOG_FILE')
        
        # 安全配置
        if os.getenv('AMDB_SECURITY_TOKEN_SECRET'):
            self.security_token_secret = os.getenv('AMDB_SECURITY_TOKEN_SECRET')
        if os.getenv('AMDB_SECURITY_ENABLE_AUTH'):
            self.security_enable_auth = os.getenv('AMDB_SECURITY_ENABLE_AUTH').lower() == 'true'


def load_config(config_path: Optional[str] = None) -> DatabaseConfig:
    """加载配置（优先级：配置文件 > 环境变量 > 默认值）"""
    global _global_config, _global_config_path
    
    # 优化：如果已经加载过相同路径的配置，直接返回缓存的配置
    if _global_config is not None:
        if config_path is None and _global_config_path is None:
            return _global_config
        if config_path == _global_config_path:
            return _global_config
    
    config = DatabaseConfig()
    
    # 1. 从环境变量加载
    config.load_from_env()
    
    # 2. 从配置文件加载（如果提供）
    actual_config_path = None
    if config_path:
        if os.path.exists(config_path):
            if config_path.endswith('.ini'):
                config = DatabaseConfig.from_ini(config_path)
                actual_config_path = config_path
            else:
                raise ValueError(f"Unsupported config file format: {config_path}")
        else:
            raise FileNotFoundError(f"Config file not found: {config_path}")
    else:
        # 尝试从默认位置加载
        default_paths = [
            "./amdb.ini",
            os.path.expanduser("~/.amdb/amdb.ini"),
            "/etc/amdb/amdb.ini"
        ]
        for path in default_paths:
            if os.path.exists(path):
                config = DatabaseConfig.from_ini(path)
                actual_config_path = path
                break
    
    # 缓存配置
    _global_config = config
    _global_config_path = actual_config_path
    
    return config


# 全局配置实例（优化：缓存配置，避免重复加载）
_global_config: Optional[DatabaseConfig] = None
_global_config_path: Optional[str] = None


def get_config() -> DatabaseConfig:
    """获取全局配置实例"""
    global _global_config
    if _global_config is None:
        _global_config = load_config()
    return _global_config


def set_config(config: DatabaseConfig):
    """设置全局配置实例"""
    global _global_config
    _global_config = config
