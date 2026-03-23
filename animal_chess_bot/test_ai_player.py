"""
Unit tests for Animal Chess AI Player - Score Maximization
Run: python -m pytest test_ai_player.py -v
Or:  python test_ai_player.py
"""
import unittest
from typing import List, Optional

from core.ai_player import (
    AIPlayer, Action, ActionType,
    CAPTURE_VALUE_WEIGHT, HIGH_VALUE_THRESHOLD, AGGRESSION_BONUS,
    SEARCH_DEPTH
)
from core.piece_detector import Piece, PIECE_POWER
from core.cell_detector import CellState, CellInfo
from core.board_detector import BOARD_SIZE


def create_empty_board() -> List[List[Optional[Piece]]]:
    """Create 4x4 empty board"""
    return [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]


def create_flipped_cells() -> List[List[CellInfo]]:
    """Create 4x4 board with all cells flipped (revealed)"""
    return [[CellInfo(state=CellState.FLIPPED, row=r, col=c) 
             for c in range(BOARD_SIZE)] for r in range(BOARD_SIZE)]


def create_piece(piece_type: str, is_blue: bool, row: int, col: int) -> Piece:
    """Helper to create a piece"""
    return Piece(
        type=piece_type,
        is_blue=is_blue,
        power=PIECE_POWER[piece_type],
        row=row,
        col=col,
        confidence=1.0
    )


def print_board(board: List[List[Optional[Piece]]]):
    """Print board for debugging"""
    print("\n  0 1 2 3")
    print("  -------")
    for r in range(BOARD_SIZE):
        print(f"{r}|", end="")
        for c in range(BOARD_SIZE):
            piece = board[r][c]
            if piece:
                symbol = piece.type[0].upper() if piece.is_blue else piece.type[0].lower()
                print(f"{symbol} ", end="")
            else:
                print(". ", end="")
        print()
    print()


class TestScoreMaximizationConfig(unittest.TestCase):
    """Test that configuration constants are set for score maximization"""
    
    def test_capture_value_weight_is_high(self):
        """Capture value weight should be high for score maximization"""
        self.assertGreaterEqual(CAPTURE_VALUE_WEIGHT, 50.0,
            "CAPTURE_VALUE_WEIGHT should be >= 50 for score maximization")
    
    def test_high_value_threshold(self):
        """High value threshold should target top pieces"""
        self.assertEqual(HIGH_VALUE_THRESHOLD, 5,
            "HIGH_VALUE_THRESHOLD should be 5 (Wolf and above)")
    
    def test_search_depth_increased(self):
        """Search depth should be increased for better planning"""
        self.assertGreaterEqual(SEARCH_DEPTH, 4,
            "SEARCH_DEPTH should be >= 4 for score maximization")


class TestCaptureValuePriority(unittest.TestCase):
    """Test that AI prioritizes captures by value"""
    
    def setUp(self):
        self.ai = AIPlayer(depth=2)
        self.board = create_empty_board()
        self.cells = create_flipped_cells()
    
    def test_prefers_high_value_capture(self):
        """AI should prefer capturing tiger (6) over mouse (1)"""
        # Blue elephant at center (power 8, can capture anything except mouse)
        self.board[1][1] = create_piece("elephant", True, 1, 1)
        # Red mouse adjacent (low value, but elephant can't capture mouse!)
        self.board[1][0] = create_piece("cat", False, 1, 0)  # power 2
        # Red tiger adjacent (high value)
        self.board[1][2] = create_piece("tiger", False, 1, 2)  # power 6
        
        actions = self.ai.get_valid_actions(self.board, self.cells)
        best_action = self.ai.select_best_action(actions, self.board, self.cells)
        
        self.assertIsNotNone(best_action)
        self.assertEqual(best_action.type, ActionType.CAPTURE)
        self.assertEqual(best_action.target_piece.type, "tiger",
            "AI should capture tiger (6 points) over cat (2 points)")
    
    def test_mouse_captures_elephant_highest_priority(self):
        """Mouse capturing elephant should be highest priority (8 points, no risk)"""
        # Blue mouse
        self.board[2][2] = create_piece("mouse", True, 2, 2)
        # Red elephant adjacent
        self.board[2][3] = create_piece("elephant", False, 2, 3)
        # Red cat adjacent (lower value)
        self.board[2][1] = create_piece("cat", False, 2, 1)
        
        actions = self.ai.get_valid_actions(self.board, self.cells)
        best_action = self.ai.select_best_action(actions, self.board, self.cells)
        
        self.assertEqual(best_action.type, ActionType.CAPTURE)
        self.assertEqual(best_action.target_piece.type, "elephant",
            "Mouse should capture elephant (special rule + 8 points)")
    
    def test_all_captures_are_considered(self):
        """Even low-value captures should be taken when available"""
        # Blue tiger
        self.board[0][0] = create_piece("tiger", True, 0, 0)
        # Only a mouse available to capture
        self.board[0][1] = create_piece("mouse", False, 0, 1)
        
        actions = self.ai.get_valid_actions(self.board, self.cells)
        best_action = self.ai.select_best_action(actions, self.board, self.cells)
        
        self.assertEqual(best_action.type, ActionType.CAPTURE,
            "AI should take any capture for points")


