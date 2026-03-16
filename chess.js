// ==================== CHESS PUZZLE ====================
// Tutorial Mode - Game State
const BOARD_SIZE = 8;
let board = [];
let playerRook = null;
let selectedCell = null;
let validMoves = [];
let isPlayerTurn = true;
let gamePhase = 'place_rook'; // 'place_rook', 'playing'
let actionMode = 'move'; // 'move', 'add', 'remove'
let selectedPieceType = 'PAWN';
let lastState = null; // For undo after capture

// Piece definitions
const PIECES = {
    PAWN: { symbol: '♟', name: 'Tốt', value: 1 },
    BISHOP: { symbol: '♝', name: 'Tượng', value: 3 },
    KNIGHT: { symbol: '♞', name: 'Mã', value: 3 },
    ROOK: { symbol: '♜', name: 'Xe', value: 5 },
    QUEEN: { symbol: '♛', name: 'Hậu', value: 9 },
    KING: { symbol: '♚', name: 'Vua', value: 10 },
    PLAYER_ROOK: { symbol: '♖', name: 'Xe (Bạn)', value: 0 }
};

// Initialize the chess game
export function initChess() {
    setupEventListeners();
    initTutorial();
}

// Setup event listeners
function setupEventListeners() {
    // Action mode buttons
    document.getElementById('chess-btn-move').addEventListener('click', () => setActionMode('move'));
    document.getElementById('chess-btn-add').addEventListener('click', () => setActionMode('add'));
    document.getElementById('chess-btn-remove').addEventListener('click', () => setActionMode('remove'));

    // Control buttons
    document.getElementById('chess-btn-switch-turn').addEventListener('click', switchTurn);
    document.getElementById('chess-btn-clear').addEventListener('click', clearEnemies);
    document.getElementById('chess-btn-restart').addEventListener('click', restartTutorial);

    // Overlay buttons
    document.getElementById('chess-btn-undo').addEventListener('click', undoCapture);
    document.getElementById('chess-btn-restart-overlay').addEventListener('click', restartTutorial);

    // Piece selector buttons
    document.querySelectorAll('#chess-piece-selector-box .chess-piece-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const type = btn.dataset.piece;
            selectPieceType(type, btn);
        });
    });
}

// Initialize the tutorial
function initTutorial() {
    board = Array(BOARD_SIZE).fill(null).map(() => Array(BOARD_SIZE).fill(null));
    playerRook = null;
    selectedCell = null;
    validMoves = [];
    isPlayerTurn = true;
    gamePhase = 'place_rook';
    actionMode = 'move';
    lastState = null;

    document.getElementById('chess-captured-overlay').classList.remove('show');

    updateUI();
    renderBoard();
}

// Save state for undo
function saveState() {
    lastState = {
        board: board.map(row => row.map(cell => cell ? { ...cell } : null)),
        playerRook: playerRook ? { ...playerRook } : null
    };
}

// Restore state after capture
function undoCapture() {
    if (lastState) {
        board = lastState.board;
        playerRook = lastState.playerRook;
        document.getElementById('chess-captured-overlay').classList.remove('show');
        renderBoard();
        updateUI();
        showMessage('Đã hoàn tác!', 'info');
    }
}

// Render the chess board
function renderBoard() {
    const boardEl = document.getElementById('chess-board');
    boardEl.innerHTML = '';

    // Find danger cells
    const dangerCells = findDangerCells();

    // Get valid moves for selected piece
    let currentValidMoves = [];
    if (selectedCell && actionMode === 'move') {
        const piece = board[selectedCell.row][selectedCell.col];
        if (piece) {
            if (piece.isPlayer) {
                currentValidMoves = getValidMovesForRook(selectedCell.row, selectedCell.col);
            } else {
                currentValidMoves = getEnemyMoves(selectedCell.row, selectedCell.col, piece.type);
            }
        }
    }

    for (let row = 0; row < BOARD_SIZE; row++) {
        for (let col = 0; col < BOARD_SIZE; col++) {
            const cell = document.createElement('div');
            cell.className = `cell ${(row + col) % 2 === 0 ? 'white' : 'black'}`;
            cell.dataset.row = row;
            cell.dataset.col = col;

            // Check if this is the selected cell
            if (selectedCell && selectedCell.row === row && selectedCell.col === col) {
                cell.classList.add('selected');
            }

            // Check if this is a valid move
            const moveInfo = currentValidMoves.find(m => m.row === row && m.col === col);
            if (moveInfo && actionMode === 'move') {
                if (moveInfo.isCapture) {
                    cell.classList.add('valid-capture');
                } else {
                    cell.classList.add('valid-move');
                }
            }

            // Show danger zones when player's rook exists
            if (playerRook && dangerCells.some(d => d.row === row && d.col === col)) {
                cell.classList.add('danger');
            }

            // Add piece if exists
            const piece = board[row][col];
            if (piece) {
                const pieceEl = document.createElement('span');
                pieceEl.className = `chess-piece ${piece.isPlayer ? 'player' : 'enemy'}`;
                pieceEl.textContent = PIECES[piece.type].symbol;
                cell.appendChild(pieceEl);
            }

            cell.addEventListener('click', () => handleCellClick(row, col));
            boardEl.appendChild(cell);
        }
    }
}

