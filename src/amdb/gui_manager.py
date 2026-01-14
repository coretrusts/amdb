# -*- coding: utf-8 -*-
"""
AmDb 桌面版数据库管理器
类似phpMyAdmin的桌面版管理工具
使用tkinter实现跨平台GUI
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import json
import time
import os
from typing import Optional, Dict, Any, List
from pathlib import Path
from .database import Database
from .config import load_config


class DatabaseManagerGUI:
    """AmDb桌面版数据库管理器"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("AmDb 数据库管理器")
        self.root.geometry("1200x800")
        
        self.db: Optional[Database] = None
        self.remote_db: Optional[RemoteDatabase] = None
        self.db_wrapper: Optional[DatabaseWrapper] = None  # 统一接口包装器
        self.config_path: Optional[str] = None
        self.data_dir: Optional[str] = None
        self.host: Optional[str] = None
        self.port: Optional[int] = None
        self.database: Optional[str] = None
        self.is_remote = False  # 是否为远程连接
        
        # 创建菜单栏
        self._create_menu()
        
        # 创建主界面
        self._create_main_ui()
        
        # 状态栏
        self._create_status_bar()
        
    def _create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="连接数据库", command=self._connect_database)
        file_menu.add_command(label="断开连接", command=self._disconnect_database)
        file_menu.add_separator()
        file_menu.add_command(label="加载配置", command=self._load_config)
        file_menu.add_command(label="保存配置", command=self._save_config)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        
        # 数据菜单
        data_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="数据", menu=data_menu)
        data_menu.add_command(label="插入数据", command=self._add_record)
        data_menu.add_command(label="批量导入", command=self._batch_import)
        data_menu.add_command(label="导出数据", command=self._export_data)
        data_menu.add_separator()
        data_menu.add_command(label="清空数据", command=self._clear_data)
        
        # 查询菜单
        query_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="查询", menu=query_menu)
        query_menu.add_command(label="执行查询", command=self._execute_query)
        query_menu.add_command(label="查询历史", command=self._query_history)
        
        # 工具菜单
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具", menu=tools_menu)
        tools_menu.add_command(label="数据库统计", command=self._show_stats)
        tools_menu.add_command(label="性能监控", command=self._show_metrics)
        tools_menu.add_command(label="备份数据库", command=self._backup_database)
        tools_menu.add_command(label="恢复数据库", command=self._restore_database)
        tools_menu.add_separator()
        tools_menu.add_command(label="压缩数据库", command=self._compact_database)
        tools_menu.add_command(label="优化数据库", command=self._optimize_database)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用说明", command=self._show_help)
        help_menu.add_command(label="关于", command=self._show_about)
    
    def _create_main_ui(self):
        """创建主界面"""
        # 创建Notebook（标签页）
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 标签页1：数据浏览
        self._create_browse_tab()
        
        # 标签页2：查询执行
        self._create_query_tab()
        
        # 标签页3：配置管理
        self._create_config_tab()
        
        # 标签页4：性能监控
        self._create_metrics_tab()
    
    def _create_browse_tab(self):
        """创建数据浏览标签页"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="数据浏览")
        
        # 工具栏
        toolbar = ttk.Frame(frame)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text="刷新", command=self._refresh_data).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="添加", command=self._add_record).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="编辑", command=self._edit_record).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="删除", command=self._delete_record).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="搜索", command=self._search_data).pack(side=tk.LEFT, padx=2)
        
        # 搜索框
        search_frame = ttk.Frame(toolbar)
        search_frame.pack(side=tk.RIGHT, padx=5)
        ttk.Label(search_frame, text="搜索:").pack(side=tk.LEFT)
        self.search_entry = ttk.Entry(search_frame, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=2)
        # 绑定回车键和输入事件（实时搜索）
        self.search_entry.bind('<Return>', lambda e: self._search_data())
        self.search_entry.bind('<KeyRelease>', lambda e: self._on_search_change())
        
        # 搜索选项
        self.search_mode = tk.StringVar(value="both")  # both, key, value
        search_mode_frame = ttk.Frame(search_frame)
        search_mode_frame.pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(search_mode_frame, text="全部", variable=self.search_mode, value="both").pack(side=tk.LEFT)
        ttk.Radiobutton(search_mode_frame, text="键", variable=self.search_mode, value="key").pack(side=tk.LEFT)
        ttk.Radiobutton(search_mode_frame, text="值", variable=self.search_mode, value="value").pack(side=tk.LEFT)
        
        ttk.Button(search_frame, text="搜索", command=self._search_data).pack(side=tk.LEFT, padx=2)
        ttk.Button(search_frame, text="清除", command=self._clear_search).pack(side=tk.LEFT, padx=2)
        
        # 加载更多按钮
        self.load_more_btn = ttk.Button(search_frame, text="加载更多", command=self._load_more_data)
        self.load_more_btn.pack(side=tk.LEFT, padx=2)
        
        # 显示数量配置
        ttk.Label(search_frame, text="每页显示:").pack(side=tk.LEFT, padx=(10, 2))
        self.page_size_var = tk.StringVar(value="1000")
        page_size_combo = ttk.Combobox(search_frame, textvariable=self.page_size_var, 
                                       values=["500", "1000", "2000", "5000", "10000", "全部"],
                                       width=8, state='readonly')
        page_size_combo.pack(side=tk.LEFT, padx=2)
        page_size_combo.bind('<<ComboboxSelected>>', lambda e: self._refresh_data())
        
        # 数据表格
        table_frame = ttk.Frame(frame)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建Treeview
        columns = ("Key", "Value", "Version", "Timestamp")
        self.data_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)
        
        # 设置列标题和宽度
        self.data_tree.heading("Key", text="键")
        self.data_tree.heading("Value", text="值")
        self.data_tree.heading("Version", text="版本")
        self.data_tree.heading("Timestamp", text="时间戳")
        
        self.data_tree.column("Key", width=300)
        self.data_tree.column("Value", width=400)
        self.data_tree.column("Version", width=100)
        self.data_tree.column("Timestamp", width=200)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.data_tree.yview)
        self.data_tree.configure(yscrollcommand=scrollbar.set)
        
        self.data_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 双击查看详情或编辑
        self.data_tree.bind("<Double-1>", lambda e: self._view_record_detail())
    
    def _create_query_tab(self):
        """创建查询执行标签页"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="查询执行")
        
        # 帮助提示区域
        help_frame = ttk.LabelFrame(frame, text="查询语法帮助")
        help_frame.pack(fill=tk.X, padx=5, pady=5)
        
        help_text = """支持的命令（不区分大小写）:
  GET <key>                    - 读取数据
  PUT <key> <value>            - 写入数据
  DELETE <key>                - 删除数据（标记删除）
  BATCH PUT <key1> <value1> <key2> <value2> ...  - 批量写入
  SELECT * FROM <prefix>      - 查询所有以prefix开头的键
  SELECT <key>                - 查询指定键（等同于GET）
  
示例:
  GET user:001
  PUT user:002 "{\"name\": \"张三\"}"
  BATCH PUT user:003 "data1" user:004 "data2"
  SELECT * FROM user
  SELECT transaction:001"""
        
        help_label = ttk.Label(help_frame, text=help_text, font=("Courier", 9), justify=tk.LEFT)
        help_label.pack(padx=5, pady=5, anchor=tk.W)
        
        # SQL输入区域
        input_frame = ttk.LabelFrame(frame, text="查询输入")
        input_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.query_text = scrolledtext.ScrolledText(input_frame, height=10, wrap=tk.WORD, font=("Courier", 10))
        self.query_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 工具栏
        toolbar = ttk.Frame(input_frame)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text="执行查询", command=self._execute_query).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="清空", command=lambda: self.query_text.delete(1.0, tk.END)).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="保存查询", command=self._save_query).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="加载查询", command=self._load_query).pack(side=tk.LEFT, padx=2)
        
        # 结果区域
        result_frame = ttk.LabelFrame(frame, text="查询结果")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 结果表格
        result_table_frame = ttk.Frame(result_frame)
        result_table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 定义列
        columns = ("key", "value", "status")
        self.result_tree = ttk.Treeview(result_table_frame, columns=columns, show="headings", height=15)
        self.result_tree.heading("key", text="键 (Key)")
        self.result_tree.heading("value", text="值 (Value)")
        self.result_tree.heading("status", text="状态")
        self.result_tree.column("key", width=300)
        self.result_tree.column("value", width=400)
        self.result_tree.column("status", width=100)
        
        result_scrollbar = ttk.Scrollbar(result_table_frame, orient=tk.VERTICAL, command=self.result_tree.yview)
        self.result_tree.configure(yscrollcommand=result_scrollbar.set)
        
        self.result_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        result_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 状态信息
        self.query_status = ttk.Label(result_frame, text="就绪")
        self.query_status.pack(side=tk.BOTTOM, padx=5, pady=5)
    
    def _create_config_tab(self):
        """创建配置管理标签页"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="配置管理")
        
        # 配置信息显示
        info_frame = ttk.LabelFrame(frame, text="配置信息")
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.config_info_label = ttk.Label(info_frame, text="未连接数据库", foreground='gray')
        self.config_info_label.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 配置文本编辑器
        config_frame = ttk.LabelFrame(frame, text="配置文件 (database.ini)")
        config_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.config_text = scrolledtext.ScrolledText(config_frame, wrap=tk.NONE, font=('Courier', 10))
        self.config_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 工具栏
        toolbar = ttk.Frame(config_frame)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text="从数据库加载", command=self._load_config_from_db).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="从文件加载", command=self._load_config_from_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="保存到数据库", command=self._save_config_to_db).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="导出到文件", command=self._export_config_to_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="重置为默认", command=self._reset_config).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="验证配置", command=self._validate_config).pack(side=tk.LEFT, padx=2)
    
    def _create_metrics_tab(self):
        """创建性能监控标签页"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="性能监控")
        
        # 指标显示区域
        metrics_frame = ttk.LabelFrame(frame, text="实时指标")
        metrics_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建指标显示
        self.metrics_text = scrolledtext.ScrolledText(metrics_frame, height=20, wrap=tk.WORD)
        self.metrics_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 工具栏
        toolbar = ttk.Frame(metrics_frame)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text="开始监控", command=self._start_monitoring).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="停止监控", command=self._stop_monitoring).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="刷新", command=self._refresh_metrics).pack(side=tk.LEFT, padx=2)
        
        self.monitoring = False
    
    def _create_status_bar(self):
        """创建状态栏"""
        self.status_bar = ttk.Label(self.root, text="未连接", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def _connect_database(self):
        """连接数据库"""
        dialog = tk.Toplevel(self.root)
        dialog.title("连接数据库")
        dialog.geometry("700x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 自动扫描数据库
        from .db_scanner import scan_databases
        databases = scan_databases('./data')
        
        # 数据库列表（自动扫描 + 预设）
        ttk.Label(dialog, text="数据库列表（自动扫描）:").grid(row=0, column=0, columnspan=3, padx=5, pady=5, sticky=tk.W)
        
        # 创建Treeview显示数据库列表
        tree_frame = ttk.Frame(dialog)
        tree_frame.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky=tk.W+tk.E+tk.N+tk.S)
        
        db_tree = ttk.Treeview(tree_frame, columns=('path', 'keys', 'description'), show='tree headings', height=8)
        db_tree.heading('#0', text='数据库名称')
        db_tree.heading('path', text='路径')
        db_tree.heading('keys', text='记录数')
        db_tree.heading('description', text='备注')
        
        db_tree.column('#0', width=150)
        db_tree.column('path', width=200)
        db_tree.column('keys', width=80)
        db_tree.column('description', width=200)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=db_tree.yview)
        db_tree.configure(yscrollcommand=scrollbar.set)
        
        db_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 填充数据库列表
        for db in databases:
            db_tree.insert('', tk.END, 
                          text=db['name'],
                          values=(db['path'], 
                                 db['total_keys'] if db['total_keys'] > 0 else '未知',
                                 db['description'] if db['description'] else '(无备注)'))
        
        def on_db_select(event):
            selection = db_tree.selection()
            if selection:
                item = db_tree.item(selection[0])
                path = item['values'][0]
                data_dir_entry.delete(0, tk.END)
                data_dir_entry.insert(0, path)
                
                # 如果选中了数据库，显示备注
                description = item['values'][2] if len(item['values']) > 2 else ''
                if description and description != '(无备注)':
                    desc_label.config(text=f"备注: {description}")
                else:
                    desc_label.config(text="")
        
        db_tree.bind('<<TreeviewSelect>>', on_db_select)
        
        # 备注显示
        desc_label = ttk.Label(dialog, text="", foreground='gray')
        desc_label.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky=tk.W)
        
        # 刷新按钮
        def refresh_list():
            databases = scan_databases('./data')
            # 清空现有项
            for item in db_tree.get_children():
                db_tree.delete(item)
            # 重新填充
            for db in databases:
                db_tree.insert('', tk.END, 
                              text=db['name'],
                              values=(db['path'], 
                                     db['total_keys'] if db['total_keys'] > 0 else '未知',
                                     db['description'] if db['description'] else '(无备注)'))
        
        ttk.Button(dialog, text="刷新列表", command=refresh_list).grid(row=0, column=2, padx=5, pady=5, sticky=tk.E)
        
        # 分隔线
        ttk.Separator(dialog, orient=tk.HORIZONTAL).grid(row=3, column=0, columnspan=3, sticky=tk.W+tk.E, padx=5, pady=10)
        
        # 连接模式选择
        ttk.Label(dialog, text="连接模式:").grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)
        connection_mode = tk.StringVar(value="local")
        ttk.Radiobutton(dialog, text="本地文件", variable=connection_mode, value="local").grid(row=4, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Radiobutton(dialog, text="远程服务器", variable=connection_mode, value="remote").grid(row=4, column=1, padx=5, pady=5, sticky=tk.E)
        
        # 本地连接输入区域
        local_frame = ttk.LabelFrame(dialog, text="本地连接")
        local_frame.grid(row=5, column=0, columnspan=3, padx=5, pady=5, sticky=tk.W+tk.E)
        
        ttk.Label(local_frame, text="数据目录:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        data_dir_entry = ttk.Entry(local_frame, width=50)
        data_dir_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
        data_dir_entry.insert(0, "./data/sample_db")
        
        # 浏览按钮
        def browse_data_dir():
            dir_path = filedialog.askdirectory(title="选择数据目录", initialdir="./data")
            if dir_path:
                data_dir_entry.delete(0, tk.END)
                data_dir_entry.insert(0, dir_path)
        
        ttk.Button(local_frame, text="浏览...", command=browse_data_dir).grid(row=0, column=2, padx=5, pady=5)
        
        # 远程连接输入区域
        remote_frame = ttk.LabelFrame(dialog, text="远程连接")
        remote_frame.grid(row=6, column=0, columnspan=3, padx=5, pady=5, sticky=tk.W+tk.E)
        
        ttk.Label(remote_frame, text="服务器地址:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        host_entry = ttk.Entry(remote_frame, width=30)
        host_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        host_entry.insert(0, "127.0.0.1")
        
        ttk.Label(remote_frame, text="端口:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        port_entry = ttk.Entry(remote_frame, width=10)
        port_entry.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        port_entry.insert(0, "3888")
        
        ttk.Label(remote_frame, text="数据库名称:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        database_entry = ttk.Entry(remote_frame, width=30)
        database_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        database_entry.insert(0, "default")
        
        # 切换连接模式
        def switch_mode():
            if connection_mode.get() == "local":
                local_frame.grid()
                remote_frame.grid_remove()
            else:
                local_frame.grid_remove()
                remote_frame.grid()
        
        connection_mode.trace_add('write', lambda *args: switch_mode())
        switch_mode()  # 初始显示
        
        # 手动输入
        ttk.Label(dialog, text="或手动输入:").grid(row=7, column=0, columnspan=3, padx=5, pady=5, sticky=tk.W)
        
        # 数据库备注（新建或更新时使用）
        ttk.Label(dialog, text="数据库备注:").grid(row=8, column=0, padx=5, pady=5, sticky=tk.W)
        description_entry = ttk.Entry(dialog, width=50)
        description_entry.grid(row=8, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
        description_entry.insert(0, "")
        
        # 如果选中了已有数据库，显示其备注
        def update_description():
            path = data_dir_entry.get().strip()
            if path:
                from .db_scanner import get_database_info
                info = get_database_info(path)
                if info['description']:
                    description_entry.delete(0, tk.END)
                    description_entry.insert(0, info['description'])
        
        data_dir_entry.bind('<FocusOut>', lambda e: update_description())
        
        def connect():
            try:
                mode = connection_mode.get()
                description = description_entry.get().strip()
                
                if mode == "remote":
                    # 远程连接
                    host = host_entry.get().strip()
                    port_str = port_entry.get().strip()
                    database = database_entry.get().strip() or "default"
                    
                    if not host:
                        messagebox.showerror("错误", "请输入服务器地址")
                        return
                    
                    try:
                        port = int(port_str)
                    except ValueError:
                        messagebox.showerror("错误", "端口必须是数字")
                        return
                    
                    print(f"[GUI调试] 连接远程数据库: {host}:{port}/{database}")
                    
                    try:
                        self.remote_db = RemoteDatabase(host=host, port=port, database=database)
                        if self.remote_db.connect():
                            self.is_remote = True
                            self.db = None
                            self.host = host
                            self.port = port
                            self.database = database
                            self.data_dir = None
                            self.config_path = None
                            # 创建统一接口包装器
                            self.db_wrapper = DatabaseWrapper(remote_db=self.remote_db)
                            
                            self._update_status(f"已连接: {host}:{port}/{database}")
                            dialog.destroy()
                            messagebox.showinfo("成功", f"远程数据库连接成功！\n\n服务器: {host}:{port}\n数据库: {database}")
                            self._refresh_data()
                        else:
                            messagebox.showerror("错误", f"无法连接到服务器 {host}:{port}")
                    except Exception as e:
                        messagebox.showerror("错误", f"连接失败: {str(e)}")
                        import traceback
                        traceback.print_exc()
                    return
                
                # 本地连接
                config_path = None
                data_dir = data_dir_entry.get().strip() or None
                
                if config_path and not os.path.exists(config_path):
                    messagebox.showerror("错误", f"配置文件不存在: {config_path}")
                    return
                
                if data_dir and not os.path.exists(data_dir):
                    # 数据目录不存在，询问是否创建
                    if messagebox.askyesno("确认", f"数据目录不存在: {data_dir}\n是否创建新数据库？"):
                        os.makedirs(data_dir, exist_ok=True)
                    else:
                        return
                
                # 创建数据库连接（确保数据从磁盘加载）
                print(f"[GUI调试] 创建数据库连接...")
                print(f"[GUI调试] config_path={config_path}, data_dir={data_dir}")
                
                try:
                    if config_path:
                        self.db = Database(config_path=config_path)
                        print(f"[GUI调试] 使用配置文件创建数据库")
                    elif data_dir:
                        self.db = Database(data_dir=data_dir)
                        print(f"[GUI调试] 使用数据目录创建数据库: {data_dir}")
                    else:
                        self.db = Database()
                        print(f"[GUI调试] 使用默认配置创建数据库")
                    
                    self.is_remote = False
                    self.remote_db = None
                    self.host = None
                    self.port = None
                    self.database = None
                    self.config_path = config_path
                    self.data_dir = data_dir if data_dir else self.db.data_dir
                    # 创建统一接口包装器
                    self.db_wrapper = DatabaseWrapper(db=self.db)
                    
                    # 强制等待一下，确保数据加载完成
                    import time
                    time.sleep(0.2)  # 增加等待时间
                    
                    print(f"[GUI调试] 数据库连接创建完成")
                    
                    # 验证数据加载（重要：确保版本管理器已加载数据）
                    print(f"[GUI调试] 验证数据加载...")
                    print(f"[GUI调试] 数据目录: {self.db.data_dir}")
                    
                    # 检查版本文件是否存在
                    from pathlib import Path
                    ver_file = Path(self.db.data_dir) / "versions" / "versions.ver"
                    print(f"[GUI调试] 版本文件路径: {ver_file}")
                    print(f"[GUI调试] 版本文件存在: {ver_file.exists()}")
                    
                    if ver_file.exists():
                        size = os.path.getsize(ver_file)
                        print(f"[GUI调试] 版本文件大小: {size} bytes")
                    
                    # 检查版本管理器中的键数量（增加重试机制）
                    key_count = 0
                    all_keys = []
                    max_retries = 3
                    try:
                        for retry in range(max_retries):
                            try:
                                if self.is_remote:
                                    all_keys = self.remote_db.get_all_keys()
                                else:
                                    all_keys = self.db.version_manager.get_all_keys()
                                key_count = len(all_keys)
                                print(f"[GUI调试] 第{retry+1}次检查键数量: {key_count}")
                                
                                if key_count > 0:
                                    break  # 成功获取，退出重试循环
                                
                                # 如果键数量为0但文件存在，尝试重新加载（仅本地）
                                if key_count == 0 and not self.is_remote and ver_file.exists() and retry < max_retries - 1:
                                    print(f"[GUI调试] 键数量为0但文件存在，尝试重新加载...")
                                    import time
                                    time.sleep(0.1)  # 等待一下
                                    self.db.version_manager.load_from_disk(self.db.data_dir)
                                    all_keys = self.db.version_manager.get_all_keys()
                                    key_count = len(all_keys)
                                    print(f"[GUI调试] 重新加载后键数量: {key_count}")
                                    
                                    if key_count > 0:
                                        break
                            except Exception as e:
                                print(f"[GUI调试] 第{retry+1}次检查失败: {e}")
                                if retry < max_retries - 1:
                                    import time
                                    time.sleep(0.2)  # 等待后重试
                                else:
                                    raise
                        
                        # 测试读取一个键（如果有）
                        if all_keys:
                            test_key = all_keys[0]
                            test_value = self.db.get(test_key)
                            print(f"[GUI调试] 测试读取: {test_key.decode('utf-8', errors='ignore')} = {test_value}")
                    except Exception as e:
                        print(f"[GUI调试] 检查键数量时出错: {e}")
                        import traceback
                        traceback.print_exc()
                    
                    # 如果提供了备注，设置备注
                    if description:
                        try:
                            self.db.set_description(description)
                            print(f"[GUI调试] 已设置数据库备注: {description}")
                        except Exception as e:
                            print(f"[GUI调试] 设置备注失败: {e}")
                    
                    self._update_status(f"已连接: {self.data_dir} (共 {key_count} 条记录)")
                    
                    dialog.destroy()
                    messagebox.showinfo("成功", f"数据库连接成功！\n\n数据目录: {self.data_dir}\n记录数: {key_count if key_count > 0 else '未知'}\n备注: {description if description else '(无)'}\n\n如果看不到数据，请点击刷新按钮。")
                    
                    # 连接成功后自动刷新数据和配置
                    print(f"[GUI调试] 连接成功，开始刷新数据...")
                    self._refresh_data()
                    # 自动加载数据库配置到配置标签页
                    self._load_config_from_db_auto()
                    
                except Exception as e:
                    print(f"[GUI调试] 创建数据库连接时出错: {e}")
                    import traceback
                    traceback.print_exc()
                    messagebox.showerror("错误", f"连接失败: {str(e)}\n\n请查看控制台获取详细信息。")
            except Exception as e:
                messagebox.showerror("错误", f"连接失败: {str(e)}")
                import traceback
                traceback.print_exc()
        
        ttk.Button(dialog, text="连接", command=connect).grid(row=9, column=2, padx=5, pady=10, sticky=tk.E)
        ttk.Button(dialog, text="取消", command=dialog.destroy).grid(row=9, column=1, padx=5, pady=10, sticky=tk.E)
        
        # 配置列权重
        dialog.columnconfigure(1, weight=1)
    
    def _disconnect_database(self):
        """断开数据库连接"""
        if self.db:
            db_name = self.data_dir if self.data_dir else "数据库"
            self.db = None
            self.data_dir = None
            self._update_status("未连接")
            self.data_tree.delete(*self.data_tree.get_children())
            messagebox.showinfo("成功", f"已断开连接: {db_name}")
        else:
            messagebox.showinfo("提示", "当前未连接任何数据库")
    
    def _refresh_data(self, load_more=False):
        """刷新数据
        
        Args:
            load_more: 如果为True，继续加载更多数据；如果为False，从头开始加载
        """
        if not self.db and not self.remote_db:
            messagebox.showwarning("警告", "请先连接数据库")
            return
        
        try:
            # 获取统计信息
            try:
                if self.is_remote:
                    stats = self.remote_db.get_stats()
                else:
                    stats = self.db.get_stats()
                
                if stats:
                    total_keys = stats.get('total_keys', 0)
                    print(f"[GUI调试] 统计信息: 总键数={total_keys}")
                else:
                    total_keys = 0
                    print(f"[GUI调试] 无法获取统计信息")
            except Exception as e:
                print(f"[GUI调试] 获取统计信息失败: {e}")
                import traceback
                traceback.print_exc()
                total_keys = 0
            
            # 从版本管理器获取所有键（用于显示）
            try:
                print(f"[GUI调试] 开始获取所有键...")
                all_keys = self.db_wrapper.get_all_keys()
                print(f"[GUI调试] 获取到 {len(all_keys)} 个键")
                
                if not all_keys:
                    # 如果没有键，显示提示信息
                    print("[GUI调试] 数据库为空，没有键")
                    self._update_status("数据库为空，没有记录")
                    messagebox.showinfo("提示", "数据库为空，没有记录。\n\n请先使用PUT命令或添加按钮写入数据。")
                    return
                
                display_count = 0
                error_count = 0
                
                # 获取显示数量配置
                page_size_str = self.page_size_var.get() if hasattr(self, 'page_size_var') else "1000"
                if page_size_str == "全部":
                    max_display = len(all_keys)
                else:
                    max_display = int(page_size_str)
                
                # 获取已显示的数量（用于"加载更多"功能）
                if not load_more:
                    # 不是加载更多，清空现有数据，从头开始
                    self.data_tree.delete(*self.data_tree.get_children())
                    start_idx = 0
                else:
                    # 加载更多，从当前位置继续
                    start_idx = len(self.data_tree.get_children())
                
                end_idx = min(start_idx + max_display, len(all_keys))
                
                print(f"[GUI调试] 开始处理 {start_idx} 到 {end_idx} 的键（共 {len(all_keys)} 个）...")
                
                for idx, key in enumerate(all_keys[start_idx:end_idx]):
                    actual_idx = start_idx + idx
                    try:
                        # 读取值
                        value = self.db_wrapper.get(key)
                        
                        if value:
                            # 获取版本信息
                            try:
                                latest = self.db.version_manager.get_latest(key)
                                version = latest.version if latest else 0
                                timestamp = latest.timestamp if latest else 0
                            except Exception as e:
                                print(f"[GUI调试] 获取版本信息失败 (键={key}): {e}")
                                version = 0
                                timestamp = 0
                            
                            # 格式化显示
                            try:
                                key_str = key.decode('utf-8', errors='ignore')
                            except:
                                key_str = key.hex()[:50]
                            
                            # 使用值格式化器获取预览
                            from .value_formatter import ValueFormatter
                            format_type = ValueFormatter.detect_format(value)
                            value_str = ValueFormatter.get_preview(value, max_length=50)
                            
                            # 添加格式标识
                            if format_type == 'json':
                                value_str = f"[JSON] {value_str}"
                            elif format_type == 'xml':
                                value_str = f"[XML] {value_str}"
                            elif format_type == 'binary':
                                value_str = f"[Binary] {value_str}"
                            elif format_type == 'tree':
                                value_str = f"[Tree] {value_str}"
                            
                            timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp)) if timestamp > 0 else "N/A"
                            
                            # 插入到树视图
                            self.data_tree.insert("", tk.END, values=(key_str, value_str, version, timestamp_str))
                            display_count += 1
                            
                            # 每100条输出一次进度
                            if (idx + 1) % 100 == 0:
                                print(f"[GUI调试] 已处理 {actual_idx + 1}/{len(all_keys)} 条记录")
                        else:
                            # 如果get返回None，仍然显示键
                            try:
                                key_str = key.decode('utf-8', errors='ignore')
                            except:
                                key_str = key.hex()[:50]
                            self.data_tree.insert("", tk.END, values=(key_str, "(值未找到)", 0, "N/A"))
                            display_count += 1
                            error_count += 1
                            print(f"[GUI调试] 警告: 键 {key_str} 的值未找到")
                    except Exception as e:
                        # 记录错误但继续处理其他键
                        error_count += 1
                        try:
                            key_str = key.decode('utf-8', errors='ignore') if 'key' in locals() else 'unknown'
                        except:
                            key_str = 'unknown'
                        print(f"[GUI调试] 处理键时出错 (键={key_str}): {e}")
                        import traceback
                        traceback.print_exc()
                        continue
                
                print(f"[GUI调试] 处理完成: 成功={display_count}, 错误={error_count}")
                
                # 更新状态栏和"加载更多"按钮
                total_displayed = len(self.data_tree.get_children())
                if total_displayed < len(all_keys):
                    remaining = len(all_keys) - total_displayed
                    self._update_status(f"已显示 {total_displayed}/{len(all_keys)} 条记录（还有 {remaining} 条未显示）")
                    # 显示"加载更多"按钮
                    if hasattr(self, 'load_more_btn'):
                        self.load_more_btn.config(state=tk.NORMAL)
                else:
                    self._update_status(f"已显示全部 {len(all_keys)} 条记录")
                    # 隐藏"加载更多"按钮
                    if hasattr(self, 'load_more_btn'):
                        self.load_more_btn.config(state=tk.DISABLED)
                
                if error_count > 0:
                    messagebox.showwarning("警告", f"加载数据时遇到 {error_count} 个错误，部分数据可能未正确显示。\n\n请查看控制台获取详细信息。")
                
            except Exception as e:
                # 如果无法获取所有键，显示详细错误信息
                import traceback
                error_msg = f"无法加载数据: {str(e)}"
                print(f"[GUI调试] {error_msg}")
                traceback.print_exc()
                self._update_status(f"总记录数: {total_keys}（{error_msg}）")
                messagebox.showerror("错误", f"刷新数据失败:\n{error_msg}\n\n请检查:\n1. 数据库是否正确连接\n2. 数据文件是否存在\n3. 查看控制台获取详细错误信息")
            
        except Exception as e:
            import traceback
            error_msg = f"刷新失败: {str(e)}"
            print(f"[GUI调试] {error_msg}")
            traceback.print_exc()
            messagebox.showerror("错误", f"刷新数据时发生异常:\n{error_msg}\n\n请查看控制台获取详细信息。")
    
    def _add_record(self):
        """添加记录"""
        if not self.db and not self.remote_db:
            messagebox.showwarning("警告", "请先连接数据库")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("添加记录")
        dialog.geometry("500x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="键:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        key_entry = ttk.Entry(dialog, width=50)
        key_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(dialog, text="值:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        value_entry = ttk.Entry(dialog, width=50)
        value_entry.grid(row=1, column=1, padx=5, pady=5)
        
        def save():
            try:
                key = key_entry.get().encode()
                value = value_entry.get().encode()
                success, _ = self.db_wrapper.put(key, value)
                if success:
                    # 刷新数据到磁盘，确保CLI可以看到
                    self.db.flush()
                    messagebox.showinfo("成功", "记录添加成功！")
                    self._refresh_data()
                    dialog.destroy()
                else:
                    messagebox.showerror("错误", "添加失败")
            except Exception as e:
                messagebox.showerror("错误", f"添加失败: {str(e)}")
        
        ttk.Button(dialog, text="保存", command=save).grid(row=2, column=1, padx=5, pady=10, sticky=tk.E)
        ttk.Button(dialog, text="取消", command=dialog.destroy).grid(row=2, column=0, padx=5, pady=10, sticky=tk.W)
    
    def _view_record_detail(self):
        """查看记录详情（支持多种格式显示）"""
        selection = self.data_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要查看的记录")
            return
        
        # 获取选中的记录
        item = self.data_tree.item(selection[0])
        key = item['values'][0]
        
        # 获取当前值
        if not self.db and not self.remote_db:
            return
        
        try:
            value = self.db_wrapper.get(key.encode())
            if not value:
                messagebox.showinfo("提示", "该记录没有值")
                return
            
            # 创建详情对话框
            dialog = tk.Toplevel(self.root)
            dialog.title(f"记录详情: {key}")
            dialog.geometry("800x600")
            dialog.transient(self.root)
            
            # 使用值格式化器格式化值
            from .value_formatter import ValueFormatter
            formatted_value, format_type = ValueFormatter.format_value(value, max_length=10000)
            
            # 格式选择器
            format_frame = ttk.Frame(dialog)
            format_frame.pack(fill=tk.X, padx=5, pady=5)
            
            ttk.Label(format_frame, text="格式:").pack(side=tk.LEFT, padx=5)
            format_var = tk.StringVar(value=format_type)
            format_combo = ttk.Combobox(format_frame, textvariable=format_var, 
                                       values=['auto', 'json', 'xml', 'binary', 'tree', 'text'],
                                       state='readonly', width=10)
            format_combo.pack(side=tk.LEFT, padx=5)
            
            # 文本显示区域
            text_frame = ttk.Frame(dialog)
            text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            text_widget = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, font=("Courier", 10))
            text_widget.pack(fill=tk.BOTH, expand=True)
            text_widget.insert(1.0, formatted_value)
            text_widget.config(state=tk.DISABLED)
            
            def on_format_change(event=None):
                """格式改变时重新格式化"""
                selected_format = format_var.get()
                if selected_format == 'auto':
                    new_formatted, detected = ValueFormatter.format_value(value, max_length=10000)
                else:
                    new_formatted, detected = ValueFormatter.format_value(value, format_type=selected_format, max_length=10000)
                
                text_widget.config(state=tk.NORMAL)
                text_widget.delete(1.0, tk.END)
                text_widget.insert(1.0, new_formatted)
                text_widget.config(state=tk.DISABLED)
            
            format_combo.bind('<<ComboboxSelected>>', on_format_change)
            
            # 按钮
            button_frame = ttk.Frame(dialog)
            button_frame.pack(fill=tk.X, padx=5, pady=5)
            
            def edit_record():
                dialog.destroy()
                self._edit_record()
            
            ttk.Button(button_frame, text="编辑", command=edit_record).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="关闭", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
            
        except Exception as e:
            messagebox.showerror("错误", f"获取记录失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _edit_record(self):
        """编辑记录"""
        selection = self.data_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要编辑的记录")
            return
        
        # 获取选中的记录
        item = self.data_tree.item(selection[0])
        key = item['values'][0]
        
        # 获取当前值
        if not self.db and not self.remote_db:
            return
        
        try:
            value = self.db_wrapper.get(key.encode())
            if value:
                # 创建编辑对话框（支持多格式）
                dialog = tk.Toplevel(self.root)
                dialog.title(f"编辑记录: {key}")
                dialog.geometry("600x400")
                dialog.transient(self.root)
                dialog.grab_set()
                
                ttk.Label(dialog, text="键:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
                key_entry = ttk.Entry(dialog, width=50)
                key_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
                key_entry.insert(0, key)
                key_entry.config(state=tk.DISABLED)  # 键不可编辑
                
                ttk.Label(dialog, text="值:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W+tk.N)
                value_text = scrolledtext.ScrolledText(dialog, width=50, height=15, wrap=tk.WORD, font=("Courier", 10))
                value_text.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W+tk.E+tk.N+tk.S)
                
                # 尝试解码值
                try:
                    value_str = value.decode('utf-8', errors='ignore')
                    value_text.insert(1.0, value_str)
                except:
                    value_text.insert(1.0, value.hex())
                
                dialog.columnconfigure(1, weight=1)
                dialog.rowconfigure(1, weight=1)
                
                def save():
                    try:
                        new_value = value_text.get(1.0, tk.END).strip().encode('utf-8')
                        success, _ = self.db_wrapper.put(key.encode(), new_value)
                        if success:
                            self.db.flush()
                            messagebox.showinfo("成功", "记录更新成功！")
                            self._refresh_data()
                            dialog.destroy()
                        else:
                            messagebox.showerror("错误", "更新失败")
                    except Exception as e:
                        messagebox.showerror("错误", f"更新失败: {str(e)}")
                
                ttk.Button(dialog, text="保存", command=save).grid(row=2, column=1, padx=5, pady=10, sticky=tk.E)
                ttk.Button(dialog, text="取消", command=dialog.destroy).grid(row=2, column=0, padx=5, pady=10, sticky=tk.W)
        except Exception as e:
            messagebox.showerror("错误", f"获取记录失败: {str(e)}")
    
    def _delete_record(self):
        """删除记录（标记删除）"""
        selection = self.data_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要删除的记录")
            return
        
        # 获取选中的记录
        item = self.data_tree.item(selection[0])
        key = item['values'][0]
        
        if not self.db and not self.remote_db:
            messagebox.showwarning("警告", "请先连接数据库")
            return
        
        # 确认删除
        if not messagebox.askyesno("确认删除", f"确定要删除键 '{key}' 吗？\n\n注意：由于使用版本管理，数据不会真正删除，但查询时将返回None。"):
            return
        
        try:
            # 检查键是否存在
            value = self.db_wrapper.get(key.encode())
            if value is None:
                messagebox.showinfo("提示", f"键 '{key}' 不存在或已被删除")
                return
            
            # 执行删除（标记删除）
            success = self.db.delete(key.encode())
            if success:
                # 刷新数据到磁盘
                self.db.flush()
                messagebox.showinfo("成功", f"已标记删除: {key}\n\n提示：数据不会真正删除，但查询时将返回None。")
                self._refresh_data()
            else:
                messagebox.showerror("错误", "删除失败")
        except Exception as e:
            messagebox.showerror("错误", f"删除失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _delete_database(self):
        """删除整个数据库"""
        if not self.db and not self.remote_db:
            messagebox.showwarning("警告", "请先连接数据库")
            return
        
        # 获取当前数据库路径
        db_path = Path(self.data_dir)
        db_name = db_path.name
        
        # 确认删除
        confirm_msg = f"警告：这将删除整个数据库目录！\n\n数据库: {db_name}\n路径: {db_path}\n\n此操作不可恢复！\n\n请输入数据库名称以确认:"
        
        dialog = tk.Toplevel(self.root)
        dialog.title("删除数据库")
        dialog.geometry("500x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text=confirm_msg, wraplength=450).pack(padx=10, pady=10)
        
        confirm_entry = ttk.Entry(dialog, width=40)
        confirm_entry.pack(padx=10, pady=5)
        confirm_entry.focus()
        
        def confirm_delete():
            confirm_name = confirm_entry.get().strip()
            if confirm_name != db_name:
                messagebox.showerror("错误", f"确认失败：输入的数据库名称 '{confirm_name}' 与 '{db_name}' 不匹配")
                return
            
            dialog.destroy()
            
            try:
                import shutil
                # 先断开连接
                self._disconnect_database()
                # 删除目录
                shutil.rmtree(db_path)
                messagebox.showinfo("成功", f"数据库已删除: {db_path}")
            except Exception as e:
                messagebox.showerror("错误", f"删除失败: {str(e)}")
                import traceback
                traceback.print_exc()
        
        def cancel():
            dialog.destroy()
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(padx=10, pady=10)
        
        ttk.Button(button_frame, text="确认删除", command=confirm_delete).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=cancel).pack(side=tk.LEFT, padx=5)
        
        # 绑定Enter键
        confirm_entry.bind('<Return>', lambda e: confirm_delete())
    
    def _on_search_change(self):
        """搜索框内容变化时的处理（实时搜索）"""
        # 延迟搜索，避免输入时频繁搜索
        if hasattr(self, '_search_timer'):
            self.root.after_cancel(self._search_timer)
        self._search_timer = self.root.after(500, self._search_data)  # 500ms后执行搜索
    
    def _clear_search(self):
        """清除搜索"""
        self.search_entry.delete(0, tk.END)
        # 重置显示位置
        if hasattr(self, 'data_tree'):
            self.data_tree.delete(*self.data_tree.get_children())
        self._refresh_data()  # 刷新显示所有数据
    
    def _load_more_data(self):
        """加载更多数据"""
        if not self.db and not self.remote_db:
            messagebox.showwarning("警告", "请先连接数据库")
            return
        
        # 调用_refresh_data，传入load_more=True表示继续加载
        self._refresh_data(load_more=True)
    
    def _search_data(self):
        """模糊搜索数据（支持key和value的部分匹配，结果显示在列表中）"""
        search_text = self.search_entry.get().strip()
        
        if not self.db and not self.remote_db:
            messagebox.showwarning("警告", "请先连接数据库")
            return
        
        # 如果搜索框为空，显示所有数据
        if not search_text:
            self._refresh_data()
            return
        
        try:
            # 获取所有键
            if self.is_remote:
                all_keys = self.remote_db.get_all_keys()
            else:
                all_keys = self.db.version_manager.get_all_keys()
            if not all_keys:
                self.data_tree.delete(*self.data_tree.get_children())
                self._update_status("数据库为空，没有记录")
                return
            
            # 清空现有显示
            self.data_tree.delete(*self.data_tree.get_children())
            
            # 获取搜索模式
            search_mode = self.search_mode.get()
            search_text_lower = search_text.lower()
            
            # 使用ValueFormatter格式化显示
            from .value_formatter import ValueFormatter
            
            matched_count = 0
            display_count = 0
            max_display = 1000  # 最多显示1000条，避免界面卡顿
            
            for key in all_keys:
                if display_count >= max_display:
                    break
                
                try:
                    key_str = key.decode('utf-8', errors='ignore')
                    key_str_lower = key_str.lower()
                    
                    # 获取值
                    value = self.db_wrapper.get(key)
                    if not value:
                        continue
                    
                    # 根据搜索模式进行匹配
                    matched = False
                    
                    if search_mode == "key":
                        # 只搜索key
                        if search_text_lower in key_str_lower:
                            matched = True
                    elif search_mode == "value":
                        # 只搜索value
                        try:
                            value_str = value.decode('utf-8', errors='ignore').lower()
                            if search_text_lower in value_str:
                                matched = True
                        except:
                            # 二进制数据，尝试hex搜索
                            value_hex = value.hex().lower()
                            if search_text_lower in value_hex:
                                matched = True
                    else:  # both
                        # 搜索key和value
                        if search_text_lower in key_str_lower:
                            matched = True
                        else:
                            try:
                                value_str = value.decode('utf-8', errors='ignore').lower()
                                if search_text_lower in value_str:
                                    matched = True
                            except:
                                # 二进制数据，尝试hex搜索
                                value_hex = value.hex().lower()
                                if search_text_lower in value_hex:
                                    matched = True
                    
                    if matched:
                        matched_count += 1
                        
                        # 获取版本信息
                        try:
                            latest = self.db.version_manager.get_latest(key)
                            version = latest.version if latest else 0
                            timestamp = latest.timestamp if latest else 0
                        except:
                            version = 0
                            timestamp = 0
                        
                        # 使用值格式化器获取预览
                        format_type = ValueFormatter.detect_format(value)
                        value_preview = ValueFormatter.get_preview(value, max_length=80)
                        
                        # 添加格式标识
                        if format_type == 'json':
                            value_preview = f"[JSON] {value_preview}"
                        elif format_type == 'xml':
                            value_preview = f"[XML] {value_preview}"
                        elif format_type == 'binary':
                            value_preview = f"[Binary] {value_preview}"
                        elif format_type == 'geo':
                            value_preview = f"[Geo] {value_preview}"
                        elif format_type == 'ip':
                            value_preview = f"[IP] {value_preview}"
                        elif format_type == 'enum':
                            value_preview = f"[Enum] {value_preview}"
                        elif format_type == 'tree':
                            value_preview = f"[Tree] {value_preview}"
                        
                        timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp)) if timestamp > 0 else "N/A"
                        
                        # 高亮显示匹配的部分（在key中）
                        display_key = key_str
                        if search_text_lower in key_str_lower and search_mode in ["both", "key"]:
                            # 简单高亮：在匹配的文本前后添加标记（GUI中可以用tag实现，这里简化处理）
                            pass
                        
                        # 插入到树视图
                        self.data_tree.insert("", tk.END, values=(display_key, value_preview, version, timestamp_str))
                        display_count += 1
                        
                except Exception as e:
                    # 记录错误但继续处理其他键
                    print(f"[GUI调试] 搜索处理键时出错: {e}")
                    continue
            
            # 更新状态栏
            if matched_count > max_display:
                self._update_status(f"找到 {matched_count} 条匹配记录（显示前 {max_display} 条）")
            else:
                self._update_status(f"找到 {matched_count} 条匹配记录")
            
            if matched_count == 0:
                messagebox.showinfo("搜索结果", f"未找到包含 '{search_text}' 的记录")
        
        except Exception as e:
            import traceback
            error_msg = f"搜索失败: {str(e)}"
            print(f"[GUI调试] {error_msg}")
            traceback.print_exc()
            messagebox.showerror("错误", error_msg)
    
    def _execute_query(self):
        """执行查询（支持GET, PUT, DELETE, BATCH, SELECT等命令，不区分大小写）"""
        query = self.query_text.get(1.0, tk.END).strip()
        if not query:
            messagebox.showwarning("警告", "请输入查询语句")
            return
        
        if not self.db and not self.remote_db:
            messagebox.showwarning("警告", "请先连接数据库")
            return
        
        try:
            # 清空结果
            self.result_tree.delete(*self.result_tree.get_children())
            
            # 转换为大写以便匹配（但保留原始大小写用于显示）
            query_upper = query.upper().strip()
            query_parts = query.split()
            
            # GET 命令
            if query_upper.startswith("GET "):
                key_str = query[4:].strip()
                if not key_str:
                    self.query_status.config(text="错误: GET命令需要指定键")
                    return
                
                key = key_str.encode()
                value = self.db.get(key)
                if value:
                    try:
                        value_str = value.decode('utf-8', errors='ignore')
                        if len(value_str) > 200:
                            value_str = value_str[:200] + "..."
                    except:
                        value_str = value.hex()[:100] + "..."
                    
                    self.result_tree.insert("", tk.END, values=(key_str, value_str, "✓ 成功"))
                    self.query_status.config(text="查询成功：找到1条记录")
                else:
                    self.result_tree.insert("", tk.END, values=(key_str, "未找到", "✗ 未找到"))
                    self.query_status.config(text="查询完成：未找到记录")
            
            # PUT 命令
            elif query_upper.startswith("PUT "):
                parts = query.split(None, 2)  # 最多分割2次
                if len(parts) < 3:
                    self.query_status.config(text="错误: PUT命令格式: PUT <key> <value>")
                    return
                
                key_str = parts[1]
                value_str = parts[2]
                key = key_str.encode()
                value = value_str.encode()
                
                success, merkle_root = self.db.put(key, value)
                if success:
                    # 刷新数据到磁盘，确保CLI可以看到
                    self.db.flush()
                    self.result_tree.insert("", tk.END, values=(key_str, value_str[:200], "✓ 写入成功"))
                    self.query_status.config(text=f"写入成功：Merkle根 {merkle_root.hex()[:16]}...")
                else:
                    self.result_tree.insert("", tk.END, values=(key_str, value_str[:200], "✗ 写入失败"))
                    self.query_status.config(text="写入失败")
            
            # DELETE 命令
            elif query_upper.startswith("DELETE "):
                delete_cmd = query[7:].strip()
                if not delete_cmd:
                    self.query_status.config(text="错误: DELETE命令需要指定键或数据库")
                    return
                
                parts = delete_cmd.split()
                
                # 检查是否是删除数据库
                if len(parts) >= 2 and parts[0].lower() == 'database':
                    db_name = parts[1]
                    # 这里可以调用删除数据库的功能
                    self.query_status.config(text=f"删除数据库功能请使用菜单操作")
                    messagebox.showinfo("提示", "删除数据库功能请使用菜单：工具 -> 删除数据库")
                    return
                
                # 删除记录
                key_str = delete_cmd
                try:
                    # 检查键是否存在
                    value = self.db.get(key_str.encode())
                    if value is None:
                        self.result_tree.insert("", tk.END, values=(key_str, "未找到", "✗ 未找到"))
                        self.query_status.config(text="查询完成：未找到记录")
                        return
                    
                    # 执行删除（标记删除）
                    success = self.db_wrapper.delete(key_str.encode())
                    if success:
                        self.db.flush()
                        self.result_tree.insert("", tk.END, values=(key_str, "已标记删除", "✓ 成功"))
                        self.query_status.config(text="删除成功：已标记删除（数据不会真正删除，但查询时将返回None）")
                    else:
                        self.result_tree.insert("", tk.END, values=(key_str, "删除失败", "✗ 失败"))
                        self.query_status.config(text="删除失败")
                except Exception as e:
                    self.result_tree.insert("", tk.END, values=(key_str, f"错误: {str(e)}", "✗ 错误"))
                    self.query_status.config(text=f"删除错误: {str(e)}")
            
            # BATCH PUT 命令
            elif query_upper.startswith("BATCH PUT "):
                parts = query[10:].strip().split()
                if len(parts) < 2 or len(parts) % 2 != 0:
                    self.query_status.config(text="错误: BATCH PUT命令格式: BATCH PUT <key1> <value1> <key2> <value2> ...")
                    return
                
                items = []
                for i in range(0, len(parts), 2):
                    if i + 1 < len(parts):
                        key = parts[i].encode()
                        value = parts[i + 1].encode()
                        items.append((key, value))
                
                if items:
                    success, merkle_root = self.db_wrapper.batch_put(items)
                    if success:
                        # 刷新数据到磁盘，确保CLI可以看到
                        self.db.flush()
                        for key, value in items:
                            key_str = key.decode('utf-8', errors='ignore')
                            value_str = value.decode('utf-8', errors='ignore')[:200]
                            self.result_tree.insert("", tk.END, values=(key_str, value_str, "✓ 成功"))
                        self.query_status.config(text=f"批量写入成功：{len(items)} 条记录，Merkle根 {merkle_root.hex()[:16]}...")
                    else:
                        self.query_status.config(text="批量写入失败")
                else:
                    self.query_status.config(text="错误：没有提供键值对")
            
            # SELECT 命令
            elif query_upper.startswith("SELECT "):
                # SELECT * FROM <prefix> 或 SELECT <key>
                if query_upper.startswith("SELECT * FROM "):
                    # 范围查询
                    prefix = query[14:].strip()
                    if not prefix:
                        self.query_status.config(text="错误: SELECT * FROM 需要指定前缀")
                        return
                    
                    try:
                        if self.is_remote:
                            all_keys = self.remote_db.get_all_keys()
                        else:
                            all_keys = self.db.version_manager.get_all_keys()
                        
                        # 支持两种匹配方式（与CLI保持一致）：
                        # 1. 如果前缀包含':'，查找以 '<prefix>:' 开头的键
                        # 2. 如果前缀不包含':'，查找以 '<prefix>' 开头的键（不要求有':'）
                        if ':' in prefix:
                            # 用户明确指定了分隔符，使用精确匹配
                            matching_keys = [k for k in all_keys 
                                           if k.decode('utf-8', errors='ignore').upper().startswith(prefix.upper())]
                        else:
                            # 没有分隔符，尝试两种匹配：
                            # - 以 '<prefix>:' 开头的键（有分隔符）
                            # - 以 '<prefix>' 开头的键（无分隔符，如 key00000000）
                            matching_keys = []
                            for k in all_keys:
                                key_str = k.decode('utf-8', errors='ignore')
                                if key_str.upper().startswith(prefix.upper() + ':') or key_str.upper().startswith(prefix.upper()):
                                    matching_keys.append(k)
                        
                        if matching_keys:
                            count = 0
                            for key in matching_keys[:100]:  # 最多显示100条
                                value = self.db_wrapper.get(key)
                                if value:
                                    key_str = key.decode('utf-8', errors='ignore')
                                    try:
                                        value_str = value.decode('utf-8', errors='ignore')
                                        if len(value_str) > 200:
                                            value_str = value_str[:200] + "..."
                                    except:
                                        value_str = value.hex()[:100] + "..."
                                    
                                    self.result_tree.insert("", tk.END, values=(key_str, value_str, "✓ 找到"))
                                    count += 1
                            
                            if len(matching_keys) > 100:
                                self.query_status.config(text=f"查询成功：找到 {len(matching_keys)} 条记录（显示前100条）")
                            else:
                                self.query_status.config(text=f"查询成功：找到 {len(matching_keys)} 条记录")
                        else:
                            self.query_status.config(text=f"查询完成：未找到以 '{prefix}' 开头的键")
                            messagebox.showinfo("提示", f"未找到以 '{prefix}' 开头的键\n\n提示: 尝试使用 'SELECT * FROM {prefix}:' 或检查键的前缀")
                    except Exception as e:
                        self.query_status.config(text=f"查询错误: {str(e)}")
                        raise
                
                else:
                    # 单键查询: SELECT <key>
                    key_str = query[7:].strip()
                    if not key_str:
                        self.query_status.config(text="错误: SELECT命令需要指定键")
                        return
                    
                    key = key_str.encode()
                    value = self.db_wrapper.get(key)
                    if value:
                        try:
                            value_str = value.decode('utf-8', errors='ignore')
                            if len(value_str) > 200:
                                value_str = value_str[:200] + "..."
                        except:
                            value_str = value.hex()[:100] + "..."
                        
                        self.result_tree.insert("", tk.END, values=(key_str, value_str, "✓ 成功"))
                        self.query_status.config(text="查询成功：找到1条记录")
                    else:
                        self.result_tree.insert("", tk.END, values=(key_str, "未找到", "✗ 未找到"))
                        self.query_status.config(text="查询完成：未找到记录")
            
            else:
                self.query_status.config(text="错误: 不支持的查询格式。支持: GET, PUT, DELETE, BATCH PUT, SELECT")
                messagebox.showwarning("提示", "不支持的查询格式\n\n支持的命令:\n- GET <key>\n- PUT <key> <value>\n- DELETE <key>\n- BATCH PUT <key1> <value1> ...\n- SELECT * FROM <prefix>\n- SELECT <key>")
            
            # 刷新数据浏览
            self._refresh_data()
            
        except Exception as e:
            self.query_status.config(text=f"查询失败: {str(e)}")
            messagebox.showerror("错误", f"查询失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _show_stats(self):
        """显示数据库统计"""
        if not self.db and not self.remote_db:
            messagebox.showwarning("警告", "请先连接数据库")
            return
        
        try:
            stats = self.db.get_stats()
            stats_text = json.dumps(stats, indent=2, ensure_ascii=False)
            
            dialog = tk.Toplevel(self.root)
            dialog.title("数据库统计")
            dialog.geometry("600x400")
            
            text = scrolledtext.ScrolledText(dialog, wrap=tk.WORD)
            text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            text.insert(1.0, stats_text)
            text.config(state=tk.DISABLED)
            
        except Exception as e:
            messagebox.showerror("错误", f"获取统计信息失败: {str(e)}")
    
    def _show_metrics(self):
        """显示性能监控"""
        self.notebook.select(3)  # 切换到性能监控标签页
        self._refresh_metrics()
    
    def _refresh_metrics(self):
        """刷新性能指标"""
        if not self.db_wrapper:
            self.metrics_text.delete(1.0, tk.END)
            self.metrics_text.insert(1.0, "请先连接数据库")
            return
        
        try:
            stats = self.db_wrapper.get_stats()
            if not stats:
                self.metrics_text.delete(1.0, tk.END)
                self.metrics_text.insert(1.0, "无法获取统计信息")
                return
            metrics_text = f"""数据库统计信息
{'=' * 60}

总键数: {stats.get('total_keys', 0)}
当前版本: {stats.get('current_version', 0)}
Merkle根哈希: {stats.get('merkle_root', 'N/A')}
存储目录: {stats.get('storage_dir', 'N/A')}
分片启用: {stats.get('sharding_enabled', False)}

"""
            if stats.get('sharding_enabled'):
                metrics_text += f"分片数量: {stats.get('shard_count', 0)}\n"
            
            self.metrics_text.delete(1.0, tk.END)
            self.metrics_text.insert(1.0, metrics_text)
        except Exception as e:
            self.metrics_text.delete(1.0, tk.END)
            self.metrics_text.insert(1.0, f"获取指标失败: {str(e)}")
    
    def _start_monitoring(self):
        """开始监控"""
        self.monitoring = True
        self._monitor_loop()
    
    def _stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
    
    def _monitor_loop(self):
        """监控循环"""
        if self.monitoring:
            self._refresh_metrics()
            self.root.after(2000, self._monitor_loop)  # 每2秒刷新一次
    
    def _load_config(self):
        """加载配置"""
        file_path = filedialog.askopenfilename(
            title="选择配置文件",
            filetypes=[("INI files", "*.ini"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.config_text.delete(1.0, tk.END)
                self.config_text.insert(1.0, content)
                messagebox.showinfo("成功", "配置加载成功")
            except Exception as e:
                messagebox.showerror("错误", f"加载配置失败: {str(e)}")
    
    def _save_config(self):
        """保存配置"""
        file_path = filedialog.asksaveasfilename(
            title="保存配置文件",
            defaultextension=".ini",
            filetypes=[("INI files", "*.ini"), ("All files", "*.*")]
        )
        if file_path:
            try:
                content = self.config_text.get(1.0, tk.END)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("成功", "配置保存成功")
            except Exception as e:
                messagebox.showerror("错误", f"保存配置失败: {str(e)}")
    
    def _load_config_from_db_auto(self):
        """从当前数据库自动加载配置（静默，不显示消息框）"""
        if not self.db and not self.remote_db:
            return
        
        try:
            config_path = self.db.get_config_path()
            
            # 检查配置文件是否存在
            from pathlib import Path
            if not Path(config_path).exists():
                # 配置文件不存在，使用当前配置生成
                self.db.save_config()
            
            # 读取配置文件内容
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 显示在文本框中
            self.config_text.delete(1.0, tk.END)
            self.config_text.insert(1.0, content)
            
            # 更新信息标签
            self.config_info_label.config(
                text=f"已加载: {config_path}",
                foreground='green'
            )
        except Exception as e:
            # 静默失败，只更新标签
            self.config_info_label.config(
                text=f"加载配置失败: {str(e)}",
                foreground='red'
            )
    
    def _load_config_from_db(self):
        """从当前数据库加载配置"""
        if not self.db_wrapper:
            messagebox.showwarning("警告", "请先连接数据库")
            return
        
        try:
            if self.is_remote:
                # 远程连接：从服务器获取配置
                config_dict = self.db_wrapper.get_config()
                if not config_dict:
                    messagebox.showwarning("警告", "无法获取远程数据库配置")
                    return
                
                # 显示配置信息
                config_text = f"""[database]
data_dir = {config_dict.get('data_dir', 'N/A')}
enable_sharding = {config_dict.get('enable_sharding', False)}
shard_count = {config_dict.get('shard_count', 256)}

[network]
host = {config_dict.get('network_host', '0.0.0.0')}
port = {config_dict.get('network_port', 3888)}

[batch]
max_size = {config_dict.get('batch_max_size', 3000)}

[threading]
enable = {config_dict.get('threading_enable', True)}
max_workers = {config_dict.get('threading_max_workers', 4)}
"""
                self.config_text.delete(1.0, tk.END)
                self.config_text.insert(1.0, config_text)
                self.config_info_label.config(text="已从远程服务器加载配置（只读）", foreground='blue')
                messagebox.showinfo("成功", "已从远程服务器加载配置\n\n注意：远程配置为只读，无法直接修改")
                return
            
            # 本地连接
            config_path = self.db.get_config_path()
            
            # 检查配置文件是否存在
            from pathlib import Path
            if not Path(config_path).exists():
                # 配置文件不存在，使用当前配置生成
                self.db.save_config()
                messagebox.showinfo("提示", f"配置文件不存在，已创建默认配置: {config_path}")
            
            # 读取配置文件内容
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 显示在文本框中
            self.config_text.delete(1.0, tk.END)
            self.config_text.insert(1.0, content)
            
            # 更新信息标签
            self.config_info_label.config(
                text=f"已加载: {config_path}",
                foreground='green'
            )
            
            messagebox.showinfo("成功", f"配置已从数据库加载: {config_path}")
        except Exception as e:
            messagebox.showerror("错误", f"加载配置失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _load_config_from_file(self):
        """从文件加载配置"""
        file_path = filedialog.askopenfilename(
            title="选择配置文件",
            filetypes=[("INI files", "*.ini"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 显示在文本框中
            self.config_text.delete(1.0, tk.END)
            self.config_text.insert(1.0, content)
            
            # 更新信息标签
            self.config_info_label.config(
                text=f"已加载: {file_path}",
                foreground='green'
            )
            
            messagebox.showinfo("成功", f"配置已从文件加载: {file_path}")
        except Exception as e:
            messagebox.showerror("错误", f"加载配置失败: {str(e)}")
    
    def _save_config_to_db(self):
        """保存配置到当前数据库"""
        if not self.db and not self.remote_db:
            messagebox.showwarning("警告", "请先连接数据库")
            return
        
        try:
            # 获取文本框内容
            content = self.config_text.get(1.0, tk.END).strip()
            
            if not content:
                messagebox.showwarning("警告", "配置内容为空")
                return
            
            # 先验证配置
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
                f.write(content)
                temp_path = f.name
            
            try:
                # 尝试加载配置以验证格式
                from .config import load_config
                test_config = load_config(temp_path)
                
                # 验证通过，保存到数据库
                config_path = self.db.get_config_path()
                with open(config_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # 重新加载配置到数据库对象
                self.db.load_config()
                
                # 更新信息标签
                self.config_info_label.config(
                    text=f"已保存: {config_path}",
                    foreground='green'
                )
                
                messagebox.showinfo("成功", f"配置已保存到数据库: {config_path}\n注意：部分配置需要重启数据库才能生效")
            finally:
                # 清理临时文件
                import os
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _export_config_to_file(self):
        """导出配置到文件"""
        file_path = filedialog.asksaveasfilename(
            title="保存配置文件",
            defaultextension=".ini",
            filetypes=[("INI files", "*.ini"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            # 获取文本框内容
            content = self.config_text.get(1.0, tk.END).strip()
            
            if not content:
                messagebox.showwarning("警告", "配置内容为空")
                return
            
            # 先验证配置
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
                f.write(content)
                temp_path = f.name
            
            try:
                # 尝试加载配置以验证格式
                from .config import load_config
                test_config = load_config(temp_path)
                
                # 验证通过，保存到文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                messagebox.showinfo("成功", f"配置已导出到: {file_path}")
            finally:
                # 清理临时文件
                import os
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
        except Exception as e:
            messagebox.showerror("错误", f"导出配置失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _reset_config(self):
        """重置为默认配置"""
        if not messagebox.askyesno("确认", "确定要重置为默认配置吗？\n当前编辑的内容将被覆盖"):
            return
        
        try:
            # 创建默认配置
            from .config import DatabaseConfig
            config = DatabaseConfig()
            
            # 如果有数据库，使用数据库的data_dir
            if self.db:
                config.data_dir = self.db.data_dir
            
            # 保存到临时文件
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
                temp_path = f.name
                config.to_ini(temp_path)
            
            # 读取默认配置内容
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 显示在文本框中
            self.config_text.delete(1.0, tk.END)
            self.config_text.insert(1.0, content)
            
            # 清理临时文件
            import os
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            
            # 更新信息标签
            self.config_info_label.config(
                text="已重置为默认配置",
                foreground='blue'
            )
            
            messagebox.showinfo("提示", "已重置为默认配置")
        except Exception as e:
            messagebox.showerror("错误", f"重置配置失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _validate_config(self):
        """验证配置"""
        try:
            content = self.config_text.get(1.0, tk.END).strip()
            
            if not content:
                messagebox.showwarning("警告", "配置内容为空")
                return
            
            # 保存到临时文件
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
                f.write(content)
                temp_path = f.name
            
            try:
                # 尝试加载配置
                from .config import load_config
                config = load_config(temp_path)
                
                # 验证通过
                messagebox.showinfo("成功", "配置验证通过！\n所有配置项格式正确")
            finally:
                # 清理临时文件
                import os
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
        except Exception as e:
            messagebox.showerror("错误", f"配置验证失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _batch_import(self):
        """批量导入"""
        file_path = filedialog.askopenfilename(
            title="选择数据文件",
            filetypes=[("JSON files", "*.json"), ("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if file_path:
            messagebox.showinfo("提示", "批量导入功能待实现")
    
    def _export_data(self):
        """导出数据"""
        file_path = filedialog.asksaveasfilename(
            title="保存数据文件",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if file_path:
            messagebox.showinfo("提示", "导出功能待实现")
    
    def _clear_data(self):
        """清空数据"""
        if messagebox.askyesno("警告", "确定要清空所有数据吗？此操作不可恢复！"):
            messagebox.showinfo("提示", "清空功能待实现")
    
    def _backup_database(self):
        """备份数据库"""
        file_path = filedialog.asksaveasfilename(
            title="保存备份文件",
            defaultextension=".backup",
            filetypes=[("Backup files", "*.backup"), ("All files", "*.*")]
        )
        if file_path and self.db:
            try:
                # 使用备份功能
                from .backup import BackupManager
                backup_mgr = BackupManager(self.db.data_dir)
                backup_mgr.create_full_backup(file_path)
                messagebox.showinfo("成功", "备份创建成功！")
            except Exception as e:
                messagebox.showerror("错误", f"备份失败: {str(e)}")
    
    def _restore_database(self):
        """恢复数据库"""
        file_path = filedialog.askopenfilename(
            title="选择备份文件",
            filetypes=[("Backup files", "*.backup"), ("All files", "*.*")]
        )
        if file_path:
            messagebox.showinfo("提示", "恢复功能待实现")
    
    def _compact_database(self):
        """压缩数据库"""
        if not self.db and not self.remote_db:
            messagebox.showwarning("警告", "请先连接数据库")
            return
        
        if messagebox.askyesno("确认", "确定要压缩数据库吗？"):
            try:
                self.db.flush()
                messagebox.showinfo("成功", "数据库压缩完成！")
            except Exception as e:
                messagebox.showerror("错误", f"压缩失败: {str(e)}")
    
    def _optimize_database(self):
        """优化数据库"""
        messagebox.showinfo("提示", "优化功能待实现")
    
    def _save_query(self):
        """保存查询"""
        query = self.query_text.get(1.0, tk.END).strip()
        if not query:
            messagebox.showwarning("警告", "查询为空")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="保存查询",
            defaultextension=".sql",
            filetypes=[("SQL files", "*.sql"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(query)
                messagebox.showinfo("成功", "查询保存成功")
            except Exception as e:
                messagebox.showerror("错误", f"保存失败: {str(e)}")
    
    def _load_query(self):
        """加载查询"""
        file_path = filedialog.askopenfilename(
            title="选择查询文件",
            filetypes=[("SQL files", "*.sql"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    query = f.read()
                self.query_text.delete(1.0, tk.END)
                self.query_text.insert(1.0, query)
            except Exception as e:
                messagebox.showerror("错误", f"加载失败: {str(e)}")
    
    def _query_history(self):
        """查询历史"""
        messagebox.showinfo("提示", "查询历史功能待实现")
    
    def _show_help(self):
        """显示帮助"""
        help_text = """AmDb 数据库管理器使用说明

1. 连接数据库
   - 点击"文件" -> "连接数据库"
   - 选择配置文件或指定数据目录

2. 数据浏览
   - 在"数据浏览"标签页查看所有数据
   - 双击记录可编辑
   - 使用搜索框快速查找

3. 查询执行
   - 在"查询执行"标签页输入查询语句
   - 支持命令（不区分大小写）：
     * GET <key>                    - 读取数据
     * PUT <key> <value>            - 写入数据
     * DELETE <key>                 - 删除数据（标记删除）
     * BATCH PUT <key1> <value1> ... - 批量写入
     * SELECT * FROM <prefix>       - 范围查询
     * SELECT <key>                  - 单键查询
   - 点击"执行查询"按钮执行

4. 配置管理
   - 在"配置管理"标签页编辑配置文件
   - 可以加载、保存、验证配置

5. 性能监控
   - 在"性能监控"标签页查看实时指标
   - 点击"开始监控"开始实时监控

更多信息请参考文档。
"""
        messagebox.showinfo("使用说明", help_text)
    
    def _show_about(self):
        """显示关于"""
        about_text = """AmDb 数据库管理器
版本: 1.0.0

AmDb是一个专为区块链应用设计的高性能数据库系统。

特性：
- 高性能键值存储
- 版本管理和历史追溯
- 数据完整性验证（Merkle树）
- 支持大数据量（分片存储）
- 多语言支持

© 2024 AmDb Project
"""
        messagebox.showinfo("关于", about_text)
    
    def _update_status(self, message: str):
        """更新状态栏"""
        self.status_bar.config(text=message)


def main():
    """启动GUI管理器"""
    root = tk.Tk()
    app = DatabaseManagerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

