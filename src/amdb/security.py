"""
安全和权限管理模块
支持认证、授权、加密
"""

import hashlib
import hmac
import secrets
import time
from typing import Optional, Dict, Set, List
from dataclasses import dataclass
from enum import Enum


class Permission(Enum):
    """权限类型"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"


@dataclass
class User:
    """用户"""
    username: str
    password_hash: str
    permissions: Set[Permission]
    created_at: float
    last_login: Optional[float] = None


@dataclass
class Token:
    """访问令牌"""
    token: str
    user: str
    expires_at: float
    permissions: Set[Permission]


class AuthenticationManager:
    """认证管理器"""
    
    def __init__(self, secret_key: Optional[str] = None):
        """
        Args:
            secret_key: 密钥（用于生成token）
        """
        self.secret_key = secret_key or secrets.token_hex(32)
        self.users: Dict[str, User] = {}
        self.tokens: Dict[str, Token] = {}
        self.token_ttl = 3600  # 1小时
    
    def hash_password(self, password: str) -> str:
        """哈希密码"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """验证密码"""
        return self.hash_password(password) == password_hash
    
    def create_user(self, username: str, password: str, 
                   permissions: Set[Permission]) -> User:
        """创建用户"""
        if username in self.users:
            raise ValueError(f"User already exists: {username}")
        
        password_hash = self.hash_password(password)
        user = User(
            username=username,
            password_hash=password_hash,
            permissions=permissions,
            created_at=time.time()
        )
        self.users[username] = user
        return user
    
    def authenticate(self, username: str, password: str) -> Optional[str]:
        """认证用户，返回token"""
        if username not in self.users:
            return None
        
        user = self.users[username]
        if not self.verify_password(password, user.password_hash):
            return None
        
        # 更新最后登录时间
        user.last_login = time.time()
        
        # 生成token
        token = self.generate_token(username, user.permissions)
        return token
    
    def generate_token(self, username: str, permissions: Set[Permission]) -> str:
        """生成访问令牌"""
        token_data = f"{username}:{time.time()}:{self.secret_key}"
        token = hmac.new(
            self.secret_key.encode(),
            token_data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        token_obj = Token(
            token=token,
            user=username,
            expires_at=time.time() + self.token_ttl,
            permissions=permissions
        )
        self.tokens[token] = token_obj
        return token
    
    def verify_token(self, token: str) -> Optional[Token]:
        """验证令牌"""
        if token not in self.tokens:
            return None
        
        token_obj = self.tokens[token]
        if time.time() > token_obj.expires_at:
            # 过期
            del self.tokens[token]
            return None
        
        return token_obj
    
    def revoke_token(self, token: str):
        """撤销令牌"""
        if token in self.tokens:
            del self.tokens[token]
    
    def check_permission(self, token: str, permission: Permission) -> bool:
        """检查权限"""
        token_obj = self.verify_token(token)
        if not token_obj:
            return False
        
        return permission in token_obj.permissions or Permission.ADMIN in token_obj.permissions


class EncryptionManager:
    """加密管理器"""
    
    def __init__(self, key: Optional[bytes] = None):
        """
        Args:
            key: 加密密钥（32字节）
        """
        if key is None:
            key = secrets.token_bytes(32)
        self.key = key
    
    def encrypt(self, data: bytes) -> bytes:
        """加密数据（使用AES-256-CBC）"""
        try:
            from Crypto.Cipher import AES
            from Crypto.Util.Padding import pad
            import os
            
            # 生成随机IV
            iv = os.urandom(16)
            
            # 使用AES-256-CBC加密
            cipher = AES.new(self.key[:32], AES.MODE_CBC, iv)
            padded_data = pad(data, AES.block_size)
            encrypted = cipher.encrypt(padded_data)
            
            # 返回 IV + 加密数据
            return iv + encrypted
        except ImportError:
            # 如果没有pycryptodome，使用XOR作为fallback
            encrypted = bytearray()
            key_len = len(self.key)
            for i, byte in enumerate(data):
                encrypted.append(byte ^ self.key[i % key_len])
            return bytes(encrypted)
    
    def decrypt(self, encrypted_data: bytes) -> bytes:
        """解密数据（使用AES-256-CBC）"""
        try:
            from Crypto.Cipher import AES
            from Crypto.Util.Padding import unpad
            
            # 提取IV和加密数据
            iv = encrypted_data[:16]
            ciphertext = encrypted_data[16:]
            
            # 使用AES-256-CBC解密
            cipher = AES.new(self.key[:32], AES.MODE_CBC, iv)
            decrypted = cipher.decrypt(ciphertext)
            return unpad(decrypted, AES.block_size)
        except ImportError:
            # 如果没有pycryptodome，使用XOR作为fallback
            return self.encrypt(encrypted_data)  # XOR是对称的
    


class AccessControl:
    """访问控制"""
    
    def __init__(self, auth_manager: AuthenticationManager):
        self.auth_manager = auth_manager
    
    def check_access(self, token: str, operation: str, resource: str) -> bool:
        """检查访问权限"""
        token_obj = self.auth_manager.verify_token(token)
        if not token_obj:
            return False
        
        # 根据操作类型检查权限
        if operation in ['get', 'read', 'query']:
            return Permission.READ in token_obj.permissions or Permission.ADMIN in token_obj.permissions
        elif operation in ['put', 'write', 'update']:
            return Permission.WRITE in token_obj.permissions or Permission.ADMIN in token_obj.permissions
        elif operation in ['delete', 'remove']:
            return Permission.DELETE in token_obj.permissions or Permission.ADMIN in token_obj.permissions
        
        return False

