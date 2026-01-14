"""
数据压缩模块
支持多种压缩算法
"""

import zlib
import lzma
from typing import Optional
from enum import IntEnum
from .storage.file_format import CompressionType


class Compressor:
    """压缩器"""
    
    @staticmethod
    def compress(data: bytes, method: CompressionType = CompressionType.SNAPPY) -> bytes:
        """
        压缩数据
        Args:
            data: 原始数据
            method: 压缩方法
        Returns:
            压缩后的数据（包含压缩标记）
        """
        if method == CompressionType.NONE:
            return bytes([CompressionType.NONE.value]) + data
        
        elif method == CompressionType.SNAPPY:
            # 使用zlib作为Snappy的替代（Python标准库没有snappy）
            compressed = zlib.compress(data, level=1)  # level 1 = 最快
            return bytes([CompressionType.SNAPPY.value]) + compressed
        
        elif method == CompressionType.LZ4:
            # 使用lzma作为LZ4的替代
            compressed = lzma.compress(data, preset=1)  # preset 1 = 最快
            return bytes([CompressionType.LZ4.value]) + compressed
        
        else:
            raise ValueError(f"Unsupported compression method: {method}")
    
    @staticmethod
    def decompress(data: bytes) -> bytes:
        """
        解压数据
        Args:
            data: 压缩数据（包含压缩标记）
        Returns:
            解压后的数据
        """
        if len(data) < 1:
            raise ValueError("Data too short")
        
        method = CompressionType(data[0])
        compressed_data = data[1:]
        
        if method == CompressionType.NONE:
            return compressed_data
        
        elif method == CompressionType.SNAPPY:
            return zlib.decompress(compressed_data)
        
        elif method == CompressionType.LZ4:
            return lzma.decompress(compressed_data)
        
        else:
            raise ValueError(f"Unsupported compression method: {method}")
    
    @staticmethod
    def get_compression_ratio(original: bytes, compressed: bytes) -> float:
        """计算压缩比"""
        if len(original) == 0:
            return 0.0
        return len(compressed) / len(original)


class BlockCompressor:
    """块压缩器（用于大文件分块压缩）"""
    
    def __init__(self, block_size: int = 64 * 1024):  # 64KB
        """
        Args:
            block_size: 压缩块大小
        """
        self.block_size = block_size
    
    def compress_blocks(self, data: bytes, 
                       method: CompressionType = CompressionType.SNAPPY) -> bytes:
        """分块压缩"""
        result = b''
        offset = 0
        
        while offset < len(data):
            block = data[offset:offset + self.block_size]
            compressed_block = Compressor.compress(block, method)
            
            # 写入块大小（4字节）
            result += len(compressed_block).to_bytes(4, 'big')
            result += compressed_block
            
            offset += self.block_size
        
        return result
    
    def decompress_blocks(self, data: bytes) -> bytes:
        """分块解压"""
        result = b''
        offset = 0
        
        while offset < len(data):
            # 读取块大小
            if offset + 4 > len(data):
                break
            
            block_size = int.from_bytes(data[offset:offset+4], 'big')
            offset += 4
            
            if offset + block_size > len(data):
                break
            
            # 解压块
            compressed_block = data[offset:offset + block_size]
            decompressed_block = Compressor.decompress(compressed_block)
            result += decompressed_block
            
            offset += block_size
        
        return result

