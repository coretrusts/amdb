"""
安全模块测试
"""

import unittest
from src.amdb.security import AuthenticationManager, Permission, EncryptionManager


class TestSecurity(unittest.TestCase):
    """安全测试"""
    
    def test_user_authentication(self):
        """测试用户认证"""
        auth_mgr = AuthenticationManager()
        
        # 创建用户
        user = auth_mgr.create_user(
            "testuser",
            "password123",
            {Permission.READ, Permission.WRITE}
        )
        self.assertEqual(user.username, "testuser")
        
        # 认证成功
        token = auth_mgr.authenticate("testuser", "password123")
        self.assertIsNotNone(token)
        
        # 认证失败
        token2 = auth_mgr.authenticate("testuser", "wrongpassword")
        self.assertIsNone(token2)
    
    def test_token_verification(self):
        """测试令牌验证"""
        auth_mgr = AuthenticationManager()
        auth_mgr.create_user("user1", "pass1", {Permission.READ})
        
        token = auth_mgr.authenticate("user1", "pass1")
        self.assertIsNotNone(token)
        
        # 验证令牌
        token_obj = auth_mgr.verify_token(token)
        self.assertIsNotNone(token_obj)
        self.assertEqual(token_obj.user, "user1")
    
    def test_permission_check(self):
        """测试权限检查"""
        auth_mgr = AuthenticationManager()
        auth_mgr.create_user("user1", "pass1", {Permission.READ})
        
        token = auth_mgr.authenticate("user1", "pass1")
        
        # 检查权限
        self.assertTrue(auth_mgr.check_permission(token, Permission.READ))
        self.assertFalse(auth_mgr.check_permission(token, Permission.WRITE))
    
    def test_encryption(self):
        """测试加密"""
        enc_mgr = EncryptionManager()
        
        data = b"test data"
        encrypted = enc_mgr.encrypt(data)
        self.assertNotEqual(data, encrypted)
        
        decrypted = enc_mgr.decrypt(encrypted)
        self.assertEqual(data, decrypted)

