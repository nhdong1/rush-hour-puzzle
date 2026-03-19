import numpy as np
import cv2
from typing import List, Optional, Tuple


BOARD_SIZE = 4


class BoardDetector:
    """
    Detector for 4x4 Animal Chess board with gaps between cells.
    Unlike regular chess board, cells are not contiguous.
    """
    
    def __init__(self, cell_color=None, tolerance=30, manual_gap=None):
        self.cell_color = np.array(cell_color) if cell_color else None
        self.tolerance = tolerance
        self.manual_gap = manual_gap
        
        self.cell_size = None
        self.gap_size = None
        self.board_offset_x = 0
        self.board_offset_y = 0
        
    def set_cell_color(self, cell_color):
        self.cell_color = np.array(cell_color) if cell_color else None
        
    def set_tolerance(self, tolerance):
        self.tolerance = tolerance
        
    def set_manual_gap(self, gap):
        """Set manual gap size (in pixels). Set to None to use auto detection."""
        self.manual_gap = gap
        
    def detect_cells(self, screenshot) -> Optional[List[List[dict]]]:
        """
        Detect 16 cells (4x4) in the screenshot.
        Returns cells[row][col] with position info for each cell.
        """
        if screenshot is None:
            return None
            
        height, width = screenshot.shape[:2]
        
        if self.cell_color is not None:
            cells = self._detect_by_color(screenshot)
            if cells is not None:
                return cells
        
        return self._fallback_grid_detection(width, height)
    
    def _detect_by_color(self, screenshot) -> Optional[List[List[dict]]]:
        """Detect cells by color matching"""
        screenshot_rgb = cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB)
        
        mask = self._create_color_mask(screenshot_rgb, self.cell_color)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if len(contours) < 16:
            return None
        
        cell_rects = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 100:
                continue
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / h if h > 0 else 0
            if 0.5 < aspect_ratio < 2.0:
                cell_rects.append((x, y, w, h, area))
        
        if len(cell_rects) < 16:
            return None
        
        cell_rects.sort(key=lambda r: r[4], reverse=True)
        cell_rects = cell_rects[:16]
        
        cell_rects.sort(key=lambda r: (r[1], r[0]))
        
        cells = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        
        rows = []
        current_row = [cell_rects[0]]
        y_threshold = cell_rects[0][3] * 0.5
        
        for rect in cell_rects[1:]:
            if abs(rect[1] - current_row[0][1]) < y_threshold:
                current_row.append(rect)
            else:
                rows.append(sorted(current_row, key=lambda r: r[0]))
                current_row = [rect]
        rows.append(sorted(current_row, key=lambda r: r[0]))
        
        if len(rows) != BOARD_SIZE:
            return None
        
        for row_idx, row in enumerate(rows):
            if len(row) != BOARD_SIZE:
                return None
            for col_idx, (x, y, w, h, _) in enumerate(row):
                cells[row_idx][col_idx] = {
                    "x": x,
                    "y": y,
                    "width": w,
                    "height": h,
                    "center_x": x + w // 2,
                    "center_y": y + h // 2
                }
        
        if cells[0][0] and cells[0][1]:
            self.cell_size = cells[0][0]["width"]
            self.gap_size = cells[0][1]["x"] - (cells[0][0]["x"] + cells[0][0]["width"])
            self.board_offset_x = cells[0][0]["x"]
            self.board_offset_y = cells[0][0]["y"]
        
        return cells
        
    def _create_color_mask(self, image, target_color):
        """Create mask for target color with tolerance"""
        lower = np.clip(target_color - self.tolerance, 0, 255)
        upper = np.clip(target_color + self.tolerance, 0, 255)
        
        mask = cv2.inRange(image, lower, upper)
        
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        return mask
        
    def _fallback_grid_detection(self, width, height) -> List[List[dict]]:
        """
        Fallback: assume uniform grid with gaps.
        Estimate cell size and gap based on image dimensions.
        If manual_gap is set, use that value instead of estimating.
        """
        total_cells = BOARD_SIZE
        
        total_width = width
        total_height = height
        
        if self.manual_gap is not None:
            self.gap_size = self.manual_gap
            total_gap_width = self.gap_size * (BOARD_SIZE - 1)
            self.cell_size = int((min(total_width, total_height) - total_gap_width) / total_cells)
        else:
            estimated_gap_ratio = 0.1
            cell_plus_gap = min(total_width, total_height) / total_cells
            self.gap_size = int(cell_plus_gap * estimated_gap_ratio)
            self.cell_size = int(cell_plus_gap - self.gap_size)
        
        total_board_width = self.cell_size * BOARD_SIZE + self.gap_size * (BOARD_SIZE - 1)
        total_board_height = self.cell_size * BOARD_SIZE + self.gap_size * (BOARD_SIZE - 1)
        
        self.board_offset_x = (width - total_board_width) // 2
        self.board_offset_y = (height - total_board_height) // 2
        
        cells = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                cell_x = self.board_offset_x + col * (self.cell_size + self.gap_size)
                cell_y = self.board_offset_y + row * (self.cell_size + self.gap_size)
                
                cells[row][col] = {
                    "x": cell_x,
                    "y": cell_y,
                    "width": self.cell_size,
                    "height": self.cell_size,
                    "center_x": cell_x + self.cell_size // 2,
                    "center_y": cell_y + self.cell_size // 2
                }
                
        return cells
        
    def get_cell_image(self, screenshot, row: int, col: int, cells: List[List[dict]]) -> Optional[np.ndarray]:
        """Extract image of a specific cell from screenshot"""
        if cells is None or row >= BOARD_SIZE or col >= BOARD_SIZE:
            return None
            
        cell_info = cells[row][col]
        if cell_info is None:
            return None
            
        x = cell_info["x"]
        y = cell_info["y"]
        w = cell_info["width"]
        h = cell_info["height"]
        
        padding = int(min(w, h) * 0.05)
        x += padding
        y += padding
        w -= 2 * padding
        h -= 2 * padding
        
        if x < 0 or y < 0:
            return None
        if x + w > screenshot.shape[1] or y + h > screenshot.shape[0]:
            return None
            
        return screenshot[y:y+h, x:x+w]
    
    def get_cell_center(self, row: int, col: int, cells: List[List[dict]]) -> Optional[Tuple[int, int]]:
        """Get center coordinates of a cell"""
        if cells is None or row >= BOARD_SIZE or col >= BOARD_SIZE:
            return None
        
        cell_info = cells[row][col]
        if cell_info is None:
            return None
            
        return (cell_info["center_x"], cell_info["center_y"])
