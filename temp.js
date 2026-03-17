// Game State
const BOARD_SIZE = 12;
let board = [];
let playerRook = null;
let selectedCell = null;
let validMoves = [];
let score = 0;
let turn = 1;
let capturedCount = 0;
let gameOver = false;
let canRevive = true;
let turnsUntilNextSpawn = 0;
let nextPieces = [];
let nextPieceCount = 0;
let isPlayerTurn = true;
let highlightedCells = []; // Cells to highlight (last moved/added)

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

// Initialize the game
function initGame() {
    board = Array(BOARD_SIZE).fill(null).map(() => Array(BOARD_SIZE).fill(null));
    playerRook = null;
    selectedCell = null;
    validMoves = [];
    score = 0;
    turn = 1;
    capturedCount = 0;
    gameOver = false;
    canRevive = true;
    isPlayerTurn = true;
    highlightedCells = [];

    // Place player's rook randomly
    const row = Math.floor(Math.random() * BOARD_SIZE);
    const col = Math.floor(Math.random() * BOARD_SIZE);
    playerRook = { row, col };
    board[row][col] = { type: 'PLAYER_ROOK', isPlayer: true };

    // Set up next spawn
    setupNextSpawn();

    // Update UI
    document.getElementById('revive-btn').disabled = false;
    document.getElementById('game-over').classList.remove('show');

    renderBoard();
    updateStats();
}

// Weighted random piece selection
// Rates decrease: pawn > knight > bishop > rook > queen > king
function getWeightedRandomPiece(includeAll = false) {
    if (includeAll) {
        // All pieces with decreasing probability
        const weights = [
            { piece: 'PAWN', weight: 30 },
            { piece: 'KNIGHT', weight: 25 },
            { piece: 'BISHOP', weight: 20 },
            { piece: 'ROOK', weight: 12 },
            { piece: 'QUEEN', weight: 8 },
            { piece: 'KING', weight: 5 }
        ];
        const totalWeight = weights.reduce((sum, w) => sum + w.weight, 0);
        let random = Math.random() * totalWeight;
        for (const w of weights) {
            random -= w.weight;
            if (random <= 0) return w.piece;
        }
        return 'PAWN';
    } else {
        // Basic pieces only (turn 2)
        const weights = [
            { piece: 'PAWN', weight: 50 },
            { piece: 'KNIGHT', weight: 30 },
            { piece: 'BISHOP', weight: 20 }
        ];
        const totalWeight = weights.reduce((sum, w) => sum + w.weight, 0);
        let random = Math.random() * totalWeight;
        for (const w of weights) {
            random -= w.weight;
            if (random <= 0) return w.piece;
        }
        return 'PAWN';
    }
}

// Set up next piece spawn info
function setupNextSpawn() {
    if (turn === 1) {
        // After player's first turn, computer will place pieces
        turnsUntilNextSpawn = 1;
        nextPieceCount = Math.random() < 0.5 ? 1 : 2;
        nextPieces = [];
        for (let i = 0; i < nextPieceCount; i++) {
            nextPieces.push(getWeightedRandomPiece(false));
        }
    } else {
        // Random X turns (1-4)
        turnsUntilNextSpawn = Math.floor(Math.random() * 4) + 1;
        nextPieceCount = Math.random() < 0.5 ? 1 : 2;
        nextPieces = [];
        for (let i = 0; i < nextPieceCount; i++) {
            nextPieces.push(getWeightedRandomPiece(true));
        }
    }
    updateNextPieceDisplay();
}

// Update the next piece display
function updateNextPieceDisplay() {
    const nextPieceEl = document.getElementById('next-piece');
    const turnsUntilEl = document.getElementById('turns-until');
    const nextCountEl = document.getElementById('next-count');

    if (nextPieces.length > 0) {
        const symbols = nextPieces.map(p => PIECES[p].symbol).join(' ');
        nextPieceEl.textContent = symbols;
        turnsUntilEl.textContent = turnsUntilNextSpawn;
        nextCountEl.textContent = `(${nextPieceCount} quân)`;
    } else {
        nextPieceEl.textContent = '-';
        turnsUntilEl.textContent = '-';
        nextCountEl.textContent = '';
    }
}

