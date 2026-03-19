import tkinter as tk
from tkinter import ttk, messagebox
from PIL import ImageGrab, ImageTk, Image
import cv2
import numpy as np
import os

from config import get_templates_path


class ConditionEditorDialog:
    """
    Dialog to create/edit auto-click conditions.
    Each condition has:
    - name: Display name
    - template_name: Template to detect (trigger)
    - enabled: Whether condition is active
    - cooldown_ms: Cooldown before re-triggering (ms)
    - click_sequence: List of {x, y, delay_ms} positions to click in order
    """

    def __init__(self, parent, condition=None, callback=None):
        self.parent = parent
        self.callback = callback
        self.condition = condition or {
            "name": "",
            "template_name": "",
            "enabled": True,
            "cooldown_ms": 1000,
            "click_sequence": []
        }
        self.click_sequence = list(self.condition.get("click_sequence", []))
        self.result = None

        self.captured_image = None
        self.preview_image = None

        self._create_dialog()

    def _create_dialog(self):
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Sửa điều kiện" if self.condition.get("name") else "Thêm điều kiện")
        self.dialog.geometry("550x650")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        name_frame = ttk.Frame(main_frame)
        name_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(name_frame, text="Tên điều kiện:").pack(side=tk.LEFT)
        self.name_var = tk.StringVar(value=self.condition.get("name", ""))
        self.name_entry = ttk.Entry(name_frame, textvariable=self.name_var, width=30)
        self.name_entry.pack(side=tk.LEFT, padx=(10, 0), fill=tk.X, expand=True)

        template_frame = ttk.LabelFrame(main_frame, text="Template Trigger", padding="10")
        template_frame.pack(fill=tk.X, pady=(0, 10))

        template_btn_frame = ttk.Frame(template_frame)
        template_btn_frame.pack(fill=tk.X, pady=(0, 5))

        self.capture_btn = ttk.Button(
            template_btn_frame,
            text="📷 Chụp Template",
            command=self._start_template_capture
        )
        self.capture_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.template_status = ttk.Label(template_btn_frame, text="Chưa có template", foreground="gray")
        self.template_status.pack(side=tk.LEFT)

        self.template_canvas = tk.Canvas(template_frame, bg="gray", width=150, height=80)
        self.template_canvas.pack(fill=tk.X, pady=(5, 0))

        if self.condition.get("template_name"):
            self._load_existing_template(self.condition["template_name"])

        enabled_frame = ttk.Frame(main_frame)
        enabled_frame.pack(fill=tk.X, pady=(0, 10))

        self.enabled_var = tk.BooleanVar(value=self.condition.get("enabled", True))
        ttk.Checkbutton(enabled_frame, text="Bật điều kiện", variable=self.enabled_var).pack(side=tk.LEFT)

        cooldown_frame = ttk.Frame(main_frame)
        cooldown_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(cooldown_frame, text="Cooldown (ms):").pack(side=tk.LEFT)
        self.cooldown_var = tk.IntVar(value=self.condition.get("cooldown_ms", 1000))
        self.cooldown_spin = ttk.Spinbox(
            cooldown_frame,
            from_=0,
            to=60000,
            textvariable=self.cooldown_var,
            width=10
        )
        self.cooldown_spin.pack(side=tk.LEFT, padx=(10, 0))

        sequence_frame = ttk.LabelFrame(main_frame, text="Chuỗi click", padding="10")
        sequence_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        list_frame = ttk.Frame(sequence_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self.sequence_listbox = tk.Listbox(list_frame, height=8, font=("Consolas", 10))
        self.sequence_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.sequence_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.sequence_listbox.config(yscrollcommand=scrollbar.set)

        self._refresh_sequence_list()

        seq_btn_frame = ttk.Frame(sequence_frame)
        seq_btn_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(seq_btn_frame, text="➕ Thêm vị trí", command=self._add_position).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(seq_btn_frame, text="✏️ Sửa", command=self._edit_position).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(seq_btn_frame, text="🗑️ Xóa", command=self._delete_position).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(seq_btn_frame, text="⬆️", command=lambda: self._move_position(-1), width=3).pack(side=tk.LEFT, padx=(0, 2))
        ttk.Button(seq_btn_frame, text="⬇️", command=lambda: self._move_position(1), width=3).pack(side=tk.LEFT)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X)

        ttk.Button(btn_frame, text="Lưu", command=self._save, width=10).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Hủy", command=self._cancel, width=10).pack(side=tk.LEFT)

        self.dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() - self.dialog.winfo_width()) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")

        self.dialog.wait_window()

    def _load_existing_template(self, template_name):
        templates_path = get_templates_path()

        for ext in ['.png', '.jpg', '.jpeg']:
            filepath = os.path.join(templates_path, f"{template_name}{ext}")
            if os.path.exists(filepath):
                try:
                    img = Image.open(filepath)
                    self.captured_image = img
                    self._update_template_preview(img)
                    self.template_status.config(text=f"Template: {template_name}", foreground="green")
                except Exception:
                    pass
                break

    def _start_template_capture(self):
        self.dialog.grab_release()
        self.dialog.withdraw()
        self.dialog.after(300, self._open_capture_overlay)

    def _open_capture_overlay(self):
        TemplateCaptureOverlay(self._on_template_captured)

    def _on_template_captured(self, image, region):
        try:
            if not self.dialog.winfo_exists():
                return
            self.dialog.deiconify()
            self.dialog.grab_set()
        except tk.TclError:
            return

        if image is None:
            self.template_status.config(text="Đã hủy", foreground="orange")
            return

        self.captured_image = image
        self._update_template_preview(image)
        self.template_status.config(text=f"Đã chụp: {image.width}x{image.height}px", foreground="green")

    def _update_template_preview(self, image):
        canvas_width = self.template_canvas.winfo_width()
        canvas_height = self.template_canvas.winfo_height()

        if canvas_width < 50:
            canvas_width = 150
        if canvas_height < 50:
            canvas_height = 80

        scale_x = canvas_width / image.width
        scale_y = canvas_height / image.height
        scale = min(scale_x, scale_y, 1.0)

        new_width = max(1, int(image.width * scale))
        new_height = max(1, int(image.height * scale))

        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        self.preview_image = ImageTk.PhotoImage(resized)

        self.template_canvas.delete("all")
        self.template_canvas.create_image(
            canvas_width // 2,
            canvas_height // 2,
            image=self.preview_image,
            anchor=tk.CENTER
        )

    def _refresh_sequence_list(self):
        self.sequence_listbox.delete(0, tk.END)

        for i, pos in enumerate(self.click_sequence):
            x = pos.get("x", 0)
            y = pos.get("y", 0)
            delay = pos.get("delay_ms", 500)
            self.sequence_listbox.insert(tk.END, f"{i+1}. X:{x}, Y:{y} - Delay: {delay}ms")

    def _add_position(self):
        self.dialog.grab_release()
        self.dialog.withdraw()
        self.dialog.after(300, self._open_position_picker)

    def _open_position_picker(self):
        DraggablePositionPicker(self._on_position_added)

    def _on_position_added(self, x, y):
        try:
            if not self.dialog.winfo_exists():
                return
            self.dialog.deiconify()
            self.dialog.grab_set()
        except tk.TclError:
            return

        if x is None or y is None:
            return

        DelayInputDialog(
            self.dialog,
            x=x,
            y=y,
            callback=lambda px, py, d: self._finalize_position_add(px, py, d)
        )

    def _finalize_position_add(self, x, y, delay_ms):
        self.click_sequence.append({"x": x, "y": y, "delay_ms": delay_ms})
        self._refresh_sequence_list()

    def _edit_position(self):
        selection = self.sequence_listbox.curselection()
        if not selection:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn vị trí để sửa")
            return

        idx = selection[0]
        pos = self.click_sequence[idx]

        PositionEditorDialog(
            self.dialog,
            x=pos.get("x", 0),
            y=pos.get("y", 0),
            delay_ms=pos.get("delay_ms", 500),
            callback=lambda x, y, d: self._on_position_edited(idx, x, y, d)
        )

    def _on_position_edited(self, idx, x, y, delay_ms):
        self.click_sequence[idx] = {"x": x, "y": y, "delay_ms": delay_ms}
        self._refresh_sequence_list()

    def _delete_position(self):
        selection = self.sequence_listbox.curselection()
        if not selection:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn vị trí để xóa")
            return

        idx = selection[0]
        del self.click_sequence[idx]
        self._refresh_sequence_list()

    def _move_position(self, direction):
        selection = self.sequence_listbox.curselection()
        if not selection:
            return

        idx = selection[0]
        new_idx = idx + direction

        if 0 <= new_idx < len(self.click_sequence):
            self.click_sequence[idx], self.click_sequence[new_idx] = \
                self.click_sequence[new_idx], self.click_sequence[idx]
            self._refresh_sequence_list()
            self.sequence_listbox.selection_set(new_idx)

    def _save(self):
        name = self.name_var.get().strip()

        if not name:
            messagebox.showerror("Lỗi", "Vui lòng nhập tên điều kiện")
            return

        if self.captured_image is None:
            messagebox.showerror("Lỗi", "Vui lòng chụp template trigger")
            return

        if not self.click_sequence:
            messagebox.showerror("Lỗi", "Vui lòng thêm ít nhất một vị trí click")
            return

        template_name = f"condition_{name.replace(' ', '_').lower()}"
        templates_path = get_templates_path()
        os.makedirs(templates_path, exist_ok=True)

        filepath = os.path.join(templates_path, f"{template_name}.png")
        cv_image = cv2.cvtColor(np.array(self.captured_image), cv2.COLOR_RGB2BGR)
        cv2.imwrite(filepath, cv_image)

        self.result = {
            "name": name,
            "template_name": template_name,
            "enabled": self.enabled_var.get(),
            "cooldown_ms": self.cooldown_var.get(),
            "click_sequence": self.click_sequence
        }

        if self.callback:
            self.callback(self.result)

        self.dialog.destroy()

    def _cancel(self):
        self.dialog.destroy()