class TestEqualPowerTrades(unittest.TestCase):
    """Test that equal power trades are not penalized (both die, but we get points)"""
    
    def setUp(self):
        self.ai = AIPlayer(depth=2)
        self.board = create_empty_board()
        self.cells = create_flipped_cells()
    
    def test_equal_trade_no_penalty(self):
        """Equal power trades should have no penalty (we gain points)"""
        # Blue wolf vs Red wolf
        self.board[1][1] = create_piece("wolf", True, 1, 1)
        self.board[1][2] = create_piece("wolf", False, 1, 2)
        
        action = Action(
            type=ActionType.CAPTURE,
            source_pos=(1, 1),
            target_pos=(1, 2),
            piece=self.board[1][1],
            target_piece=self.board[1][2]
        )
        
        penalty = self.ai._calculate_risk_penalty(action, self.board, self.cells)
        self.assertEqual(penalty, 0,
            "Equal power trade should have 0 penalty for score maximization")
    
    def test_equal_trade_net_value_positive(self):
        """Equal power trade net value should be positive (we gain their power)"""
        self.board[1][1] = create_piece("tiger", True, 1, 1)
        self.board[1][2] = create_piece("tiger", False, 1, 2)
        
        action = Action(
            type=ActionType.CAPTURE,
            source_pos=(1, 1),
            target_pos=(1, 2),
            piece=self.board[1][1],
            target_piece=self.board[1][2]
        )
        
        net_value = self.ai._calculate_net_capture_value(action, self.board, self.cells)
        self.assertGreater(net_value, 0,
            "Equal trade net value should be positive (we get points)")


class TestAggressivePositioning(unittest.TestCase):
    """Test that AI positions aggressively towards high-value targets"""
    
    def setUp(self):
        self.ai = AIPlayer(depth=2)
        self.board = create_empty_board()
        self.cells = create_flipped_cells()
    
    def test_hunt_score_increases_when_approaching_target(self):
        """Hunt score should be positive when moving closer to capturable target"""
        # Blue lion at corner
        blue_lion = create_piece("lion", True, 0, 0)
        self.board[0][0] = blue_lion
        # Red wolf at (2, 2) - can be captured by lion
        self.board[2][2] = create_piece("wolf", False, 2, 2)
        
        # Moving from (0,0) to (0,1) gets closer to wolf
        hunt_score = self.ai._calculate_hunt_score(blue_lion, 0, 1, self.board)
        
        self.assertGreater(hunt_score, 0,
            "Hunt score should be positive when approaching target")
    
    def test_hunt_score_higher_for_high_value_targets(self):
        """Hunt score should be higher when approaching high-value targets"""
        # Use elephant which can capture most pieces (except mouse)
        blue_elephant = create_piece("elephant", True, 0, 0)
        self.board[0][0] = blue_elephant
        
        # Scenario 1: Approaching cat (power 2) - elephant can capture
        board1 = create_empty_board()
        board1[0][0] = blue_elephant
        board1[2][2] = create_piece("cat", False, 2, 2)
        hunt_score_cat = self.ai._calculate_hunt_score(blue_elephant, 0, 1, board1)
        
        # Scenario 2: Approaching tiger (power 6) - elephant can capture
        board2 = create_empty_board()
        board2[0][0] = blue_elephant
        board2[2][2] = create_piece("tiger", False, 2, 2)
        hunt_score_tiger = self.ai._calculate_hunt_score(blue_elephant, 0, 1, board2)
        
        self.assertGreater(hunt_score_tiger, hunt_score_cat,
            "Hunt score should be higher for high-value targets")


