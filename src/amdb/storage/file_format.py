"""
文件格式定义和序列化/反序列化
"""

import struct
import hashlib
from typing import List, Tuple, Optional, Dict, Any
from enum import IntEnum


class FileMagic:
    """文件魔数定义"""
    SST = b"SST\0"
    BPT = b"BPT\0"
    MPT = b"MPT\0"
    WAL = b"WAL\0"
    VER = b"VER\0"
    IDX = b"IDX\0"
    AMDB = b"AMDB"


class CompressionType(IntEnum):
    """压缩类型"""
    NONE = 0
    SNAPPY = 1
    LZ4 = 2


class SSTableFormat:
    """SSTable文件格式处理"""
    
    FILE_VERSION = 1
    HEADER_SIZE = 42  # 4+2+8+8+8+8+4
    
    @staticmethod
    def write_header(f, key_count: int, data_offset: int, index_offset: int):
        """写入文件头"""
        f.write(FileMagic.SST)  # 4 bytes
        f.write(struct.pack('H', SSTableFormat.FILE_VERSION))  # 2 bytes
        f.write(struct.pack('Q', key_count))  # 8 bytes
        f.write(struct.pack('Q', data_offset))  # 8 bytes
        f.write(struct.pack('Q', index_offset))  # 8 bytes
        f.write(struct.pack('Q', 0))  # footer_offset (稍后填充) 8 bytes
    
    @staticmethod
    def read_header(f) -> Tuple[int, int, int]:
        """读取文件头"""
        magic = f.read(4)
        if magic != FileMagic.SST:
            raise ValueError("Invalid SSTable file")
        
        version = struct.unpack('H', f.read(2))[0]
        key_count = struct.unpack('Q', f.read(8))[0]
        data_offset = struct.unpack('Q', f.read(8))[0]
        index_offset = struct.unpack('Q', f.read(8))[0]
        footer_offset = struct.unpack('Q', f.read(8))[0]
        
        return key_count, index_offset, footer_offset
    
    @staticmethod
    def write_entry(f, key: bytes, value: bytes, version: int, timestamp: float):
        """写入键值对条目"""
        f.write(struct.pack('I', len(key)))  # 4 bytes
        f.write(key)
        f.write(struct.pack('I', len(value)))  # 4 bytes
        f.write(value)
        f.write(struct.pack('I', version))  # 4 bytes
        f.write(struct.pack('d', timestamp))  # 8 bytes
    
    @staticmethod
    def read_entry(f) -> Optional[Tuple[bytes, bytes, int, float]]:
        """读取键值对条目"""
        try:
            key_len = struct.unpack('I', f.read(4))[0]
            key = f.read(key_len)
            value_len = struct.unpack('I', f.read(4))[0]
            value = f.read(value_len)
            version = struct.unpack('I', f.read(4))[0]
            timestamp = struct.unpack('d', f.read(8))[0]
            return (key, value, version, timestamp)
        except struct.error:
            return None
    
    @staticmethod
    def write_footer(f, index_offset: int, data: bytes):
        """写入footer"""
        footer_start = f.tell()
        f.write(struct.pack('Q', index_offset))  # 8 bytes
        checksum = hashlib.sha256(data).digest()
        f.write(checksum)  # 32 bytes
        f.write(FileMagic.SST)  # 4 bytes
        
        # 更新header中的footer_offset
        f.seek(34)  # footer_offset位置
        f.write(struct.pack('Q', footer_start))
        f.seek(0, 2)  # 回到文件末尾


