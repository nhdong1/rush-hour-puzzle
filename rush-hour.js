// ==================== RUSH HOUR PUZZLE MODULE ====================

const ROWS = 6;
const COLS = 6;

let gridContainer;
let nextCarId = 1;
let hasCarX = false;

// Bảng màu cho các xe (tránh màu đỏ vì đã dùng cho xe x)
const CAR_COLORS = [
    '#3498db', '#2ecc71', '#9b59b6', '#f39c12', '#1abc9c',
    '#e67e22', '#34495e', '#16a085', '#8e44ad', '#27ae60',
    '#2980b9', '#d35400', '#c0392b', '#7f8c8d', '#f1c40f',
    '#95a5a6'
];

const carColorMap = {};

// ==================== INITIALIZATION ====================

export function initRushHour() {
    gridContainer = document.getElementById('grid');
    createGrid();
    setupDragAndDrop();
    setupDropZones();
    setupContextMenu();
    setupButtons();
    setTimeout(resetDragDropState, 0);
}

function createGrid() {
    gridContainer.innerHTML = '';
    for (let i = 0; i < ROWS; i++) {
        for (let j = 0; j < COLS; j++) {
            const input = document.createElement('input');
            input.type = 'text';
            input.dataset.row = i;
            input.dataset.col = j;
            input.maxLength = 3;

            input.addEventListener('input', function (e) {
                let value = e.target.value.trim().toLowerCase();

                if (value === 'x' || value === 'X') {
                    e.target.value = 'x';
                    return;
                }

                if (value !== '' && !/^\d+$/.test(value)) {
                    e.target.value = value.replace(/[^\dx]/gi, '');
                    return;
                }

                if (value !== '' && !isNaN(parseInt(value))) {
                    const num = parseInt(value);
                    if (num < 1) {
                        e.target.value = '1';
                    } else if (num > 100) {
                        e.target.value = '100';
                    }
                }
                setTimeout(updateInputStyles, 0);
            });

            gridContainer.appendChild(input);
        }
    }
}

// ==================== DRAG AND DROP ====================

function resetDragDropState() {
    nextCarId = 1;
    hasCarX = false;
    const grid = getArray2D();
    for (let i = 0; i < ROWS; i++) {
        for (let j = 0; j < COLS; j++) {
            if (grid[i][j] === 'x') {
                hasCarX = true;
            }
            if (typeof grid[i][j] === 'number' && grid[i][j] >= nextCarId) {
                nextCarId = grid[i][j] + 1;
            }
        }
    }
    updateInputStyles();
}

function updateInputStyles() {
    const inputs = gridContainer.querySelectorAll('input');
    inputs.forEach(input => {
        input.classList.remove('car-x', 'has-car');
        const value = input.value.trim().toLowerCase();
        if (value === 'x') {
            input.classList.add('car-x', 'has-car');
        } else if (value !== '') {
            input.classList.add('has-car');
            const carId = parseInt(value);
            if (!isNaN(carId)) {
                input.style.backgroundColor = getCarColorForInput(carId);
                input.style.color = 'white';
            }
        } else {
            input.style.backgroundColor = '';
            input.style.color = '';
        }
    });
}

function getCarColorForInput(carId) {
    const colors = [
        '#3498db', '#2ecc71', '#9b59b6', '#f39c12', '#1abc9c',
        '#e67e22', '#34495e', '#16a085', '#8e44ad', '#27ae60',
        '#2980b9', '#d35400', '#c0392b', '#7f8c8d', '#f1c40f'
    ];
    return colors[(carId - 1) % colors.length];
}

function canPlaceCar(startRow, startCol, size, orientation) {
    const grid = getArray2D();

    if (orientation === 'H') {
        if (startCol + size > COLS) return false;
        for (let i = 0; i < size; i++) {
            if (grid[startRow][startCol + i] !== null) return false;
        }
    } else {
        if (startRow + size > ROWS) return false;
        for (let i = 0; i < size; i++) {
            if (grid[startRow + i][startCol] !== null) return false;
        }
    }
    return true;
}

function placeCar(startRow, startCol, size, orientation, carType) {
    const inputs = gridContainer.querySelectorAll('input');
    let carValue;

    if (carType === 'x') {
        carValue = 'x';
        hasCarX = true;
    } else {
        carValue = nextCarId;
        nextCarId++;
    }

    if (orientation === 'H') {
        for (let i = 0; i < size; i++) {
            const index = startRow * COLS + (startCol + i);
            inputs[index].value = carValue;
        }
    } else {
        for (let i = 0; i < size; i++) {
            const index = (startRow + i) * COLS + startCol;
            inputs[index].value = carValue;
        }
    }

    updateInputStyles();
}