class TestActionPriority(unittest.TestCase):
    """Test the new priority system for score maximization"""
    
    def setUp(self):
        self.ai = AIPlayer(depth=2)
        self.board = create_empty_board()
        self.cells = create_flipped_cells()
    
    def test_high_value_capture_priority_1(self):
        """High-value captures (power >= 5) should be priority 1"""
        self.board[1][1] = create_piece("lion", True, 1, 1)
        self.board[1][2] = create_piece("tiger", False, 1, 2)  # power 6
        
        action = Action(
            type=ActionType.CAPTURE,
            source_pos=(1, 1),
            target_pos=(1, 2),
            piece=self.board[1][1],
            target_piece=self.board[1][2]
        )
        
        priority, sub_score = self.ai._get_action_priority(action, self.board, self.cells)
        self.assertEqual(priority, 1,
            "High-value capture should be priority 1")
    
    def test_medium_value_capture_priority_2(self):
        """Medium-value captures (power 3-4) should be priority 2"""
        self.board[1][1] = create_piece("lion", True, 1, 1)
        self.board[1][2] = create_piece("dog", False, 1, 2)  # power 3
        
        action = Action(
            type=ActionType.CAPTURE,
            source_pos=(1, 1),
            target_pos=(1, 2),
            piece=self.board[1][1],
            target_piece=self.board[1][2]
        )
        
        priority, sub_score = self.ai._get_action_priority(action, self.board, self.cells)
        self.assertEqual(priority, 2,
            "Medium-value capture should be priority 2")
    
    def test_low_value_capture_priority_3(self):
        """Low-value captures (power 1-2) should be priority 3"""
        self.board[1][1] = create_piece("lion", True, 1, 1)
        self.board[1][2] = create_piece("mouse", False, 1, 2)  # power 1
        
        action = Action(
            type=ActionType.CAPTURE,
            source_pos=(1, 1),
            target_pos=(1, 2),
            piece=self.board[1][1],
            target_piece=self.board[1][2]
        )
        
        priority, sub_score = self.ai._get_action_priority(action, self.board, self.cells)
        self.assertEqual(priority, 3,
            "Low-value capture should be priority 3")
    
    def test_captures_prioritized_over_moves(self):
        """Any capture should have higher priority than regular moves"""
        self.board[1][1] = create_piece("lion", True, 1, 1)
        self.board[1][2] = create_piece("mouse", False, 1, 2)
        
        capture_action = Action(
            type=ActionType.CAPTURE,
            source_pos=(1, 1),
            target_pos=(1, 2),
            piece=self.board[1][1],
            target_piece=self.board[1][2]
        )
        
        move_action = Action(
            type=ActionType.MOVE,
            source_pos=(1, 1),
            target_pos=(1, 0),
            piece=self.board[1][1]
        )
        
        capture_priority, _ = self.ai._get_action_priority(capture_action, self.board, self.cells)
        move_priority, _ = self.ai._get_action_priority(move_action, self.board, self.cells)
        
        self.assertLess(capture_priority, move_priority,
            "Capture priority should be lower (better) than move priority")


