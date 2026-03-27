#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试通用爬虫 GUI 的响应式布局
"""

import sys
import os

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from universal_crawler_gui import UniversalCrawlerGUI
import tkinter as tk
from tkinter import ttk

def test_responsive_layout():
    """测试响应式布局"""
    root = tk.Tk()
    
    # 设置主题
    style = ttk.Style()
    try:
        style.theme_use('clam')
    except:
        pass
    
    # 创建 GUI
    app = UniversalCrawlerGUI(root)
    
    # 添加测试说明
    info_text = """
    响应式布局测试说明：
    
    1. 尝试拖动窗口边缘来改变窗口大小
    2. 所有组件应该随窗口大小自动调整
    3. 最小窗口大小：900x600
    4. 左右两侧按比例分配空间（2:3）
    5. 选择器表格、日志和预览区域会自动扩展
    
    测试项目：
    ✓ 缩小窗口 - 所有组件应该保持可见
    ✓ 放大窗口 - 组件应该自动扩展填充空间
    ✓ 改变宽度 - 左右两侧按比例调整
    ✓ 改变高度 - 可扩展区域自动调整
    """
    
    print(info_text)
    
    # 运行主循环
    root.mainloop()

if __name__ == '__main__':
    test_responsive_layout()
