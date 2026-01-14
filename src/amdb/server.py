# -*- coding: utf-8 -*-
"""
AmDb 数据库服务器
提供网络服务接口
"""

import sys
import argparse
import signal
from pathlib import Path

def main():
    """服务器主函数"""
    parser = argparse.ArgumentParser(description='AmDb Database Server')
    parser.add_argument('--config', type=str, help='配置文件路径')
    parser.add_argument('--data-dir', type=str, help='数据目录路径')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='监听地址')
    parser.add_argument('--port', type=int, default=3888, help='监听端口')
    parser.add_argument('--daemon', action='store_true', help='后台运行')
    
    args = parser.parse_args()
    
    # 加载配置
    from .config import load_config
    config = load_config(args.config) if args.config else load_config()
    
    # 使用参数覆盖配置
    if args.data_dir:
        config.data_dir = args.data_dir
    if args.host:
        config.network_host = args.host
    if args.port:
        config.network_port = args.port
    
    # 创建数据库实例
    from .database import Database
    db = Database(data_dir=config.data_dir, config_path=args.config)
    
    print(f"AmDb 数据库服务器启动")
    print(f"数据目录: {db.data_dir}")
    print(f"监听地址: {config.network_host}:{config.network_port}")
    print(f"按 Ctrl+C 停止服务器")
    print("")
    
    # 信号处理
    def signal_handler(sig, frame):
        print("\n正在关闭服务器...")
        db.flush()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 启动网络服务
    try:
        from .network import DatabaseServer
        server = DatabaseServer(
            db, 
            host=config.network_host, 
            port=config.network_port
        )
        print(f"✓ 网络服务器已启动，监听 {config.network_host}:{config.network_port}")
        server.start()
        
        # 保持运行
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            signal_handler(None, None)
    except Exception as e:
        print(f"✗ 启动网络服务失败: {e}")
        print("数据库已就绪，仅提供本地访问")
        
        # 保持运行
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            signal_handler(None, None)

if __name__ == "__main__":
    main()

