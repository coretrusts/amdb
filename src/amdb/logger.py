"""
日志系统模块
支持多级别日志、文件轮转、异步写入
"""

import logging
import logging.handlers
import os
import sys
from typing import Optional
from pathlib import Path
from .config import LogConfig


class DatabaseLogger:
    """数据库日志管理器"""
    
    def __init__(self, config: LogConfig):
        self.config = config
        self.logger = logging.getLogger('amdb')
        self.logger.setLevel(getattr(logging, config.log_level))
        
        # 清除现有处理器
        self.logger.handlers.clear()
        
        # 控制台处理器
        if config.enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, config.log_level))
            console_formatter = logging.Formatter(config.log_format)
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
        
        # 文件处理器
        if config.enable_file:
            if config.log_file:
                log_path = Path(config.log_file)
            else:
                log_dir = Path(config.log_dir)
                log_dir.mkdir(parents=True, exist_ok=True)
                log_path = log_dir / "amdb.log"
            
            # 使用RotatingFileHandler支持文件轮转
            file_handler = logging.handlers.RotatingFileHandler(
                log_path,
                maxBytes=config.max_file_size,
                backupCount=config.backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(getattr(logging, config.log_level))
            file_formatter = logging.Formatter(config.log_format)
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
    
    def debug(self, message: str, *args, **kwargs):
        """调试日志"""
        self.logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """信息日志"""
        self.logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """警告日志"""
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """错误日志"""
        self.logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """严重错误日志"""
        self.logger.critical(message, *args, **kwargs)
    
    def exception(self, message: str, *args, **kwargs):
        """异常日志（包含堆栈）"""
        self.logger.exception(message, *args, **kwargs)


# 全局日志实例
_logger_instance: Optional[DatabaseLogger] = None


def get_logger(config: Optional[LogConfig] = None) -> DatabaseLogger:
    """获取日志实例"""
    global _logger_instance
    if _logger_instance is None:
        if config is None:
            from .config import default_config
            config = default_config.log
        _logger_instance = DatabaseLogger(config)
    return _logger_instance


def set_logger(logger: DatabaseLogger):
    """设置日志实例"""
    global _logger_instance
    _logger_instance = logger