class TemplateCaptureOverlay:
    def __init__(self, callback):
        self.callback = callback
        self.start_x = None
        self.start_y = None
        self.rect_id = None

        self.screenshot = ImageGrab.grab()

        self.root = tk.Toplevel()
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)
        self.root.configure(cursor="cross")

        self.screenshot_tk = ImageTk.PhotoImage(self.screenshot)

        self.canvas = tk.Canvas(self.root, highlightthickness=0, cursor="cross")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.create_image(0, 0, image=self.screenshot_tk, anchor=tk.NW)

        self.canvas.create_rectangle(
            0, 0,
            self.root.winfo_screenwidth(),
            self.root.winfo_screenheight(),
            fill="black",
            stipple="gray50",
            outline=""
        )

        self.canvas.create_text(
            self.root.winfo_screenwidth() // 2,
            30,
            text="Kéo để chọn vùng template. Nhấn ESC để hủy.",
            fill="white",
            font=("Arial", 16, "bold")
        )

        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.root.bind("<Escape>", self._on_cancel)

        self.root.focus_force()

    def _on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        self.rect_id = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline="red", width=2
        )

    def _on_drag(self, event):
        if self.rect_id:
            self.canvas.coords(self.rect_id, self.start_x, self.start_y, event.x, event.y)

    def _on_release(self, event):
        end_x, end_y = event.x, event.y
        self.root.destroy()

        if self.start_x is not None and abs(end_x - self.start_x) > 10 and abs(end_y - self.start_y) > 10:
            x1, y1 = min(self.start_x, end_x), min(self.start_y, end_y)
            x2, y2 = max(self.start_x, end_x), max(self.start_y, end_y)
            cropped = self.screenshot.crop((x1, y1, x2, y2))
            self.callback(cropped, (x1, y1, x2, y2))
        else:
            self.callback(None, None)

    def _on_cancel(self, event):
        self.root.destroy()
        self.callback(None, None)


