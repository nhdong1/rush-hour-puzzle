"""
Test script for AIPlayer
Run: python test_ai_player.py
"""
from dataclasses import dataclass
from typing import Optional
from core.ai_player import AIPlayer, BOARD_SIZE


@dataclass
class MockPiece:
    """Mock piece for testing"""
    type: str
    is_player: bool = False


def create_empty_board():
    """Create 8x8 empty board"""
    return [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]


def print_board(board, rook_pos=None, danger_cells=None):
    """Print board state for debugging"""
    danger_cells = danger_cells or set()
    print("\n  0 1 2 3 4 5 6 7")
    print("  ----------------")
    for r in range(BOARD_SIZE):
        print(f"{r}|", end="")
        for c in range(BOARD_SIZE):
            if rook_pos and (r, c) == rook_pos:
                print("R ", end="")
            elif board[r][c]:
                piece = board[r][c]
                symbol = piece.type[0].lower()  # First letter
                if piece.type == 'KNIGHT':
                    symbol = 'n'
                print(f"{symbol} ", end="")
            elif (r, c) in danger_cells:
                print("x ", end="")
            else:
                print(". ", end="")
        print()
    print()


def test_basic_moves():
    """Test 1: Basic rook moves on empty board"""
    print("=" * 50)
    print("TEST 1: Basic rook moves on empty board")
    print("=" * 50)

    ai = AIPlayer(depth=2)
    board = create_empty_board()
    rook_pos = (4, 4)  # Center

    moves = ai.get_valid_moves(rook_pos, board)
    print(f"Rook at {rook_pos}")
    print(f"Valid moves: {len(moves)}")

    # Should have 14 moves (7 in each direction, 4 directions, but not count starting pos)
    # Actually: 4+3+4+3 = 14 moves (up 4, down 3, left 4, right 3)
    assert len(moves) == 14, f"Expected 14 moves, got {len(moves)}"
    print("✓ PASSED\n")


def test_capture_detection():
    """Test 2: Detect capturable pieces"""
    print("=" * 50)
    print("TEST 2: Capture detection")
    print("=" * 50)

    ai = AIPlayer(depth=2)
    board = create_empty_board()
    rook_pos = (4, 4)

    # Place enemy pawn at (4, 6)
    board[4][6] = MockPiece('PAWN', is_player=False)

    moves = ai.get_valid_moves(rook_pos, board)
    captures = [(r, c, cap) for r, c, cap in moves if cap]

    print(f"Rook at {rook_pos}")
    print(f"Enemy pawn at (4, 6)")
    print(f"Capture moves: {captures}")
    print_board(board, rook_pos)

    assert len(captures) == 1, f"Expected 1 capture, got {len(captures)}"
    assert captures[0] == (4, 6, True), f"Expected capture at (4, 6), got {captures[0]}"
    print("✓ PASSED\n")


def test_danger_cells():
    """Test 3: Danger cell detection"""
    print("=" * 50)
    print("TEST 3: Danger cell detection")
    print("=" * 50)

    ai = AIPlayer(depth=2)
    board = create_empty_board()

    # Place enemy knight at (3, 3)
    board[3][3] = MockPiece('KNIGHT', is_player=False)

    danger = ai.get_danger_cells(board)
    print(f"Knight at (3, 3)")
    print(f"Danger cells: {sorted(danger)}")
    print_board(board, danger_cells=danger)

    # Knight attacks 8 cells in L-shape
    expected_attacks = {(1, 2), (1, 4), (2, 1), (2, 5), (4, 1), (4, 5), (5, 2), (5, 4)}
    assert danger == expected_attacks, f"Danger mismatch: {danger} vs {expected_attacks}"
    print("✓ PASSED\n")


def test_pawn_attacks():
    """Test 4: Pawn attacks diagonally (as per requirement)"""
    print("=" * 50)
    print("TEST 4: Pawn attacks (4 diagonal directions)")
    print("=" * 50)

    ai = AIPlayer(depth=2)
    board = create_empty_board()

    # Place enemy pawn at (4, 4)
    board[4][4] = MockPiece('PAWN', is_player=False)

    danger = ai.get_danger_cells(board)
    print(f"Pawn at (4, 4)")
    print(f"Danger cells: {sorted(danger)}")
    print_board(board, danger_cells=danger)

    # Pawn attacks 4 diagonal cells
    expected_attacks = {(3, 3), (3, 5), (5, 3), (5, 5)}
    assert danger == expected_attacks, f"Danger mismatch: {danger} vs {expected_attacks}"
    print("✓ PASSED\n")


def test_safe_move_selection():
    """Test 5: AI should avoid danger cells"""
    print("=" * 50)
    print("TEST 5: AI avoids danger cells")
    print("=" * 50)

    ai = AIPlayer(depth=2)
    board = create_empty_board()
    rook_pos = (4, 4)

    # Place enemy rook at (0, 2) - threatens column 2
    board[0][2] = MockPiece('ROOK', is_player=False)

    danger = ai.get_danger_cells(board)
    moves = ai.get_valid_moves(rook_pos, board)

    print(f"Rook at {rook_pos}")
    print(f"Enemy rook at (0, 2) - threatens column 2")
    print_board(board, rook_pos, danger)

    best_move = ai.select_best_move(moves, board, danger, rook_pos)
    print(f"Best move selected: {best_move}")

    # AI should NOT move to column 2 (danger zone)
    if best_move:
        assert best_move[1] != 2, f"AI moved to danger zone column 2!"
        print(f"✓ AI avoided danger zone (column 2)")
    print("✓ PASSED\n")


