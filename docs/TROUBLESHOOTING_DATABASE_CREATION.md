# 数据库创建问题排查指南

## 问题：database.amdb 文件未创建

### 可能的原因

#### 1. 导入路径不正确

**❌ 错误示例：**
```python
# 方式1: 直接导入（如果不在项目根目录）
from amdb import Database  # 可能找不到模块

# 方式2: 相对导入（如果不在src目录下）
from .database import Database  # 相对导入可能失败
```

**✅ 正确示例：**
```python
# 方式1: 从项目根目录导入（推荐）
from src.amdb import Database

# 方式2: 添加路径后导入
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))
from amdb import Database

# 方式3: 直接导入模块
from src.amdb.database import Database
```

#### 2. 没有使用 Database 类初始化

**❌ 错误示例：**
```python
# 只创建目录，不初始化Database
import os
os.makedirs('./data/my_db', exist_ok=True)
# 这样不会创建 database.amdb 文件！
```

**✅ 正确示例：**
```python
from src.amdb import Database

# 必须使用Database类初始化
db = Database(data_dir='./data/my_db')
# 会自动创建 database.amdb 文件和所有目录
```

#### 3. 使用了旧版本的代码

**问题：** 如果使用的是旧版本的代码，可能没有自动创建 `database.amdb` 的功能。

**解决方法：** 确保使用最新版本的代码（已修复）。

#### 4. 初始化时发生异常但被忽略

**问题：** `_save_metadata()` 可能失败，但异常被捕获并只打印警告。

**检查方法：**
```python
from src.amdb import Database
from pathlib import Path

try:
    db = Database(data_dir='./data/test')
    amdb_file = Path(db.data_dir) / 'database.amdb'
    if not amdb_file.exists():
        print('警告: database.amdb 文件未创建！')
        print('请检查控制台是否有错误信息')
    else:
        print(f'✓ database.amdb 文件已创建: {amdb_file.stat().st_size} 字节')
except Exception as e:
    print(f'错误: {e}')
    import traceback
    traceback.print_exc()
```

## 诊断步骤

### 步骤1: 检查导入

```python
# 测试导入
try:
    from src.amdb import Database
    print('✓ 导入成功')
except ImportError as e:
    print(f'✗ 导入失败: {e}')
    print('请检查Python路径和项目结构')
```

### 步骤2: 检查初始化

```python
from src.amdb import Database
from pathlib import Path
import os

# 创建数据库
test_dir = './data/diagnosis_test'
if os.path.exists(test_dir):
    import shutil
    shutil.rmtree(test_dir)

try:
    db = Database(data_dir=test_dir)
    print('✓ Database 初始化成功')
    
    # 检查文件
    amdb_file = Path(test_dir) / 'database.amdb'
    if amdb_file.exists():
        print(f'✓ database.amdb 文件存在: {amdb_file.stat().st_size} 字节')
    else:
        print('✗ database.amdb 文件不存在')
        print('可能的原因:')
        print('  1. _save_metadata() 失败（检查控制台错误）')
        print('  2. 权限问题（检查目录权限）')
        print('  3. 磁盘空间不足')
    
    # 检查目录
    required_dirs = ['versions', 'lsm', 'wal', 'bplus', 'merkle', 'indexes']
    for d in required_dirs:
        dir_path = Path(test_dir) / d
        if dir_path.exists():
            print(f'✓ {d}/ 目录存在')
        else:
            print(f'✗ {d}/ 目录不存在')
            
except Exception as e:
    print(f'✗ 初始化失败: {e}')
    import traceback
    traceback.print_exc()
```

### 步骤3: 检查权限和路径

```python
from pathlib import Path

data_dir = './data/test_db'
dir_path = Path(data_dir)

# 检查父目录权限
parent = dir_path.parent
print(f'父目录: {parent}')
print(f'父目录存在: {parent.exists()}')
print(f'父目录可写: {parent.exists() and os.access(parent, os.W_OK)}')

# 尝试创建目录
try:
    dir_path.mkdir(parents=True, exist_ok=True)
    print('✓ 目录创建成功')
    
    # 尝试创建文件
    test_file = dir_path / 'test.txt'
    test_file.write_text('test')
    test_file.unlink()
    print('✓ 文件写入测试成功')
except Exception as e:
    print(f'✗ 权限或路径问题: {e}')
```

## 常见错误和解决方案

### 错误1: ModuleNotFoundError

**错误信息：**
```
ModuleNotFoundError: No module named 'src.amdb'
```

