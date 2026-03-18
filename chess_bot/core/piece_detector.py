import os
import cv2
import numpy as np
from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict


@dataclass
class Piece:
    type: str
    is_player: bool
    row: int
    col: int
    confidence: float = 0.0


class PieceDetector:
    PIECE_TYPES = {
        "rook_white": ("ROOK", True),
        "pawn_black": ("PAWN", False),
        "bishop_black": ("BISHOP", False),
        "knight_black": ("KNIGHT", False),
        "rook_black": ("ROOK", False),
        "queen_black": ("QUEEN", False),
        "king_black": ("KING", False),
    }

    def __init__(self, templates_path: str):
        self.templates_path = templates_path
        self.templates: Dict[str, np.ndarray] = {}
        self.threshold = 0.7
        self._load_templates()

    def _load_templates(self):
        if not os.path.exists(self.templates_path):
            os.makedirs(self.templates_path, exist_ok=True)
            return

        for filename in os.listdir(self.templates_path):
            if filename.endswith(('.png', '.jpg', '.jpeg')):
                name = os.path.splitext(filename)[0]
                filepath = os.path.join(self.templates_path, filename)
                template = cv2.imread(filepath)
                if template is not None:
                    self.templates[name] = template

    def add_template(self, name: str, image: np.ndarray):
        self.templates[name] = image
        filepath = os.path.join(self.templates_path, f"{name}.png")
        cv2.imwrite(filepath, image)

    def set_threshold(self, threshold: float):
        self.threshold = threshold

    def detect_pieces(self, screenshot: np.ndarray, cells: List[List[dict]]) -> Tuple[List[List[Optional[Piece]]], Optional[Tuple[int, int]]]:
        if screenshot is None or cells is None:
            return [[None] * 8 for _ in range(8)], None

        board_state = [[None for _ in range(8)] for _ in range(8)]
        player_rook_pos = None

        for template_name, template in self.templates.items():
            if template_name not in self.PIECE_TYPES:
                continue

            piece_type, is_player = self.PIECE_TYPES[template_name]

            locations = self._find_template(screenshot, template)

            for loc in locations:
                row, col = self._location_to_cell(loc, cells)
                if row is not None and col is not None:
                    if board_state[row][col] is None or locations[loc] > board_state[row][col].confidence:
                        piece = Piece(
                            type=piece_type,
                            is_player=is_player,
                            row=row,
                            col=col,
                            confidence=locations[loc]
                        )
                        board_state[row][col] = piece

                        if is_player and piece_type == "ROOK":
                            player_rook_pos = (row, col)

        if player_rook_pos is None:
            player_rook_pos = self._find_player_rook_by_color(screenshot, cells, board_state)

        return board_state, player_rook_pos

    def _find_template(self, screenshot: np.ndarray, template: np.ndarray) -> Dict[Tuple[int, int], float]:
        locations = {}

        if template.shape[0] > screenshot.shape[0] or template.shape[1] > screenshot.shape[1]:
            return locations

        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)

        loc = np.where(result >= self.threshold)

        for pt in zip(*loc[::-1]):
            center_x = pt[0] + template.shape[1] // 2
            center_y = pt[1] + template.shape[0] // 2

            is_duplicate = False
            for existing_loc in locations:
                if abs(existing_loc[0] - center_x) < 20 and abs(existing_loc[1] - center_y) < 20:
                    is_duplicate = True
                    if result[pt[1], pt[0]] > locations[existing_loc]:
                        del locations[existing_loc]
                        locations[(center_x, center_y)] = result[pt[1], pt[0]]
                    break

            if not is_duplicate:
                locations[(center_x, center_y)] = result[pt[1], pt[0]]

        return locations

    def _location_to_cell(self, location: Tuple[int, int], cells: List[List[dict]]) -> Tuple[Optional[int], Optional[int]]:
        x, y = location

        for row in range(8):
            for col in range(8):
                cell = cells[row][col]
                if cell is None:
                    continue

                cell_x = cell["x"]
                cell_y = cell["y"]
                cell_w = cell["width"]
                cell_h = cell["height"]

                # Mở rộng vùng detect lên trên 15% cho các quân cờ cao (Queen, King)
                # vì phần đầu quân cờ có thể vượt ra ngoài ô
                top_extension = int(cell_h * 0.15)

                if cell_x <= x < cell_x + cell_w and cell_y - top_extension <= y < cell_y + cell_h:
                    return row, col

        return None, None

    def _find_player_rook_by_color(self, screenshot: np.ndarray, cells: List[List[dict]], board_state: List[List[Optional[Piece]]]) -> Optional[Tuple[int, int]]:
        screenshot_hsv = cv2.cvtColor(screenshot, cv2.COLOR_BGR2HSV)

        lower_white = np.array([0, 0, 200])
        upper_white = np.array([180, 30, 255])

        for row in range(8):
            for col in range(8):
                if board_state[row][col] is not None:
                    continue

                cell = cells[row][col]
                if cell is None:
                    continue

                x = cell["x"]
                y = cell["y"]
                w = cell["width"]
                h = cell["height"]

                padding = int(w * 0.2)
                cell_region = screenshot_hsv[y+padding:y+h-padding, x+padding:x+w-padding]

                if cell_region.size == 0:
                    continue

                white_mask = cv2.inRange(cell_region, lower_white, upper_white)
                white_ratio = np.sum(white_mask > 0) / white_mask.size

                if white_ratio > 0.1:
                    piece = Piece(
                        type="ROOK",
                        is_player=True,
                        row=row,
                        col=col,
                        confidence=white_ratio
                    )
                    board_state[row][col] = piece
                    return (row, col)

        return None

    def detect_single_cell(self, cell_image: np.ndarray) -> Optional[Piece]:
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

            if scaled_template.shape[0] > cell_image.shape[0] or scaled_template.shape[1] > cell_image.shape[1]:
                continue

            result = cv2.matchTemplate(cell_image, scaled_template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)

            if max_val > self.threshold and max_val > best_confidence:
                piece_type, is_player = self.PIECE_TYPES[template_name]
                best_match = Piece(
                    type=piece_type,
                    is_player=is_player,
                    row=0,
                    col=0,
                    confidence=max_val
                )
                best_confidence = max_val

        return best_match
