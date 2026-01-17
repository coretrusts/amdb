"""
Merkle树实现 - 用于数据完整性验证
基于Merkle Patricia Tree (MPT)，支持增量更新
支持持久化到磁盘（.mpt文件）
"""

import hashlib
import os
import struct
import json
from typing import Optional, Dict, List, Tuple
from enum import Enum
from .file_format import FileMagic


class NodeType(Enum):
    """节点类型"""
    LEAF = "leaf"  # 叶子节点
    EXTENSION = "extension"  # 扩展节点
    BRANCH = "branch"  # 分支节点


class MerkleNode:
    """Merkle树节点"""
    
    def __init__(self, node_type: NodeType, data: Dict):
        self.node_type = node_type
        self.data = data
        self.hash: Optional[bytes] = None
        self._compute_hash()
    
    def _compute_hash(self):
        """计算节点哈希"""
        if self.node_type == NodeType.LEAF:
            # 叶子节点：hash(key + value)
            key = self.data.get('key', b'')
            value = self.data.get('value', b'')
            content = b'leaf:' + key + b':' + value
        elif self.node_type == NodeType.EXTENSION:
            # 扩展节点：hash(prefix + child_hash)
            prefix = self.data.get('prefix', b'')
            child_hash = self.data.get('child_hash', b'')
            content = b'ext:' + prefix + b':' + child_hash
        else:  # BRANCH
            # 分支节点：hash(所有子节点哈希)
            children = self.data.get('children', [b''] * 16)
            content = b'branch:' + b''.join(children)
        
        self.hash = hashlib.sha256(content).digest()
    
    def get_hash(self) -> bytes:
        """获取节点哈希"""
        return self.hash