**原因：** Python路径不正确

**解决方案：**
```python
# 方法1: 添加项目根目录到路径
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent  # 假设在src/amdb/目录下
sys.path.insert(0, str(project_root))

from src.amdb import Database

# 方法2: 使用绝对路径
import sys
sys.path.insert(0, '/path/to/AmDb')
from src.amdb import Database
```

### 错误2: database.amdb 文件未创建

**错误信息：**
```
警告: 创建数据库元数据文件失败: ...
```

**原因：** `_save_metadata()` 失败

**解决方案：**
1. 检查控制台错误信息
2. 检查目录权限
3. 检查磁盘空间
4. 确保使用最新版本的代码

### 错误3: 目录结构不完整

**问题：** 某些目录未创建

**原因：** 可能是旧版本代码

**解决方案：** 使用最新版本的代码（已修复）

## 验证代码

### 完整验证脚本

```python
#!/usr/bin/env python3
"""
数据库创建验证脚本
用于诊断数据库创建问题
"""

from src.amdb import Database
from pathlib import Path
import os
import shutil

def verify_database_creation(data_dir: str):
    """验证数据库创建"""
    print(f"\n{'='*60}")
    print(f"验证数据库创建: {data_dir}")
    print(f"{'='*60}\n")
    
    # 清理旧数据
    if os.path.exists(data_dir):
        shutil.rmtree(data_dir)
        print(f"✓ 已清理旧数据: {data_dir}")
    
    # 步骤1: 导入测试
    print("\n步骤1: 测试导入...")
    try:
        from src.amdb import Database
        print("✓ Database 类导入成功")
    except Exception as e:
        print(f"✗ 导入失败: {e}")
        return False
    
    # 步骤2: 初始化测试
    print("\n步骤2: 测试初始化...")
    try:
        db = Database(data_dir=data_dir)
        print("✓ Database 初始化成功")
        print(f"  数据目录: {db.data_dir}")
        print(f"  分片启用: {db.enable_sharding}")
    except Exception as e:
        print(f"✗ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 步骤3: 检查文件结构
    print("\n步骤3: 检查文件结构...")
    data_path = Path(data_dir)
    
    # 检查 database.amdb
    amdb_file = data_path / 'database.amdb'
    if amdb_file.exists():
        size = amdb_file.stat().st_size
        print(f"✓ database.amdb 存在 ({size} 字节)")
    else:
        print("✗ database.amdb 不存在")
        return False
    
    # 检查目录
    required_dirs = ['versions', 'lsm', 'wal', 'bplus', 'merkle', 'indexes']
    all_exist = True
    for d in required_dirs:
        dir_path = data_path / d
        if dir_path.exists():
            print(f"✓ {d}/ 目录存在")
        else:
            print(f"✗ {d}/ 目录不存在")
            all_exist = False
    
    if not all_exist:
        print("\n⚠ 警告: 部分目录未创建")
        return False
    
    # 步骤4: 测试读写
    print("\n步骤4: 测试读写...")
    try:
        # 写入
        db.put(b'test_key', b'test_value')
        print("✓ 写入成功")
        
        # 读取
        value = db.get(b'test_key')
        if value == b'test_value':
            print("✓ 读取成功")
        else:
            print(f"✗ 读取失败: 期望 b'test_value', 得到 {value}")
            return False
        
        # 持久化
        db.flush()
        print("✓ 持久化成功")
        
    except Exception as e:
        print(f"✗ 读写测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 步骤5: 验证数据文件
    print("\n步骤5: 验证数据文件...")
    versions_file = data_path / 'versions' / 'versions.ver'
    indexes_file = data_path / 'indexes' / 'indexes.idx'
    
    if versions_file.exists():
        print(f"✓ versions.ver 存在 ({versions_file.stat().st_size} 字节)")
    else:
        print("⚠ versions.ver 不存在（可能还未写入数据）")
    
    if indexes_file.exists():
        print(f"✓ indexes.idx 存在 ({indexes_file.stat().st_size} 字节)")
    else:
        print("⚠ indexes.idx 不存在（可能还未写入数据）")
    
    print(f"\n{'='*60}")
    print("✓ 数据库创建验证通过！")
    print(f"{'='*60}\n")
    
    return True

if __name__ == '__main__':
    test_dir = './data/verification_test'
    success = verify_database_creation(test_dir)
    
    # 清理
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    
    if not success:
        print("\n✗ 验证失败，请检查上述错误信息")
        exit(1)
    else:
        print("\n✓ 所有验证通过！")

