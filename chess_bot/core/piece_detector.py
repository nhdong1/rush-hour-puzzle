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

    # Threshold riêng cho từng loại quân - quân dễ nhầm cần threshold cao hơn
    PIECE_THRESHOLDS = {
        "bishop_black": 0.80,  # Bishop dễ nhầm với Pawn nên cần threshold cao
        "pawn_black": 0.75,    # Pawn cũng cần threshold cao hơn
        "knight_black": 0.75,  # Knight có hình dạng đặc trưng
        "queen_black": 0.72,
        "king_black": 0.72,
        "rook_white": 0.70,
        "rook_black": 0.70,
    }

    # Priority khi cùng một ô có nhiều match - quân lớn hơn được ưu tiên kiểm tra trước
    PIECE_PRIORITY = {
        "queen_black": 1,
        "king_black": 2,
        "rook_black": 3,
        "rook_white": 3,
        "bishop_black": 4,
        "knight_black": 5,
        "pawn_black": 6,
    }

    def __init__(self, templates_path: str):
        self.templates_path = templates_path
        self.templates: Dict[str, np.ndarray] = {}
        self.templates_multi_scale: Dict[str, List[np.ndarray]] = {}  # Multi-scale templates
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
                    # Tạo multi-scale templates cho các quân dễ nhầm lẫn
                    self._create_multi_scale_templates(name, template)

    def _create_multi_scale_templates(self, name: str, template: np.ndarray):
        """Tạo nhiều phiên bản scaled của template để matching tốt hơn với 3D pieces"""
        scales = [0.85, 0.90, 0.95, 1.0, 1.05, 1.10, 1.15]
        self.templates_multi_scale[name] = []

        for scale in scales:
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
        # Lưu tất cả candidates cho mỗi ô để conflict resolution
        cell_candidates: Dict[Tuple[int, int], List[Tuple[str, float]]] = {}
        player_rook_pos = None

        # Sắp xếp templates theo priority (quân lớn trước)
        sorted_templates = sorted(
            self.templates.items(),
            key=lambda x: self.PIECE_PRIORITY.get(x[0], 99)
        )

        for template_name, template in sorted_templates:
            if template_name not in self.PIECE_TYPES:
                continue

            piece_type, is_player = self.PIECE_TYPES[template_name]
            # Sử dụng threshold riêng cho từng loại quân
            piece_threshold = self.PIECE_THRESHOLDS.get(template_name, self.threshold)

            # Multi-scale matching
            locations = self._find_template_multi_scale(screenshot, template_name, piece_threshold)

            for loc in locations:
                row, col = self._location_to_cell(loc, cells)
                if row is not None and col is not None:
                    cell_key = (row, col)
                    if cell_key not in cell_candidates:
                        cell_candidates[cell_key] = []
                    cell_candidates[cell_key].append((template_name, locations[loc]))

        # Conflict resolution - chọn piece tốt nhất cho mỗi ô
        for (row, col), candidates in cell_candidates.items():
            best_piece = self._resolve_piece_conflict(candidates)
            if best_piece:
                template_name, confidence = best_piece
                piece_type, is_player = self.PIECE_TYPES[template_name]
                piece = Piece(
                    type=piece_type,
                    is_player=is_player,
                    row=row,
                    col=col,
                    confidence=confidence
                )
                board_state[row][col] = piece

                if is_player and piece_type == "ROOK":
                    player_rook_pos = (row, col)

        if player_rook_pos is None:
            player_rook_pos = self._find_player_rook_by_color(screenshot, cells, board_state)

        return board_state, player_rook_pos

    def _find_template_multi_scale(self, screenshot: np.ndarray, template_name: str, threshold: float) -> Dict[Tuple[int, int], float]:
        """Multi-scale template matching để tăng độ chính xác với 3D pieces"""
        best_locations = {}

        templates = self.templates_multi_scale.get(template_name, [self.templates[template_name]])

        for template in templates:
            locations = self._find_template(screenshot, template, threshold)
            for loc, conf in locations.items():
                # Giữ lại match tốt nhất cho mỗi vị trí
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

    def _resolve_piece_conflict(self, candidates: List[Tuple[str, float]]) -> Optional[Tuple[str, float]]:
        """
        Giải quyết xung đột khi nhiều quân match cùng 1 ô.
        Đặc biệt xử lý trường hợp bishop vs pawn.
        """
        if not candidates:
            return None

        if len(candidates) == 1:
            return candidates[0]

        # Tìm candidate có confidence cao nhất
        candidates_sorted = sorted(candidates, key=lambda x: x[1], reverse=True)
        best = candidates_sorted[0]
        second = candidates_sorted[1] if len(candidates_sorted) > 1 else None

        # Xử lý đặc biệt cho bishop vs pawn
        if second:
            best_name, best_conf = best
            second_name, second_conf = second

            is_bishop_pawn_conflict = (
                ('bishop' in best_name.lower() and 'pawn' in second_name.lower()) or
                ('pawn' in best_name.lower() and 'bishop' in second_name.lower())
            )

            if is_bishop_pawn_conflict:
                # Cần difference đủ lớn (>0.05) để chắc chắn
                confidence_diff = best_conf - second_conf
                if confidence_diff < 0.05:
                    # Confidence quá gần nhau, ưu tiên pawn vì phổ biến hơn
                    for name, conf in candidates_sorted:
                        if 'pawn' in name.lower():
                            return (name, conf)
                # Nếu difference đủ lớn, chọn best
                return best

        return best

    def _find_template(self, screenshot: np.ndarray, template: np.ndarray, threshold: float = None) -> Dict[Tuple[int, int], float]:
        locations = {}
        if threshold is None:
            threshold = self.threshold

        if template.shape[0] > screenshot.shape[0] or template.shape[1] > screenshot.shape[1]:
            return locations

        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)

        loc = np.where(result >= threshold)

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
