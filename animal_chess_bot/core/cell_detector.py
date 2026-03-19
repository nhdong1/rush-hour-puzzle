import numpy as np
import cv2
from enum import Enum
from typing import Optional, List
from dataclasses import dataclass


class CellState(Enum):
    UNFLIPPED = "unflipped"
    FLIPPED = "flipped"
    EMPTY = "empty"
    UNKNOWN = "unknown"


@dataclass
class CellInfo:
    state: CellState
    row: int
    col: int
    confidence: float = 0.0


class CellDetector:
    """
    Detector for cell states in Animal Chess.
    Distinguishes between:
    - UNFLIPPED: Cell has not been revealed yet (shows back of card)
    - FLIPPED: Cell has been revealed and contains a piece
    - EMPTY: Cell was revealed but piece was captured (empty cell)
    """
    
    def __init__(self, templates_path: str = None):
        self.templates_path = templates_path
        self.unflipped_template = None
        self.unflipped_color = None
        self.flipped_color = None
        self.color_tolerance = 30
        self.template_threshold = 0.7
        
        if templates_path:
            self._load_unflipped_template()
    
    def _load_unflipped_template(self):
        """Load template for unflipped cell"""
        import os
        if self.templates_path:
            template_path = os.path.join(self.templates_path, "unflipped.png")
            if os.path.exists(template_path):
                self.unflipped_template = cv2.imread(template_path)
    
    def set_unflipped_color(self, color):
        """Set the color used to identify unflipped cells"""
        self.unflipped_color = np.array(color) if color else None
    
    def set_flipped_color(self, color):
        """Set the color used to identify flipped/empty cells"""
        self.flipped_color = np.array(color) if color else None
    
    def set_tolerance(self, tolerance: int):
        self.color_tolerance = tolerance
    
    def detect_cell_state(self, cell_image: np.ndarray) -> CellState:
        """
        Detect the state of a single cell.
        
        Args:
            cell_image: BGR image of the cell
            
        Returns:
            CellState enum value
        """
        if cell_image is None or cell_image.size == 0:
            return CellState.UNKNOWN
        
        if self.unflipped_template is not None:
            if self._match_template(cell_image, self.unflipped_template):
                return CellState.UNFLIPPED
        
        if self.unflipped_color is not None:
            if self._match_color(cell_image, self.unflipped_color):
                return CellState.UNFLIPPED
        
        if self._is_empty_cell(cell_image):
            return CellState.EMPTY
        
        return CellState.FLIPPED
    
    def detect_all_cells(self, screenshot: np.ndarray, 
                         cells: List[List[dict]]) -> List[List[CellInfo]]:
        """
        Detect states of all cells on the board.
        
        Args:
            screenshot: Full screenshot
            cells: Cell position info from BoardDetector
            
        Returns:
            2D list of CellInfo objects
        """
        from .board_detector import BOARD_SIZE
        
        result = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                cell_info = cells[row][col]
                if cell_info is None:
                    result[row][col] = CellInfo(
                        state=CellState.UNKNOWN,
                        row=row,
                        col=col
                    )
                    continue
                
                x = cell_info["x"]
                y = cell_info["y"]
                w = cell_info["width"]
                h = cell_info["height"]
                
                if (x >= 0 and y >= 0 and 
                    x + w <= screenshot.shape[1] and 
                    y + h <= screenshot.shape[0]):
                    cell_image = screenshot[y:y+h, x:x+w]
                    state = self.detect_cell_state(cell_image)
                else:
                    state = CellState.UNKNOWN
                
                result[row][col] = CellInfo(
                    state=state,
                    row=row,
                    col=col
                )
        
        return result
    
    def _match_template(self, cell_image: np.ndarray, 
                        template: np.ndarray) -> bool:
        """Check if cell matches a template"""
        if template is None:
            return False
        
        if (template.shape[0] > cell_image.shape[0] or 
            template.shape[1] > cell_image.shape[1]):
            scale = min(
                cell_image.shape[0] / template.shape[0],
                cell_image.shape[1] / template.shape[1]
            ) * 0.9
            template = cv2.resize(template, None, fx=scale, fy=scale)
        
        if (template.shape[0] > cell_image.shape[0] or 
            template.shape[1] > cell_image.shape[1]):
            return False
        
        result = cv2.matchTemplate(cell_image, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(result)
        
        return max_val >= self.template_threshold
    
    def _match_color(self, cell_image: np.ndarray, 
                     target_color: np.ndarray) -> bool:
        """Check if cell predominantly matches target color"""
        cell_rgb = cv2.cvtColor(cell_image, cv2.COLOR_BGR2RGB)
        
        lower = np.clip(target_color - self.color_tolerance, 0, 255)
        upper = np.clip(target_color + self.color_tolerance, 0, 255)
        
        mask = cv2.inRange(cell_rgb, lower, upper)
        
        match_ratio = np.sum(mask > 0) / mask.size
        
        return match_ratio > 0.3
    
    def _is_empty_cell(self, cell_image: np.ndarray) -> bool:
        """
        Check if cell is empty (no piece).
        Empty cells typically have uniform color or very low variance.
        """
        gray = cv2.cvtColor(cell_image, cv2.COLOR_BGR2GRAY)
        
        variance = np.var(gray)
        
        return variance < 100
    
    def get_unflipped_cells(self, cell_states: List[List[CellInfo]]) -> List[tuple]:
        """Get list of (row, col) for all unflipped cells"""
        unflipped = []
        for row in range(len(cell_states)):
            for col in range(len(cell_states[row])):
                if cell_states[row][col].state == CellState.UNFLIPPED:
                    unflipped.append((row, col))
        return unflipped
    
    def get_flipped_cells(self, cell_states: List[List[CellInfo]]) -> List[tuple]:
        """Get list of (row, col) for all flipped cells (with pieces)"""
        flipped = []
        for row in range(len(cell_states)):
            for col in range(len(cell_states[row])):
                if cell_states[row][col].state == CellState.FLIPPED:
                    flipped.append((row, col))
        return flipped
    
    def get_empty_cells(self, cell_states: List[List[CellInfo]]) -> List[tuple]:
        """Get list of (row, col) for all empty cells"""
        empty = []
        for row in range(len(cell_states)):
            for col in range(len(cell_states[row])):
                if cell_states[row][col].state == CellState.EMPTY:
                    empty.append((row, col))
        return empty
