import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from src.ui.theme import COLORS
from src.ui.translations import TRANSLATIONS
from src.config.website_templates import WEBSITE_TEMPLATES
from src.config.site_rules import get_site_rule

class ConfigFrame(ctk.CTkScrollableFrame):
    """
    Main configuration interface for crawler parameters and templates.
    Part of the modular project restructuring.
    """
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self._active_template_id = None  # Track which template is active
        
        self.grid_columnconfigure(0, weight=1)

        # Template Selection Row
        self.tpl_row = ctk.CTkFrame(self, fg_color="transparent")
        self.tpl_row.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
        self.tpl_row.grid_columnconfigure(1, weight=1)
        
        self.tpl_label = ctk.CTkLabel(self.tpl_row, text="📋 选择模板", font=ctk.CTkFont(size=16, weight="bold"))
        self.tpl_label.grid(row=0, column=0, padx=(0, 15))
        
        tpl_names = [tpl["name"] for tpl in WEBSITE_TEMPLATES.values()]
        self.tpl_menu = ctk.CTkOptionMenu(
            self.tpl_row, 
            values=tpl_names, 
            width=220, 
            fg_color=COLORS["card"], 
            text_color=COLORS["text"],
            button_color=COLORS["primary"], 
            corner_radius=10,
            command=self._apply_template
        )
        self.tpl_menu.grid(row=0, column=1, sticky="w")

        # Configuration Card
        self.config_card = ctk.CTkFrame(self, fg_color=COLORS["card"], border_width=1, border_color="#e2e8f0", corner_radius=15)
        self.config_card.grid(row=2, column=0, sticky="ew", pady=(20, 50), padx=10)
        self.config_card.grid_columnconfigure(0, weight=1)
        
        self.inner = ctk.CTkFrame(self.config_card, fg_color="transparent")
        self.inner.grid(row=0, column=0, padx=25, pady=25, sticky="ew")
        self.inner.grid_columnconfigure(0, weight=1)

        # Inputs
        self.url_label_widget, self.url_box = self._add_entry_section(
            self.inner, 0, "目标 URL", controller.url_var, "https://", "url"
        )
        self.list_label_widget, self.list_sel_box = self._add_entry_section(
            self.inner, 2, "列表容器选择器", controller.list_selector_var, ".item-list", "selector"
        )

        # Crawl count
        self.limit_label = ctk.CTkLabel(self.inner, text="爬取数量 (留空或非数字视为不限制)", font=ctk.CTkFont(size=13, weight="bold"))
        self.limit_label.grid(row=4, column=0, sticky="w", pady=(0, 5))
        self.limit_box = ctk.CTkEntry(
            self.inner, textvariable=controller.limit_var,
            height=42, corner_radius=10,
            placeholder_text="默认: 30"
        )
        self.limit_box.grid(row=5, column=0, pady=(0, 20), sticky="ew")

        # Selector Tree (using ttk.Treeview as per original design)
        self._setup_treeview(self.inner)

        # Options (Advanced Mode & Delay)
        self._setup_options_row(self.inner)

        # Execution Panel (Launch & Stop)
        self._setup_execution_panel(self.config_card)

    def _setup_treeview(self, parent):
        self.tree_label = ctk.CTkLabel(parent, text="提取字段映射", font=ctk.CTkFont(size=14, weight="bold"))
        self.tree_label.grid(row=6, column=0, sticky="w", pady=(10, 5))
        
        # Lighter border for tree frame
        self.tree_frame = ctk.CTkFrame(parent, fg_color="#ffffff", border_width=1, border_color="#e5e7eb")
        self.tree_frame.grid(row=7, column=0, pady=(5, 15), sticky="nsew")
        
        cols = ("Field", "Selector")
        
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", 
                        background="#ffffff", 
                        foreground="#334155", 
                        rowheight=40, 
                        fieldbackground="#ffffff",
                        borderwidth=0,
                        font=("Microsoft YaHei", 11))
        style.configure("Treeview.Heading", 
                        background="#f1f5f9", 
                        foreground="#475569", 
                        font=("Microsoft YaHei", 12, "bold"),
                        borderwidth=0)
        style.map("Treeview", 
                  background=[("selected", "#e0f2fe")],
                  foreground=[("selected", "#0369a1")])
                  
        self.tree = ttk.Treeview(self.tree_frame, columns=cols, show="headings", height=8)
        self.tree.heading("Field", text="字段名称")
        self.tree.heading("Selector", text="CSS 选择器")
        self.tree.column("Field", width=150)
        self.tree.column("Selector", width=400)
        self.tree.pack(side="left", fill="both", expand=True)

        self.tree_ctrl = ctk.CTkFrame(parent, fg_color="transparent")
        self.tree_ctrl.grid(row=8, column=0, sticky="w")
        
        self.add_btn = ctk.CTkButton(self.tree_ctrl, text=" 添加字段", width=110, height=32, corner_radius=16, 
                                      font=ctk.CTkFont(weight="bold"), fg_color="#0ea5e9", text_color="#ffffff",
                                      command=self._add_field)
        self.add_btn.pack(side="left", padx=5)
        
        self.del_btn = ctk.CTkButton(self.tree_ctrl, text=" 删除选中", width=100, height=32, corner_radius=16, 
                                      font=ctk.CTkFont(weight="bold"), fg_color="#fce7f3", text_color="#db2777", hover_color="#fbcfe8", 
                                      command=self._del_field)
        self.del_btn.pack(side="left", padx=5)

    def _setup_options_row(self, parent):
        self.opt_row = ctk.CTkFrame(parent, fg_color="transparent")
        self.opt_row.grid(row=9, column=0, sticky="ew", pady=(25, 10))
        
        self.adv_toggle = ctk.CTkSwitch(
            self.opt_row, 
            text="高级模式 (浏览器渲染)", 
            variable=self.controller.adv_mode_var, 
            progress_color=COLORS["primary"]
        )
        self.adv_toggle.pack(side="left")
        
        self.wait_label = ctk.CTkLabel(self.opt_row, text="  |  渲染等待: 3s", font=ctk.CTkFont(size=12))
        self.wait_label.pack(side="left", padx=(10, 5))
        
        self.wait_slider = ctk.CTkSlider(
            self.opt_row, from_=1, to=15, number_of_steps=14,
            variable=self.controller.wait_time_var, width=150,
            command=self._update_wait_label
        )
        self.wait_slider.pack(side="left", padx=5)

    def _setup_execution_panel(self, parent):
        self.exec_frame = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        self.exec_frame.grid(row=1, column=0, sticky="ew")
        self.exec_frame.grid_columnconfigure(0, weight=1)
        
        self.btn_row = ctk.CTkFrame(self.exec_frame, fg_color="transparent")
        self.btn_row.grid(row=2, column=0, padx=25, pady=(20, 60), sticky="ew")
        self.btn_row.grid_columnconfigure(0, weight=3)
        self.btn_row.grid_columnconfigure(1, weight=1)

        self.btn_launch = ctk.CTkButton(
            self.btn_row, 
            textvariable=self.controller.btn_text_var, 
            height=60, 
            font=ctk.CTkFont(size=16, weight="bold"), 
            corner_radius=12,
            fg_color=COLORS["primary"],
            command=self.controller.start_crawl
        )
        self.btn_launch.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        self.btn_stop = ctk.CTkButton(
            self.btn_row, 
            text="⏹", 
            width=60, 
            height=60, 
            font=ctk.CTkFont(size=20), 
            corner_radius=12,
            fg_color="#fee2e2", 
            text_color="#ef4444",
            command=self.controller.stop_crawl
        )
        self.btn_stop.grid(row=0, column=1, sticky="ew")

    def _add_entry_section(self, parent, row, label, var, placeholder, icon_name):
        lbl = ctk.CTkLabel(parent, text=label, font=ctk.CTkFont(size=13, weight="bold"))
        lbl.grid(row=row, column=0, sticky="w", pady=(0, 5))
        entry = ctk.CTkEntry(parent, textvariable=var, height=42, corner_radius=10, placeholder_text=placeholder)
        entry.grid(row=row+1, column=0, pady=(0, 20), sticky="ew")
        return lbl, entry

    def _add_field(self):
        self.tree.insert("", "end", values=("new_field", ".selector"))

    def _del_field(self):
        for item in self.tree.selection(): self.tree.delete(item)

    def _update_wait_label(self, val):
        lang = self.controller.lang_var.get()
        t = TRANSLATIONS.get(lang, TRANSLATIONS["zh"])
        self.wait_label.configure(text="  |  " + t["cfg_wait_time"].format(int(val)))

    def _apply_template(self, display_name):
        target_id = next((tid for tid, tpl in WEBSITE_TEMPLATES.items() if tpl.get("name") == display_name), None)
        tpl = WEBSITE_TEMPLATES.get(target_id)
        if not tpl: return
        
        self._active_template_id = target_id  # Save for worker to look up
        
        self.url_label_widget.configure(text=tpl.get("input_label", "目标 URL"))
        self.url_box.configure(placeholder_text=tpl.get("input_hint", ""))
        self.controller.url_var.set(tpl.get("example_url", ""))
        self.controller.list_selector_var.set(tpl.get("list_selector", ""))

        # Show/hide crawl count — novels don't need it
        wf = tpl.get("workflow", "")
        if wf == "biquuge_full_book":
            self.limit_label.grid_remove()
            self.limit_box.grid_remove()
        else:
            self.limit_label.grid()
            self.limit_box.grid()

        # Auto-enable advanced mode if the template's target site requires it
        search_tpl = tpl.get("search_url_template", "")
        if search_tpl:
            rule = get_site_rule(search_tpl)
            if rule.get("force_headed"):
                self.controller.adv_mode_var.set(True)
                self.adv_toggle.select()
                cur = int(self.controller.wait_time_var.get())
                if cur < 5:
                    self.controller.wait_time_var.set(5)
                    self._update_wait_label(5)

        for i in self.tree.get_children(): self.tree.delete(i)
        for k, v in tpl.get("fields", {}).items():
            self.tree.insert("", "end", values=(k, v))

    def get_active_template(self):
        """Return the full template dict for the currently selected template."""
        return WEBSITE_TEMPLATES.get(self._active_template_id, {})

    def get_selectors(self):
        return {self.tree.item(i)["values"][0]: self.tree.item(i)["values"][1] for i in self.tree.get_children()}

    def update_lang(self, t):
        self.tpl_label.configure(text="📋 " + t["cfg_templates"])
        self.btn_launch.configure(text=t["launch"])
