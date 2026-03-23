import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageDraw


class PreviewTab:
    def __init__(self, parent, main_window):
        self.main_window = main_window
        self.frame = ttk.Frame(parent, padding="10")

        self.preview_image = None
        self.live_preview_active = False
        self.update_job = None

        self._setup_ui()

    def _setup_ui(self):
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))

        self.preview_btn = ttk.Button(
            control_frame,
            text="📷 Chụp một lần",
            command=self._capture_once
        )
        self.preview_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.live_btn = ttk.Button(
            control_frame,
            text="Bắt đầu xem trực tiếp",
            command=self._toggle_live_preview
        )
        self.live_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Refresh rate control
        refresh_frame = ttk.Frame(control_frame)
        refresh_frame.pack(side=tk.LEFT, padx=(10, 0))

        ttk.Label(refresh_frame, text="Tỉ lệ làm mới:").pack(side=tk.LEFT)
        self.refresh_var = tk.IntVar(value=500)
        self.refresh_scale = ttk.Scale(
            refresh_frame,
            from_=100,
            to=2000,
            variable=self.refresh_var,
            orient=tk.HORIZONTAL,
            length=150,
            command=self._on_refresh_change
        )
        self.refresh_scale.pack(side=tk.LEFT, padx=5)
        self.refresh_label = ttk.Label(refresh_frame, text="500ms")
        self.refresh_label.pack(side=tk.LEFT)

        self.status_label = ttk.Label(control_frame, text="", foreground="gray")
        self.status_label.pack(side=tk.LEFT, padx=(10, 0))

        preview_frame = ttk.LabelFrame(self.frame, text="Xem trước Detection", padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(preview_frame, bg="gray")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        legend_frame = ttk.LabelFrame(self.frame, text="Chú thích", padding="5")
        legend_frame.pack(fill=tk.X, pady=(10, 0))

        legend_text = "🟦 Quân xanh | 🟥 Quân đỏ | ⬜ Ô chưa lật | ⬛ Ô trống"
        ttk.Label(legend_frame, text=legend_text).pack(anchor=tk.W)

    def _on_refresh_change(self, value):
        """Handle refresh rate slider change"""
        int_value = int(float(value))
        self.refresh_label.config(text=f"{int_value}ms")

    def _capture_once(self):
        """Capture and display detection result once"""
        self._do_capture()

    def _toggle_live_preview(self):
        """Toggle live preview mode"""
        if self.live_preview_active:
            self._stop_live_preview()
        else:
            self._start_live_preview()

    def _start_live_preview(self):
        """Start live preview"""
        self.live_preview_active = True
        self.live_btn.config(text="Dừng xem trực tiếp")
        self._schedule_update()
        self.status_label.config(text="Đang xem trực tiếp...")

    def _stop_live_preview(self):
        """Stop live preview"""
        self.live_preview_active = False
        self.live_btn.config(text="Bắt đầu xem trực tiếp")

        if self.update_job:
            self.main_window.root.after_cancel(self.update_job)
            self.update_job = None

        self.status_label.config(text="")

    def _schedule_update(self):
        """Schedule next preview update"""
        if not self.live_preview_active:
            return

        self._do_capture()

        refresh_ms = self.refresh_var.get()
        self.update_job = self.main_window.root.after(refresh_ms, self._schedule_update)

    def _do_capture(self):
        """Perform capture and detection"""
        region = self.main_window.config.get("game_region")
        if not region:
            self.status_label.config(text="Chưa chọn vùng chơi")
            return

        try:
            from core.screen_capture import ScreenCapture
            from core.board_detector import BoardDetector, BOARD_SIZE
            from core.cell_detector import CellDetector, CellState
            from core.piece_detector import PieceDetector
            from config import get_templates_path

            capture = ScreenCapture(region)
            screenshot = capture.capture()

            if screenshot is None:
                self.status_label.config(text="Không thể chụp màn hình")
                return

            board_detector = BoardDetector(
                self.main_window.config.get("cell_color"),
                self.main_window.config.get("color_tolerance", 30),
                self.main_window.config.get("cell_gap")
            )

            templates_path = get_templates_path()
            cell_detector = CellDetector(templates_path)
            piece_detector = PieceDetector(templates_path)

            cells = board_detector.detect_cells(screenshot)

            if cells is None:
                self.status_label.config(text="Không phát hiện được bàn cờ")
                return

            cell_states = cell_detector.detect_all_cells(screenshot, cells)
            board_state = piece_detector.detect_pieces(screenshot, cells)

            self._draw_preview(screenshot, cells, cell_states, board_state)

            blue_count = sum(1 for row in board_state for p in row if p and p.is_blue)
            red_count = sum(1 for row in board_state for p in row if p and not p.is_blue)
            unflipped_count = sum(1 for row in cell_states for c in row if c.state == CellState.UNFLIPPED)

            self.status_label.config(
                text=f"Xanh: {blue_count} | Đỏ: {red_count} | Chưa lật: {unflipped_count}"
            )

        except Exception as e:
            self.status_label.config(text=f"Lỗi: {str(e)}")
            import traceback
            traceback.print_exc()

    def _draw_preview(self, screenshot, cells, cell_states, board_state):
        """Draw detection preview on canvas"""
        import cv2
        import numpy as np
        from core.board_detector import BOARD_SIZE
        from core.cell_detector import CellState

        img_rgb = cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(img_rgb)
        draw = ImageDraw.Draw(pil_image)

        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                cell = cells[row][col]
                if cell is None:
                    continue

                x1 = cell["x"]
                y1 = cell["y"]
                x2 = x1 + cell["width"]
                y2 = y1 + cell["height"]

                cell_state = cell_states[row][col]
                piece = board_state[row][col]

                if cell_state.state == CellState.UNFLIPPED:
                    outline_color = "yellow"
                    draw.rectangle([x1, y1, x2, y2], outline=outline_color, width=3)
                    draw.text((x1 + 5, y1 + 5), "?", fill="yellow")
                elif piece is not None:
                    if piece.is_blue:
                        outline_color = "blue"
                    else:
                        outline_color = "red"
                    draw.rectangle([x1, y1, x2, y2], outline=outline_color, width=3)

                    piece_text = piece.type[:3].upper()
                    text_color = "cyan" if piece.is_blue else "orange"
                    draw.text((x1 + 5, y1 + 5), piece_text, fill=text_color)
                    draw.text((x1 + 5, y2 - 20), str(piece.power), fill=text_color)
                else:
                    outline_color = "gray"
                    draw.rectangle([x1, y1, x2, y2], outline=outline_color, width=1)

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if canvas_width < 10:
            canvas_width = 400
        if canvas_height < 10:
            canvas_height = 400

        img_ratio = pil_image.width / pil_image.height
        canvas_ratio = canvas_width / canvas_height

        if img_ratio > canvas_ratio:
            new_width = canvas_width
            new_height = int(canvas_width / img_ratio)
        else:
            new_height = canvas_height
            new_width = int(canvas_height * img_ratio)

        pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        self.preview_image = ImageTk.PhotoImage(pil_image)

        self.canvas.delete("all")
        self.canvas.create_image(
            canvas_width // 2,
            canvas_height // 2,
            image=self.preview_image,
            anchor=tk.CENTER
        )

    def cleanup(self):
        """Cleanup when closing"""
        self._stop_live_preview()