class TestBoardEvaluation(unittest.TestCase):
    """Test board evaluation for score maximization"""
    
    def setUp(self):
        self.ai = AIPlayer(depth=2)
        self.cells = create_flipped_cells()
    
    def test_immediate_capture_opportunity_bonus(self):
        """Board with immediate capture opportunity should score higher"""
        # Board 1: No capture available
        board1 = create_empty_board()
        board1[0][0] = create_piece("lion", True, 0, 0)
        board1[3][3] = create_piece("wolf", False, 3, 3)  # Far away
        
        # Board 2: Capture available
        board2 = create_empty_board()
        board2[0][0] = create_piece("lion", True, 0, 0)
        board2[0][1] = create_piece("wolf", False, 0, 1)  # Adjacent
        
        score1 = self.ai._evaluate_board(board1, self.cells)
        score2 = self.ai._evaluate_board(board2, self.cells)
        
        self.assertGreater(score2, score1,
            "Board with capture opportunity should score higher")
    
    def test_high_value_target_nearby_bonus(self):
        """Having high-value capturable targets nearby should increase score"""
        # Board with tiger nearby (elephant can capture tiger)
        board1 = create_empty_board()
        board1[0][0] = create_piece("elephant", True, 0, 0)
        board1[0][2] = create_piece("tiger", False, 0, 2)  # 2 steps away, power 6
        
        # Board with cat nearby (elephant can capture cat)
        board2 = create_empty_board()
        board2[0][0] = create_piece("elephant", True, 0, 0)
        board2[0][2] = create_piece("cat", False, 0, 2)  # 2 steps away, power 2
        
        score1 = self.ai._evaluate_board(board1, self.cells)
        score2 = self.ai._evaluate_board(board2, self.cells)
        
        self.assertGreater(score1, score2,
            "High-value capturable target nearby should give higher score")
    
    def test_mouse_near_elephant_massive_bonus(self):
        """Blue mouse near red elephant should get massive bonus"""
        board = create_empty_board()
        board[1][1] = create_piece("mouse", True, 1, 1)
        board[1][2] = create_piece("elephant", False, 1, 2)  # Adjacent!
        
        score = self.ai._evaluate_board(board, self.cells)
        
        # Score should be very high due to 200 point bonus
        self.assertGreater(score, 150,
            "Mouse adjacent to elephant should have very high score")


class TestNetCaptureValue(unittest.TestCase):
    """Test net capture value calculation"""
    
    def setUp(self):
        self.ai = AIPlayer(depth=2)
        self.board = create_empty_board()
        self.cells = create_flipped_cells()
    
    def test_safe_capture_full_value(self):
        """Safe capture should return full target value"""
        self.board[1][1] = create_piece("lion", True, 1, 1)
        self.board[1][2] = create_piece("wolf", False, 1, 2)
        
        action = Action(
            type=ActionType.CAPTURE,
            source_pos=(1, 1),
            target_pos=(1, 2),
            piece=self.board[1][1],
            target_piece=self.board[1][2]
        )
        
        net_value = self.ai._calculate_net_capture_value(action, self.board, self.cells)
        self.assertEqual(net_value, 5,  # Wolf power = 5
            "Safe capture should return full target value")
    
    def test_non_capture_returns_zero(self):
        """Non-capture actions should return 0 net value"""
        self.board[1][1] = create_piece("lion", True, 1, 1)
        
        action = Action(
            type=ActionType.MOVE,
            source_pos=(1, 1),
            target_pos=(1, 2),
            piece=self.board[1][1]
        )
        
        net_value = self.ai._calculate_net_capture_value(action, self.board, self.cells)
        self.assertEqual(net_value, 0,
            "Move action should return 0 net value")


class TestWillBeCapturedAfter(unittest.TestCase):
    """Test prediction of whether piece will be captured after action"""
    
    def setUp(self):
        self.ai = AIPlayer(depth=2)
        self.board = create_empty_board()
        self.cells = create_flipped_cells()
    
    def test_detects_threat_after_capture(self):
        """Should detect when piece will be threatened after capture"""
        # Blue wolf captures red mouse, but red lion is waiting
        self.board[1][1] = create_piece("wolf", True, 1, 1)
        self.board[1][2] = create_piece("mouse", False, 1, 2)
        self.board[1][3] = create_piece("lion", False, 1, 3)  # Will capture wolf
        
        action = Action(
            type=ActionType.CAPTURE,
            source_pos=(1, 1),
            target_pos=(1, 2),
            piece=self.board[1][1],
            target_piece=self.board[1][2]
        )
        
        will_be_captured = self.ai._will_be_captured_after(action, self.board, self.cells)
        self.assertTrue(will_be_captured,
            "Should detect that wolf will be captured by lion after taking mouse")
    
    def test_safe_capture_not_threatened(self):
        """Should return False when capture is safe"""
        self.board[1][1] = create_piece("lion", True, 1, 1)
        self.board[1][2] = create_piece("mouse", False, 1, 2)
        # No red pieces nearby
        
        action = Action(
            type=ActionType.CAPTURE,
            source_pos=(1, 1),
            target_pos=(1, 2),
            piece=self.board[1][1],
            target_piece=self.board[1][2]
        )
        
        will_be_captured = self.ai._will_be_captured_after(action, self.board, self.cells)
        self.assertFalse(will_be_captured,
            "Safe capture should not be marked as threatened")


