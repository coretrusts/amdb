# -*- coding: utf-8 -*-
"""
数据库扫描器
自动扫描data目录下的所有数据库，并读取元数据（包括备注）
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
import json
import struct


def scan_databases(data_dir: str = './data') -> List[Dict[str, any]]:
    """
    扫描数据目录下的所有数据库
    
    Args:
        data_dir: 数据目录路径
        
    Returns:
        数据库列表，每个数据库包含：
        - name: 数据库名称（目录名）
        - path: 数据库路径
        - description: 数据库备注
        - total_keys: 总键数（如果可读取）
        - created_at: 创建时间
        - exists: 是否存在
    """
    databases = []
    
    if not os.path.exists(data_dir):
        return databases
    
    # 扫描所有子目录
    for item in os.listdir(data_dir):
        item_path = os.path.join(data_dir, item)
        if os.path.isdir(item_path):
            # 检查是否是数据库目录
            # 标准标识：database.amdb文件或versions目录
            amdb_file = Path(item_path) / "database.amdb"
            versions_dir = Path(item_path) / "versions"
            
            # 扩展标识：如果有多个数据库相关目录，也认为是数据库
            # 这适用于没有database.amdb文件但有多数据库结构的旧格式
            lsm_dir = Path(item_path) / "lsm"
            bplus_dir = Path(item_path) / "bplus"
            merkle_dir = Path(item_path) / "merkle"
            wal_dir = Path(item_path) / "wal"
            
            # 检查是否有数据库相关结构
            has_db_structure = (
                amdb_file.exists() or 
                versions_dir.exists() or
                (lsm_dir.exists() and (bplus_dir.exists() or merkle_dir.exists() or wal_dir.exists()))
            )
            
            if has_db_structure:
                db_info = {
                    'name': item,
                    'path': item_path,
                    'description': '',
                    'total_keys': 0,
                    'created_at': None,
                    'exists': True
                }
                
                # 尝试读取元数据
                if amdb_file.exists():
                    try:
                        metadata = _load_database_metadata(amdb_file)
                        if metadata:
                            db_info['description'] = metadata.get('description', '')
                            db_info['created_at'] = metadata.get('created_at')
                            db_info['total_keys'] = metadata.get('total_keys', 0)
                    except Exception as e:
                        # 如果读取失败，继续使用默认值
                        pass
                
                # 如果没有备注，尝试从版本管理器获取键数量
                # 即使没有versions目录，也尝试加载数据库获取键数量（适用于旧格式数据库）
                if db_info['total_keys'] == 0:
                    try:
                        from .database import Database
                        db = Database(data_dir=item_path)
                        # 先尝试从版本管理器获取
                        try:
                            db_info['total_keys'] = len(db.version_manager.get_all_keys())
                        except:
                            # 如果版本管理器获取失败，尝试使用get_stats获取
                            stats = db.get_stats()
                            db_info['total_keys'] = stats.get('total_keys', 0)
                    except Exception:
                        # 如果加载数据库失败，跳过
                        pass
                
                databases.append(db_info)
    
    # 按名称排序
    databases.sort(key=lambda x: x['name'])
    
    return databases


def _load_database_metadata(metadata_file: Path) -> Optional[Dict]:
    """加载数据库元数据（不创建完整的Database对象）"""
    try:
        from .storage.file_format import FileMagic
        
        with open(metadata_file, 'rb') as f:
            # 读取文件魔数
            magic = f.read(4)
            if magic != FileMagic.AMDB:
                return None  # 无效文件
            
            # 读取版本号
            version = struct.unpack('H', f.read(2))[0]
            
            # 读取元数据
            metadata_len = struct.unpack('Q', f.read(8))[0]
            metadata_json = f.read(metadata_len).decode('utf-8')
            metadata = json.loads(metadata_json)
            
            return metadata
    except Exception:
        return None


def get_database_info(db_path: str) -> Dict[str, any]:
    """
    获取单个数据库的详细信息
    
    Args:
        db_path: 数据库路径
        
    Returns:
        数据库信息字典
    """
    db_path = Path(db_path)
    amdb_file = db_path / "database.amdb"
    
    info = {
        'name': db_path.name,
        'path': str(db_path),
        'description': '',
        'total_keys': 0,
        'created_at': None,
        'exists': db_path.exists()
    }
    
    if amdb_file.exists():
        metadata = _load_database_metadata(amdb_file)
        if metadata:
            info['description'] = metadata.get('description', '')
            info['created_at'] = metadata.get('created_at')
            info['total_keys'] = metadata.get('total_keys', 0)
    
    return info

