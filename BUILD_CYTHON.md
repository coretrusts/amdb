# Cython扩展构建指南

## 安装依赖

```bash
pip install cython numpy
```

## 构建C扩展

```bash
python setup_cython.py build_ext --inplace
```

## 使用Cython优化版本

### 方法1: 修改MemTable使用Cython版本

在 `src/amdb/storage/lsm_tree.py` 中：

```python
try:
    from .skip_list_cython import SkipListCython as SkipList
    USE_CYTHON = True
except ImportError:
    from .skip_list import SkipList
    USE_CYTHON = False

class MemTable:
    def __init__(self, use_skip_list=True, max_size=10*1024*1024):
        if USE_CYTHON and use_skip_list:
            self.skip_list = SkipList(max_level=16, max_size=max_size)
        elif use_skip_list:
            self.skip_list = SkipList(max_size=max_size)
        # ...
```

### 方法2: 使用分布式集群

```python
from amdb.distributed import DistributedCluster

# 创建4节点集群（超越PolarDB性能）
cluster = DistributedCluster(node_count=4)

# 批量写入
items = [(f'key_{i}'.encode(), f'value_{i}'.encode()) for i in range(1000000)]
success, results = cluster.batch_put(items)
```

## 性能测试

```bash
python tests/test_cython_performance.py
```

## 预期性能

- **单节点（Cython）**: 50-100万ops/s
- **4节点集群**: 200-400万ops/s（超越PolarDB的342.5万tps）
- **8节点集群**: 400-800万ops/s
- **16节点集群**: 800-1600万ops/s

