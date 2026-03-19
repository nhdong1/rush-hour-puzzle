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
        self.cell_color = main_window.config.get("cell_color")

        self._setup_ui()
        self._load_existing_config()

    def _setup_ui(self):
        left_frame = ttk.Frame(self.frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        right_frame = ttk.Frame(self.frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        region_frame = ttk.LabelFrame(left_frame, text="Vùng chơi", padding="10")
        region_frame.pack(fill=tk.X, pady=(0, 10))

        btn_frame = ttk.Frame(region_frame)
        btn_frame.pack(fill=tk.X)

        self.select_region_btn = ttk.Button(
            btn_frame,
            text="Chọn vùng chơi",
            command=self._select_region
        )
        self.select_region_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.region_label = ttk.Label(region_frame, text="Chưa chọn vùng")
        self.region_label.pack(fill=tk.X, pady=(5, 0))

        color_frame = ttk.LabelFrame(left_frame, text="Màu ô cờ", padding="10")
        color_frame.pack(fill=tk.X, pady=(0, 10))

        cell_frame = ttk.Frame(color_frame)
        cell_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(cell_frame, text="Màu ô:").pack(side=tk.LEFT)
        self.cell_color_btn = ttk.Button(
            cell_frame,
            text="Chọn màu",
            command=self._pick_cell_color
        )
        self.cell_color_btn.pack(side=tk.LEFT, padx=5)

        self.cell_color_preview = tk.Canvas(cell_frame, width=30, height=20, bg="white")
        self.cell_color_preview.pack(side=tk.LEFT)

        tolerance_frame = ttk.Frame(color_frame)
        tolerance_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Label(tolerance_frame, text="Dung sai màu:").pack(side=tk.LEFT)
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

        gap_frame = ttk.LabelFrame(left_frame, text="Chỉnh khoảng cách giữa các ô", padding="10")
        gap_frame.pack(fill=tk.X, pady=(0, 10))

        gap_control_frame = ttk.Frame(gap_frame)
        gap_control_frame.pack(fill=tk.X)

        self.gap_auto_var = tk.BooleanVar(value=self.main_window.config.get("cell_gap") is None)
        self.gap_auto_checkbox = ttk.Checkbutton(
            gap_control_frame,
            text="Tự động",
            variable=self.gap_auto_var,
            command=self._on_gap_auto_changed
        )
        self.gap_auto_checkbox.pack(side=tk.LEFT)

        ttk.Label(gap_control_frame, text="Gap (px):").pack(side=tk.LEFT, padx=(10, 5))

        current_gap = self.main_window.config.get("cell_gap")
        self.gap_var = tk.IntVar(value=current_gap if current_gap is not None else 10)
        self.gap_spinbox = ttk.Spinbox(
            gap_control_frame,
            from_=0,
            to=100,
            width=6,
            textvariable=self.gap_var,
            command=self._on_gap_change
        )
        self.gap_spinbox.pack(side=tk.LEFT)
        self.gap_spinbox.bind('<Return>', lambda e: self._on_gap_change())
        self.gap_spinbox.bind('<FocusOut>', lambda e: self._on_gap_change())

        if self.gap_auto_var.get():
            self.gap_spinbox.config(state='disabled')

        template_frame = ttk.LabelFrame(left_frame, text="Quản lý Template", padding="10")
        template_frame.pack(fill=tk.X, pady=(0, 10))

        template_btn_frame = ttk.Frame(template_frame)
        template_btn_frame.pack(fill=tk.X, pady=(0, 5))

        self.capture_template_btn = ttk.Button(
            template_btn_frame,
            text="📷 Chụp Template",
            command=self._open_template_capture
        )
        self.capture_template_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.refresh_templates_btn = ttk.Button(
            template_btn_frame,
            text="🔄 Làm mới",
            command=self._refresh_template_list,
            width=10
        )
        self.refresh_templates_btn.pack(side=tk.LEFT)

        self.template_listbox = tk.Listbox(template_frame, height=6, width=35)
        self.template_listbox.pack(fill=tk.X, pady=(5, 5))

        template_action_frame = ttk.Frame(template_frame)
        template_action_frame.pack(fill=tk.X)

        self.delete_template_btn = ttk.Button(
            template_action_frame,
            text="🗑️ Xóa đã chọn",
            command=self._delete_selected_template
        )
        self.delete_template_btn.pack(side=tk.LEFT)

        self.template_count_label = ttk.Label(template_action_frame, text="", foreground="gray")
        self.template_count_label.pack(side=tk.RIGHT)

        conditions_frame = ttk.LabelFrame(left_frame, text="Điều kiện Auto Click", padding="10")
        conditions_frame.pack(fill=tk.X, pady=(0, 10))

        conditions_btn_frame = ttk.Frame(conditions_frame)
        conditions_btn_frame.pack(fill=tk.X, pady=(0, 5))

        self.add_condition_btn = ttk.Button(
            conditions_btn_frame,
            text="➕ Thêm điều kiện",
            command=self._add_condition
        )
        self.add_condition_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.edit_condition_btn = ttk.Button(
            conditions_btn_frame,
            text="✏️ Sửa",
            command=self._edit_condition,
            width=8
        )
        self.edit_condition_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.delete_condition_btn = ttk.Button(
            conditions_btn_frame,
            text="🗑️ Xóa",
            command=self._delete_condition,
            width=8
        )
        self.delete_condition_btn.pack(side=tk.LEFT)

        self.conditions_listbox = tk.Listbox(conditions_frame, height=5, width=35, font=("Consolas", 9))
        self.conditions_listbox.pack(fill=tk.X, pady=(5, 5))

        conditions_info_frame = ttk.Frame(conditions_frame)
        conditions_info_frame.pack(fill=tk.X)

        self.conditions_count_label = ttk.Label(conditions_info_frame, text="0 điều kiện", foreground="gray")
        self.conditions_count_label.pack(side=tk.LEFT)

        self.toggle_condition_btn = ttk.Button(
            conditions_info_frame,
            text="🔄 Bật/Tắt",
            command=self._toggle_condition,
            width=10
        )
        self.toggle_condition_btn.pack(side=tk.RIGHT)

        self.virtual_mode_var = tk.BooleanVar(value=True)
        self.virtual_mode_checkbox = ttk.Checkbutton(
            conditions_frame,
            text="Bật/tắt chế độ không chiếm chuột",
            variable=self.virtual_mode_var,
            command=self._on_virtual_mode_changed
        )
        self.virtual_mode_checkbox.pack(anchor=tk.W, pady=(5, 0))

        save_frame = ttk.Frame(left_frame)
        save_frame.pack(fill=tk.X, pady=(10, 0))

        self.save_btn = ttk.Button(
            save_frame,
            text="Lưu cấu hình",
            command=self._save_config
        )
        self.save_btn.pack(side=tk.LEFT)

        preview_frame = ttk.LabelFrame(right_frame, text="Xem trước", padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=True)

        self.preview_canvas = tk.Canvas(preview_frame, bg="gray", width=300, height=300)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)

    def _load_existing_config(self):
        config = self.main_window.config

        if config.get("game_region"):
            region = config["game_region"]
            self.region_label.config(
                text=f"Vùng: ({region[0]}, {region[1]}) đến ({region[2]}, {region[3]})"
            )

        if config.get("cell_color"):
            color = config["cell_color"]
            self.cell_color = color
            hex_color = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
            self.cell_color_preview.config(bg=hex_color)

        cell_gap = config.get("cell_gap")
        if cell_gap is not None:
            self.gap_auto_var.set(False)
            self.gap_var.set(cell_gap)
            self.gap_spinbox.config(state='normal')
        else:
            self.gap_auto_var.set(True)
            self.gap_spinbox.config(state='disabled')

        self._refresh_template_list()
        self._refresh_conditions_list()

        virtual_mode = config.get("virtual_click_mode", True)
        self.virtual_mode_var.set(virtual_mode)

    def _on_virtual_mode_changed(self):
        self.main_window.config["virtual_click_mode"] = self.virtual_mode_var.get()
        mode_text = "bật" if self.virtual_mode_var.get() else "tắt"
        self.main_window.log(f"Chế độ không chiếm chuột: {mode_text}")

    def _select_region(self):
        self.main_window.root.iconify()
        self.main_window.root.after(300, self._start_region_selection)

    def _start_region_selection(self):
        from .region_selector import RegionSelector
        selector = RegionSelector(self._on_region_selected)

    def _on_region_selected(self, x1, y1, x2, y2):
        self.main_window.root.deiconify()

        if x1 is None:
            return

        x1, x2 = min(x1, x2), max(x1, x2)
        y1, y2 = min(y1, y2), max(y1, y2)

        self.main_window.config["game_region"] = [x1, y1, x2, y2]
        self.region_label.config(text=f"Vùng: ({x1}, {y1}) đến ({x2}, {y2})")

        self._update_preview()
        self.main_window.log(f"Đã chọn vùng chơi: ({x1}, {y1}) đến ({x2}, {y2})")

    def _pick_cell_color(self):
        self.main_window.root.iconify()
        self.main_window.root.after(300, self._start_color_pick)

    def _start_color_pick(self):
        from .color_picker import ColorPicker
        picker = ColorPicker(self._on_cell_color_picked)

    def _on_cell_color_picked(self, color):
        self.main_window.root.deiconify()

        if color is None:
            return

        hex_color = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"

        self.cell_color = color
        self.main_window.config["cell_color"] = list(color)
        self.cell_color_preview.config(bg=hex_color)
        self.main_window.log(f"Màu ô: RGB{color}")

    def _on_tolerance_change(self, value):
        int_value = int(float(value))
        self.tolerance_label.config(text=str(int_value))
        self.main_window.config["color_tolerance"] = int_value

    def _on_gap_auto_changed(self):
        if self.gap_auto_var.get():
            self.gap_spinbox.config(state='disabled')
            self.main_window.config["cell_gap"] = None
            self.main_window.log("Khoảng cách ô: Tự động")
        else:
            self.gap_spinbox.config(state='normal')
            gap_value = self.gap_var.get()
            self.main_window.config["cell_gap"] = gap_value
            self.main_window.log(f"Khoảng cách ô: {gap_value}px")

    def _on_gap_change(self):
        if not self.gap_auto_var.get():
            try:
                gap_value = self.gap_var.get()
                self.main_window.config["cell_gap"] = gap_value
                self.main_window.log(f"Khoảng cách ô: {gap_value}px")
            except tk.TclError:
                pass

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
            self.main_window.log(f"Lỗi xem trước: {str(e)}")

    def _save_config(self):
        self.main_window.save_current_config()
        messagebox.showinfo("Thành công", "Cấu hình đã được lưu!")

    def _open_template_capture(self):
        from .template_capture import TemplateCaptureDialog
        templates_path = get_templates_path()
        TemplateCaptureDialog(
            self.main_window.root,
            templates_path,
            callback=self._on_template_saved
        )

    def _on_template_saved(self, template_name):
        self._refresh_template_list()
        self.main_window.log(f"Đã lưu template: {template_name}")

    def _refresh_template_list(self):
        self.template_listbox.delete(0, tk.END)

        templates_path = get_templates_path()
        if not os.path.exists(templates_path):
            self.template_count_label.config(text="0 template")
            return

        templates = []
        for filename in os.listdir(templates_path):
            if filename.endswith(('.png', '.jpg', '.jpeg')):
                name = os.path.splitext(filename)[0]
                templates.append(name)

        templates.sort()
        for name in templates:
            self.template_listbox.insert(tk.END, name)

        self.template_count_label.config(text=f"{len(templates)} template")

    def _delete_selected_template(self):
        selection = self.template_listbox.curselection()
        if not selection:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn template để xóa")
            return

        template_name = self.template_listbox.get(selection[0])

        if not messagebox.askyesno("Xác nhận xóa",
                                    f"Xóa template '{template_name}'?"):
            return

        templates_path = get_templates_path()

        for ext in ['.png', '.jpg', '.jpeg']:
            filepath = os.path.join(templates_path, f"{template_name}{ext}")
            if os.path.exists(filepath):
                os.remove(filepath)
                self.main_window.log(f"Đã xóa template: {template_name}")
                break

        self._refresh_template_list()

    def _refresh_conditions_list(self):
        self.conditions_listbox.delete(0, tk.END)

        conditions = self.main_window.config.get("auto_click_conditions", [])

        for cond in conditions:
            name = cond.get("name", "Unknown")
            template = cond.get("template_name", "")
            enabled = cond.get("enabled", True)
            clicks = len(cond.get("click_sequence", []))

            status = "✓" if enabled else "✗"
            display = f"{status} {name} [{template}] - {clicks} clicks"
            self.conditions_listbox.insert(tk.END, display)

        self.conditions_count_label.config(text=f"{len(conditions)} điều kiện")

    def _add_condition(self):
        from .condition_editor import ConditionEditorDialog

        ConditionEditorDialog(
            self.main_window.root,
            callback=self._on_condition_added
        )

    def _on_condition_added(self, condition):
        if "auto_click_conditions" not in self.main_window.config:
            self.main_window.config["auto_click_conditions"] = []

        self.main_window.config["auto_click_conditions"].append(condition)
        self._refresh_conditions_list()
        self.main_window.log(f"Đã thêm điều kiện: {condition['name']}")

    def _edit_condition(self):
        selection = self.conditions_listbox.curselection()
        if not selection:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn điều kiện để sửa")
            return

        idx = selection[0]
        conditions = self.main_window.config.get("auto_click_conditions", [])

        if idx >= len(conditions):
            return

        condition = conditions[idx]

        from .condition_editor import ConditionEditorDialog

        ConditionEditorDialog(
            self.main_window.root,
            condition=condition.copy(),
            callback=lambda c: self._on_condition_edited(idx, c)
        )

    def _on_condition_edited(self, idx, condition):
        conditions = self.main_window.config.get("auto_click_conditions", [])

        if idx < len(conditions):
            conditions[idx] = condition
            self._refresh_conditions_list()
            self.main_window.log(f"Đã cập nhật điều kiện: {condition['name']}")

    def _delete_condition(self):
        selection = self.conditions_listbox.curselection()
        if not selection:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn điều kiện để xóa")
            return

        idx = selection[0]
        conditions = self.main_window.config.get("auto_click_conditions", [])

        if idx >= len(conditions):
            return

        cond_name = conditions[idx].get("name", "Unknown")

        if not messagebox.askyesno("Xác nhận xóa", f"Xóa điều kiện '{cond_name}'?"):
            return

        del conditions[idx]
        self._refresh_conditions_list()
        self.main_window.log(f"Đã xóa điều kiện: {cond_name}")

    def _toggle_condition(self):
        selection = self.conditions_listbox.curselection()
        if not selection:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn điều kiện để bật/tắt")
            return

        idx = selection[0]
        conditions = self.main_window.config.get("auto_click_conditions", [])

        if idx >= len(conditions):
            return

        conditions[idx]["enabled"] = not conditions[idx].get("enabled", True)
        status = "bật" if conditions[idx]["enabled"] else "tắt"
        self._refresh_conditions_list()
        self.main_window.log(f"Điều kiện '{conditions[idx]['name']}' đã {status}")
