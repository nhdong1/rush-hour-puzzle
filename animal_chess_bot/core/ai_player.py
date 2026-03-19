from typing import List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import copy

from .board_detector import BOARD_SIZE
from .piece_detector import Piece, PIECE_POWER
from .cell_detector import CellState, CellInfo


SEARCH_DEPTH = 3
INF = float('inf')


class ActionType(Enum):
    FLIP = "flip"
    MOVE = "move"
    CAPTURE = "capture"


@dataclass
class Action:
    type: ActionType
    source_pos: Optional[Tuple[int, int]] = None
    target_pos: Tuple[int, int] = None
    piece: Optional[Piece] = None
    target_piece: Optional[Piece] = None
    
    def __repr__(self):
        if self.type == ActionType.FLIP:
            return f"Flip at {self.target_pos}"
        elif self.type == ActionType.MOVE:
            return f"Move {self.piece.type} from {self.source_pos} to {self.target_pos}"
        else:
            return f"Capture {self.target_piece.type} at {self.target_pos} with {self.piece.type}"


class AIPlayer:
    """
    AI Player for Animal Chess (Blue team).
    Uses Minimax with Alpha-Beta pruning to look ahead 3 moves.
    """
    
    def __init__(self, depth: int = SEARCH_DEPTH):
        self.search_depth = depth
        self.blue_score = 0
        self.red_score = 0
        self.turn_count = 0
        self.max_turns = 40
    
    def reset(self):
        self.blue_score = 0
        self.red_score = 0
        self.turn_count = 0
    
    def can_capture(self, attacker: Piece, defender: Piece) -> bool:
        """
        Check if attacker can capture defender.
        Special rule: Mouse (1) can capture Elephant (8), but Elephant cannot capture Mouse.
        """
        if attacker.is_blue == defender.is_blue:
            return False
        
        if attacker.type == "mouse" and defender.type == "elephant":
            return True
        
        if attacker.type == "elephant" and defender.type == "mouse":
            return False
        
        return attacker.power >= defender.power
    
    def get_valid_actions(self, board_state: List[List[Optional[Piece]]], 
                          cell_states: List[List[CellInfo]]) -> List[Action]:
        """
        Get all valid actions for blue team.
        
        Actions:
        1. Flip any unflipped cell
        2. Move blue piece to adjacent empty cell
        3. Capture adjacent red piece (if allowed by power rules)
        """
        actions = []
        
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if cell_states[row][col].state == CellState.UNFLIPPED:
                    actions.append(Action(
                        type=ActionType.FLIP,
                        target_pos=(row, col)
                    ))
        
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = board_state[row][col]
                if piece is None or not piece.is_blue:
                    continue
                
                for dr, dc in directions:
                    nr, nc = row + dr, col + dc
                    
                    if not self._is_valid_pos(nr, nc):
                        continue
                    
                    target_piece = board_state[nr][nc]
                    target_cell = cell_states[nr][nc]
                    
                    if target_cell.state == CellState.UNFLIPPED:
                        continue
                    
                    if target_piece is None:
                        actions.append(Action(
                            type=ActionType.MOVE,
                            source_pos=(row, col),
                            target_pos=(nr, nc),
                            piece=piece
                        ))
                    elif not target_piece.is_blue:
                        if self.can_capture(piece, target_piece):
                            actions.append(Action(
                                type=ActionType.CAPTURE,
                                source_pos=(row, col),
                                target_pos=(nr, nc),
                                piece=piece,
                                target_piece=target_piece
                            ))
        
        return actions
    
    def _get_red_actions(self, board_state: List[List[Optional[Piece]]],
                         cell_states: List[List[CellInfo]]) -> List[Action]:
        """Get all valid actions for red team (for minimax simulation)"""
        actions = []
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = board_state[row][col]
                if piece is None or piece.is_blue:
                    continue
                
                for dr, dc in directions:
                    nr, nc = row + dr, col + dc
                    
                    if not self._is_valid_pos(nr, nc):
                        continue
                    
                    target_piece = board_state[nr][nc]
                    target_cell = cell_states[nr][nc]
                    
                    if target_cell.state == CellState.UNFLIPPED:
                        continue
                    
                    if target_piece is None:
                        actions.append(Action(
                            type=ActionType.MOVE,
                            source_pos=(row, col),
                            target_pos=(nr, nc),
                            piece=piece
                        ))
                    elif target_piece.is_blue:
                        if self.can_capture(piece, target_piece):
                            actions.append(Action(
                                type=ActionType.CAPTURE,
                                source_pos=(row, col),
                                target_pos=(nr, nc),
                                piece=piece,
                                target_piece=target_piece
                            ))
        
        return actions
    
    def select_best_action(self, valid_actions: List[Action],
                           board_state: List[List[Optional[Piece]]],
                           cell_states: List[List[CellInfo]]) -> Optional[Action]:
        """
        Select the best action using Minimax with Alpha-Beta pruning.
        Looks ahead 3 moves to evaluate outcomes.
        """
        if not valid_actions:
            return None
        
        safe_actions = []
        risky_actions = []
        
        for action in valid_actions:
            if self._is_safe_action(action, board_state, cell_states):
                safe_actions.append(action)
            else:
                risky_actions.append(action)
        
        actions_to_evaluate = safe_actions if safe_actions else risky_actions
        
        best_action = None
        best_score = -INF
        alpha = -INF
        beta = INF
        
        for action in actions_to_evaluate:
            new_board, new_cells, score_change = self._simulate_action(
                action, board_state, cell_states
            )
            
            score = self._minimax(
                new_board, new_cells,
                depth=self.search_depth - 1,
                alpha=alpha, beta=beta,
                is_blue_turn=False
            )
            score += score_change
            
            if action.type == ActionType.CAPTURE:
                if not self._is_safe_action(action, board_state, cell_states):
                    risk_penalty = self._calculate_risk_penalty(action, board_state, cell_states)
                    score -= risk_penalty
            
            if score > best_score:
                best_score = score
                best_action = action
            
            alpha = max(alpha, score)
        
        return best_action
    
    def _minimax(self, board_state: List[List[Optional[Piece]]],
                 cell_states: List[List[CellInfo]],
                 depth: int, alpha: float, beta: float,
                 is_blue_turn: bool) -> float:
        """
        Minimax with alpha-beta pruning.
        - is_blue_turn=True: Blue's turn (maximize)
        - is_blue_turn=False: Red's turn (minimize blue's score)
        """
        if depth <= 0 or self._is_game_over(board_state):
            return self._evaluate_board(board_state, cell_states)
        
        if is_blue_turn:
            max_eval = -INF
            blue_actions = self.get_valid_actions(board_state, cell_states)
            
            if not blue_actions:
                return self._evaluate_board(board_state, cell_states)
            
            for action in blue_actions:
                new_board, new_cells, score_change = self._simulate_action(
                    action, board_state, cell_states
                )
                eval_score = self._minimax(
                    new_board, new_cells,
                    depth - 1, alpha, beta, False
                ) + score_change
                
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            
            return max_eval
        else:
            min_eval = INF
            red_actions = self._get_red_actions(board_state, cell_states)
            
            if not red_actions:
                return self._evaluate_board(board_state, cell_states)
            
            for action in red_actions:
                new_board, new_cells, score_change = self._simulate_action(
                    action, board_state, cell_states
                )
                eval_score = self._minimax(
                    new_board, new_cells,
                    depth - 1, alpha, beta, True
                ) - score_change
                
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            
            return min_eval
    
    def _is_safe_action(self, action: Action,
                        board_state: List[List[Optional[Piece]]],
                        cell_states: List[List[CellInfo]]) -> bool:
        """Check if action is safe (piece won't be captured next turn)"""
        if action.type == ActionType.FLIP:
            return True
        
        new_board, new_cells, _ = self._simulate_action(action, board_state, cell_states)
        target_pos = action.target_pos
        
        blue_piece = new_board[target_pos[0]][target_pos[1]]
        if blue_piece is None:
            return True
        
        return not self._is_threatened_by_red(target_pos, blue_piece, new_board, new_cells)
    
    def _is_threatened_by_red(self, pos: Tuple[int, int], blue_piece: Piece,
                               board_state: List[List[Optional[Piece]]],
                               cell_states: List[List[CellInfo]]) -> bool:
        """Check if blue piece at pos is threatened by any red piece"""
        row, col = pos
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        
        for dr, dc in directions:
            nr, nc = row + dr, col + dc
            if not self._is_valid_pos(nr, nc):
                continue
            
            red_piece = board_state[nr][nc]
            if red_piece and not red_piece.is_blue:
                if self.can_capture(red_piece, blue_piece):
                    return True
        
        return False
    
    def _calculate_risk_penalty(self, action: Action,
                                board_state: List[List[Optional[Piece]]],
                                cell_states: List[List[CellInfo]]) -> float:
        """Calculate penalty for risky actions"""
        if action.type != ActionType.CAPTURE:
            return 0
        
        reward = action.target_piece.power
        risk = action.piece.power
        
        if action.piece.power == action.target_piece.power:
            return risk * 5
        
        new_board, new_cells, _ = self._simulate_action(action, board_state, cell_states)
        
        if self._is_threatened_by_red(action.target_pos, action.piece, new_board, new_cells):
            return (risk - reward) * 10 if risk > reward else 0
        
        return 0
    
    def _simulate_action(self, action: Action,
                         board_state: List[List[Optional[Piece]]],
                         cell_states: List[List[CellInfo]]) -> Tuple[List[List], List[List], float]:
        """
        Simulate an action and return new board state.
        Returns: (new_board, new_cells, score_change)
        """
        new_board = [row[:] for row in board_state]
        new_cells = [[cell for cell in row] for row in cell_states]
        score_change = 0.0
        
        if action.type == ActionType.FLIP:
            row, col = action.target_pos
            new_cells[row][col] = CellInfo(
                state=CellState.FLIPPED,
                row=row,
                col=col
            )
        
        elif action.type == ActionType.MOVE:
            src_row, src_col = action.source_pos
            dst_row, dst_col = action.target_pos
            
            piece = new_board[src_row][src_col]
            new_board[src_row][src_col] = None
            
            moved_piece = Piece(
                type=piece.type,
                is_blue=piece.is_blue,
                power=piece.power,
                row=dst_row,
                col=dst_col,
                confidence=piece.confidence
            )
            new_board[dst_row][dst_col] = moved_piece
        
        elif action.type == ActionType.CAPTURE:
            src_row, src_col = action.source_pos
            dst_row, dst_col = action.target_pos
            
            attacker = action.piece
            defender = action.target_piece
            
            score_change = defender.power
            
            new_board[src_row][src_col] = None
            
            if attacker.power == defender.power:
                new_board[dst_row][dst_col] = None
            else:
                moved_piece = Piece(
                    type=attacker.type,
                    is_blue=attacker.is_blue,
                    power=attacker.power,
                    row=dst_row,
                    col=dst_col,
                    confidence=attacker.confidence
                )
                new_board[dst_row][dst_col] = moved_piece
        
        return new_board, new_cells, score_change
    
    def _evaluate_board(self, board_state: List[List[Optional[Piece]]],
                        cell_states: List[List[CellInfo]]) -> float:
        """Evaluate board state from blue's perspective"""
        score = 0.0
        
        blue_pieces = []
        red_pieces = []
        
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = board_state[row][col]
                if piece:
                    if piece.is_blue:
                        blue_pieces.append(piece)
                    else:
                        red_pieces.append(piece)
        
        blue_power = sum(p.power for p in blue_pieces)
        red_power = sum(p.power for p in red_pieces)
        score += (blue_power - red_power) * 10
        
        score += (len(blue_pieces) - len(red_pieces)) * 20
        
        for piece in blue_pieces:
            if not self._is_threatened_by_red((piece.row, piece.col), piece, board_state, cell_states):
                score += 15
            else:
                score -= 25
        
        for blue in blue_pieces:
            for red in red_pieces:
                if self._is_adjacent(blue, red) and self.can_capture(blue, red):
                    score += red.power * 5
        
        for blue in blue_pieces:
            if blue.type == "mouse":
                for red in red_pieces:
                    if red.type == "elephant" and self._is_adjacent(blue, red):
                        score += 50
        
        return score
    
    def _is_game_over(self, board_state: List[List[Optional[Piece]]]) -> bool:
        """Check if game is over"""
        blue_count = 0
        red_count = 0
        
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = board_state[row][col]
                if piece:
                    if piece.is_blue:
                        blue_count += 1
                    else:
                        red_count += 1
        
        return blue_count == 0 or red_count == 0 or self.turn_count >= self.max_turns
    
    def _is_valid_pos(self, row: int, col: int) -> bool:
        return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE
    
    def _is_adjacent(self, piece1: Piece, piece2: Piece) -> bool:
        """Check if two pieces are adjacent (4-directional)"""
        return (abs(piece1.row - piece2.row) + abs(piece1.col - piece2.col)) == 1
    
    def update_turn(self):
        """Increment turn counter"""
        self.turn_count += 1
    
    def add_score(self, points: int, is_blue: bool):
        """Add points to score"""
        if is_blue:
            self.blue_score += points
        else:
            self.red_score += points
