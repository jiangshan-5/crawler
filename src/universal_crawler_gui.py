#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用爬虫 GUI 版本
支持用户自定义 URL、选择器、爬取数量等
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import os
import sys
from datetime import datetime
import json

# 导入爬虫模块
try:
    from universal_crawler import UniversalCrawler
except ImportError:
    import importlib.util
    
    def load_module(name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    UniversalCrawler = load_module('universal_crawler', 
                                   os.path.join(base_dir, 'universal_crawler.py')).UniversalCrawler


class UniversalCrawlerGUI:
    """通用爬虫图形界面 - 美化版"""
    
    # 配色方案
    PRIMARY_COLOR = "#2196F3"      # 主色调 - 蓝色
    SECONDARY_COLOR = "#00BCD4"    # 次要色 - 青色
    SUCCESS_COLOR = "#4CAF50"      # 成功 - 绿色
    WARNING_COLOR = "#FF9800"      # 警告 - 橙色
    ERROR_COLOR = "#F44336"        # 错误 - 红色
    BG_COLOR = "#f5f5f5"           # 背景色
    CARD_BG = "#ffffff"            # 卡片背景
    
    def __init__(self, root):
        self.root = root
        self.root.title("🕷️ 通用网页爬虫工具 v2.0")
        self.root.geometry("1300x750")
        
        # 设置最小窗口大小
        self.root.minsize(1000, 650)
        
        # 设置窗口背景色
        self.root.configure(bg=self.BG_COLOR)
        
        # 配置根窗口的行列权重，使其可以自适应
        self.root.rowconfigure(1, weight=1)  # 主内容区域可扩展
        self.root.columnconfigure(0, weight=1)
        
        # 变量
        self.is_crawling = False
        self.crawler = None
        self.selectors = []  # 选择器列表
        
        # 配置样式
        self.setup_styles()
        
        # 创建界面
        self.create_widgets()
    
    def setup_styles(self):
        """配置自定义样式"""
        style = ttk.Style()
        
        # 使用现代主题
        try:
            style.theme_use('clam')
        except:
            pass
        
        # 配置 Frame 背景
        style.configure("TFrame", background=self.BG_COLOR)
        style.configure("Card.TFrame", background=self.CARD_BG, relief="raised", borderwidth=1)
        
        # 配置 LabelFrame
        style.configure("TLabelframe", background=self.CARD_BG, borderwidth=2, relief="solid")
        style.configure("TLabelframe.Label", 
                       background=self.CARD_BG,
                       foreground=self.PRIMARY_COLOR,
                       font=("Microsoft YaHei UI", 10, "bold"))
        
        # 配置按钮 - 主按钮
        style.configure("Primary.TButton",
                       background=self.PRIMARY_COLOR,
                       foreground="white",
                       borderwidth=0,
                       focuscolor='none',
                       padding=(20, 10),
                       font=("Microsoft YaHei UI", 10, "bold"))
        style.map("Primary.TButton",
                 background=[('active', self.SECONDARY_COLOR), ('disabled', '#BDBDBD')])
        
        # 配置按钮 - 次要按钮
        style.configure("Secondary.TButton",
                       background=self.CARD_BG,
                       foreground=self.PRIMARY_COLOR,
                       borderwidth=1,
                       padding=(10, 6),
                       font=("Microsoft YaHei UI", 9))
        
        # 配置 Entry
        style.configure("TEntry", fieldbackground="white", borderwidth=1)
        
        # 配置 Treeview
        style.configure("Treeview",
                       background="white",
                       fieldbackground="white",
                       foreground="#212121",
                       rowheight=25)
        style.configure("Treeview.Heading",
                       background=self.PRIMARY_COLOR,
                       foreground="white",
                       font=("Microsoft YaHei UI", 9, "bold"))
        style.map("Treeview.Heading",
                 background=[('active', self.SECONDARY_COLOR)])
        
        # 配置 Progressbar
        style.configure("TProgressbar",
                       background=self.SUCCESS_COLOR,
                       troughcolor=self.BG_COLOR,
                       borderwidth=0,
                       thickness=4)
        
    def create_widgets(self):
        """创建界面组件 - 使用响应式布局和现代化设计"""
        
        # 标题区域 (row 0) - 渐变背景效果
        title_frame = tk.Frame(self.root, bg=self.PRIMARY_COLOR, height=80)
        title_frame.grid(row=0, column=0, sticky="ew")
        title_frame.grid_propagate(False)
        
        title_label = tk.Label(
            title_frame, 
            text="🕷️ 通用网页爬虫工具", 
            font=("Microsoft YaHei UI", 18, "bold"),
            bg=self.PRIMARY_COLOR,
            fg="white"
        )
        title_label.pack(pady=(15, 5))
        
        subtitle_label = tk.Label(
            title_frame,
            text="自定义 URL、选择器、爬取数量和保存位置 | 简单、强大、高效",
            font=("Microsoft YaHei UI", 10),
            bg=self.PRIMARY_COLOR,
            fg="white"
        )
        subtitle_label.pack()
        
        # 主容器 (row 1) - 使用 grid 布局
        main_frame = ttk.Frame(self.root)
        main_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        # 配置主容器的行列权重
        main_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=2)  # 左侧配置区域
        main_frame.columnconfigure(1, weight=3)  # 右侧日志预览区域
        
        # 左侧：配置区域 (column 0)
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        
        # 配置左侧区域的行权重
        left_frame.rowconfigure(0, weight=0)  # URL 配置 - 固定高度
        left_frame.rowconfigure(1, weight=1)  # 字段选择器 - 可扩展
        left_frame.rowconfigure(2, weight=0)  # 爬取控制 - 固定高度
        left_frame.columnconfigure(0, weight=1)
        
        # URL 配置 (row 0) - 卡片样式
        url_frame = ttk.LabelFrame(left_frame, text="🌐 URL 配置", padding="10")
        url_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        url_frame.columnconfigure(0, weight=1)
        
        ttk.Label(url_frame, text="目标 URL:", font=("Microsoft YaHei UI", 9)).grid(row=0, column=0, sticky="w", pady=(0, 5))
        self.url_entry = ttk.Entry(url_frame, font=("Consolas", 10))
        self.url_entry.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self.url_entry.insert(0, "https://example.com")
        
        # 爬取模式 - 使用更现代的布局
        mode_frame = ttk.Frame(url_frame)
        mode_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        
        ttk.Label(mode_frame, text="爬取模式:", font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT, padx=(0, 15))
        self.mode_var = tk.StringVar(value='list')
        ttk.Radiobutton(
            mode_frame, 
            text="📋 列表页面", 
            variable=self.mode_var, 
            value='list'
        ).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(
            mode_frame, 
            text="📄 单个页面", 
            variable=self.mode_var, 
            value='single'
        ).pack(side=tk.LEFT)
        
        # 列表选择器
        ttk.Label(url_frame, text="列表容器选择器:", font=("Microsoft YaHei UI", 9)).grid(row=3, column=0, sticky="w", pady=(0, 5))
        self.list_selector_entry = ttk.Entry(url_frame, font=("Consolas", 10))
        self.list_selector_entry.grid(row=4, column=0, sticky="ew")
        self.list_selector_entry.insert(0, "div.item")
        
        # 字段选择器配置 (row 1) - 可扩展
        selector_frame = ttk.LabelFrame(left_frame, text="⚙️ 字段选择器配置", padding="10")
        selector_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 8))
        
        # 配置选择器框架的行列权重
        selector_frame.rowconfigure(0, weight=1)  # 表格可扩展
        selector_frame.rowconfigure(1, weight=0)  # 按钮固定
        selector_frame.columnconfigure(0, weight=1)
        
        # 选择器列表
        selector_list_frame = ttk.Frame(selector_frame)
        selector_list_frame.grid(row=0, column=0, sticky="nsew")
        selector_list_frame.rowconfigure(0, weight=1)
        selector_list_frame.columnconfigure(0, weight=1)
        
        # 创建表格 - 不设置固定高度，让它自适应
        columns = ('字段名', 'CSS选择器', '说明')
        self.selector_tree = ttk.Treeview(
            selector_list_frame, 
            columns=columns, 
            show='headings'
        )
        
        for col in columns:
            self.selector_tree.heading(col, text=col)
            if col == '字段名':
                self.selector_tree.column(col, width=100)
            elif col == 'CSS选择器':
                self.selector_tree.column(col, width=200)
            else:
                self.selector_tree.column(col, width=150)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(selector_list_frame, orient=tk.VERTICAL, command=self.selector_tree.yview)
        self.selector_tree.configure(yscrollcommand=scrollbar.set)
        
        self.selector_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # 选择器操作按钮 - 使用次要按钮样式
        selector_btn_frame = ttk.Frame(selector_frame)
        selector_btn_frame.grid(row=1, column=0, sticky="ew")
        
        ttk.Button(
            selector_btn_frame,
            text="➕ 添加",
            command=self.add_selector,
            style="Secondary.TButton"
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            selector_btn_frame,
            text="✏️ 编辑",
            command=self.edit_selector,
            style="Secondary.TButton"
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            selector_btn_frame,
            text="🗑️ 删除",
            command=self.delete_selector,
            style="Secondary.TButton"
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            selector_btn_frame,
            text="📋 示例",
            command=self.load_example_selectors,
            style="Secondary.TButton"
        ).pack(side=tk.LEFT)
        
        # 爬取控制 (row 2) - 固定高度
        control_frame = ttk.LabelFrame(left_frame, text="🎮 爬取控制", padding="10")
        control_frame.grid(row=2, column=0, sticky="ew")
        control_frame.columnconfigure(0, weight=1)
        
        # 爬取数量
        limit_frame = ttk.Frame(control_frame)
        limit_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        
        ttk.Label(limit_frame, text="爬取数量:", font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT, padx=(0, 10))
        self.limit_var = tk.IntVar(value=10)
        limit_spinbox = ttk.Spinbox(
            limit_frame, 
            from_=1, 
            to=1000, 
            textvariable=self.limit_var,
            width=12,
            font=("Microsoft YaHei UI", 9)
        )
        limit_spinbox.pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(limit_frame, text="条", font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        
        # 延迟设置
        delay_frame = ttk.Frame(control_frame)
        delay_frame.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        
        ttk.Label(delay_frame, text="请求延迟:", font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT, padx=(0, 10))
        self.delay_var = tk.DoubleVar(value=1.0)
        delay_spinbox = ttk.Spinbox(
            delay_frame, 
            from_=0, 
            to=10, 
            increment=0.5,
            textvariable=self.delay_var,
            width=12,
            font=("Microsoft YaHei UI", 9)
        )
        delay_spinbox.pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(delay_frame, text="秒", font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        
        # 保存格式
        format_frame = ttk.Frame(control_frame)
        format_frame.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        
        ttk.Label(format_frame, text="保存格式:", font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT, padx=(0, 15))
        self.format_var = tk.StringVar(value='json')
        ttk.Radiobutton(
            format_frame, 
            text="JSON", 
            variable=self.format_var, 
            value='json'
        ).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(
            format_frame, 
            text="CSV", 
            variable=self.format_var, 
            value='csv'
        ).pack(side=tk.LEFT)
        
        # 输出目录
        ttk.Label(control_frame, text="保存位置:", font=("Microsoft YaHei UI", 9)).grid(row=3, column=0, sticky="w", pady=(0, 5))
        
        output_entry_frame = ttk.Frame(control_frame)
        output_entry_frame.grid(row=4, column=0, sticky="ew", pady=(0, 10))
        output_entry_frame.columnconfigure(0, weight=1)
        
        self.output_var = tk.StringVar(value="data/crawled_data")
        output_entry = ttk.Entry(output_entry_frame, textvariable=self.output_var, font=("Consolas", 9))
        output_entry.grid(row=0, column=0, sticky="ew")
        
        browse_btn = ttk.Button(
            output_entry_frame, 
            text="📁 浏览", 
            command=self.browse_output_dir,
            style="Secondary.TButton",
            width=10
        )
        browse_btn.grid(row=0, column=1, padx=(5, 0))
        
        # 操作按钮 - 使用主按钮样式
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=5, column=0, sticky="ew")
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        
        self.start_btn = ttk.Button(
            button_frame,
            text="🚀 开始爬取",
            command=self.start_crawling,
            style="Primary.TButton"
        )
        self.start_btn.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        
        self.stop_btn = ttk.Button(
            button_frame,
            text="⏹ 停止",
            command=self.stop_crawling,
            style="Secondary.TButton",
            state=tk.DISABLED
        )
        self.stop_btn.grid(row=0, column=1, sticky="ew")
        
        # 右侧：日志和预览区域 (column 1)
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        
        # 配置右侧区域的行权重
        right_frame.rowconfigure(0, weight=1)  # 日志区域
        right_frame.rowconfigure(1, weight=1)  # 预览区域
        right_frame.columnconfigure(0, weight=1)
        
        # 日志区域 (row 0) - 可扩展
        log_frame = ttk.LabelFrame(right_frame, text="📊 运行日志", padding="10")
        log_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 8))
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="white",
            selectbackground=self.PRIMARY_COLOR,
            relief="flat",
            borderwidth=0
        )
        self.log_text.grid(row=0, column=0, sticky="nsew")
        
        # 数据预览区域 (row 1) - 可扩展
        preview_frame = ttk.LabelFrame(right_frame, text="👁️ 数据预览", padding="10")
        preview_frame.grid(row=1, column=0, sticky="nsew")
        preview_frame.rowconfigure(0, weight=1)
        preview_frame.columnconfigure(0, weight=1)
        
        self.preview_text = scrolledtext.ScrolledText(
            preview_frame,
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg="white",
            fg="#212121",
            insertbackground=self.PRIMARY_COLOR,
            selectbackground=self.PRIMARY_COLOR,
            relief="flat",
            borderwidth=0
        )
        self.preview_text.grid(row=0, column=0, sticky="nsew")
        
        # 底部：状态栏 (row 2) - 现代化设计
        status_frame = tk.Frame(self.root, bg=self.BG_COLOR, height=50)
        status_frame.grid(row=2, column=0, sticky="ew")
        status_frame.grid_propagate(False)
        status_frame.columnconfigure(0, weight=1)
        
        self.status_var = tk.StringVar(value="✅ 就绪")
        status_label = tk.Label(
            status_frame, 
            textvariable=self.status_var,
            bg=self.BG_COLOR,
            fg=self.PRIMARY_COLOR,
            font=("Microsoft YaHei UI", 10),
            anchor=tk.W
        )
        status_label.grid(row=0, column=0, sticky="ew", padx=15, pady=(5, 2))
        
        # 进度条 - 现代化样式
        self.progress = ttk.Progressbar(
            status_frame,
            mode='indeterminate'
        )
        self.progress.grid(row=1, column=0, sticky="ew", padx=15, pady=(2, 10))
    
    def add_selector(self):
        """添加选择器"""
        dialog = tk.Toplevel(self.root)
        dialog.title("添加字段")
        dialog.geometry("500x250")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 字段名
        ttk.Label(dialog, text="字段名:").pack(anchor=tk.W, padx=20, pady=(20, 5))
        field_entry = ttk.Entry(dialog, width=50)
        field_entry.pack(padx=20, pady=(0, 10))
        
        # CSS 选择器
        ttk.Label(dialog, text="CSS 选择器:").pack(anchor=tk.W, padx=20, pady=(0, 5))
        selector_entry = ttk.Entry(dialog, width=50)
        selector_entry.pack(padx=20, pady=(0, 10))
        
        # 说明
        ttk.Label(dialog, text="说明（可选）:").pack(anchor=tk.W, padx=20, pady=(0, 5))
        desc_entry = ttk.Entry(dialog, width=50)
        desc_entry.pack(padx=20, pady=(0, 20))
        
        # 提示
        tip_label = ttk.Label(
            dialog,
            text="提示：提取文本用 'h1'，提取属性用 'a@href'",
            foreground="gray"
        )
        tip_label.pack(padx=20)
        
        def do_add():
            field = field_entry.get().strip()
            selector = selector_entry.get().strip()
            desc = desc_entry.get().strip()
            
            if not field or not selector:
                messagebox.showwarning("警告", "字段名和选择器不能为空！")
                return
            
            self.selector_tree.insert('', tk.END, values=(field, selector, desc))
            dialog.destroy()
        
        ttk.Button(dialog, text="添加", command=do_add).pack(pady=10)
    
    def edit_selector(self):
        """编辑选择器"""
        selected = self.selector_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择要编辑的字段！")
            return
        
        item = selected[0]
        values = self.selector_tree.item(item, 'values')
        
        dialog = tk.Toplevel(self.root)
        dialog.title("编辑字段")
        dialog.geometry("500x250")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 字段名
        ttk.Label(dialog, text="字段名:").pack(anchor=tk.W, padx=20, pady=(20, 5))
        field_entry = ttk.Entry(dialog, width=50)
        field_entry.pack(padx=20, pady=(0, 10))
        field_entry.insert(0, values[0])
        
        # CSS 选择器
        ttk.Label(dialog, text="CSS 选择器:").pack(anchor=tk.W, padx=20, pady=(0, 5))
        selector_entry = ttk.Entry(dialog, width=50)
        selector_entry.pack(padx=20, pady=(0, 10))
        selector_entry.insert(0, values[1])
        
        # 说明
        ttk.Label(dialog, text="说明（可选）:").pack(anchor=tk.W, padx=20, pady=(0, 5))
        desc_entry = ttk.Entry(dialog, width=50)
        desc_entry.pack(padx=20, pady=(0, 20))
        desc_entry.insert(0, values[2] if len(values) > 2 else '')
        
        def do_edit():
            field = field_entry.get().strip()
            selector = selector_entry.get().strip()
            desc = desc_entry.get().strip()
            
            if not field or not selector:
                messagebox.showwarning("警告", "字段名和选择器不能为空！")
                return
            
            self.selector_tree.item(item, values=(field, selector, desc))
            dialog.destroy()
        
        ttk.Button(dialog, text="保存", command=do_edit).pack(pady=10)
    
    def delete_selector(self):
        """删除选择器"""
        selected = self.selector_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择要删除的字段！")
            return
        
        if messagebox.askyesno("确认", "确定要删除选中的字段吗？"):
            for item in selected:
                self.selector_tree.delete(item)
    
    def load_example_selectors(self):
        """加载示例选择器"""
        examples = [
            ('标题', 'h1', '提取 h1 标签文本'),
            ('链接', 'a@href', '提取 a 标签的 href 属性'),
            ('图片', 'img@src', '提取 img 标签的 src 属性'),
            ('价格', 'span.price', '提取 class 为 price 的 span 文本'),
            ('描述', 'p.description', '提取 class 为 description 的 p 文本')
        ]
        
        # 清空现有选择器
        for item in self.selector_tree.get_children():
            self.selector_tree.delete(item)
        
        # 添加示例
        for field, selector, desc in examples:
            self.selector_tree.insert('', tk.END, values=(field, selector, desc))
        
        messagebox.showinfo("提示", "已加载示例选择器，请根据实际网页修改！")
    
    def browse_output_dir(self):
        """浏览输出目录"""
        directory = filedialog.askdirectory(
            title="选择保存位置",
            initialdir=os.getcwd()
        )
        if directory:
            self.output_var.set(directory)
    
    def log(self, message, level="INFO"):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        colors = {
            "INFO": "#4ec9b0",
            "SUCCESS": "#4ec9b0",
            "WARNING": "#dcdcaa",
            "ERROR": "#f48771"
        }
        
        color = colors.get(level, "#d4d4d4")
        
        self.log_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
        self.log_text.insert(tk.END, f"[{level}] ", level)
        self.log_text.insert(tk.END, f"{message}\n")
        
        self.log_text.tag_config("timestamp", foreground="#808080")
        self.log_text.tag_config(level, foreground=color)
        
        self.log_text.see(tk.END)
        self.root.update()
    
    def preview_data(self, data):
        """预览数据"""
        self.preview_text.delete('1.0', tk.END)
        
        if isinstance(data, list):
            preview = json.dumps(data[:5], ensure_ascii=False, indent=2)
            self.preview_text.insert('1.0', f"前 5 条数据预览:\n\n{preview}")
        else:
            preview = json.dumps(data, ensure_ascii=False, indent=2)
            self.preview_text.insert('1.0', f"数据预览:\n\n{preview}")
    
    def get_selectors(self):
        """获取选择器配置"""
        selectors = {}
        for item in self.selector_tree.get_children():
            values = self.selector_tree.item(item, 'values')
            field_name = values[0]
            selector = values[1]
            selectors[field_name] = selector
        return selectors
    
    def start_crawling(self):
        """开始爬取"""
        # 验证输入
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("警告", "请输入目标 URL！")
            return
        
        selectors = self.get_selectors()
        if not selectors:
            messagebox.showwarning("警告", "请至少添加一个字段选择器！")
            return
        
        # 更新UI状态
        self.is_crawling = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_var.set("正在爬取...")
        self.progress.start()
        
        # 清空日志和预览
        self.log_text.delete('1.0', tk.END)
        self.preview_text.delete('1.0', tk.END)
        
        # 在新线程中运行爬虫
        thread = threading.Thread(
            target=self.run_crawler,
            args=(url, selectors)
        )
        thread.daemon = True
        thread.start()
    
    def run_crawler(self, url, selectors):
        """运行爬虫（在后台线程中）"""
        try:
            self.log(f"开始爬取: {url}", "INFO")
            self.log(f"爬取模式: {'列表页面' if self.mode_var.get() == 'list' else '单个页面'}", "INFO")
            self.log(f"字段数量: {len(selectors)}", "INFO")
            self.log("-" * 50, "INFO")
            
            # 创建爬虫实例
            crawler = UniversalCrawler(
                base_url=url,
                output_dir=self.output_var.get()
            )
            
            # 根据模式爬取
            if self.mode_var.get() == 'list':
                # 列表模式
                list_selector = self.list_selector_entry.get().strip()
                if not list_selector:
                    self.log("列表容器选择器不能为空！", "ERROR")
                    return
                
                self.log(f"列表容器: {list_selector}", "INFO")
                
                results = crawler.crawl_list_page(
                    url,
                    list_selector,
                    selectors,
                    max_items=self.limit_var.get()
                )
                
                if results:
                    self.log(f"成功提取 {len(results)} 条数据", "SUCCESS")
                    
                    # 预览数据
                    self.root.after(0, lambda: self.preview_data(results))
                    
                    # 保存数据
                    filename = f"crawled_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    if self.format_var.get() == 'json':
                        filepath = crawler.save_to_json(results, filename)
                    else:
                        filepath = crawler.save_to_csv(results, filename)
                    
                    if filepath:
                        self.log(f"数据已保存: {filepath}", "SUCCESS")
                        self.root.after(0, lambda: messagebox.showinfo(
                            "完成",
                            f"爬取完成！\n提取了 {len(results)} 条数据\n保存位置: {filepath}"
                        ))
                else:
                    self.log("没有提取到数据", "WARNING")
                    self.root.after(0, lambda: messagebox.showwarning(
                        "警告",
                        "没有提取到数据，请检查选择器是否正确"
                    ))
            else:
                # 单页模式
                data = crawler.crawl_single_page(url, selectors)
                
                if data:
                    self.log("成功提取数据", "SUCCESS")
                    
                    # 预览数据
                    self.root.after(0, lambda: self.preview_data(data))
                    
                    # 保存数据
                    filename = f"crawled_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    filepath = crawler.save_to_json(data, filename)
                    
                    if filepath:
                        self.log(f"数据已保存: {filepath}", "SUCCESS")
                        self.root.after(0, lambda: messagebox.showinfo(
                            "完成",
                            f"爬取完成！\n保存位置: {filepath}"
                        ))
                else:
                    self.log("没有提取到数据", "WARNING")
            
            # 显示统计
            stats = crawler.get_stats()
            self.log("-" * 50, "INFO")
            self.log(f"爬取统计:", "INFO")
            self.log(f"  总页面数: {stats['total_pages']}", "INFO")
            self.log(f"  成功: {stats['success_pages']}", "INFO")
            self.log(f"  失败: {stats['failed_pages']}", "INFO")
            self.log(f"  总数据条数: {stats['total_items']}", "INFO")
            
        except Exception as e:
            self.log(f"爬取失败: {e}", "ERROR")
            self.root.after(0, lambda: messagebox.showerror("错误", f"爬取失败:\n{e}"))
        
        finally:
            self.root.after(0, self.crawling_finished)
    
    def stop_crawling(self):
        """停止爬取"""
        self.is_crawling = False
        self.log("正在停止...", "WARNING")
    
    def crawling_finished(self):
        """爬取完成后的清理"""
        self.is_crawling = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_var.set("✅ 就绪")
        self.progress.stop()


def main():
    """主函数"""
    root = tk.Tk()
    
    # 设置主题
    style = ttk.Style()
    try:
        style.theme_use('clam')
    except:
        pass
    
    # 设置窗口图标（如果有的话）
    try:
        root.iconbitmap('icon.ico')
    except:
        pass
    
    app = UniversalCrawlerGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
