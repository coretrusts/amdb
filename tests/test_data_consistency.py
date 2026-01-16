#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据一致性：
1. 连接数据库后，新数据写入是否能及时读取
2. 数据文件删除后，是否能及时获得最新状态
3. 数据读写状态是否正常
"""

import os
import sys
import shutil
import time
import tempfile
from pathlib import Path

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.amdb.database import Database


def test_new_data_immediately_readable():
    """测试1: 新数据写入后是否能立即读取"""
    print("\n" + "="*70)
    print("测试1: 新数据写入后是否能立即读取")
    print("="*70)
    
    # 创建临时数据库
    temp_dir = tempfile.mkdtemp(prefix="amdb_test_")
    print(f"创建临时数据库: {temp_dir}")
    
    try:
        # 连接数据库（初始为空）
        db = Database(data_dir=temp_dir)
        print("✓ 数据库连接成功")
        
        # 检查初始状态
        stats = db.get_stats()
        initial_keys = stats.get('total_keys', 0)
        print(f"初始键数量: {initial_keys}")
        assert initial_keys == 0, "初始数据库应该为空"
        
        # 写入新数据
        test_key = b"test:001"
        test_value = b"test_value_001"
        print(f"\n写入数据: key={test_key}, value={test_value}")
        success, merkle_root = db.put(test_key, test_value)
        assert success, "写入应该成功"
        print(f"✓ 写入成功，Merkle根: {merkle_root.hex()[:16]}...")
        
        # 立即读取（不flush）
        print("\n立即读取数据（不flush）...")
        value = db.get(test_key)
        assert value is not None, "应该能立即读取到新写入的数据"
        assert value == test_value, f"读取的值应该等于写入的值: {value} != {test_value}"
        print(f"✓ 立即读取成功: {value}")
        
        # 检查统计信息
        stats = db.get_stats()
        new_keys = stats.get('total_keys', 0)
        print(f"写入后键数量: {new_keys}")
        assert new_keys == 1, f"键数量应该是1，实际是{new_keys}"
        
        # 再次写入多条数据
        print("\n批量写入多条数据...")
        for i in range(2, 6):
            key = f"test:{i:03d}".encode()
            value = f"test_value_{i:03d}".encode()
            db.put(key, value)
        
        # 立即读取所有数据
        print("立即读取所有数据...")
        for i in range(1, 6):
            key = f"test:{i:03d}".encode()
            value = db.get(key)
            assert value is not None, f"应该能读取到key={key}"
            expected = f"test_value_{i:03d}".encode()
            assert value == expected, f"值不匹配: {value} != {expected}"
            print(f"  ✓ {key.decode()}: {value.decode()}")
        
        stats = db.get_stats()
        final_keys = stats.get('total_keys', 0)
        assert final_keys == 5, f"最终键数量应该是5，实际是{final_keys}"
        print(f"\n✓ 测试1通过: 新数据写入后能立即读取，共{final_keys}条记录")
        
    finally:
        # 清理
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"\n清理临时目录: {temp_dir}")


def test_file_deletion_detection():
    """测试2: 数据文件删除后是否能及时检测到"""
    print("\n" + "="*70)
    print("测试2: 数据文件删除后是否能及时检测到")
    print("="*70)
    
    # 创建临时数据库
    temp_dir = tempfile.mkdtemp(prefix="amdb_test_")
    print(f"创建临时数据库: {temp_dir}")
    
    try:
        # 连接数据库并写入数据
        db = Database(data_dir=temp_dir)
        print("✓ 数据库连接成功")
        
        # 写入一些数据
        print("\n写入测试数据...")
        for i in range(1, 6):
            key = f"data:{i:03d}".encode()
            value = f"value_{i:03d}".encode()
            db.put(key, value)
            print(f"  ✓ 写入: {key.decode()}")
        
        # 确保数据持久化
        db.flush()
        print("✓ 数据已持久化到磁盘")
        
        # 验证数据存在
        stats = db.get_stats()
        initial_keys = stats.get('total_keys', 0)
        assert initial_keys == 5, f"应该有5条记录，实际是{initial_keys}"
        print(f"✓ 验证: 数据库包含{initial_keys}条记录")
        
        # 验证文件存在
        version_file = Path(temp_dir) / "versions" / "versions.ver"
        assert version_file.exists(), "版本文件应该存在"
        print(f"✓ 验证: 版本文件存在: {version_file}")
        
        # 检查文件状态
        files_exist = db.check_files_exist()
        assert files_exist, "文件应该存在"
        print(f"✓ 验证: check_files_exist() = {files_exist}")
        
        # 读取数据验证
        print("\n读取数据验证...")
        for i in range(1, 6):
            key = f"data:{i:03d}".encode()
            value = db.get(key)
            assert value is not None, f"应该能读取到key={key}"
            print(f"  ✓ {key.decode()}: {value.decode()}")
        
        # 删除版本文件（模拟文件被删除）
        print(f"\n删除版本文件: {version_file}")
        version_file.unlink()
        assert not version_file.exists(), "版本文件应该已被删除"
        
        # 检查文件状态（应该检测到文件不存在）
        files_exist = db.check_files_exist()
        assert not files_exist, "应该检测到文件不存在"
        print(f"✓ 验证: check_files_exist() = {files_exist} (文件已删除)")
        
        # 重新加载数据（应该清空缓存）
        print("\n重新加载数据...")
        db.reload_if_files_changed()
        
        # 验证数据已被清空
        stats = db.get_stats()
        after_reload_keys = stats.get('total_keys', 0)
        print(f"重新加载后键数量: {after_reload_keys}")
        assert after_reload_keys == 0, f"重新加载后应该没有数据，实际是{after_reload_keys}"
        
        # 尝试读取数据（应该返回None）
        print("\n尝试读取已删除的数据...")
        for i in range(1, 6):
            key = f"data:{i:03d}".encode()
            value = db.get(key)
            assert value is None, f"应该读取不到key={key}（文件已删除）"
            print(f"  ✓ {key.decode()}: None (已清空)")
        
        print(f"\n✓ 测试2通过: 文件删除后能及时检测到并清空缓存")
        
    finally:
        # 清理
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"\n清理临时目录: {temp_dir}")


def test_file_cleared_detection():
    """测试3: 数据文件被清空后是否能及时检测到"""
    print("\n" + "="*70)
    print("测试3: 数据文件被清空后是否能及时检测到")
    print("="*70)
    
    # 创建临时数据库
    temp_dir = tempfile.mkdtemp(prefix="amdb_test_")
    print(f"创建临时数据库: {temp_dir}")
    
    try:
        # 连接数据库并写入数据
        db = Database(data_dir=temp_dir)
        print("✓ 数据库连接成功")
        
        # 写入数据
        print("\n写入测试数据...")
        for i in range(1, 4):
            key = f"item:{i:03d}".encode()
            value = f"content_{i:03d}".encode()
            db.put(key, value)
        
        db.flush()
        print("✓ 数据已持久化")
        
        # 验证文件存在且有内容
        version_file = Path(temp_dir) / "versions" / "versions.ver"
        assert version_file.exists(), "版本文件应该存在"
        file_size = version_file.stat().st_size
        assert file_size >= 14, f"文件大小应该>=14字节，实际是{file_size}"
        print(f"✓ 版本文件大小: {file_size} 字节")
        
        # 清空文件（模拟文件被清空）
        print(f"\n清空版本文件...")
        with open(version_file, 'wb') as f:
            f.write(b'')  # 清空文件
        file_size = version_file.stat().st_size
        assert file_size == 0, f"文件应该被清空，实际大小是{file_size}"
        print(f"✓ 文件已清空，大小: {file_size} 字节")
        
        # 检查文件状态（应该检测到文件无效）
        files_exist = db.check_files_exist()
        assert not files_exist, "应该检测到文件无效（太小）"
        print(f"✓ 验证: check_files_exist() = {files_exist} (文件已清空)")
        
        # 重新加载
        print("\n重新加载数据...")
        db.reload_if_files_changed()
        
        # 验证数据已被清空
        stats = db.get_stats()
        after_reload_keys = stats.get('total_keys', 0)
        assert after_reload_keys == 0, f"重新加载后应该没有数据，实际是{after_reload_keys}"
        print(f"✓ 重新加载后键数量: {after_reload_keys}")
        
        print(f"\n✓ 测试3通过: 文件清空后能及时检测到并清空缓存")
        
    finally:
        # 清理
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"\n清理临时目录: {temp_dir}")


def test_read_write_consistency():
    """测试4: 数据读写一致性"""
    print("\n" + "="*70)
    print("测试4: 数据读写一致性")
    print("="*70)
    
    # 创建临时数据库
    temp_dir = tempfile.mkdtemp(prefix="amdb_test_")
    print(f"创建临时数据库: {temp_dir}")
    
    try:
        db = Database(data_dir=temp_dir)
        print("✓ 数据库连接成功")
        
        # 测试写入-读取循环
        print("\n测试写入-读取循环...")
        test_cases = [
            (b"key1", b"value1"),
            (b"key2", b"value2"),
            (b"key3", b"value3"),
        ]
        
        for key, value in test_cases:
            # 写入
            success, _ = db.put(key, value)
            assert success, f"写入应该成功: {key}"
            
            # 立即读取
            read_value = db.get(key)
            assert read_value is not None, f"应该能读取到: {key}"
            assert read_value == value, f"值应该匹配: {read_value} != {value}"
            print(f"  ✓ {key.decode()}: {value.decode()} -> {read_value.decode()}")
        
        # 测试更新
        print("\n测试更新数据...")
        db.put(b"key1", b"updated_value1")
        updated = db.get(b"key1")
        assert updated == b"updated_value1", f"更新后的值应该匹配: {updated}"
        print(f"  ✓ key1: updated_value1 -> {updated.decode()}")
        
        # 测试删除（标记删除）
        print("\n测试删除数据...")
        db.delete(b"key2")
        deleted = db.get(b"key2")
        assert deleted is None, f"删除后应该返回None: {deleted}"
        print(f"  ✓ key2: 已删除 -> None")
        
        # 验证最终状态
        stats = db.get_stats()
        final_keys = stats.get('total_keys', 0)
        print(f"\n最终键数量: {final_keys}")
        # key1存在，key2已删除，key3存在，所以应该是2个有效键
        assert final_keys == 2, f"最终应该有2个有效键，实际是{final_keys}"
        
        print(f"\n✓ 测试4通过: 数据读写一致性正常")
        
    finally:
        # 清理
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"\n清理临时目录: {temp_dir}")


def main():
    """运行所有测试"""
    print("\n" + "="*70)
    print("AmDb 数据一致性测试")
    print("="*70)
    
    tests = [
        ("新数据写入后立即读取", test_new_data_immediately_readable),
        ("文件删除后状态检测", test_file_deletion_detection),
        ("文件清空后状态检测", test_file_cleared_detection),
        ("数据读写一致性", test_read_write_consistency),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
            print(f"\n✅ {test_name}: 通过")
        except AssertionError as e:
            failed += 1
            print(f"\n❌ {test_name}: 失败 - {e}")
            import traceback
            traceback.print_exc()
        except Exception as e:
            failed += 1
            print(f"\n❌ {test_name}: 异常 - {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*70)
    print("测试结果汇总")
    print("="*70)
    print(f"总计: {len(tests)} 个测试")
    print(f"通过: {passed} 个")
    print(f"失败: {failed} 个")
    print("="*70)
    
    if failed == 0:
        print("\n✅ 所有测试通过！")
        return 0
    else:
        print(f"\n❌ 有 {failed} 个测试失败")
        return 1


if __name__ == "__main__":
    exit(main())

