import tkinter as tk
from tkinter import ttk, messagebox
from PIL import ImageGrab, ImageTk, Image
import cv2
import numpy as np
import os


# Hard-coded template names
PIECE_TEMPLATES = [
    "rook_white",
    "pawn_black",
    "bishop_black",
    "knight_black",
    "rook_black",
    "queen_black",
    "king_black",
]

ALL_TEMPLATES = PIECE_TEMPLATES


class TemplateCaptureDialog:
    """
    Dialog for capturing and saving templates for pieces and buttons.
    Uses fullscreen overlay with region selection.
    """

    def __init__(self, parent, templates_path: str, callback=None):
        """
        Args:
            parent: Parent window
            templates_path: Path to save templates
            callback: Optional callback when template is saved (receives template_name)
        """
        self.parent = parent
        self.templates_path = templates_path
        self.callback = callback

        self.captured_region = None
        self.captured_image = None

        # Create main dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Chụp Template")
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._setup_ui()

        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() - 500) // 2
        y = (self.dialog.winfo_screenheight() - 400) // 2
        self.dialog.geometry(f"+{x}+{y}")

    def _setup_ui(self):
        main_frame = ttk.Frame(self.dialog, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Template type selection
        type_frame = ttk.LabelFrame(main_frame, text="Chọn loại template", padding="10")
        type_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(type_frame, text="Template:").pack(side=tk.LEFT)

        self.template_var = tk.StringVar(value=ALL_TEMPLATES[0])
        self.template_combo = ttk.Combobox(
            type_frame,
            textvariable=self.template_var,
            values=ALL_TEMPLATES,
            state="readonly",
            width=25
        )
        self.template_combo.pack(side=tk.LEFT, padx=10)
        self.template_combo.bind("<<ComboboxSelected>>", self._on_template_selected)

        # Template type indicator
        self.type_label = ttk.Label(type_frame, text="")
        self.type_label.pack(side=tk.LEFT, padx=5)
        self._update_type_label()

        # Capture button
        capture_frame = ttk.Frame(main_frame)
        capture_frame.pack(fill=tk.X, pady=(0, 10))

        self.capture_btn = ttk.Button(
            capture_frame,
            text="📷 Chụp vùng màn hình",
            command=self._start_capture
        )
        self.capture_btn.pack(side=tk.LEFT)

        self.status_label = ttk.Label(capture_frame, text="Chưa chụp", foreground="gray")
        self.status_label.pack(side=tk.LEFT, padx=10)

        # Preview
        preview_frame = ttk.LabelFrame(main_frame, text="Xem trước", padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.preview_canvas = tk.Canvas(preview_frame, bg="gray", width=200, height=150)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)

        self.preview_image = None  # Keep reference

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X)

        self.save_btn = ttk.Button(
            btn_frame,
            text="💾 Lưu Template",
            command=self._save_template,
            state=tk.DISABLED
        )
        self.save_btn.pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            btn_frame,
            text="Đóng",
            command=self.dialog.destroy
        ).pack(side=tk.RIGHT)

        # Info label
        info_text = "Hướng dẫn: Chọn loại template → Nhấn 'Chụp vùng màn hình' → Kéo chọn vùng → Lưu"
        ttk.Label(
            main_frame,
            text=info_text,
            foreground="gray",
            wraplength=450
        ).pack(pady=(10, 0))

    def _on_template_selected(self, event=None):
        self._update_type_label()

    def _update_type_label(self):
        template_name = self.template_var.get()
        if template_name in PIECE_TEMPLATES:
            self.type_label.config(text="(Quân cờ)", foreground="blue")
        else:
            self.type_label.config(text="(Nút bấm)", foreground="green")

    def _start_capture(self):
        """Start fullscreen capture mode"""
        # Release grab so overlay can receive events
        self.dialog.grab_release()
        self.dialog.withdraw()
        self.parent.after(300, self._open_capture_overlay)

    def _open_capture_overlay(self):
        """Open fullscreen overlay for region selection"""
        CaptureOverlay(self._on_region_captured)

    def _on_region_captured(self, image, region):
        """
        Callback when region is captured.

        Args:
            image: PIL Image of captured region
            region: (x1, y1, x2, y2) tuple
        """
        # Check if dialog still exists before trying to show it
        try:
            if not self.dialog.winfo_exists():
                return
            self.dialog.deiconify()
            self.dialog.grab_set()  # Re-acquire grab
        except tk.TclError:
            return

        if image is None:
            self.status_label.config(text="Đã hủy", foreground="orange")
            return

        self.captured_image = image
        self.captured_region = region

        # Update preview
        self._update_preview(image)

        # Enable save button
        self.save_btn.config(state=tk.NORMAL)
        self.status_label.config(
            text=f"Đã chụp: {image.width}x{image.height}px",
            foreground="green"
        )

    def _update_preview(self, image):
        """Update preview canvas with captured image"""
        # Resize to fit preview
        canvas_width = self.preview_canvas.winfo_width()
        canvas_height = self.preview_canvas.winfo_height()

        if canvas_width < 50:
            canvas_width = 200
        if canvas_height < 50:
            canvas_height = 150

        # Calculate scale to fit
        scale_x = canvas_width / image.width
        scale_y = canvas_height / image.height
        scale = min(scale_x, scale_y, 1.0)  # Don't upscale

        new_width = int(image.width * scale)
        new_height = int(image.height * scale)

        if new_width < 1:
            new_width = 1
        if new_height < 1:
            new_height = 1

        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        self.preview_image = ImageTk.PhotoImage(resized)

        self.preview_canvas.delete("all")
        self.preview_canvas.create_image(
            canvas_width // 2,
            canvas_height // 2,
            image=self.preview_image,
            anchor=tk.CENTER
        )

    def _save_template(self):
        """Save captured template to file"""
        if self.captured_image is None:
            messagebox.showerror("Lỗi", "Chưa chụp template!")
            return

        template_name = self.template_var.get()

        # Ensure templates folder exists
        os.makedirs(self.templates_path, exist_ok=True)

        # Save as PNG
        filepath = os.path.join(self.templates_path, f"{template_name}.png")

        # Convert PIL to OpenCV and save
        cv_image = cv2.cvtColor(np.array(self.captured_image), cv2.COLOR_RGB2BGR)
        cv2.imwrite(filepath, cv_image)

        messagebox.showinfo("Thành công", f"Đã lưu template: {template_name}.png")

        # Reset state
        self.captured_image = None
        self.captured_region = None
        self.save_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Đã lưu!", foreground="blue")
        self.preview_canvas.delete("all")

        # Callback
        if self.callback:
            self.callback(template_name)


