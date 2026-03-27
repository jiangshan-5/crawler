#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图标爬虫 GUI 版本
使用 Tkinter 创建图形界面
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import os
import sys
from datetime import datetime

# 导入爬虫模块
try:
    from multi_source_icon_crawler import MultiSourceIconCrawler
    from apply_icons_to_miniapp import IconApplier
except ImportError:
    # 如果打包成 exe，需要调整导入路径
    import importlib.util
    
    def load_module(name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    MultiSourceIconCrawler = load_module('multi_source_icon_crawler', 
                                         os.path.join(base_dir, 'multi_source_icon_crawler.py')).MultiSourceIconCrawler
    IconApplier = load_module('apply_icons_to_miniapp',
                              os.path.join(base_dir, 'apply_icons_to_miniapp.py')).IconApplier


class IconCrawlerGUI:
    """图标爬虫图形界面"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("图标爬虫工具 v1.0")
        self.root.geometry("800x600")
        
        # 设置图标（如果有的话）
        try:
            self.root.iconbitmap('icon.ico')
        except:
            pass
        
        # 变量
        self.is_crawling = False
        self.crawler = None
        
        # 创建界面
        self.create_widgets()
        
    def create_widgets(self):
        """创建界面组件"""
        
        # 标题
        title_frame = ttk.Frame(self.root, padding="10")
        title_frame.pack(fill=tk.X)
        
        title_label = ttk.Label(
            title_frame, 
            text="🎨 图标爬虫工具", 
            font=("Arial", 16, "bold")
        )
        title_label.pack()
        
        subtitle_label = ttk.Label(
            title_frame,
            text="从多个免费图标网站爬取图标",
            font=("Arial", 10)
        )
        subtitle_label.pack()
        
        # 主容器
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧：配置区域
        left_frame = ttk.LabelFrame(main_frame, text="配置", padding="10")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # 来源选择
        source_frame = ttk.LabelFrame(left_frame, text="选择图标来源", padding="10")
        source_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.source_vars = {}
        sources = [
            ('feather', 'Feather Icons (推荐)', True),
            ('heroicons', 'Heroicons (推荐)', True),
            ('iconmonstr', 'Iconmonstr', False),
            ('icons8', 'Icons8', False),
            ('flaticon', 'Flaticon', False)
        ]
        
        for value, text, default in sources:
            var = tk.BooleanVar(value=default)
            self.source_vars[value] = var
            cb = ttk.Checkbutton(source_frame, text=text, variable=var)
            cb.pack(anchor=tk.W)
        
        # 关键词输入
        keyword_frame = ttk.LabelFrame(left_frame, text="搜索关键词", padding="10")
        keyword_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(keyword_frame, text="每行一个关键词:").pack(anchor=tk.W)
        
        self.keyword_text = scrolledtext.ScrolledText(
            keyword_frame, 
            height=6, 
            width=30,
            font=("Consolas", 10)
        )
        self.keyword_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        self.keyword_text.insert('1.0', 'list\nadd\nchart\nsettings')
        
        # 下载数量
        limit_frame = ttk.Frame(left_frame)
        limit_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(limit_frame, text="每个关键词下载数量:").pack(side=tk.LEFT)
        self.limit_var = tk.IntVar(value=3)
        limit_spinbox = ttk.Spinbox(
            limit_frame, 
            from_=1, 
            to=10, 
            textvariable=self.limit_var,
            width=10
        )
        limit_spinbox.pack(side=tk.LEFT, padx=(5, 0))
        
        # 输出目录
        output_frame = ttk.LabelFrame(left_frame, text="输出目录", padding="10")
        output_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.output_var = tk.StringVar(value="data/icons_comparison")
        output_entry = ttk.Entry(output_frame, textvariable=self.output_var)
        output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        browse_btn = ttk.Button(
            output_frame, 
            text="浏览...", 
            command=self.browse_output_dir,
            width=10
        )
        browse_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # 操作按钮
        button_frame = ttk.Frame(left_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.start_btn = ttk.Button(
            button_frame,
            text="🚀 开始爬取",
            command=self.start_crawling,
            style="Accent.TButton"
        )
        self.start_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.stop_btn = ttk.Button(
            button_frame,
            text="⏹ 停止",
            command=self.stop_crawling,
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 应用到小程序按钮
        apply_frame = ttk.Frame(left_frame)
        apply_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.apply_btn = ttk.Button(
            apply_frame,
            text="📱 应用到小程序",
            command=self.apply_to_miniapp
        )
        self.apply_btn.pack(fill=tk.X)
        
        # 右侧：日志区域
        right_frame = ttk.LabelFrame(main_frame, text="运行日志", padding="10")
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.log_text = scrolledtext.ScrolledText(
            right_frame,
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#d4d4d4"
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 底部：状态栏
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(
            status_frame, 
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        status_label.pack(fill=tk.X, padx=5, pady=2)
        
        # 进度条
        self.progress = ttk.Progressbar(
            status_frame,
            mode='indeterminate'
        )
        self.progress.pack(fill=tk.X, padx=5, pady=2)
        
    def browse_output_dir(self):
        """浏览输出目录"""
        directory = filedialog.askdirectory(
            title="选择输出目录",
            initialdir=os.getcwd()
        )
        if directory:
            self.output_var.set(directory)
    
    def log(self, message, level="INFO"):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 颜色标签
        colors = {
            "INFO": "#4ec9b0",
            "SUCCESS": "#4ec9b0",
            "WARNING": "#dcdcaa",
            "ERROR": "#f48771"
        }
        
        color = colors.get(level, "#d4d4d4")
        
        self.log_text.insert(
            tk.END,
            f"[{timestamp}] ",
            "timestamp"
        )
        self.log_text.insert(
            tk.END,
            f"[{level}] ",
            level
        )
        self.log_text.insert(
            tk.END,
            f"{message}\n"
        )
        
        # 配置标签颜色
        self.log_text.tag_config("timestamp", foreground="#808080")
        self.log_text.tag_config(level, foreground=color)
        
        # 自动滚动到底部
        self.log_text.see(tk.END)
        self.root.update()
    
    def get_selected_sources(self):
        """获取选中的来源"""
        return [source for source, var in self.source_vars.items() if var.get()]
    
    def get_keywords(self):
        """获取关键词列表"""
        text = self.keyword_text.get('1.0', tk.END).strip()
        keywords = [k.strip() for k in text.split('\n') if k.strip()]
        return keywords
    
    def start_crawling(self):
        """开始爬取"""
        # 验证输入
        sources = self.get_selected_sources()
        if not sources:
            messagebox.showwarning("警告", "请至少选择一个图标来源！")
            return
        
        keywords = self.get_keywords()
        if not keywords:
            messagebox.showwarning("警告", "请至少输入一个关键词！")
            return
        
        # 更新UI状态
        self.is_crawling = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_var.set("正在爬取...")
        self.progress.start()
        
        # 清空日志
        self.log_text.delete('1.0', tk.END)
        
        # 在新线程中运行爬虫
        thread = threading.Thread(
            target=self.run_crawler,
            args=(sources, keywords, self.limit_var.get(), self.output_var.get())
        )
        thread.daemon = True
        thread.start()
    
    def run_crawler(self, sources, keywords, limit, output_dir):
        """运行爬虫（在后台线程中）"""
        try:
            self.log(f"开始爬取图标...", "INFO")
            self.log(f"来源: {', '.join(sources)}", "INFO")
            self.log(f"关键词: {', '.join(keywords)}", "INFO")
            self.log(f"下载数量: {limit}", "INFO")
            self.log(f"输出目录: {output_dir}", "INFO")
            self.log("-" * 50, "INFO")
            
            # 创建爬虫实例
            crawler = MultiSourceIconCrawler(output_dir=output_dir)
            all_results = []
            
            # 爬取每个关键词
            for keyword in keywords:
                if not self.is_crawling:
                    self.log("爬取已停止", "WARNING")
                    break
                
                self.log(f"\n搜索关键词: {keyword}", "INFO")
                icons = []
                
                # 根据选择的来源进行搜索
                for source in sources:
                    if not self.is_crawling:
                        break
                    
                    try:
                        self.log(f"正在搜索 {source}...", "INFO")
                        
                        if source == 'feather':
                            icons.extend(crawler.search_feather_icons(keyword))
                        elif source == 'heroicons':
                            icons.extend(crawler.search_heroicons(keyword))
                        elif source == 'iconmonstr':
                            icons.extend(crawler.search_iconmonstr(keyword, limit))
                        elif source == 'icons8':
                            icons.extend(crawler.search_icons8(keyword, limit))
                        elif source == 'flaticon':
                            icons.extend(crawler.search_flaticon(keyword, limit))
                    except Exception as e:
                        self.log(f"{source} 搜索失败: {e}", "ERROR")
                
                self.log(f"找到 {len(icons)} 个图标", "SUCCESS")
                
                # 下载图标
                if icons:
                    results = crawler.download_all_icons(icons)
                    all_results.extend(results)
            
            # 保存结果
            if all_results:
                crawler.save_results(all_results)
                
                success_count = sum(1 for r in all_results if r.get('downloaded'))
                self.log("-" * 50, "INFO")
                self.log(f"爬取完成！成功: {success_count}/{len(all_results)}", "SUCCESS")
                self.log(f"图标保存在: {output_dir}", "SUCCESS")
                
                # 显示完成对话框
                self.root.after(0, lambda: messagebox.showinfo(
                    "完成",
                    f"爬取完成！\n成功下载: {success_count} 个图标\n保存位置: {output_dir}"
                ))
            else:
                self.log("没有下载任何图标", "WARNING")
                self.root.after(0, lambda: messagebox.showwarning(
                    "警告",
                    "没有成功下载任何图标，请检查网络连接或尝试其他来源"
                ))
            
        except Exception as e:
            self.log(f"爬取失败: {e}", "ERROR")
            self.root.after(0, lambda: messagebox.showerror("错误", f"爬取失败:\n{e}"))
        
        finally:
            # 恢复UI状态
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
        self.status_var.set("就绪")
        self.progress.stop()
    
    def apply_to_miniapp(self):
        """应用到小程序"""
        # 选择来源
        sources = ['feather', 'heroicons', 'iconmonstr']
        
        dialog = tk.Toplevel(self.root)
        dialog.title("应用到小程序")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(
            dialog,
            text="选择要应用的图标来源:",
            font=("Arial", 10, "bold")
        ).pack(pady=10)
        
        source_var = tk.StringVar(value='feather')
        
        for source in sources:
            ttk.Radiobutton(
                dialog,
                text=source.capitalize(),
                variable=source_var,
                value=source
            ).pack(anchor=tk.W, padx=20)
        
        ttk.Label(dialog, text="\n输入要应用的图标名称（用空格分隔）:").pack()
        
        icons_entry = ttk.Entry(dialog, width=40)
        icons_entry.pack(pady=5)
        icons_entry.insert(0, "list add chart settings")
        
        def do_apply():
            source = source_var.get()
            icons_text = icons_entry.get().strip()
            icons = icons_text.split() if icons_text else None
            
            dialog.destroy()
            
            # 在新线程中应用
            thread = threading.Thread(
                target=self.run_apply,
                args=(source, icons)
            )
            thread.daemon = True
            thread.start()
        
        ttk.Button(
            dialog,
            text="应用",
            command=do_apply
        ).pack(pady=20)
    
    def run_apply(self, source, icons):
        """运行应用（在后台线程中）"""
        try:
            self.log(f"\n开始应用图标到小程序...", "INFO")
            self.log(f"来源: {source}", "INFO")
            if icons:
                self.log(f"图标: {', '.join(icons)}", "INFO")
            
            applier = IconApplier()
            results = applier.process_icons(source=source, icon_names=icons)
            
            if results:
                self.log(f"成功应用 {len(results)} 组图标", "SUCCESS")
                self.log("请重新编译小程序查看效果", "INFO")
                
                self.root.after(0, lambda: messagebox.showinfo(
                    "完成",
                    f"成功应用 {len(results)} 组图标！\n\n下一步:\n1. 重新编译小程序\n2. 在微信开发者工具中查看效果"
                ))
            else:
                self.log("没有找到可应用的图标", "WARNING")
                
        except Exception as e:
            self.log(f"应用失败: {e}", "ERROR")
            self.root.after(0, lambda: messagebox.showerror("错误", f"应用失败:\n{e}"))


def main():
    """主函数"""
    root = tk.Tk()
    
    # 设置主题
    style = ttk.Style()
    try:
        style.theme_use('clam')
    except:
        pass
    
    app = IconCrawlerGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
