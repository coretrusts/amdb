#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AmDb GUI管理器启动脚本（调试模式）
带详细调试输出，帮助诊断数据加载问题
"""

import sys
import os

# 设置环境变量，确保输出不被缓冲
os.environ['PYTHONUNBUFFERED'] = '1'

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
os.environ['PYTHONPATH'] = project_root

print("=" * 70)
print("AmDb GUI 管理器（调试模式）")
print("=" * 70)
print()

# 检查数据目录
data_dirs = ['./data/sample_db', './data/test_show_commands', './data/perf_large_seq']
print("检查数据目录:")
for d in data_dirs:
    if os.path.exists(d):
        try:
            from src.amdb import Database
            db = Database(data_dir=d)
            import time
            time.sleep(0.2)
            keys = db.version_manager.get_all_keys()
            print(f"  ✓ {d}: {len(keys)} 条记录")
            if len(keys) > 0:
                # 测试读取
                value = db.get(keys[0])
                key_str = keys[0].decode('utf-8', errors='ignore')[:30]
                value_str = str(value)[:30]
                print(f"    测试读取: {key_str} = {value_str}")
        except Exception as e:
            print(f"  ✗ {d}: 错误 - {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"  - {d}: 不存在")

print()
print("启动GUI...")
print("提示:")
print("  1. 连接数据库后，请查看控制台的[GUI调试]信息")
print("  2. 如果看不到数据，请点击'刷新'按钮")
print("  3. 所有调试信息都会输出到控制台")
print("=" * 70)
print()

# 启动GUI
try:
    from src.amdb.gui_manager import main
    main()
except Exception as e:
    print(f"GUI启动失败: {e}")
    import traceback
    traceback.print_exc()
    input("按Enter键退出...")