// ==================== TOUCH DRAG AND DROP ====================

let touchDragData = null;
let touchDragElement = null;
let touchClone = null;

function setupTouchDragAndDrop() {
    document.querySelectorAll('.draggable-car').forEach(car => {
        car.addEventListener('touchstart', handleTouchStart, { passive: false });
    });

    document.addEventListener('touchmove', handleTouchMove, { passive: false });
    document.addEventListener('touchend', handleTouchEnd);
    document.addEventListener('touchcancel', handleTouchCancel);
}

function handleTouchStart(e) {
    const car = e.currentTarget;
    const type = car.dataset.type;
    const size = parseInt(car.dataset.size);
    const orientation = car.dataset.orientation;

    if (type === 'x' && hasCarX) {
        alert('Chỉ được phép có 1 xe X trên lưới!');
        return;
    }

    e.preventDefault();

    touchDragData = { type, size, orientation };
    touchDragElement = car;
    car.style.opacity = '0.5';

    // Create a clone to follow finger
    touchClone = car.cloneNode(true);
    touchClone.style.position = 'fixed';
    touchClone.style.pointerEvents = 'none';
    touchClone.style.zIndex = '9999';
    touchClone.style.opacity = '0.8';
    touchClone.style.transform = 'scale(0.9)';
    document.body.appendChild(touchClone);

    const touch = e.touches[0];
    positionTouchClone(touch.clientX, touch.clientY);
}

function positionTouchClone(x, y) {
    if (!touchClone) return;
    const rect = touchClone.getBoundingClientRect();
    touchClone.style.left = (x - rect.width / 2) + 'px';
    touchClone.style.top = (y - rect.height / 2) + 'px';
}

function handleTouchMove(e) {
    if (!touchDragData || !touchClone) return;

    e.preventDefault();
    const touch = e.touches[0];
    positionTouchClone(touch.clientX, touch.clientY);

    // Highlight the target cell
    const inputs = gridContainer.querySelectorAll('input');
    inputs.forEach(input => input.classList.remove('drag-over'));

    const targetElement = document.elementFromPoint(touch.clientX, touch.clientY);
    if (targetElement && targetElement.tagName === 'INPUT' && gridContainer.contains(targetElement)) {
        targetElement.classList.add('drag-over');
    }
}

function handleTouchEnd(e) {
    if (!touchDragData) return;

    // Find the element under the last touch
    const touch = e.changedTouches[0];
    const targetElement = document.elementFromPoint(touch.clientX, touch.clientY);

    cleanupTouchDrag();

    if (targetElement && targetElement.tagName === 'INPUT' && gridContainer.contains(targetElement)) {
        const row = parseInt(targetElement.dataset.row);
        const col = parseInt(targetElement.dataset.col);
        const { type, size, orientation } = touchDragData;

        if (type === 'x' && row !== 2) {
            alert('Xe X (đỏ) chỉ được đặt ở hàng 3!');
        } else if (!canPlaceCar(row, col, size, orientation)) {
            alert('Không thể đặt xe ở vị trí này! Kiểm tra xem có đủ chỗ trống không.');
        } else {
            placeCar(row, col, size, orientation, type);
        }
    }

    touchDragData = null;
}

function handleTouchCancel() {
    cleanupTouchDrag();
    touchDragData = null;
}

function cleanupTouchDrag() {
    if (touchDragElement) {
        touchDragElement.style.opacity = '1';
        touchDragElement = null;
    }
    if (touchClone && touchClone.parentNode) {
        touchClone.parentNode.removeChild(touchClone);
        touchClone = null;
    }
    gridContainer.querySelectorAll('input').forEach(input => {
        input.classList.remove('drag-over', 'drag-invalid');
    });
}

// ==================== DESKTOP DRAG AND DROP ====================