// Find cells where enemy pieces can attack
function findDangerCells() {
    const dangers = [];

    for (let row = 0; row < BOARD_SIZE; row++) {
        for (let col = 0; col < BOARD_SIZE; col++) {
            const piece = board[row][col];
            if (piece && !piece.isPlayer) {
                const attacks = getAttackMoves(row, col, piece.type);
                dangers.push(...attacks);
            }
        }
    }

    return dangers;
}

// Get attack positions for an enemy piece
function getAttackMoves(row, col, pieceType) {
    const attacks = [];

    switch (pieceType) {
        case 'PAWN':
            // Pawn attacks diagonally
            const pawnDirs = [[-1, -1], [-1, 1], [1, -1], [1, 1]];
            for (const [dr, dc] of pawnDirs) {
                const nr = row + dr;
                const nc = col + dc;
                if (isValidPosition(nr, nc)) {
                    attacks.push({ row: nr, col: nc });
                }
            }
            break;

        case 'BISHOP':
            // Bishop attacks diagonally
            const bishopDirs = [[-1, -1], [-1, 1], [1, -1], [1, 1]];
            for (const [dr, dc] of bishopDirs) {
                for (let i = 1; i < BOARD_SIZE; i++) {
                    const nr = row + dr * i;
                    const nc = col + dc * i;
                    if (!isValidPosition(nr, nc)) break;
                    attacks.push({ row: nr, col: nc });
                    if (board[nr][nc]) break;
                }
            }
            break;

        case 'KNIGHT':
            // Knight attacks in L-shape
            const knightMoves = [
                [-2, -1], [-2, 1], [-1, -2], [-1, 2],
                [1, -2], [1, 2], [2, -1], [2, 1]
            ];
            for (const [dr, dc] of knightMoves) {
                const nr = row + dr;
                const nc = col + dc;
                if (isValidPosition(nr, nc)) {
                    attacks.push({ row: nr, col: nc });
                }
            }
            break;

        case 'ROOK':
            // Rook attacks horizontally and vertically
            const rookDirs = [[-1, 0], [1, 0], [0, -1], [0, 1]];
            for (const [dr, dc] of rookDirs) {
                for (let i = 1; i < BOARD_SIZE; i++) {
                    const nr = row + dr * i;
                    const nc = col + dc * i;
                    if (!isValidPosition(nr, nc)) break;
                    attacks.push({ row: nr, col: nc });
                    if (board[nr][nc]) break;
                }
            }
            break;

        case 'QUEEN':
            // Queen attacks like rook + bishop
            const queenDirs = [
                [-1, 0], [1, 0], [0, -1], [0, 1],
                [-1, -1], [-1, 1], [1, -1], [1, 1]
            ];
            for (const [dr, dc] of queenDirs) {
                for (let i = 1; i < BOARD_SIZE; i++) {
                    const nr = row + dr * i;
                    const nc = col + dc * i;
                    if (!isValidPosition(nr, nc)) break;
                    attacks.push({ row: nr, col: nc });
                    if (board[nr][nc]) break;
                }
            }
            break;

        case 'KING':
            // King attacks one square in all directions
            const kingDirs = [
                [-1, 0], [1, 0], [0, -1], [0, 1],
                [-1, -1], [-1, 1], [1, -1], [1, 1]
            ];
            for (const [dr, dc] of kingDirs) {
                const nr = row + dr;
                const nc = col + dc;
                if (isValidPosition(nr, nc)) {
                    attacks.push({ row: nr, col: nc });
                }
            }
            break;
    }

    return attacks;
}

// Check if position is valid
function isValidPosition(row, col) {
    return row >= 0 && row < BOARD_SIZE && col >= 0 && col < BOARD_SIZE;
}

