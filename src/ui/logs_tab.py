import customtkinter as ctk
from datetime import datetime

class LogsFrame(ctk.CTkFrame):
    """
    Dedicated logging interface component.
    Part of the modular UI refactoring.
    """
    def __init__(self, parent, controller=None):
        super().__init__(parent, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.console = ctk.CTkTextbox(
            self, font=("Consolas", 13), 
            border_width=1, border_color="#e5e7eb",
            corner_radius=12,
            fg_color="#ffffff", text_color="#334155"
        )
        self.console.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        
        self.clear = ctk.CTkButton(
            self, 
            text="Clear Logs", 
            width=100,
            height=32,
            corner_radius=16,
            fg_color="#f1f5f9",
            text_color="#475569",
            hover_color="#e2e8f0",
            font=ctk.CTkFont(weight="bold"),
            command=lambda: self.console.delete("1.0", "end")
        )
        self.clear.grid(row=1, column=0, pady=(0, 10), sticky="e")

    def update_lang(self, t):
        self.clear.configure(text=t["btn_clear"])

    def append(self, msg, level="INFO"):
        time_str = datetime.now().strftime("%H:%M:%S")
        prefix = f"[{time_str}] "
        
        # Color mapping for Light mode (Fresh & Bright)
        colors = {
            "INFO": "#64748b",      # Slate Gray
            "SUCCESS": "#059669",   # Green
            "WARNING": "#d97706",   # Amber/Orange
            "ERROR": "#dc2626"      # Red
        }
        color = colors.get(level, "#334155")
        
        # We need to use tkinter tags for text color in CTkTextbox
        self.console.tag_config(level, foreground=color)
        self.console.insert("end", prefix, "INFO")
        self.console.insert("end", f"[{level}] {msg}\n", level)
        self.console.see("end")