function setupDragAndDrop() {
    document.querySelectorAll('.draggable-car').forEach(car => {
        car.addEventListener('dragstart', function (e) {
            const type = this.dataset.type;
            const size = parseInt(this.dataset.size);
            const orientation = this.dataset.orientation;

            if (type === 'x' && hasCarX) {
                e.preventDefault();
                alert('Chỉ được phép có 1 xe X trên lưới!');
                return;
            }

            e.dataTransfer.setData('text/plain', JSON.stringify({
                type, size, orientation
            }));
            e.dataTransfer.effectAllowed = 'copy';
            this.style.opacity = '0.5';
        });

        car.addEventListener('dragend', function (e) {
            this.style.opacity = '1';
            document.querySelectorAll('.grid-container input').forEach(input => {
                input.classList.remove('drag-over', 'drag-invalid');
            });
        });
    });

    // Setup touch drag and drop for mobile
    setupTouchDragAndDrop();
}

function setupDropZones() {
    const inputs = gridContainer.querySelectorAll('input');

    inputs.forEach(input => {
        input.addEventListener('dragover', function (e) {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'copy';
        });

        input.addEventListener('dragenter', function (e) {
            e.preventDefault();
            this.classList.add('drag-over');
        });

        input.addEventListener('dragleave', function (e) {
            this.classList.remove('drag-over', 'drag-invalid');
        });

        input.addEventListener('drop', function (e) {
            e.preventDefault();
            this.classList.remove('drag-over', 'drag-invalid');

            const row = parseInt(this.dataset.row);
            const col = parseInt(this.dataset.col);

            try {
                const data = JSON.parse(e.dataTransfer.getData('text/plain'));
                const { type, size, orientation } = data;

                if (type === 'x' && row !== 2) {
                    alert('Xe X (đỏ) chỉ được đặt ở hàng 3!');
                    return;
                }

                if (!canPlaceCar(row, col, size, orientation)) {
                    alert('Không thể đặt xe ở vị trí này! Kiểm tra xem có đủ chỗ trống không.');
                    return;
                }

                placeCar(row, col, size, orientation, type);
            } catch (err) {
                console.error('Drop error:', err);
            }
        });
    });
}

function setupContextMenu() {
    gridContainer.addEventListener('contextmenu', function (e) {
        e.preventDefault();
        const input = e.target;
        if (input.tagName !== 'INPUT') return;

        const value = input.value.trim();
        if (value === '') return;

        const inputs = gridContainer.querySelectorAll('input');
        inputs.forEach(inp => {
            if (inp.value.trim() === value) {
                inp.value = '';
            }
        });

        if (value.toLowerCase() === 'x') {
            hasCarX = false;
        }

        updateInputStyles();
    });
}

// ==================== GRID HELPERS ====================

function getArray2D() {
    const inputs = gridContainer.querySelectorAll('input');
    const array2D = [];

    for (let i = 0; i < ROWS; i++) {
        const row = [];
        for (let j = 0; j < COLS; j++) {
            const index = i * COLS + j;
            const value = inputs[index].value.trim();

            if (value === 'x' || value === 'X') {
                row.push('x');
            } else if (value !== '' && !isNaN(parseInt(value))) {
                row.push(parseInt(value));
            } else {
                row.push(null);
            }
        }
        array2D.push(row);
    }
    return array2D;
}

function setArray2D(array2D) {
    const inputs = gridContainer.querySelectorAll('input');
    for (let i = 0; i < ROWS; i++) {
        for (let j = 0; j < COLS; j++) {
            const index = i * COLS + j;
            const value = array2D[i][j];
            inputs[index].value = value === null ? '' : value;
        }
    }
}

// ==================== SOLVER ====================

function getCarColor(carId) {
    if (carId === 'x') return '#e74c3c';
    if (!carColorMap[carId]) {
        const colorIndex = Object.keys(carColorMap).length % CAR_COLORS.length;
        carColorMap[carId] = CAR_COLORS[colorIndex];
    }
    return carColorMap[carId];
}

function resetCarColors() {
    for (const key in carColorMap) {
        delete carColorMap[key];
    }
}

function parseCars(grid) {
    const cars = {};

    for (let i = 0; i < ROWS; i++) {
        for (let j = 0; j < COLS; j++) {
            const cell = grid[i][j];
            if (cell !== null) {
                const carId = String(cell);
                if (!cars[carId]) {
                    cars[carId] = {
                        id: carId,
                        cells: [],
                        orientation: null
                    };
                }
                cars[carId].cells.push({ row: i, col: j });
            }
        }
    }

    for (const carId in cars) {
        const car = cars[carId];
        if (car.cells.length >= 2) {
            if (car.cells[0].row === car.cells[1].row) {
                car.orientation = 'H';
            } else {
                car.orientation = 'V';
            }
        }
        car.cells.sort((a, b) => {
            if (car.orientation === 'H') return a.col - b.col;
            return a.row - b.row;
        });
    }

    return cars;
}