// Render the chess board
function renderBoard() {
    const boardEl = document.getElementById('board');
    boardEl.innerHTML = '';

    // Find cells where player is in danger
    const dangerCells = findDangerCells();

    // Always calculate valid moves when it's player's turn
    const currentValidMoves = (isPlayerTurn && playerRook)
        ? getValidMovesForRook(playerRook.row, playerRook.col)
        : validMoves;

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

            // Check if this is a valid move (always show when player turn)
            const moveInfo = currentValidMoves.find(m => m.row === row && m.col === col);
            if (moveInfo) {
                if (moveInfo.isCapture) {
                    cell.classList.add('valid-capture');
                } else {
                    cell.classList.add('valid-move');
                }
            }

            // Check if this cell is in danger (always show all danger cells when player turn)
            if (isPlayerTurn && dangerCells.some(d => d.row === row && d.col === col)) {
                cell.classList.add('danger');
            }

            // Check if this cell should be highlighted (last computer move/spawn)
            if (highlightedCells.some(h => h.row === row && h.col === col)) {
                cell.classList.add('highlighted');
            }

            // Add piece if exists
            const piece = board[row][col];
            if (piece) {
                const pieceEl = document.createElement('span');
                pieceEl.className = `piece ${piece.isPlayer ? 'player' : 'enemy'}`;
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
    if (gameOver || !isPlayerTurn) return;

    const piece = board[row][col];

    // If clicking on player's rook, select it
    if (piece && piece.isPlayer) {
        selectedCell = { row, col };
        validMoves = getValidMovesForRook(row, col);
        renderBoard();
        return;
    }

    // If a cell is selected and clicking on a valid move
    if (selectedCell) {
        const moveInfo = validMoves.find(m => m.row === row && m.col === col);
        if (moveInfo) {
            makePlayerMove(row, col, moveInfo.isCapture);
            return;
        }
    }

    // Deselect
    selectedCell = null;
    validMoves = [];
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

// Make player's move
function makePlayerMove(row, col, isCapture) {
    // Clear highlights from computer's turn
    highlightedCells = [];

    // If capturing, add score
    if (isCapture) {
        const capturedPiece = board[row][col];
        score += PIECES[capturedPiece.type].value;
        capturedCount++;
        showMessage(`Ăn ${PIECES[capturedPiece.type].name}! +${PIECES[capturedPiece.type].value} điểm`);
    }

    // Move player's rook
    board[playerRook.row][playerRook.col] = null;
    board[row][col] = { type: 'PLAYER_ROOK', isPlayer: true };
    playerRook = { row, col };

    // Clear selection
    selectedCell = null;
    validMoves = [];

    // Update turn
    turn++;
    turnsUntilNextSpawn--;

    // Set to computer's turn before rendering (so danger is not shown during transition)
    isPlayerTurn = false;

    updateStats();
    renderBoard();

    // Computer's turn
    setTimeout(computerTurn, 500);
}

// Computer's turn
function computerTurn() {
    if (gameOver) return;

    // Clear previous highlights
    highlightedCells = [];

    // First, try to move pieces to attack player
    let attacked = tryAttackPlayer();

    if (attacked) {
        // Player was captured
        if (!canRevive) {
            endGame();
            return;
        } else {
            showMessage('Quân xe của bạn bị tấn công! Sử dụng nút Hồi sinh để tiếp tục!');
            document.getElementById('revive-btn').classList.add('pulse');
            // Game pauses until player uses revive or game over
            return;
        }
    }

    // Spawn new pieces if countdown reaches 0
    if (turnsUntilNextSpawn <= 0) {
        spawnEnemyPieces();
        setupNextSpawn();
    }

    updateNextPieceDisplay();

    // Back to player's turn (set before renderBoard so danger is shown)
    isPlayerTurn = true;

    renderBoard();
}

// Try to attack player with existing pieces
function tryAttackPlayer() {
    for (let row = 0; row < BOARD_SIZE; row++) {
        for (let col = 0; col < BOARD_SIZE; col++) {
            const piece = board[row][col];
            if (piece && !piece.isPlayer) {
                const moves = getEnemyMoves(row, col, piece.type);
                // Check if any move can capture player's rook
                for (const move of moves) {
                    if (move.row === playerRook.row && move.col === playerRook.col) {
                        // Move this piece to attack
                        board[row][col] = null;
                        board[move.row][move.col] = piece;
                        highlightedCells.push({ row: move.row, col: move.col });
                        showMessage(`${PIECES[piece.type].name} tấn công quân xe của bạn!`);
                        return true;
                    }
                }
            }
        }
    }

    // Move enemy pieces strategically (closer to player)
    moveEnemyPiecesCloser();

    return false;
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
                    moves.push({ row: nr, col: nc });
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
                        moves.push({ row: nr, col: nc });
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
                        if (target.isPlayer) moves.push({ row: nr, col: nc });
                        break;
                    }
                    moves.push({ row: nr, col: nc });
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
                    if (!target || target.isPlayer) {
                        moves.push({ row: nr, col: nc });
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
                        if (target.isPlayer) moves.push({ row: nr, col: nc });
                        break;
                    }
                    moves.push({ row: nr, col: nc });
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
                        if (target.isPlayer) moves.push({ row: nr, col: nc });
                        break;
                    }
                    moves.push({ row: nr, col: nc });
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
                    if (!target || target.isPlayer) {
                        moves.push({ row: nr, col: nc });
                    }
                }
            }
            break;
    }

    return moves;
}

