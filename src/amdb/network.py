"""
网络和外部链接支持
支持远程数据库连接和数据同步
"""

import socket
import struct
import json
import threading
import time
from typing import Optional, Dict, Any, List, Tuple, Callable
from enum import IntEnum
import hashlib


class MessageType(IntEnum):
    """消息类型"""
    PING = 0
    PONG = 1
    PUT = 2
    GET = 3
    GET_RESPONSE = 4
    SYNC_REQUEST = 5
    SYNC_RESPONSE = 6
    MERKLE_ROOT = 7
    VERIFY = 8
    VERIFY_RESPONSE = 9
    GET_STATS = 10          # 获取统计信息
    GET_ALL_KEYS = 11       # 获取所有键
    BATCH_PUT = 12          # 批量写入
    DELETE = 13             # 删除键
    GET_CONFIG = 14         # 获取配置
    SET_CONFIG = 15         # 设置配置


class NetworkProtocol:
    """网络协议处理"""
    
    HEADER_SIZE = 9  # type(1) + length(4) + checksum(4)
    
    @staticmethod
    def encode_message(msg_type: MessageType, data: bytes) -> bytes:
        """编码消息"""
        length = len(data)
        header = struct.pack('B', msg_type.value) + struct.pack('I', length)
        checksum = struct.pack('I', hash(data) & 0xFFFFFFFF)
        return header + checksum + data
    
    @staticmethod
    def decode_message(data: bytes) -> Tuple[MessageType, bytes]:
        """解码消息"""
        if len(data) < NetworkProtocol.HEADER_SIZE:
            raise ValueError("Message too short")
        
        msg_type = MessageType(struct.unpack('B', data[0:1])[0])
        length = struct.unpack('I', data[1:5])[0]
        checksum = struct.unpack('I', data[5:9])[0]
        payload = data[9:9+length]
        
        # 验证checksum
        if (hash(payload) & 0xFFFFFFFF) != checksum:
            raise ValueError("Checksum mismatch")
        
        return msg_type, payload


