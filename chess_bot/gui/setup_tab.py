import tkinter as tk
from tkinter import ttk, colorchooser, filedialog, messagebox
from PIL import Image, ImageTk
import pyautogui
import os


class SetupTab:
    def __init__(self, parent, main_window):
        self.main_window = main_window
        self.frame = ttk.Frame(parent, padding="10")
        
        self.region_preview_image = None
        self.light_color = main_window.config.get("light_cell_color")
        self.dark_color = main_window.config.get("dark_cell_color")
        
        self._setup_ui()
        self._load_existing_config()
        
    def _setup_ui(self):
        left_frame = ttk.Frame(self.frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        right_frame = ttk.Frame(self.frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        region_frame = ttk.LabelFrame(left_frame, text="Game Region", padding="10")
        region_frame.pack(fill=tk.X, pady=(0, 10))
        
        btn_frame = ttk.Frame(region_frame)
        btn_frame.pack(fill=tk.X)
        
        self.select_region_btn = ttk.Button(
            btn_frame, 
            text="Select Game Region",
            command=self._select_region
        )
        self.select_region_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.region_label = ttk.Label(region_frame, text="No region selected")
        self.region_label.pack(fill=tk.X, pady=(5, 0))
        
        color_frame = ttk.LabelFrame(left_frame, text="Cell Colors", padding="10")
        color_frame.pack(fill=tk.X, pady=(0, 10))
        
        light_frame = ttk.Frame(color_frame)
        light_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(light_frame, text="Light cell:").pack(side=tk.LEFT)
        self.light_color_btn = ttk.Button(
            light_frame,
            text="Pick Color",
            command=lambda: self._pick_color("light")
        )
        self.light_color_btn.pack(side=tk.LEFT, padx=5)
        
        self.light_color_preview = tk.Canvas(light_frame, width=30, height=20, bg="white")
        self.light_color_preview.pack(side=tk.LEFT)
        
        dark_frame = ttk.Frame(color_frame)
        dark_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(dark_frame, text="Dark cell:").pack(side=tk.LEFT)
        self.dark_color_btn = ttk.Button(
            dark_frame,
            text="Pick Color",
            command=lambda: self._pick_color("dark")
        )
        self.dark_color_btn.pack(side=tk.LEFT, padx=5)
        
        self.dark_color_preview = tk.Canvas(dark_frame, width=30, height=20, bg="gray")
        self.dark_color_preview.pack(side=tk.LEFT)
        
        tolerance_frame = ttk.Frame(color_frame)
        tolerance_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(tolerance_frame, text="Color tolerance:").pack(side=tk.LEFT)
        self.tolerance_var = tk.IntVar(value=self.main_window.config.get("color_tolerance", 30))
        self.tolerance_scale = ttk.Scale(
            tolerance_frame,
            from_=5,
            to=100,
            variable=self.tolerance_var,
            orient=tk.HORIZONTAL,
            command=self._on_tolerance_change
        )
        self.tolerance_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.tolerance_label = ttk.Label(tolerance_frame, text="30")
        self.tolerance_label.pack(side=tk.LEFT)
        
        revive_frame = ttk.LabelFrame(left_frame, text="Revive Button", padding="10")
        revive_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.select_revive_btn = ttk.Button(
            revive_frame,
            text="Select Revive Button Position",
            command=self._select_revive_position
        )
        self.select_revive_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.revive_label = ttk.Label(revive_frame, text="Not set")
        self.revive_label.pack(side=tk.LEFT)
        
        save_frame = ttk.Frame(left_frame)
        save_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.save_btn = ttk.Button(
            save_frame,
            text="Save Configuration",
            command=self._save_config
        )
        self.save_btn.pack(side=tk.LEFT)
        
        preview_frame = ttk.LabelFrame(right_frame, text="Preview", padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=True)
        
        self.preview_canvas = tk.Canvas(preview_frame, bg="gray", width=300, height=300)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)
        
    def _load_existing_config(self):
        config = self.main_window.config
        
        if config.get("game_region"):
            region = config["game_region"]
            self.region_label.config(
                text=f"Region: ({region[0]}, {region[1]}) to ({region[2]}, {region[3]})"
            )
            
        if config.get("light_cell_color"):
            color = config["light_cell_color"]
            self.light_color = color
            hex_color = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
            self.light_color_preview.config(bg=hex_color)
            
        if config.get("dark_cell_color"):
            color = config["dark_cell_color"]
            self.dark_color = color
            hex_color = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
            self.dark_color_preview.config(bg=hex_color)
            
        if config.get("revive_button_pos"):
            pos = config["revive_button_pos"]
            self.revive_label.config(text=f"Position: ({pos[0]}, {pos[1]})")
            
    def _select_region(self):
        self.main_window.root.iconify()
        self.main_window.root.after(300, self._start_region_selection)
        
    def _start_region_selection(self):
        from .region_selector import RegionSelector
        selector = RegionSelector(self._on_region_selected)
        
    def _on_region_selected(self, x1, y1, x2, y2):
        self.main_window.root.deiconify()
        
        x1, x2 = min(x1, x2), max(x1, x2)
        y1, y2 = min(y1, y2), max(y1, y2)
        
        self.main_window.config["game_region"] = [x1, y1, x2, y2]
        self.region_label.config(text=f"Region: ({x1}, {y1}) to ({x2}, {y2})")
        
        self._update_preview()
        self.main_window.log(f"Game region selected: ({x1}, {y1}) to ({x2}, {y2})")
        
    def _pick_color(self, color_type):
        self.main_window.root.iconify()
        self.main_window.root.after(300, lambda: self._start_color_pick(color_type))
        
    def _start_color_pick(self, color_type):
        from .color_picker import ColorPicker
        picker = ColorPicker(lambda color: self._on_color_picked(color_type, color))
        
    def _on_color_picked(self, color_type, color):
        self.main_window.root.deiconify()
        
        if color is None:
            return
            
        hex_color = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
        
        if color_type == "light":
            self.light_color = color
            self.main_window.config["light_cell_color"] = list(color)
            self.light_color_preview.config(bg=hex_color)
            self.main_window.log(f"Light cell color: RGB{color}")
        else:
            self.dark_color = color
            self.main_window.config["dark_cell_color"] = list(color)
            self.dark_color_preview.config(bg=hex_color)
            self.main_window.log(f"Dark cell color: RGB{color}")
            
    def _on_tolerance_change(self, value):
        int_value = int(float(value))
        self.tolerance_label.config(text=str(int_value))
        self.main_window.config["color_tolerance"] = int_value
        
    def _select_revive_position(self):
        self.main_window.root.iconify()
        self.main_window.root.after(300, self._start_revive_selection)
        
    def _start_revive_selection(self):
        from .color_picker import ColorPicker
        picker = ColorPicker(self._on_revive_selected, pick_position_only=True)
        
    def _on_revive_selected(self, pos):
        self.main_window.root.deiconify()
        
        if pos is None:
            return
            
        self.main_window.config["revive_button_pos"] = list(pos)
        self.revive_label.config(text=f"Position: ({pos[0]}, {pos[1]})")
        self.main_window.log(f"Revive button position: ({pos[0]}, {pos[1]})")
        
    def _update_preview(self):
        region = self.main_window.config.get("game_region")
        if not region:
            return
            
        try:
            screenshot = pyautogui.screenshot(region=(
                region[0], region[1],
                region[2] - region[0],
                region[3] - region[1]
            ))
            
            canvas_width = self.preview_canvas.winfo_width()
            canvas_height = self.preview_canvas.winfo_height()
            
            if canvas_width < 10:
                canvas_width = 300
            if canvas_height < 10:
                canvas_height = 300
                
            img_ratio = screenshot.width / screenshot.height
            canvas_ratio = canvas_width / canvas_height
            
            if img_ratio > canvas_ratio:
                new_width = canvas_width
                new_height = int(canvas_width / img_ratio)
            else:
                new_height = canvas_height
                new_width = int(canvas_height * img_ratio)
                
            screenshot = screenshot.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            self.region_preview_image = ImageTk.PhotoImage(screenshot)
            
            self.preview_canvas.delete("all")
            self.preview_canvas.create_image(
                canvas_width // 2,
                canvas_height // 2,
                image=self.region_preview_image,
                anchor=tk.CENTER
            )
        except Exception as e:
            self.main_window.log(f"Preview error: {str(e)}")
            
    def _save_config(self):
        self.main_window.save_current_config()
        messagebox.showinfo("Success", "Configuration saved successfully!")