class BPlusTreeFormat:
    """B+树节点文件格式处理"""
    
    FILE_VERSION = 1
    HEADER_SIZE = 27  # 4+8+1+2+8+8
    
    @staticmethod
    def write_node(f, node_id: int, is_leaf: bool, keys: List[bytes], 
                   values: List[bytes], parent_id: int = 0, next_leaf_id: int = 0):
        """写入节点"""
        f.write(FileMagic.BPT)  # 4 bytes
        f.write(struct.pack('Q', node_id))  # 8 bytes
        f.write(struct.pack('B', 1 if is_leaf else 0))  # 1 byte
        f.write(struct.pack('H', len(keys)))  # 2 bytes
        f.write(struct.pack('Q', parent_id))  # 8 bytes
        f.write(struct.pack('Q', next_leaf_id))  # 8 bytes
        
        # 写入键
        for key in keys:
            f.write(struct.pack('H', len(key)))  # 2 bytes
            f.write(key)
        
        # 写入值
        for value in values:
            if is_leaf:
                f.write(struct.pack('I', len(value)))  # 4 bytes
                f.write(value)
            else:
                # 内部节点：存储子节点ID
                f.write(struct.pack('Q', struct.unpack('Q', value[:8])[0] if len(value) >= 8 else 0))
        
        # 计算并写入checksum
        # 先关闭文件，重新打开读取数据
        current_pos = f.tell()
        f.close()
        
        # 重新打开文件读取数据
        with open(f.name, 'rb') as rf:
            data = rf.read()
        
        # 重新打开文件追加checksum
        with open(f.name, 'ab') as af:
            checksum = hashlib.sha256(data).digest()
            af.write(checksum)  # 32 bytes
    
    @staticmethod
    def read_node(f) -> Optional[Dict[str, Any]]:
        """读取节点"""
        try:
            magic = f.read(4)
            if magic != FileMagic.BPT:
                return None
            
            node_id = struct.unpack('Q', f.read(8))[0]
            is_leaf = struct.unpack('B', f.read(1))[0] == 1
            key_count = struct.unpack('H', f.read(2))[0]
            parent_id = struct.unpack('Q', f.read(8))[0]
            next_leaf_id = struct.unpack('Q', f.read(8))[0]
            
            keys = []
            for _ in range(key_count):
                key_len = struct.unpack('H', f.read(2))[0]
                keys.append(f.read(key_len))
            
            values = []
            for _ in range(key_count):
                if is_leaf:
                    value_len = struct.unpack('I', f.read(4))[0]
                    values.append(f.read(value_len))
                else:
                    child_id = struct.unpack('Q', f.read(8))[0]
                    values.append(struct.pack('Q', child_id))
            
            # 读取checksum
            checksum = f.read(32)
            
            return {
                'node_id': node_id,
                'is_leaf': is_leaf,
                'keys': keys,
                'values': values,
                'parent_id': parent_id,
                'next_leaf_id': next_leaf_id,
                'checksum': checksum
            }
        except struct.error:
            return None


class WALFormat:
    """WAL文件格式处理"""
    
    ENTRY_PUT = 0
    ENTRY_DELETE = 1
    ENTRY_COMMIT = 2
    ENTRY_ABORT = 3
    
    @staticmethod
    def write_entry(f, entry_type: int, key: bytes, value: Optional[bytes] = None, 
                   timestamp: Optional[float] = None):
        """写入WAL条目"""
        import time
        if timestamp is None:
            timestamp = time.time()
        
        f.write(struct.pack('B', entry_type))  # 1 byte
        f.write(struct.pack('d', timestamp))  # 8 bytes
        f.write(struct.pack('I', len(key)))  # 4 bytes
        f.write(key)
        
        if entry_type == WALFormat.ENTRY_PUT and value is not None:
            f.write(struct.pack('I', len(value)))  # 4 bytes
            f.write(value)
        
        # 计算checksum
        f.seek(f.tell() - (1 + 8 + 4 + len(key) + (4 + len(value) if value else 0)))
        data = f.read()
        f.seek(0, 2)
        checksum = hashlib.sha256(data).digest()
        f.write(checksum)  # 32 bytes
    
    @staticmethod
    def read_entry(f) -> Optional[Dict[str, Any]]:
        """读取WAL条目"""
        try:
            entry_type = struct.unpack('B', f.read(1))[0]
            timestamp = struct.unpack('d', f.read(8))[0]
            key_len = struct.unpack('I', f.read(4))[0]
            key = f.read(key_len)
            
            value = None
            if entry_type == WALFormat.ENTRY_PUT:
                value_len = struct.unpack('I', f.read(4))[0]
                value = f.read(value_len)
            
            checksum = f.read(32)
            
            return {
                'type': entry_type,
                'timestamp': timestamp,
                'key': key,
                'value': value,
                'checksum': checksum
            }
        except struct.error:
            return None

