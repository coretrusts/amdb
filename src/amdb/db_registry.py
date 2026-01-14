# -*- coding: utf-8 -*-
"""
数据库注册表
管理多个数据库实例，支持通过数据库名称访问
类似MySQL的数据库管理方式
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional, List
from .config import DatabaseConfig


class DatabaseRegistry:
    """数据库注册表"""
    
    REGISTRY_FILE = "database_registry.json"
    
    def __init__(self, registry_dir: str = "./data"):
        """
        Args:
            registry_dir: 注册表目录（通常与数据目录相同）
        """
        self.registry_dir = Path(registry_dir)
        self.registry_file = self.registry_dir / self.REGISTRY_FILE
        self.registries: Dict[str, Dict] = {}
        self._load_registry()
    
    def _load_registry(self):
        """加载注册表"""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, 'r', encoding='utf-8') as f:
                    self.registries = json.load(f)
            except Exception as e:
                print(f"加载注册表失败: {e}")
                self.registries = {}
        else:
            self.registries = {}
    
    def _save_registry(self):
        """保存注册表"""
        try:
            self.registry_dir.mkdir(parents=True, exist_ok=True)
            with open(self.registry_file, 'w', encoding='utf-8') as f:
                json.dump(self.registries, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存注册表失败: {e}")
    
    def register_database(self, db_name: str, data_dir: str, 
                         description: str = "", config_path: Optional[str] = None):
        """
        注册数据库
        
        Args:
            db_name: 数据库名称
            data_dir: 数据目录路径
            description: 数据库描述
            config_path: 配置文件路径（可选）
        """
        self.registries[db_name] = {
            "data_dir": str(data_dir),
            "description": description,
            "config_path": config_path or "",
            "created_at": str(Path(data_dir).stat().st_ctime) if Path(data_dir).exists() else ""
        }
        self._save_registry()
    
    def unregister_database(self, db_name: str):
        """取消注册数据库"""
        if db_name in self.registries:
            del self.registries[db_name]
            self._save_registry()
    
    def get_database_path(self, db_name: str) -> Optional[str]:
        """获取数据库路径"""
        if db_name in self.registries:
            return self.registries[db_name]["data_dir"]
        return None
    
    def get_database_info(self, db_name: str) -> Optional[Dict]:
        """获取数据库信息"""
        return self.registries.get(db_name)
    
    def list_databases(self) -> List[str]:
        """列出所有已注册的数据库"""
        return list(self.registries.keys())
    
    def find_database_by_path(self, data_dir: str) -> Optional[str]:
        """通过路径查找数据库名称"""
        data_dir = str(Path(data_dir).absolute())
        for db_name, info in self.registries.items():
            if str(Path(info["data_dir"]).absolute()) == data_dir:
                return db_name
        return None
    
    def auto_register_from_data_dir(self, data_dir: str = "./data"):
        """自动从数据目录注册数据库"""
        data_path = Path(data_dir)
        if not data_path.exists():
            return
        
        # 扫描数据目录下的所有子目录
        for item in data_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # 检查是否是数据库目录（有database.ini或versions目录）
                db_ini = item / "database.ini"
                versions_dir = item / "versions"
                
                if db_ini.exists() or versions_dir.exists():
                    db_name = item.name
                    if db_name not in self.registries:
                        # 尝试读取描述
                        description = ""
                        if db_ini.exists():
                            try:
                                from .config import load_config
                                config = load_config(str(db_ini))
                                # 从metadata读取描述
                                metadata_file = item / "database.amdb"
                                if metadata_file.exists():
                                    import json
                                    with open(metadata_file, 'r', encoding='utf-8') as f:
                                        metadata = json.load(f)
                                        description = metadata.get('description', '')
                            except:
                                pass
                        
                        self.register_database(
                            db_name, 
                            str(item),
                            description=description
                        )