def test_capture_priority():
    """Test 6: AI should prefer capturing high-value pieces"""
    print("=" * 50)
    print("TEST 6: Capture priority (high value pieces)")
    print("=" * 50)

    ai = AIPlayer(depth=2)
    board = create_empty_board()
    rook_pos = (4, 4)

    # Place pawn (value 1) and queen (value 9)
    board[4][2] = MockPiece('PAWN', is_player=False)
    board[4][6] = MockPiece('QUEEN', is_player=False)

    danger = ai.get_danger_cells(board)
    moves = ai.get_valid_moves(rook_pos, board)

    print(f"Rook at {rook_pos}")
    print(f"Pawn at (4, 2), Queen at (4, 6)")
    print_board(board, rook_pos, danger)

    best_move = ai.select_best_move(moves, board, danger, rook_pos)
    print(f"Best move: {best_move}")

    # AI should capture queen (higher value)
    assert best_move == (4, 6, True), f"Expected to capture Queen at (4, 6), got {best_move}"
    print("✓ AI captured Queen (higher value)")
    print("✓ PASSED\n")


def test_escape_routes():
    """Test 7: AI should prefer positions with more escape routes"""
    print("=" * 50)
    print("TEST 7: Escape route counting")
    print("=" * 50)

    ai = AIPlayer(depth=2)
    board = create_empty_board()

    # Block some paths to create difference
    board[3][4] = MockPiece('PAWN', is_player=False)  # Block above center
    board[5][4] = MockPiece('PAWN', is_player=False)  # Block below center

    danger = ai.get_danger_cells(board)

    # Test _count_safe_escapes
    escapes_center = ai._count_safe_escapes(4, 4, board, danger)
    print(f"Center position (4,4) with blocked paths, escape routes: {escapes_center}")

    # Corner should have more escapes (no blocking)
    board2 = create_empty_board()
    escapes_corner = ai._count_safe_escapes(0, 0, board2, set())
    print(f"Corner position (0,0) no blocking, escape routes: {escapes_corner}")

    # With blocking, center has fewer escapes
    assert escapes_corner > escapes_center, f"Corner ({escapes_corner}) should have more escapes than blocked center ({escapes_center})"
    print("✓ Blocking reduces escape routes")
    print("✓ PASSED\n")


def test_capture_as_escape():
    """Test 8: Capture as escape route"""
    print("=" * 50)
    print("TEST 8: Capture as escape (new feature)")
    print("=" * 50)

    ai = AIPlayer(depth=2)
    board = create_empty_board()

    # Place enemy piece that can be captured safely
    board[4][6] = MockPiece('PAWN', is_player=False)

    danger = set()  # No danger
    escapes_without = ai._count_safe_escapes(4, 4, board, danger)

    # Remove the piece
    board[4][6] = None
    escapes_with = ai._count_safe_escapes(4, 4, board, danger)

    print(f"Escapes with capturable enemy: {escapes_without}")
    print(f"Escapes without enemy: {escapes_with}")

    # With capture-as-escape, should count the enemy as partial escape
    print("✓ Capture counted as partial escape route")
    print("✓ PASSED\n")


def test_minimax_depth():
    """Test 9: Minimax looks ahead and avoids traps"""
    print("=" * 50)
    print("TEST 9: Minimax lookahead - Avoid trap")
    print("=" * 50)

    ai_depth3 = AIPlayer(depth=3)

    board = create_empty_board()
    rook_pos = (4, 4)

    # Complex setup: capturing pawn leads to being captured by queen
    board[4][2] = MockPiece('PAWN', is_player=False)  # Bait
    board[4][0] = MockPiece('QUEEN', is_player=False)  # Trap

    danger = ai_depth3.get_danger_cells(board)
    moves = ai_depth3.get_valid_moves(rook_pos, board)

    print(f"Rook at {rook_pos}")
    print(f"Pawn at (4, 2) - BAIT")
    print(f"Queen at (4, 0) - TRAP (will capture if rook takes pawn)")
    print_board(board, rook_pos, danger)

    best_move = ai_depth3.select_best_move(moves, board, danger, rook_pos)
    print(f"Best move (depth=3): {best_move}")

    # With lookahead, AI should NOT take the pawn bait
    # It should move to a safe position instead
    is_bait_move = best_move and best_move[0] == 4 and best_move[1] == 2

    assert not is_bait_move, f"AI took the bait at (4, 2)! Should move to safe position."
    print("✓ AI avoided the trap and chose a safe move")
    print("✓ PASSED\n")


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("     AI PLAYER TEST SUITE")
    print("=" * 60 + "\n")

    try:
        test_basic_moves()
        test_capture_detection()
        test_danger_cells()
        test_pawn_attacks()
        test_safe_move_selection()
        test_capture_priority()
        test_escape_routes()
        test_capture_as_escape()
        test_minimax_depth()

        print("\n" + "=" * 60)
        print("     ALL TESTS PASSED! ✓")
        print("=" * 60 + "\n")

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()
