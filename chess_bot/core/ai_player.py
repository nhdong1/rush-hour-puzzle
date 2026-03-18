from typing import List, Optional, Tuple, Set
from dataclasses import dataclass
import copy


PIECE_VALUES = {
    'PAWN': 1,
    'BISHOP': 3,
    'KNIGHT': 3,
    'ROOK': 5,
    'QUEEN': 9,
    'KING': 10
}

BOARD_SIZE = 8
MAX_DEPTH = 3  # Độ sâu tối đa cho minimax
INF = float('inf')


class AIPlayer:
    def __init__(self, depth: int = MAX_DEPTH):
        self.last_position = None
        self.position_history = []
        self.safety_threshold = 0.7
        self.repeat_move_count = 0
        self.search_depth = depth

    def get_valid_moves(self, rook_pos: Tuple[int, int], board_state: List[List]) -> List[Tuple[int, int, bool]]:
        if rook_pos is None:
            return []

        moves = []
        row, col = rook_pos
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        for dr, dc in directions:
            for i in range(1, BOARD_SIZE):
                nr, nc = row + dr * i, col + dc * i

                if not self._is_valid_pos(nr, nc):
                    break

                piece = board_state[nr][nc]

                if piece is None:
                    moves.append((nr, nc, False))
                elif not piece.is_player:
                    moves.append((nr, nc, True))
                    break
                else:
                    break

        return moves

    def get_danger_cells(self, board_state: List[List]) -> Set[Tuple[int, int]]:
        danger = set()

        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = board_state[row][col]
                if piece and not piece.is_player:
                    attacks = self._get_attack_moves(row, col, piece.type, board_state)
                    danger.update(attacks)

        return danger

    def _get_attack_moves(self, row: int, col: int, piece_type: str, board_state: List[List]) -> List[Tuple[int, int]]:
        attacks = []

        if piece_type == 'PAWN':
            pawn_attacks = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
            for dr, dc in pawn_attacks:
                nr, nc = row + dr, col + dc
                if self._is_valid_pos(nr, nc):
                    attacks.append((nr, nc))

        elif piece_type == 'BISHOP':
            bishop_dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
            for dr, dc in bishop_dirs:
                for i in range(1, BOARD_SIZE):
                    nr, nc = row + dr * i, col + dc * i
                    if not self._is_valid_pos(nr, nc):
                        break
                    attacks.append((nr, nc))
                    if board_state[nr][nc] is not None:
                        break

        elif piece_type == 'KNIGHT':
            knight_moves = [
                (-2, -1), (-2, 1), (-1, -2), (-1, 2),
                (1, -2), (1, 2), (2, -1), (2, 1)
            ]
            for dr, dc in knight_moves:
                nr, nc = row + dr, col + dc
                if self._is_valid_pos(nr, nc):
                    attacks.append((nr, nc))

        elif piece_type == 'ROOK':
            rook_dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            for dr, dc in rook_dirs:
                for i in range(1, BOARD_SIZE):
                    nr, nc = row + dr * i, col + dc * i
                    if not self._is_valid_pos(nr, nc):
                        break
                    attacks.append((nr, nc))
                    if board_state[nr][nc] is not None:
                        break

        elif piece_type == 'QUEEN':
            queen_dirs = [
                (-1, 0), (1, 0), (0, -1), (0, 1),
                (-1, -1), (-1, 1), (1, -1), (1, 1)
            ]
            for dr, dc in queen_dirs:
                for i in range(1, BOARD_SIZE):
                    nr, nc = row + dr * i, col + dc * i
                    if not self._is_valid_pos(nr, nc):
                        break
                    attacks.append((nr, nc))
                    if board_state[nr][nc] is not None:
                        break

        elif piece_type == 'KING':
            king_dirs = [
                (-1, 0), (1, 0), (0, -1), (0, 1),
                (-1, -1), (-1, 1), (1, -1), (1, 1)
            ]
            for dr, dc in king_dirs:
                nr, nc = row + dr, col + dc
                if self._is_valid_pos(nr, nc):
                    attacks.append((nr, nc))

        return attacks

    def _is_valid_pos(self, row: int, col: int) -> bool:
        return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE

    def select_best_move(self, valid_moves: List[Tuple[int, int, bool]],
                         board_state: List[List],
                         danger_cells: Set[Tuple[int, int]],
                         rook_pos: Tuple[int, int] = None) -> Optional[Tuple[int, int, bool]]:
        """Chọn nước đi tốt nhất sử dụng minimax với alpha-beta pruning."""
        if not valid_moves:
            return None

        if rook_pos is None:
            rook_pos = self.last_position

        if rook_pos is None:
            return valid_moves[0]

        # Phân loại nước đi: an toàn vs tự sát
        safe_moves = []
        suicide_moves = []

        for move in valid_moves:
            target_row, target_col, is_capture = move

            # Mô phỏng nước đi
            new_board, captured_piece = self._simulate_move(
                board_state, rook_pos, (target_row, target_col), is_capture
            )

            # Tính danger sau khi đi
            future_danger = self.get_danger_cells(new_board)

            # Kiểm tra nếu ô đích bị tấn công sau khi đi
            if (target_row, target_col) in future_danger:
                suicide_moves.append((move, new_board, captured_piece))
            else:
                safe_moves.append((move, new_board, captured_piece))

        # Ưu tiên nước an toàn, chỉ xét nước tự sát khi không còn lựa chọn
        moves_to_evaluate = safe_moves if safe_moves else suicide_moves

        best_move = None
        best_score = -INF
        alpha = -INF
        beta = INF

        for move, new_board, captured_piece in moves_to_evaluate:
            target_row, target_col, is_capture = move
            new_rook_pos = (target_row, target_col)

            # Tính điểm bằng minimax
            score = self._minimax(
                new_board, new_rook_pos,
                depth=self.search_depth - 1,
                alpha=alpha, beta=beta,
                is_maximizing=False
            )

            # Cộng thêm điểm ăn quân ngay lập tức
            if is_capture and captured_piece:
                score += PIECE_VALUES.get(captured_piece.type, 1) * 20

            if score > best_score:
                best_score = score
                best_move = move

            alpha = max(alpha, score)

        return best_move

    def _minimax(self, board_state: List[List], rook_pos: Tuple[int, int],
                 depth: int, alpha: float, beta: float,
                 is_maximizing: bool) -> float:
        """
        Minimax với alpha-beta pruning.
        - is_maximizing=True: Lượt của player (tối đa hóa điểm)
        - is_maximizing=False: Lượt của đối thủ (tối thiểu hóa điểm player)
        """
        # Kiểm tra game over
        danger_cells = self.get_danger_cells(board_state)
        if rook_pos in danger_cells:
            return -10000 if is_maximizing else -10000  # Rook bị ăn = thua

        # Đạt độ sâu tối đa
        if depth <= 0:
            return self._evaluate_board(board_state, rook_pos, danger_cells)

        if is_maximizing:
            # Lượt player: tối đa hóa
            max_eval = -INF
            valid_moves = self.get_valid_moves(rook_pos, board_state)

            if not valid_moves:
                return self._evaluate_board(board_state, rook_pos, danger_cells)

            for move in valid_moves:
                target_row, target_col, is_capture = move

                new_board, captured = self._simulate_move(
                    board_state, rook_pos, (target_row, target_col), is_capture
                )
                new_rook_pos = (target_row, target_col)

                eval_score = self._minimax(
                    new_board, new_rook_pos,
                    depth - 1, alpha, beta, False
                )

                # Cộng điểm ăn quân
                if is_capture and captured:
                    eval_score += PIECE_VALUES.get(captured.type, 1) * 10

                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)

                if beta <= alpha:
                    break  # Beta cut-off

            return max_eval
        else:
            # Lượt đối thủ: tối thiểu hóa điểm player
            min_eval = INF
            enemy_moves = self._get_all_enemy_moves(board_state)

            if not enemy_moves:
                return self._evaluate_board(board_state, rook_pos, danger_cells)

            for enemy_move in enemy_moves:
                from_pos, to_pos, piece = enemy_move

                new_board = self._simulate_enemy_move(board_state, from_pos, to_pos)

                # Kiểm tra nếu enemy ăn được rook
                if to_pos == rook_pos:
                    return -10000  # Player thua

                eval_score = self._minimax(
                    new_board, rook_pos,
                    depth - 1, alpha, beta, True
                )

                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)

                if beta <= alpha:
                    break  # Alpha cut-off

            return min_eval

    def _evaluate_board(self, board_state: List[List], rook_pos: Tuple[int, int],
                        danger_cells: Set[Tuple[int, int]]) -> float:
        """Đánh giá trạng thái bàn cờ."""
        score = 0.0

        # Phạt nếu đang ở ô nguy hiểm
        if rook_pos in danger_cells:
            score -= 500

        # Số ô trốn an toàn
        escape_routes = self._count_safe_escapes(rook_pos[0], rook_pos[1], board_state, danger_cells)
        score += escape_routes * 15

        # Ưu tiên trung tâm
        center_dist = abs(rook_pos[0] - 3.5) + abs(rook_pos[1] - 3.5)
        score += (7 - center_dist) * 2

        # Phạt lặp vị trí
        if self.last_position and rook_pos == self.last_position:
            score -= 5
        position_count = self.position_history.count(rook_pos)
        score -= position_count * 2.5

        return score

    def _simulate_move(self, board_state: List[List], from_pos: Tuple[int, int],
                       to_pos: Tuple[int, int], is_capture: bool):
        """Mô phỏng nước đi của player, trả về board mới và quân bị ăn."""
        new_board = [row[:] for row in board_state]  # Deep copy

        captured_piece = None
        if is_capture:
            captured_piece = new_board[to_pos[0]][to_pos[1]]

        # Di chuyển rook (rook không có trong board_state vì nó được track riêng)
        new_board[to_pos[0]][to_pos[1]] = None  # Clear target (nếu có quân bị ăn)

        return new_board, captured_piece

    def _simulate_enemy_move(self, board_state: List[List],
                             from_pos: Tuple[int, int], to_pos: Tuple[int, int]):
        """Mô phỏng nước đi của quân địch."""
        new_board = [row[:] for row in board_state]

        piece = new_board[from_pos[0]][from_pos[1]]
        new_board[from_pos[0]][from_pos[1]] = None
        new_board[to_pos[0]][to_pos[1]] = piece

        return new_board

    def _get_all_enemy_moves(self, board_state: List[List]) -> List[Tuple[Tuple[int, int], Tuple[int, int], any]]:
        """Lấy tất cả nước đi có thể của quân địch."""
        moves = []

        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = board_state[row][col]
                if piece and not piece.is_player:
                    piece_moves = self._get_piece_moves(row, col, piece.type, board_state)
                    for to_pos in piece_moves:
                        moves.append(((row, col), to_pos, piece))

        return moves

    def _get_piece_moves(self, row: int, col: int, piece_type: str,
                         board_state: List[List]) -> List[Tuple[int, int]]:
        """Lấy các nước đi hợp lệ của một quân cờ."""
        moves = []

        if piece_type == 'PAWN':
            # Tốt di chuyển 4 hướng (theo requirement)
            pawn_dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            for dr, dc in pawn_dirs:
                nr, nc = row + dr, col + dc
                if self._is_valid_pos(nr, nc) and board_state[nr][nc] is None:
                    moves.append((nr, nc))
            # Tốt ăn chéo
            pawn_attacks = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
            for dr, dc in pawn_attacks:
                nr, nc = row + dr, col + dc
                if self._is_valid_pos(nr, nc):
                    moves.append((nr, nc))  # Có thể ăn rook

        elif piece_type == 'BISHOP':
            dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
            for dr, dc in dirs:
                for i in range(1, BOARD_SIZE):
                    nr, nc = row + dr * i, col + dc * i
                    if not self._is_valid_pos(nr, nc):
                        break
                    if board_state[nr][nc] is not None:
                        break
                    moves.append((nr, nc))

        elif piece_type == 'KNIGHT':
            knight_moves = [
                (-2, -1), (-2, 1), (-1, -2), (-1, 2),
                (1, -2), (1, 2), (2, -1), (2, 1)
            ]
            for dr, dc in knight_moves:
                nr, nc = row + dr, col + dc
                if self._is_valid_pos(nr, nc):
                    moves.append((nr, nc))

        elif piece_type == 'ROOK':
            dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            for dr, dc in dirs:
                for i in range(1, BOARD_SIZE):
                    nr, nc = row + dr * i, col + dc * i
                    if not self._is_valid_pos(nr, nc):
                        break
                    if board_state[nr][nc] is not None:
                        break
                    moves.append((nr, nc))

        elif piece_type == 'QUEEN':
            dirs = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
            for dr, dc in dirs:
                for i in range(1, BOARD_SIZE):
                    nr, nc = row + dr * i, col + dc * i
                    if not self._is_valid_pos(nr, nc):
                        break
                    if board_state[nr][nc] is not None:
                        break
                    moves.append((nr, nc))

        elif piece_type == 'KING':
            dirs = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
            for dr, dc in dirs:
                nr, nc = row + dr, col + dc
                if self._is_valid_pos(nr, nc):
                    moves.append((nr, nc))

        return moves

    def _simulate_danger_after_capture(self, target_row: int, target_col: int,
                                        board_state: List[List]) -> Set[Tuple[int, int]]:
        """
        Mô phỏng các ô nguy hiểm SAU KHI player di chuyển đến (target_row, target_col) và ăn quân ở đó.
        Quân bị ăn tại target sẽ biến mất, player sẽ chiếm vị trí đó.
        """
        danger = set()

        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                # Bỏ qua ô mà player sẽ chiếm (quân địch ở đây sẽ bị ăn)
                if r == target_row and c == target_col:
                    continue

                piece = board_state[r][c]
                if piece and not piece.is_player:
                    attacks = self._get_attack_moves_after_capture(
                        r, c, piece.type, board_state, target_row, target_col
                    )
                    danger.update(attacks)

        return danger

    def _get_attack_moves_after_capture(self, row: int, col: int, piece_type: str,
                                         board_state: List[List],
                                         captured_row: int, captured_col: int) -> List[Tuple[int, int]]:
        """
        Tính các ô bị tấn công bởi quân địch SAU KHI player ăn quân tại (captured_row, captured_col).
        Sau khi ăn:
        - Quân bị ăn biến mất → không còn chặn đường
        - Quân player chiếm vị trí đó → chặn đường tấn công của quân địch khác
        """
        attacks = []

        if piece_type in ['PAWN', 'KNIGHT', 'KING']:
            return self._get_attack_moves(row, col, piece_type, board_state)

        if piece_type == 'BISHOP':
            dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        elif piece_type == 'ROOK':
            dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        else:
            dirs = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]

        for dr, dc in dirs:
            for i in range(1, BOARD_SIZE):
                nr, nc = row + dr * i, col + dc * i
                if not self._is_valid_pos(nr, nc):
                    break

                attacks.append((nr, nc))

                # Vị trí mà player sẽ chiếm sau khi ăn - quân player chặn đường
                if nr == captured_row and nc == captured_col:
                    break

                # Các quân khác vẫn chặn đường như bình thường
                if board_state[nr][nc] is not None:
                    break

        return attacks

    def _count_safe_escapes(self, row: int, col: int,
                            board_state: List[List],
                            danger_cells: Set[Tuple[int, int]]) -> float:
        """
        Đếm số đường thoát an toàn từ vị trí (row, col).
        Bao gồm cả ô trống và ô có quân địch (capture as escape).
        """
        safe_count = 0
        capture_escape_count = 0
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        for dr, dc in directions:
            for i in range(1, BOARD_SIZE):
                nr, nc = row + dr * i, col + dc * i

                if not self._is_valid_pos(nr, nc):
                    break

                piece = board_state[nr][nc]

                if piece is not None:
                    # Quân địch = có thể ăn để thoát
                    if not piece.is_player:
                        # Kiểm tra nếu ăn quân này thì có an toàn không
                        future_danger = self._simulate_danger_after_capture(nr, nc, board_state)
                        if (nr, nc) not in future_danger:
                            capture_escape_count += 1
                    break  # Dừng hướng này (bị chặn)

                # Ô trống và an toàn
                if (nr, nc) not in danger_cells:
                    safe_count += 1

        # Capture as escape có giá trị thấp hơn ô trống an toàn
        return safe_count + capture_escape_count * 0.5

    def update_position(self, position: Tuple[int, int]):
        self.last_position = position
        self.position_history.append(position)

        if len(self.position_history) > 20:
            self.position_history = self.position_history[-20:]

    def reset(self):
        self.last_position = None
        self.position_history = []
