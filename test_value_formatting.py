# -*- coding: utf-8 -*-
"""
测试不同类型value的渲染方式
演示JSON、XML、Binary、Text等格式的格式化显示
"""

import sys
import json
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.amdb import Database
from src.amdb.value_formatter import ValueFormatter

def create_test_data():
    """创建测试数据库并写入不同类型的数据"""
    
    # 创建测试数据库
    db_path = './data/test_formatting'
    db = Database(data_dir=db_path)
    
    print("=" * 80)
    print("创建测试数据")
    print("=" * 80)
    print()
    
    # 1. JSON格式数据
    print("1. 写入JSON格式数据...")
    json_data = {
        "name": "测试用户",
        "age": 30,
        "email": "test@example.com",
        "address": {
            "city": "北京",
            "district": "朝阳区",
            "street": "测试街道123号"
        },
        "tags": ["开发", "测试", "数据库"],
        "active": True,
        "balance": 1234.56
    }
    db.put(b'user:json:001', json.dumps(json_data, ensure_ascii=False).encode('utf-8'))
    print("   ✓ JSON数据已写入: user:json:001")
    
    # 2. XML格式数据
    print("2. 写入XML格式数据...")
    xml_data = '''<?xml version="1.0" encoding="UTF-8"?>
<user>
    <id>001</id>
    <name>测试用户</name>
    <age>30</age>
    <email>test@example.com</email>
    <address>
        <city>北京</city>
        <district>朝阳区</district>
        <street>测试街道123号</street>
    </address>
    <tags>
        <tag>开发</tag>
        <tag>测试</tag>
        <tag>数据库</tag>
    </tags>
    <active>true</active>
    <balance>1234.56</balance>
</user>'''
    db.put(b'user:xml:001', xml_data.encode('utf-8'))
    print("   ✓ XML数据已写入: user:xml:001")
    
    # 3. 压缩的JSON（单行）
    print("3. 写入压缩JSON（单行）...")
    compact_json = json.dumps({"id": 1, "name": "压缩JSON", "data": [1, 2, 3, 4, 5]}, ensure_ascii=False)
    db.put(b'data:compact_json', compact_json.encode('utf-8'))
    print("   ✓ 压缩JSON已写入: data:compact_json")
    
    # 4. 嵌套JSON
    print("4. 写入嵌套JSON...")
    nested_json = {
        "level1": {
            "level2": {
                "level3": {
                    "level4": {
                        "value": "深度嵌套的数据",
                        "numbers": [1, 2, 3, 4, 5],
                        "nested": {
                            "final": "最终值"
                        }
                    }
                }
            }
        },
        "array": [
            {"item": 1, "name": "项目1"},
            {"item": 2, "name": "项目2"},
            {"item": 3, "name": "项目3"}
        ]
    }
    db.put(b'data:nested_json', json.dumps(nested_json, ensure_ascii=False).encode('utf-8'))
    print("   ✓ 嵌套JSON已写入: data:nested_json")
    
    # 5. 二进制数据
    print("5. 写入二进制数据...")
    binary_data = bytes(range(256))  # 0-255的字节序列
    db.put(b'data:binary', binary_data)
    print("   ✓ 二进制数据已写入: data:binary")
    
    # 6. 文本数据
    print("6. 写入文本数据...")
    text_data = "这是一段普通文本数据。\n包含多行内容。\n第三行内容。"
    db.put(b'data:text', text_data.encode('utf-8'))
    print("   ✓ 文本数据已写入: data:text")
    
    # 7. Tree格式（键值对）
    print("7. 写入Tree格式数据...")
    tree_data = """name: 测试用户
age: 30
email: test@example.com
city: 北京
district: 朝阳区
active: true
balance: 1234.56"""
    db.put(b'data:tree', tree_data.encode('utf-8'))
    print("   ✓ Tree格式数据已写入: data:tree")
    
    # 8. 混合格式（包含JSON字符串的文本）
    print("8. 写入混合格式数据...")
    mixed_data = "这是一个包含JSON字符串的文本: {\"key\": \"value\", \"number\": 123}"
    db.put(b'data:mixed', mixed_data.encode('utf-8'))
    print("   ✓ 混合格式数据已写入: data:mixed")
    
    # 刷新到磁盘
    db.flush()
    print()
    print("=" * 80)
    print("所有测试数据已创建并保存")
    print("=" * 80)
    print()
    
    return db_path

def test_formatting(db_path):
    """测试格式化显示"""
    
    db = Database(data_dir=db_path)
    
    print("=" * 80)
    print("测试不同类型value的渲染方式")
    print("=" * 80)
    print()
    
    test_keys = [
        (b'user:json:001', 'JSON格式（美化）'),
        (b'user:xml:001', 'XML格式（美化）'),
        (b'data:compact_json', '压缩JSON（单行）'),
        (b'data:nested_json', '嵌套JSON（深度嵌套）'),
        (b'data:binary', '二进制数据（十六进制）'),
        (b'data:text', '文本数据'),
        (b'data:tree', 'Tree格式（键值对）'),
        (b'data:mixed', '混合格式（文本包含JSON）'),
    ]
    
    for key, description in test_keys:
        print("=" * 80)
        print(f"测试: {description}")
        print("=" * 80)
        print()
        
        value = db.get(key)
        if value:
            key_str = key.decode('utf-8', errors='ignore')
            print(f"键: {key_str}")
            print(f"大小: {len(value)} bytes")
            print("-" * 80)
            
            # 使用ValueFormatter格式化
            formatted_value, format_type = ValueFormatter.format_value(value, max_length=10000)
            
            format_labels = {
                'json': 'JSON',
                'xml': 'XML',
                'binary': 'Binary (十六进制)',
                'tree': 'Tree (键值对)',
                'text': 'Text',
                'unknown': 'Unknown'
            }
            format_label = format_labels.get(format_type, format_type)
            
            print(f"检测到的格式: {format_label}")
            print()
            print("格式化后的值:")
            print("-" * 80)
            print(formatted_value)
            print("-" * 80)
        else:
            print(f"✗ 未找到键: {key.decode('utf-8', errors='ignore')}")
        
        print()
        print()

def main():
    """主函数"""
    import os
    import shutil
    
    # 清理旧的测试数据
    db_path = './data/test_formatting'
    if os.path.exists(db_path):
        print(f"清理旧的测试数据: {db_path}")
        shutil.rmtree(db_path)
        print()
    
    # 创建测试数据
    create_test_data()
    
    # 测试格式化显示
    test_formatting(db_path)
    
    print("=" * 80)
    print("测试完成！")
    print("=" * 80)
    print()
    print("提示: 可以在CLI中使用以下命令查看格式化效果:")
    print("  connect ./data/test_formatting")
    print("  get user:json:001")
    print("  get user:xml:001")
    print("  get data:binary")
    print("  get data:tree")
    print()

if __name__ == "__main__":
    main()