// Handle cell click
function handleCellClick(row, col) {
    // Phase 1: Place player's rook
    if (gamePhase === 'place_rook') {
        playerRook = { row, col };
        board[row][col] = { type: 'PLAYER_ROOK', isPlayer: true };
        gamePhase = 'playing';
        showMessage('Quân xe đã được đặt! Bây giờ bạn có thể thêm quân địch.', 'info');
        updateUI();
        renderBoard();
        return;
    }

    const piece = board[row][col];

    // Handle based on action mode
    switch (actionMode) {
        case 'move':
            handleMoveAction(row, col, piece);
            break;
        case 'add':
            handleAddAction(row, col, piece);
            break;
        case 'remove':
            handleRemoveAction(row, col, piece);
            break;
    }
}

// Handle move action
function handleMoveAction(row, col, piece) {
    // If clicking on a piece, select it
    if (piece) {
        // In player turn, can only select player's rook
        // In enemy turn, can only select enemy pieces
        if (isPlayerTurn && piece.isPlayer) {
            selectedCell = { row, col };
            validMoves = getValidMovesForRook(row, col);
            renderBoard();
            return;
        } else if (!isPlayerTurn && !piece.isPlayer) {
            selectedCell = { row, col };
            validMoves = getEnemyMoves(row, col, piece.type);
            renderBoard();
            return;
        }
    }

    // If a cell is selected and clicking on a valid move
    if (selectedCell) {
        const selectedPiece = board[selectedCell.row][selectedCell.col];
        let moves = [];

        if (selectedPiece.isPlayer) {
            moves = getValidMovesForRook(selectedCell.row, selectedCell.col);
        } else {
            moves = getEnemyMoves(selectedCell.row, selectedCell.col, selectedPiece.type);
        }

        const moveInfo = moves.find(m => m.row === row && m.col === col);
        if (moveInfo) {
            saveState();
            makeMove(selectedCell.row, selectedCell.col, row, col, selectedPiece);
            selectedCell = null;
            validMoves = [];
            return;
        }
    }

    // Deselect
    selectedCell = null;
    validMoves = [];
    renderBoard();
}

// Handle add action
function handleAddAction(row, col, piece) {
    if (piece) {
        showMessage('Ô này đã có quân cờ!', 'warning');
        return;
    }

    // Add enemy piece
    board[row][col] = { type: selectedPieceType, isPlayer: false };
    showMessage(`Đã thêm ${PIECES[selectedPieceType].name}!`, 'info');
    updateUI();
    renderBoard();
}

// Handle remove action
function handleRemoveAction(row, col, piece) {
    if (!piece) {
        showMessage('Không có quân cờ để xóa!', 'warning');
        return;
    }

    if (piece.isPlayer) {
        showMessage('Không thể xóa quân xe của bạn!', 'warning');
        return;
    }

    board[row][col] = null;
    showMessage(`Đã xóa ${PIECES[piece.type].name}!`, 'info');
    updateUI();
    renderBoard();
}

// Make a move
function makeMove(fromRow, fromCol, toRow, toCol, piece) {
    const targetPiece = board[toRow][toCol];

    // Check if capturing player's rook
    if (targetPiece && targetPiece.isPlayer && !piece.isPlayer) {
        // Show capture warning
        document.getElementById('chess-captured-overlay').classList.add('show');
        return;
    }

    // Check if player captures enemy
    if (targetPiece && !targetPiece.isPlayer && piece.isPlayer) {
        showMessage(`Ăn ${PIECES[targetPiece.type].name}!`, 'info');
    }

    // Move piece
    board[fromRow][fromCol] = null;
    board[toRow][toCol] = piece;

    // Update player rook position if moving it
    if (piece.isPlayer) {
        playerRook = { row: toRow, col: toCol };
        // Auto switch turn after player moves
        setTimeout(() => {
            switchTurn();
        }, 300);
    }

    updateUI();
    renderBoard();
}

// Get valid moves for player's rook
function getValidMovesForRook(row, col) {
    const moves = [];
    const directions = [[-1, 0], [1, 0], [0, -1], [0, 1]];

    for (const [dr, dc] of directions) {
        for (let i = 1; i < BOARD_SIZE; i++) {
            const nr = row + dr * i;
            const nc = col + dc * i;

            if (!isValidPosition(nr, nc)) break;

            const targetPiece = board[nr][nc];
            if (targetPiece) {
                if (!targetPiece.isPlayer) {
                    // Can capture enemy piece
                    moves.push({ row: nr, col: nc, isCapture: true });
                }
                break; // Can't go further
            } else {
                moves.push({ row: nr, col: nc, isCapture: false });
            }
        }
    }

    return moves;
}

