#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Modern GUI for the universal crawler."""

import importlib.util
import json
import os
import queue
import sys
import threading
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk


APP_TITLE = "通用网页爬虫工作台"
APP_SUBTITLE = "模板驱动、实时日志、图片自动保存，适合 Flaticon 等图标站点"
DEFAULT_OUTPUT_DIR = os.path.join("data", "crawled_data")

EXAMPLE_SELECTORS = [
    ("标题", "h1", "提取页面主标题"),
    ("链接", "a@href", "提取链接地址"),
    ("图片", "img@src", "提取图片地址"),
    ("价格", ".price", "提取价格文本"),
    ("描述", ".description", "提取描述文本"),
]

BUILTIN_TEMPLATES = {
    "flaticon": {
        "name": "Flaticon 天气图标",
        "description": "适合抓取 Flaticon 列表页，命中图片时自动下载到 data 目录。",
        "mode": "list",
        "example_url": "https://www.flaticon.com/free-icons/weather",
        "list_selector": '.icon--item || li:has(a[href*="/free-icon/"]) || a[href*="/free-icon/"]',
        "fields": {
            "图标图片": "img.icon--item__img@src || img@src || img@data-src",
            "图标标题": ".icon--item__title || img@alt || @title",
            "图标链接": "a.icon--item__link@href || a@href || @href",
        },
    },
    "github_trending": {
        "name": "GitHub Trending",
        "description": "抓取 GitHub Trending 项目列表。",
        "mode": "list",
        "example_url": "https://github.com/trending",
        "list_selector": "article.Box-row",
        "fields": {
            "项目名称": "h2 a",
            "项目链接": "h2 a@href",
            "描述": "p.col-9",
            "语言": 'span[itemprop="programmingLanguage"]',
            "星标": "svg.octicon-star ~ span",
        },
    },
    "hackernews": {
        "name": "Hacker News",
        "description": "抓取 Hacker News 热门帖子。",
        "mode": "list",
        "example_url": "https://news.ycombinator.com",
        "list_selector": "tr.athing",
        "fields": {
            "标题": "span.titleline a",
            "链接": "span.titleline a@href",
            "来源": "span.sitestr",
        },
    },
    "producthunt": {
        "name": "Product Hunt",
        "description": "抓取 Product Hunt 今日产品。",
        "mode": "list",
        "example_url": "https://www.producthunt.com",
        "list_selector": 'div[data-test="post-item"]',
        "fields": {
            "产品": "h3",
            "描述": "p",
            "链接": "a@href",
        },
    },
    "novel_generic": {
        "name": "通用小说网站",
        "description": "以 biquuge 为默认示例，适合大多数小说列表页，应用后通常只需要小幅微调选择器。",
        "mode": "list",
        "example_url": "https://www.biquuge.com/top/",
        "list_selector": "li:has(h3 a) || li:has(h4 a) || .bookbox || .book-item || .novel-item || .book-list li || .book-img-text li || .rank-book-list li || .txt-list li",
        "fields": {
            "书名": ".book-title || h4 a || h3 a || .bookname a || .name a || a[title]",
            "作者": ".author || .book-author || .writer || .author a || .author-name || .s4",
            "分类": ".cat || .category || .book-cat || .tag || .s1",
            "简介": ".intro || .book-desc || .description || .book-intro || .detail",
            "最新章节": ".update a || .latest-chapter a || .chapter a || .lastchapter a || .s3 a",
            "封面": "img@src || img@data-src || .book-cover img@src",
            "详情链接": "h4 a@href || h3 a@href || .bookname a@href || .name a@href || a[title]@href || @href",
        },
    },
    "novel_biquuge_list": {
        "name": "笔趣阁小说列表（biquuge）",
        "description": "适合 biquuge 的排行榜、分类页和首页小说列表。",
        "mode": "list",
        "example_url": "https://www.biquuge.com/top/",
        "list_selector": ".l li || .topbooks li || .rank li || li:has(.s2 a) || li:has(h3 a) || li:has(h4 a)",
        "fields": {
            "分类": ".s1 || .cat || .category",
            "书名": ".s2 a || h3 a || h4 a || .bookname a || a[title]",
            "详情链接": ".s2 a@href || h3 a@href || h4 a@href || .bookname a@href || a[title]@href",
            "最新章节": ".s3 a || .update a || .latest-chapter a",
            "作者": ".s4 || .author || .book-author",
            "更新时间": ".s5 || .update-time || .date",
        },
    },
    "novel_biquuge_directory": {
        "name": "笔趣阁章节目录（biquuge）",
        "description": "适合 biquuge 的书籍目录页，提取章节标题和章节链接。",
        "mode": "list",
        "example_url": "https://www.biquuge.com/112/112271/index_14.html",
        "list_selector": "#list dd || .listmain dd || .box_con #list dd || dd:has(a[href$=\".html\"])",
        "fields": {
            "章节标题": "a",
            "章节链接": "a@href",
        },
    },
    "novel_biquuge_chapter": {
        "name": "笔趣阁章节正文（biquuge）",
        "description": "适合 biquuge 的章节正文页，提取章节标题、正文与上下章导航。",
        "mode": "single",
        "example_url": "https://www.biquuge.com/112/112271/1339.html",
        "list_selector": "",
        "fields": {
            "章节标题": ".bookname h1 || h1",
            "正文内容": "#content || .content || .showtxt || .txtnav",
            "面包屑": ".con_top || .path || .nav",
            "上一章链接": ".bottem2 a:nth-of-type(1)@href || .bottem1 a:nth-of-type(1)@href",
            "目录链接": ".bottem2 a:nth-of-type(2)@href || .bottem1 a:nth-of-type(2)@href",
            "下一章链接": ".bottem2 a:nth-of-type(3)@href || .bottem1 a:nth-of-type(3)@href",
        },
    },
    "novel_biquuge_full_book": {
        "name": "笔趣阁整本抓取（biquuge）",
        "description": "输入书名或书籍 URL，自动搜索、解析目录并抓取整本书，保存为 txt 和 json。",
        "mode": "single",
        "workflow": "biquuge_full_book",
        "input_label": "书名或书籍 URL",
        "input_hint": "直接输入书名即可，例如：剑来。也支持直接粘贴 biquuge 的书籍 URL。",
        "example_url": "剑来",
        "list_selector": "",
        "fields": {},
    },
    "novel_biquuge_book": {
        "name": "笔趣阁书籍详情（biquuge）",
        "description": "适合 biquuge 的单本书详情页，提取书名、简介、封面等信息。",
        "mode": "single",
        "example_url": "https://www.biquuge.com/112/112271/",
        "list_selector": "",
        "fields": {
            "书名": "#info h1 || h1",
            "基本信息": "#info || .info || .small",
            "简介": "#intro || .intro || .desc",
            "封面": "#fmimg img@src || .cover img@src || img@src",
            "目录页链接": "a[href*=\"index_\"]@href || .read a@href",
        },
    },
}


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


try:
    from universal_crawler_v2 import UniversalCrawlerV2 as UniversalCrawler
except ImportError:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    UniversalCrawler = _load_module(
        "universal_crawler_v2",
        os.path.join(BASE_DIR, "universal_crawler_v2.py"),
    ).UniversalCrawlerV2

try:
    from advanced_crawler import AdvancedCrawler, is_advanced_mode_available
except ImportError:
    try:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        _advanced_module = _load_module(
            "advanced_crawler",
            os.path.join(BASE_DIR, "advanced_crawler.py"),
        )
        AdvancedCrawler = _advanced_module.AdvancedCrawler
        is_advanced_mode_available = _advanced_module.is_advanced_mode_available
    except Exception:
        AdvancedCrawler = None
        def is_advanced_mode_available():
            return False

