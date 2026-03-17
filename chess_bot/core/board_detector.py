import numpy as np
import cv2


class BoardDetector:
    BOARD_SIZE = 8
    
    def __init__(self, light_color, dark_color, tolerance=30):
        self.light_color = np.array(light_color) if light_color else None
        self.dark_color = np.array(dark_color) if dark_color else None
        self.tolerance = tolerance
        
        self.cell_size = None
        self.board_offset_x = 0
        self.board_offset_y = 0
        
    def set_colors(self, light_color, dark_color):
        self.light_color = np.array(light_color) if light_color else None
        self.dark_color = np.array(dark_color) if dark_color else None
        
    def set_tolerance(self, tolerance):
        self.tolerance = tolerance
        
    def detect_cells(self, screenshot):
        if screenshot is None:
            return None
        if self.light_color is None or self.dark_color is None:
            return None
            
        height, width = screenshot.shape[:2]
        
        screenshot_rgb = cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB)
        
        light_mask = self._create_color_mask(screenshot_rgb, self.light_color)
        dark_mask = self._create_color_mask(screenshot_rgb, self.dark_color)
        
        combined_mask = cv2.bitwise_or(light_mask, dark_mask)
        
        contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return self._fallback_grid_detection(width, height)
            
        all_points = np.vstack(contours)
        x, y, w, h = cv2.boundingRect(all_points)
        
        self.cell_size = min(w, h) // self.BOARD_SIZE
        self.board_offset_x = x
        self.board_offset_y = y
        
        if self.cell_size < 10:
            return self._fallback_grid_detection(width, height)
            
        cells = {}
        for row in range(self.BOARD_SIZE):
            for col in range(self.BOARD_SIZE):
                cell_x = self.board_offset_x + col * self.cell_size
                cell_y = self.board_offset_y + row * self.cell_size
                
                center_x = cell_x + self.cell_size // 2
                center_y = cell_y + self.cell_size // 2
                
                cells[(row, col)] = {
                    "x": cell_x,
                    "y": cell_y,
                    "width": self.cell_size,
                    "height": self.cell_size,
                    "center_x": center_x,
                    "center_y": center_y
                }
                
        cells = self._convert_to_2d_array(cells)
        return cells
        
    def _create_color_mask(self, image, target_color):
        lower = np.clip(target_color - self.tolerance, 0, 255)
        upper = np.clip(target_color + self.tolerance, 0, 255)
        
        mask = cv2.inRange(image, lower, upper)
        
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        return mask
        
    def _fallback_grid_detection(self, width, height):
        self.cell_size = min(width, height) // self.BOARD_SIZE
        self.board_offset_x = (width - self.cell_size * self.BOARD_SIZE) // 2
        self.board_offset_y = (height - self.cell_size * self.BOARD_SIZE) // 2
        
        cells = {}
        for row in range(self.BOARD_SIZE):
            for col in range(self.BOARD_SIZE):
                cell_x = self.board_offset_x + col * self.cell_size
                cell_y = self.board_offset_y + row * self.cell_size
                
                center_x = cell_x + self.cell_size // 2
                center_y = cell_y + self.cell_size // 2
                
                cells[(row, col)] = {
                    "x": cell_x,
                    "y": cell_y,
                    "width": self.cell_size,
                    "height": self.cell_size,
                    "center_x": center_x,
                    "center_y": center_y
                }
                
        return self._convert_to_2d_array(cells)
        
    def _convert_to_2d_array(self, cells_dict):
        cells = [[None for _ in range(self.BOARD_SIZE)] for _ in range(self.BOARD_SIZE)]
        for (row, col), cell_info in cells_dict.items():
            cells[row][col] = cell_info
        return cells
        
    def get_cell_image(self, screenshot, row, col, cells):
        if cells is None or row >= len(cells) or col >= len(cells[0]):
            return None
            
        cell_info = cells[row][col]
        if cell_info is None:
            return None
            
        x = cell_info["x"]
        y = cell_info["y"]
        w = cell_info["width"]
        h = cell_info["height"]
        
        padding = int(w * 0.1)
        x += padding
        y += padding
        w -= 2 * padding
        h -= 2 * padding
        
        if x < 0 or y < 0:
            return None
        if x + w > screenshot.shape[1] or y + h > screenshot.shape[0]:
            return None
            
        return screenshot[y:y+h, x:x+w]
