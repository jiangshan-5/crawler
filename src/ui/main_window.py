import os
import queue
import threading
import tkinter as tk
from tkinter import messagebox, ttk
import customtkinter as ctk
from PIL import Image
from datetime import datetime

# Modular imports
from src.core.engine import UniversalEngine
from src.core.config import DEFAULT_OUTPUT_DIR
from src.ui.theme import COLORS
from src.ui.translations import TRANSLATIONS
from src.ui.dashboard_tab import DashboardFrame
from src.ui.config_tab import ConfigFrame
from src.ui.logs_tab import LogsFrame
from src.utils.media_downloader import download_all_media, detect_all_media_fields

class MainApp(ctk.CTk):
    """
    Refined Main Application Shell.
    Restores premium aesthetics and integrates modular components.
    """
    def __init__(self):
        super().__init__()
        
        # Window configuration
        self.title("Universal Crawler Workbench")
        self.geometry("1400x900")
        self.configure(fg_color=COLORS.get("bg", "#f1f5f9"))
        
        ctk.set_appearance_mode("Light")
        ctk.set_default_color_theme("blue")
        
        # Eliminate aliasing for Chinese characters by forcing Microsoft YaHei natively
        try:
            from customtkinter import ThemeManager
            ThemeManager.theme["CTkFont"]["family"] = "Microsoft YaHei"
        except Exception:
            pass
        
        # State Variables
        self.is_crawling = False
        self.stop_requested = False
        self.ui_queue = queue.Queue()
        self.current_engine = None
        
        # Reactive UI Variables
        self.lang_var = tk.StringVar(value="zh")
        self.status_var = tk.StringVar(value="Ready")
        self.pages_var = tk.StringVar(value="0")
        self.items_var = tk.StringVar(value="0")
        self.saved_var = tk.StringVar(value="None")
        self.success_rate_var = tk.StringVar(value="0%")
        self.progress_val = tk.DoubleVar(value=0.0)
        self.task_desc_var = tk.StringVar(value="")
        self.btn_text_var = tk.StringVar(value="LAUNCH")
        
        # Input State (Shared or passed to tabs)
        self.url_var = tk.StringVar()
        self.mode_var = tk.StringVar(value="list")
        self.list_selector_var = tk.StringVar()
        self.limit_var = ctk.IntVar(value=30)
        self.delay_var = tk.DoubleVar(value=1.0)  # seconds between requests
        self.adv_mode_var = ctk.BooleanVar(value=False)
        self.wait_time_var = ctk.IntVar(value=3)
        self.output_dir_var = tk.StringVar(value=DEFAULT_OUTPUT_DIR)
        self.format_var = tk.StringVar(value="json")

        # Icons Loading
        self.icons = {}
        self._load_icons()
        
        self._setup_layout()
        self.update_language() # Initialize text
        self._select_tab("config")
        
        # UI Event Loop
        self.after(100, self.process_ui_queue)

    def _load_icons(self):
        # We assume icons are migrated to src/ui/assets
        asset_path = os.path.join(os.path.dirname(__file__), "assets")
        icon_names = ["dashboard", "config", "logs", "lang", "logo"]
        for name in icon_names:
            path = os.path.join(asset_path, f"{name}.png")
            if os.path.exists(path):
                img = Image.open(path)
                self.icons[name] = ctk.CTkImage(light_image=img, dark_image=img, size=(20, 20))
            else:
                self.icons[name] = None

    def _get_icon(self, name):
        return self.icons.get(name)

    def _setup_layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color="#ffffff", border_width=1, border_color="#e2e8f0")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(10, weight=1)

        # Sidebar Header
        self.sidebar_header = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.sidebar_header.grid(row=0, column=0, padx=20, pady=(40, 40), sticky="ew")
        
        logo = self._get_icon("logo")
        if logo:
            logo.configure(size=(32, 32))
            ctk.CTkLabel(self.sidebar_header, image=logo, text="").pack(side="left")
            
        self.logo_text = ctk.CTkLabel(self.sidebar_header, text="  Workbench", 
                                       font=ctk.CTkFont(size=22, weight="bold"),
                                       text_color=COLORS["primary"])
        self.logo_text.pack(side="left")

        # Nav Buttons
        btn_params = {"height": 50, "corner_radius": 12, "anchor": "w", "font": ctk.CTkFont(size=14, weight="bold")}
        
        self.nav_config = ctk.CTkButton(self.sidebar, text="  Configuration", **btn_params,
                                         image=self._get_icon("config"),
                                         command=lambda: self._select_tab("config"))
        self.nav_config.grid(row=1, column=0, padx=15, pady=5, sticky="ew")

        self.nav_dashboard = ctk.CTkButton(self.sidebar, text="  Dashboard", **btn_params,
                                            image=self._get_icon("dashboard"),
                                            fg_color="transparent", text_color=COLORS["text"],
                                            command=lambda: self._select_tab("dashboard"))
        self.nav_dashboard.grid(row=2, column=0, padx=15, pady=5, sticky="ew")

        self.nav_logs = ctk.CTkButton(self.sidebar, text="  Live Logs", **btn_params,
                                       image=self._get_icon("logs"),
                                       fg_color="transparent", text_color=COLORS["text"],
                                       command=lambda: self._select_tab("logs"))
        self.nav_logs.grid(row=3, column=0, padx=15, pady=5, sticky="ew")

        # Sidebar Footer
        self.sidebar_footer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.sidebar_footer.grid(row=10, column=0, sticky="s", pady=20)
        
        self.lang_btn = ctk.CTkButton(self.sidebar_footer, text="  EN / 中文", image=self._get_icon("lang"),
                                       height=32, corner_radius=20, 
                                       fg_color="transparent", border_width=1, border_color="#e2e8f0",
                                       text_color=COLORS["text"],
                                       command=self.toggle_language)
        self.lang_btn.pack(pady=10)

        # Main Content
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=0, column=1, sticky="nsew", padx=25, pady=25)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        self.frames = {}
        self.frames["dashboard"] = DashboardFrame(self.content, self)
        self.frames["config"] = ConfigFrame(self.content, self)
        self.frames["logs"] = LogsFrame(self.content, self)

    def _select_tab(self, name):
        for f in self.frames.values(): f.grid_forget()
        self.frames[name].grid(row=0, column=0, sticky="nsew")
        
        # Highlight Button
        for btn, tab in [(self.nav_config, "config"), (self.nav_dashboard, "dashboard"), (self.nav_logs, "logs")]:
            if tab == name:
                btn.configure(fg_color=COLORS["primary"], text_color="#ffffff")
            else:
                btn.configure(fg_color="transparent", text_color=COLORS["text"])
                
        if name == "dashboard": self.frames[name].refresh_history()

    def toggle_language(self):
        self.lang_var.set("en" if self.lang_var.get() == "zh" else "zh")
        self.update_language()

    def update_language(self):
        lang = self.lang_var.get()
        t = TRANSLATIONS[lang]
        self.nav_config.configure(text=f"  {t['nav_config']}")
        self.nav_dashboard.configure(text=f"  {t['nav_dashboard']}")
        self.nav_logs.configure(text=f"  {t['nav_logs']}")
        self.status_var.set(t["status_ready"])
        for frame in self.frames.values():
            if hasattr(frame, "update_lang"): frame.update_lang(t)

    def process_ui_queue(self):
        try:
            while True:
                callback, args, kwargs = self.ui_queue.get_nowait()
                callback(*args, **kwargs)
        except queue.Empty: pass
        self.after(60, self.process_ui_queue)

    def start_crawl(self):
        if self.is_crawling:
            return
        self.is_crawling = True
        self.stop_requested = False
        lang = self.lang_var.get()
        t = TRANSLATIONS[lang]

        self.status_var.set(t["status_running"])
        self.btn_text_var.set(t["btn_crawling"])

        # Visual feedback: change launch button color to indicate running
        try:
            self.frames["config"].btn_launch.configure(
                fg_color="#059669", state="disabled")  # green = running
            self.frames["config"].btn_stop.configure(
                fg_color="#fee2e2", text_color="#ef4444", state="normal")
        except Exception:
            pass

        config = {
            "url": self.url_var.get(),
            "mode": self.mode_var.get(),
            "list_selector": self.list_selector_var.get(),
            "limit": self.limit_var.get(),
            "delay": self.delay_var.get(),
            "adv": self.adv_mode_var.get(),
            "wait": self.wait_time_var.get(),
            "dir": self.output_dir_var.get(),
            "format": self.format_var.get(),
            "selectors": self.frames["config"].get_selectors(),
            "template": self.frames["config"].get_active_template(),
        }

        self._select_tab("logs")
        # Log a clear start message
        self.frames["logs"].append("🚀 爬虫已启动，正在运行中...", "SUCCESS")
        threading.Thread(target=self._worker, args=(config,), daemon=True).start()

    def _worker(self, config):
        try:
            delay = max(0.5, config["delay"])
            log = self.frames["logs"].append
            tpl = config.get("template", {})
            workflow = tpl.get("workflow", "")

            # ── NOVEL WORKFLOW (biquuge full book) ──────────────────────────
            if workflow == "biquuge_full_book":
                keyword_or_url = config["url"].strip()
                self.ui_queue.put((log, (f"📖 小说模式 → 搜索: {keyword_or_url}", "INFO"), {}))

                engine = UniversalEngine(
                    base_url="https://www.biquuge.com/",
                    output_dir=config["dir"],
                    use_advanced_mode=False,  # novel uses standard HTTP
                    requests_per_second=1.0 / delay
                )
                self.current_engine = engine

                def _novel_progress(stage, done=0, total=0):
                    self.ui_queue.put((log, (stage, "INFO"), {}))

                saved_path = engine.crawl_novel(keyword_or_url, progress_callback=_novel_progress)
                if saved_path:
                    self.ui_queue.put((log, (f"✅ 小说保存至: {saved_path}", "SUCCESS"), {}))
                    self.ui_queue.put((self.frames["dashboard"].refresh_history, (), {}))
                else:
                    self.ui_queue.put((log, ("❌ 小说下载失败，请查看上方日志。", "ERROR"), {}))
                return  # done, skip standard flow below

            # ── MUSIC API WORKFLOW (Solara / bttts) ──────────────────────────
            if workflow == "music_api":
                from src.workflows.music_workflow import MusicWorkflow

                keyword = config["url"].strip()
                api_base = tpl.get("api_base", "")
                source = tpl.get("source", "netease")

                self.ui_queue.put((log, (f"🎵 音乐模式 → 搜索: {keyword} (音源: {source})", "INFO"), {}))

                mw = MusicWorkflow(
                    api_base=api_base,
                    source=source,
                    output_dir=config["dir"],
                    bitrate=320,
                    max_workers=4,
                    stop_check=lambda: self.stop_requested
                )

                # Search
                limit = config["limit"]
                results = mw.search(keyword, count=limit)
                if not results:
                    self.ui_queue.put((log, ("❌ 未找到任何结果，请检查关键词。", "ERROR"), {}))
                    return

                self.ui_queue.put((log, (f"🔍 找到 {len(results)} 首歌曲，开始下载...", "SUCCESS"), {}))

                # Download with progress
                def _music_progress(msg, done=0, total=0):
                    self.ui_queue.put((log, (msg, "INFO"), {}))

                saved_dir = mw.download_all(results, keyword=keyword, progress_cb=_music_progress)

                if saved_dir:
                    self.ui_queue.put((log, (f"✅ 音乐保存至: {saved_dir}", "SUCCESS"), {}))
                    self.ui_queue.put((self.frames["dashboard"].refresh_history, (), {}))
                else:
                    self.ui_queue.put((log, ("❌ 音乐下载失败。", "ERROR"), {}))
                return

            # ── STANDARD LIST CRAWL ─────────────────────────────────────────
            from urllib.parse import quote_plus
            raw_input = config["url"].strip()
            search_url_template = tpl.get("search_url_template", "")

            if search_url_template:
                url = search_url_template.replace("{query}", quote_plus(raw_input, encoding='utf-8'))
                self.ui_queue.put((log, (f"🔗 Keyword '{raw_input}' → {url}", "INFO"), {}))
            elif raw_input.startswith("http://") or raw_input.startswith("https://"):
                url = raw_input
                self.ui_queue.put((log, (f"🔗 URL: {url}", "INFO"), {}))
            else:
                self.ui_queue.put((log, (
                    f"❌ 输入 '{raw_input}' 不是合法 URL，且当前模板无搜索链接模版。请检查配置。", "ERROR"), {}))
                return

            engine = UniversalEngine(
                base_url=url,
                output_dir=config["dir"],
                use_advanced_mode=config["adv"],
                wait_time=config["wait"],
                requests_per_second=1.0 / delay
            )
            self.current_engine = engine

            list_sel = config["list_selector"]
            selectors = config["selectors"]
            self.ui_queue.put((log, (f"📋 Selector: '{list_sel}' | Fields: {list(selectors.keys())}", "INFO"), {}))

            results = engine.crawl_list_page(url, list_sel, selectors, max_items=config["limit"])

            if results:
                self.ui_queue.put((log, (f"✅ Extracted {len(results)} items.", "SUCCESS"), {}))

                # ── Create a dedicated result folder (like novels/image dirs) ──
                from src.utils.file_storage import sanitize_filename
                from datetime import datetime as _dt
                safe_kw = sanitize_filename(raw_input)
                if not safe_kw or safe_kw == 'unnamed':
                    safe_kw = 'crawled'
                ts = _dt.now().strftime('%Y%m%d_%H%M%S')
                result_folder = os.path.join(config["dir"], f"{safe_kw}_{ts}")
                os.makedirs(result_folder, exist_ok=True)

                # Save JSON/CSV inside the result folder
                saved_path = engine.save_results(
                    results,
                    preferred_format=config["format"],
                    override_dir=result_folder,
                    override_name=safe_kw
                )
                if saved_path:
                    self.ui_queue.put((log, (f"💾 Saved: {saved_path}", "INFO"), {}))

                # --- Auto Media Download Pipeline (images / audio / video) ---
                media_fields = detect_all_media_fields(results)
                has_any = any(media_fields.values())

                if has_any:
                    type_labels = {'image': '🖼 图片', 'audio': '🎵 音频', 'video': '🎬 视频'}
                    detected = [f"{type_labels[k]}({len(v)})" for k, v in media_fields.items() if v]
                    self.ui_queue.put((log, (
                        f"检测到媒体字段: {', '.join(detected)}，开始下载...", "INFO"), {}))

                    def _progress(done, total, _log=log):
                        if done % 5 == 0 or done == total:
                            self.ui_queue.put((_log, (f"  ⬇ {done}/{total} 已下载", "INFO"), {}))

                    all_results = download_all_media(
                        results, result_folder,
                        max_workers=8, progress_callback=_progress
                    )

                    for mtype, label in type_labels.items():
                        r = all_results.get(mtype)
                        if r and r['total'] > 0:
                            self.ui_queue.put((log, (
                                f"✅ {label}下载完成：{r['success']}/{r['total']} → {r['folder']}",
                                "SUCCESS"), {}))
                else:
                    self.ui_queue.put((log, ("ℹ️ 未检测到媒体URL字段，跳过下载。", "INFO"), {}))

                # Auto-refresh dashboard
                self.ui_queue.put((self.frames["dashboard"].refresh_history, (), {}))
            else:
                self.ui_queue.put((log, ("⚠️ No data extracted. Check selectors and URL.", "WARNING"), {}))

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            self.ui_queue.put((self.frames["logs"].append, (f"❌ Error: {e}\n{tb}", "ERROR"), {}))
        finally:
            was_stopped = self.stop_requested
            self.is_crawling = False
            self.stop_requested = False
            t = TRANSLATIONS[self.lang_var.get()]

            # Log completion/stop summary
            if was_stopped:
                self.ui_queue.put((self.frames["logs"].append,
                    ("🛑 爬虫已停止（用户中断）。", "WARNING"), {}))
            else:
                self.ui_queue.put((self.frames["logs"].append,
                    ("✅ 爬虫任务已完成。", "SUCCESS"), {}))

            # Restore button states via UI queue
            self.ui_queue.put((self.status_var.set, (t["status_finished"],), {}))
            self.ui_queue.put((self.btn_text_var.set, (t["launch"],), {}))
            self.ui_queue.put((self._reset_buttons, (), {}))

            if self.current_engine:
                self.current_engine.close()

    def _reset_buttons(self):
        """Restore launch/stop buttons to idle state (called on UI thread)."""
        try:
            self.frames["config"].btn_launch.configure(
                fg_color=COLORS["primary"], state="normal")
            self.frames["config"].btn_stop.configure(
                fg_color="#f1f5f9", text_color="#94a3b8", state="normal")
        except Exception:
            pass

    def stop_crawl(self):
        """Request cooperative stop with immediate user feedback."""
        if not self.is_crawling:
            return

        self.stop_requested = True

        # Immediate visual feedback
        self.frames["logs"].append("⏳ 正在停止爬虫，请等待当前任务完成...", "WARNING")
        self.status_var.set("⏳ 正在停止...")
        self.btn_text_var.set("⏳ 停止中...")

        # Grey out the stop button so user knows it was received
        try:
            self.frames["config"].btn_stop.configure(
                fg_color="#f1f5f9", text_color="#94a3b8", state="disabled")
        except Exception:
            pass

        # Signal the engine
        if self.current_engine:
            self.current_engine.request_stop()
