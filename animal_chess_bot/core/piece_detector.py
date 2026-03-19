import os
import cv2
import numpy as np
from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict

from .board_detector import BOARD_SIZE


PIECE_POWER = {
    "mouse": 1,
    "cat": 2,
    "dog": 3,
    "fox": 4,
    "wolf": 5,
    "tiger": 6,
    "lion": 7,
    "elephant": 8,
}

PIECE_NAMES = list(PIECE_POWER.keys())


@dataclass
class Piece:
    type: str
    is_blue: bool
    power: int
    row: int
    col: int
    confidence: float = 0.0
    
    def __repr__(self):
        color = "Blue" if self.is_blue else "Red"
        return f"{color} {self.type.capitalize()} at ({self.row}, {self.col})"


class PieceDetector:
    """
    Detector for Animal Chess pieces.
    Recognizes 8 types of pieces for both blue and red teams.
    """
    
    PIECE_TYPES = {}
    for piece_name in PIECE_NAMES:
        PIECE_TYPES[f"{piece_name}_blue"] = (piece_name, True)
        PIECE_TYPES[f"{piece_name}_red"] = (piece_name, False)
    
    SCALE_FACTORS = [0.85, 0.90, 0.95, 1.0, 1.05, 1.10, 1.15]
    
    def __init__(self, templates_path: str):
        self.templates_path = templates_path
        self.templates: Dict[str, np.ndarray] = {}
        self.templates_multi_scale: Dict[str, List[np.ndarray]] = {}
        self.threshold = 0.7
        self._load_templates()
    
    def _load_templates(self):
        """Load all piece templates from templates folder"""
        if not os.path.exists(self.templates_path):
            os.makedirs(self.templates_path, exist_ok=True)
            return
        
        for filename in os.listdir(self.templates_path):
            if filename.endswith(('.png', '.jpg', '.jpeg')):
                name = os.path.splitext(filename)[0]
                if name in self.PIECE_TYPES:
                    filepath = os.path.join(self.templates_path, filename)
                    template = cv2.imread(filepath)
                    if template is not None:
                        self.templates[name] = template
                        self._create_multi_scale_templates(name, template)
    
    def _create_multi_scale_templates(self, name: str, template: np.ndarray):
        """Create multiple scaled versions of template for better matching"""
        self.templates_multi_scale[name] = []
        
        for scale in self.SCALE_FACTORS:
            if scale == 1.0:
                self.templates_multi_scale[name].append(template)
            else:
                scaled = cv2.resize(
                    template,
                    None,
                    fx=scale,
                    fy=scale,
                    interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR
                )
                self.templates_multi_scale[name].append(scaled)
    
    def reload_templates(self):
        """Reload templates from disk"""
        self.templates.clear()
        self.templates_multi_scale.clear()
        self._load_templates()
    
    def set_threshold(self, threshold: float):
        self.threshold = threshold
    
    def detect_pieces(self, screenshot: np.ndarray, 
                      cells: List[List[dict]]) -> List[List[Optional[Piece]]]:
        """
        Detect all pieces on the board.
        
        Args:
            screenshot: Full screenshot
            cells: Cell position info from BoardDetector
            
        Returns:
            2D list where each element is a Piece or None
        """
        if screenshot is None or cells is None:
            return [[None] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        
        board_state = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        cell_candidates: Dict[Tuple[int, int], List[Tuple[str, float]]] = {}
        
        for template_name, template in self.templates.items():
            if template_name not in self.PIECE_TYPES:
                continue
            
            locations = self._find_template_multi_scale(screenshot, template_name)
            
            for loc, confidence in locations.items():
                row, col = self._location_to_cell(loc, cells)
                if row is not None and col is not None:
                    cell_key = (row, col)
                    if cell_key not in cell_candidates:
                        cell_candidates[cell_key] = []
                    cell_candidates[cell_key].append((template_name, confidence))
        
        for (row, col), candidates in cell_candidates.items():
            best_piece = self._resolve_piece_conflict(candidates)
            if best_piece:
                template_name, confidence = best_piece
                piece_type, is_blue = self.PIECE_TYPES[template_name]
                piece = Piece(
                    type=piece_type,
                    is_blue=is_blue,
                    power=PIECE_POWER[piece_type],
                    row=row,
                    col=col,
                    confidence=confidence
                )
                board_state[row][col] = piece
        
        return board_state
    
    def _find_template_multi_scale(self, screenshot: np.ndarray, 
                                    template_name: str) -> Dict[Tuple[int, int], float]:
        """Multi-scale template matching"""
        best_locations = {}
        
        templates = self.templates_multi_scale.get(template_name, [self.templates.get(template_name)])
        if templates is None or templates[0] is None:
            return best_locations
        
        for template in templates:
            if template is None:
                continue
            locations = self._find_template(screenshot, template)
            for loc, conf in locations.items():
                matched = False
                for existing_loc in list(best_locations.keys()):
                    if abs(existing_loc[0] - loc[0]) < 25 and abs(existing_loc[1] - loc[1]) < 25:
                        if conf > best_locations[existing_loc]:
                            del best_locations[existing_loc]
                            best_locations[loc] = conf
                        matched = True
                        break
                if not matched:
                    best_locations[loc] = conf
        
        return best_locations
    
    def _find_template(self, screenshot: np.ndarray, 
                       template: np.ndarray) -> Dict[Tuple[int, int], float]:
        """Find template in screenshot"""
        locations = {}
        
        if (template.shape[0] > screenshot.shape[0] or 
            template.shape[1] > screenshot.shape[1]):
            return locations
        
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        
        loc = np.where(result >= self.threshold)
        
        for pt in zip(*loc[::-1]):
            center_x = pt[0] + template.shape[1] // 2
            center_y = pt[1] + template.shape[0] // 2
            
            is_duplicate = False
            for existing_loc in list(locations.keys()):
                if abs(existing_loc[0] - center_x) < 20 and abs(existing_loc[1] - center_y) < 20:
                    is_duplicate = True
                    if result[pt[1], pt[0]] > locations[existing_loc]:
                        del locations[existing_loc]
                        locations[(center_x, center_y)] = result[pt[1], pt[0]]
                    break
            
            if not is_duplicate:
                locations[(center_x, center_y)] = result[pt[1], pt[0]]
        
        return locations
    
    def _location_to_cell(self, location: Tuple[int, int], 
                          cells: List[List[dict]]) -> Tuple[Optional[int], Optional[int]]:
        """Convert pixel location to cell coordinates"""
        x, y = location
        
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                cell = cells[row][col]
                if cell is None:
                    continue
                
                cell_x = cell["x"]
                cell_y = cell["y"]
                cell_w = cell["width"]
                cell_h = cell["height"]
                
                top_extension = int(cell_h * 0.15)
                
                if (cell_x <= x < cell_x + cell_w and 
                    cell_y - top_extension <= y < cell_y + cell_h):
                    return row, col
        
        return None, None
    
    def _resolve_piece_conflict(self, candidates: List[Tuple[str, float]]) -> Optional[Tuple[str, float]]:
        """Resolve conflict when multiple pieces match same cell"""
        if not candidates:
            return None
        
        if len(candidates) == 1:
            return candidates[0]
        
        candidates_sorted = sorted(candidates, key=lambda x: x[1], reverse=True)
        return candidates_sorted[0]
    
    def detect_single_cell(self, cell_image: np.ndarray) -> Optional[Piece]:
        """Detect piece in a single cell image"""
        if cell_image is None or cell_image.size == 0:
            return None
        
        best_match = None
        best_confidence = 0
        
        for template_name, template in self.templates.items():
            if template_name not in self.PIECE_TYPES:
                continue
            
            scale = min(
                cell_image.shape[0] / template.shape[0],
                cell_image.shape[1] / template.shape[1]
            )
            
            if scale < 0.3 or scale > 3.0:
                continue
            
            scaled_template = cv2.resize(
                template,
                None,
                fx=scale,
                fy=scale,
                interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR
            )
            
            if (scaled_template.shape[0] > cell_image.shape[0] or 
                scaled_template.shape[1] > cell_image.shape[1]):
                continue
            
            result = cv2.matchTemplate(cell_image, scaled_template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)
            
            if max_val > self.threshold and max_val > best_confidence:
                piece_type, is_blue = self.PIECE_TYPES[template_name]
                best_match = Piece(
                    type=piece_type,
                    is_blue=is_blue,
                    power=PIECE_POWER[piece_type],
                    row=0,
                    col=0,
                    confidence=max_val
                )
                best_confidence = max_val
        
        return best_match
    
    def get_blue_pieces(self, board_state: List[List[Optional[Piece]]]) -> List[Piece]:
        """Get all blue pieces on the board"""
        pieces = []
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = board_state[row][col]
                if piece and piece.is_blue:
                    pieces.append(piece)
        return pieces
    
    def get_red_pieces(self, board_state: List[List[Optional[Piece]]]) -> List[Piece]:
        """Get all red pieces on the board"""
        pieces = []
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = board_state[row][col]
                if piece and not piece.is_blue:
                    pieces.append(piece)
        return pieces
