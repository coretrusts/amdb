"""
网络功能测试
"""

import unittest
import time
import os
import tempfile
import shutil
import threading
from src.amdb import Database
from src.amdb.network import RemoteDatabase, DatabaseServer


class TestNetwork(unittest.TestCase):
    """网络功能测试"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.db = Database(data_dir=os.path.join(self.temp_dir, "network_db"))
        self.server = DatabaseServer(self.db, host="127.0.0.1", port=8888)
        self.server.start()
        time.sleep(0.5)  # 等待服务器启动
    
    def tearDown(self):
        """测试后清理"""
        self.server.stop()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_remote_put_get(self):
        """测试远程读写"""
        client = RemoteDatabase("127.0.0.1", 8888)
        
        self.assertTrue(client.connect())
        
        # 写入
        success = client.put(b"remote_key", b"remote_value")
        self.assertTrue(success)
        
        # 读取
        value = client.get(b"remote_key")
        self.assertEqual(value, b"remote_value")
        
        client.disconnect()
    
    def test_merkle_root_sync(self):
        """测试Merkle根同步"""
        # 本地写入
        self.db.put(b"local_key1", b"local_value1")
        self.db.put(b"local_key2", b"local_value2")
        local_root = self.db.get_root_hash()
        
        # 远程获取
        client = RemoteDatabase("127.0.0.1", 8888)
        self.assertTrue(client.connect())
        
        remote_root = client.get_merkle_root()
        self.assertIsNotNone(remote_root)
        self.assertEqual(local_root, remote_root)
        
        client.disconnect()
    
    def test_concurrent_remote_operations(self):
        """测试并发远程操作"""
        def remote_worker(worker_id: int):
            """远程工作线程"""
            client = RemoteDatabase("127.0.0.1", 8888)
            if not client.connect():
                return False
            
            success = True
            for i in range(10):
                key = f"worker_{worker_id}_key_{i}".encode()
                value = f"worker_{worker_id}_value_{i}".encode()
                if not client.put(key, value):
                    success = False
                    break
                
                retrieved = client.get(key)
                if retrieved != value:
                    success = False
                    break
            
            client.disconnect()
            return success
        
        # 启动多个工作线程
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(remote_worker, i) for i in range(5)]
            results = [f.result() for f in futures]
        
        self.assertTrue(all(results))


if __name__ == '__main__':
    unittest.main()