// Move enemy pieces closer to player
function moveEnemyPiecesCloser() {
    const enemies = [];
    for (let row = 0; row < BOARD_SIZE; row++) {
        for (let col = 0; col < BOARD_SIZE; col++) {
            const piece = board[row][col];
            if (piece && !piece.isPlayer) {
                enemies.push({ row, col, piece });
            }
        }
    }

    // Move up to 2 pieces
    const movedCount = Math.min(2, enemies.length);
    const shuffled = enemies.sort(() => Math.random() - 0.5);

    for (let i = 0; i < movedCount; i++) {
        const enemy = shuffled[i];
        const moves = getEnemyMoves(enemy.row, enemy.col, enemy.piece.type);

        if (moves.length > 0) {
            // Find move that gets closest to player
            let bestMove = moves[0];
            let bestDist = getDistance(bestMove.row, bestMove.col, playerRook.row, playerRook.col);

            for (const move of moves) {
                const dist = getDistance(move.row, move.col, playerRook.row, playerRook.col);
                if (dist < bestDist) {
                    bestDist = dist;
                    bestMove = move;
                }
            }

            // Make the move
            board[enemy.row][enemy.col] = null;
            board[bestMove.row][bestMove.col] = enemy.piece;
            highlightedCells.push({ row: bestMove.row, col: bestMove.col });
        }
    }
}

// Calculate distance between two cells
function getDistance(r1, c1, r2, c2) {
    return Math.abs(r1 - r2) + Math.abs(c1 - c2);
}

// Spawn enemy pieces
function spawnEnemyPieces() {
    for (const pieceType of nextPieces) {
        // Find random empty cell
        let attempts = 0;
        while (attempts < 100) {
            const row = Math.floor(Math.random() * BOARD_SIZE);
            const col = Math.floor(Math.random() * BOARD_SIZE);

            if (!board[row][col]) {
                // Don't spawn directly adjacent to player
                const dist = getDistance(row, col, playerRook.row, playerRook.col);
                if (dist >= 2) {
                    board[row][col] = { type: pieceType, isPlayer: false };
                    highlightedCells.push({ row, col });
                    showMessage(`${PIECES[pieceType].name} xuất hiện!`);
                    break;
                }
            }
            attempts++;
        }
    }
}

// Update stats display
function updateStats() {
    document.getElementById('score').textContent = score;
    document.getElementById('turn').textContent = turn;
    document.getElementById('captured').textContent = capturedCount;
}

// Show message
function showMessage(text) {
    const msgEl = document.getElementById('message');
    msgEl.textContent = text;
    msgEl.classList.add('show');
    setTimeout(() => {
        msgEl.classList.remove('show');
    }, 2000);
}

// Revive player
function revivePlayer() {
    if (!canRevive || gameOver) return;

    canRevive = false;
    document.getElementById('revive-btn').disabled = true;
    document.getElementById('revive-btn').classList.remove('pulse');

    // Restore player's rook at the same position
    board[playerRook.row][playerRook.col] = { type: 'PLAYER_ROOK', isPlayer: true };

    showMessage('Hồi sinh thành công! Tiếp tục chơi!');

    // Remove the enemy piece that captured the player
    // (Find any enemy on player's position and remove surrounding threats)

    renderBoard();
    isPlayerTurn = true;
}

// End game
function endGame() {
    gameOver = true;
    document.getElementById('final-score').textContent = score;
    document.getElementById('game-over').classList.add('show');
}

// Restart game
function restartGame() {
    initGame();
}

// Start the game
initGame();
