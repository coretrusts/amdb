#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AmDb 桌面版数据库管理器启动脚本
类似phpMyAdmin的桌面版管理工具
"""

import sys
import os

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 设置PYTHONPATH
os.environ['PYTHONPATH'] = project_root

from src.amdb.gui_manager import DatabaseManagerGUI
import tkinter as tk

def main():
    """启动GUI管理器"""
    root = tk.Tk()
    app = DatabaseManagerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()