class RemoteDatabase:
    """远程数据库客户端"""
    
    def __init__(self, host: str, port: int, database: str = "default", timeout: float = 5.0):
        """
        Args:
            host: 服务器地址
            port: 服务器端口
            database: 数据库名称（默认"default"）
            timeout: 超时时间（秒）
        """
        self.host = host
        self.port = port
        self.database = database
        self.timeout = timeout
        self.socket: Optional[socket.socket] = None
        self.lock = threading.RLock()
    
    def connect(self) -> bool:
        """连接到服务器"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            self.socket.connect((self.host, self.port))
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        with self.lock:
            if self.socket:
                try:
                    self.socket.close()
                except Exception:
                    pass
                self.socket = None
    
    def put(self, key: bytes, value: bytes) -> bool:
        """远程写入"""
        with self.lock:
            if not self.socket:
                if not self.connect():
                    return False
            
            try:
                data = json.dumps({
                    'database': self.database,
                    'key': key.hex(),
                    'value': value.hex()
                }).encode()
                msg = NetworkProtocol.encode_message(MessageType.PUT, data)
                self.socket.sendall(struct.pack('I', len(msg)) + msg)
                
                # 等待响应
                response_len = struct.unpack('I', self._recv_exact(4))[0]
                response = self._recv_exact(response_len)
                msg_type, payload = NetworkProtocol.decode_message(response)
                
                if msg_type == MessageType.PONG:
                    result = json.loads(payload.decode())
                    return result.get('success', False)
                return False
            except Exception as e:
                print(f"Put failed: {e}")
                self.disconnect()
                return False
    
    def get(self, key: bytes) -> Optional[bytes]:
        """远程读取"""
        with self.lock:
            if not self.socket:
                if not self.connect():
                    return None
            
            try:
                data = json.dumps({
                    'database': self.database,
                    'key': key.hex()
                }).encode()
                msg = NetworkProtocol.encode_message(MessageType.GET, data)
                self.socket.sendall(struct.pack('I', len(msg)) + msg)
                
                # 等待响应
                response_len = struct.unpack('I', self._recv_exact(4))[0]
                response = self._recv_exact(response_len)
                msg_type, payload = NetworkProtocol.decode_message(response)
                
                if msg_type == MessageType.GET_RESPONSE or msg_type == MessageType.PONG:
                    result = json.loads(payload.decode())
                    if result.get('found'):
                        return bytes.fromhex(result['value'])
                return None
            except Exception as e:
                print(f"Get failed: {e}")
                self.disconnect()
                return None
    
    def get_merkle_root(self) -> Optional[bytes]:
        """获取远程Merkle根"""
        with self.lock:
            if not self.socket:
                if not self.connect():
                    return None
            
            try:
                data = json.dumps({'database': self.database}).encode()
                msg = NetworkProtocol.encode_message(MessageType.MERKLE_ROOT, data)
                self.socket.sendall(struct.pack('I', len(msg)) + msg)
                
                response_len = struct.unpack('I', self._recv_exact(4))[0]
                response = self._recv_exact(response_len)
                msg_type, payload = NetworkProtocol.decode_message(response)
                
                if msg_type == MessageType.MERKLE_ROOT or msg_type == MessageType.PONG:
                    result = json.loads(payload.decode())
                    if 'root' in result:
                        return bytes.fromhex(result['root'])
                return None
            except Exception as e:
                print(f"Get merkle root failed: {e}")
                self.disconnect()
                return None
    
    def get_stats(self) -> Optional[Dict]:
        """获取远程数据库统计信息"""
        with self.lock:
            if not self.socket:
                if not self.connect():
                    return None
            
            try:
                data = json.dumps({'database': self.database}).encode()
                msg = NetworkProtocol.encode_message(MessageType.GET_STATS, data)
                self.socket.sendall(struct.pack('I', len(msg)) + msg)
                
                response_len = struct.unpack('I', self._recv_exact(4))[0]
                response = self._recv_exact(response_len)
                msg_type, payload = NetworkProtocol.decode_message(response)
                
                if msg_type == MessageType.PONG:
                    result = json.loads(payload.decode())
                    if 'error' not in result:
                        # 转换hex字符串回bytes
                        stats = {}
                        for k, v in result.items():
                            if isinstance(v, str) and len(v) > 0 and all(c in '0123456789abcdefABCDEF' for c in v):
                                try:
                                    stats[k] = bytes.fromhex(v)
                                except:
                                    stats[k] = v
                            else:
                                stats[k] = v
                        return stats
                return None
            except Exception as e:
                print(f"Get stats failed: {e}")
                self.disconnect()
                return None
    
    def get_all_keys(self) -> List[bytes]:
        """获取所有键"""
        with self.lock:
            if not self.socket:
                if not self.connect():
                    return []
            
            try:
                data = json.dumps({'database': self.database}).encode()
                msg = NetworkProtocol.encode_message(MessageType.GET_ALL_KEYS, data)
                self.socket.sendall(struct.pack('I', len(msg)) + msg)
                
                response_len = struct.unpack('I', self._recv_exact(4))[0]
                response = self._recv_exact(response_len)
                msg_type, payload = NetworkProtocol.decode_message(response)
                
                if msg_type == MessageType.PONG:
                    result = json.loads(payload.decode())
                    if 'keys' in result:
                        return [bytes.fromhex(k) for k in result['keys']]
                return []
            except Exception as e:
                print(f"Get all keys failed: {e}")
                self.disconnect()
                return []
    
    def batch_put(self, items: List[Tuple[bytes, bytes]]) -> Tuple[bool, Optional[bytes]]:
        """批量写入"""
        with self.lock:
            if not self.socket:
                if not self.connect():
                    return False, None
            
            try:
                items_data = [
                    {'key': k.hex(), 'value': v.hex()}
                    for k, v in items
                ]
                data = json.dumps({
                    'database': self.database,
                    'items': items_data
                }).encode()
                msg = NetworkProtocol.encode_message(MessageType.BATCH_PUT, data)
                self.socket.sendall(struct.pack('I', len(msg)) + msg)
                
                response_len = struct.unpack('I', self._recv_exact(4))[0]
                response = self._recv_exact(response_len)
                msg_type, payload = NetworkProtocol.decode_message(response)
                
                if msg_type == MessageType.PONG:
                    result = json.loads(payload.decode())
                    if result.get('success'):
                        merkle_root = bytes.fromhex(result['merkle_root']) if result.get('merkle_root') else None
                        return True, merkle_root
                return False, None
            except Exception as e:
                print(f"Batch put failed: {e}")
                self.disconnect()
                return False, None
    
    def delete(self, key: bytes) -> bool:
        """删除键"""
        with self.lock:
            if not self.socket:
                if not self.connect():
                    return False
            
            try:
                data = json.dumps({
                    'database': self.database,
                    'key': key.hex()
                }).encode()
                msg = NetworkProtocol.encode_message(MessageType.DELETE, data)
                self.socket.sendall(struct.pack('I', len(msg)) + msg)
                
                response_len = struct.unpack('I', self._recv_exact(4))[0]
                response = self._recv_exact(response_len)
                msg_type, payload = NetworkProtocol.decode_message(response)
                
                if msg_type == MessageType.PONG:
                    result = json.loads(payload.decode())
                    return result.get('success', False)
                return False
            except Exception as e:
                print(f"Delete failed: {e}")
                self.disconnect()
                return False
    
    def get_config(self) -> Optional[Dict]:
        """获取远程数据库配置"""
        with self.lock:
            if not self.socket:
                if not self.connect():
                    return None
            
            try:
                data = json.dumps({'database': self.database}).encode()
                msg = NetworkProtocol.encode_message(MessageType.GET_CONFIG, data)
                self.socket.sendall(struct.pack('I', len(msg)) + msg)
                
                response_len = struct.unpack('I', self._recv_exact(4))[0]
                response = self._recv_exact(response_len)
                msg_type, payload = NetworkProtocol.decode_message(response)
                
                if msg_type == MessageType.PONG:
                    result = json.loads(payload.decode())
                    if 'error' not in result:
                        return result
                return None
            except Exception as e:
                print(f"Get config failed: {e}")
                self.disconnect()
                return None
    
    def _recv_exact(self, n: int) -> bytes:
        """精确接收n字节"""
        data = b''
        while len(data) < n:
            chunk = self.socket.recv(n - len(data))
            if not chunk:
                raise ConnectionError("Connection closed")
            data += chunk
        return data
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()


class NetworkServer:
    """网络服务器（别名，用于兼容server.py）"""
    def __init__(self, db, config=None, host: str = "0.0.0.0", port: int = 3888):
        """
        Args:
            db: Database实例
            config: DatabaseConfig实例（可选）
            host: 监听地址（如果config提供则使用config的值）
            port: 监听端口（如果config提供则使用config的值）
        """
        if config:
            host = config.network_host
            port = config.network_port
        self._server = DatabaseServer(db, host, port)
    
    def start(self):
        """启动服务器"""
        self._server.start()
    
    def stop(self):
        """停止服务器"""
        self._server.stop()


class DatabaseServer:
    """数据库服务器（用于远程访问）"""
    
    def __init__(self, db, host: str = "0.0.0.0", port: int = 8888):
        """
        Args:
            db: Database实例
            host: 监听地址
            port: 监听端口
        """
        self.db = db
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.running = False
        self.thread: Optional[threading.Thread] = None
    
    def start(self):
        """启动服务器"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen(10)
        self.running = True
        
        self.thread = threading.Thread(target=self._accept_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """停止服务器"""
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
    
    def _accept_loop(self):
        """接受连接循环"""
        while self.running:
            try:
                client_socket, addr = self.socket.accept()
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, addr),
                    daemon=True
                )
                client_thread.start()
            except Exception:
                break
    
    def _handle_client(self, client_socket: socket.socket, addr: Tuple[str, int]):
        """处理客户端请求"""
        try:
            while self.running:
                # 接收消息长度
                length_data = client_socket.recv(4)
                if len(length_data) < 4:
                    break
                
                msg_length = struct.unpack('I', length_data)[0]
                msg_data = b''
                while len(msg_data) < msg_length:
                    chunk = client_socket.recv(msg_length - len(msg_data))
                    if not chunk:
                        break
                    msg_data += chunk
                
                if len(msg_data) < msg_length:
                    break
                
                # 解码消息
                try:
                    msg_type, payload = NetworkProtocol.decode_message(msg_data)
                    response = self._process_message(msg_type, payload)
                    
                    # 发送响应
                    if response:
                        response_msg = NetworkProtocol.encode_message(
                            MessageType.PONG, response
                        )
                        client_socket.sendall(
                            struct.pack('I', len(response_msg)) + response_msg
                        )
                except Exception as e:
                    print(f"Error processing message: {e}")
                    break
        except Exception as e:
            print(f"Client connection error: {e}")
        finally:
            try:
                client_socket.close()
            except Exception:
                pass
    
    def _process_message(self, msg_type: MessageType, payload: bytes) -> Optional[bytes]:
        """处理消息"""
        try:
            request = json.loads(payload.decode()) if payload else {}
            db_name = request.get('database', 'default')
            
            # 获取数据库实例（支持多数据库）
            db = self._get_database(db_name)
            if not db:
                return json.dumps({'error': f'Database {db_name} not found'}).encode()
            
            if msg_type == MessageType.PUT:
                key = bytes.fromhex(request['key'])
                value = bytes.fromhex(request['value'])
                success, merkle_root = db.put(key, value)
                return json.dumps({
                    'success': success,
                    'merkle_root': merkle_root.hex() if merkle_root else ''
                }).encode()
            
            elif msg_type == MessageType.GET:
                key = bytes.fromhex(request['key'])
                value = db.get(key)
                return json.dumps({
                    'found': value is not None,
                    'value': value.hex() if value else ''
                }).encode()
            
            elif msg_type == MessageType.BATCH_PUT:
                items = request.get('items', [])
                batch_items = []
                for item in items:
                    batch_items.append((
                        bytes.fromhex(item['key']),
                        bytes.fromhex(item['value'])
                    ))
                success, merkle_root = db.batch_put(batch_items)
                return json.dumps({
                    'success': success,
                    'count': len(batch_items),
                    'merkle_root': merkle_root.hex() if merkle_root else ''
                }).encode()
            
            elif msg_type == MessageType.DELETE:
                key = bytes.fromhex(request['key'])
                success = db.delete(key)
                return json.dumps({'success': success}).encode()
            
            elif msg_type == MessageType.GET_STATS:
                stats = db.get_stats()
                # 转换bytes为hex字符串以便JSON序列化
                stats_serializable = {}
                for k, v in stats.items():
                    if isinstance(v, bytes):
                        stats_serializable[k] = v.hex()
                    else:
                        stats_serializable[k] = v
                return json.dumps(stats_serializable).encode()
            
            elif msg_type == MessageType.GET_ALL_KEYS:
                all_keys = db.version_manager.get_all_keys()
                keys_hex = [k.hex() for k in all_keys]
                return json.dumps({
                    'keys': keys_hex,
                    'count': len(keys_hex)
                }).encode()
            
            elif msg_type == MessageType.GET_CONFIG:
                config = db.config
                # 将配置转换为字典
                config_dict = {
                    'data_dir': config.data_dir,
                    'network_host': config.network_host,
                    'network_port': config.network_port,
                    'batch_max_size': config.batch_max_size,
                    'enable_sharding': config.enable_sharding,
                    'shard_count': config.shard_count,
                    'threading_enable': config.threading_enable,
                    'threading_max_workers': config.threading_max_workers,
                }
                return json.dumps(config_dict).encode()
            
            elif msg_type == MessageType.MERKLE_ROOT:
                root = db.get_root_hash()
                return json.dumps({'root': root.hex()}).encode()
            
            elif msg_type == MessageType.PING:
                return json.dumps({'status': 'pong'}).encode()
            
        except Exception as e:
            import traceback
            error_msg = f"{type(e).__name__}: {str(e)}"
            traceback.print_exc()
            return json.dumps({'error': error_msg}).encode()
        
        return None
    
    def _get_database(self, db_name: str):
        """获取数据库实例（支持多数据库）"""
        if db_name == 'default' or db_name == '':
            return self.db
        
        # 如果已缓存，直接返回
        if db_name in self.databases:
            return self.databases[db_name]
        
        # 尝试从注册表加载
        try:
            from .db_registry import DatabaseRegistry
            registry = DatabaseRegistry()
            db_path = registry.get_database_path(db_name)
            if db_path:
                from .database import Database
                db = Database(data_dir=db_path)
                self.databases[db_name] = db
                return db
        except Exception as e:
            print(f"加载数据库 {db_name} 失败: {e}")
        
        return None




