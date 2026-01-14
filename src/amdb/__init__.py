# -*- coding: utf-8 -*-
"""
AmDb - Advanced Merkle Database
专为区块链应用设计的高性能数据库系统
"""

__version__ = "1.0.0"
__author__ = "AmDb Project"
__license__ = "MIT"

from .database import Database
from .config import DatabaseConfig, load_config

__all__ = [
    'Database',
    'DatabaseConfig',
    'load_config',
    '__version__',
]
