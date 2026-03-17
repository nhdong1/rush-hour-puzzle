from typing import List, Optional, Tuple, Set
from dataclasses import dataclass


PIECE_VALUES = {
    'PAWN': 1,
    'BISHOP': 3,
    'KNIGHT': 3,
    'ROOK': 5,
    'QUEEN': 9,
    'KING': 10
}

BOARD_SIZE = 8


class AIPlayer:
    def __init__(self):
        self.last_position = None
        self.position_history = []
        
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
                         danger_cells: Set[Tuple[int, int]]) -> Optional[Tuple[int, int, bool]]:
        if not valid_moves:
            return None
            
        scored_moves = []
        
        for move in valid_moves:
            score = self._evaluate_move(move, board_state, danger_cells)
            scored_moves.append((score, move))
            
        scored_moves.sort(key=lambda x: x[0], reverse=True)
        
        best_score = scored_moves[0][0]
        best_moves = [m for s, m in scored_moves if s == best_score]
        
        if len(best_moves) > 1:
            import random
            return random.choice(best_moves)
            
        return scored_moves[0][1]
        
    def _evaluate_move(self, move: Tuple[int, int, bool], 
                       board_state: List[List], 
                       danger_cells: Set[Tuple[int, int]]) -> float:
        target_row, target_col, is_capture = move
        score = 0.0
        
        if (target_row, target_col) in danger_cells:
            score -= 1000
            
        if is_capture:
            piece = board_state[target_row][target_col]
            if piece:
                piece_value = PIECE_VALUES.get(piece.type, 1)
                score += piece_value * 10
                
                future_danger = self._simulate_danger_after_capture(
                    target_row, target_col, board_state
                )
                if (target_row, target_col) not in future_danger:
                    score += 50
                else:
                    score -= piece_value * 5
                    
        escape_routes = self._count_safe_escapes(target_row, target_col, board_state, danger_cells)
        score += escape_routes * 5
        
        center_dist = abs(target_row - 3.5) + abs(target_col - 3.5)
        score += (7 - center_dist) * 2
        
        if self.last_position and (target_row, target_col) == self.last_position:
            score -= 20
            
        position_count = self.position_history.count((target_row, target_col))
        score -= position_count * 10
        
        return score
        
    def _simulate_danger_after_capture(self, row: int, col: int, 
                                        board_state: List[List]) -> Set[Tuple[int, int]]:
        danger = set()
        
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if r == row and c == col:
                    continue
                    
                piece = board_state[r][c]
                if piece and not piece.is_player:
                    attacks = self._get_attack_moves_after_capture(r, c, piece.type, board_state, row, col)
                    danger.update(attacks)
                    
        return danger
        
    def _get_attack_moves_after_capture(self, row: int, col: int, piece_type: str,
                                         board_state: List[List], 
                                         captured_row: int, captured_col: int) -> List[Tuple[int, int]]:
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
                
                if nr == captured_row and nc == captured_col:
                    continue
                    
                if board_state[nr][nc] is not None:
                    break
                    
        return attacks
        
    def _count_safe_escapes(self, row: int, col: int, 
                            board_state: List[List], 
                            danger_cells: Set[Tuple[int, int]]) -> int:
        safe_count = 0
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        
        for dr, dc in directions:
            for i in range(1, BOARD_SIZE):
                nr, nc = row + dr * i, col + dc * i
                
                if not self._is_valid_pos(nr, nc):
                    break
                    
                piece = board_state[nr][nc]
                
                if piece is not None:
                    break
                    
                if (nr, nc) not in danger_cells:
                    safe_count += 1
                    
        return safe_count
        
    def update_position(self, position: Tuple[int, int]):
        self.last_position = position
        self.position_history.append(position)
        
        if len(self.position_history) > 20:
            self.position_history = self.position_history[-20:]
            
    def reset(self):
        self.last_position = None
        self.position_history = []
