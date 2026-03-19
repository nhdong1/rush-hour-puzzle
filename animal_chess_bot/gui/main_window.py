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
        self.root.title("Animal Chess Bot - Cờ Thú Tự Động")
        self.root.geometry("800x650")
        self.root.minsize(700, 550)

        self.config = load_config()
        self.bot_running = False
        self.bot_paused = False
        self.bot_thread = None
        self.script_dir = script_dir
        
        self.selected_piece_pos = None

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
        
        self.score_label = ttk.Label(status_frame, text="Điểm: Xanh 0 - Đỏ 0")
        self.score_label.pack(side=tk.RIGHT)

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
    
    def update_score(self, blue_score: int, red_score: int):
        self.score_label.config(text=f"Điểm: Xanh {blue_score} - Đỏ {red_score}")

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
        self.selected_piece_pos = None
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
        return True

    def _bot_loop(self):
        from core.screen_capture import ScreenCapture
        from core.board_detector import BoardDetector
        from core.cell_detector import CellDetector
        from core.piece_detector import PieceDetector
        from core.ai_player import AIPlayer, ActionType
        from core.mouse_controller import MouseController
        from core.button_detector import ButtonDetector

        capture = ScreenCapture(self.config["game_region"])
        
        board_detector = BoardDetector(
            self.config.get("cell_color"),
            self.config.get("color_tolerance", 30)
        )

        templates_path = get_templates_path()
        cell_detector = CellDetector(templates_path)
        piece_detector = PieceDetector(templates_path)
        button_detector = ButtonDetector(templates_path)
        
        ai_player = AIPlayer()
        mouse = MouseController()

        virtual_mode = self.config.get("virtual_click_mode", True)
        mouse.set_virtual_mode(virtual_mode)

        move_count = 0
        condition_last_triggered = {}

        self._safe_log("Bắt đầu vòng lặp bot - Cờ Thú")

        while self.bot_running:
            if self.bot_paused:
                time.sleep(0.1)
                continue

            try:
                screenshot = capture.capture()
                if screenshot is None:
                    self._safe_log("Chụp màn hình thất bại")
                    time.sleep(1)
                    continue

                condition_executed = self._check_and_execute_conditions(
                    screenshot, button_detector, mouse, condition_last_triggered
                )
                if condition_executed:
                    time.sleep(0.5)
                    continue

                cells = board_detector.detect_cells(screenshot)
                if cells is None:
                    self._safe_log("Không phát hiện được bàn cờ")
                    time.sleep(1)
                    continue

                cell_states = cell_detector.detect_all_cells(screenshot, cells)
                board_state = piece_detector.detect_pieces(screenshot, cells)

                valid_actions = ai_player.get_valid_actions(board_state, cell_states)

                if not valid_actions:
                    self._safe_log("Không có hành động hợp lệ")
                    time.sleep(0.5)
                    continue

                best_action = ai_player.select_best_action(valid_actions, board_state, cell_states)

                if best_action:
                    region = self.config["game_region"]
                    
                    if best_action.type == ActionType.FLIP:
                        target_row, target_col = best_action.target_pos
                        cell_info = cells[target_row][target_col]
                        click_x = region[0] + cell_info["center_x"]
                        click_y = region[1] + cell_info["center_y"]
                        
                        self._safe_log(f"Lật ô ({target_row}, {target_col})")
                        mouse.click(click_x, click_y)
                        
                    elif best_action.type in [ActionType.MOVE, ActionType.CAPTURE]:
                        src_row, src_col = best_action.source_pos
                        src_cell = cells[src_row][src_col]
                        src_x = region[0] + src_cell["center_x"]
                        src_y = region[1] + src_cell["center_y"]
                        
                        self._safe_log(f"Chọn quân {best_action.piece.type} tại ({src_row}, {src_col})")
                        mouse.click(src_x, src_y)
                        
                        time.sleep(0.3)
                        
                        dst_row, dst_col = best_action.target_pos
                        dst_cell = cells[dst_row][dst_col]
                        dst_x = region[0] + dst_cell["center_x"]
                        dst_y = region[1] + dst_cell["center_y"]
                        
                        action_name = "Di chuyển" if best_action.type == ActionType.MOVE else "Ăn"
                        target_info = ""
                        if best_action.type == ActionType.CAPTURE:
                            target_info = f" {best_action.target_piece.type}"
                            ai_player.add_score(best_action.target_piece.power, True)
                        
                        self._safe_log(f"{action_name}{target_info} đến ({dst_row}, {dst_col})")
                        mouse.click(dst_x, dst_y)
                    
                    move_count += 1
                    ai_player.update_turn()
                    
                    self.root.after(0, lambda c=move_count: self.control_tab.update_move_count(c))
                    self.root.after(0, lambda: self.update_score(ai_player.blue_score, ai_player.red_score))

                delay = self.config.get("move_delay", 500) / 1000.0
                time.sleep(delay)

            except Exception as e:
                self._safe_log(f"Lỗi: {str(e)}")
                import traceback
                traceback.print_exc()
                time.sleep(1)

        self._safe_log("Vòng lặp bot đã kết thúc")

    def _check_and_execute_conditions(self, screenshot, button_detector, mouse, condition_last_triggered):
        """Check all auto-click conditions and execute click sequences if triggered."""
        conditions = self.config.get("auto_click_conditions", [])

        if not conditions:
            return False

        current_time = time.time() * 1000

        for condition in conditions:
            if not condition.get("enabled", True):
                continue

            cond_name = condition.get("name", "Unknown")
            template_name = condition.get("template_name", "")
            cooldown_ms = condition.get("cooldown_ms", 1000)
            click_sequence = condition.get("click_sequence", [])

            if not template_name or not click_sequence:
                continue

            last_triggered = condition_last_triggered.get(cond_name, 0)
            if current_time - last_triggered < cooldown_ms:
                continue

            result = button_detector.detect_button(screenshot, template_name)
            if result is None:
                continue

            self._safe_log(f"Điều kiện '{cond_name}' kích hoạt - phát hiện {template_name}")

            for i, click_pos in enumerate(click_sequence):
                if not self.bot_running:
                    return True

                x = click_pos.get("x", 0)
                y = click_pos.get("y", 0)
                delay_ms = click_pos.get("delay_ms", 500)

                if delay_ms > 0:
                    time.sleep(delay_ms / 1000.0)

                self._safe_log(f"  Click {i+1}/{len(click_sequence)}: ({x}, {y})")
                mouse.click(x, y)

            condition_last_triggered[cond_name] = time.time() * 1000
            self._safe_log(f"Điều kiện '{cond_name}' hoàn thành")

            return True

        return False

    def _safe_log(self, message):
        try:
            if self.root.winfo_exists():
                self.root.after_idle(lambda m=message: self._do_log(m))
        except Exception:
            pass
        print(f"[LOG] {message}")

    def _do_log(self, message):
        try:
            if self.root.winfo_exists():
                self.log(message)
        except Exception:
            pass

    def run(self):
        self.root.mainloop()
