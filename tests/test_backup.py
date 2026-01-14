"""
备份恢复测试
"""

import unittest
import tempfile
import shutil
from src.amdb import Database
from src.amdb.backup import BackupManager


class TestBackup(unittest.TestCase):
    """备份测试"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = f"{self.temp_dir}/data"
        self.backup_dir = f"{self.temp_dir}/backups"
        
        self.db = Database(data_dir=self.data_dir)
        self.backup_mgr = BackupManager(self.data_dir, self.backup_dir)
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_full_backup(self):
        """测试全量备份"""
        # 写入一些数据
        self.db.put(b"key1", b"value1")
        self.db.put(b"key2", b"value2")
        
        # 创建备份
        backup_path = self.backup_mgr.create_full_backup("test_backup")
        self.assertTrue(os.path.exists(backup_path))
        
        # 列出备份
        backups = self.backup_mgr.list_backups()
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0]['name'], "test_backup")
    
    def test_restore_backup(self):
        """测试恢复备份"""
        # 写入数据并备份
        self.db.put(b"key1", b"value1")
        backup_path = self.backup_mgr.create_full_backup("test_backup")
        
        # 修改数据
        self.db.put(b"key1", b"value2")
        
        # 恢复备份
        restore_dir = f"{self.temp_dir}/restored"
        self.backup_mgr.restore_backup("test_backup", restore_dir)
        
        # 验证恢复
        restored_db = Database(data_dir=restore_dir)
        value = restored_db.get(b"key1")
        self.assertEqual(value, b"value1")