class TestElephantMouseInteraction(unittest.TestCase):
    """Test special elephant-mouse rules"""
    
    def setUp(self):
        self.ai = AIPlayer(depth=2)
        self.board = create_empty_board()
        self.cells = create_flipped_cells()
    
    def test_elephant_escapes_mouse(self):
        """Blue elephant should escape from red mouse threat"""
        # Blue elephant threatened by red mouse
        self.board[1][1] = create_piece("elephant", True, 1, 1)
        self.board[1][2] = create_piece("mouse", False, 1, 2)
        
        actions = self.ai.get_valid_actions(self.board, self.cells)
        best_action = self.ai.select_best_action(actions, self.board, self.cells)
        
        # Should move elephant away
        self.assertEqual(best_action.type, ActionType.MOVE)
        self.assertEqual(best_action.piece.type, "elephant")
        # Should not move to (1, 2) where mouse is
        self.assertNotEqual(best_action.target_pos, (1, 2))
    
    def test_elephant_cannot_capture_mouse(self):
        """Elephant should not be able to capture mouse"""
        elephant = create_piece("elephant", True, 1, 1)
        mouse = create_piece("mouse", False, 1, 2)
        
        can_capture = self.ai.can_capture(elephant, mouse)
        self.assertFalse(can_capture,
            "Elephant should not be able to capture mouse")
    
    def test_mouse_can_capture_elephant(self):
        """Mouse should be able to capture elephant"""
        mouse = create_piece("mouse", True, 1, 1)
        elephant = create_piece("elephant", False, 1, 2)
        
        can_capture = self.ai.can_capture(mouse, elephant)
        self.assertTrue(can_capture,
            "Mouse should be able to capture elephant")


class TestIntegration(unittest.TestCase):
    """Integration tests for complete game scenarios"""
    
    def setUp(self):
        self.ai = AIPlayer(depth=3)
        self.board = create_empty_board()
        self.cells = create_flipped_cells()
    
    def test_takes_high_value_even_with_risk(self):
        """AI should take high-value capture even with some risk"""
        # Blue elephant can capture red tiger (6 points), but red lion threatens after
        self.board[1][1] = create_piece("elephant", True, 1, 1)  # power 8
        self.board[1][2] = create_piece("tiger", False, 1, 2)    # power 6, capturable
        self.board[1][3] = create_piece("lion", False, 1, 3)     # power 7, threatens after
        
        actions = self.ai.get_valid_actions(self.board, self.cells)
        best_action = self.ai.select_best_action(actions, self.board, self.cells)
        
        # Should capture tiger (6 points) - it's a high value target (>= 5)
        # Even though lion threatens after, net value is positive
        self.assertEqual(best_action.type, ActionType.CAPTURE)
        self.assertEqual(best_action.target_piece.type, "tiger",
            "Should capture high-value tiger even with risk")
    
    def test_complex_board_prefers_captures(self):
        """In complex board state, AI should still prioritize captures"""
        # Multiple pieces on board
        self.board[0][0] = create_piece("lion", True, 0, 0)
        self.board[0][1] = create_piece("wolf", False, 0, 1)  # Capturable
        self.board[2][2] = create_piece("tiger", True, 2, 2)
        self.board[3][3] = create_piece("elephant", False, 3, 3)
        
        actions = self.ai.get_valid_actions(self.board, self.cells)
        best_action = self.ai.select_best_action(actions, self.board, self.cells)
        
        self.assertEqual(best_action.type, ActionType.CAPTURE,
            "Should prioritize capture over other moves")


def run_all_tests():
    """Run all tests with verbose output"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestScoreMaximizationConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestCaptureValuePriority))
    suite.addTests(loader.loadTestsFromTestCase(TestEqualPowerTrades))
    suite.addTests(loader.loadTestsFromTestCase(TestAggressivePositioning))
    suite.addTests(loader.loadTestsFromTestCase(TestActionPriority))
    suite.addTests(loader.loadTestsFromTestCase(TestBoardEvaluation))
    suite.addTests(loader.loadTestsFromTestCase(TestNetCaptureValue))
    suite.addTests(loader.loadTestsFromTestCase(TestWillBeCapturedAfter))
    suite.addTests(loader.loadTestsFromTestCase(TestElephantMouseInteraction))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