function createStateKey(cars) {
    const parts = [];
    const sortedIds = Object.keys(cars).sort();
    for (const id of sortedIds) {
        const car = cars[id];
        const pos = car.cells[0];
        parts.push(`${id}:${pos.row},${pos.col}`);
    }
    return parts.join('|');
}

function copyCars(cars) {
    const newCars = {};
    for (const id in cars) {
        newCars[id] = {
            id: cars[id].id,
            orientation: cars[id].orientation,
            cells: cars[id].cells.map(c => ({ row: c.row, col: c.col }))
        };
    }
    return newCars;
}

function createGridFromCars(cars) {
    const grid = Array(ROWS).fill(null).map(() => Array(COLS).fill(null));
    for (const id in cars) {
        for (const cell of cars[id].cells) {
            grid[cell.row][cell.col] = id === 'x' ? 'x' : parseInt(id);
        }
    }
    return grid;
}

function isGoal(cars) {
    const carX = cars['x'];
    if (!carX) return false;
    const lastCell = carX.cells[carX.cells.length - 1];
    return lastCell.col === COLS - 1 && lastCell.row === 2;
}

function getPossibleMoves(cars) {
    const moves = [];
    const grid = createGridFromCars(cars);

    for (const carId in cars) {
        const car = cars[carId];
        const firstCell = car.cells[0];
        const lastCell = car.cells[car.cells.length - 1];

        if (car.orientation === 'H') {
            for (let steps = 1; firstCell.col - steps >= 0; steps++) {
                if (grid[firstCell.row][firstCell.col - steps] === null) {
                    moves.push({ carId, direction: 'left', steps });
                } else {
                    break;
                }
            }
            for (let steps = 1; lastCell.col + steps < COLS; steps++) {
                if (grid[lastCell.row][lastCell.col + steps] === null) {
                    moves.push({ carId, direction: 'right', steps });
                } else {
                    break;
                }
            }
        } else {
            for (let steps = 1; firstCell.row - steps >= 0; steps++) {
                if (grid[firstCell.row - steps][firstCell.col] === null) {
                    moves.push({ carId, direction: 'up', steps });
                } else {
                    break;
                }
            }
            for (let steps = 1; lastCell.row + steps < ROWS; steps++) {
                if (grid[lastCell.row + steps][lastCell.col] === null) {
                    moves.push({ carId, direction: 'down', steps });
                } else {
                    break;
                }
            }
        }
    }

    return moves;
}

function applyMove(cars, move) {
    const newCars = copyCars(cars);
    const car = newCars[move.carId];
    const steps = move.steps || 1;

    for (const cell of car.cells) {
        switch (move.direction) {
            case 'left': cell.col -= steps; break;
            case 'right': cell.col += steps; break;
            case 'up': cell.row -= steps; break;
            case 'down': cell.row += steps; break;
        }
    }

    return newCars;
}

function translateDirection(dir) {
    const map = {
        'left': 'sang trái',
        'right': 'sang phải',
        'up': 'lên trên',
        'down': 'xuống dưới'
    };
    return map[dir] || dir;
}

function solvePuzzle(grid) {
    const initialCars = parseCars(grid);

    if (!initialCars['x']) {
        return { success: false, message: 'Không tìm thấy xe "x" trong grid!' };
    }

    const carX = initialCars['x'];
    if (carX.cells[0].row !== 2) {
        return { success: false, message: 'Xe "x" phải nằm ở hàng 3 (hàng số 3 từ trên xuống)!' };
    }

    if (isGoal(initialCars)) {
        return { success: true, moves: [], message: 'Xe x đã ở vị trí thoát!' };
    }

    const visited = new Set();
    const queue = [{
        cars: initialCars,
        moves: []
    }];

    visited.add(createStateKey(initialCars));

    while (queue.length > 0) {
        const current = queue.shift();
        const possibleMoves = getPossibleMoves(current.cars);

        for (const move of possibleMoves) {
            const newCars = applyMove(current.cars, move);
            const stateKey = createStateKey(newCars);

            if (!visited.has(stateKey)) {
                visited.add(stateKey);
                const newMoves = [...current.moves, move];

                if (isGoal(newCars)) {
                    return {
                        success: true,
                        moves: newMoves,
                        finalCars: newCars,
                        statesExplored: visited.size
                    };
                }

                queue.push({
                    cars: newCars,
                    moves: newMoves
                });
            }
        }
    }

    return {
        success: false,
        message: 'Không tìm được lời giải! Bài toán không có đáp án.',
        statesExplored: visited.size
    };
}

