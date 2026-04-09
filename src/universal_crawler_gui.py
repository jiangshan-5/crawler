#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modern Universal Crawler Workflow - V3 (CustomTkinter Edition)
High-performance, Aesthetic UI for Universal Scraper
"""

import json
import os
import queue
import sys
import threading
import time
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import customtkinter as ctk
from PIL import Image

# Core Modules
import traceback

try:
    from universal_crawler_v2 import UniversalCrawlerV2 as UniversalCrawler
except (ImportError, Exception) as e:
    print(f"CRITICAL: Failed to import UniversalCrawlerV2: {e}")
    traceback.print_exc()
    UniversalCrawler = None

try:
    from advanced_crawler import AdvancedCrawler, is_advanced_mode_available
except (ImportError, Exception) as e:
    print(f"WARNING: Failed to import AdvancedCrawler: {e}")
    AdvancedCrawler = None
    if 'is_advanced_mode_available' not in locals():
        def is_advanced_mode_available(): return False
try:
    from website_templates import WEBSITE_TEMPLATES
except ImportError:
    WEBSITE_TEMPLATES = {}

# Global Constants
APP_TITLE = "Universal Crawler Workbench"
APP_SUBTITLE = "Premium Workspace for High-Performance Scraping"
DEFAULT_OUTPUT_DIR = os.path.join("data", "crawled_data")

# --- Styling (Modern Light) ---
COLORS = {
    "bg": "#f1f5f9",       # Soft Slate
    "sidebar": "#ffffff",
    "card": "#ffffff",
    "primary": "#2563eb",  # Modern Blue (Tailwind 600)
    "secondary": "#0f172a", # Dark Navy for text
    "accent": "#f59e0b",
    "border": "#e2e8f0",   # Light border
    "entry_bg": "#ffffff",
    "text": "#1e293b",
    "text_dark": "#475569"
}

# --- I18N ---
TRANSLATIONS = {
    "zh": {
        "nav_dashboard": "仪表盘",
        "nav_config": "配置中心",
        "nav_logs": "实时日志",
        "theme": "外观模式",
        "lang": "语言设置",
        "dash_title": "性能监控看板",
        "stat_status": "运行状态",
        "stat_pages": "已爬取页面",
        "stat_items": "已提取条数",
        "stat_saved": "最近保存文件",
        "launch": "🚀 启动爬虫引擎",
        "stop": "停止运行",
        "cfg_target": "🎯 目标网页配置",
        "cfg_url_placeholder": "在此输入目标 URL...",
        "cfg_mode": "抓取模式",
        "mode_list": "列表页模式",
        "mode_single": "单页模式",
        "cfg_adv": "高级反反爬模式",
        "cfg_templates": "📦 快速模板库",
        "cfg_selector_ws": "🧩 选择器工作区",
        "cfg_list_sel_placeholder": "列表容器选择器 (如 .item-row)",
        "tree_col_field": "字段名称",
        "tree_col_sel": "CSS 选择器",
        "btn_add": "+ 新增",
        "btn_del": "- 删除",
        "logs_title": "实时运行日志",
        "btn_clear": "清空日志",
        "cfg_exec_title": "🚀 执行控制中心",
        "history_title": "📜 历史任务回溯",
        "history_col_date": "日期",
        "history_col_folder": "结果目录",
        "btn_open_folder": "📂 打开文件夹",
        "btn_refresh": "🔄 刷新",
        "status_ready": "就绪",
        "status_running": "运行中",
        "status_finished": "完成",
        "status_error": "错误",
        "progress_label": "任务进度",
        "stat_success_rate": "成功率",
        "btn_launching": "⏳ 正在启动...",
        "btn_crawling": "🕷️ 正在爬取...",
        "msg_url_req": "必须输入目标 URL",
        "msg_success": "成功：提取了 {} 条数据",
        "msg_init": "正在初始化爬虫引擎..."
    },
    "en": {
        "nav_dashboard": "Dashboard",
        "nav_config": "Configuration",
        "nav_logs": "Live Activity",
        "theme": "Appearance",
        "lang": "Language",
        "dash_title": "Performance Dashboard",
        "stat_status": "Status",
        "stat_pages": "Pages",
        "stat_items": "Items",
        "stat_saved": "Last File",
        "launch": "🚀 LAUNCH CRAWLER",
        "stop": "STOP",
        "cfg_target": "🎯 Target Configuration",
        "cfg_url_placeholder": "Enter target URL here...",
        "cfg_mode": "Crawl Mode",
        "mode_list": "List Mode",
        "mode_single": "Single Page",
        "cfg_adv": "Advanced Anti-Bot",
        "cfg_templates": "📦 Quick Templates",
        "cfg_selector_ws": "🧩 Selector Workspace",
        "cfg_list_sel_placeholder": "List Container Selector (e.g. .item-row)",
        "tree_col_field": "Field Name",
        "tree_col_sel": "CSS Selector",
        "btn_add": "+ Add",
        "btn_del": "- Del",
        "logs_title": "Live Activity Logs",
        "btn_clear": "Clear Logs",
        "cfg_exec_title": "🚀 Execution Center",
        "history_title": "📜 Crawl History",
        "history_col_date": "Date",
        "history_col_folder": "Result Folder",
        "btn_open_folder": "📂 Open Folder",
        "btn_refresh": "🔄 Refresh",
        "status_ready": "Ready",
        "status_running": "Running",
        "status_finished": "Finished",
        "status_error": "Error",
        "progress_label": "Progress",
        "stat_success_rate": "Success Rate",
        "btn_launching": "⏳ Launching...",
        "btn_crawling": "🕷️ Crawling...",
        "msg_url_req": "Target URL is required.",
        "msg_success": "Success: Extracted {} items.",
        "msg_init": "Initializing Crawler Engine..."
    }
}

# --- Templates & Selectors ---
EXAMPLE_SELECTORS = [
    ("Title", "h1", "Page main title"),
    ("Link", "a@href", "Target link URL"),
    ("Image", "img@src", "Target image URL"),
]

BUILTIN_TEMPLATES = {
    "flaticon": {
        "name": "Flaticon Icons",
        "description": "Scrape icons from Flaticon list pages.",
        "mode": "list",
        "example_url": "https://www.flaticon.com/free-icons/weather",
        "list_selector": '.icon--item || li:has(a[href*="/free-icon/"])',
        "fields": {
            "Icon Image": "img.icon--item__img@src || img@src || img@data-src",
            "Icon Title": ".icon--item__title || img@alt || @title",
            "Icon Link": "a.icon--item__link@href || a@href",
        },
    },
    "github_trending": {
        "name": "GitHub Trending",
        "description": "Scrape daily trending repositories on GitHub.",
        "mode": "list",
        "example_url": "https://github.com/trending",
        "list_selector": "article.Box-row",
        "fields": {
            "Repo Name": "h2 a",
            "Repo Link": "h2 a@href",
            "Language": 'span[itemprop="programmingLanguage"]',
            "Stars": "svg.octicon-star ~ span",
        },
    },
    "novel_generic": {
        "name": "Generic Novel Site",
        "description": "General purpose selector for biquge-like novel sites.",
        "mode": "list",
        "example_url": "https://www.biquuge.com/top/",
        "list_selector": "li:has(h3 a) || li:has(h4 a) || .bookbox",
        "fields": {
            "Book Title": ".book-title || h4 a || h3 a",
            "Author": ".author || .writer",
            "Latest Chapter": ".update a || .latest-chapter a",
            "Cover": "img@src || img@data-src",
        },
    }
}

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue") # We will override largely
        
        self.title(APP_TITLE)
        self.geometry("1400x900")
        self.configure(fg_color=COLORS["bg"])
        
        ctk.set_appearance_mode("Light")
        ctk.set_default_color_theme("blue")
        self._setup_ttk_styles()

        # Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # State Variables
        self.is_crawling = False
        self.stop_requested = False
        self.ui_queue = queue.Queue()
        self.current_crawler = None
        
        # Observable Status
        self.lang_var = tk.StringVar(value="zh")
        self.status_var = tk.StringVar(value="Ready")
        self.pages_var = tk.StringVar(value="0")
        self.items_var = tk.StringVar(value="0")
        self.saved_var = tk.StringVar(value="None")
        self.success_rate_var = tk.StringVar(value="0%")
        self.progress_val = tk.DoubleVar(value=0.0)
        self.task_desc_var = tk.StringVar(value="")
        self.btn_text_var = tk.StringVar(value="LAUNCH")
        
        # Inputs
        self.url_var = tk.StringVar()
        self.mode_var = tk.StringVar(value="list")
        self.list_selector_var = tk.StringVar()
        self.limit_var = tk.IntVar(value=10)
        self.delay_var = tk.DoubleVar(value=0.5)
        self.adv_mode_var = tk.BooleanVar(value=False)
        self.output_dir_var = tk.StringVar(value=DEFAULT_OUTPUT_DIR)
        self.format_var = tk.StringVar(value="json")

        # Assets
        self.icons = {}
        self._load_icons()

        # Components
        self._build_sidebar()
        self._build_main_view()
        
        # Initialize Language Labels
        self.update_language()
        
        self.after(100, self.process_ui_queue)

    def _setup_ttk_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", 
                        background="#ffffff", 
                        foreground=COLORS["text"],
                        rowheight=30,
                        fieldbackground="#ffffff",
                        bordercolor=COLORS["border"],
                        borderwidth=0,
                        font=("Segoe UI", 10))
        style.configure("Treeview.Heading", 
                        background="#f8fafc", 
                        foreground=COLORS["text"],
                        relief="flat",
                        font=("Segoe UI", 10, "bold"))
        style.map("Treeview", background=[('selected', COLORS["primary"])], foreground=[('selected', "#ffffff")])
        style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})]) # Remove borders

    def _load_icons(self):
        # Pointing to our fresh crawled icons in src/assets
        path = os.path.join(os.path.dirname(__file__), "assets")
        icon_names = ["dashboard", "config", "history", "logs", "lang", "add", "del", "logo"]
        for icon_name in icon_names:
            file_path = os.path.join(path, f"{icon_name}.png")
            if os.path.exists(file_path):
                img = Image.open(file_path)
                self.icons[icon_name] = ctk.CTkImage(light_image=img, dark_image=img, size=(20, 20))
            else:
                print(f"Warning: Icon {icon_name} missing at {file_path}")

    def _get_icon(self, name, size=(24, 24)):
        try:
            # Load from our newly crawled src/assets
            path = os.path.join(os.path.dirname(__file__), "assets", f"{name}.png")
            if os.path.exists(path):
                img = Image.open(path)
                return ctk.CTkImage(light_image=img, dark_image=img, size=size)
        except Exception: pass
        return None

    def _build_sidebar(self):
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color=COLORS["sidebar"], border_width=1, border_color="#1a1c23")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(10, weight=1)

        # Sidebar Header: Logo + Title
        self.sidebar_header = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.sidebar_header.grid(row=0, column=0, padx=20, pady=(40, 40), sticky="ew")
        
        logo_img = self.icons.get("logo", None)
        if logo_img:
            logo_img.configure(size=(32, 32))
            self.logo_icon = ctk.CTkLabel(self.sidebar_header, image=logo_img, text="")
            self.logo_icon.pack(side="left")
            
        self.logo_text = ctk.CTkLabel(self.sidebar_header, text="  工作台", 
                                      font=ctk.CTkFont(size=22, weight="bold"),
                                      text_color=COLORS["primary"])
        self.logo_text.pack(side="left")

        # Nav Buttons
        btn_params = {"height": 50, "corner_radius": 12, "anchor": "w", "font": ctk.CTkFont(size=14, weight="bold")}
        
        self.nav_config = ctk.CTkButton(self.sidebar, text="  配置中心", **btn_params,
                                         image=self._get_icon("config"),
                                         fg_color=COLORS["primary"], text_color="#ffffff", hover_color="#1d4ed8",
                                         command=lambda: self._select_tab("config"))
        self.nav_config.grid(row=1, column=0, padx=15, pady=5, sticky="ew")

        self.nav_dashboard = ctk.CTkButton(self.sidebar, text="  仪表盘", **btn_params,
                                            image=self._get_icon("dashboard"),
                                            fg_color="transparent", text_color=COLORS["text"], hover_color="#f1f5f9",
                                            command=lambda: self._select_tab("dashboard"))
        self.nav_dashboard.grid(row=2, column=0, padx=15, pady=5, sticky="ew")

        self.nav_logs = ctk.CTkButton(self.sidebar, text="  实时日志", **btn_params,
                                       image=self._get_icon("logs"),
                                       fg_color="transparent", text_color=COLORS["text"], hover_color="#f1f5f9",
                                       command=lambda: self._select_tab("logs"))
        self.nav_logs.grid(row=3, column=0, padx=15, pady=5, sticky="ew")

        self.nav_history = ctk.CTkButton(self.sidebar, text="  历史记录", **btn_params,
                                          image=self._get_icon("history"),
                                          fg_color="transparent", text_color=COLORS["text"], hover_color="#f1f5f9",
                                          command=lambda: self._select_tab("history"))
        self.nav_history.grid(row=4, column=0, padx=15, pady=5, sticky="ew")

        # Sidebar Footer
        self.sidebar_footer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.sidebar_footer.grid(row=10, column=0, sticky="s", pady=20)
        
        self.lang_btn = ctk.CTkButton(self.sidebar_footer, text="  EN / 中文", image=self._get_icon("lang"),
                                       height=32, corner_radius=20, 
                                       fg_color="transparent", border_width=1, border_color="#e2e8f0",
                                       text_color=COLORS["text"],
                                       command=self.toggle_language)
        self.lang_btn.pack(pady=10)

    def toggle_language(self):
        curr = self.lang_var.get()
        self.lang_var.set("en" if curr == "zh" else "zh")
        self.update_language()

    def trigger_demo_crawl(self):
        """Autonomous demo: GitHub Trending."""
        self.log("--- ⚡ SYSTEM INITIALIZING CYBERPUNK DEMO ---", "INFO")
        self.url_var.set("https://github.com/trending/python?since=daily")
        self.list_selector_var.set("article.Box-row")
        self.current_selectors = {
            "Repository": "h2 a",
            "Description": "p.col-9",
            "Stars": "svg.octicon-star + span || .f6 a[href$='stargazers']",
            "Language": "span[itemprop='programmingLanguage']"
        }
        self.mode_var.set("list")
        self._select_tab("logs")
        self.after(1000, self.start_crawl)

    def update_language(self):
        lang = self.lang_var.get()
        t = TRANSLATIONS[lang]
        
        self.nav_dashboard.configure(text=t["nav_dashboard"])
        self.nav_config.configure(text=t["nav_config"])
        self.nav_logs.configure(text=t["nav_logs"])
        
        # Update Frames
        for frame in self.frames.values():
            if hasattr(frame, "update_lang"):
                frame.update_lang(t)
        
        # Update Status Var if it matches a key
        curr_status = self.status_var.get()
        # Initial set
        if curr_status in ["Ready", "就绪"]: self.status_var.set(t["status_ready"])

    def _build_main_view(self):
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=0, column=1, sticky="nsew", padx=25, pady=25)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        # Container for views
        self.frames = {}
        
        # 1. Dashboard
        self.dash_frame = DashboardFrame(self.content, self)
        self.frames["dashboard"] = self.dash_frame
        
        # 2. Config
        self.cfg_frame = ConfigFrame(self.content, self)
        self.frames["config"] = self.cfg_frame
        
        # 3. Logs
        self.logs_frame = LogsFrame(self.content, self)
        self.frames["logs"] = self.logs_frame

        self._select_tab("config")

    def _select_tab(self, name):
        for f in self.frames.values(): f.grid_forget()
        self.frames[name].grid(row=0, column=0, sticky="nsew")
        
        # Refresh history if dashboard
        if name == "dashboard" and hasattr(self.frames[name], "refresh_history"):
            self.frames[name].refresh_history()
        
        # Update Nav Styles
        self.nav_dashboard.configure(fg_color=COLORS["primary"] if name == "dashboard" else "transparent",
                                      text_color="#ffffff" if name == "dashboard" else COLORS["text"])
        self.nav_config.configure(fg_color=COLORS["primary"] if name == "config" else "transparent",
                                   text_color="#ffffff" if name == "config" else COLORS["text"])
        self.nav_logs.configure(fg_color=COLORS["primary"] if name == "logs" else "transparent",
                                 text_color="#ffffff" if name == "logs" else COLORS["text"])

    # --- Worker Thread Logic ---
    def process_ui_queue(self):
        try:
            while True:
                callback, args, kwargs = self.ui_queue.get_nowait()
                callback(*args, **kwargs)
        except queue.Empty:
            pass
        self.after(60, self.process_ui_queue)

    def log(self, message, level="INFO"):
        self.logs_frame.append(message, level)

    def start_crawl(self):
        if UniversalCrawler is None:
            messagebox.showerror("Critical Error", "Crawler core module (universal_crawler_v2.py) could not be loaded.\nCheck terminal for detailed error.")
            return

        if self.is_crawling: return
        url = self.url_var.get().strip()
        if not url:
            lang = self.lang_var.get()
            messagebox.showwarning("Input Error", TRANSLATIONS[lang]["msg_url_req"])
            return

        self.is_crawling = True
        self.stop_requested = False
        lang = self.lang_var.get()
        t = TRANSLATIONS[lang]
        
        # Reset Stats
        self.progress_val.set(0)
        self.pages_var.set("0")
        self.items_var.set("0")
        self.success_rate_var.set("0%")
        self.status_var.set(t["status_running"])
        self.btn_text_var.set(t["btn_launching"])
        self.task_desc_var.set(t["msg_init"])
        
        self.log(f"--- Crawl Initiated: {url} ---", "INFO")
        
        # Switch to Logs Tab
        self._select_tab("logs")
        
        # Get selectors
        selectors = self.current_selectors if self.current_selectors else self.cfg_frame.get_selectors()
        config = {
            "url": url,
            "mode": self.mode_var.get(),
            "list_selector": self.list_selector_var.get(),
            "limit": self.limit_var.get(),
            "delay": self.delay_var.get(),
            "adv": self.adv_mode_var.get(),
            "dir": self.output_dir_var.get(),
            "format": self.format_var.get(),
            "selectors": selectors,
            "workflow": getattr(self, "current_workflow", None),
            "search_url_template": getattr(self, "current_search_template", None)
        }

        threading.Thread(target=self._run_crawler, args=(config,), daemon=True).start()
        
        # Start Polling Stats
        self.after(1000, self.poll_stats)

    def poll_stats(self):
        if not self.is_crawling or not self.current_crawler:
            return
            
        try:
            stats = self.current_crawler.get_stats()
            self.ui_queue.put((self.pages_var.set, (str(stats.get('success_pages', 0)),), {}))
            self.ui_queue.put((self.items_var.set, (str(stats.get('total_items', 0)),), {}))
            self.ui_queue.put((self.success_rate_var.set, (stats.get('success_rate', '0%'),), {}))
            
            # Update Progress Bar if limit is set
            limit = self.limit_var.get()
            if limit > 0:
                prog = min(1.0, stats.get('success_pages', 0) / limit)
                self.ui_queue.put((self.progress_val.set, (prog,), {}))
            else:
                # Indeterminate pulse? CTK pbar doesn't have easy indeterminate mode via var
                pass
                
        except: pass
        
        if self.is_crawling:
            self.after(1000, self.poll_stats)

    def _run_crawler(self, config):
        crawler = None
        try:
            # Detect if it's a flaticon task to force headed mode
            is_flaticon = (config.get("workflow") == "keyword_search" and "flaticon" in (config.get("search_url_template") or "")) or "flaticon" in config["url"]
            
            crawler = UniversalCrawler(
                base_url=config["url"],
                output_dir=config["dir"],
                use_advanced_mode=config["adv"],
                requests_per_second=1.0/max(0.1, config["delay"]),
                is_flaticon_task=is_flaticon
            )
            self.current_crawler = crawler
            
            t = TRANSLATIONS[self.lang_var.get()]
            self.ui_queue.put((self.btn_text_var.set, (t["btn_crawling"],), {}))
            self.ui_queue.put((self.task_desc_var.set, (t["msg_init"],), {}))
            self.ui_queue.put((self.log, (t["msg_init"], "INFO"), {}))
            
            results = None
            if config.get("workflow") == "biquuge_full_book":
                self.ui_queue.put((self.log, ("Detected Book Workflow: Searching and parsing full novel...", "INFO"), {}))
                results = crawler.crawl_biquuge_full_book(config["url"])
            elif config.get("workflow") == "keyword_search" and config.get("search_url_template"):
                search_url = config["search_url_template"].format(query=config["url"])
                self.ui_queue.put((self.log, (f"Searching keyword: {config['url']} -> {search_url}", "INFO"), {}))
                results = crawler.crawl_list_page(
                    search_url, config["list_selector"], config["selectors"], max_items=config["limit"]
                )
            elif config["mode"] == "list":
                results = crawler.crawl_list_page(
                    config["url"], config["list_selector"], config["selectors"], max_items=config["limit"]
                )
            else:
                results = crawler.crawl_single_page(config["url"], config["selectors"])
            
            if results:
                count = len(results) if isinstance(results, list) else 1
                t = TRANSLATIONS[self.lang_var.get()]
                self.ui_queue.put((self.items_var.set, (str(count),), {}))
                self.ui_queue.put((self.log, (t["msg_success"].format(count), "SUCCESS"), {}))
                
                # Save
                fname = f"crawled_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                saved = crawler.save_results(results, fname, preferred_format=config["format"])
                if saved:
                    self.ui_queue.put((self.saved_var.set, (os.path.basename(saved["path"]),), {}))
                    self.ui_queue.put((self.log, (f"Saved to: {saved['path']}", "SUCCESS"), {}))
            else:
                self.ui_queue.put((self.log, ("No data extracted. Please check selectors.", "WARNING"), {}))

        except Exception as e:
            self.ui_queue.put((self.log, (f"Crawler Fault: {e}", "ERROR"), {}))
        finally:
            self.is_crawling = False
            lang = self.lang_var.get()
            t = TRANSLATIONS[lang]
            self.ui_queue.put((self.status_var.set, (t["status_finished"],), {}))
            self.ui_queue.put((self.btn_text_var.set, (t["launch"],), {}))
            self.ui_queue.put((self.progress_val.set, (1.0,), {}))
            if crawler: crawler.close()

    def stop_crawl(self):
        if self.current_crawler:
            self.current_crawler.request_stop()
        self.stop_requested = True
        self.log("⏹ Stop requested. Waiting for current task...", "WARNING")

# --- Views ---

class DashboardFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        self.header.grid_columnconfigure(0, weight=1)
        
        self.title = ctk.CTkLabel(self.header, text="Intelligence Dashboard", font=ctk.CTkFont(size=28, weight="bold"))
        self.title.grid(row=0, column=0, sticky="w")
        
        # Grid area for cards
        self.scroll_canvas = ctk.CTkScrollableFrame(self, fg_color="transparent", label_text="Scanned History")
        self.scroll_canvas.grid(row=1, column=0, sticky="nsew")
        self.scroll_canvas.grid_columnconfigure((0, 1, 2), weight=1)

        # Footer
        self.footer = ctk.CTkFrame(self, fg_color="transparent")
        self.footer.grid(row=2, column=0, sticky="ew", pady=10)
        
        self.btn_refresh = ctk.CTkButton(self.footer, text="Refresh Grid", fg_color=COLORS["primary"], corner_radius=20,
                                          command=self.refresh_history)
        self.btn_refresh.pack(side="right", padx=10)

        self.refresh_history()

    def refresh_history(self):
        for widget in self.scroll_canvas.winfo_children(): widget.destroy()
            
        dir_path = self.controller.output_dir_var.get()
        if not os.path.exists(dir_path): return
        
        try:
            folders = [f for f in os.listdir(dir_path) if os.path.isdir(os.path.join(dir_path, f))]
            folders.sort(reverse=True)
            
            for i, f in enumerate(folders):
                card = ctk.CTkFrame(self.scroll_canvas, fg_color=COLORS["card"], height=160, 
                                     border_width=1, border_color="#e2e8f0", corner_radius=12)
                card.grid(row=i // 3, column=i % 3, padx=10, pady=10, sticky="nsew")
                card.grid_propagate(False)
                
                # Metadata Header
                display_date = f
                if f.startswith("crawled_") and len(f) >= 23:
                    try:
                        dt = datetime.strptime(f[8:23], "%Y%m%d_%H%M%S")
                        display_date = "📅 " + dt.strftime("%Y-%m-%d %H:%M")
                    except: pass
                ctk.CTkLabel(card, text=display_date, font=ctk.CTkFont(size=12, weight="bold"), text_color=COLORS["primary"]).pack(pady=(15, 2))
                ctk.CTkLabel(card, text=f[:25] + "..." if len(f) > 25 else f, font=ctk.CTkFont(size=13), text_color=COLORS["text"]).pack(pady=5)
                # Action Buttons in Card
                btn_frame = ctk.CTkFrame(card, fg_color="transparent")
                btn_frame.pack(side="bottom", fill="x", padx=10, pady=10)
                
                ctk.CTkButton(btn_frame, text="View Data", height=28, fg_color="#333", font=ctk.CTkFont(size=11),
                              command=lambda path=os.path.join(dir_path, f): os.startfile(path)).pack(side="left", expand=True, padx=2)
        except Exception as e:
            print(f"Error loading history: {e}")

    def update_lang(self, t):
        self.title.configure(text=t["history_title"])
        self.scroll_canvas.configure(label_text=t["history_title"])
        self.btn_refresh.configure(text=t["btn_refresh"])

    def _add_stat(self, parent, label, var, col):
        frame = ctk.CTkFrame(parent, height=120)
        frame.grid(row=0, column=col, padx=10, sticky="ew")
        frame.grid_propagate(False)
        
        lbl = ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(size=13, weight="normal"))
        lbl.pack(pady=(20, 0))
        # Store for translation
        if not hasattr(self, "stat_labels"): self.stat_labels = []
        self.stat_labels.append(lbl)
        
        ctk.CTkLabel(frame, textvariable=var, font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(5, 10))

class ConfigFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        
        self.grid_columnconfigure(0, weight=1)

        # Header Row: Quick Templates
        self.tpl_row = ctk.CTkFrame(self, fg_color="transparent")
        self.tpl_row.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
        self.tpl_row.grid_columnconfigure(1, weight=1)
        
        self.tpl_label = ctk.CTkLabel(self.tpl_row, text="📋 选择模板", font=ctk.CTkFont(size=16, weight="bold"))
        self.tpl_label.grid(row=0, column=0, padx=(0, 15))
        
        tpl_names = [tpl["name"] for tpl in WEBSITE_TEMPLATES.values()]
        self.tpl_menu = ctk.CTkOptionMenu(self.tpl_row, values=tpl_names, 
                                         width=220, fg_color=COLORS["card"], text_color=COLORS["text"],
                                         button_color=COLORS["primary"], corner_radius=10,
                                         command=self._apply_template)
        self.tpl_menu.grid(row=0, column=1, sticky="w")

        # Section 2: Precise Configuration Card
        self.config_card = ctk.CTkFrame(self, fg_color=COLORS["card"], border_width=1, border_color="#e2e8f0", corner_radius=15)
        self.config_card.grid(row=2, column=0, sticky="ew", pady=(20, 50), padx=10)
        self.config_card.grid_columnconfigure(0, weight=1)
        
        # Inner Content for Config
        self.inner = ctk.CTkFrame(self.config_card, fg_color="transparent")
        self.inner.grid(row=0, column=0, padx=25, pady=25, sticky="ew")
        self.inner.grid_columnconfigure(0, weight=1)

        # Entry Grid
        self.url_label_widget, self.url_box = self._add_entry_section(self.inner, 0, "目标 URL", controller.url_var, "https://", "url")
        self.list_label_widget, self.list_sel_box = self._add_entry_section(self.inner, 2, "列表容器选择器 (List Selector)", controller.list_selector_var, ".item-list", "selector")

        # Selector Tree
        self.tree_label = self._add_field_label(self.inner, 4, "提取字段映射", 10)
        
        self.tree_frame = ctk.CTkFrame(self.inner, fg_color="#f8fafc", border_width=1, border_color="#e2e8f0")
        self.tree_frame.grid(row=5, column=0, pady=(5, 15), sticky="nsew")
        
        cols = ("Field", "Selector")
        self.tree = ttk.Treeview(self.tree_frame, columns=cols, show="headings", height=8)
        self.tree.heading("Field", text="字段名称")
        self.tree.heading("Selector", text="CSS 选择器")
        self.tree.column("Field", width=150)
        self.tree.column("Selector", width=400)
        self.tree.pack(side="left", fill="both", expand=True)

        self.tree_ctrl = ctk.CTkFrame(self.inner, fg_color="transparent")
        self.tree_ctrl.grid(row=6, column=0, sticky="w")
        
        self.add_btn = ctk.CTkButton(self.tree_ctrl, text=" 添加字段", image=self.controller._get_icon("add", size=(16, 16)),
                                      width=110, height=32, corner_radius=8, command=self._add_field)
        self.add_btn.pack(side="left", padx=5)
        
        self.del_btn = ctk.CTkButton(self.tree_ctrl, text=" 删除选中", image=self.controller._get_icon("del", size=(16, 16)),
                                      width=100, height=32, corner_radius=8, fg_color="#fee2e2", 
                                      text_color="#ef4444", hover_color="#fecaca", command=self._del_field)
        self.del_btn.pack(side="left", padx=5)

        # Options Row
        self.opt_row = ctk.CTkFrame(self.inner, fg_color="transparent")
        self.opt_row.grid(row=7, column=0, sticky="ew", pady=(25, 10))
        
        self.adv_toggle = ctk.CTkSwitch(self.opt_row, text="浏览器渲染模式 (处理动态加载)", 
                                        variable=controller.adv_mode_var, progress_color=COLORS["primary"])
        self.adv_toggle.pack(side="left")

        # Bottom Panel: EXECUTION (Modernized)
        self.exec_frame = ctk.CTkFrame(self.config_card, fg_color="#f8fafc", corner_radius=0)
        self.exec_frame.grid(row=1, column=0, sticky="ew")
        self.exec_frame.grid_columnconfigure(0, weight=1)
        
        # Stats & Progress
        self.status_bar = ctk.CTkFrame(self.exec_frame, fg_color="transparent")
        self.status_bar.grid(row=0, column=0, sticky="ew", padx=25, pady=(20, 5))
        
        self.lbl_status = ctk.CTkLabel(self.status_bar, textvariable=controller.status_var, 
                                        font=ctk.CTkFont(weight="bold"), text_color=COLORS["primary"])
        self.lbl_status.pack(side="left")
        
        self.lbl_count = ctk.CTkLabel(self.status_bar, textvariable=controller.items_var, 
                                       font=ctk.CTkFont(size=13), text_color=COLORS["text_dark"])
        self.lbl_count.pack(side="right")
        
        self.pbar = ctk.CTkProgressBar(self.exec_frame, variable=controller.progress_val, 
                                        progress_color=COLORS["primary"], height=10, corner_radius=5)
        self.pbar.grid(row=1, column=0, padx=25, pady=5, sticky="ew")

        # Button Row
        self.btn_row = ctk.CTkFrame(self.exec_frame, fg_color="transparent")
        self.btn_row.grid(row=2, column=0, padx=25, pady=(20, 30), sticky="ew")
        self.btn_row.grid_columnconfigure(0, weight=3) # Launch button is wider
        self.btn_row.grid_columnconfigure(1, weight=1)

        self.btn_launch = ctk.CTkButton(self.btn_row, textvariable=controller.btn_text_var, height=60, 
                                         font=ctk.CTkFont(size=16, weight="bold"), corner_radius=12,
                                         fg_color=COLORS["primary"], hover_color="#1d4ed8",
                                         command=controller.start_crawl)
        self.btn_launch.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        self.btn_stop = ctk.CTkButton(self.btn_row, text="⏹", width=60, height=60, 
                                       font=ctk.CTkFont(size=20), corner_radius=12,
                                       fg_color="#fee2e2", text_color="#ef4444", hover_color="#fecaca",
                                       command=controller.stop_crawl)
        self.btn_stop.grid(row=0, column=1, sticky="ew")

    def _add_entry_section(self, parent, row, label, var, placeholder, icon_name):
        lbl = ctk.CTkLabel(parent, text=label, font=ctk.CTkFont(size=13, weight="bold"))
        lbl.grid(row=row, column=0, sticky="w", pady=(0, 5))
        
        entry = ctk.CTkEntry(parent, textvariable=var, height=42, corner_radius=10,
                               fg_color="#ffffff", border_color="#e2e8f0", 
                               placeholder_text=placeholder)
        entry.grid(row=row+1, column=0, pady=(0, 20), sticky="ew")
        return lbl, entry

    def _add_field_label(self, parent, row, text, pady_top):
        lbl = ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(size=13, weight="bold"))
        lbl.grid(row=row, column=0, sticky="w", pady=(pady_top, 5))
        return lbl

    def _add_field(self):
        self.tree.insert("", "end", values=("new_field", ".selector"))

    def _add_field(self):
        self.tree.insert("", "end", values=("new_field", ".selector"))

    def _del_field(self):
        for item in self.tree.selection():
            self.tree.delete(item)

    def _apply_template(self, display_name):
        # Map display name back to internal ID
        target_id = None
        for tid, tpl in WEBSITE_TEMPLATES.items():
            if tpl.get("name") == display_name:
                target_id = tid
                break
        
        tpl = WEBSITE_TEMPLATES.get(target_id)
        if not tpl: return
        
        # Dynamic Label Switching
        new_label = tpl.get("input_label", "目标 URL")
        new_hint = tpl.get("input_hint", tpl.get("example_url", ""))
        self.url_label_widget.configure(text=new_label)
        self.url_box.configure(placeholder_text=new_hint)
        
        self.controller.url_var.set(tpl.get("example_url", ""))
        self.controller.list_selector_var.set(tpl.get("list_selector", ""))
        self.controller.current_workflow = tpl.get("workflow")
        self.controller.current_search_template = tpl.get("search_url_template")
        
        # Update Tree (Rendering internal selectors)
        for i in self.tree.get_children(): self.tree.delete(i)
        for k, v in tpl.get("fields", {}).items():
            self.tree.insert("", "end", values=(k, v))
        self.controller.current_selectors = tpl.get("fields", {})

    def get_selectors(self):
        res = {}
        for item in self.tree.get_children():
            cols = self.tree.item(item)["values"]
            res[cols[0]] = cols[1]
        return res

    def update_lang(self, t):
        if hasattr(self, "tpl_label"):
            self.tpl_label.configure(text="📋 " + t["cfg_templates"])
        self.btn_launch.configure(text=t["launch"])

    def _add_label(self, text, size):
        lbl = ctk.CTkLabel(self, text=text, font=ctk.CTkFont(size=size, weight="bold"))
        lbl.grid(column=0, sticky="w", padx=20, pady=(20, 5))
        return lbl

class LogsFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.console = ctk.CTkTextbox(self, font=("Consolas", 13), border_width=1)
        self.console.grid(row=0, column=0, sticky="nsew")
        
        self.clear = ctk.CTkButton(self, text="Clear Logs", width=100, command=lambda: self.console.delete("1.0", "end"))
        self.clear.grid(row=1, column=0, pady=10, sticky="e")

    def update_lang(self, t):
        self.clear.configure(text=t["btn_clear"])

    def append(self, msg, level="INFO"):
        time_str = datetime.now().strftime("%H:%M:%S")
        prefix = f"[{time_str}] "
        if level == "INFO": color = "white"
        elif level == "SUCCESS": color = "#2ecc71"
        elif level == "WARNING": color = "#f1c40f"
        elif level == "ERROR": color = "#e74c3c"
        else: color = "white"
        
        self.console.insert("end", prefix)
        self.console.insert("end", f"[{level}] {msg}\n")
        self.console.see("end")

if __name__ == "__main__":
    app = App()
    app.mainloop()
