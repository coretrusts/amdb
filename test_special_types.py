# -*- coding: utf-8 -*-
"""
测试特殊数据类型：enum、geo、IP、坐标系
"""

import sys
import json
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.amdb import Database
from src.amdb.value_formatter import ValueFormatter

def create_special_type_data():
    """创建特殊类型测试数据"""
    
    db_path = './data/test_special_types'
    db = Database(data_dir=db_path)
    
    print("=" * 80)
    print("创建特殊类型测试数据")
    print("=" * 80)
    print()
    
    # 1. 地理坐标 - JSON格式
    print("1. 写入地理坐标（JSON格式）...")
    geo_json = {
        "lat": 39.9042,
        "lng": 116.4074,
        "altitude": 50,
        "name": "北京天安门"
    }
    db.put(b'location:beijing', json.dumps(geo_json, ensure_ascii=False).encode('utf-8'))
    print("   ✓ 地理坐标JSON已写入: location:beijing")
    
    # 2. 地理坐标 - GeoJSON格式
    print("2. 写入地理坐标（GeoJSON格式）...")
    geojson = {
        "type": "Point",
        "coordinates": [116.4074, 39.9042, 50]
    }
    db.put(b'location:geojson', json.dumps(geojson, ensure_ascii=False).encode('utf-8'))
    print("   ✓ GeoJSON已写入: location:geojson")
    
    # 3. 地理坐标 - 逗号分隔格式
    print("3. 写入地理坐标（逗号分隔）...")
    geo_string = "39.9042,116.4074,50"
    db.put(b'location:simple', geo_string.encode('utf-8'))
    print("   ✓ 简单坐标已写入: location:simple")
    
    # 4. 地理坐标 - lat/lng格式
    print("4. 写入地理坐标（lat/lng格式）...")
    geo_latlng = "latitude: 39.9042, longitude: 116.4074"
    db.put(b'location:latlng', geo_latlng.encode('utf-8'))
    print("   ✓ lat/lng格式已写入: location:latlng")
    
    # 5. IP地址 - IPv4
    print("5. 写入IP地址（IPv4）...")
    ipv4 = "192.168.1.1"
    db.put(b'ip:ipv4', ipv4.encode('utf-8'))
    print("   ✓ IPv4已写入: ip:ipv4")
    
    # 6. IP地址 - IPv6
    print("6. 写入IP地址（IPv6）...")
    ipv6 = "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
    db.put(b'ip:ipv6', ipv6.encode('utf-8'))
    print("   ✓ IPv6已写入: ip:ipv6")
    
    # 7. IP地址 - localhost
    print("7. 写入IP地址（localhost）...")
    localhost = "127.0.0.1"
    db.put(b'ip:localhost', localhost.encode('utf-8'))
    print("   ✓ localhost已写入: ip:localhost")
    
    # 8. IP地址 - JSON格式（带地理位置信息）
    print("8. 写入IP地址（JSON格式，带地理位置）...")
    ip_info = {
        "ip": "8.8.8.8",
        "type": "public",
        "version": 4,
        "country": "US",
        "city": "Mountain View",
        "isp": "Google"
    }
    db.put(b'ip:info', json.dumps(ip_info, ensure_ascii=False).encode('utf-8'))
    print("   ✓ IP信息JSON已写入: ip:info")
    
    # 9. 枚举 - JSON格式
    print("9. 写入枚举（JSON格式）...")
    enum_json = {
        "type": "Status",
        "value": "ACTIVE",
        "options": ["ACTIVE", "INACTIVE", "PENDING", "DELETED"]
    }
    db.put(b'enum:status', json.dumps(enum_json, ensure_ascii=False).encode('utf-8'))
    print("   ✓ 枚举JSON已写入: enum:status")
    
    # 10. 枚举 - 逗号分隔格式
    print("10. 写入枚举（逗号分隔）...")
    enum_list = "ACTIVE,INACTIVE,PENDING,DELETED"
    db.put(b'enum:list', enum_list.encode('utf-8'))
    print("   ✓ 枚举列表已写入: enum:list")
    
    # 11. 枚举 - key=value格式
    print("11. 写入枚举（key=value格式）...")
    enum_kv = "status=ACTIVE"
    db.put(b'enum:kv', enum_kv.encode('utf-8'))
    print("   ✓ 枚举键值对已写入: enum:kv")
    
    # 12. 坐标系 - WGS84
    print("12. 写入坐标系（WGS84）...")
    wgs84 = {
        "type": "WGS84",
        "lat": 39.9042,
        "lng": 116.4074,
        "datum": "WGS84",
        "srid": 4326
    }
    db.put(b'coordinate:wgs84', json.dumps(wgs84, ensure_ascii=False).encode('utf-8'))
    print("   ✓ WGS84坐标系已写入: coordinate:wgs84")
    
    # 13. 坐标系 - GCJ02（火星坐标）
    print("13. 写入坐标系（GCJ02）...")
    gcj02 = {
        "type": "GCJ02",
        "lat": 39.9069,
        "lng": 116.3974,
        "datum": "GCJ02",
        "description": "中国国家测绘局坐标系"
    }
    db.put(b'coordinate:gcj02', json.dumps(gcj02, ensure_ascii=False).encode('utf-8'))
    print("   ✓ GCJ02坐标系已写入: coordinate:gcj02")
    
    # 14. 坐标系 - BD09（百度坐标）
    print("14. 写入坐标系（BD09）...")
    bd09 = {
        "type": "BD09",
        "lat": 39.9151,
        "lng": 116.4034,
        "datum": "BD09",
        "description": "百度地图坐标系"
    }
    db.put(b'coordinate:bd09', json.dumps(bd09, ensure_ascii=False).encode('utf-8'))
    print("   ✓ BD09坐标系已写入: coordinate:bd09")
    
    # 刷新到磁盘
    db.flush()
    print()
    print("=" * 80)
    print("所有特殊类型测试数据已创建并保存")
    print("=" * 80)
    print()
    
    return db_path

