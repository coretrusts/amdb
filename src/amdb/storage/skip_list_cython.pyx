"""
跳表Cython优化版本
使用Cython优化核心逻辑，预期提升8-12倍性能
目标：超越PolarDB的20.55亿tpmC性能
"""

# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True
# cython: infer_types=True

cimport cython
from libc.stdlib cimport malloc, free, realloc
from libc.string cimport memcpy, memcmp
import time
import random

cdef struct SkipListNode:
    unsigned char* key
    size_t key_len
    unsigned char* value
    size_t value_len
    int version
    double timestamp
    int level
    SkipListNode** forward

cdef class SkipListCython:
    """
    Cython优化的跳表实现
    预期性能提升：8-12倍
    目标：支持超高并发写入，达到百万级ops/s
    """
    cdef SkipListNode* header
    cdef int max_level
    cdef int level
    cdef size_t max_size
    cdef size_t size
    cdef SkipListNode** update
    
    def __cinit__(self, int max_level=16, size_t max_size=10485760):
        self.max_level = max_level
        self.level = 1
        self.max_size = max_size
        self.size = 0
        
        # 分配头节点
        self.header = <SkipListNode*>malloc(sizeof(SkipListNode))
        self.header.key = NULL
        self.header.key_len = 0
        self.header.value = NULL
        self.header.value_len = 0
        self.header.version = 0
        self.header.timestamp = 0.0
        self.header.level = max_level
        self.header.forward = <SkipListNode**>malloc(max_level * sizeof(SkipListNode*))
        cdef int i
        for i in range(max_level):
            self.header.forward[i] = NULL
        
        # 分配update数组
        self.update = <SkipListNode**>malloc(max_level * sizeof(SkipListNode*))
    
    def __dealloc__(self):
        # 清理所有节点
        cdef SkipListNode* current = self.header.forward[0]
        cdef SkipListNode* next_node
        while current != NULL:
            next_node = current.forward[0]
            if current.key != NULL:
                free(current.key)
            if current.value != NULL:
                free(current.value)
            if current.forward != NULL:
                free(current.forward)
            free(current)
            current = next_node
        
        # 清理头节点
        if self.header != NULL:
            if self.header.forward != NULL:
                free(self.header.forward)
            free(self.header)
        
        # 清理update数组
        if self.update != NULL:
            free(self.update)
    
    cdef inline int _random_level(self):
        """生成随机层级（优化：使用内联函数）"""
        cdef int level = 1
        cdef double r
        while random.random() < 0.5 and level < self.max_level:
            level += 1
        return level
    
    cpdef bint put(self, bytes key, bytes value, int version, double timestamp=0.0):
        """单个插入（兼容接口）"""
        if timestamp == 0.0:
            timestamp = time.time()
        result = self.put_batch([(key, value, version)])
        return result > 0
    
    @cython.boundscheck(False)
    @cython.wraparound(False)
    cpdef int put_batch(self, list items):
        """
        批量插入（Cython优化版本，极致性能）
        优化策略：
        1. 减少Python对象访问（使用局部变量缓存）
        2. 预计算所有节点层级
        3. 优化内存比较（使用memcmp）
        4. 减少函数调用开销
        """
        cdef int success_count = 0
        cdef int items_len = len(items)
        if items_len == 0:
            return 0
        
        cdef int idx, i
        cdef int found
        cdef bytes key_bytes, value_bytes
        cdef unsigned char* key_ptr
        cdef unsigned char* value_ptr
        cdef size_t key_len, value_len, entry_size
        cdef int version
        cdef double timestamp = time.time()  # 只计算一次时间戳
        
        # 预先计算所有节点层级（减少函数调用）
        cdef int* node_levels = <int*>malloc(items_len * sizeof(int))
        cdef int max_node_level = 1
        cdef int node_level
        
        # 预提取所有数据到C数组（减少Python list访问）
        cdef unsigned char** key_ptrs = <unsigned char**>malloc(items_len * sizeof(unsigned char*))
        cdef unsigned char** value_ptrs = <unsigned char**>malloc(items_len * sizeof(unsigned char*))
        cdef size_t* key_lens = <size_t*>malloc(items_len * sizeof(size_t))
        cdef size_t* value_lens = <size_t*>malloc(items_len * sizeof(size_t))
        cdef int* versions = <int*>malloc(items_len * sizeof(int))
        
        # 批量提取数据（优化：减少Python对象访问）
        for idx in range(items_len):
            key_bytes, value_bytes, version = items[idx]  # Python解包（必须）
            key_ptr = <unsigned char*>key_bytes
            value_ptr = <unsigned char*>value_bytes
            key_len = len(key_bytes)
            value_len = len(value_bytes)
            
            key_ptrs[idx] = key_ptr
            value_ptrs[idx] = value_ptr
            key_lens[idx] = key_len
            value_lens[idx] = value_len
            versions[idx] = version
            
            # 计算节点层级
            node_level = self._random_level()
            node_levels[idx] = node_level
            if node_level > max_node_level:
                max_node_level = node_level
        
        # 扩展层级
        if max_node_level > self.level:
            for i in range(self.level, max_node_level):
                self.update[i] = self.header
            self.level = max_node_level
        
        # 批量插入（完全C级操作）
        cdef SkipListNode* current
        cdef SkipListNode* new_node
        cdef SkipListNode* next_node
        cdef int cmp_result
        cdef size_t old_size, new_size
        cdef size_t min_len
        
        for idx in range(items_len):
            key_ptr = key_ptrs[idx]
            value_ptr = value_ptrs[idx]
            key_len = key_lens[idx]
            value_len = value_lens[idx]
            version = versions[idx]
            entry_size = key_len + value_len + 16
            
            if self.size + entry_size > self.max_size:
                break
            
            # 查找插入位置（优化：减少比较次数）
            current = self.header
            for i in range(self.level - 1, -1, -1):
                while current.forward[i] != NULL:
                    next_node = current.forward[i]
                    # 优化比较：先比较长度，再比较内容
                    if next_node.key_len == key_len:
                        cmp_result = memcmp(next_node.key, key_ptr, key_len)
                    else:
                        min_len = next_node.key_len if next_node.key_len < key_len else key_len
                        cmp_result = memcmp(next_node.key, key_ptr, min_len)
                        if cmp_result == 0:
                            cmp_result = 1 if next_node.key_len > key_len else -1
                    
                    if cmp_result < 0:
                        current = next_node
                    else:
                        break
                self.update[i] = current
            
            current = current.forward[0]
            
            # 检查key是否已存在（优化：快速路径）
            found = 0
            if current != NULL and current.key_len == key_len:
                if memcmp(current.key, key_ptr, key_len) == 0:
                    found = 1
            
            if found:
                # 更新现有节点
                old_size = current.value_len + 16
                new_size = value_len + 16
                self.size = self.size - old_size + new_size
                
                if current.value_len != value_len:
                    current.value = <unsigned char*>realloc(current.value, value_len)
                memcpy(current.value, value_ptr, value_len)
                current.value_len = value_len
                current.version = version
                current.timestamp = timestamp
                success_count += 1
                continue
            
            # 创建新节点
            node_level = node_levels[idx]
            new_node = <SkipListNode*>malloc(sizeof(SkipListNode))
            new_node.key = <unsigned char*>malloc(key_len)
            new_node.value = <unsigned char*>malloc(value_len)
            memcpy(new_node.key, key_ptr, key_len)
            memcpy(new_node.value, value_ptr, value_len)
            new_node.key_len = key_len
            new_node.value_len = value_len
            new_node.version = version
            new_node.timestamp = timestamp
            new_node.level = node_level
            new_node.forward = <SkipListNode**>malloc(node_level * sizeof(SkipListNode*))
            
            # 插入节点
            for i in range(node_level):
                new_node.forward[i] = self.update[i].forward[i]
                self.update[i].forward[i] = new_node
            
            self.size += entry_size
            success_count += 1
        
        # 清理
        free(node_levels)
        free(key_ptrs)
        free(value_ptrs)
        free(key_lens)
        free(value_lens)
        free(versions)
        
        return success_count
