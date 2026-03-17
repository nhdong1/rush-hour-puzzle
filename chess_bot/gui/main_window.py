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
        self.root.title("Chess Bot - Auto Player")
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
        
        self.notebook.add(self.setup_tab.frame, text="Setup")
        self.notebook.add(self.control_tab.frame, text="Control")
        self.notebook.add(self.log_tab.frame, text="Log")
        self.notebook.add(self.preview_tab.frame, text="Detection Preview")
        
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.status_label = ttk.Label(status_frame, text="Status: Ready")
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
        self.status_label.config(text=f"Status: {text}")
        
    def log(self, message):
        self.log_tab.add_log(message)
        
    def save_current_config(self):
        save_config(self.config)
        self.log("Configuration saved")
        
    def start_bot(self):
        if not self._validate_config():
            return False
            
        self.bot_running = True
        self.bot_paused = False
        self.bot_thread = threading.Thread(target=self._bot_loop, daemon=True)
        self.bot_thread.start()
        self.update_status("Running")
        self.log("Bot started")
        return True
        
    def stop_bot(self):
        self.bot_running = False
        self.bot_paused = False
        self.update_status("Stopped")
        self.log("Bot stopped")
        
    def pause_bot(self):
        self.bot_paused = not self.bot_paused
        status = "Paused" if self.bot_paused else "Running"
        self.update_status(status)
        self.log(f"Bot {status.lower()}")
        
    def _validate_config(self):
        if not self.config.get("game_region"):
            messagebox.showerror("Error", "Please select game region first")
            return False
        if not self.config.get("light_cell_color") or not self.config.get("dark_cell_color"):
            messagebox.showerror("Error", "Please pick cell colors first")
            return False
        return True
        
    def _bot_loop(self):
        from core.screen_capture import ScreenCapture
        from core.board_detector import BoardDetector
        from core.piece_detector import PieceDetector
        from core.ai_player import AIPlayer
        from core.mouse_controller import MouseController
        
        capture = ScreenCapture(self.config["game_region"])
        board_detector = BoardDetector(
            self.config["light_cell_color"],
            self.config["dark_cell_color"],
            self.config.get("color_tolerance", 30)
        )
        
        templates_path = get_templates_path()
        piece_detector = PieceDetector(templates_path)
        ai_player = AIPlayer()
        mouse = MouseController()
        
        move_count = 0
        no_rook_count = 0
        max_no_rook_retries = 3
        
        self._safe_log("Bot loop started")
        
        while self.bot_running:
            if self.bot_paused:
                time.sleep(0.1)
                continue
                
            try:
                screenshot = capture.capture()
                if screenshot is None:
                    self._safe_log("Failed to capture screen")
                    time.sleep(1)
                    continue
                
                cells = board_detector.detect_cells(screenshot)
                if cells is None:
                    self._safe_log("Failed to detect board")
                    time.sleep(1)
                    continue
                
                board_state, rook_pos = piece_detector.detect_pieces(screenshot, cells)
                
                if rook_pos is None:
                    no_rook_count += 1
                    
                    if no_rook_count >= max_no_rook_retries:
                        self._safe_log("Player rook not found - checking for game over")
                        
                        self._safe_log("Game over or rook not detected - waiting...")
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
                    self._safe_log(f"WARNING: Rook at {rook_pos} is in danger!")
                
                if not valid_moves:
                    self._safe_log("No valid moves available")
                    time.sleep(0.5)
                    continue
                
                best_move = ai_player.select_best_move(valid_moves, board_state, danger_cells)
                
                if best_move:
                    target_row, target_col, is_capture = best_move
                    cell_info = cells[target_row][target_col]
                    click_x = cell_info["center_x"]
                    click_y = cell_info["center_y"]
                    
                    region = self.config["game_region"]
                    abs_x = region[0] + click_x
                    abs_y = region[1] + click_y
                    
                    action = "Capture" if is_capture else "Move"
                    target_in_danger = (target_row, target_col) in danger_cells
                    danger_warning = " [DANGER!]" if target_in_danger else ""
                    
                    self._safe_log(f"{action} to ({target_row}, {target_col}){danger_warning}")
                    
                    mouse.click(abs_x, abs_y)
                    move_count += 1
                    
                    current_count = move_count
                    self.root.after(0, lambda c=current_count: self.control_tab.update_move_count(c))
                
                delay = self.config.get("move_delay", 500) / 1000.0
                time.sleep(delay)
                
            except Exception as e:
                self._safe_log(f"Error: {str(e)}")
                import traceback
                traceback.print_exc()
                time.sleep(1)
                
        self._safe_log("Bot loop ended")
        
    def _safe_log(self, message):
        try:
            self.root.after(0, lambda m=message: self.log(m))
        except Exception:
            print(f"[LOG] {message}")
        
    def run(self):
        self.root.mainloop()
