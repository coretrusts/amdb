# -*- coding: utf-8 -*-
"""
值格式化模块
支持多种数据格式的解析和展示：JSON、XML、Binary、Tree等
"""

import json
import xml.etree.ElementTree as ET
from typing import Tuple, Optional, Dict, Any
import re


class ValueFormatter:
    """值格式化器"""
    
    @staticmethod
    def detect_format(value: bytes) -> str:
        """
        检测值的格式
        
        Returns:
            'json', 'xml', 'binary', 'text', 'tree', 'geo', 'ip', 'enum', 'unknown'
        """
        if not value:
            return 'unknown'
        
        # 检查是否包含不可打印字符（可能是二进制数据）
        if len(value) > 0:
            non_printable = sum(1 for b in value if b < 32 and b not in [9, 10, 13])  # 排除tab、换行、回车
            if non_printable > len(value) * 0.1:  # 如果超过10%是不可打印字符，可能是二进制
                return 'binary'
        
        # 尝试解码为文本
        try:
            text = value.decode('utf-8', errors='strict')
        except:
            # 无法解码为UTF-8，可能是二进制数据
            return 'binary'
        
        # 检测JSON
        text_stripped = text.strip()
        if (text_stripped.startswith('{') and text_stripped.endswith('}')) or \
           (text_stripped.startswith('[') and text_stripped.endswith(']')):
            try:
                obj = json.loads(text_stripped)
                # 检查是否是特殊类型的JSON
                if isinstance(obj, dict):
                    # 检测地理坐标
                    if 'lat' in obj and 'lng' in obj:
                        return 'geo'
                    if 'latitude' in obj and 'longitude' in obj:
                        return 'geo'
                    if 'type' in obj and obj.get('type') == 'Point' and 'coordinates' in obj:
                        return 'geo'
                    # 检测IP地址
                    if 'ip' in obj or 'ipv4' in obj or 'ipv6' in obj:
                        return 'ip'
                    # 检测枚举
                    if 'enum' in obj or 'type' in obj and isinstance(obj.get('type'), str) and obj.get('type').upper() in ['ENUM', 'ENUMERATION']:
                        return 'enum'
                return 'json'
            except:
                pass
        
        # 检测XML
        if text_stripped.startswith('<?xml') or text_stripped.startswith('<'):
            try:
                ET.fromstring(text_stripped)
                return 'xml'
            except:
                pass
        
        # 检测IP地址格式（IPv4或IPv6）
        ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        ipv6_pattern = r'^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$|^::1$|^::$'
        if re.match(ipv4_pattern, text_stripped) or re.match(ipv6_pattern, text_stripped):
            return 'ip'
        
        # 检测地理坐标格式（纬度,经度 或 lat,lng）
        geo_patterns = [
            r'^-?\d+\.?\d*,\s*-?\d+\.?\d*$',  # 39.9042,116.4074
            r'^lat:\s*-?\d+\.?\d*,\s*lng:\s*-?\d+\.?\d*$',  # lat: 39.9042, lng: 116.4074
            r'^latitude:\s*-?\d+\.?\d*,\s*longitude:\s*-?\d+\.?\d*$',  # latitude: 39.9042, longitude: 116.4074
        ]
        for pattern in geo_patterns:
            if re.match(pattern, text_stripped, re.IGNORECASE):
                return 'geo'
        
        # 检测枚举格式（逗号分隔的值列表，或 key=value 格式）
        enum_pattern = r'^[\w\s,=]+$'
        if re.match(enum_pattern, text_stripped) and ',' in text_stripped:
            # 可能是枚举值列表
            parts = [p.strip() for p in text_stripped.split(',')]
            if len(parts) >= 2 and all(len(p) < 50 for p in parts):
                return 'enum'
        
        # 检测Tree结构（键值对格式，如 key:value 或 key=value）
        if re.search(r'^\s*[\w\-]+\s*[:=]\s*', text, re.MULTILINE):
            return 'tree'
        
        # 普通文本
        return 'text'
    
    @staticmethod
    def format_value(value: bytes, format_type: Optional[str] = None, max_length: int = 1000) -> Tuple[str, str]:
        """
        格式化值用于显示
        
        Args:
            value: 原始字节值
            format_type: 格式类型（如果为None，自动检测）
            max_length: 最大显示长度
            
        Returns:
            (formatted_value, detected_format)
        """
        if not value:
            return ('(空)', 'unknown')
        
        # 自动检测格式
        if format_type is None:
            format_type = ValueFormatter.detect_format(value)
        
        try:
            if format_type == 'json':
                return ValueFormatter._format_json(value, max_length)
            elif format_type == 'xml':
                return ValueFormatter._format_xml(value, max_length)
            elif format_type == 'binary':
                return ValueFormatter._format_binary(value, max_length)
            elif format_type == 'tree':
                return ValueFormatter._format_tree(value, max_length)
            elif format_type == 'geo':
                return ValueFormatter._format_geo(value, max_length)
            elif format_type == 'ip':
                return ValueFormatter._format_ip(value, max_length)
            elif format_type == 'enum':
                return ValueFormatter._format_enum(value, max_length)
            elif format_type == 'text':
                return ValueFormatter._format_text(value, max_length)
            else:
                return ValueFormatter._format_text(value, max_length)
        except Exception as e:
            # 格式化失败，返回原始文本
            try:
                text = value.decode('utf-8', errors='ignore')
                if len(text) > max_length:
                    text = text[:max_length] + "..."
                return (text, 'text')
            except:
                hex_str = value.hex()[:max_length]
                if len(value) * 2 > max_length:
                    hex_str += "..."
                return (hex_str, 'binary')
    
    @staticmethod
    def _format_json(value: bytes, max_length: int) -> Tuple[str, str]:
        """格式化JSON"""
        try:
            text = value.decode('utf-8')
            obj = json.loads(text)
            formatted = json.dumps(obj, ensure_ascii=False, indent=2)
            
            if len(formatted) > max_length:
                formatted = formatted[:max_length] + "\n...(已截断)"
            
            return (formatted, 'json')
        except:
            # JSON解析失败，返回原始文本
            text = value.decode('utf-8', errors='ignore')
            if len(text) > max_length:
                text = text[:max_length] + "..."
            return (text, 'text')
    
    @staticmethod
    def _format_xml(value: bytes, max_length: int) -> Tuple[str, str]:
        """格式化XML"""
        try:
            text = value.decode('utf-8')
            root = ET.fromstring(text)
            
            # 美化XML
            def indent(elem, level=0):
                i = "\n" + level * "  "
                if len(elem):
                    if not elem.text or not elem.text.strip():
                        elem.text = i + "  "
                    if not elem.tail or not elem.tail.strip():
                        elem.tail = i
                    for child in elem:
                        indent(child, level+1)
                    if not child.tail or not child.tail.strip():
                        child.tail = i
                else:
                    if level and (not elem.tail or not elem.tail.strip()):
                        elem.tail = i
            
            indent(root)
            formatted = ET.tostring(root, encoding='unicode')
            
            if len(formatted) > max_length:
                formatted = formatted[:max_length] + "\n...(已截断)"
            
            return (formatted, 'xml')
        except:
            # XML解析失败，返回原始文本
            text = value.decode('utf-8', errors='ignore')
            if len(text) > max_length:
                text = text[:max_length] + "..."
            return (text, 'text')
    
    @staticmethod
    def _format_binary(value: bytes, max_length: int) -> Tuple[str, str]:
        """格式化二进制数据（十六进制显示）"""
        hex_str = value.hex()
        
        # 每16字节一行
        lines = []
        for i in range(0, len(hex_str), 32):  # 32个十六进制字符 = 16字节
            chunk = hex_str[i:i+32]
            # 添加ASCII表示
            ascii_repr = ''.join(chr(b) if 32 <= b < 127 else '.' 
                               for b in value[i//2:(i+32)//2])
            lines.append(f"{i//2:08x}: {chunk[:32]}  {ascii_repr}")
        
        formatted = '\n'.join(lines)
        
        if len(formatted) > max_length:
            formatted = formatted[:max_length] + "\n...(已截断)"
        
        return (formatted, 'binary')
    
    @staticmethod
    def _format_tree(value: bytes, max_length: int) -> Tuple[str, str]:
        """格式化Tree结构（键值对）"""
        try:
            text = value.decode('utf-8')
            lines = text.split('\n')
            
            formatted_lines = []
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # 尝试解析 key:value 或 key=value
                if ':' in line:
                    key, val = line.split(':', 1)
                    formatted_lines.append(f"{key.strip()}: {val.strip()}")
                elif '=' in line:
                    key, val = line.split('=', 1)
                    formatted_lines.append(f"{key.strip()} = {val.strip()}")
                else:
                    formatted_lines.append(line)
            
            formatted = '\n'.join(formatted_lines)
            
            if len(formatted) > max_length:
                formatted = formatted[:max_length] + "\n...(已截断)"
            
            return (formatted, 'tree')
        except:
            text = value.decode('utf-8', errors='ignore')
            if len(text) > max_length:
                text = text[:max_length] + "..."
            return (text, 'text')
    
    @staticmethod
    def _format_geo(value: bytes, max_length: int) -> Tuple[str, str]:
        """格式化地理坐标"""
        try:
            text = value.decode('utf-8')
            text_stripped = text.strip()
            
            # 尝试解析为JSON
            try:
                obj = json.loads(text_stripped)
                if isinstance(obj, dict):
                    # GeoJSON格式
                    if 'type' in obj and obj.get('type') == 'Point' and 'coordinates' in obj:
                        coords = obj['coordinates']
                        formatted = f"GeoJSON Point\n  经度 (Longitude): {coords[0]}\n  纬度 (Latitude): {coords[1]}"
                        if len(coords) > 2:
                            formatted += f"\n  高度 (Altitude): {coords[2]}"
                        return (formatted, 'geo')
                    # 普通坐标对象
                    lat = obj.get('lat') or obj.get('latitude')
                    lng = obj.get('lng') or obj.get('longitude') or obj.get('lon')
                    if lat is not None and lng is not None:
                        formatted = f"地理坐标\n  纬度 (Latitude): {lat}\n  经度 (Longitude): {lng}"
                        if 'altitude' in obj or 'elevation' in obj:
                            alt = obj.get('altitude') or obj.get('elevation')
                            formatted += f"\n  高度 (Altitude): {alt}"
                        if 'name' in obj:
                            formatted += f"\n  名称: {obj['name']}"
                        return (formatted, 'geo')
            except:
                pass
            
            # 解析逗号分隔的坐标
            if ',' in text_stripped:
                parts = [p.strip() for p in text_stripped.split(',')]
                if len(parts) >= 2:
                    try:
                        lat = float(parts[0])
                        lng = float(parts[1])
                        formatted = f"地理坐标\n  纬度 (Latitude): {lat}\n  经度 (Longitude): {lng}"
                        if len(parts) >= 3:
                            alt = float(parts[2])
                            formatted += f"\n  高度 (Altitude): {alt}"
                        return (formatted, 'geo')
                    except ValueError:
                        pass
            
            # 解析 lat: x, lng: y 格式
            lat_match = re.search(r'lat(?:itude)?:\s*(-?\d+\.?\d*)', text_stripped, re.IGNORECASE)
            lng_match = re.search(r'lng(?:itude)?|lon(?:gitude)?:\s*(-?\d+\.?\d*)', text_stripped, re.IGNORECASE)
            if lat_match and lng_match:
                lat = float(lat_match.group(1))
                lng = float(lng_match.group(1))
                formatted = f"地理坐标\n  纬度 (Latitude): {lat}\n  经度 (Longitude): {lng}"
                return (formatted, 'geo')
            
            # 无法解析，返回原始文本
            if len(text_stripped) > max_length:
                text_stripped = text_stripped[:max_length] + "..."
            return (text_stripped, 'geo')
        except:
            text = value.decode('utf-8', errors='ignore')
            if len(text) > max_length:
                text = text[:max_length] + "..."
            return (text, 'geo')
    
    @staticmethod
    def _format_ip(value: bytes, max_length: int) -> Tuple[str, str]:
        """格式化IP地址"""
        try:
            text = value.decode('utf-8')
            text_stripped = text.strip()
            
            # 尝试解析为JSON
            try:
                obj = json.loads(text_stripped)
                if isinstance(obj, dict):
                    ip = obj.get('ip') or obj.get('ipv4') or obj.get('ipv6')
                    if ip:
                        formatted = f"IP地址信息\n  IP地址: {ip}"
                        if 'type' in obj:
                            formatted += f"\n  类型: {obj['type']}"
                        if 'version' in obj:
                            formatted += f"\n  版本: IPv{obj['version']}"
                        if 'country' in obj:
                            formatted += f"\n  国家: {obj['country']}"
                        if 'city' in obj:
                            formatted += f"\n  城市: {obj['city']}"
                        if 'isp' in obj:
                            formatted += f"\n  ISP: {obj['isp']}"
                        return (formatted, 'ip')
            except:
                pass
            
            # 直接是IP地址字符串
            ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
            ipv6_pattern = r'^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$|^::1$|^::$'
            
            if re.match(ipv4_pattern, text_stripped):
                parts = text_stripped.split('.')
                formatted = f"IPv4地址\n  {text_stripped}"
                try:
                    # 检查是否是私有IP
                    first_octet = int(parts[0])
                    if first_octet == 10 or (first_octet == 172 and 16 <= int(parts[1]) <= 31) or (first_octet == 192 and int(parts[1]) == 168):
                        formatted += "\n  类型: 私有IP地址"
                    elif first_octet == 127:
                        formatted += "\n  类型: 回环地址 (localhost)"
                    elif first_octet >= 224:
                        formatted += "\n  类型: 组播地址"
                    else:
                        formatted += "\n  类型: 公网IP地址"
                except:
                    pass
                return (formatted, 'ip')
            elif re.match(ipv6_pattern, text_stripped) or '::' in text_stripped:
                formatted = f"IPv6地址\n  {text_stripped}"
                if text_stripped == '::1':
                    formatted += "\n  类型: 回环地址 (localhost)"
                return (formatted, 'ip')
            
            # 无法解析，返回原始文本
            if len(text_stripped) > max_length:
                text_stripped = text_stripped[:max_length] + "..."
            return (text_stripped, 'ip')
        except:
            text = value.decode('utf-8', errors='ignore')
            if len(text) > max_length:
                text = text[:max_length] + "..."
            return (text, 'ip')
    
    @staticmethod
    def _format_enum(value: bytes, max_length: int) -> Tuple[str, str]:
        """格式化枚举类型"""
        try:
            text = value.decode('utf-8')
            text_stripped = text.strip()
            
            # 尝试解析为JSON
            try:
                obj = json.loads(text_stripped)
                if isinstance(obj, dict):
                    enum_value = obj.get('value') or obj.get('enum')
                    enum_type = obj.get('type') or obj.get('name', 'Enum')
                    formatted = f"枚举类型: {enum_type}\n  值: {enum_value}"
                    if 'options' in obj:
                        formatted += f"\n  可选值: {', '.join(map(str, obj['options']))}"
                    return (formatted, 'enum')
                elif isinstance(obj, list):
                    formatted = "枚举值列表:\n"
                    for i, item in enumerate(obj, 1):
                        formatted += f"  {i}. {item}\n"
                    return (formatted.strip(), 'enum')
            except:
                pass
            
            # 解析逗号分隔的枚举值
            if ',' in text_stripped:
                parts = [p.strip() for p in text_stripped.split(',')]
                formatted = "枚举值列表:\n"
                for i, part in enumerate(parts, 1):
                    formatted += f"  {i}. {part}\n"
                return (formatted.strip(), 'enum')
            
            # 解析 key=value 格式
            if '=' in text_stripped:
                parts = [p.strip() for p in text_stripped.split('=')]
                if len(parts) == 2:
                    formatted = f"枚举\n  键: {parts[0]}\n  值: {parts[1]}"
                    return (formatted, 'enum')
            
            # 无法解析，返回原始文本
            if len(text_stripped) > max_length:
                text_stripped = text_stripped[:max_length] + "..."
            return (text_stripped, 'enum')
        except:
            text = value.decode('utf-8', errors='ignore')
            if len(text) > max_length:
                text = text[:max_length] + "..."
            return (text, 'enum')
    
    @staticmethod
    def _format_text(value: bytes, max_length: int) -> Tuple[str, str]:
        """格式化普通文本"""
        try:
            text = value.decode('utf-8', errors='ignore')
            if len(text) > max_length:
                text = text[:max_length] + "..."
            return (text, 'text')
        except:
            hex_str = value.hex()[:max_length]
            if len(value) * 2 > max_length:
                hex_str += "..."
            return (hex_str, 'binary')
    
    @staticmethod
    def get_preview(value: bytes, max_length: int = 50) -> str:
        """
        获取值的预览（用于列表显示）
        
        Args:
            value: 原始字节值
            max_length: 最大预览长度
            
        Returns:
            预览字符串
        """
        if not value:
            return '(空)'
        
        format_type = ValueFormatter.detect_format(value)
        
        try:
            if format_type == 'json':
                text = value.decode('utf-8')
                obj = json.loads(text)
                preview = json.dumps(obj, ensure_ascii=False)
                if len(preview) > max_length:
                    preview = preview[:max_length] + "..."
                return preview
            elif format_type == 'xml':
                text = value.decode('utf-8')
                if len(text) > max_length:
                    return text[:max_length] + "..."
                return text
            elif format_type == 'binary':
                hex_str = value.hex()[:max_length]
                if len(value) * 2 > max_length:
                    hex_str += "..."
                return f"[Binary: {len(value)} bytes] {hex_str}"
            elif format_type == 'tree':
                text = value.decode('utf-8')
                first_line = text.split('\n')[0]
                if len(first_line) > max_length:
                    return first_line[:max_length] + "..."
                return first_line
            else:
                text = value.decode('utf-8', errors='ignore')
                if len(text) > max_length:
                    return text[:max_length] + "..."
                return text
        except:
            try:
                text = value.decode('utf-8', errors='ignore')
                if len(text) > max_length:
                    return text[:max_length] + "..."
                return text
            except:
                return f"[Binary: {len(value)} bytes]"

