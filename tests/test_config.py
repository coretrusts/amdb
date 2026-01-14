"""
配置管理测试
"""

import unittest
import tempfile
import os
from src.amdb.config import DatabaseConfig, load_config


class TestConfig(unittest.TestCase):
    """配置测试"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = DatabaseConfig()
        self.assertIsNotNone(config.storage)
        self.assertIsNotNone(config.network)
        self.assertIsNotNone(config.cache)
    
    def test_config_serialization(self):
        """测试配置序列化"""
        config = DatabaseConfig()
        config_dict = config.to_dict()
        self.assertIn('storage', config_dict)
        self.assertIn('network', config_dict)
        
        # 从字典恢复
        new_config = DatabaseConfig.from_dict(config_dict)
        self.assertEqual(config.storage.data_dir, new_config.storage.data_dir)
    
    def test_config_file(self):
        """测试配置文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config = DatabaseConfig()
            config.save_to_file(f.name)
            
            # 加载配置
            loaded_config = DatabaseConfig()
            loaded_config.load_from_file(f.name)
            
            self.assertEqual(config.storage.data_dir, loaded_config.storage.data_dir)
            
            os.unlink(f.name)