class MerkleTree:
    """
    Merkle Patricia Tree (MPT) 实现
    用于区块链数据完整性验证
    支持持久化到磁盘（.mpt文件）
    """
    
    def __init__(self, data_dir: str = "./data/merkle"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self.root: Optional[MerkleNode] = None
        self.nodes: Dict[bytes, MerkleNode] = {}  # hash -> node
        self.key_value_map: Dict[bytes, bytes] = {}  # key -> value
        self.mpt_file = os.path.join(data_dir, "merkle_tree.mpt")
        
        # 从磁盘加载
        self._load_from_disk()
    
    def put(self, key: bytes, value: bytes) -> bytes:
        """插入键值对，返回根哈希"""
        self.key_value_map[key] = value
        self.root = self._build_tree()
        return self.root.get_hash() if self.root else b''
    
    def get(self, key: bytes) -> Optional[bytes]:
        """获取值"""
        return self.key_value_map.get(key)
    
    def get_root_hash(self) -> bytes:
        """获取根哈希"""
        if self.root:
            return self.root.get_hash()
        return b''
    
    def verify(self, key: bytes, value: bytes, proof: List[bytes]) -> bool:
        """验证键值对（使用Merkle证明，完整MPT结构）"""
        if not self.root:
            return False
        
        # 计算叶子节点哈希
        leaf_hash = hashlib.sha256(b'leaf:' + key + b':' + value).digest()
        
        # 使用证明路径重建根哈希（按照MPT结构）
        current_hash = leaf_hash
        current_key_nibbles = []
        
        # 将key转换为nibble序列
        for byte in key:
            current_key_nibbles.append((byte >> 4) & 0xF)
            current_key_nibbles.append(byte & 0xF)
        
        # 按照证明路径重建
        proof_index = 0
        for i in range(len(current_key_nibbles)):
            if proof_index >= len(proof):
                break
            
            nibble = current_key_nibbles[i]
            proof_hash = proof[proof_index]
            
            # 构建分支节点哈希
            children = [b''] * 16
            children[nibble] = current_hash
            # 其他位置使用证明哈希
            for j, ph in enumerate(proof[proof_index:proof_index+15]):
                if j != nibble and j < 16:
                    children[j] = ph
            
            # 计算分支节点哈希
            branch_content = b'branch:' + b''.join(children)
            current_hash = hashlib.sha256(branch_content).digest()
            proof_index += 1
        
        # 如果还有剩余的证明哈希，继续合并
        while proof_index < len(proof):
            current_hash = hashlib.sha256(current_hash + proof[proof_index]).digest()
            proof_index += 1
        
        # 验证是否匹配根哈希
        return current_hash == self.get_root_hash()
    
    def _build_tree(self) -> Optional[MerkleNode]:
        """构建Merkle Patricia Tree"""
        if not self.key_value_map:
            return None
        
        if len(self.key_value_map) == 1:
            # 单个键值对，创建叶子节点
            key, value = next(iter(self.key_value_map.items()))
            node = MerkleNode(NodeType.LEAF, {'key': key, 'value': value})
            self.nodes[node.get_hash()] = node
            return node
        
        # 构建MPT树
        root = self._build_mpt_node(list(self.key_value_map.items()), 0)
        return root
    
    def _build_mpt_node(self, items: List[Tuple[bytes, bytes]], nibble_pos: int) -> MerkleNode:
        """递归构建MPT节点"""
        if len(items) == 1:
            # 单个项，创建叶子节点
            key, value = items[0]
            node = MerkleNode(NodeType.LEAF, {'key': key, 'value': value})
            self.nodes[node.get_hash()] = node
            return node
        
        # 按当前nibble位置分组
        groups: Dict[int, List[Tuple[bytes, bytes]]] = {}
        for key, value in items:
            if len(key) * 2 > nibble_pos:
                # 获取nibble（半字节）
                byte_pos = nibble_pos // 2
                if nibble_pos % 2 == 0:
                    nibble = (key[byte_pos] >> 4) & 0xF
                else:
                    nibble = key[byte_pos] & 0xF
            else:
                nibble = 0
            
            if nibble not in groups:
                groups[nibble] = []
            groups[nibble].append((key, value))
        
        # 如果所有项都有相同的前缀，创建扩展节点
        if len(groups) == 1:
            nibble, group_items = next(iter(groups.items()))
            # 继续构建
            child = self._build_mpt_node(group_items, nibble_pos + 1)
            prefix = bytes([nibble])
            node = MerkleNode(NodeType.EXTENSION, {
                'prefix': prefix,
                'child_hash': child.get_hash()
            })
            self.nodes[node.get_hash()] = node
            return node
        
        # 创建分支节点
        children = [b''] * 16
        for nibble, group_items in groups.items():
            child = self._build_mpt_node(group_items, nibble_pos + 1)
            children[nibble] = child.get_hash()
        
        node = MerkleNode(NodeType.BRANCH, {'children': children})
        self.nodes[node.get_hash()] = node
        return node
    
    def get_proof(self, key: bytes) -> List[bytes]:
        """获取Merkle证明路径"""
        if key not in self.key_value_map or self.root is None:
            return []
        
        proof = []
        node = self.root
        
        # 将key转换为nibble序列
        key_nibbles = []
        for byte in key:
            key_nibbles.append((byte >> 4) & 0xF)
            key_nibbles.append(byte & 0xF)
        
        nibble_pos = 0
        while node is not None:
            if node.node_type == NodeType.LEAF:
                # 叶子节点，证明完成
                break
            
            elif node.node_type == NodeType.EXTENSION:
                # 扩展节点
                prefix = node.data.get('prefix', b'')
                prefix_nibbles = []
                for byte in prefix:
                    prefix_nibbles.append((byte >> 4) & 0xF)
                    prefix_nibbles.append(byte & 0xF)
                
                # 检查前缀匹配
                if key_nibbles[nibble_pos:nibble_pos+len(prefix_nibbles)] == prefix_nibbles:
                    nibble_pos += len(prefix_nibbles)
                    child_hash = node.data.get('child_hash')
                    node = self.nodes.get(child_hash) if child_hash else None
                else:
                    break
            
            elif node.node_type == NodeType.BRANCH:
                # 分支节点
                if nibble_pos < len(key_nibbles):
                    nibble = key_nibbles[nibble_pos]
                    nibble_pos += 1
                    
                    # 收集兄弟节点哈希作为证明
                    for i, child_hash in enumerate(node.data.get('children', [])):
                        if i != nibble and child_hash:
                            proof.append(child_hash)
                    
                    # 继续到子节点
                    children = node.data.get('children', [])
                    if nibble < len(children) and children[nibble]:
                        node = self.nodes.get(children[nibble])
                    else:
                        break
                else:
                    break
        
        return proof
    
    def update_root(self, new_root_hash: bytes) -> bool:
        """更新根节点（用于同步）"""
        if new_root_hash in self.nodes:
            self.root = self.nodes[new_root_hash]
            return True
        return False
    
    def save_to_disk(self):
        """保存Merkle树到磁盘（.mpt文件）"""
        try:
            with open(self.mpt_file, 'wb') as f:
                # 写入文件魔数
                f.write(FileMagic.MPT)  # 4 bytes
                
                # 写入版本号
                f.write(struct.pack('H', 1))  # 2 bytes
                
                # 写入根哈希
                root_hash = self.get_root_hash()
                f.write(struct.pack('I', len(root_hash)))  # 4 bytes
                f.write(root_hash)  # 32 bytes
                
                # 写入键值对数量
                f.write(struct.pack('Q', len(self.key_value_map)))  # 8 bytes
                
                # 写入所有键值对
                for key, value in self.key_value_map.items():
                    f.write(struct.pack('I', len(key)))  # 4 bytes
                    f.write(key)
                    f.write(struct.pack('I', len(value)))  # 4 bytes
                    f.write(value)
                
                # 写入节点数量
                f.write(struct.pack('Q', len(self.nodes)))  # 8 bytes
                
                # 写入所有节点（序列化）
                for node_hash, node in self.nodes.items():
                    f.write(struct.pack('I', len(node_hash)))  # 4 bytes
                    f.write(node_hash)  # 32 bytes
                    
                    # 序列化节点类型和数据
                    node_type_str = node.node_type.value.encode()
                    f.write(struct.pack('I', len(node_type_str)))  # 4 bytes
                    f.write(node_type_str)
                    
                    # 序列化节点数据（JSON）
                    node_data_json = json.dumps(node.data, default=lambda x: x.hex() if isinstance(x, bytes) else str(x)).encode()
                    f.write(struct.pack('I', len(node_data_json)))  # 4 bytes
                    f.write(node_data_json)
                
                # 写入checksum（先关闭文件，重新打开读取）
                current_pos = f.tell()
            
            # 重新打开文件读取数据并计算checksum
            with open(self.mpt_file, 'rb') as rf:
                data = rf.read()
            
            # 追加checksum
            with open(self.mpt_file, 'ab') as af:
                checksum = hashlib.sha256(data).digest()
                af.write(checksum)  # 32 bytes
        except Exception as e:
            import traceback
            print(f"保存Merkle树失败: {e}")
            traceback.print_exc()
    
    def _load_from_disk(self):
        """从磁盘加载Merkle树（.mpt文件）"""
        if not os.path.exists(self.mpt_file):
            return
        
        try:
            # 检查文件大小，如果文件太小可能是损坏的
            file_size = os.path.getsize(self.mpt_file)
            if file_size < 50:  # 至少需要文件头+一些数据
                print(f"⚠️ 警告: Merkle树文件太小 ({file_size} 字节)，可能已损坏，跳过加载")
                return
            with open(self.mpt_file, 'rb') as f:
                # 读取文件魔数
                magic = f.read(4)
                if magic != FileMagic.MPT:
                    return  # 无效文件
                
                # 读取版本号
                version = struct.unpack('H', f.read(2))[0]
                
                # 读取根哈希
                root_hash_len = struct.unpack('I', f.read(4))[0]
                root_hash = f.read(root_hash_len)
                
                # 读取键值对数量
                key_count = struct.unpack('Q', f.read(8))[0]
                
                # 读取所有键值对
                for _ in range(key_count):
                    key_len = struct.unpack('I', f.read(4))[0]
                    key = f.read(key_len)
                    value_len = struct.unpack('I', f.read(4))[0]
                    value = f.read(value_len)
                    self.key_value_map[key] = value
                
                # 读取节点数量
                node_count = struct.unpack('Q', f.read(8))[0]
                
                # 读取所有节点
                for _ in range(node_count):
                    node_hash_len = struct.unpack('I', f.read(4))[0]
                    node_hash = f.read(node_hash_len)
                    
                    node_type_len = struct.unpack('I', f.read(4))[0]
                    node_type_str = f.read(node_type_len).decode()
                    node_type = NodeType(node_type_str)
                    
                    node_data_len = struct.unpack('I', f.read(4))[0]
                    node_data_bytes = f.read(node_data_len)
                    # 安全解码：使用errors='replace'处理无效UTF-8字符
                    try:
                        node_data_json = node_data_bytes.decode('utf-8')
                    except UnicodeDecodeError:
                        # 如果UTF-8解码失败，尝试使用errors='replace'
                        node_data_json = node_data_bytes.decode('utf-8', errors='replace')
                    
                    # 安全解析JSON：添加错误处理
                    try:
                        node_data_raw = json.loads(node_data_json)
                    except json.JSONDecodeError as e:
                        # JSON解析失败，记录错误并跳过该节点
                        print(f"⚠️ 警告: Merkle树节点JSON解析失败 (位置 {f.tell() - node_data_len}, 长度 {node_data_len}): {e}")
                        print(f"   前100个字符: {node_data_json[:100] if len(node_data_json) > 100 else node_data_json}")
                        # 跳过该节点，继续加载其他节点
                        continue
                    
                    # 转换JSON数据：将字符串形式的bytes转换回bytes
                    node_data = {}
                    for k, v in node_data_raw.items():
                        if isinstance(v, str):
                            # 尝试从hex字符串恢复bytes
                            try:
                                # 检查是否是hex字符串（长度是偶数且只包含0-9a-f）
                                if len(v) % 2 == 0 and all(c in '0123456789abcdef' for c in v.lower()):
                                    node_data[k] = bytes.fromhex(v)
                                else:
                                    # 如果不是hex字符串，可能是普通字符串，编码为bytes
                                    node_data[k] = v.encode('utf-8')
                            except (ValueError, TypeError):
                                # 如果转换失败，编码为bytes
                                node_data[k] = v.encode('utf-8') if isinstance(v, str) else v
                        elif isinstance(v, list):
                            # 处理children列表
                            node_data[k] = []
                            for item in v:
                                if isinstance(item, str):
                                    try:
                                        if len(item) % 2 == 0 and all(c in '0123456789abcdef' for c in item.lower()):
                                            node_data[k].append(bytes.fromhex(item))
                                        else:
                                            node_data[k].append(item.encode('utf-8'))
                                    except (ValueError, TypeError):
                                        node_data[k].append(item.encode('utf-8') if isinstance(item, str) else item)
                                else:
                                    node_data[k].append(item)
                        else:
                            node_data[k] = v
                    
                    # 重建节点
                    node = MerkleNode(node_type, node_data)
                    self.nodes[node_hash] = node
                
                # 重建根节点
                if root_hash in self.nodes:
                    self.root = self.nodes[root_hash]
        except Exception as e:
            import traceback
            print(f"⚠️ 警告: 加载Merkle树失败: {e}")
            # 不打印完整traceback，只记录错误，允许继续运行
            # traceback.print_exc()
            # 清空已加载的数据，避免部分加载导致的不一致
            self.nodes.clear()
            self.key_value_map.clear()
            self.root = None

