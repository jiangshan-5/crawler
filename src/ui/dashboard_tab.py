import os
import json
import subprocess
import customtkinter as ctk
from datetime import datetime
from src.ui.theme import COLORS


class DashboardFrame(ctk.CTkFrame):
    """
    Intelligence Dashboard - shows crawl history files with preview support.
    """
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        self.header.grid_columnconfigure(0, weight=1)

        self.title = ctk.CTkLabel(
            self.header,
            text="历史任务回溯",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=COLORS.get("primary", "#3b82f6")
        )
        self.title.grid(row=0, column=0, sticky="w")

        # Scrollable grid for history cards
        self.scroll_canvas = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            label_text="📁 历史任务回溯"
        )
        self.scroll_canvas.grid(row=1, column=0, sticky="nsew")
        self.scroll_canvas.grid_columnconfigure((0, 1, 2), weight=1)

        # Footer
        self.footer = ctk.CTkFrame(self, fg_color="transparent")
        self.footer.grid(row=2, column=0, sticky="ew", pady=10)

        self.btn_refresh = ctk.CTkButton(
            self.footer,
            text="↺ 刷新",
            fg_color=COLORS.get("primary", "#3b82f6"),
            corner_radius=20,
            command=self.refresh_history
        )
        self.btn_refresh.pack(side="right", padx=10)

        self.refresh_history()

    def refresh_history(self):
        """Scan output directory for crawled data files and render cards."""
        for widget in self.scroll_canvas.winfo_children():
            widget.destroy()

        dir_path = self.controller.output_dir_var.get()
        if not os.path.isdir(dir_path):
            self._show_empty(f"输出目录不存在:\n{dir_path}")
            return

        MEDIA_SUBDIRS = {'images', 'audio', 'video'}

        # Collect result entries: files (JSON/CSV) + unified result folders
        try:
            entries = []
            for name in os.listdir(dir_path):
                full = os.path.join(dir_path, name)
                if name.endswith('_raw.json'):
                    continue
                if os.path.isfile(full) and name.endswith(('.json', '.csv', '.txt')):
                    entries.append(name)
                elif os.path.isdir(full):
                    children = os.listdir(full)
                    has_txt  = any(f.endswith('.txt') for f in children)
                    has_json = any(f.endswith(('.json', '.csv')) for f in children)
                    has_media = any(
                        os.path.isdir(os.path.join(full, sd)) and os.listdir(os.path.join(full, sd))
                        for sd in MEDIA_SUBDIRS if os.path.isdir(os.path.join(full, sd))
                    )
                    if has_txt or has_json or has_media:
                        entries.append(name)
            entries = sorted(entries, reverse=True)
        except Exception as e:
            self._show_empty(f"读取目录失败: {e}")
            return

        if not entries:
            self._show_empty("暂无历史记录\n完成一次抓取后将在此显示")
            return

        for i, name in enumerate(entries):
            fpath = os.path.join(dir_path, name)
            self._build_card(i, name, fpath)

    def _build_card(self, index, fname, fpath):
        """Build a single history card for a file or result folder."""
        import re as _re
        is_folder = os.path.isdir(fpath)

        IMG_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp'}
        AUD_EXTS = {'.mp3', '.wav', '.flac', '.ogg', '.aac', '.m4a', '.wma', '.opus'}
        VID_EXTS = {'.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv', '.wmv'}

        # ── Detect content type ───────────────────────────────────────────
        folder_txt = None
        folder_img_dir = None
        folder_audio_dir = None
        folder_video_dir = None

        def _media_subdir(parent, name, exts):
            sub = os.path.join(parent, name)
            if os.path.isdir(sub) and os.listdir(sub):
                return sub
            return None

        if is_folder:
            children = os.listdir(fpath)
            txts = [c for c in children if c.endswith('.txt')]
            folder_txt = os.path.join(fpath, txts[0]) if txts else None

            folder_img_dir   = _media_subdir(fpath, 'images', IMG_EXTS)
            folder_audio_dir = _media_subdir(fpath, 'audio',  AUD_EXTS)
            folder_video_dir = _media_subdir(fpath, 'video',  VID_EXTS)
            # Fallback: images directly in folder (legacy)
            if not folder_img_dir and any(os.path.splitext(c)[1].lower() in IMG_EXTS for c in children):
                folder_img_dir = fpath
        else:
            if fpath.endswith('.txt'):
                folder_txt = fpath
            # Legacy sibling folder
            base = fname.rsplit('.', 1)[0]
            candidate = os.path.join(os.path.dirname(fpath), base + '_images')
            if os.path.isdir(candidate) and os.listdir(candidate):
                folder_img_dir = candidate

        has_images = folder_img_dir is not None
        has_audio  = folder_audio_dir is not None
        has_video  = folder_video_dir is not None

        # ── Display date ─────────────────────────────────────────────────
        display_date = fname
        m = _re.search(r'(\d{8}_\d{6})', fname)
        if m:
            try:
                from datetime import datetime as _dt
                dt = _dt.strptime(m.group(1), '%Y%m%d_%H%M%S')
                display_date = '📅 ' + dt.strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                pass

        # ── Badge (multi-media aware) ─────────────────────────────────────
        def _count_in(d, exts):
            return sum(1 for f in os.listdir(d) if os.path.splitext(f)[1].lower() in exts) if d else 0

        if is_folder:
            parts = []
            if folder_txt:
                size_kb = os.path.getsize(folder_txt) // 1024
                parts.append(f'📖 小说 {size_kb}KB')
            n_img = _count_in(folder_img_dir, IMG_EXTS)
            n_aud = _count_in(folder_audio_dir, AUD_EXTS)
            n_vid = _count_in(folder_video_dir, VID_EXTS)
            if n_img: parts.append(f'🖼 {n_img}张')
            if n_aud: parts.append(f'🎵 {n_aud}首')
            if n_vid: parts.append(f'🎬 {n_vid}个')
            if not parts:
                children = os.listdir(fpath)
                jsons = [c for c in children if c.endswith(('.json', '.csv'))]
                if jsons:
                    cnt = self._count_records(os.path.join(fpath, jsons[0]))
                    parts.append(f'JSON · {cnt}条' if cnt >= 0 else 'JSON')
                else:
                    parts.append('📁 结果文件夹')
            badge_text = '  ·  '.join(parts)
        else:
            item_count = self._count_records(fpath)
            ext = fname.rsplit('.', 1)[-1].upper()
            badge_text = f'{ext}  ·  {item_count} 条记录' if item_count >= 0 else ext

        # ── Card frame ────────────────────────────────────────────────────
        card = ctk.CTkFrame(
            self.scroll_canvas,
            fg_color=COLORS.get("card", "#ffffff"),
            border_width=1,
            border_color="#e5e7eb",
            corner_radius=20
        )
        card.grid(row=index // 3, column=index % 3, padx=12, pady=12, sticky="nsew")

        ctk.CTkLabel(card, text=display_date,
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=COLORS.get("primary", "#3b82f6")).pack(pady=(15, 2))

        short_name = fname if len(fname) <= 28 else fname[:25] + "..."
        ctk.CTkLabel(card, text=short_name,
                     font=ctk.CTkFont(size=11),
                     text_color=COLORS.get("text", "#374151")).pack(pady=2)

        ctk.CTkLabel(card, text=badge_text,
                     font=ctk.CTkFont(size=11),
                     text_color="#6b7280").pack(pady=(0, 8))

        # ── Buttons ───────────────────────────────────────────────────────
        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(side="bottom", fill="x", padx=12, pady=12)

        ctk.CTkButton(
            btn_row, text="📂 位置", height=32, corner_radius=12,
            fg_color=COLORS.get("primary", "#0ea5e9"),
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda p=fpath: self._reveal_in_explorer(p)
        ).pack(side="left", expand=True, padx=(0, 3))

        if folder_txt:
            ctk.CTkButton(
                btn_row, text="📖 阅读", height=32, corner_radius=12,
                fg_color="#ecfdf5", text_color="#059669",
                font=ctk.CTkFont(size=12, weight="bold"),
                command=lambda p=folder_txt: os.startfile(p)
            ).pack(side="left", expand=True, padx=(3, 0))
        elif not is_folder:
            ctk.CTkButton(
                btn_row, text="👁 预览", height=32, corner_radius=12,
                fg_color="#f1f5f9", text_color="#475569",
                font=ctk.CTkFont(size=12, weight="bold"),
                command=lambda p=fpath: self._preview_file(p)
            ).pack(side="left", expand=True, padx=3)

        if has_images:
            ctk.CTkButton(
                btn_row, text="🖼 图库", height=32, corner_radius=12,
                fg_color="#fef3c7", text_color="#d97706",
                font=ctk.CTkFont(size=12, weight="bold"),
                command=lambda f=folder_img_dir: self._open_gallery(f)
            ).pack(side="left", expand=True, padx=(3, 0))

        if has_audio:
            ctk.CTkButton(
                btn_row, text="🎵 音频", height=32, corner_radius=12,
                fg_color="#ede9fe", text_color="#7c3aed",
                font=ctk.CTkFont(size=12, weight="bold"),
                command=lambda f=folder_audio_dir: os.startfile(f)
            ).pack(side="left", expand=True, padx=(3, 0))

        if has_video:
            ctk.CTkButton(
                btn_row, text="🎬 视频", height=32, corner_radius=12,
                fg_color="#fce7f3", text_color="#db2777",
                font=ctk.CTkFont(size=12, weight="bold"),
                command=lambda f=folder_video_dir: os.startfile(f)
            ).pack(side="left", expand=True, padx=(3, 0))


    def _open_gallery(self, img_folder):
        """Open a scrollable thumbnail gallery window for downloaded images."""
        try:
            from PIL import Image as PILImage
        except ImportError:
            import subprocess
            subprocess.run(['explorer', os.path.normpath(img_folder)])
            return

        # Collect image files
        supported = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
        img_files = sorted([
            os.path.join(img_folder, f) for f in os.listdir(img_folder)
            if os.path.splitext(f.lower())[-1] in supported
        ])

        if not img_files:
            import subprocess
            subprocess.run(['explorer', os.path.normpath(img_folder)])
            return

        win = ctk.CTkToplevel(self)
        win.title(f"🖼 图片画廊 — {os.path.basename(img_folder)}  ({len(img_files)} 张)")
        win.geometry("980x680")
        win.grab_set()

        # Top bar
        top = ctk.CTkFrame(win, fg_color="transparent")
        top.pack(fill="x", padx=15, pady=(12, 0))
        ctk.CTkLabel(top, text=f"共 {len(img_files)} 张图片",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        ctk.CTkButton(top, text="📂 打开文件夹", width=120, height=30,
                      command=lambda: self._reveal_in_explorer(img_files[0])
                      ).pack(side="right")

        # Scrollable grid of thumbnails
        scroll = ctk.CTkScrollableFrame(win, fg_color="#f8fafc")
        scroll.pack(fill="both", expand=True, padx=15, pady=12)

        THUMB = 160
        COLS = 5
        for i, img_path in enumerate(img_files):
            try:
                img = PILImage.open(img_path)
                img.thumbnail((THUMB, THUMB), PILImage.LANCZOS)
                photo = ctk.CTkImage(img, size=img.size)
            except Exception:
                continue

            cell = ctk.CTkFrame(scroll, fg_color="white", corner_radius=8,
                                border_width=1, border_color="#e2e8f0")
            cell.grid(row=i // COLS, column=i % COLS, padx=6, pady=6, sticky="nsew")

            # Make columns equal
            scroll.grid_columnconfigure(i % COLS, weight=1)

            ctk.CTkLabel(cell, image=photo, text="").pack(padx=8, pady=(8, 2))
            ctk.CTkLabel(cell,
                         text=os.path.basename(img_path)[:18],
                         font=ctk.CTkFont(size=9),
                         text_color="#6b7280").pack(padx=4, pady=(0, 6))

            # Click to open full-size in default viewer
            cell.bind("<Button-1>", lambda e, p=img_path: os.startfile(p))


    def _count_records(self, fpath):
        """Try to count the number of records in a JSON or CSV file."""
        try:
            if fpath.endswith('.json'):
                with open(fpath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return len(data) if isinstance(data, list) else 1
            elif fpath.endswith('.csv'):
                with open(fpath, 'r', encoding='utf-8-sig') as f:
                    return sum(1 for _ in f) - 1  # subtract header
        except Exception:
            pass
        return -1

    def _reveal_in_explorer(self, fpath):
        """Open Windows Explorer and highlight the specific file."""
        try:
            # /select, and path must NOT be separate args - use shell mode
            norm = os.path.normpath(fpath)
            subprocess.Popen(f'explorer /select,"{norm}"', shell=True)
        except Exception as e:
            # Fallback: just open the containing folder
            try:
                os.startfile(os.path.dirname(fpath))
            except Exception:
                pass

    def _preview_file(self, fpath):
        """Show a simple content preview popup."""
        try:
            with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read(3000)
        except Exception as e:
            content = f"无法读取文件: {e}"

        win = ctk.CTkToplevel(self)
        win.title(f"预览 — {os.path.basename(fpath)}")
        win.geometry("700x500")
        win.grab_set()

        text = ctk.CTkTextbox(win, font=ctk.CTkFont(family="Consolas", size=12))
        text.pack(fill="both", expand=True, padx=15, pady=15)
        text.insert("end", content)
        text.configure(state="disabled")

    def _show_empty(self, msg):
        """Render an empty-state message in the grid."""
        ctk.CTkLabel(
            self.scroll_canvas, text=msg,
            font=ctk.CTkFont(size=14), text_color="#9ca3af"
        ).grid(row=0, column=0, columnspan=3, pady=60)

    def update_lang(self, t):
        self.title.configure(text=t.get("history_title", "历史任务回溯"))
        self.scroll_canvas.configure(label_text=t.get("history_title", "📁 历史任务回溯"))
        self.btn_refresh.configure(text=t.get("btn_refresh", "↺ 刷新"))