// Get valid moves for enemy piece
function getEnemyMoves(row, col, pieceType) {
    const moves = [];

    switch (pieceType) {
        case 'PAWN':
            // Pawn moves in 4 directions
            const pawnMoves = [[-1, 0], [1, 0], [0, -1], [0, 1]];
            for (const [dr, dc] of pawnMoves) {
                const nr = row + dr;
                const nc = col + dc;
                if (isValidPosition(nr, nc) && !board[nr][nc]) {
                    moves.push({ row: nr, col: nc, isCapture: false });
                }
            }
            // Pawn attacks diagonally
            const pawnAttacks = [[-1, -1], [-1, 1], [1, -1], [1, 1]];
            for (const [dr, dc] of pawnAttacks) {
                const nr = row + dr;
                const nc = col + dc;
                if (isValidPosition(nr, nc)) {
                    const target = board[nr][nc];
                    if (target && target.isPlayer) {
                        moves.push({ row: nr, col: nc, isCapture: true });
                    }
                }
            }
            break;

        case 'BISHOP':
            const bishopDirs = [[-1, -1], [-1, 1], [1, -1], [1, 1]];
            for (const [dr, dc] of bishopDirs) {
                for (let i = 1; i < BOARD_SIZE; i++) {
                    const nr = row + dr * i;
                    const nc = col + dc * i;
                    if (!isValidPosition(nr, nc)) break;
                    const target = board[nr][nc];
                    if (target) {
                        if (target.isPlayer) moves.push({ row: nr, col: nc, isCapture: true });
                        break;
                    }
                    moves.push({ row: nr, col: nc, isCapture: false });
                }
            }
            break;

        case 'KNIGHT':
            const knightMoves = [
                [-2, -1], [-2, 1], [-1, -2], [-1, 2],
                [1, -2], [1, 2], [2, -1], [2, 1]
            ];
            for (const [dr, dc] of knightMoves) {
                const nr = row + dr;
                const nc = col + dc;
                if (isValidPosition(nr, nc)) {
                    const target = board[nr][nc];
                    if (!target) {
                        moves.push({ row: nr, col: nc, isCapture: false });
                    } else if (target.isPlayer) {
                        moves.push({ row: nr, col: nc, isCapture: true });
                    }
                }
            }
            break;

        case 'ROOK':
            const rookDirs = [[-1, 0], [1, 0], [0, -1], [0, 1]];
            for (const [dr, dc] of rookDirs) {
                for (let i = 1; i < BOARD_SIZE; i++) {
                    const nr = row + dr * i;
                    const nc = col + dc * i;
                    if (!isValidPosition(nr, nc)) break;
                    const target = board[nr][nc];
                    if (target) {
                        if (target.isPlayer) moves.push({ row: nr, col: nc, isCapture: true });
                        break;
                    }
                    moves.push({ row: nr, col: nc, isCapture: false });
                }
            }
            break;

        case 'QUEEN':
            const queenDirs = [
                [-1, 0], [1, 0], [0, -1], [0, 1],
                [-1, -1], [-1, 1], [1, -1], [1, 1]
            ];
            for (const [dr, dc] of queenDirs) {
                for (let i = 1; i < BOARD_SIZE; i++) {
                    const nr = row + dr * i;
                    const nc = col + dc * i;
                    if (!isValidPosition(nr, nc)) break;
                    const target = board[nr][nc];
                    if (target) {
                        if (target.isPlayer) moves.push({ row: nr, col: nc, isCapture: true });
                        break;
                    }
                    moves.push({ row: nr, col: nc, isCapture: false });
                }
            }
            break;

        case 'KING':
            const kingDirs = [
                [-1, 0], [1, 0], [0, -1], [0, 1],
                [-1, -1], [-1, 1], [1, -1], [1, 1]
            ];
            for (const [dr, dc] of kingDirs) {
                const nr = row + dr;
                const nc = col + dc;
                if (isValidPosition(nr, nc)) {
                    const target = board[nr][nc];
                    if (!target) {
                        moves.push({ row: nr, col: nc, isCapture: false });
                    } else if (target.isPlayer) {
                        moves.push({ row: nr, col: nc, isCapture: true });
                    }
                }
            }
            break;
    }

    return moves;
}

// Set action mode
function setActionMode(mode) {
    // Player turn only allows 'move' mode
    if (isPlayerTurn && mode !== 'move') {
        showMessage('Lượt người chơi chỉ có thể di chuyển!', 'warning');
        return;
    }

    actionMode = mode;
    selectedCell = null;
    validMoves = [];

    // Update button states
    document.getElementById('chess-btn-move').classList.toggle('active', mode === 'move');
    document.getElementById('chess-btn-add').classList.toggle('active', mode === 'add');
    document.getElementById('chess-btn-remove').classList.toggle('active', mode === 'remove');

    // Show/hide piece selector
    document.getElementById('chess-piece-selector-box').style.display = mode === 'add' ? 'block' : 'none';

    renderBoard();
}

