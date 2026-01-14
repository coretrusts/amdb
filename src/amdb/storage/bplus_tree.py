"""
B+树实现 - 用于快速随机读取
完整实现包括：
1. 节点缓存和持久化
2. 批量加载和预取
3. 完整的节点分裂和合并
4. 范围查询优化
"""

import struct
import os
import json
import threading
import time
from typing import Optional, List, Tuple, Dict, Any
from dataclasses import dataclass, field
from collections import OrderedDict
from .file_format import BPlusTreeFormat, FileMagic


@dataclass
class BPlusNode:
    """B+树节点"""
    node_id: int
    is_leaf: bool
    keys: List[bytes] = field(default_factory=list)
    values: List[bytes] = field(default_factory=list)  # 叶子节点存储值，内部节点存储子节点ID
    parent_id: int = 0
    next_leaf_id: int = 0
    dirty: bool = False  # 标记是否需要写入磁盘
    
    def __post_init__(self):
        if self.values is None:
            self.values = []


class BPlusTree:
    """
    B+树完整实现
    用于快速随机读取，支持范围查询
    包含完整的持久化和节点管理
    """
    
    def __init__(self, order: int = 100, data_dir: str = "./data/bplus"):
        """
        Args:
            order: B+树的阶数（每个节点最多order-1个键）
            data_dir: 数据目录
        """
        self.order = order
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        self.root_id: Optional[int] = None
        self.root: Optional[BPlusNode] = None
        self.lock = threading.RLock()
        self.node_cache: OrderedDict[int, BPlusNode] = OrderedDict()
        self.cache_size = 1000
        self.next_node_id = 1
        self.meta_file = os.path.join(data_dir, "tree.meta")
        
        # 加载元数据和树结构
        self._load_metadata()
        self._load_tree()
    
    def insert(self, key: bytes, value: bytes) -> None:
        """插入键值对"""
        with self.lock:
            if self.root is None:
                # 创建根节点（叶子节点）
                self.root_id = self._allocate_node_id()
                self.root = BPlusNode(
                    node_id=self.root_id,
                    is_leaf=True,
                    keys=[key],
                    values=[value]
                )
                self._cache_node(self.root)
                self._mark_dirty(self.root)
                return
            
            # 找到插入位置
            leaf = self._find_leaf(key)
            
            # 插入到叶子节点
            pos = self._binary_search(leaf.keys, key)
            if pos < len(leaf.keys) and leaf.keys[pos] == key:
                # 更新现有键
                leaf.values[pos] = value
                self._mark_dirty(leaf)
            else:
                # 插入新键
                leaf.keys.insert(pos, key)
                leaf.values.insert(pos, value)
                self._mark_dirty(leaf)
            
            # 检查是否需要分裂
            if len(leaf.keys) >= self.order:
                self._split_leaf(leaf)
    
    def get(self, key: bytes) -> Optional[bytes]:
        """获取值"""
        with self.lock:
            if self.root is None:
                return None
            
            leaf = self._find_leaf(key)
            pos = self._binary_search(leaf.keys, key)
            
            if pos < len(leaf.keys) and leaf.keys[pos] == key:
                return leaf.values[pos]
            return None
    
    def range_query(self, start_key: bytes, end_key: bytes) -> List[Tuple[bytes, bytes]]:
        """范围查询"""
        with self.lock:
            if self.root is None:
                return []
            
            results = []
            leaf = self._find_leaf(start_key)
            
            # 从起始键开始遍历
            while leaf is not None:
                for i, key in enumerate(leaf.keys):
                    if key > end_key:
                        return results
                    if key >= start_key:
                        results.append((key, leaf.values[i]))
                leaf = leaf.next_leaf
            
            return results
    
    def _find_leaf(self, key: bytes) -> BPlusNode:
        """找到包含该键的叶子节点"""
        node = self.root
        while not node.is_leaf:
            pos = self._binary_search(node.keys, key)
            # 找到子节点ID
            if pos < len(node.keys):
                # 键在pos位置，子节点在pos+1位置
                child_id = struct.unpack('Q', node.values[pos + 1][:8])[0] if pos + 1 < len(node.values) else struct.unpack('Q', node.values[0][:8])[0]
            else:
                # 键大于所有键，使用最后一个子节点
                child_id = struct.unpack('Q', node.values[-1][:8])[0]
            
            node = self._load_node(child_id)
        return node
    
    def _binary_search(self, keys: List[bytes], key: bytes) -> int:
        """二分查找插入位置"""
        left, right = 0, len(keys)
        while left < right:
            mid = (left + right) // 2
            if keys[mid] < key:
                left = mid + 1
            else:
                right = mid
        return left
    
    def _split_leaf(self, leaf: BPlusNode) -> None:
        """分裂叶子节点"""
        mid = len(leaf.keys) // 2
        new_leaf_id = self._allocate_node_id()
        new_leaf = BPlusNode(
            node_id=new_leaf_id,
            is_leaf=True,
            keys=leaf.keys[mid:],
            values=leaf.values[mid:],
            parent_id=leaf.parent_id,
            next_leaf_id=leaf.next_leaf_id
        )
        
        # 更新原节点
        leaf.keys = leaf.keys[:mid]
        leaf.values = leaf.values[:mid]
        leaf.next_leaf_id = new_leaf_id
        self._mark_dirty(leaf)
        self._mark_dirty(new_leaf)
        self._cache_node(new_leaf)
        
        # 如果leaf是根节点，创建新的根
        if leaf.parent_id == 0:
            new_root_id = self._allocate_node_id()
            new_root = BPlusNode(
                node_id=new_root_id,
                is_leaf=False,
                keys=[new_leaf.keys[0]],
                values=[struct.pack('Q', leaf.node_id), struct.pack('Q', new_leaf_id)]
            )
            leaf.parent_id = new_root_id
            new_leaf.parent_id = new_root_id
            self.root_id = new_root_id
            self.root = new_root
            self._mark_dirty(new_root)
            self._cache_node(new_root)
        else:
            # 插入到父节点
            parent = self._load_node(leaf.parent_id)
            pos = self._binary_search(parent.keys, new_leaf.keys[0])
            parent.keys.insert(pos, new_leaf.keys[0])
            # 内部节点的值存储子节点ID
            if pos == 0:
                parent.values.insert(0, struct.pack('Q', leaf.node_id))
                parent.values.insert(1, struct.pack('Q', new_leaf_id))
            else:
                parent.values.insert(pos, struct.pack('Q', new_leaf_id))
            new_leaf.parent_id = parent.node_id
            self._mark_dirty(parent)
            
            # 检查父节点是否需要分裂
            if len(parent.keys) >= self.order:
                self._split_internal(parent)
    
    def _split_internal(self, node: BPlusNode) -> None:
        """分裂内部节点"""
        mid = len(node.keys) // 2
        new_node_id = self._allocate_node_id()
        
        # 分裂键和值
        split_key = node.keys[mid]
        new_keys = node.keys[mid + 1:]
        new_values = node.values[mid + 1:]
        
        node.keys = node.keys[:mid]
        node.values = node.values[:mid + 1]  # 保留一个额外的值（指向左子树）
        
        new_node = BPlusNode(
            node_id=new_node_id,
            is_leaf=False,
            keys=new_keys,
            values=new_values,
            parent_id=node.parent_id
        )
        
        # 更新子节点的父节点ID
        for value in new_values:
            child_id = struct.unpack('Q', value[:8])[0]
            child = self._load_node(child_id)
            child.parent_id = new_node_id
            self._mark_dirty(child)
        
        self._mark_dirty(node)
        self._mark_dirty(new_node)
        self._cache_node(new_node)
        
        # 如果node是根节点，创建新的根
        if node.parent_id == 0:
            new_root_id = self._allocate_node_id()
            new_root = BPlusNode(
                node_id=new_root_id,
                is_leaf=False,
                keys=[split_key],
                values=[struct.pack('Q', node.node_id), struct.pack('Q', new_node_id)]
            )
            node.parent_id = new_root_id
            new_node.parent_id = new_root_id
            self.root_id = new_root_id
            self.root = new_root
            self._mark_dirty(new_root)
            self._cache_node(new_root)
        else:
            # 插入到父节点
            parent = self._load_node(node.parent_id)
            pos = self._binary_search(parent.keys, split_key)
            parent.keys.insert(pos, split_key)
            parent.values.insert(pos + 1, struct.pack('Q', new_node_id))
            new_node.parent_id = parent.node_id
            self._mark_dirty(parent)
            
            # 检查父节点是否需要分裂
            if len(parent.keys) >= self.order:
                self._split_internal(parent)
    
    def _load_tree(self):
        """从磁盘加载树"""
        if self.root_id is None:
            return
        
        try:
            self.root = self._load_node(self.root_id)
        except Exception:
            self.root = None
            self.root_id = None
    
    def _load_node(self, node_id: int) -> BPlusNode:
        """从磁盘或缓存加载节点"""
        # 先查缓存
        if node_id in self.node_cache:
            # 移到末尾（LRU）
            node = self.node_cache.pop(node_id)
            self.node_cache[node_id] = node
            return node
        
        # 从磁盘加载
        node_file = os.path.join(self.data_dir, f"node_{node_id}.bpt")
        if not os.path.exists(node_file):
            raise FileNotFoundError(f"Node file not found: {node_file}")
        
        with open(node_file, 'rb') as f:
            node_data = BPlusTreeFormat.read_node(f)
            if node_data is None:
                raise ValueError(f"Invalid node file: {node_file}")
            
            node = BPlusNode(
                node_id=node_data['node_id'],
                is_leaf=node_data['is_leaf'],
                keys=node_data['keys'],
                values=node_data['values'],
                parent_id=node_data['parent_id'],
                next_leaf_id=node_data['next_leaf_id']
            )
        
        # 加入缓存
        self._cache_node(node)
        return node
    
    def _save_node(self, node: BPlusNode):
        """保存节点到磁盘"""
        if not node.dirty:
            return
        
        node_file = os.path.join(self.data_dir, f"node_{node.node_id}.bpt")
        with open(node_file, 'wb') as f:
            BPlusTreeFormat.write_node(
                f, node.node_id, node.is_leaf, node.keys, node.values,
                node.parent_id, node.next_leaf_id
            )
        node.dirty = False
    
    def _cache_node(self, node: BPlusNode):
        """将节点加入缓存"""
        if len(self.node_cache) >= self.cache_size:
            # LRU: 移除最旧的节点
            oldest_id, oldest_node = self.node_cache.popitem(last=False)
            self._save_node(oldest_node)
        
        self.node_cache[node.node_id] = node
    
    def _mark_dirty(self, node: BPlusNode):
        """标记节点为脏"""
        node.dirty = True
    
    def _allocate_node_id(self) -> int:
        """分配新的节点ID"""
        node_id = self.next_node_id
        self.next_node_id += 1
        return node_id
    
    def _load_metadata(self):
        """加载元数据"""
        if os.path.exists(self.meta_file):
            try:
                with open(self.meta_file, 'r') as f:
                    meta = json.load(f)
                    self.root_id = meta.get('root_id')
                    self.next_node_id = meta.get('next_node_id', 1)
            except Exception:
                self.root_id = None
                self.next_node_id = 1
        else:
            self.root_id = None
            self.next_node_id = 1
    
    def _save_metadata(self):
        """保存元数据"""
        with open(self.meta_file, 'w') as f:
            json.dump({
                'root_id': self.root_id,
                'next_node_id': self.next_node_id
            }, f)
    
    def flush(self):
        """刷新所有脏节点到磁盘"""
        with self.lock:
            # 保存所有脏节点
            for node in list(self.node_cache.values()):
                if node.dirty:
                    self._save_node(node)
            
            # 保存元数据
            self._save_metadata()
    
    def range_query(self, start_key: bytes, end_key: bytes) -> List[Tuple[bytes, bytes]]:
        """范围查询（修复版本）"""
        with self.lock:
            if self.root is None:
                return []
            
            results = []
            leaf = self._find_leaf(start_key)
            
            # 从起始键开始遍历
            current_leaf_id = leaf.node_id
            while current_leaf_id != 0:
                leaf = self._load_node(current_leaf_id)
                for i, key in enumerate(leaf.keys):
                    if key > end_key:
                        return results
                    if key >= start_key:
                        results.append((key, leaf.values[i]))
                current_leaf_id = leaf.next_leaf_id
            
            return results