class DraggablePositionPicker:
    def __init__(self, callback):
        self.callback = callback

        self.screenshot = ImageGrab.grab()

        self.root = tk.Toplevel()
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)

        self.screenshot_tk = ImageTk.PhotoImage(self.screenshot)

        self.canvas = tk.Canvas(self.root, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.create_image(0, 0, image=self.screenshot_tk, anchor=tk.NW)

        self.canvas.create_rectangle(
            0, 0,
            self.root.winfo_screenwidth(),
            self.root.winfo_screenheight(),
            fill="black",
            stipple="gray25",
            outline=""
        )

        self.circle_radius = 25
        self.circle_x = self.root.winfo_screenwidth() // 2
        self.circle_y = self.root.winfo_screenheight() // 2

        self.h_line = self.canvas.create_line(
            0, self.circle_y, self.root.winfo_screenwidth(), self.circle_y,
            fill="yellow", width=1, dash=(4, 4)
        )
        self.v_line = self.canvas.create_line(
            self.circle_x, 0, self.circle_x, self.root.winfo_screenheight(),
            fill="yellow", width=1, dash=(4, 4)
        )

        self.circle = self.canvas.create_oval(
            self.circle_x - self.circle_radius,
            self.circle_y - self.circle_radius,
            self.circle_x + self.circle_radius,
            self.circle_y + self.circle_radius,
            outline="red",
            width=3,
            fill=""
        )

        self.center_dot = self.canvas.create_oval(
            self.circle_x - 3, self.circle_y - 3,
            self.circle_x + 3, self.circle_y + 3,
            fill="red", outline="red"
        )

        self.coord_label = self.canvas.create_text(
            self.circle_x,
            self.circle_y - self.circle_radius - 20,
            text=f"X: {self.circle_x}, Y: {self.circle_y}",
            fill="white",
            font=("Arial", 12, "bold")
        )

        self.canvas.create_text(
            self.root.winfo_screenwidth() // 2,
            30,
            text="Kéo hình tròn đến vị trí cần click. Nhấn ENTER để xác nhận, ESC để hủy.",
            fill="white",
            font=("Arial", 16, "bold")
        )

        btn_y = self.root.winfo_screenheight() - 60
        self.canvas.create_rectangle(
            self.root.winfo_screenwidth() // 2 - 60, btn_y - 15,
            self.root.winfo_screenwidth() // 2 + 60, btn_y + 15,
            fill="green", outline="white", width=2,
            tags="confirm_btn"
        )
        self.canvas.create_text(
            self.root.winfo_screenwidth() // 2, btn_y,
            text="✓ Xác nhận",
            fill="white",
            font=("Arial", 12, "bold"),
            tags="confirm_btn"
        )

        self.canvas.tag_bind(self.circle, "<ButtonPress-1>", self._on_circle_press)
        self.canvas.tag_bind(self.center_dot, "<ButtonPress-1>", self._on_circle_press)
        self.canvas.tag_bind("confirm_btn", "<Button-1>", self._on_confirm)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.root.bind("<Return>", self._on_confirm)
        self.root.bind("<Escape>", self._on_cancel)

        self.dragging = False

        self.root.focus_force()

    def _on_circle_press(self, event):
        self.dragging = True

    def _on_canvas_click(self, event):
        items = self.canvas.find_withtag("confirm_btn")
        for item in items:
            coords = self.canvas.bbox(item)
            if coords and coords[0] <= event.x <= coords[2] and coords[1] <= event.y <= coords[3]:
                return

        self._move_circle_to(event.x, event.y)

    def _on_drag(self, event):
        if self.dragging:
            self._move_circle_to(event.x, event.y)

    def _on_release(self, event):
        self.dragging = False

    def _move_circle_to(self, x, y):
        self.circle_x = x
        self.circle_y = y

        self.canvas.coords(
            self.circle,
            x - self.circle_radius, y - self.circle_radius,
            x + self.circle_radius, y + self.circle_radius
        )

        self.canvas.coords(
            self.center_dot,
            x - 3, y - 3, x + 3, y + 3
        )

        self.canvas.coords(
            self.h_line,
            0, y, self.root.winfo_screenwidth(), y
        )
        self.canvas.coords(
            self.v_line,
            x, 0, x, self.root.winfo_screenheight()
        )

        self.canvas.coords(
            self.coord_label,
            x, y - self.circle_radius - 20
        )
        self.canvas.itemconfig(self.coord_label, text=f"X: {x}, Y: {y}")

    def _on_confirm(self, event=None):
        x, y = self.circle_x, self.circle_y
        self.root.destroy()
        self.callback(x, y)

    def _on_cancel(self, event):
        self.root.destroy()
        self.callback(None, None)


class DelayInputDialog:
    def __init__(self, parent, x, y, callback=None):
        self.parent = parent
        self.x = x
        self.y = y
        self.callback = callback

        self._create_dialog()

    def _create_dialog(self):
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Nhập delay")
        self.dialog.geometry("300x150")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text=f"Vị trí: X={self.x}, Y={self.y}").pack(pady=(0, 10))

        delay_frame = ttk.Frame(main_frame)
        delay_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(delay_frame, text="Delay trước khi click (ms):").pack(side=tk.LEFT)
        self.delay_var = tk.IntVar(value=500)
        self.delay_spin = ttk.Spinbox(
            delay_frame,
            from_=0,
            to=60000,
            textvariable=self.delay_var,
            width=10
        )
        self.delay_spin.pack(side=tk.LEFT, padx=(10, 0))

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack()

        ttk.Button(btn_frame, text="OK", command=self._save, width=10).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Hủy", command=self._cancel, width=10).pack(side=tk.LEFT)

        self.dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() - self.dialog.winfo_width()) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")

    def _save(self):
        if self.callback:
            self.callback(self.x, self.y, self.delay_var.get())
        self.dialog.destroy()

    def _cancel(self):
        self.dialog.destroy()


