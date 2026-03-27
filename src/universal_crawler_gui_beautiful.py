#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用爬虫 GUI 美化版本
现代化设计，支持用户自定义 URL、选择器、爬取数量等
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


class ModernStyle:
    """现代化样式配置"""
    
    # 配色方案 - 现代蓝绿色调
    PRIMARY = "#2196F3"      # 主色调 - 蓝色
    SECONDARY = "#00BCD4"    # 次要色 - 青色
    SUCCESS = "#4CAF50"      # 成功 - 绿色
    WARNING = "#FF9800"      # 警告 - 橙色
    ERROR = "#F44336"        # 错误 - 红色
    
    BG_DARK = "#1e1e1e"      # 深色背景
    BG_LIGHT = "#f5f5f5"     # 浅色背景
    TEXT_DARK = "#212121"    # 深色文字
    TEXT_LIGHT = "#ffffff"   # 浅色文字
    TEXT_GRAY = "#757575"    # 灰色文字
    
    BORDER = "#e0e0e0"       # 边框颜色
    HOVER = "#e3f2fd"        # 悬停背景
    
    # 字体
    FONT_TITLE = ("Microsoft YaHei UI", 16, "bold")
    FONT_SUBTITLE = ("Microsoft YaHei UI", 10)
    FONT_LABEL = ("Microsoft YaHei UI", 9)
    FONT_CODE = ("Consolas", 9)


class UniversalCrawlerGUI:
    """通用爬虫图形界面 - 美化版"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("🕷️ 通用网页爬虫工具 v2.0")
        self.root.geometry("1300x750")
        self.root.minsize(1000, 650)
        
        # 设置窗口背景色
        self.root.configure(bg=ModernStyle.BG_LIGHT)
        
        # 配置根窗口权重
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)
        
        # 变量
        self.is_crawling = False
        self.crawler = None
        
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
        
        # 自定义按钮样式 - 主按钮
        style.configure(
            "Primary.TButton",
            background=ModernStyle.PRIMARY,
            foreground=ModernStyle.TEXT_LIGHT,
            borderwidth=0,
            focuscolor='none',
            padding=(20, 10),
            font=("Microsoft YaHei UI", 10, "bold")
        )
        style.map("Primary.TButton",
            background=[('active', ModernStyle.SECONDARY), ('disabled', '#BDBDBD')]
        )
        
        # 自定义按钮样式 - 次要按钮
        style.configure(
            "Secondary.TButton",
            background=ModernStyle.BG_LIGHT,
            foreground=ModernStyle.TEXT_DARK,
            borderwidth=1,
            relief="solid",
            padding=(15, 8),
            font=("Microsoft YaHei UI", 9)
        )
        
        # 自定义 LabelFrame 样式
        style.configure(
            "Modern.TLabelframe",
            background=ModernStyle.BG_LIGHT,
            borderwidth=2,
            relief="groove"
        )
        style.configure(
            "Modern.TLabelframe.Label",
            background=ModernStyle.BG_LIGHT,
            foreground=ModernStyle.PRIMARY,
            font=("Microsoft YaHei UI", 10, "bold")
        )
