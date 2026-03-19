import tkinter as tk
from tkinter import ttk
from datetime import datetime


class LogTab:
    def __init__(self, parent, main_window):
        self.main_window = main_window
        self.frame = ttk.Frame(parent, padding="10")

        self._setup_ui()

    def _setup_ui(self):
        log_frame = ttk.LabelFrame(self.frame, text="Nhật ký hoạt động", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)

        text_frame = ttk.Frame(log_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(
            text_frame,
            wrap=tk.WORD,
            font=("Consolas", 10),
            state=tk.DISABLED,
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="white"
        )
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)

        self.log_text.tag_configure("timestamp", foreground="#6a9955")
        self.log_text.tag_configure("info", foreground="#d4d4d4")
        self.log_text.tag_configure("warning", foreground="#dcdcaa")
        self.log_text.tag_configure("error", foreground="#f14c4c")
        self.log_text.tag_configure("success", foreground="#4ec9b0")

        btn_frame = ttk.Frame(log_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        self.clear_btn = ttk.Button(
            btn_frame,
            text="Xóa nhật ký",
            command=self._clear_log
        )
        self.clear_btn.pack(side=tk.LEFT)

        self.export_btn = ttk.Button(
            btn_frame,
            text="Xuất nhật ký",
            command=self._export_log
        )
        self.export_btn.pack(side=tk.LEFT, padx=(5, 0))

    def add_log(self, message, level="info"):
        self.log_text.config(state=tk.NORMAL)

        timestamp = datetime.now().strftime("[%H:%M:%S] ")
        self.log_text.insert(tk.END, timestamp, "timestamp")

        tag = level.lower()
        if tag not in ["info", "warning", "error", "success"]:
            tag = "info"

        self.log_text.insert(tk.END, message + "\n", tag)

        self.log_text.see(tk.END)

        self.log_text.config(state=tk.DISABLED)

    def _clear_log(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _export_log(self):
        from tkinter import filedialog

        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfilename=f"animal_chess_bot_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )

        if filename:
            try:
                content = self.log_text.get(1.0, tk.END)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.add_log(f"Đã xuất nhật ký ra {filename}", "success")
            except Exception as e:
                self.add_log(f"Xuất thất bại: {str(e)}", "error")