class DatabaseWrapper:
    """统一接口包装器，封装Database和RemoteDatabase"""
    
    def __init__(self, db=None, remote_db=None):
        """
        Args:
            db: 本地Database实例
            remote_db: 远程RemoteDatabase实例
        """
        if db and remote_db:
            raise ValueError("不能同时提供db和remote_db")
        if not db and not remote_db:
            raise ValueError("必须提供db或remote_db之一")
        
        self.db = db
        self.remote_db = remote_db
        self.is_remote = remote_db is not None
    
    def put(self, key, value):
        """写入数据"""
        if self.is_remote:
            return self.remote_db.put(key, value)
        else:
            return self.db.put(key, value)
    
    def get(self, key, version=None):
        """读取数据"""
        if self.is_remote:
            return self.remote_db.get(key, version)
        else:
            return self.db.get(key, version)
    
    def batch_put(self, items):
        """批量写入"""
        if self.is_remote:
            return self.remote_db.batch_put(items)
        else:
            return self.db.batch_put(items)
    
    def delete(self, key):
        """删除数据"""
        if self.is_remote:
            return self.remote_db.delete(key)
        else:
            return self.db.delete(key)
    
    def flush(self, force_sync=False):
        """刷新"""
        if self.is_remote:
            return self.remote_db.flush(force_sync)
        else:
            return self.db.flush(force_sync)
    
    def get_stats(self):
        """获取统计信息"""
        if self.is_remote:
            return self.remote_db.get_stats()
        else:
            return self.db.get_stats()
    
    def get_history(self, key):
        """获取版本历史"""
        if self.is_remote:
            return self.remote_db.get_history(key)
        else:
            return self.db.version_manager.get_history(key)
    
    def get_all_keys(self):
        """获取所有键"""
        if self.is_remote:
            return self.remote_db.get_all_keys()
        else:
            return self.db.version_manager.get_all_keys()
    
    def get_config(self):
        """获取配置信息"""
        if self.is_remote:
            # RemoteDatabase可能没有get_config方法，返回None或空字典
            if hasattr(self.remote_db, 'get_config'):
                return self.remote_db.get_config()
            else:
                return {}
        else:
            # Database可能没有get_config方法，返回None或空字典
            if hasattr(self.db, 'get_config'):
                return self.db.get_config()
            else:
                return {}
