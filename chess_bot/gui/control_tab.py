import tkinter as tk
from tkinter import ttk
import time
import threading

try:
    from pynput import keyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False


class ControlTab:
    def __init__(self, parent, main_window):
        self.main_window = main_window
        self.frame = ttk.Frame(parent, padding="10")
        
        self.start_time = None
        self.move_count = 0
        self.timer_running = False
        
        self._last_hotkey_time = 0
        self._hotkey_debounce_ms = 300
        
        self._setup_ui()
        self._setup_hotkeys()
        
    def _setup_ui(self):
        control_frame = ttk.LabelFrame(self.frame, text="Bot Control", padding="15")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.start_btn = ttk.Button(
            btn_frame,
            text="Start (F5)",
            command=self._on_start,
            width=15
        )
        self.start_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.pause_btn = ttk.Button(
            btn_frame,
            text="Pause (F6)",
            command=self._on_pause,
            width=15,
            state=tk.DISABLED
        )
        self.pause_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_btn = ttk.Button(
            btn_frame,
            text="Stop (F7)",
            command=self._on_stop,
            width=15,
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT)
        
        settings_frame = ttk.LabelFrame(self.frame, text="Settings", padding="15")
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        speed_frame = ttk.Frame(settings_frame)
        speed_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(speed_frame, text="Move delay (ms):").pack(side=tk.LEFT)
        
        self.speed_var = tk.IntVar(value=self.main_window.config.get("move_delay", 500))
        self.speed_scale = ttk.Scale(
            speed_frame,
            from_=100,
            to=3000,
            variable=self.speed_var,
            orient=tk.HORIZONTAL,
            command=self._on_speed_change
        )
        self.speed_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        
        self.speed_label = ttk.Label(speed_frame, text="500", width=5)
        self.speed_label.pack(side=tk.LEFT)
        
        status_frame = ttk.LabelFrame(self.frame, text="Statistics", padding="15")
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        stats_grid = ttk.Frame(status_frame)
        stats_grid.pack(fill=tk.X)
        
        ttk.Label(stats_grid, text="Status:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.status_value = ttk.Label(stats_grid, text="Stopped", foreground="red")
        self.status_value.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        ttk.Label(stats_grid, text="Moves made:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.moves_value = ttk.Label(stats_grid, text="0")
        self.moves_value.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        ttk.Label(stats_grid, text="Running time:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.time_value = ttk.Label(stats_grid, text="00:00:00")
        self.time_value.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
    def _on_start(self):
        if self.main_window.start_bot():
            self.start_btn.config(state=tk.DISABLED)
            self.pause_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.NORMAL)
            self.status_value.config(text="Running", foreground="green")
            
            self.start_time = time.time()
            self.move_count = 0
            self.timer_running = True
            self._update_timer()
            
    def _on_pause(self):
        self.main_window.pause_bot()
        
        if self.main_window.bot_paused:
            self.pause_btn.config(text="Resume (F6)")
            self.status_value.config(text="Paused", foreground="orange")
        else:
            self.pause_btn.config(text="Pause (F6)")
            self.status_value.config(text="Running", foreground="green")
            
    def _on_stop(self):
        self.main_window.stop_bot()
        
        self.start_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.DISABLED, text="Pause (F6)")
        self.stop_btn.config(state=tk.DISABLED)
        self.status_value.config(text="Stopped", foreground="red")
        
        self.timer_running = False
        
    def _on_speed_change(self, value):
        int_value = int(float(value))
        self.speed_label.config(text=str(int_value))
        self.main_window.config["move_delay"] = int_value
        
    def _update_timer(self):
        if not self.timer_running:
            return
            
        if self.start_time and not self.main_window.bot_paused:
            elapsed = int(time.time() - self.start_time)
            hours = elapsed // 3600
            minutes = (elapsed % 3600) // 60
            seconds = elapsed % 60
            self.time_value.config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            
        self.frame.after(1000, self._update_timer)
        
    def update_move_count(self, count):
        self.move_count = count
        self.moves_value.config(text=str(count))
        
    def _setup_hotkeys(self):
        if PYNPUT_AVAILABLE:
            self._setup_global_hotkeys()
        else:
            self.main_window.log("pynput not installed - global hotkeys disabled")
            root = self.main_window.root
            root.bind("<F5>", self._hotkey_start)
            root.bind("<F6>", self._hotkey_pause)
            root.bind("<F7>", self._hotkey_stop)
            
    def _setup_global_hotkeys(self):
        self.hotkey_listener = None
        
        def on_press(key):
            try:
                current_time = time.time() * 1000
                if current_time - self._last_hotkey_time < self._hotkey_debounce_ms:
                    return
                self._last_hotkey_time = current_time
                
                if key == keyboard.Key.f5:
                    self.main_window.root.after(0, self._hotkey_start)
                elif key == keyboard.Key.f6:
                    self.main_window.root.after(0, self._hotkey_pause)
                elif key == keyboard.Key.f7:
                    self.main_window.root.after(0, self._hotkey_stop)
            except Exception:
                pass
                
        self.hotkey_listener = keyboard.Listener(on_press=on_press)
        self.hotkey_listener.daemon = True
        self.hotkey_listener.start()
        
    def stop_hotkey_listener(self):
        if hasattr(self, 'hotkey_listener') and self.hotkey_listener:
            self.hotkey_listener.stop()
        
    def _hotkey_start(self, event=None):
        if str(self.start_btn["state"]) != "disabled":
            self._on_start()
            
    def _hotkey_pause(self, event=None):
        if str(self.pause_btn["state"]) != "disabled":
            self._on_pause()
            
    def _hotkey_stop(self, event=None):
        if str(self.stop_btn["state"]) != "disabled":
            self._on_stop()