try:
    from prepare_gui_icons import GuiIconPreparer
except ImportError:
    try:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        GuiIconPreparer = _load_module(
            "prepare_gui_icons",
            os.path.join(BASE_DIR, "prepare_gui_icons.py"),
        ).GuiIconPreparer
    except Exception:
        GuiIconPreparer = None


class ModernUniversalCrawlerGUI:
    BG = "#edf3f7"
    CARD = "#ffffff"
    HEADER = "#10263d"
    HEADER_ACCENT = "#17a6a5"
    TEXT = "#102a43"
    MUTED = "#5f6c7b"
    BORDER = "#d9e2ec"
    ACCENT = "#138b97"
    ACCENT_HOVER = "#0f7680"
    SUCCESS = "#1f9d55"
    WARNING = "#c8830d"
    ERROR = "#d64545"
    LOG_BG = "#0b1724"
    LOG_TEXT = "#d9e6f2"
    PREVIEW_BG = "#fbfdff"

    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_TITLE} 2.0")
        self._configure_window()
        self.root.configure(bg=self.BG)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self.templates = BUILTIN_TEMPLATES
        self.template_name_map = {item["name"]: key for key, item in self.templates.items()}
        self.current_template_id = ""
        self.current_template = {}
        self.ui_queue = queue.Queue()
        self.is_crawling = False
        self.current_crawler = None
        self.worker_thread = None
        self.last_saved_path = ""
        self.icons = {}
        self.advanced_user_data_dir = os.path.abspath(os.path.join(os.getcwd(), "data", "browser_profile"))
        self._advanced_prewarm_inflight = set()
        self._advanced_prewarm_ready = set()

        self.status_var = tk.StringVar(value="就绪")
        self.summary_status_var = tk.StringVar(value="待启动")
        self.summary_pages_var = tk.StringVar(value="0")
        self.summary_items_var = tk.StringVar(value="0")
        self.summary_saved_var = tk.StringVar(value="尚未保存")

        self._ensure_icon_assets()
        self._setup_styles()
        self._load_icons()
        self._build_ui()
        self._apply_default_template()
        self.root.after(60, self.process_ui_queue)

    def _configure_window(self):
        screen_w = max(self.root.winfo_screenwidth(), 1024)
        screen_h = max(self.root.winfo_screenheight(), 720)
        width = min(1440, max(980, screen_w - 72))
        height = min(860, max(640, screen_h - 96))
        pos_x = max((screen_w - width) // 2, 0)
        pos_y = max((screen_h - height) // 3, 0)
        self.root.geometry(f"{width}x{height}+{pos_x}+{pos_y}")
        self.root.minsize(900, 600)

    def _ensure_icon_assets(self):
        icon_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "gui_icons")
        required = {"app", "template", "url", "selector", "start", "stop", "folder", "log", "preview", "advanced"}
        existing = set()
        if os.path.isdir(icon_dir):
            existing = {os.path.splitext(name)[0] for name in os.listdir(icon_dir)}
        if required.issubset(existing) or GuiIconPreparer is None:
            return
        try:
            preparer = GuiIconPreparer(output_dir=icon_dir, size=28, color="#9be2eb")
            try:
                preparer.prepare(sorted(required))
            finally:
                preparer.close()
        except Exception:
            pass

    def _setup_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure("TFrame", background=self.BG)
        style.configure("Card.TFrame", background=self.CARD)
        style.configure(
            "Accent.TButton",
            background=self.ACCENT,
            foreground="white",
            borderwidth=0,
            focusthickness=0,
            padding=(14, 10),
            font=("Microsoft YaHei UI", 10, "bold"),
        )
        style.map(
            "Accent.TButton",
            background=[("active", self.ACCENT_HOVER), ("disabled", "#b9c7d3")],
            foreground=[("disabled", "#f8fbfd")],
        )
        style.configure(
            "Ghost.TButton",
            background=self.CARD,
            foreground=self.TEXT,
            borderwidth=1,
            relief="solid",
            padding=(10, 8),
            font=("Microsoft YaHei UI", 9),
        )
        style.map(
            "Ghost.TButton",
            background=[("active", "#f1f7fb")],
            bordercolor=[("active", self.ACCENT)],
        )
        style.configure(
            "Warn.TButton",
            background="#fff4e5",
            foreground=self.WARNING,
            borderwidth=1,
            relief="solid",
            padding=(10, 8),
            font=("Microsoft YaHei UI", 9, "bold"),
        )
        style.map("Warn.TButton", background=[("active", "#ffe9c7")])
        style.configure(
            "Modern.TRadiobutton",
            background=self.CARD,
            foreground=self.TEXT,
            font=("Microsoft YaHei UI", 9),
        )
        style.configure(
            "Modern.TCheckbutton",
            background=self.CARD,
            foreground=self.TEXT,
            font=("Microsoft YaHei UI", 9),
        )
        style.configure(
            "Modern.Treeview",
            background=self.CARD,
            foreground=self.TEXT,
            fieldbackground=self.CARD,
            bordercolor=self.BORDER,
            rowheight=28,
            font=("Microsoft YaHei UI", 9),
        )
        style.configure(
            "Modern.Treeview.Heading",
            background="#f4f8fb",
            foreground=self.TEXT,
            borderwidth=0,
            font=("Microsoft YaHei UI", 9, "bold"),
        )
        style.map("Modern.Treeview", background=[("selected", "#dff3f4")], foreground=[("selected", self.TEXT)])
        style.configure(
            "Modern.TNotebook",
            background=self.BG,
            borderwidth=0,
            tabmargins=(0, 0, 0, 0),
        )
        style.configure(
            "Modern.TNotebook.Tab",
            background="#dfe8ef",
            foreground=self.TEXT,
            padding=(16, 8),
            font=("Microsoft YaHei UI", 9, "bold"),
        )
        style.map(
            "Modern.TNotebook.Tab",
            background=[("selected", self.CARD), ("active", "#e9f2f7")],
            foreground=[("selected", self.ACCENT)],
        )

    def _icon_path(self, name):
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(root_dir, "assets", "gui_icons", f"{name}.png")

    def _load_icons(self):
        for name in ("app", "template", "url", "selector", "start", "stop", "folder", "log", "preview", "advanced"):
            path = self._icon_path(name)
            if not os.path.exists(path):
                continue
            try:
                self.icons[name] = tk.PhotoImage(file=path)
            except Exception:
                continue

    def _get_icon(self, name):
        return self.icons.get(name)

    def _build_ui(self):
        self._build_header()
        self._build_body()
        self._build_footer()

    def _build_header(self):
        header = tk.Frame(self.root, bg=self.HEADER, height=108)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(0, weight=1)

        left = tk.Frame(header, bg=self.HEADER)
        left.grid(row=0, column=0, sticky="w", padx=24, pady=16)

        icon = self._get_icon("app")
        if icon:
            tk.Label(left, image=icon, bg=self.HEADER).grid(row=0, column=0, rowspan=2, padx=(0, 14))

        tk.Label(
            left,
            text=APP_TITLE,
            bg=self.HEADER,
            fg="white",
            font=("Microsoft YaHei UI", 21, "bold"),
        ).grid(row=0, column=1, sticky="w")
        tk.Label(
            left,
            text=APP_SUBTITLE,
            bg=self.HEADER,
            fg="#d4e3ef",
            font=("Microsoft YaHei UI", 10),
        ).grid(row=1, column=1, sticky="w", pady=(6, 0))

        right = tk.Frame(header, bg=self.HEADER)
        right.grid(row=0, column=1, sticky="e", padx=24, pady=18)
        self._create_header_badge(right, "图片自动保存", self.HEADER_ACCENT, "white").pack(side=tk.LEFT, padx=(0, 10))
        self._create_header_badge(right, "Flaticon 快速优化", "#24415e", "#cfe4f4").pack(side=tk.LEFT)

    def _create_header_badge(self, parent, text, bg, fg):
        badge = tk.Label(
            parent,
            text=text,
            bg=bg,
            fg=fg,
            padx=14,
            pady=7,
            font=("Microsoft YaHei UI", 9, "bold"),
        )
        return badge

    def _build_body(self):
        body = tk.Frame(self.root, bg=self.BG)
        body.grid(row=1, column=0, sticky="nsew", padx=16, pady=(16, 10))
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=1)
        self.body_container = body
        self.main_layout = tk.Frame(body, bg=self.BG)
        self.main_layout.grid(row=0, column=0, sticky="nsew")

        self.left_panel = tk.Frame(self.main_layout, bg=self.BG)
        self.right_panel = tk.Frame(self.main_layout, bg=self.BG)

        self.left_panel.grid_columnconfigure(0, weight=1)
        self.left_panel.grid_rowconfigure(0, weight=1)
        self.right_panel.grid_columnconfigure(0, weight=1)
        self.right_panel.grid_rowconfigure(1, weight=1)

        self._build_config_panel(self.left_panel)
        self._build_summary_strip(self.right_panel).grid(row=0, column=0, sticky="ew", pady=(0, 12))
        self._build_workbench(self.right_panel).grid(row=1, column=0, sticky="nsew")

        self.body_container.bind("<Configure>", self._relayout_main_layout)
        self.root.after(0, self._relayout_main_layout)

    def _build_config_panel(self, parent):
        container = tk.Frame(parent, bg=self.BG)
        container.grid(row=0, column=0, sticky="nsew")
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        notebook = ttk.Notebook(container, style="Modern.TNotebook")
        notebook.grid(row=0, column=0, sticky="nsew")
        self.config_notebook = notebook

        tabs = [
            ("模板启动", self._build_template_card),
            ("目标模式", self._build_target_card),
            ("字段选择器", self._build_selector_card),
            ("运行参数", self._build_run_card),
        ]

        for title, builder in tabs:
            tab = tk.Frame(notebook, bg=self.BG)
            tab.grid_rowconfigure(0, weight=1)
            tab.grid_columnconfigure(0, weight=1)
            builder(tab).grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
            notebook.add(tab, text=title)

    def _relayout_main_layout(self, event=None):
        width = getattr(event, "width", 0) if event is not None else self.body_container.winfo_width()
        height = getattr(event, "height", 0) if event is not None else self.body_container.winfo_height()
        if width <= 1 or height <= 1:
            return

        stacked = width < 1220
        mode = "stacked" if stacked else "split"
        if getattr(self, "_layout_mode", None) == mode:
            return
        self._layout_mode = mode

        self.left_panel.grid_forget()
        self.right_panel.grid_forget()

        for index in range(2):
            self.main_layout.grid_columnconfigure(index, weight=0, uniform="")
            self.main_layout.grid_rowconfigure(index, weight=0, uniform="")

        if stacked:
            self.main_layout.grid_columnconfigure(0, weight=1)
            self.main_layout.grid_rowconfigure(0, weight=0)
            self.main_layout.grid_rowconfigure(1, weight=1)
            self.left_panel.grid(row=0, column=0, sticky="ew", pady=(0, 12))
            self.right_panel.grid(row=1, column=0, sticky="nsew")
        else:
            self.main_layout.grid_rowconfigure(0, weight=1)
            self.main_layout.grid_columnconfigure(0, weight=5, uniform="main")
            self.main_layout.grid_columnconfigure(1, weight=8, uniform="main")
            self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
            self.right_panel.grid(row=0, column=1, sticky="nsew")

    def _build_footer(self):
        footer = tk.Frame(self.root, bg=self.BG, height=38)
        footer.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 10))
        footer.grid_propagate(False)
        footer.grid_columnconfigure(0, weight=1)
        footer.grid_columnconfigure(1, weight=0)

        tk.Label(
            footer,
            textvariable=self.status_var,
            bg=self.BG,
            fg=self.TEXT,
            anchor="w",
            font=("Microsoft YaHei UI", 9, "bold"),
        ).grid(row=0, column=0, sticky="ew")
        tk.Label(
            footer,
            text="检测到图片字段时会自动保存为图片目录",
            bg=self.BG,
            fg=self.MUTED,
            anchor="e",
            font=("Microsoft YaHei UI", 9),
        ).grid(row=0, column=1, sticky="e")

    def _create_card(self, parent, title, description="", icon_name=""):
        card = tk.Frame(parent, bg=self.CARD, highlightbackground=self.BORDER, highlightthickness=1, bd=0)
        card.grid_columnconfigure(0, weight=1)

        header = tk.Frame(card, bg=self.CARD)
        header.grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 8))
        header.grid_columnconfigure(1, weight=1)

        icon = self._get_icon(icon_name)
        if icon:
            tk.Label(header, image=icon, bg=self.CARD).grid(row=0, column=0, rowspan=2, padx=(0, 12), sticky="nw")

        tk.Label(
            header,
            text=title,
            bg=self.CARD,
            fg=self.TEXT,
            anchor="w",
            font=("Microsoft YaHei UI", 12, "bold"),
        ).grid(row=0, column=1, sticky="w")
        if description:
            tk.Label(
                header,
                text=description,
                bg=self.CARD,
                fg=self.MUTED,
                justify="left",
                anchor="w",
                font=("Microsoft YaHei UI", 9),
            ).grid(row=1, column=1, sticky="w", pady=(4, 0))

        body = tk.Frame(card, bg=self.CARD)
        body.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 18))
        body.grid_columnconfigure(0, weight=1)
        return card, body

    def _build_template_card(self, parent):
        card, body = self._create_card(parent, "模板与快捷启动", "先选模板再微调字段，能明显减少手动配置。", "template")
        self.template_var = tk.StringVar(value=self.templates["flaticon"]["name"])

        ttk.Combobox(
            body,
            textvariable=self.template_var,
            values=[item["name"] for item in self.templates.values()],
            state="readonly",
            font=("Microsoft YaHei UI", 10),
        ).grid(row=0, column=0, sticky="ew", padx=(0, 10))

        ttk.Button(
            body,
            text="应用模板",
            image=self._get_icon("template"),
            compound=tk.LEFT,
            command=self.apply_template,
            style="Ghost.TButton",
        ).grid(row=0, column=1, sticky="e")

        self.template_desc_var = tk.StringVar(value=self.templates["flaticon"]["description"])
        tk.Label(
            body,
            textvariable=self.template_desc_var,
            bg=self.CARD,
            fg=self.MUTED,
            justify="left",
            anchor="w",
            wraplength=400,
            font=("Microsoft YaHei UI", 9),
        ).grid(row=1, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        return card

    def _build_target_card(self, parent):
        card, body = self._create_card(parent, "目标地址与模式", "支持列表页和单页抓取。列表页为空时会走站点兜底逻辑。", "url")
        body.grid_columnconfigure(0, weight=1)

        self.target_input_label_var = tk.StringVar(value="目标 URL")
        tk.Label(body, textvariable=self.target_input_label_var, bg=self.CARD, fg=self.TEXT, anchor="w", font=("Microsoft YaHei UI", 9, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(body, textvariable=self.url_var, font=("Consolas", 10))
        self.url_entry.grid(row=1, column=0, sticky="ew", pady=(6, 10))
        self.target_input_hint_var = tk.StringVar(value="输入目标网页地址。")
        tk.Label(
            body,
            textvariable=self.target_input_hint_var,
            bg=self.CARD,
            fg=self.MUTED,
            font=("Microsoft YaHei UI", 8),
            justify="left",
            anchor="w",
        ).grid(row=2, column=0, sticky="ew", pady=(0, 10))

        mode_row = tk.Frame(body, bg=self.CARD)
        mode_row.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        tk.Label(mode_row, text="抓取模式", bg=self.CARD, fg=self.TEXT, font=("Microsoft YaHei UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 14))
        self.mode_var = tk.StringVar(value="list")
        ttk.Radiobutton(mode_row, text="列表页", variable=self.mode_var, value="list", style="Modern.TRadiobutton", command=self._on_mode_changed).pack(
            side=tk.LEFT, padx=(0, 10)
        )
        ttk.Radiobutton(mode_row, text="单页", variable=self.mode_var, value="single", style="Modern.TRadiobutton", command=self._on_mode_changed).pack(
            side=tk.LEFT
        )

        tk.Label(body, text="列表容器选择器", bg=self.CARD, fg=self.TEXT, anchor="w", font=("Microsoft YaHei UI", 9, "bold")).grid(
            row=4, column=0, sticky="w"
        )
        self.list_selector_var = tk.StringVar()
        self.list_selector_entry = ttk.Entry(body, textvariable=self.list_selector_var, font=("Consolas", 10))
        self.list_selector_entry.grid(row=5, column=0, sticky="ew", pady=(6, 0))
        self.list_selector_hint_var = tk.StringVar(value="支持多候选写法，例如 selector1 || selector2。")
        self.list_selector_hint = tk.Label(
            body,
            textvariable=self.list_selector_hint_var,
            bg=self.CARD,
            fg=self.MUTED,
            font=("Microsoft YaHei UI", 8),
        )
        self.list_selector_hint.grid(row=6, column=0, sticky="w", pady=(6, 0))
        return card

    def _build_selector_card(self, parent):
        card, body = self._create_card(parent, "字段选择器", "字段越清晰，预览和自动图片保存就越稳定。", "selector")
        body.grid_rowconfigure(1, weight=1)
        body.grid_columnconfigure(0, weight=1)

        toolbar = tk.Frame(body, bg=self.CARD)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ttk.Button(toolbar, text="新增字段", command=self.add_selector, style="Ghost.TButton").pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(toolbar, text="编辑", command=self.edit_selector, style="Ghost.TButton").pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(toolbar, text="删除", command=self.delete_selector, style="Ghost.TButton").pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(toolbar, text="示例", command=self.load_example_selectors, style="Ghost.TButton").pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(toolbar, text="清空", command=self.clear_selectors, style="Warn.TButton").pack(side=tk.LEFT)

        tree_frame = tk.Frame(body, bg=self.CARD)
        tree_frame.grid(row=1, column=0, sticky="nsew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        columns = ("字段", "选择器", "说明")
        self.selector_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", style="Modern.Treeview", height=8)
        self.selector_tree.heading("字段", text="字段")
        self.selector_tree.heading("选择器", text="选择器")
        self.selector_tree.heading("说明", text="说明")
        self.selector_tree.column("字段", width=120, anchor="w")
        self.selector_tree.column("选择器", width=260, anchor="w")
        self.selector_tree.column("说明", width=180, anchor="w")
        self.selector_tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.selector_tree.yview)
        self.selector_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")
        return card

    def _build_run_card(self, parent):
        card, body = self._create_card(parent, "运行参数", "标准模式更快，高级模式更适合有反爬或重渲染页面。", "advanced")
        for col in range(4):
            body.grid_columnconfigure(col, weight=1)

        tk.Label(body, text="条数", bg=self.CARD, fg=self.TEXT, font=("Microsoft YaHei UI", 9, "bold")).grid(row=0, column=0, sticky="w")
        self.limit_var = tk.IntVar(value=12)
        ttk.Spinbox(body, from_=1, to=1000, textvariable=self.limit_var, width=10, font=("Microsoft YaHei UI", 10)).grid(
            row=1, column=0, sticky="ew", padx=(0, 8), pady=(6, 10)
        )

        tk.Label(body, text="请求间隔(秒)", bg=self.CARD, fg=self.TEXT, font=("Microsoft YaHei UI", 9, "bold")).grid(row=0, column=1, sticky="w")
        self.delay_var = tk.DoubleVar(value=0.6)
        ttk.Spinbox(
            body,
            from_=0,
            to=10,
            increment=0.2,
            textvariable=self.delay_var,
            width=10,
            font=("Microsoft YaHei UI", 10),
        ).grid(row=1, column=1, sticky="ew", padx=(0, 8), pady=(6, 10))

        tk.Label(body, text="保存格式", bg=self.CARD, fg=self.TEXT, font=("Microsoft YaHei UI", 9, "bold")).grid(row=0, column=2, sticky="w")
        format_row = tk.Frame(body, bg=self.CARD)
        format_row.grid(row=1, column=2, sticky="w", pady=(6, 10))
        self.format_var = tk.StringVar(value="json")
        ttk.Radiobutton(format_row, text="JSON", variable=self.format_var, value="json", style="Modern.TRadiobutton").pack(side=tk.LEFT, padx=(0, 8))
        ttk.Radiobutton(format_row, text="CSV", variable=self.format_var, value="csv", style="Modern.TRadiobutton").pack(side=tk.LEFT)

        tk.Label(body, text="高级模式", bg=self.CARD, fg=self.TEXT, font=("Microsoft YaHei UI", 9, "bold")).grid(row=0, column=3, sticky="w")
        advanced_row = tk.Frame(body, bg=self.CARD)
        advanced_row.grid(row=1, column=3, sticky="w", pady=(6, 10))
        self.advanced_mode_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            advanced_row,
            text="启用",
            variable=self.advanced_mode_var,
            command=self.on_advanced_mode_toggle,
            style="Modern.TCheckbutton",
        ).pack(side=tk.LEFT)
        self.advanced_state_var = tk.StringVar(value="检测中")
        tk.Label(
            advanced_row,
            textvariable=self.advanced_state_var,
            bg=self.CARD,
            fg=self.MUTED,
            font=("Microsoft YaHei UI", 8),
        ).pack(side=tk.LEFT, padx=(10, 0))

        tk.Label(body, text="输出目录", bg=self.CARD, fg=self.TEXT, font=("Microsoft YaHei UI", 9, "bold")).grid(
            row=2, column=0, columnspan=4, sticky="w"
        )
        self.output_var = tk.StringVar(value=DEFAULT_OUTPUT_DIR)
        output_row = tk.Frame(body, bg=self.CARD)
        output_row.grid(row=3, column=0, columnspan=4, sticky="ew", pady=(6, 10))
        output_row.grid_columnconfigure(0, weight=1)
        ttk.Entry(output_row, textvariable=self.output_var, font=("Consolas", 10)).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(
            output_row,
            text="浏览",
            image=self._get_icon("folder"),
            compound=tk.LEFT,
            command=self.browse_output_dir,
            style="Ghost.TButton",
        ).grid(row=0, column=1, padx=(0, 8))
        ttk.Button(output_row, text="打开", command=self.open_output_directory, style="Ghost.TButton").grid(row=0, column=2)

        tk.Label(
            body,
            text="提示：如果提取结果中包含图片地址，程序会直接下载图片，不再只保存 JSON。",
            bg=self.CARD,
            fg=self.MUTED,
            font=("Microsoft YaHei UI", 8),
        ).grid(row=4, column=0, columnspan=4, sticky="w")

        action_row = tk.Frame(body, bg=self.CARD)
        action_row.grid(row=5, column=0, columnspan=4, sticky="ew", pady=(14, 0))
        action_row.grid_columnconfigure(0, weight=1)
        action_row.grid_columnconfigure(1, weight=1)
        self.start_btn = ttk.Button(
            action_row,
            text="开始抓取",
            image=self._get_icon("start"),
            compound=tk.LEFT,
            command=self.start_crawling,
            style="Accent.TButton",
        )
        self.start_btn.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.stop_btn = ttk.Button(
            action_row,
            text="停止",
            image=self._get_icon("stop"),
            compound=tk.LEFT,
            command=self.stop_crawling,
            style="Warn.TButton",
            state=tk.DISABLED,
        )
        self.stop_btn.grid(row=0, column=1, sticky="ew")

        self.progress = ttk.Progressbar(body, mode="indeterminate")
        self.progress.grid(row=6, column=0, columnspan=4, sticky="ew", pady=(14, 0))

        self.check_advanced_mode_availability()
        return card

    def _build_summary_strip(self, parent):
        strip = tk.Frame(parent, bg=self.BG)
        self.summary_strip = strip
        self.summary_tiles = [
            self._create_stat_tile(strip, "状态", self.summary_status_var, self.ACCENT),
            self._create_stat_tile(strip, "成功页面", self.summary_pages_var, self.SUCCESS),
            self._create_stat_tile(strip, "提取条数", self.summary_items_var, self.HEADER_ACCENT),
            self._create_stat_tile(strip, "最近保存", self.summary_saved_var, self.WARNING),
        ]
        strip.bind("<Configure>", self._relayout_summary_tiles)
        self.root.after(0, self._relayout_summary_tiles)
        return strip
        for col in range(4):
            strip.grid_columnconfigure(col, weight=1)

        self._create_stat_tile(strip, "状态", self.summary_status_var, self.ACCENT).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self._create_stat_tile(strip, "成功页面", self.summary_pages_var, self.SUCCESS).grid(row=0, column=1, sticky="ew", padx=4)
        self._create_stat_tile(strip, "提取条数", self.summary_items_var, self.HEADER_ACCENT).grid(row=0, column=2, sticky="ew", padx=4)
        self._create_stat_tile(strip, "最近保存", self.summary_saved_var, self.WARNING).grid(row=0, column=3, sticky="ew", padx=(8, 0))
        return strip

    def _create_stat_tile(self, parent, title, value_var, accent):
        tile = tk.Frame(parent, bg=self.CARD, highlightbackground=self.BORDER, highlightthickness=1, bd=0)
        tk.Frame(tile, bg=accent, height=4).pack(fill="x")
        tk.Label(tile, text=title, bg=self.CARD, fg=self.MUTED, anchor="w", font=("Microsoft YaHei UI", 9)).pack(fill="x", padx=14, pady=(12, 4))
        tk.Label(tile, textvariable=value_var, bg=self.CARD, fg=self.TEXT, anchor="w", font=("Microsoft YaHei UI", 14, "bold")).pack(
            fill="x", padx=14, pady=(0, 12)
        )
        return tile

    def _relayout_summary_tiles(self, event=None):
        if not hasattr(self, "summary_tiles"):
            return

        width = getattr(event, "width", 0) if event is not None else 0
        if not width and hasattr(self, "summary_strip"):
            width = self.summary_strip.winfo_width()

        if width >= 860:
            columns = 4
        elif width >= 460:
            columns = 2
        else:
            columns = 1

        for index in range(4):
            self.summary_strip.grid_columnconfigure(index, weight=0, uniform="")
        for index in range(columns):
            self.summary_strip.grid_columnconfigure(index, weight=1, uniform="summary")

        rows = (len(self.summary_tiles) + columns - 1) // columns
        for tile in self.summary_tiles:
            tile.grid_forget()

        for index, tile in enumerate(self.summary_tiles):
            row = index // columns
            column = index % columns
            tile.grid(
                row=row,
                column=column,
                sticky="ew",
                padx=6,
                pady=(0, 8 if row < rows - 1 else 0),
            )

    def _build_workbench(self, parent):
        container = tk.Frame(parent, bg=self.CARD, highlightbackground=self.BORDER, highlightthickness=1, bd=0)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        notebook = ttk.Notebook(container, style="Modern.TNotebook")
        notebook.grid(row=0, column=0, sticky="nsew")

        log_tab = tk.Frame(notebook, bg=self.CARD)
        preview_tab = tk.Frame(notebook, bg=self.CARD)
        notebook.add(log_tab, text="运行日志")
        notebook.add(preview_tab, text="结果预览")

        self._build_log_tab(log_tab)
        self._build_preview_tab(preview_tab)
        return container

    def _build_log_tab(self, parent):
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        toolbar = tk.Frame(parent, bg=self.CARD)
        toolbar.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 10))
        ttk.Button(toolbar, text="清空日志", command=self.clear_log, style="Ghost.TButton").pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(toolbar, text="复制日志", command=self.copy_log, style="Ghost.TButton").pack(side=tk.LEFT)

        self.log_text = scrolledtext.ScrolledText(
            parent,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg=self.LOG_BG,
            fg=self.LOG_TEXT,
            insertbackground="white",
            relief="flat",
            borderwidth=0,
            padx=14,
            pady=14,
        )
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))

    def _build_preview_tab(self, parent):
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        toolbar = tk.Frame(parent, bg=self.CARD)
        toolbar.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 10))
        ttk.Button(toolbar, text="打开输出目录", command=self.open_output_directory, style="Ghost.TButton").pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(toolbar, text="清空预览", command=self.clear_preview, style="Ghost.TButton").pack(side=tk.LEFT)

        self.preview_text = scrolledtext.ScrolledText(
            parent,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg=self.PREVIEW_BG,
            fg=self.TEXT,
            insertbackground=self.TEXT,
            relief="flat",
            borderwidth=0,
            padx=14,
            pady=14,
        )
        self.preview_text.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))

    def _apply_default_template(self):
        self.apply_template(show_message=False)
        self.log("界面已准备就绪，可以直接开始抓取或继续调整配置。", "SUCCESS")

    def _on_mode_changed(self):
        workflow = self._get_active_workflow()
        if workflow == "biquuge_full_book":
            self.list_selector_entry.configure(state="disabled")
            self.list_selector_hint_var.set("整本抓取会自动搜索书籍、解析目录并抓取全部章节，无需填写列表选择器。")
            return

        is_list_mode = self.mode_var.get() == "list"
        state = "normal" if is_list_mode else "disabled"
        self.list_selector_entry.configure(state=state)
        self.list_selector_hint_var.set(
            "支持多候选写法，例如 selector1 || selector2。" if is_list_mode else "单页模式下不会使用列表容器选择器。"
        )

    def _apply_template_input_state(self, template):
        workflow = (template or {}).get("workflow", "")
        label = (template or {}).get("input_label") or "目标 URL"
        hint = (template or {}).get("input_hint") or "输入目标网页地址。"
        if workflow == "biquuge_full_book":
            label = (template or {}).get("input_label") or "书名或书籍 URL"
            hint = (template or {}).get("input_hint") or "输入书名后，程序会自动搜索书籍、抓取目录并保存整本内容。"
        self.target_input_label_var.set(label)
        self.target_input_hint_var.set(hint)

    def _preferred_advanced_headless(self, url):
        return "flaticon.com" not in (url or "").lower()

    def _set_advanced_state_text(self, text):
        if threading.current_thread() is threading.main_thread():
            self.advanced_state_var.set(text)
        else:
            self._run_on_ui_thread(self.advanced_state_var.set, text)

    def _schedule_startup_advanced_prewarm(self):
        self._schedule_advanced_prewarm(self.url_var.get().strip() if hasattr(self, "url_var") else "")

    def _schedule_advanced_prewarm(self, url):
        if hasattr(self, "advanced_mode_var") and not self.advanced_mode_var.get():
            return
        try:
            available = bool(AdvancedCrawler) and bool(is_advanced_mode_available())
        except Exception:
            available = False

        if not available:
            return

        key = (self._preferred_advanced_headless(url), self.advanced_user_data_dir)
        if key in self._advanced_prewarm_ready or key in self._advanced_prewarm_inflight:
            return

        self._advanced_prewarm_inflight.add(key)
        self._set_advanced_state_text("已安装，预热中")
        self.log(
            f"后台预热高级模式浏览器：{'无头模式' if key[0] else '可视模式'}",
            "INFO",
        )
        thread = threading.Thread(
            target=self._prewarm_advanced_browser,
            args=(key,),
            daemon=True,
        )
        thread.start()

    def _prewarm_advanced_browser(self, key):
        crawler = None
        try:
            crawler = AdvancedCrawler(
                headless=key[0],
                user_data_dir=self.advanced_user_data_dir,
                reuse_browser=True,
            )
            crawler.start()
            self._advanced_prewarm_ready.add(key)
            self.log(
                f"高级模式预热完成：{'无头模式' if key[0] else '可视模式'}",
                "SUCCESS",
            )
            self._set_advanced_state_text("已预热")
        except Exception as exc:
            self.log(f"高级模式预热失败：{exc}", "WARNING")
            self._set_advanced_state_text("已安装，预热失败")
        finally:
            self._advanced_prewarm_inflight.discard(key)
            if crawler:
                try:
                    crawler.close()
                except Exception:
                    pass

    def process_ui_queue(self):
        try:
            while True:
                callback, args, kwargs = self.ui_queue.get_nowait()
                callback(*args, **kwargs)
        except queue.Empty:
            pass
        finally:
            self.root.after(60, self.process_ui_queue)

    def _run_on_ui_thread(self, callback, *args, **kwargs):
        self.ui_queue.put((callback, args, kwargs))

    def clear_log(self):
        self.log_text.delete("1.0", tk.END)

    def clear_preview(self):
        self.preview_text.delete("1.0", tk.END)

    def copy_log(self):
        content = self.log_text.get("1.0", tk.END).strip()
        if not content:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        self.status_var.set("日志已复制到剪贴板")

    def browse_output_dir(self):
        directory = filedialog.askdirectory(title="选择输出目录", initialdir=os.getcwd())
        if directory:
            self.output_var.set(directory)

    def open_output_directory(self):
        target = self.last_saved_path or self.output_var.get().strip()
        if not target:
            return
        path = os.path.abspath(target)
        if os.path.isfile(path):
            path = os.path.dirname(path)
        if not os.path.exists(path):
            messagebox.showwarning("路径不存在", f"未找到目录：\n{path}")
            return
        try:
            os.startfile(path)
        except Exception as exc:
            messagebox.showerror("打开失败", f"无法打开目录：\n{exc}")

    def _show_selector_dialog(self, title, initial_values=None):
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.geometry("560x280")
        dialog.configure(bg=self.CARD)
        dialog.resizable(False, False)

        result = {}
        field_var = tk.StringVar(value=initial_values[0] if initial_values else "")
        selector_var = tk.StringVar(value=initial_values[1] if initial_values else "")
        desc_var = tk.StringVar(value=initial_values[2] if initial_values and len(initial_values) > 2 else "")

        content = tk.Frame(dialog, bg=self.CARD)
        content.pack(fill="both", expand=True, padx=24, pady=20)
        content.grid_columnconfigure(0, weight=1)

        tk.Label(content, text="字段名称", bg=self.CARD, fg=self.TEXT, anchor="w", font=("Microsoft YaHei UI", 9, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Entry(content, textvariable=field_var, font=("Microsoft YaHei UI", 10)).grid(row=1, column=0, sticky="ew", pady=(6, 12))

        tk.Label(content, text="CSS 选择器", bg=self.CARD, fg=self.TEXT, anchor="w", font=("Microsoft YaHei UI", 9, "bold")).grid(
            row=2, column=0, sticky="w"
        )
        ttk.Entry(content, textvariable=selector_var, font=("Consolas", 10)).grid(row=3, column=0, sticky="ew", pady=(6, 12))

        tk.Label(content, text="说明", bg=self.CARD, fg=self.TEXT, anchor="w", font=("Microsoft YaHei UI", 9, "bold")).grid(
            row=4, column=0, sticky="w"
        )
        ttk.Entry(content, textvariable=desc_var, font=("Microsoft YaHei UI", 10)).grid(row=5, column=0, sticky="ew", pady=(6, 12))

        tk.Label(
            content,
            text="提取属性时可写成 a@href、img@src；多个候选选择器可用 || 分隔。",
            bg=self.CARD,
            fg=self.MUTED,
            anchor="w",
            justify="left",
            font=("Microsoft YaHei UI", 8),
        ).grid(row=6, column=0, sticky="w")

        action_row = tk.Frame(content, bg=self.CARD)
        action_row.grid(row=7, column=0, sticky="e", pady=(18, 0))

        def submit():
            field_name = field_var.get().strip()
            selector = selector_var.get().strip()
            desc = desc_var.get().strip()
            if not field_name or not selector:
                messagebox.showwarning("信息不完整", "字段名称和 CSS 选择器不能为空。", parent=dialog)
                return
            result["value"] = (field_name, selector, desc)
            dialog.destroy()

        ttk.Button(action_row, text="取消", command=dialog.destroy, style="Ghost.TButton").pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(action_row, text="保存", command=submit, style="Accent.TButton").pack(side=tk.LEFT)
        dialog.wait_window()
        return result.get("value")

    def add_selector(self):
        value = self._show_selector_dialog("新增字段")
        if value:
            self.selector_tree.insert("", tk.END, values=value)

    def edit_selector(self):
        selected = self.selector_tree.selection()
        if not selected:
            messagebox.showwarning("未选择字段", "请先在表格中选择要编辑的字段。")
            return
        item_id = selected[0]
        values = self.selector_tree.item(item_id, "values")
        updated = self._show_selector_dialog("编辑字段", values)
        if updated:
            self.selector_tree.item(item_id, values=updated)

    def delete_selector(self):
        selected = self.selector_tree.selection()
        if not selected:
            messagebox.showwarning("未选择字段", "请先在表格中选择要删除的字段。")
            return
        if not messagebox.askyesno("确认删除", "确认删除当前选中的字段吗？"):
            return
        for item_id in selected:
            self.selector_tree.delete(item_id)

    def clear_selectors(self):
        for item_id in self.selector_tree.get_children():
            self.selector_tree.delete(item_id)

    def load_example_selectors(self):
        self.clear_selectors()
        for row in EXAMPLE_SELECTORS:
            self.selector_tree.insert("", tk.END, values=row)
        self.log("已加载通用示例选择器，可以再按目标站点微调。", "INFO")

    def apply_template(self, show_message=True):
        template_name = self.template_var.get().strip()
        template_id = self.template_name_map.get(template_name)
        if not template_id:
            messagebox.showwarning("模板不存在", "未找到所选模板。")
            return

        template = self.templates[template_id]
        self.current_template_id = template_id
        self.current_template = template
        self.template_desc_var.set(template["description"])
        self._apply_template_input_state(template)
        self.url_var.set(template["example_url"])
        self.mode_var.set(template.get("mode", "list"))
        self.list_selector_var.set(template["list_selector"])
        self._on_mode_changed()

        self.clear_selectors()
        for field_name, selector in template["fields"].items():
            self.selector_tree.insert("", tk.END, values=(field_name, selector, f"来自 {template['name']} 模板"))

        self.log(f"已应用模板：{template['name']}", "SUCCESS")
        self.log(f"示例地址：{template['example_url']}", "INFO")
        self.root.after(200, lambda url=template["example_url"]: self._schedule_advanced_prewarm(url))
        if show_message:
            messagebox.showinfo(
                "模板已应用",
                f"{template['name']} 已就绪。\n\n字段数量：{len(template['fields'])}\n你可以直接开始抓取，也可以继续微调。",
            )

    def check_advanced_mode_availability(self):
        try:
            available = bool(is_advanced_mode_available())
        except Exception:
            available = False
        if available:
            if self._advanced_prewarm_inflight:
                self.advanced_state_var.set("已安装，预热中")
            elif self._advanced_prewarm_ready:
                self.advanced_state_var.set("已预热")
            else:
                self.advanced_state_var.set("已安装")
        else:
            self.advanced_state_var.set("未检测到 Edge/Chrome 自动化引擎")
            self.advanced_mode_var.set(False)

    def on_advanced_mode_toggle(self):
        if not self.advanced_mode_var.get():
            self.log("已切回标准模式，优先走更快的请求链路。", "INFO")
            return
        try:
            available = bool(is_advanced_mode_available())
        except Exception:
            available = False
        if not available:
            self.advanced_mode_var.set(False)
            messagebox.showinfo(
                "高级模式不可用",
                "当前环境未检测到可用的高级浏览器引擎。\n\n"
                "推荐先确认本机已安装 Microsoft Edge；\n"
                "如果仍需 Chrome 兜底，再执行：\n"
                "py -3 -m pip install undetected-chromedriver",
            )
            return
        self._schedule_advanced_prewarm(self.url_var.get().strip() if hasattr(self, "url_var") else "")
        self.log("已启用高级模式，适合有反爬或大量 JS 渲染的网站。", "INFO")

    def _append_log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        colors = {
            "INFO": "#8bd3dd",
            "SUCCESS": "#7fe19b",
            "WARNING": "#f8d16c",
            "ERROR": "#ff8b8b",
        }
        self.log_text.insert(tk.END, f"[{timestamp}] ", "time")
        self.log_text.insert(tk.END, f"[{level}] ", level)
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.tag_config("time", foreground="#6e859c")
        self.log_text.tag_config(level, foreground=colors.get(level, self.LOG_TEXT))
        self.log_text.see(tk.END)

    def log(self, message, level="INFO"):
        if threading.current_thread() is threading.main_thread():
            self._append_log(message, level)
        else:
            self._run_on_ui_thread(self._append_log, message, level)

    def preview_data(self, data, header="结果预览"):
        if threading.current_thread() is not threading.main_thread():
            self._run_on_ui_thread(self.preview_data, data, header)
            return
        self.preview_text.delete("1.0", tk.END)
        text = json.dumps(data, ensure_ascii=False, indent=2)
        self.preview_text.insert("1.0", f"{header}\n\n{text}")

    def get_selectors(self):
        selectors = {}
        for item_id in self.selector_tree.get_children():
            values = self.selector_tree.item(item_id, "values")
            if len(values) >= 2:
                selectors[values[0]] = values[1]
        return selectors

    def _get_active_workflow(self):
        return (self.current_template or {}).get("workflow", "")

    def _create_crawler(self, url, crawl_config):
        delay = max(crawl_config["delay"], 0)
        requests_per_second = 2 if delay <= 0 else max(0.2, 1.0 / delay)
        try:
            crawler = UniversalCrawler(
                base_url=url,
                output_dir=crawl_config["output_dir"],
                use_advanced_mode=crawl_config["use_advanced"],
                requests_per_second=requests_per_second,
                max_retries=3,
                advanced_user_data_dir=self.advanced_user_data_dir,
            )
        except TypeError:
            crawler = UniversalCrawler(
                base_url=url,
                output_dir=crawl_config["output_dir"],
                use_advanced_mode=crawl_config["use_advanced"],
            )
        self.current_crawler = crawler
        return crawler

    def _set_running_state(self, running):
        self.is_crawling = running
        self.start_btn.config(state=tk.DISABLED if running else tk.NORMAL)
        self.stop_btn.config(state=tk.NORMAL if running else tk.DISABLED)
        if running:
            self.progress.start(10)
        else:
            self.progress.stop()

    def _set_summary(self, status=None, pages=None, items=None, saved=None):
        if threading.current_thread() is not threading.main_thread():
            self._run_on_ui_thread(self._set_summary, status, pages, items, saved)
            return
        if status is not None:
            self.summary_status_var.set(status)
        if pages is not None:
            self.summary_pages_var.set(str(pages))
        if items is not None:
            self.summary_items_var.set(str(items))
        if saved is not None:
            self.summary_saved_var.set(saved)

    def start_crawling(self):
        url = self.url_var.get().strip()
        workflow = self._get_active_workflow()
        if not url:
            prompt = "请输入书名或书籍 URL。" if workflow == "biquuge_full_book" else "请输入目标 URL。"
            messagebox.showwarning("缺少输入", prompt)
            return

        selectors = self.get_selectors()
        if not selectors and not workflow:
            messagebox.showwarning("缺少字段", "请至少配置一个字段选择器。")
            return

        crawl_config = {
            "mode": self.mode_var.get(),
            "workflow": workflow,
            "use_advanced": self.advanced_mode_var.get(),
            "list_selector": self.list_selector_var.get().strip(),
            "limit": self.limit_var.get(),
            "delay": self.delay_var.get(),
            "output_dir": self.output_var.get().strip() or DEFAULT_OUTPUT_DIR,
            "format": self.format_var.get(),
        }

        if not workflow and crawl_config["mode"] == "list" and not crawl_config["list_selector"]:
            messagebox.showwarning("缺少列表选择器", "列表页模式下需要填写列表容器选择器。")
            return

        self.clear_log()
        self.clear_preview()
        self.status_var.set("正在抓取，请稍候…")
        self._set_summary(status="运行中", pages=0, items=0)
        self._set_running_state(True)

        worker = threading.Thread(target=self.run_crawler, args=(url, selectors, crawl_config), daemon=True)
        self.worker_thread = worker
        worker.start()

    def run_crawler(self, url, selectors, crawl_config):
        crawler = None
        try:
            # 检查是否已停止
            if not self.is_running:
                self.log("⏹ 爬取在启动前被取消", "WARNING")
                self._set_summary(status="已停止")
                return
            
            workflow = crawl_config.get("workflow", "")
            self.log(f"开始抓取：{url}", "INFO")
            if workflow == "biquuge_full_book":
                self.log("工作流：笔趣阁整本小说抓取", "INFO")
                self.log("抓取策略：入口页智能兜底，章节正文并发抓取，失败章节自动重试。", "INFO")
            else:
                self.log(f"抓取模式：{'列表页' if crawl_config['mode'] == 'list' else '单页'}", "INFO")
            self.log(f"引擎模式：{'高级模式' if crawl_config['use_advanced'] else '标准模式'}", "INFO")
            self.log(f"字段数量：{len(selectors)}", "INFO")
            self.log("-" * 56, "INFO")

            # 检查是否已停止
            if not self.is_running:
                self.log("⏹ 爬取在初始化阶段被取消", "WARNING")
                self._set_summary(status="已停止")
                return

            crawler = self._create_crawler(url, crawl_config)
            self.current_crawler = crawler  # 保存引用以便停止
            result_data = None

            # 检查是否已停止
            if not self.is_running:
                self.log("⏹ 爬取在执行前被取消", "WARNING")
                self._set_summary(status="已停止")
                return

            if workflow == "biquuge_full_book":
                self.log("开始搜索书名并抓取整本小说，这一步会自动解析目录与章节。", "INFO")
                result_data = crawler.crawl_biquuge_full_book(url)
            elif crawl_config["mode"] == "list":
                self.log(f"列表容器：{crawl_config['list_selector']}", "INFO")
                result_data = crawler.crawl_list_page(
                    url,
                    crawl_config["list_selector"],
                    selectors,
                    max_items=crawl_config["limit"],
                )
            else:
                result_data = crawler.crawl_single_page(url, selectors)

            # 检查是否已停止
            if not self.is_running:
                self.log("⏹ 爬取在数据处理阶段被取消", "WARNING")
                self.log("提示：已爬取的数据将不会保存", "WARNING")
                self._set_summary(status="已停止（未保存数据）")
                return

            if result_data:
                count = result_data.get("chapter_count", 0) if workflow == "biquuge_full_book" else (len(result_data) if isinstance(result_data, list) else 1)
                self.log(f"成功提取 {count} 条数据", "SUCCESS")
                if workflow == "biquuge_full_book":
                    self.preview_data(
                        {
                            "书名": result_data.get("book_title", ""),
                            "书籍地址": result_data.get("book_url", ""),
                            "目录地址": result_data.get("directory_url", ""),
                            "章节数": result_data.get("chapter_count", 0),
                            "失败章节数": result_data.get("failed_chapter_count", 0),
                            "简介": result_data.get("intro", ""),
                            "前5章": [
                                {
                                    "index": item.get("index"),
                                    "章节标题": item.get("chapter_title"),
                                    "章节链接": item.get("chapter_url"),
                                }
                                for item in result_data.get("chapters", [])[:5]
                            ],
                        },
                        header="整本小说抓取预览",
                    )
                else:
                    self.preview_data(result_data)

                filename = f"crawled_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                save_result = crawler.save_results(result_data, filename, preferred_format=crawl_config["format"])

                if save_result and save_result.get("path"):
                    self.last_saved_path = save_result["path"]
                    save_type = save_result.get("save_type", "json")
                    saved_count = save_result.get("saved_count", count)
                    self._set_summary(items=saved_count, saved=os.path.basename(self.last_saved_path))
                    if save_type == "images":
                        self.log(f"已保存图片 {saved_count} 张 -> {self.last_saved_path}", "SUCCESS")
                        self.preview_data(
                            {
                                "save_type": "images",
                                "saved_count": saved_count,
                                "path": self.last_saved_path,
                                "files": save_result.get("files", [])[:12],
                            },
                            header="图片保存结果",
                        )
                    elif save_type == "novel_book":
                        self.log(f"已保存整本小说，共 {saved_count} 章 -> {self.last_saved_path}", "SUCCESS")
                        self.preview_data(
                            {
                                "save_type": "novel_book",
                                "saved_count": saved_count,
                                "path": self.last_saved_path,
                                "directory": save_result.get("directory", ""),
                                "files": save_result.get("files", []),
                            },
                            header="整本小说保存结果",
                        )
                    else:
                        self.log(f"已保存结果 -> {self.last_saved_path}", "SUCCESS")

                    self.root.after(
                        0,
                        lambda: messagebox.showinfo(
                            "抓取完成",
                            f"提取完成。\n\n保存类型：{save_type}\n保存位置：\n{self.last_saved_path}",
                        ),
                    )
                else:
                    self.log("提取成功，但保存阶段没有生成输出文件。", "WARNING")
            else:
                self.log("没有提取到数据，请检查页面是否被拦截或选择器是否命中。", "WARNING")
                self._set_summary(items=0)
                self.root.after(0, lambda: messagebox.showwarning("没有数据", "没有提取到数据，请检查选择器或访问状态。"))

            stats = crawler.get_stats() if crawler else {}
            self.log("-" * 56, "INFO")
            self.log("抓取统计", "INFO")
            self.log(f"总页面数：{stats.get('total_pages', 0)}", "INFO")
            self.log(f"成功页面：{stats.get('success_pages', 0)}", "INFO")
            self.log(f"失败页面：{stats.get('failed_pages', 0)}", "INFO")
            self.log(f"总数据条数：{stats.get('total_items', 0)}", "INFO")
            self._set_summary(
                status="已完成" if stats.get("success_pages", 0) else "已结束",
                pages=stats.get("success_pages", 0),
                items=stats.get("total_items", 0),
            )

            if stats.get("last_error_reason") == "flaticon_access_denied":
                self.log("Flaticon 返回了 Access Denied 页面，当前网络出口可能被风控。", "ERROR")
                self.log("建议先换网络或代理出口，再尝试高级模式。", "WARNING")
            elif stats.get("last_error_reason") == "novel_book_not_found":
                self.log("没有在 biquuge 搜到对应书籍，请检查书名是否准确，或直接粘贴书籍 URL。", "WARNING")
            elif stats.get("last_error_reason") == "novel_book_page_failed":
                self.log("书籍详情页访问失败，可能是站点波动或搜索结果命中了无效链接。", "WARNING")
            elif stats.get("last_error_reason") == "novel_directory_not_found":
                self.log("目录页已经访问到，但没有识别出章节链接；这通常是站点目录结构变体导致的。", "WARNING")
            elif stats.get("last_error_reason") == "novel_chapter_fetch_failed":
                self.log("目录已拿到，但章节正文抓取全部失败；这通常是正文页结构变化或访问被限制。", "WARNING")
            elif stats.get("last_error_reason") == "novel_book_mixed_roots":
                self.log("检测到章节链接来自多本小说，程序已拦截本次保存，避免把串书结果写入文件。", "ERROR")
        except Exception as exc:
            self.log(f"抓取失败：{exc}", "ERROR")
            self._set_summary(status="失败")
            self.root.after(0, lambda: messagebox.showerror("抓取失败", f"运行时出现错误：\n{exc}"))
        finally:
            if crawler:
                try:
                    crawler.close()
                except Exception:
                    pass
            self.current_crawler = None
            self.root.after(0, self.crawling_finished)

    def stop_crawling(self):
        """停止爬取"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # 更新状态栏
        self.status_var.set("⏹ 正在停止爬取...")
        
        self.log("=" * 50, "WARNING")
        self.log("⏹ 用户请求停止爬取", "WARNING")
        self.log("=" * 50, "WARNING")
        self.log("", "INFO")
        self.log("停止流程：", "INFO")
        self.log("  [1/3] 设置停止标志...", "INFO")
        
        # 请求爬虫停止
        crawler = self.current_crawler
        if crawler:
            try:
                self.log("  [2/3] 请求爬虫停止...", "INFO")
                crawler.request_stop()
                self.log("  ✓ 停止请求已发送", "SUCCESS")
                self.log("  [3/3] 等待当前操作完成...", "INFO")
                self.log("", "INFO")
                self.log("提示：爬虫将在当前操作完成后停止", "WARNING")
                self.log("  - 如果正在等待网络响应，需要等待超时或完成", "WARNING")
                self.log("  - 如果正在处理数据，需要等待处理完成", "WARNING")
                self.log("  - 预计等待时间：5-30秒", "WARNING")
            except Exception as e:
                error_msg = str(e)
                self.log(f"  ✗ 发送停止请求时出错: {error_msg}", "ERROR")
                self.log("  [3/3] 尝试强制关闭...", "WARNING")
                # 强制关闭
                try:
                    crawler.close()
                    self.log("  ✓ 已强制关闭爬虫", "SUCCESS")
                except Exception as close_error:
                    self.log(f"  ✗ 强制关闭失败: {close_error}", "ERROR")
        else:
            self.log("  [2/3] 无活动爬虫实例", "INFO")
            self.log("  [3/3] 停止完成", "SUCCESS")
        
        self.log("", "INFO")
        self.log("=" * 50, "WARNING")
        self.log("⏹ 停止请求已处理，等待爬虫响应...", "WARNING")
        self.log("=" * 50, "WARNING")

    def crawling_finished(self):
        self._set_running_state(False)
        if self.summary_status_var.get() == "运行中":
            self._set_summary(status="已停止")
        self.status_var.set("就绪")


def main():
    root = tk.Tk()
    app = ModernUniversalCrawlerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