def test_special_types(db_path):
    """测试特殊类型格式化显示"""
    
    db = Database(data_dir=db_path)
    
    print("=" * 80)
    print("测试特殊类型格式化显示")
    print("=" * 80)
    print()
    
    test_cases = [
        (b'location:beijing', '地理坐标（JSON格式）'),
        (b'location:geojson', '地理坐标（GeoJSON格式）'),
        (b'location:simple', '地理坐标（逗号分隔）'),
        (b'location:latlng', '地理坐标（lat/lng格式）'),
        (b'ip:ipv4', 'IP地址（IPv4）'),
        (b'ip:ipv6', 'IP地址（IPv6）'),
        (b'ip:localhost', 'IP地址（localhost）'),
        (b'ip:info', 'IP地址（JSON格式，带地理位置）'),
        (b'enum:status', '枚举（JSON格式）'),
        (b'enum:list', '枚举（逗号分隔）'),
        (b'enum:kv', '枚举（key=value格式）'),
        (b'coordinate:wgs84', '坐标系（WGS84）'),
        (b'coordinate:gcj02', '坐标系（GCJ02）'),
        (b'coordinate:bd09', '坐标系（BD09）'),
    ]
    
    for key, description in test_cases:
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
                'geo': 'Geo (地理坐标)',
                'ip': 'IP (IP地址)',
                'enum': 'Enum (枚举)',
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
    db_path = './data/test_special_types'
    if os.path.exists(db_path):
        print(f"清理旧的测试数据: {db_path}")
        shutil.rmtree(db_path)
        print()
    
    # 创建测试数据
    create_special_type_data()
    
    # 测试格式化显示
    test_special_types(db_path)
    
    print("=" * 80)
    print("测试完成！")
    print("=" * 80)
    print()
    print("提示: 可以在CLI中使用以下命令查看格式化效果:")
    print("  connect ./data/test_special_types")
    print("  get location:beijing")
    print("  get ip:ipv4")
    print("  get enum:status")
    print("  get coordinate:wgs84")
    print()

if __name__ == "__main__":
    main()

