import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import os
import sys


def get_base_path():
    """Get base path for both script and frozen exe"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


script_dir = get_base_path()
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from config import load_config, save_config, get_templates_path
from .setup_tab import SetupTab
from .control_tab import ControlTab
from .log_tab import LogTab
from .preview_tab import PreviewTab


class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Chess Bot - Tự động chơi cờ")
        self.root.geometry("800x600")
        self.root.minsize(700, 500)

        self.config = load_config()
        self.bot_running = False
        self.bot_paused = False
        self.bot_thread = None
        self.script_dir = script_dir

        self._setup_ui()

    def _setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.setup_tab = SetupTab(self.notebook, self)
        self.control_tab = ControlTab(self.notebook, self)
        self.log_tab = LogTab(self.notebook, self)
        self.preview_tab = PreviewTab(self.notebook, self)

        self.notebook.add(self.setup_tab.frame, text="Cài đặt")
        self.notebook.add(self.control_tab.frame, text="Điều khiển")
        self.notebook.add(self.log_tab.frame, text="Nhật ký")
        self.notebook.add(self.preview_tab.frame, text="Xem trước")

        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(10, 0))

        self.status_label = ttk.Label(status_frame, text="Trạng thái: Sẵn sàng")
        self.status_label.pack(side=tk.LEFT)

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        if self.bot_running:
            self.stop_bot()
        if hasattr(self.control_tab, 'stop_hotkey_listener'):
            self.control_tab.stop_hotkey_listener()
        if hasattr(self.preview_tab, 'cleanup'):
            self.preview_tab.cleanup()
        self.root.destroy()

    def update_status(self, text):
        self.status_label.config(text=f"Trạng thái: {text}")

    def log(self, message):
        self.log_tab.add_log(message)

    def save_current_config(self):
        save_config(self.config)
        self.log("Đã lưu cấu hình")

    def start_bot(self):
        if not self._validate_config():
            return False

        self.bot_running = True
        self.bot_paused = False
        self.bot_thread = threading.Thread(target=self._bot_loop, daemon=True)
        self.bot_thread.start()
        self.update_status("Đang chạy")
        self.log("Bot đã bắt đầu")
        return True

    def stop_bot(self):
        self.bot_running = False
        self.bot_paused = False
        self.update_status("Đã dừng")
        self.log("Bot đã dừng")

    def pause_bot(self):
        self.bot_paused = not self.bot_paused
        status = "Tạm dừng" if self.bot_paused else "Đang chạy"
        self.update_status(status)
        self.log(f"Bot {'đã tạm dừng' if self.bot_paused else 'đang chạy'}")

    def _validate_config(self):
        if not self.config.get("game_region"):
            messagebox.showerror("Lỗi", "Vui lòng chọn vùng chơi trước")
            return False
        if not self.config.get("light_cell_color") or not self.config.get("dark_cell_color"):
            messagebox.showerror("Lỗi", "Vui lòng chọn màu ô cờ trước")
            return False
        return True

    def _bot_loop(self):
        from core.screen_capture import ScreenCapture
        from core.board_detector import BoardDetector
        from core.piece_detector import PieceDetector
        from core.ai_player import AIPlayer
        from core.mouse_controller import MouseController
        from core.button_detector import ButtonDetector

        capture = ScreenCapture(self.config["game_region"])
        board_detector = BoardDetector(
            self.config["light_cell_color"],
            self.config["dark_cell_color"],
            self.config.get("color_tolerance", 30)
        )

        templates_path = get_templates_path()
        piece_detector = PieceDetector(templates_path)
        button_detector = ButtonDetector(templates_path)

        # Get play mode from config
        play_mode = self.config.get("play_mode", "normal")
        ai_player = AIPlayer(play_mode=play_mode)
        mouse = MouseController()

        # Apply virtual click mode setting
        virtual_mode = self.config.get("virtual_click_mode", True)
        mouse.set_virtual_mode(virtual_mode)

        move_count = 0
        no_rook_count = 0
        max_no_rook_retries = 3

        # Track last trigger time per condition for cooldown
        condition_last_triggered = {}

        self._safe_log(f"Bắt đầu vòng lặp bot - Chế độ: {'Tự sát' if play_mode == 'suicide' else 'Bình thường'}")

        while self.bot_running:
            if self.bot_paused:
                time.sleep(0.1)
                continue

            # Update play mode dynamically (in case user changed it)
            current_mode = self.config.get("play_mode", "normal")
            if ai_player.play_mode != current_mode:
                ai_player.set_play_mode(current_mode)
                self._safe_log(f"Đã đổi chế độ: {'Tự sát' if current_mode == 'suicide' else 'Bình thường'}")

            try:
                screenshot = capture.capture()
                if screenshot is None:
                    self._safe_log("Chụp màn hình thất bại")
                    time.sleep(1)
                    continue

                # Check and execute auto-click conditions
                condition_executed = self._check_and_execute_conditions(
                    screenshot, button_detector, mouse, condition_last_triggered
                )
                if condition_executed:
                    # Re-capture after condition execution
                    time.sleep(0.5)
                    continue

                cells = board_detector.detect_cells(screenshot)
                if cells is None:
                    self._safe_log("Không phát hiện được bàn cờ")
                    time.sleep(1)
                    continue

                board_state, rook_pos = piece_detector.detect_pieces(screenshot, cells)

                if rook_pos is None:
                    no_rook_count += 1

                    if no_rook_count >= max_no_rook_retries:
                        self._safe_log("Không tìm thấy xe - đang chờ...")
                        time.sleep(2)
                        continue
                    else:
                        time.sleep(0.3)
                        continue
                else:
                    no_rook_count = 0

                ai_player.update_position(rook_pos)

                valid_moves = ai_player.get_valid_moves(rook_pos, board_state)
                danger_cells = ai_player.get_danger_cells(board_state)

                current_in_danger = rook_pos in danger_cells
                if current_in_danger:
                    self._safe_log(f"CẢNH BÁO: Xe tại {rook_pos} đang bị đe dọa!")

                if not valid_moves:
                    self._safe_log("Không có nước đi hợp lệ")
                    time.sleep(0.5)
                    continue

                best_move = ai_player.select_best_move(valid_moves, board_state, danger_cells, rook_pos)

                if best_move:
                    target_row, target_col, is_capture = best_move
                    cell_info = cells[target_row][target_col]
                    click_x = cell_info["center_x"]
                    click_y = cell_info["center_y"]

                    region = self.config["game_region"]
                    abs_x = region[0] + click_x
                    abs_y = region[1] + click_y

                    action = "Ăn" if is_capture else "Di chuyển"
                    target_in_danger = (target_row, target_col) in danger_cells
                    danger_warning = " [NGUY HIỂM!]" if target_in_danger else ""

                    self._safe_log(f"{action} đến ({target_row}, {target_col}){danger_warning}")

                    mouse.click(abs_x, abs_y)
                    move_count += 1

                    current_count = move_count
                    self.root.after(0, lambda c=current_count: self.control_tab.update_move_count(c))

                delay = self.config.get("move_delay", 500) / 1000.0
                time.sleep(delay)

            except Exception as e:
                self._safe_log(f"Lỗi: {str(e)}")
                import traceback
                traceback.print_exc()
                time.sleep(1)

        self._safe_log("Vòng lặp bot đã kết thúc")

    def _check_and_execute_conditions(self, screenshot, button_detector, mouse, condition_last_triggered):
        """
        Check all auto-click conditions and execute click sequences if triggered.

        Args:
            screenshot: Current screenshot
            button_detector: ButtonDetector instance
            mouse: MouseController instance
            condition_last_triggered: Dict tracking last trigger time per condition name

        Returns:
            True if any condition was executed, False otherwise
        """
        conditions = self.config.get("auto_click_conditions", [])

        if not conditions:
            return False

        current_time = time.time() * 1000  # Convert to ms

        for condition in conditions:
            if not condition.get("enabled", True):
                continue

            cond_name = condition.get("name", "Unknown")
            template_name = condition.get("template_name", "")
            cooldown_ms = condition.get("cooldown_ms", 1000)
            click_sequence = condition.get("click_sequence", [])

            if not template_name or not click_sequence:
                continue

            # Check cooldown
            last_triggered = condition_last_triggered.get(cond_name, 0)
            if current_time - last_triggered < cooldown_ms:
                continue

            # Check if template is detected
            result = button_detector.detect_button(screenshot, template_name)
            if result is None:
                continue

            # Template detected! Execute click sequence
            self._safe_log(f"Điều kiện '{cond_name}' kích hoạt - phát hiện {template_name}")

            # Execute click sequence
            for i, click_pos in enumerate(click_sequence):
                if not self.bot_running:
                    return True

                x = click_pos.get("x", 0)
                y = click_pos.get("y", 0)
                delay_ms = click_pos.get("delay_ms", 500)

                # Apply delay before click
                if delay_ms > 0:
                    time.sleep(delay_ms / 1000.0)

                self._safe_log(f"  Click {i+1}/{len(click_sequence)}: ({x}, {y})")
                mouse.click(x, y)

            # Update last triggered time
            condition_last_triggered[cond_name] = time.time() * 1000
            self._safe_log(f"Điều kiện '{cond_name}' hoàn thành")

            return True  # Only execute one condition per loop

        return False

    def _safe_log(self, message):
        try:
            if self.root.winfo_exists():
                self.root.after_idle(lambda m=message: self._do_log(m))
        except Exception:
            pass
        # Always print to console for debugging
        print(f"[LOG] {message}")

    def _do_log(self, message):
        """Actually perform the log - must be called from main thread"""
        try:
            if self.root.winfo_exists():
                self.log(message)
        except Exception:
            pass

    def run(self):
        self.root.mainloop()