class CaptureOverlay:
    """Fullscreen overlay for region selection - based on RegionSelector logic"""

    def __init__(self, callback):
        """
        Args:
            callback: Function(image, region) called when capture completes
                     image: PIL Image or None if cancelled
                     region: (x1, y1, x2, y2) or None
        """
        self.callback = callback
        self.start_x = None
        self.start_y = None
        self.rect_id = None

        # Take screenshot first
        self.screenshot = ImageGrab.grab()

        # Create fullscreen window
        self.root = tk.Toplevel()
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)
        self.root.configure(cursor="cross")

        # Convert to PhotoImage
        self.screenshot_tk = ImageTk.PhotoImage(self.screenshot)

        # Create canvas
        self.canvas = tk.Canvas(
            self.root,
            highlightthickness=0,
            cursor="cross"
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Draw screenshot
        self.canvas.create_image(0, 0, image=self.screenshot_tk, anchor=tk.NW)

        # Draw semi-transparent overlay
        self.canvas.create_rectangle(
            0, 0,
            self.root.winfo_screenwidth(),
            self.root.winfo_screenheight(),
            fill="black",
            stipple="gray50",
            outline=""
        )

        # Instructions
        self.canvas.create_text(
            self.root.winfo_screenwidth() // 2,
            30,
            text="Kéo để chọn vùng template. Nhấn ESC để hủy.",
            fill="white",
            font=("Arial", 16, "bold")
        )

        # Bind events
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
            self.start_x, self.start_y,
            self.start_x, self.start_y,
            outline="red",
            width=2
        )

    def _on_drag(self, event):
        if self.rect_id:
            self.canvas.coords(
                self.rect_id,
                self.start_x, self.start_y,
                event.x, event.y
            )

    def _on_release(self, event):
        end_x = event.x
        end_y = event.y

        # Destroy window first
        self.root.destroy()

        # Check if valid selection
        if self.start_x is not None and self.start_y is not None:
            if abs(end_x - self.start_x) > 10 and abs(end_y - self.start_y) > 10:
                # Ensure proper coordinates
                x1 = min(self.start_x, end_x)
                y1 = min(self.start_y, end_y)
                x2 = max(self.start_x, end_x)
                y2 = max(self.start_y, end_y)

                # Crop screenshot
                cropped = self.screenshot.crop((x1, y1, x2, y2))
                self.callback(cropped, (x1, y1, x2, y2))
            else:
                self.callback(None, None)
        else:
            self.callback(None, None)

    def _on_cancel(self, event):
        self.root.destroy()
        self.callback(None, None)