class PositionEditorDialog:
    def __init__(self, parent, x=0, y=0, delay_ms=500, callback=None):
        self.parent = parent
        self.callback = callback
        self.dialog = None

        self._create_dialog(x, y, delay_ms)

    def _create_dialog(self, x, y, delay_ms):
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Sửa vị trí")
        self.dialog.geometry("350x200")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        x_frame = ttk.Frame(main_frame)
        x_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(x_frame, text="X:", width=10).pack(side=tk.LEFT)
        self.x_var = tk.IntVar(value=x)
        ttk.Spinbox(x_frame, from_=0, to=9999, textvariable=self.x_var, width=10).pack(side=tk.LEFT)

        ttk.Button(x_frame, text="📍 Chọn", command=self._pick_position).pack(side=tk.LEFT, padx=(10, 0))

        y_frame = ttk.Frame(main_frame)
        y_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(y_frame, text="Y:", width=10).pack(side=tk.LEFT)
        self.y_var = tk.IntVar(value=y)
        ttk.Spinbox(y_frame, from_=0, to=9999, textvariable=self.y_var, width=10).pack(side=tk.LEFT)

        delay_frame = ttk.Frame(main_frame)
        delay_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(delay_frame, text="Delay (ms):", width=10).pack(side=tk.LEFT)
        self.delay_var = tk.IntVar(value=delay_ms)
        ttk.Spinbox(delay_frame, from_=0, to=60000, textvariable=self.delay_var, width=10).pack(side=tk.LEFT)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack()

        ttk.Button(btn_frame, text="Lưu", command=self._save, width=10).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Hủy", command=self._cancel, width=10).pack(side=tk.LEFT)

        self.dialog.update_idletasks()
        px = self.parent.winfo_x() + (self.parent.winfo_width() - self.dialog.winfo_width()) // 2
        py = self.parent.winfo_y() + (self.parent.winfo_height() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{px}+{py}")

    def _pick_position(self):
        self.dialog.grab_release()
        self.dialog.withdraw()
        self.dialog.after(300, self._open_position_picker)

    def _open_position_picker(self):
        DraggablePositionPicker(self._on_position_picked)

    def _on_position_picked(self, x, y):
        try:
            if not self.dialog.winfo_exists():
                return
            self.dialog.deiconify()
            self.dialog.grab_set()
        except tk.TclError:
            return

        if x is not None and y is not None:
            self.x_var.set(x)
            self.y_var.set(y)

    def _save(self):
        if self.callback:
            self.callback(self.x_var.get(), self.y_var.get(), self.delay_var.get())
        self.dialog.destroy()

    def _cancel(self):
        self.dialog.destroy()
