# -*- coding: utf-8 -*-
"""
AmDb 命令行工具（CLI）
类似MySQL的mysql命令行客户端
支持交互式命令行界面和数据库连接管理
"""

import sys
import os
import argparse
import cmd
import shlex
from typing import Optional, Dict, Any, List
from pathlib import Path

from .database import Database
from .config import load_config
from .value_formatter import ValueFormatter
from .network import RemoteDatabase


class AmDbCLI(cmd.Cmd):
    """AmDb交互式命令行界面"""
    
    intro = """
╔══════════════════════════════════════════════════════════════╗
║                  AmDb 命令行工具 (CLI)                        ║
║           类似MySQL的mysql命令行客户端                        ║
╚══════════════════════════════════════════════════════════════╝

输入 'help' 或 '?' 查看可用命令
输入 'help <命令>' 查看命令详细说明
输入 'exit' 或 'quit' 退出

"""
    prompt = 'amdb> '
    
    def __init__(self, data_dir: Optional[str] = None, config_path: Optional[str] = None,
                 host: Optional[str] = None, port: Optional[int] = None, database: Optional[str] = None,
                 data_root_dir: Optional[str] = None):
        super().__init__()
        self.db: Optional[Database] = None
        self.remote_db: Optional[RemoteDatabase] = None
        self.data_dir: Optional[str] = None
        self.data_root_dir: Optional[str] = None  # 数据存储根目录
        self.config_path: Optional[str] = None
        self.host: Optional[str] = None
        self.port: Optional[int] = None
        self.database: Optional[str] = None
        self.connected = False
        self.is_remote = False  # 是否为远程连接
        
        # 优先使用传入的 data_root_dir，否则从配置加载
        if data_root_dir:
            self.data_root_dir = data_root_dir
        else:
            try:
                config = load_config(config_path)
                self.data_root_dir = config.data_root_dir
            except:
                self.data_root_dir = None  # 未指定，使用默认相对路径
        
        # 如果提供了 data_dir，检查是否是根目录
        # 如果用户通过 --data-dir 指定了路径，优先将其作为数据存储根目录
        should_connect = True  # 是否应该连接数据库
        if data_dir and os.path.exists(data_dir):
            try:
                from .db_scanner import scan_databases
                from pathlib import Path
                
                # 检查指定路径是否是一个数据库目录（有 database.amdb 或 versions 目录）
                amdb_file = Path(data_dir) / "database.amdb"
                versions_dir = Path(data_dir) / "versions"
                is_db_dir = amdb_file.exists() or versions_dir.exists()
                
                dbs = scan_databases(data_dir)
                
                if is_db_dir:
                    # 如果指定路径是一个数据库目录，从父目录扫描其他数据库
                    parent_dir = os.path.dirname(os.path.abspath(data_dir))
                    if parent_dir != data_dir:  # 确保不是根目录
                        parent_dbs = scan_databases(parent_dir)
                        if len(parent_dbs) > 1:
                            # 父目录包含多个数据库，使用父目录作为根目录
                            self.data_root_dir = parent_dir
                            print(f"检测到数据存储根目录: {parent_dir}")
                        else:
                            # 父目录不是根目录，使用父目录作为根目录（至少包含当前数据库）
                            self.data_root_dir = parent_dir
                            print(f"将父目录设置为数据存储根目录: {parent_dir}")
                else:
                    # 如果指定路径不是数据库目录，将其作为根目录
                    # 不连接数据库，因为这不是一个数据库目录
                    self.data_root_dir = data_dir
                    should_connect = False  # 不连接，因为这是根目录，不是数据库目录
                    print(f"将指定路径设置为数据存储根目录: {data_dir}")
                    if len(dbs) > 0:
                        print(f"找到 {len(dbs)} 个数据库")
                    else:
                        print(f"提示: 该目录下暂无数据库，可以使用 'connect <数据库名>' 创建新数据库")
            except Exception as e:
                # 如果扫描失败，仍然将指定路径作为根目录，但不连接
                self.data_root_dir = data_dir
                should_connect = False
                print(f"将指定路径设置为数据存储根目录: {data_dir}")
        
        # 如果提供了初始参数，自动连接（仅在应该连接时）
        if host and port:
            self._connect_remote(host, port, database)
        elif (data_dir or config_path) and should_connect:
            self._connect(data_dir, config_path)
    
    def _connect(self, data_dir: Optional[str] = None, config_path: Optional[str] = None) -> bool:
        """连接本地数据库"""
        try:
            if config_path:
                self.db = Database(config_path=config_path)
                self.config_path = config_path
            elif data_dir:
                self.db = Database(data_dir=data_dir, config_path=config_path)
                self.data_dir = data_dir
            else:
                self.db = Database()
                self.data_dir = self.db.data_dir
            
            self.is_remote = False
            self.remote_db = None
            self.host = None
            self.port = None
            self.database = None
            
            # 不在这里flush，因为flush是写入操作，连接时只需要加载数据
            # 数据会在Database初始化时自动从磁盘加载
            
            self.connected = True
            self.prompt = f'amdb [{os.path.basename(self.data_dir)}]> '
            print(f"✓ 已连接到本地数据库: {self.data_dir}")
            
            # 显示统计信息
            try:
                stats = self.db.get_stats()
                key_count = stats.get('total_keys', 0)
                if key_count > 0:
                    print(f"  当前数据库包含 {key_count} 条记录")
            except:
                pass
            
            return True
        except Exception as e:
            print(f"✗ 连接失败: {type(e).__name__}: {e}")
            self.db = None
            self.data_dir = None
            self.config_path = None
            self.connected = False
            self.prompt = 'amdb> '
            return False
    
    def _connect_remote(self, host: str, port: int, database: Optional[str] = None) -> bool:
        """连接远程数据库服务器"""
        try:
            self.remote_db = RemoteDatabase(host=host, port=port, database=database or "default")
            if self.remote_db.connect():
                self.is_remote = True
                self.db = None  # 远程连接不使用本地Database
                self.host = host
                self.port = port
                self.database = database or "default"
                self.data_dir = None
                self.config_path = None
                
                self.connected = True
                self.prompt = f'amdb [{host}:{port}/{self.database}]> '
                print(f"✓ 已连接到远程数据库: {host}:{port}/{self.database}")
                return True
            else:
                print(f"✗ 连接失败: 无法连接到 {host}:{port}")
                return False
        except Exception as e:
            print(f"✗ 连接失败: {type(e).__name__}: {e}")
            self.remote_db = None
            self.is_remote = False
            self.connected = False
            self.prompt = 'amdb> '
            return False
    
    def _check_connection(self) -> bool:
        """检查是否已连接"""
        if not self.connected:
            print("✗ 错误: 未连接到数据库，请先使用 'connect' 命令连接")
            return False
        if not self.is_remote and not self.db:
            print("✗ 错误: 本地数据库连接无效")
            return False
        if self.is_remote and not self.remote_db:
            print("✗ 错误: 远程数据库连接无效")
            return False
        return True
    
    def do_create(self, args: str):
        """
        创建新数据库
        
        用法:
          create database <数据库名> [--description "描述"] [--config 配置文件路径]
          
        示例:
          create database my_db
          create database my_db --description "我的数据库"
          create database my_db --config ./amdb.ini
        """
        if not args:
            print("用法: create database <数据库名> [--description \"描述\"] [--config 配置文件路径]")
            print("示例: create database my_db")
            print("      create database my_db --description \"我的数据库\"")
            return
        
        # 解析参数
        parts = shlex.split(args)
        if len(parts) < 2 or parts[0].lower() != 'database':
            print("用法: create database <数据库名> [--description \"描述\"] [--config 配置文件路径]")
            return
        
        db_name = parts[1]
        description = ""
        config_path = None
        
        i = 2
        while i < len(parts):
            if parts[i] == '--description' and i + 1 < len(parts):
                description = parts[i + 1]
                i += 2
            elif parts[i] == '--config' and i + 1 < len(parts):
                config_path = parts[i + 1]
                i += 2
            else:
                i += 1
        
        # 获取数据存储根目录
        if self.data_root_dir:
            data_root = self.data_root_dir
        else:
            try:
                config = load_config(config_path)
                data_root = config.data_root_dir if config.data_root_dir else "./data"
            except:
                data_root = "./data"
        
        # 构建数据库路径
        if os.path.isabs(db_name):
            db_path = db_name
        else:
            db_path = os.path.join(data_root, db_name)
        
        # 检查数据库是否已存在
        if os.path.exists(db_path):
            response = input(f"数据库已存在: {db_path}\n是否覆盖? (y/n): ")
            if response.lower() != 'y':
                print("已取消")
                return
            import shutil
            shutil.rmtree(db_path)
            print(f"✓ 已删除旧数据库: {db_path}")
        
        # 创建数据库目录
        try:
            os.makedirs(db_path, exist_ok=True)
            print(f"✓ 已创建数据库目录: {db_path}")
        except Exception as e:
            print(f"✗ 创建数据库目录失败: {e}")
            return
        
        # 创建数据库实例（这会自动创建 database.amdb 文件）
        try:
            db = Database(data_dir=db_path, config_path=config_path)
            
            # 设置数据库描述
            if description:
                db.set_description(description)
                db.flush()  # 确保元数据保存
            
            print(f"✓ 数据库创建成功: {db_path}")
            if description:
                print(f"  描述: {description}")
            
            # 询问是否立即连接
            response = input("是否立即连接到此数据库? (y/n): ")
            if response.lower() == 'y':
                self._connect(db_path, config_path)
        except Exception as e:
            print(f"✗ 创建数据库失败: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    def do_connect(self, args: str):
        """
        连接数据库（支持数据库名，自动补全路径）
        
        用法:
          connect [数据目录或数据库名] [--config 配置文件路径]
          
        示例:
          connect ./data/user_db          # 使用完整路径
          connect user_db                 # 使用数据库名（自动补全为./data/user_db）
          connect sample_db --config ./amdb.ini
          connect --config ./amdb.ini     # 仅指定配置文件
        """
        if not args:
            print("用法: connect [数据目录或数据库名] [--config 配置文件路径]")
            print("示例: connect ./data/user_db")
            print("      connect user_db  # 自动补全为 ./data/user_db")
            return
        
        # 解析参数
        parts = shlex.split(args)
        data_dir = None
        config_path = None
        
        i = 0
        while i < len(parts):
            if parts[i] == '--config' and i + 1 < len(parts):
                config_path = parts[i + 1]
                i += 2
            else:
                data_dir = parts[i]
                i += 1
        
        # 如果提供了数据目录，检查是否需要补全路径
        if data_dir:
            # 获取数据存储根目录（如果未指定，使用默认相对路径）
            if self.data_root_dir:
                data_root = self.data_root_dir
            else:
                try:
                    config = load_config(config_path)
                    data_root = config.data_root_dir if config.data_root_dir else "./data"
                except:
                    data_root = "./data"
            
            # 如果不是绝对路径且不以./或../开头，尝试作为数据库名处理
            if not os.path.isabs(data_dir) and not data_dir.startswith('./') and not data_dir.startswith('../'):
                # 尝试从数据存储根目录补全路径
                potential_path = os.path.join(data_root, data_dir)
                if os.path.exists(potential_path):
                    data_dir = potential_path
                    print(f"自动补全路径: {data_dir}")
                else:
                    # 如果数据根目录/<数据库名>不存在，仍然使用原路径（让用户决定是否创建）
                    pass
        
        # 如果数据目录不存在，询问是否创建
        if data_dir and not os.path.exists(data_dir):
            response = input(f"数据目录不存在: {data_dir}\n是否创建新数据库? (y/n): ")
            if response.lower() == 'y':
                os.makedirs(data_dir, exist_ok=True)
            else:
                print("已取消")
                return
        
        self._connect(data_dir, config_path)
    
    def do_set(self, args: str):
        """
        设置配置
        
        用法:
          set root <数据存储根目录路径>  # 设置数据存储根目录
          set root                      # 显示当前数据存储根目录
          
        示例:
          set root /path/to/storage      # 设置数据存储根目录
          set root ./data                # 设置相对路径
        """
        if not args:
            print("用法: set root <路径>")
            print("示例: set root /path/to/storage")
            return
        
        parts = args.strip().split(None, 1)
        if len(parts) < 1:
            print("用法: set root <路径>")
            return
        
        if parts[0] == 'root':
            if len(parts) < 2:
                # 显示当前根目录
                current_root = self.data_root_dir if self.data_root_dir else "./data"
                print(f"当前数据存储根目录: {current_root}")
                return
            
            root_path = parts[1].strip()
            # 验证路径是否存在
            if not os.path.exists(root_path):
                response = input(f"路径不存在: {root_path}\n是否创建? (y/n): ")
                if response.lower() == 'y':
                    os.makedirs(root_path, exist_ok=True)
                else:
                    print("已取消")
                    return
            
            if not os.path.isdir(root_path):
                print(f"✗ 错误: {root_path} 不是一个目录")
                return
            
            self.data_root_dir = os.path.abspath(root_path)
            print(f"✓ 已设置数据存储根目录: {self.data_root_dir}")
            print(f"提示: 使用 'show databases' 查看该目录下的所有数据库")
        else:
            print(f"✗ 未知的配置项: {parts[0]}")
            print("可用配置项: root")
    
    def do_disconnect(self, args: str):
        """
        断开数据库连接
        
        用法:
          disconnect
        """
        if self.connected:
            old_info = f"{self.host}:{self.port}/{self.database}" if self.is_remote else str(self.data_dir)
            if self.is_remote and self.remote_db:
                self.remote_db.disconnect()
            elif self.db:
                self.db.flush()
            self.db = None
            self.remote_db = None
            self.data_dir = None
            self.config_path = None
            self.host = None
            self.port = None
            self.database = None
            self.is_remote = False
            self.connected = False
            self.prompt = 'amdb> '
            print(f"✓ 已断开连接: {old_info}")
        else:
            print("✗ 当前未连接任何数据库")
    
    def do_use(self, args: str):
        """
        切换到指定数据库（快捷命令，支持数据库名）
        
        用法:
          use <数据目录或数据库名>
          
        示例:
          use ./data/user_db      # 使用完整路径
          use user_db             # 使用数据库名（自动补全为./data/user_db）
          use sample_db
        """
        if not args:
            print("用法: use <数据目录或数据库名>")
            print("示例: use ./data/user_db")
            print("      use user_db  # 自动补全为 ./data/user_db")
            return
        
        data_dir = args.strip()
        
        # 获取数据存储根目录（如果未指定，使用默认相对路径）
        if self.data_root_dir:
            data_root = self.data_root_dir
        else:
            try:
                config = load_config()
                data_root = config.data_root_dir if config.data_root_dir else "./data"
            except:
                data_root = "./data"
        
        # 如果不是绝对路径且不以./或../开头，尝试作为数据库名处理
        if not os.path.isabs(data_dir) and not data_dir.startswith('./') and not data_dir.startswith('../'):
            # 尝试从数据存储根目录补全路径
            potential_path = os.path.join(data_root, data_dir)
            if os.path.exists(potential_path):
                data_dir = potential_path
                print(f"自动补全路径: {data_dir}")
            else:
                # 如果./data/<数据库名>不存在，仍然使用原路径（让用户决定是否创建）
                pass
        
        if not os.path.exists(data_dir):
            response = input(f"数据目录不存在: {data_dir}\n是否创建新数据库? (y/n): ")
            if response.lower() == 'y':
                os.makedirs(data_dir, exist_ok=True)
            else:
                return
        
        self._connect(data_dir, self.config_path)
    
    def do_show(self, args: str):
        """
        显示信息
        
        用法:
          show databases          - 显示所有数据库
          show tables             - 显示所有表（键前缀）
          show keys [limit]       - 显示所有键（默认1000条，可指定limit，如: show keys 5000）
          show stats              - 显示数据库统计信息
          show config             - 显示当前配置
          show connection         - 显示当前连接信息
        """
        if not args:
            print("用法: show <databases|tables|keys|stats|config|connection>")
            return
        
        # 先分割参数，提取命令类型
        parts = args.strip().split()
        cmd_type = parts[0].lower() if parts else ''
        
        if cmd_type == 'databases':
            self._show_databases()
        elif cmd_type == 'tables':
            if not self._check_connection():
                return
            # 检查数据库文件状态（仅本地连接）
            if not self.is_remote and self.db:
                if not self.db.check_files_exist():
                    print("⚠ 警告: 数据库文件不存在或已清空，正在重新加载...")
                    self.db.reload_if_files_changed()
                    print("✓ 已重新加载数据库状态")
            self._show_tables()
        elif cmd_type == 'keys':
            if not self._check_connection():
                return
            # 检查数据库文件状态（仅本地连接）
            if not self.is_remote and self.db:
                if not self.db.check_files_exist():
                    print("⚠ 警告: 数据库文件不存在或已清空，正在重新加载...")
                    self.db.reload_if_files_changed()
                    print("✓ 已重新加载数据库状态")
            # 支持限制数量: show keys 5000
            limit = None
            if len(parts) > 1:
                try:
                    limit = int(parts[1])
                except ValueError:
                    print(f"✗ 无效的限制数量: {parts[1]}")
                    return
            self._show_keys(limit=limit)
        elif cmd_type == 'stats':
            if not self._check_connection():
                return
            # 检查数据库文件状态（仅本地连接）
            if not self.is_remote and self.db:
                if not self.db.check_files_exist():
                    print("⚠ 警告: 数据库文件不存在或已清空，正在重新加载...")
                    self.db.reload_if_files_changed()
                    print("✓ 已重新加载数据库状态")
            self._show_stats()
        elif cmd_type == 'config':
            if not self._check_connection():
                return
            self._show_config()
        elif cmd_type == 'connection':
            self._show_connection()
        else:
            print(f"✗ 未知的show命令: {cmd_type}")
            print("可用命令: databases, tables, keys, stats, config, connection")
    
    def _show_databases(self):
        """显示所有数据库（从数据存储根目录扫描）"""
        # 使用数据存储根目录（如果未指定，使用默认相对路径）
        if self.data_root_dir:
            data_root = self.data_root_dir
        else:
            # 从配置加载，如果配置也没有，使用默认相对路径
            try:
                config = load_config(self.config_path)
                data_root = config.data_root_dir if config.data_root_dir else "./data"
            except:
                data_root = "./data"
        
        if not os.path.exists(data_root):
            print(f"✗ 数据存储根目录不存在: {data_root}")
            print(f"提示: 使用 'set root <路径>' 设置数据存储根目录")
            return
        
        # 使用数据库扫描器扫描
        from .db_scanner import scan_databases
        databases = scan_databases(data_root)
        
        if databases:
            print(f"\n数据存储根目录: {data_root}")
            print("\n数据库列表:")
            print("-" * 80)
            print(f"{'数据库名':<30} {'路径':<40} {'记录数':<10}")
            print("-" * 80)
            for db in databases:
                name = db['name']
                path = db['path']
                count = db['total_keys'] if db['total_keys'] > 0 else 0
                print(f"{name:<30} {path:<40} {count:<10}")
            print("-" * 80)
            print(f"总计: {len(databases)} 个数据库")
        else:
            print(f"\n数据存储根目录: {data_root}")
            print(f"✗ 在 {data_root} 中未找到数据库")
            if self.data_root_dir:
                print(f"提示: 该目录下暂无数据库，可以使用 'connect <数据库名>' 创建新数据库")
            else:
                print(f"提示: 使用 'set root <路径>' 设置数据存储根目录")
    
    def _show_tables(self):
        """显示所有表（键前缀）"""
        try:
            all_keys = self.db.version_manager.get_all_keys()
            if not all_keys:
                print("✗ 数据库为空，没有键")
                return
            
            prefixes = {}
            for key in all_keys:
                key_str = key.decode('utf-8', errors='ignore')
                if ':' in key_str:
                    # 有分隔符的键，使用分隔符前的部分作为前缀
                    prefix = key_str.split(':')[0]
                    if prefix not in prefixes:
                        prefixes[prefix] = 0
                    prefixes[prefix] += 1
                else:
                    # 没有分隔符的键，尝试提取共同前缀
                    # 例如 key00000000, key00000001 -> key
                    # 或者 user001, user002 -> user
                    if len(key_str) > 0:
                        # 找到第一个数字的位置
                        first_digit_pos = -1
                        for i, char in enumerate(key_str):
                            if char.isdigit():
                                first_digit_pos = i
                                break
                        
                        if first_digit_pos > 0:
                            # 有数字，使用数字前的部分作为前缀
                            prefix = key_str[:first_digit_pos]
                        else:
                            # 没有数字，使用整个键作为前缀（如果键太长，截断）
                            if len(key_str) > 20:
                                prefix = key_str[:20] + "..."
                            else:
                                prefix = key_str
                        
                        if prefix not in prefixes:
                            prefixes[prefix] = 0
                        prefixes[prefix] += 1
                    else:
                        # 空键，归类为"empty"
                        if 'empty' not in prefixes:
                            prefixes['empty'] = 0
                        prefixes['empty'] += 1
            
            if prefixes:
                print("\n表（键前缀）列表:")
                print("-" * 80)
                print(f"{'前缀':<30} {'记录数':<10}")
                print("-" * 80)
                for prefix in sorted(prefixes.keys()):
                    print(f"{prefix:<30} {prefixes[prefix]:<10}")
                print("-" * 80)
                print(f"总计: {len(prefixes)} 个前缀，{len(all_keys)} 条记录")
                print("\n提示: 使用 'select * from <prefix>' 查询特定前缀的键")
                print("      例如: select * from key  (查询以'key'开头的键)")
            else:
                print("✗ 未找到表")
        except Exception as e:
            import traceback
            print(f"✗ 错误: {e}")
            traceback.print_exc()
    
    def _show_keys(self, limit: Optional[int] = None):
        """显示所有键（支持限制数量）"""
        try:
            all_keys = self.db.version_manager.get_all_keys()
            if not all_keys:
                print("✗ 数据库为空，没有键")
                return
            
            total_count = len(all_keys)
            print(f"\n所有键列表（共 {total_count} 个）:")
            print("-" * 80)
            
            # 如果没有指定限制，显示所有键（但为了避免输出过多，默认限制1000）
            if limit is None:
                limit = 1000  # 默认显示前1000个
            
            display_count = min(limit, total_count)
            displayed = 0
            
            for i, key in enumerate(all_keys):
                if displayed >= display_count:
                    break
                    
                try:
                    key_str = key.decode('utf-8', errors='ignore')
                    # 获取对应的值（可选，显示前50个字符）
                    value = self.db.get(key)
                    if value:
                        value_str = value.decode('utf-8', errors='ignore')
                        if len(value_str) > 50:
                            value_str = value_str[:50] + "..."
                        print(f"{i+1:6d}. {key_str:<50} = {value_str}")
                    else:
                        print(f"{i+1:6d}. {key_str}")
                    displayed += 1
                except Exception:
                    print(f"{i+1:6d}. {key.hex()[:50]}...")
                    displayed += 1
            
            if total_count > display_count:
                print("-" * 80)
                print(f"提示: 只显示前 {display_count} 个键，共有 {total_count} 个键")
                print(f"      使用 'select * from <prefix>' 查询特定前缀的键")
                print(f"      使用 'show keys <limit>' 显示更多键（例如: show keys 5000）")
            
            print("-" * 80)
        except Exception as e:
            import traceback
            print(f"✗ 错误: {e}")
            traceback.print_exc()
    
    def _show_stats(self):
        """显示数据库统计信息"""
        try:
            stats = self.db.get_stats()
            print("\n数据库统计信息:")
            print("=" * 80)
            print(f"总键数: {stats.get('total_keys', 0)}")
            print(f"当前版本: {stats.get('current_version', 0)}")
            print(f"Merkle根哈希: {stats.get('merkle_root', 'N/A')}")
            print(f"存储目录: {stats.get('storage_dir', 'N/A')}")
            print(f"分片启用: {stats.get('sharding_enabled', False)}")
            if stats.get('sharding_enabled'):
                print(f"分片数量: {stats.get('shard_count', 0)}")
            print("=" * 80)
        except Exception as e:
            print(f"✗ 错误: {e}")
    
    def _show_config(self):
        """显示当前配置"""
        try:
            if self.is_remote:
                # 远程连接
                config_dict = self.remote_db.get_config()
                if not config_dict:
                    print("✗ 无法获取配置信息")
                    return
                print("\n当前配置:")
                print("=" * 80)
                print(f"数据目录: {config_dict.get('data_dir', 'N/A')}")
                print(f"网络地址: {config_dict.get('network_host', 'N/A')}")
                print(f"网络端口: {config_dict.get('network_port', 'N/A')}")
                print(f"批量大小: {config_dict.get('batch_max_size', 'N/A')}")
                print(f"多线程启用: {config_dict.get('threading_enable', 'N/A')}")
                print(f"最大工作线程数: {config_dict.get('threading_max_workers', 'N/A')}")
                print(f"分片启用: {config_dict.get('enable_sharding', 'N/A')}")
                if config_dict.get('enable_sharding'):
                    print(f"分片数量: {config_dict.get('shard_count', 'N/A')}")
                print("=" * 80)
            else:
                # 本地连接
                config = self.db.config
                print("\n当前配置:")
                print("=" * 80)
                print(f"数据目录: {config.data_dir}")
                print(f"网络端口: {config.network_port}")
                print(f"批量大小: {config.batch_max_size}")
                print(f"多线程启用: {config.threading_enable}")
                print(f"最大工作线程数: {config.threading_max_workers}")
                print(f"分片启用: {config.enable_sharding}")
                if config.enable_sharding:
                    print(f"分片数量: {config.shard_count}")
                print("=" * 80)
        except Exception as e:
            print(f"✗ 错误: {e}")
            import traceback
            traceback.print_exc()
    
    def _show_connection(self):
        """显示当前连接信息"""
        if self.connected:
            print("\n当前连接:")
            print("=" * 80)
            if self.is_remote:
                print(f"连接类型: 远程服务器")
                print(f"服务器地址: {self.host}:{self.port}")
                print(f"数据库名称: {self.database}")
            else:
                print(f"连接类型: 本地文件")
                print(f"数据目录: {self.data_dir}")
                if self.config_path:
                    print(f"配置文件: {self.config_path}")
            print(f"连接状态: 已连接")
            print("=" * 80)
        else:
            print("✗ 当前未连接任何数据库")
    
    def do_put(self, args: str):
        """
        写入数据
        
        用法:
          put <key> <value>
          
        示例:
          put user:001 "{\"name\": \"张三\"}"
          put tx:001 "transaction data"
        """
        if not self._check_connection():
            return
        
        parts = shlex.split(args)
        if len(parts) < 2:
            print("用法: put <key> <value>")
            print("示例: put user:001 \"{\\\"name\\\": \\\"张三\\\"}\"")
            return
        
        key = parts[0].encode()
        value = ' '.join(parts[1:]).encode()
        
        try:
            if self.is_remote:
                # 远程连接
                success = self.remote_db.put(key, value)
                if success:
                    print(f"✓ 写入成功")
                    print(f"  Key: {key.decode('utf-8', errors='ignore')}")
                else:
                    print("✗ 写入失败")
            else:
                # 本地连接
                success, merkle_root = self.db.put(key, value)
                if success:
                    # 自动flush确保数据持久化
                    self.db.flush(async_mode=True)
                    print(f"✓ 写入成功（已持久化）")
                    print(f"  Key: {key.decode('utf-8', errors='ignore')}")
                    print(f"  Merkle根哈希: {merkle_root.hex()[:16]}...")
                else:
                    print("✗ 写入失败")
        except Exception as e:
            print(f"✗ 错误: {type(e).__name__}: {e}")
    
    def do_get(self, args: str):
        """
        读取数据（自动格式化显示）
        
        用法:
          get <key>
          
        示例:
          get user:001
          get tx:001
        """
        if not self._check_connection():
            return
        
        if not args:
            print("用法: get <key>")
            print("示例: get user:001")
            return
        
        key = args.strip().encode()
        
        try:
            # 检查数据库文件状态（仅本地连接）
            if not self.is_remote and self.db:
                if not self.db.check_files_exist():
                    print("⚠ 警告: 数据库文件不存在或已清空，正在重新加载...")
                    self.db.reload_if_files_changed()
                    print("✓ 已重新加载数据库状态")
            
            if self.is_remote:
                # 远程连接
                value = self.remote_db.get(key)
            else:
                # 本地连接
                value = self.db.get(key)
            
            if value:
                key_str = key.decode('utf-8', errors='ignore')
                print(f"✓ 找到数据:")
                print(f"  Key: {key_str}")
                print(f"  Value ({len(value)} bytes):")
                print("-" * 80)
                
                # 使用ValueFormatter自动检测和格式化
                formatted_value, format_type = ValueFormatter.format_value(value, max_length=5000)
                
                # 显示格式类型
                format_labels = {
                    'json': 'JSON',
                    'xml': 'XML',
                    'binary': 'Binary (十六进制)',
                    'tree': 'Tree (键值对)',
                    'text': 'Text',
                    'unknown': 'Unknown'
                }
                format_label = format_labels.get(format_type, format_type)
                print(f"  格式: {format_label}")
                print()
                
                # 显示格式化后的值
                print(formatted_value)
                print("-" * 80)
            else:
                print(f"✗ 未找到键: {key.decode('utf-8', errors='ignore')}")
        except Exception as e:
            print(f"✗ 错误: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    def do_delete(self, args: str):
        """
        删除数据或数据库
        
        用法:
          delete <key>              - 删除记录（标记删除）
          delete database <name>     - 删除整个数据库目录
          
        示例:
          delete user:001
          delete database test_db
        """
        if not args:
            print("用法: delete <key> 或 delete database <name>")
            print("示例: delete user:001")
            print("      delete database test_db")
            return
        
        parts = args.strip().split()
        
        # 检查是否是删除数据库
        if len(parts) >= 2 and parts[0].lower() == 'database':
            db_name = parts[1]
            self._delete_database(db_name)
            return
        
        # 删除记录
        if not self._check_connection():
            return
        
        key = args.strip().encode()
        
        try:
            # 检查键是否存在
            value = self.db.get(key)
            if value is None:
                # 检查是否已删除
                if self.db.is_deleted(key):
                    print(f"✗ 键 '{key.decode('utf-8', errors='ignore')}' 已被标记删除")
                else:
                    print(f"✗ 未找到键: {key.decode('utf-8', errors='ignore')}")
                return
            
            # 确认删除
            key_str = key.decode('utf-8', errors='ignore')
            confirm = input(f"确定要删除键 '{key_str}' 吗？(y/N): ").strip().lower()
            if confirm != 'y':
                print("已取消删除")
                return
            
            # 执行删除（标记删除）
            success = self.db.delete(key)
            if success:
                # 自动flush确保数据持久化
                self.db.flush(async_mode=True)
                print(f"✓ 已标记删除: {key_str}")
                print("提示: 由于使用版本管理，数据不会真正删除，但查询时将返回None")
            else:
                print("✗ 删除失败")
        except Exception as e:
            print(f"✗ 错误: {type(e).__name__}: {e}")
    
    def _delete_database(self, db_name: str):
        """
        删除整个数据库目录
        
        Args:
            db_name: 数据库名称（目录名）
        """
        import shutil
        from pathlib import Path
        
        # 构建数据库路径
        db_path = Path('./data') / db_name
        
        if not db_path.exists():
            print(f"✗ 数据库不存在: {db_path}")
            return
        
        # 显示数据库信息
        try:
            from .db_scanner import get_database_info
            info = get_database_info(str(db_path))
            print(f"\n数据库信息:")
            print(f"  名称: {info['name']}")
            print(f"  路径: {info['path']}")
            print(f"  记录数: {info['total_keys']}")
            print(f"  备注: {info['description'] if info['description'] else '(无)'}")
        except:
            pass
        
        # 确认删除
        print(f"\n警告: 这将删除整个数据库目录: {db_path}")
        print("此操作不可恢复！")
        confirm = input(f"确定要删除吗？请输入数据库名称 '{db_name}' 以确认: ").strip()
        
        if confirm != db_name:
            print("确认失败，已取消删除")
            return
        
        try:
            # 如果当前连接的是这个数据库，先断开
            if self.connected and self.data_dir:
                current_path = Path(self.data_dir).resolve()
                target_path = db_path.resolve()
                if current_path == target_path:
                    print("正在断开当前连接...")
                    self.do_disconnect("")
            
            # 删除目录
            shutil.rmtree(db_path)
            print(f"✓ 数据库已删除: {db_path}")
        except Exception as e:
            print(f"✗ 删除失败: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    def do_batch(self, args: str):
        """
        批量写入数据
        
        用法:
          batch put <key1> <value1> <key2> <value2> ...
          
        示例:
          batch put user:001 "data1" user:002 "data2" user:003 "data3"
        """
        if not self._check_connection():
            return
        
        parts = shlex.split(args)
        if len(parts) < 2 or parts[0] != 'put':
            print("用法: batch put <key1> <value1> <key2> <value2> ...")
            print("示例: batch put user:001 \"data1\" user:002 \"data2\"")
            return
        
        items = []
        for i in range(1, len(parts), 2):
            if i + 1 < len(parts):
                key = parts[i].encode()
                value = parts[i + 1].encode()
                items.append((key, value))
        
        if not items:
            print("✗ 错误: 没有提供键值对")
            return
        
        try:
            if self.is_remote:
                # 远程连接（批量写入需要逐个发送）
                success_count = 0
                for key, value in items:
                    if self.remote_db.put(key, value):
                        success_count += 1
                if success_count == len(items):
                    print(f"✓ 批量写入成功: {len(items)} 条记录")
                else:
                    print(f"✗ 批量写入部分成功: {success_count}/{len(items)} 条记录")
            else:
                # 本地连接
                success, merkle_root = self.db.batch_put(items)
                if success:
                    # 自动flush确保数据持久化
                    self.db.flush(async_mode=True)
                    print(f"✓ 批量写入成功: {len(items)} 条记录（已持久化）")
                    print(f"  Merkle根哈希: {merkle_root.hex()[:16]}...")
                else:
                    print("✗ 批量写入失败")
        except Exception as e:
            print(f"✗ 错误: {type(e).__name__}: {e}")
    
    def do_select(self, args: str):
        """
        查询数据（支持范围查询和分页）
        
        用法:
          select * from <prefix> [limit <n>]  - 查询所有以prefix开头的键（默认1000条，可指定limit）
          select <key>                         - 查询指定键
          
        示例:
          select * from user
          select * from block limit 5000
          select user:001
        """
        if not self._check_connection():
            return
        
        # 检查数据库文件状态（仅本地连接）
        if not self.is_remote and self.db:
            # 每次查询都检查文件状态，确保获取最新数据
            self.db.reload_if_files_changed()
        
        if not args:
            print("用法: select * from <prefix> 或 select <key>")
            print("示例: select * from user")
            print("      select user:001")
            return
        
        parts = args.strip().split()
        
        if len(parts) >= 3 and parts[0] == '*' and parts[1].lower() == 'from':
            # 范围查询: select * from <prefix> [limit <n>]
            prefix = parts[2]
            limit = None
            # 检查是否有limit参数
            if len(parts) >= 5 and parts[3].lower() == 'limit':
                try:
                    limit = int(parts[4])
                except (ValueError, IndexError):
                    pass
            try:
                if self.is_remote:
                    all_keys = self.remote_db.get_all_keys()
                else:
                    all_keys = self.db.version_manager.get_all_keys()
                
                # 支持两种匹配方式：
                # 1. 如果前缀包含':'，查找以 '<prefix>:' 开头的键
                # 2. 如果前缀不包含':'，查找以 '<prefix>' 开头的键（不要求有':'）
                if ':' in prefix:
                    # 用户明确指定了分隔符，使用精确匹配
                    matching_keys = [k for k in all_keys 
                                   if k.decode('utf-8', errors='ignore').startswith(prefix)]
                else:
                    # 没有分隔符，尝试两种匹配：
                    # - 以 '<prefix>:' 开头的键（有分隔符）
                    # - 以 '<prefix>' 开头的键（无分隔符，如 key00000000）
                    matching_keys = []
                    for k in all_keys:
                        key_str = k.decode('utf-8', errors='ignore')
                        if key_str.startswith(prefix + ':') or key_str.startswith(prefix):
                            matching_keys.append(k)
                
                if matching_keys:
                    total_count = len(matching_keys)
                    print(f"\n找到 {total_count} 条记录:")
                    print("-" * 80)
                    
                    # 使用limit参数或默认1000条
                    display_limit = limit if limit is not None else 1000
                    displayed = 0
                    
                    for key in matching_keys:
                        if displayed >= display_limit:
                            break
                        value = self.db.get(key)
                        # 过滤掉无效键（值为None的键）
                        if value is not None:
                            key_str = key.decode('utf-8', errors='ignore')
                            value_str = value.decode('utf-8', errors='ignore')
                            if len(value_str) > 50:
                                value_str = value_str[:50] + "..."
                            print(f"  {key_str}: {value_str}")
                            displayed += 1
                    
                    if total_count > display_limit:
                        print(f"  ... 还有 {total_count - display_limit} 条记录未显示")
                        print(f"提示: 使用 'select * from <prefix> limit <n>' 显示更多记录（例如: select * from {prefix} limit 5000）")
                    print("-" * 80)
                else:
                    print(f"✗ 未找到以 '{prefix}' 开头的键")
                    print(f"提示: 尝试使用 'select * from {prefix}:' 或检查键的前缀")
            except Exception as e:
                print(f"✗ 错误: {type(e).__name__}: {e}")
        else:
            # 单键查询: select <key>（使用格式化显示）
            key = args.strip().encode()
            try:
                # 检查并刷新数据（确保获取最新状态）
                if not self.is_remote:
                    self.db.reload_if_files_changed()
                value = self.db.get(key)
                if value:
                    key_str = key.decode('utf-8', errors='ignore')
                    print(f"✓ 找到数据:")
                    print(f"  Key: {key_str}")
                    print(f"  Value ({len(value)} bytes):")
                    print("-" * 80)
                    
                    # 使用ValueFormatter自动检测和格式化
                    formatted_value, format_type = ValueFormatter.format_value(value, max_length=5000)
                    
                    # 显示格式类型
                    format_labels = {
                        'json': 'JSON',
                        'xml': 'XML',
                        'binary': 'Binary (十六进制)',
                        'tree': 'Tree (键值对)',
                        'text': 'Text',
                        'unknown': 'Unknown'
                    }
                    format_label = format_labels.get(format_type, format_type)
                    print(f"  格式: {format_label}")
                    print()
                    
                    # 显示格式化后的值
                    print(formatted_value)
                    print("-" * 80)
                else:
                    print(f"✗ 未找到键: {key.decode('utf-8', errors='ignore')}")
            except Exception as e:
                print(f"✗ 错误: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
    
    def do_history(self, args: str):
        """
        查看键的历史版本
        
        用法:
          history <key>
          
        示例:
          history user:001
        """
        if not self._check_connection():
            return
        
        if not args:
            print("用法: history <key>")
            print("示例: history user:001")
            return
        
        key = args.strip().encode()
        
        try:
            history = self.db.get_history(key)
            if history:
                print(f"\n键 '{key.decode('utf-8', errors='ignore')}' 的历史版本:")
                print("-" * 80)
                for version in history:
                    print(f"  版本 {version['version']}:")
                    print(f"    时间戳: {version['timestamp']}")
                    print(f"    值: {version['value'].decode('utf-8', errors='ignore')[:50]}...")
                    if version.get('hash'):
                        print(f"    哈希: {version['hash'][:16]}...")
                    print()
                print("-" * 80)
            else:
                print(f"✗ 未找到键的历史版本: {key.decode('utf-8', errors='ignore')}")
        except Exception as e:
            print(f"✗ 错误: {type(e).__name__}: {e}")
    
    def do_flush(self, args: str):
        """
        强制刷新数据到磁盘
        
        用法:
          flush
        """
        if not self._check_connection():
            return
        
        try:
            self.db.flush()
            print("✓ 数据已刷新到磁盘")
        except Exception as e:
            print(f"✗ 错误: {type(e).__name__}: {e}")
    
    def do_clear(self, args: str):
        """
        清空屏幕
        
        用法:
          clear
        """
        os.system('clear' if os.name != 'nt' else 'cls')
    
    def do_exit(self, args: str):
        """退出CLI"""
        if self.connected:
            print(f"正在断开连接: {self.data_dir}")
        print("再见！")
        return True
    
    def do_quit(self, args: str):
        """退出CLI（同exit）"""
        return self.do_exit(args)
    
    def do_EOF(self, args: str):
        """处理EOF（Ctrl+D）"""
        print()
        return self.do_exit(args)
    
    def default(self, line: str):
        """处理未知命令"""
        print(f"✗ 未知命令: {line}")
        print("输入 'help' 查看可用命令")
    
    def emptyline(self):
        """处理空行"""
        pass


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='AmDb 命令行工具 (CLI)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 启动CLI（不连接数据库）
  amdb-cli
  
  # 启动CLI并连接到指定数据库
  amdb-cli --data-dir ./data/user_db
  
  # 启动CLI并使用指定配置
  amdb-cli --config ./amdb.ini --data-dir ./data/user_db
  
  # 在CLI中执行命令
  amdb-cli --data-dir ./data/user_db --command "show stats"
        """
    )
    
    parser.add_argument(
        '--data-dir', '-d',
        type=str,
        help='数据目录路径（单个数据库）'
    )
    
    parser.add_argument(
        '--data-root-dir', '-r',
        type=str,
        help='数据存储根目录路径（包含多个数据库的父目录）'
    )
    
    parser.add_argument(
        '--config', '-c',
        type=str,
        help='配置文件路径'
    )
    
    parser.add_argument(
        '--command', '-e',
        type=str,
        help='执行命令后退出（非交互模式）'
    )
    
    args = parser.parse_args()
    
    # 创建CLI实例
    cli = AmDbCLI(data_dir=args.data_dir, config_path=args.config, data_root_dir=args.data_root_dir)
    
    # 如果提供了命令，执行后退出
    if args.command:
        cli.onecmd(args.command)
        return
    
    # 启动交互式界面
    try:
        cli.cmdloop()
    except KeyboardInterrupt:
        print("\n\n中断，正在退出...")
        cli.do_exit("")


if __name__ == "__main__":
    main()
