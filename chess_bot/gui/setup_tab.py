import tkinter as tk
from tkinter import ttk, colorchooser, filedialog, messagebox
from PIL import Image, ImageTk
import pyautogui
import os

from config import get_templates_path


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

        # Template Management section
        template_frame = ttk.LabelFrame(left_frame, text="Template Management", padding="10")
        template_frame.pack(fill=tk.X, pady=(0, 10))

        template_btn_frame = ttk.Frame(template_frame)
        template_btn_frame.pack(fill=tk.X, pady=(0, 5))

        self.capture_template_btn = ttk.Button(
            template_btn_frame,
            text="📷 Capture Template",
            command=self._open_template_capture
        )
        self.capture_template_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.refresh_templates_btn = ttk.Button(
            template_btn_frame,
            text="🔄 Refresh",
            command=self._refresh_template_list,
            width=10
        )
        self.refresh_templates_btn.pack(side=tk.LEFT)

        # Template list
        self.template_listbox = tk.Listbox(template_frame, height=6, width=35)
        self.template_listbox.pack(fill=tk.X, pady=(5, 5))

        template_action_frame = ttk.Frame(template_frame)
        template_action_frame.pack(fill=tk.X)

        self.delete_template_btn = ttk.Button(
            template_action_frame,
            text="🗑️ Delete Selected",
            command=self._delete_selected_template
        )
        self.delete_template_btn.pack(side=tk.LEFT)

        self.template_count_label = ttk.Label(template_action_frame, text="", foreground="gray")
        self.template_count_label.pack(side=tk.RIGHT)

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

        # Load template list
        self._refresh_template_list()


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

    def _open_template_capture(self):
        """Open template capture dialog"""
        from .template_capture import TemplateCaptureDialog
        templates_path = get_templates_path()
        TemplateCaptureDialog(
            self.main_window.root,
            templates_path,
            callback=self._on_template_saved
        )

    def _on_template_saved(self, template_name):
        """Callback when template is saved"""
        self._refresh_template_list()
        self.main_window.log(f"Template saved: {template_name}")

    def _refresh_template_list(self):
        """Refresh the template listbox"""
        self.template_listbox.delete(0, tk.END)

        templates_path = get_templates_path()
        if not os.path.exists(templates_path):
            self.template_count_label.config(text="0 templates")
            return

        templates = []
        for filename in os.listdir(templates_path):
            if filename.endswith(('.png', '.jpg', '.jpeg')):
                name = os.path.splitext(filename)[0]
                templates.append(name)

        templates.sort()
        for name in templates:
            self.template_listbox.insert(tk.END, name)

        self.template_count_label.config(text=f"{len(templates)} templates")

    def _delete_selected_template(self):
        """Delete selected template from list"""
        selection = self.template_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a template to delete")
            return

        template_name = self.template_listbox.get(selection[0])

        if not messagebox.askyesno("Confirm Delete",
                                    f"Delete template '{template_name}'?"):
            return

        templates_path = get_templates_path()

        # Try different extensions
        for ext in ['.png', '.jpg', '.jpeg']:
            filepath = os.path.join(templates_path, f"{template_name}{ext}")
            if os.path.exists(filepath):
                os.remove(filepath)
                self.main_window.log(f"Template deleted: {template_name}")
                break

        self._refresh_template_list()
