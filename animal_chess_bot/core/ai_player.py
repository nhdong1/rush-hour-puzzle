from typing import List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import copy

from .board_detector import BOARD_SIZE
from .piece_detector import Piece, PIECE_POWER
from .cell_detector import CellState, CellInfo


SEARCH_DEPTH = 4
INF = float('inf')

# Score maximization weights
CAPTURE_VALUE_WEIGHT = 50.0  # High weight for capture value
MATERIAL_DIFF_WEIGHT = 5.0   # Lower weight for material difference
PIECE_COUNT_WEIGHT = 10.0    # Lower weight for piece count
AGGRESSION_BONUS = 30.0      # Bonus for aggressive positioning
HIGH_VALUE_THRESHOLD = 5     # Pieces with power >= this are high priority targets


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

    def _get_action_priority(self, action: Action,
                              board_state: List[List[Optional[Piece]]],
                              cell_states: List[List[CellInfo]]) -> Tuple[int, float]:
        """
        Calculate priority for an action optimized for MAXIMUM SCORE.
        
        Priority order (score-focused):
        Priority 1 (highest): High-value captures (power >= 5: Elephant, Lion, Tiger)
        Priority 2: Blue mouse captures red elephant (8 points!)
        Priority 3: Medium-value captures (power 3-4: Leopard, Wolf)
        Priority 4: Any capture (even low value - all points matter)
        Priority 5: Aggressive positioning towards high-value targets
        Priority 6: Blue elephant escapes from red mouse (preserve our scorer)
        Priority 7: Flip cells
        Priority 8: Other moves

        Returns: (priority_level, sub_score) - lower priority_level = higher priority
        """
        # Priority 1: High-value captures (Elephant=8, Lion=7, Tiger=6)
        if action.type == ActionType.CAPTURE:
            capture_value = action.target_piece.power
            
            # Mouse capturing elephant is the BEST (8 points, no risk)
            if action.piece.type == "mouse" and action.target_piece.type == "elephant":
                return (1, capture_value * CAPTURE_VALUE_WEIGHT + 100)
            
            # High-value targets (power >= 5)
            if capture_value >= HIGH_VALUE_THRESHOLD:
                # Bonus for safe captures, but still prioritize high value even if risky
                safety_bonus = 50 if not self._will_be_captured_after(action, board_state, cell_states) else 0
                return (1, capture_value * CAPTURE_VALUE_WEIGHT + safety_bonus)
            
            # Medium-value captures (power 3-4)
            if capture_value >= 3:
                safety_bonus = 30 if not self._will_be_captured_after(action, board_state, cell_states) else 0
                return (2, capture_value * CAPTURE_VALUE_WEIGHT + safety_bonus)
            
            # Low-value captures (power 1-2) - still worth taking!
            return (3, capture_value * CAPTURE_VALUE_WEIGHT)

        # Priority 4: Aggressive moves towards high-value targets
        if action.type == ActionType.MOVE:
            dst_row, dst_col = action.target_pos
            
            # Calculate how close this move gets us to high-value targets
            hunt_score = self._calculate_hunt_score(action.piece, dst_row, dst_col, board_state)
            if hunt_score > 0:
                return (4, hunt_score)
            
            # Blue elephant escaping mouse - preserve our high-value piece for later captures
            if action.piece.type == "elephant":
                src_row, src_col = action.source_pos
                if self._is_threatened_by_mouse(src_row, src_col, board_state):
                    if not self._is_threatened_by_mouse(dst_row, dst_col, board_state):
                        return (5, 80.0)

        # Priority 6: Flip cells (needed to reveal pieces to capture)
        if action.type == ActionType.FLIP:
            row, col = action.target_pos
            center_cells = [(1, 1), (1, 2), (2, 1), (2, 2)]
            if (row, col) in center_cells:
                return (6, 40.0)
            else:
                return (7, 20.0)

        # Priority 8: Other moves
        return (8, 0.0)
    
    def _will_be_captured_after(self, action: Action,
                                 board_state: List[List[Optional[Piece]]],
                                 cell_states: List[List[CellInfo]]) -> bool:
        """Check if our piece will be captured after this action"""
        if action.type == ActionType.FLIP:
            return False
        
        new_board, new_cells, _ = self._simulate_action(action, board_state, cell_states)
        target_pos = action.target_pos
        
        our_piece = new_board[target_pos[0]][target_pos[1]]
        if our_piece is None:
            return False
        
        return self._is_threatened_by_red(target_pos, our_piece, new_board, new_cells)
    
    def _calculate_hunt_score(self, piece: Piece, row: int, col: int,
                               board_state: List[List[Optional[Piece]]]) -> float:
        """Calculate score for hunting high-value targets"""
        hunt_score = 0.0
        
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                target = board_state[r][c]
                if target and not target.is_blue:
                    # Can we capture this target?
                    if self.can_capture(piece, target):
                        old_dist = abs(piece.row - r) + abs(piece.col - c)
                        new_dist = abs(row - r) + abs(col - c)
                        
                        # Moving closer to a capturable target
                        if new_dist < old_dist:
                            # Higher value targets = higher hunt score
                            value_multiplier = target.power * 5
                            hunt_score += value_multiplier * (old_dist - new_dist)
                            
                            # Extra bonus for getting adjacent to high-value targets
                            if new_dist == 1 and target.power >= HIGH_VALUE_THRESHOLD:
                                hunt_score += target.power * 20
        
        return hunt_score

    def _is_threatened_by_mouse(self, row: int, col: int,
                                 board_state: List[List[Optional[Piece]]]) -> bool:
        """Check if position is threatened by a red mouse"""
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, dc in directions:
            nr, nc = row + dr, col + dc
            if not self._is_valid_pos(nr, nc):
                continue
            piece = board_state[nr][nc]
            if piece and not piece.is_blue and piece.type == "mouse":
                return True
        return False

    def _calculate_attack_potential(self, piece: Piece, row: int, col: int,
                                     board_state: List[List[Optional[Piece]]],
                                     cell_states: List[List[CellInfo]]) -> float:
        """Calculate attack potential for a piece at a given position"""
        potential = 0.0
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        for dr, dc in directions:
            nr, nc = row + dr, col + dc
            if not self._is_valid_pos(nr, nc):
                continue

            target_piece = board_state[nr][nc]
            target_cell = cell_states[nr][nc]

            if target_cell.state == CellState.UNFLIPPED:
                continue

            if target_piece and not target_piece.is_blue:
                # Can capture this red piece
                if self.can_capture(piece, target_piece):
                    potential += target_piece.power * 5

        return potential

    def select_best_action(self, valid_actions: List[Action],
                           board_state: List[List[Optional[Piece]]],
                           cell_states: List[List[CellInfo]]) -> Optional[Action]:
        """
        Select the best action optimized for MAXIMUM SCORE.
        
        Strategy:
        - Prioritize ALL captures (points are points!)
        - High-value captures get massive priority
        - Accept calculated risks for high rewards
        - Position aggressively to enable future captures
        """
        if not valid_actions:
            return None

        # Calculate priority for each action
        action_priorities = []
        for action in valid_actions:
            priority, sub_score = self._get_action_priority(action, board_state, cell_states)
            is_safe = self._is_safe_action(action, board_state, cell_states)
            
            # For score maximization: calculate net value even for risky captures
            net_value = self._calculate_net_capture_value(action, board_state, cell_states)
            
            action_priorities.append((action, priority, sub_score, is_safe, net_value))

        # Sort by priority first, then by sub_score (captures sorted by value)
        action_priorities.sort(key=lambda x: (x[1], -x[2]))

        # Get the highest priority level among all actions
        highest_priority = action_priorities[0][1]

        # For capture actions (priority 1-3), take the highest value capture
        if highest_priority <= 3:
            capture_actions = [ap for ap in action_priorities if ap[1] <= 3]
            # Sort by net value (reward - risk), then by raw capture value
            capture_actions.sort(key=lambda x: (-x[4], -x[2]))
            
            best_capture = capture_actions[0]
            # Take the capture if net value is positive OR if it's a high-value target
            if best_capture[4] >= 0 or best_capture[0].target_piece.power >= HIGH_VALUE_THRESHOLD:
                return best_capture[0]

        # For other actions, use minimax with score-maximization focus
        best_action = None
        best_score = -INF
        alpha = -INF
        beta = INF

        for action, priority, sub_score, is_safe, net_value in action_priorities:
            # For score maximization: don't skip risky captures if net value is positive
            if action.type == ActionType.CAPTURE:
                if net_value < 0 and is_safe == False:
                    # Only skip if we're losing points AND it's unsafe
                    continue
            elif not is_safe:
                # For non-captures, still prefer safe moves if available
                safe_options = [ap for ap in action_priorities if ap[3]]
                if safe_options:
                    continue

            new_board, new_cells, score_change = self._simulate_action(
                action, board_state, cell_states
            )

            score = self._minimax(
                new_board, new_cells,
                depth=self.search_depth - 1,
                alpha=alpha, beta=beta,
                is_blue_turn=False
            )
            
            # Heavily weight the immediate score gain
            score += score_change * CAPTURE_VALUE_WEIGHT

            # Add priority bonus (lower priority number = higher bonus)
            priority_bonus = (9 - priority) * 15
            score += priority_bonus + sub_score
            
            # Add net value bonus for captures
            if action.type == ActionType.CAPTURE:
                score += net_value * 10

            if score > best_score:
                best_score = score
                best_action = action

            alpha = max(alpha, score)

        return best_action
    
    def _calculate_net_capture_value(self, action: Action,
                                      board_state: List[List[Optional[Piece]]],
                                      cell_states: List[List[CellInfo]]) -> float:
        """
        Calculate net value of a capture: reward - potential loss.
        Positive = good trade, Negative = bad trade, Zero = even trade
        """
        if action.type != ActionType.CAPTURE:
            return 0.0
        
        reward = action.target_piece.power
        
        # Check if we'll lose our piece after the capture
        new_board, new_cells, _ = self._simulate_action(action, board_state, cell_states)
        our_piece = new_board[action.target_pos[0]][action.target_pos[1]]
        
        if our_piece is None:
            # Equal power trade - we both die, but we got points!
            return reward  # For score maximization, this is POSITIVE
        
        if self._is_threatened_by_red(action.target_pos, our_piece, new_board, new_cells):
            # We might lose our piece - but we still got the capture points
            # Net = what we gain - what we might lose
            potential_loss = our_piece.power
            # For score max: even trades are good (we gain points)
            return reward - (potential_loss * 0.5)  # Discount potential loss
        
        # Safe capture - full value
        return reward

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
        """
        Calculate penalty for risky actions - REDUCED for score maximization.
        We want to take more risks for points!
        """
        if action.type != ActionType.CAPTURE:
            return 0

        reward = action.target_piece.power
        risk = action.piece.power

        # Equal power trades: NO PENALTY for score maximization!
        # We gain points equal to their piece value
        if action.piece.power == action.target_piece.power:
            return 0  # Changed from risk * 5

        new_board, new_cells, _ = self._simulate_action(action, board_state, cell_states)

        if self._is_threatened_by_red(action.target_pos, action.piece, new_board, new_cells):
            # Only penalize if we lose MORE than we gain
            if risk > reward:
                return (risk - reward) * 5  # Reduced penalty
            else:
                return 0  # Good trade or even - no penalty

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
        """
        Evaluate board state optimized for MAXIMUM SCORE accumulation.
        
        Key principles:
        - Heavily reward positions that enable captures
        - Value remaining enemy pieces as "potential points"
        - Aggressive positioning towards high-value targets
        - Reduced safety concerns (we want to trade for points)
        """
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

        # === SCORE MAXIMIZATION EVALUATION ===
        
        # 1. Potential points remaining (enemy pieces = future points)
        potential_points = sum(p.power for p in red_pieces)
        score += potential_points * 3  # We WANT enemies alive to capture them
        
        # 2. Our capturing power (blue pieces that can capture)
        blue_power = sum(p.power for p in blue_pieces)
        score += blue_power * MATERIAL_DIFF_WEIGHT
        
        # 3. Piece count - we need pieces to capture with
        score += len(blue_pieces) * PIECE_COUNT_WEIGHT
        
        # 4. IMMEDIATE CAPTURE OPPORTUNITIES (highest priority!)
        for blue in blue_pieces:
            for red in red_pieces:
                if self._is_adjacent(blue, red) and self.can_capture(blue, red):
                    # Immediate capture available - HUGE bonus
                    score += red.power * CAPTURE_VALUE_WEIGHT
                    
                    # Extra bonus for high-value targets
                    if red.power >= HIGH_VALUE_THRESHOLD:
                        score += red.power * 20

        # 5. HUNTING BONUS - pieces close to capturable targets
        for blue in blue_pieces:
            for red in red_pieces:
                if self.can_capture(blue, red):
                    dist = abs(blue.row - red.row) + abs(blue.col - red.col)
                    if dist == 2:
                        # One move away from capture
                        score += red.power * AGGRESSION_BONUS
                    elif dist == 3:
                        # Two moves away
                        score += red.power * (AGGRESSION_BONUS / 2)

        # 6. Mouse hunting elephant - MASSIVE bonus (8 points!)
        for blue in blue_pieces:
            if blue.type == "mouse":
                for red in red_pieces:
                    if red.type == "elephant":
                        dist = abs(blue.row - red.row) + abs(blue.col - red.col)
                        if dist == 1:
                            score += 200  # Can capture next turn!
                        elif dist == 2:
                            score += 100  # Very close
                        elif dist <= 4:
                            score += 50 / dist  # Getting closer

        # 7. Protect our high-value pieces (they can capture more)
        for blue in blue_pieces:
            if blue.power >= HIGH_VALUE_THRESHOLD:
                if self._is_threatened_by_red((blue.row, blue.col), blue, board_state, cell_states):
                    # High-value piece threatened - moderate penalty
                    # (reduced from before - we're more aggressive now)
                    score -= blue.power * 5
                else:
                    # Safe high-value piece - small bonus
                    score += blue.power * 2

        # 8. Elephant vs Mouse special case
        for blue in blue_pieces:
            if blue.type == "elephant":
                for red in red_pieces:
                    if red.type == "mouse":
                        dist = abs(blue.row - red.row) + abs(blue.col - red.col)
                        if dist == 1:
                            score -= 40  # Immediate danger - but reduced penalty
                        elif dist == 2:
                            score -= 15  # Nearby danger

        # 9. Bonus for having diverse pieces (more capture options)
        blue_types = set(p.type for p in blue_pieces)
        score += len(blue_types) * 5

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

        return blue_count == 0 or red_count == 0

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