// Select piece type to add
function selectPieceType(type, btnElement) {
    selectedPieceType = type;

    // Update button states
    document.querySelectorAll('#chess-piece-selector-box .chess-piece-btn').forEach(btn => {
        btn.classList.remove('selected');
    });
    btnElement.classList.add('selected');
}

// Switch turn
function switchTurn() {
    isPlayerTurn = !isPlayerTurn;
    selectedCell = null;
    validMoves = [];

    // Reset action mode to 'move' when switching to player turn
    if (isPlayerTurn) {
        actionMode = 'move';
        document.getElementById('chess-btn-move').classList.add('active');
        document.getElementById('chess-btn-add').classList.remove('active');
        document.getElementById('chess-btn-remove').classList.remove('active');
        document.getElementById('chess-piece-selector-box').style.display = 'none';
    }

    updateUI();
    renderBoard();

    const turnName = isPlayerTurn ? 'NGƯỜI CHƠI' : 'MÁY (địch)';
    showMessage(`Đã chuyển sang lượt của ${turnName}`, 'info');
}

// Clear all enemies
function clearEnemies() {
    for (let row = 0; row < BOARD_SIZE; row++) {
        for (let col = 0; col < BOARD_SIZE; col++) {
            const piece = board[row][col];
            if (piece && !piece.isPlayer) {
                board[row][col] = null;
            }
        }
    }
    showMessage('Đã xóa tất cả quân địch!', 'info');
    updateUI();
    renderBoard();
}

// Restart tutorial
function restartTutorial() {
    initTutorial();
    showMessage('Đã làm lại từ đầu!', 'info');
}

// Update UI elements
function updateUI() {
    // Update turn indicator
    const turnIndicator = document.getElementById('chess-turn-indicator');
    if (isPlayerTurn) {
        turnIndicator.textContent = 'Lượt của: NGƯỜI CHƠI';
        turnIndicator.className = 'chess-current-turn player-turn';
    } else {
        turnIndicator.textContent = 'Lượt của: MÁY (địch)';
        turnIndicator.className = 'chess-current-turn enemy-turn';
    }

    // Update game status
    const statusEl = document.getElementById('chess-game-status');
    if (gamePhase === 'place_rook') {
        statusEl.textContent = 'Đặt quân xe';
    } else {
        statusEl.textContent = 'Đang chơi';
    }

    // Update enemy count
    let enemyCount = 0;
    for (let row = 0; row < BOARD_SIZE; row++) {
        for (let col = 0; col < BOARD_SIZE; col++) {
            if (board[row][col] && !board[row][col].isPlayer) {
                enemyCount++;
            }
        }
    }
    document.getElementById('chess-enemy-count').textContent = enemyCount;

    // Update danger status
    const dangerStatus = document.getElementById('chess-danger-status');
    if (playerRook) {
        const dangerCells = findDangerCells();
        const isInDanger = dangerCells.some(d => d.row === playerRook.row && d.col === playerRook.col);

        if (isInDanger) {
            dangerStatus.className = 'chess-danger-info';
            dangerStatus.innerHTML = '⚠️ Quân xe đang bị đe dọa!';
        } else {
            dangerStatus.className = 'chess-danger-info safe';
            dangerStatus.innerHTML = '✓ Quân xe đang an toàn';
        }
    } else {
        dangerStatus.className = 'chess-danger-info safe';
        dangerStatus.innerHTML = 'Hãy đặt quân xe';
    }

    // Show/hide piece selector based on action mode
    document.getElementById('chess-piece-selector-box').style.display = actionMode === 'add' ? 'block' : 'none';

    // Show/hide action mode buttons based on turn
    // Player turn: only move allowed, hide action buttons
    // Enemy turn: show action buttons
    const actionModeBox = document.getElementById('chess-action-mode-box');
    if (actionModeBox) {
        if (isPlayerTurn && gamePhase === 'playing') {
            actionModeBox.style.display = 'none';
        } else if (!isPlayerTurn) {
            actionModeBox.style.display = 'block';
        }
    }
}

// Show message
function showMessage(text, type = 'default') {
    const msgEl = document.getElementById('chess-message');
    msgEl.textContent = text;
    msgEl.className = 'chess-message show';
    if (type === 'info') msgEl.classList.add('info');
    if (type === 'warning') msgEl.classList.add('warning');

    setTimeout(() => {
        msgEl.classList.remove('show');
    }, 2500);
}