// ==================== DISPLAY ====================

function createStepGridHTML(cars, stepNumber, moveInfo, highlightCarId = null) {
    const grid = createGridFromCars(cars);

    let html = `<div class="step-wrapper">`;
    html += `<div class="step-title">Bước ${stepNumber}</div>`;
    html += `<div class="step-grid">`;

    for (let i = 0; i < ROWS; i++) {
        for (let j = 0; j < COLS; j++) {
            const cell = grid[i][j];
            const cellId = cell === null ? null : String(cell);
            const isHighlighted = highlightCarId && cellId === highlightCarId;
            let cellClass = 'step-cell';
            let style = '';
            let content = '';

            if (cell === null) {
                cellClass += ' empty';
            } else if (cell === 'x') {
                cellClass += ' car-x';
                content = 'X';
            } else {
                style = `background: ${getCarColor(String(cell))};`;
                content = cell;
            }

            if (isHighlighted) {
                cellClass += ' highlight';
            }

            if (i === 2 && j === COLS - 1) {
                cellClass += ' exit-marker';
            }

            html += `<div class="${cellClass}" style="${style}">${content}</div>`;
        }
    }

    html += `</div>`;
    if (moveInfo) {
        html += `<div class="move-info">${moveInfo}</div>`;
    }
    html += `</div>`;

    return html;
}

function displaySolutionSteps(initialCars, moves) {
    const stepsContainer = document.getElementById('stepsContainer');
    stepsContainer.innerHTML = '';

    let currentCars = copyCars(initialCars);
    let html = createStepGridHTML(currentCars, 0, 'Trạng thái ban đầu', null);

    let moveIndex = 0;
    for (const move of moves) {
        currentCars = applyMove(currentCars, move);
        moveIndex++;

        const carLabel = move.carId === 'x' ? 'Xe X' : `Xe ${move.carId}`;
        const direction = translateDirection(move.direction);
        const stepText = move.steps > 1 ? `${move.steps} ô` : '1 ô';
        const moveInfo = `${carLabel} ${direction} ${stepText}`;

        html += createStepGridHTML(currentCars, moveIndex, moveInfo, move.carId);
    }

    stepsContainer.innerHTML = html;
}

// ==================== BUTTON HANDLERS ====================

function setupButtons() {
    document.getElementById('btnReset').addEventListener('click', function () {
        const example = [
            [null, null, null, null, null, null],
            [null, null, null, null, null, null],
            [null, null, null, null, null, null],
            [null, null, null, null, null, null],
            [null, null, null, null, null, null],
            [null, null, null, null, null, null],
        ];
        setArray2D(example);
        setTimeout(resetDragDropState, 0);
        document.getElementById('result').style.display = 'none';
    });

    document.getElementById('btnLoadExample').addEventListener('click', function () {
        const example = [
            [null, 1, 1, 2, 3, 3],
            [null, null, null, 2, null, 5],
            [null, "x", "x", null, 4, 5],
            [7, 7, 8, 8, 4, 6],
            [null, null, 9, 10, 10, 6],
            [null, null, 9, 11, 11, 11]
        ];
        setArray2D(example);
        setTimeout(resetDragDropState, 100);
    });

    document.getElementById('btnSolve').addEventListener('click', function () {
        const grid = getArray2D();
        console.log('Đang giải bài toán...');
        console.log('Grid:', grid);

        resetCarColors();

        const initialCars = parseCars(grid);
        for (const carId in initialCars) {
            getCarColor(carId);
        }

        const startTime = performance.now();
        const result = solvePuzzle(grid);
        const endTime = performance.now();

        const resultDiv = document.getElementById('result');
        const solutionPre = document.getElementById('solution');
        const stepsContainer = document.getElementById('stepsContainer');
        resultDiv.style.display = 'block';

        if (result.success) {
            const moves = result.moves;
            solutionPre.textContent = '';
            displaySolutionSteps(initialCars, moves);
            console.log('Lời giải:', result);
            console.log('Các bước:', moves);
        } else {
            solutionPre.textContent = `❌ ${result.message}\n🔍 Số trạng thái đã duyệt: ${result.statesExplored || 'N/A'}`;
            stepsContainer.innerHTML = '';
            console.log('Không tìm được lời giải:', result);
        }
    });
}
