import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageDraw, ImageFont
import numpy as np
import cv2


class PreviewTab:
    PIECE_LABELS = {
        "ROOK": "R",
        "PAWN": "P",
        "BISHOP": "B",
        "KNIGHT": "N",
        "QUEEN": "Q",
        "KING": "K",
    }
    
    def __init__(self, parent, main_window):
        self.main_window = main_window
        self.frame = ttk.Frame(parent, padding="10")
        
        self.preview_image = None
        self.live_preview_active = False
        self.update_job = None
        
        self._screen_capture = None
        self._board_detector = None
        self._piece_detector = None
        
        self._setup_ui()
        
    def _setup_ui(self):
        preview_frame = ttk.LabelFrame(self.frame, text="Detection Preview", padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.preview_canvas = tk.Canvas(preview_frame, bg="#2b2b2b", width=500, height=400)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)
        
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(fill=tk.X)
        
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.test_btn = ttk.Button(
            btn_frame,
            text="Test Detection",
            command=self._test_detection
        )
        self.test_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.live_btn = ttk.Button(
            btn_frame,
            text="Start Live Preview",
            command=self._toggle_live_preview
        )
        self.live_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        refresh_frame = ttk.Frame(btn_frame)
        refresh_frame.pack(side=tk.LEFT, padx=(20, 0))
        
        ttk.Label(refresh_frame, text="Refresh rate:").pack(side=tk.LEFT)
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
        
        status_frame = ttk.LabelFrame(control_frame, text="Detection Status", padding="5")
        status_frame.pack(fill=tk.X)
        
        self.status_label = ttk.Label(
            status_frame, 
            text="Board: -- | Cells: -- | Pieces: -- | Rook: --"
        )
        self.status_label.pack(fill=tk.X)
        
    def _on_refresh_change(self, value):
        int_value = int(float(value))
        self.refresh_label.config(text=f"{int_value}ms")
        
    def _get_detectors(self):
        if self._screen_capture is None or self._board_detector is None or self._piece_detector is None:
            from core.screen_capture import ScreenCapture
            from core.board_detector import BoardDetector
            from core.piece_detector import PieceDetector
            from config import get_templates_path
            
            config = self.main_window.config
            region = config.get("game_region")
            
            if region:
                self._screen_capture = ScreenCapture(region)
            
            light_color = config.get("light_cell_color")
            dark_color = config.get("dark_cell_color")
            tolerance = config.get("color_tolerance", 30)
            
            if light_color and dark_color:
                self._board_detector = BoardDetector(light_color, dark_color, tolerance)
            
            templates_path = get_templates_path()
            self._piece_detector = PieceDetector(templates_path)
            
        return self._screen_capture, self._board_detector, self._piece_detector
    
    def _reset_detectors(self):
        self._screen_capture = None
        self._board_detector = None
        self._piece_detector = None
        
    def _test_detection(self):
        self._reset_detectors()
        self._run_detection()
        
    def _run_detection(self):
        config = self.main_window.config
        region = config.get("game_region")
        
        if not region:
            self._show_error("No game region selected.\nGo to Setup tab to select a region.")
            self._update_status(board_ok=False)
            return
            
        light_color = config.get("light_cell_color")
        dark_color = config.get("dark_cell_color")
        
        if not light_color or not dark_color:
            self._show_error("Cell colors not configured.\nGo to Setup tab to pick colors.")
            self._update_status(board_ok=False)
            return
            
        try:
            screen_capture, board_detector, piece_detector = self._get_detectors()
            
            if screen_capture is None:
                self._show_error("Failed to initialize screen capture.")
                self._update_status(board_ok=False)
                return
                
            screen_capture.set_region(region)
            
            if board_detector:
                board_detector.set_colors(light_color, dark_color)
                board_detector.set_tolerance(config.get("color_tolerance", 30))
            
            screenshot = screen_capture.capture()
            
            if screenshot is None:
                self._show_error("Failed to capture screen.")
                self._update_status(board_ok=False)
                return
                
            cells = None
            board_state = None
            rook_pos = None
            piece_count = 0
            
            if board_detector:
                cells = board_detector.detect_cells(screenshot)
                
            if cells and piece_detector:
                board_state, rook_pos = piece_detector.detect_pieces(screenshot, cells)
                if board_state:
                    for row in board_state:
                        for piece in row:
                            if piece is not None:
                                piece_count += 1
            
            self._render_preview(screenshot, cells, board_state, rook_pos)
            
            cell_count = 64 if cells else 0
            self._update_status(
                board_ok=cells is not None,
                cell_count=cell_count,
                piece_count=piece_count,
                rook_pos=rook_pos
            )
            
        except Exception as e:
            self._show_error(f"Detection error:\n{str(e)}")
            self._update_status(board_ok=False)
            self.main_window.log(f"Preview error: {str(e)}")
            
    def _render_preview(self, screenshot, cells, board_state, rook_pos):
        screenshot_rgb = cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(screenshot_rgb)
        
        draw = ImageDraw.Draw(pil_image, 'RGBA')
        
        if cells:
            self._draw_grid_overlay(draw, cells)
            
        if board_state:
            self._draw_piece_markers(draw, cells, board_state, rook_pos)
            
        canvas_width = self.preview_canvas.winfo_width()
        canvas_height = self.preview_canvas.winfo_height()
        
        if canvas_width < 10:
            canvas_width = 500
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
        
        self.preview_canvas.delete("all")
        self.preview_canvas.create_image(
            canvas_width // 2,
            canvas_height // 2,
            image=self.preview_image,
            anchor=tk.CENTER
        )
        
    def _draw_grid_overlay(self, draw, cells):
        grid_color = (0, 255, 0, 180)
        
        if not cells or len(cells) < 8 or len(cells[0]) < 8:
            return
            
        first_cell = cells[0][0]
        last_cell = cells[7][7]
        
        if first_cell is None or last_cell is None:
            return
            
        for row in range(9):
            if row < 8:
                cell = cells[row][0]
                y = cell["y"]
            else:
                cell = cells[7][0]
                y = cell["y"] + cell["height"]
                
            x1 = cells[0][0]["x"]
            x2 = cells[0][7]["x"] + cells[0][7]["width"]
            draw.line([(x1, y), (x2, y)], fill=grid_color, width=2)
            
        for col in range(9):
            if col < 8:
                cell = cells[0][col]
                x = cell["x"]
            else:
                cell = cells[0][7]
                x = cell["x"] + cell["width"]
                
            y1 = cells[0][0]["y"]
            y2 = cells[7][0]["y"] + cells[7][0]["height"]
            draw.line([(x, y1), (x, y2)], fill=grid_color, width=2)
            
    def _draw_piece_markers(self, draw, cells, board_state, rook_pos):
        if not cells or not board_state:
            return
            
        try:
            font = ImageFont.truetype("arial.ttf", 14)
        except:
            font = ImageFont.load_default()
            
        for row in range(8):
            for col in range(8):
                piece = board_state[row][col]
                if piece is None:
                    continue
                    
                cell = cells[row][col]
                if cell is None:
                    continue
                    
                center_x = cell["center_x"]
                center_y = cell["center_y"]
                radius = min(cell["width"], cell["height"]) // 4
                
                if piece.is_player:
                    fill_color = (0, 200, 0, 150)
                    outline_color = (0, 255, 0, 255)
                    text_color = (255, 255, 255, 255)
                else:
                    fill_color = (200, 0, 0, 150)
                    outline_color = (255, 0, 0, 255)
                    text_color = (255, 255, 255, 255)
                    
                draw.ellipse(
                    [
                        center_x - radius,
                        center_y - radius,
                        center_x + radius,
                        center_y + radius
                    ],
                    fill=fill_color,
                    outline=outline_color,
                    width=2
                )
                
                label = self.PIECE_LABELS.get(piece.type, "?")
                bbox = draw.textbbox((0, 0), label, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                draw.text(
                    (center_x - text_width // 2, center_y - text_height // 2),
                    label,
                    fill=text_color,
                    font=font
                )
                
                confidence_text = f"{int(piece.confidence * 100)}%"
                conf_bbox = draw.textbbox((0, 0), confidence_text, font=font)
                conf_width = conf_bbox[2] - conf_bbox[0]
                
                draw.text(
                    (center_x - conf_width // 2, center_y + radius + 2),
                    confidence_text,
                    fill=text_color,
                    font=font
                )
                
    def _show_error(self, message):
        self.preview_canvas.delete("all")
        
        canvas_width = self.preview_canvas.winfo_width()
        canvas_height = self.preview_canvas.winfo_height()
        
        if canvas_width < 10:
            canvas_width = 500
        if canvas_height < 10:
            canvas_height = 400
            
        self.preview_canvas.create_text(
            canvas_width // 2,
            canvas_height // 2,
            text=message,
            fill="#ff6b6b",
            font=("Arial", 14),
            justify=tk.CENTER
        )
        
    def _update_status(self, board_ok=False, cell_count=0, piece_count=0, rook_pos=None):
        board_status = "OK" if board_ok else "FAIL"
        rook_text = f"({rook_pos[0]}, {rook_pos[1]})" if rook_pos else "--"
        
        status_text = f"Board: {board_status} | Cells: {cell_count} | Pieces: {piece_count} | Rook: {rook_text}"
        self.status_label.config(text=status_text)
        
    def _toggle_live_preview(self):
        if self.live_preview_active:
            self._stop_live_preview()
        else:
            self._start_live_preview()
            
    def _start_live_preview(self):
        self.live_preview_active = True
        self.live_btn.config(text="Stop Live Preview")
        self._reset_detectors()
        self._schedule_update()
        self.main_window.log("Live preview started")
        
    def _stop_live_preview(self):
        self.live_preview_active = False
        self.live_btn.config(text="Start Live Preview")
        
        if self.update_job:
            self.main_window.root.after_cancel(self.update_job)
            self.update_job = None
            
        self.main_window.log("Live preview stopped")
        
    def _schedule_update(self):
        if not self.live_preview_active:
            return
            
        self._run_detection()
        
        refresh_ms = self.refresh_var.get()
        self.update_job = self.main_window.root.after(refresh_ms, self._schedule_update)
        
    def cleanup(self):
        self._stop_live_preview()
        self._reset_detectors()
