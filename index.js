// Tạo lưới 6x6 input
const gridContainer = document.getElementById('grid');
const ROWS = 6;
const COLS = 6;

// Tạo các ô input
for (let i = 0; i < ROWS; i++) {
    for (let j = 0; j < COLS; j++) {
        const input = document.createElement('input');
        input.type = 'text';
        input.dataset.row = i;
        input.dataset.col = j;
        input.maxLength = 3;

        // Validate input: chỉ cho phép số 1-100 hoặc 'x'
        input.addEventListener('input', function(e) {
            let value = e.target.value.trim().toLowerCase();

            if (value === 'x' || value === 'X') {
                e.target.value = 'x';
                return;
            }

            // Chỉ cho phép số
            if (value !== '' && !/^\d+$/.test(value)) {
                e.target.value = value.replace(/[^\dx]/gi, '');
                return;
            }

            // Kiểm tra số trong khoảng 1-100
            if (value !== '' && !isNaN(parseInt(value))) {
                const num = parseInt(value);
                if (num < 1) {
                    e.target.value = '1';
                } else if (num > 100) {
                    e.target.value = '100';
                }
            }
        });

        gridContainer.appendChild(input);
    }
}

// ==================== DRAG AND DROP ====================

let nextCarId = 1; // ID tự động cho xe mới
let hasCarX = false; // Kiểm tra đã có xe X chưa

// Hàm reset trạng thái kéo thả
function resetDragDropState() {
    nextCarId = 1;
    hasCarX = false;
    // Kiểm tra lại grid để cập nhật trạng thái
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

// Cập nhật style cho các ô input dựa trên giá trị
function updateInputStyles() {
    const inputs = gridContainer.querySelectorAll('input');
    inputs.forEach(input => {
        input.classList.remove('car-x', 'has-car');
        const value = input.value.trim().toLowerCase();
        if (value === 'x') {
            input.classList.add('car-x', 'has-car');
        } else if (value !== '') {
            input.classList.add('has-car');
            // Tạo màu nền cho xe dựa trên ID
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

// Màu cho các xe trong input grid
function getCarColorForInput(carId) {
    const colors = [
        '#3498db', '#2ecc71', '#9b59b6', '#f39c12', '#1abc9c',
        '#e67e22', '#34495e', '#16a085', '#8e44ad', '#27ae60',
        '#2980b9', '#d35400', '#c0392b', '#7f8c8d', '#f1c40f'
    ];
    return colors[(carId - 1) % colors.length];
}

// Kiểm tra có thể đặt xe vào vị trí không
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

// Đặt xe vào grid
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

// Thiết lập drag events cho các xe trong palette
document.querySelectorAll('.draggable-car').forEach(car => {
    car.addEventListener('dragstart', function(e) {
        const type = this.dataset.type;
        const size = parseInt(this.dataset.size);
        const orientation = this.dataset.orientation;

        // Không cho kéo xe X nếu đã có
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

    car.addEventListener('dragend', function(e) {
        this.style.opacity = '1';
        // Xóa các class highlight
        document.querySelectorAll('.grid-container input').forEach(input => {
            input.classList.remove('drag-over', 'drag-invalid');
        });
    });
});

// Thiết lập drop events cho các ô input
function setupDropZones() {
    const inputs = gridContainer.querySelectorAll('input');

    inputs.forEach(input => {
        input.addEventListener('dragover', function(e) {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'copy';
        });

        input.addEventListener('dragenter', function(e) {
            e.preventDefault();
            const row = parseInt(this.dataset.row);
            const col = parseInt(this.dataset.col);

            try {
                // Không thể đọc data trong dragenter, chỉ highlight
                this.classList.add('drag-over');
            } catch (err) {
                this.classList.add('drag-over');
            }
        });

        input.addEventListener('dragleave', function(e) {
            this.classList.remove('drag-over', 'drag-invalid');
        });

        input.addEventListener('drop', function(e) {
            e.preventDefault();
            this.classList.remove('drag-over', 'drag-invalid');

            const row = parseInt(this.dataset.row);
            const col = parseInt(this.dataset.col);

            try {
                const data = JSON.parse(e.dataTransfer.getData('text/plain'));
                const { type, size, orientation } = data;

                // Xe X chỉ được đặt ở hàng 3 (index 2)
                if (type === 'x' && row !== 2) {
                    alert('Xe X (đỏ) chỉ được đặt ở hàng 3!');
                    return;
                }

                // Kiểm tra có thể đặt không
                if (!canPlaceCar(row, col, size, orientation)) {
                    alert('Không thể đặt xe ở vị trí này! Kiểm tra xem có đủ chỗ trống không.');
                    return;
                }

                // Đặt xe
                placeCar(row, col, size, orientation, type);

            } catch (err) {
                console.error('Drop error:', err);
            }
        });

        // Cập nhật style khi input thay đổi
        input.addEventListener('input', function() {
            setTimeout(updateInputStyles, 0);
        });
    });
}

// Khởi tạo drop zones
setupDropZones();

// Xóa xe khi click chuột phải
gridContainer.addEventListener('contextmenu', function(e) {
    e.preventDefault();
    const input = e.target;
    if (input.tagName !== 'INPUT') return;

    const value = input.value.trim();
    if (value === '') return;

    // Tìm tất cả các ô có cùng giá trị và xóa
    const inputs = gridContainer.querySelectorAll('input');
    inputs.forEach(inp => {
        if (inp.value.trim() === value) {
            inp.value = '';
        }
    });

    // Nếu xóa xe X
    if (value.toLowerCase() === 'x') {
        hasCarX = false;
    }

    updateInputStyles();
});

// Cập nhật resetDragDropState khi reset
const originalResetHandler = document.getElementById('btnReset').onclick;
document.getElementById('btnReset').addEventListener('click', function() {
    setTimeout(resetDragDropState, 0);
});

// Cập nhật khi load ví dụ
document.getElementById('btnLoadExample').addEventListener('click', function() {
    setTimeout(resetDragDropState, 100);
});

// Khởi tạo ban đầu
setTimeout(resetDragDropState, 0);

// Lấy array 2D từ grid
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

// Set array vào grid
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

// Xử lý button click - Lấy Array
document.getElementById('btnReset').addEventListener('click', function() {
    const example = [
        [null, null, null, null, null, null],
        [null, null, null, null, null, null],
        [null, null, null, null, null, null],
        [null, null, null, null, null, null],
        [null, null, null, null, null, null],
        [null, null, null, null, null, null],
    ];
    setArray2D(example);
});

// Load ví dụ
document.getElementById('btnLoadExample').addEventListener('click', function() {
    const example = [
        [null, 1, 1, 2, 3, 3],
        [null, null, null, 2, null, 5],
        [null, "x", "x", null, 4, 5],
        [7, 7, 8, 8, 4, 6],
        [null, null, 9, 10, 10, 6],
        [null, null, 9, 11, 11, 11]
    ];
    setArray2D(example);
});

// ==================== RUSH HOUR SOLVER ====================

// Bảng màu cho các xe (tránh màu đỏ vì đã dùng cho xe x)
const CAR_COLORS = [
    '#3498db', // blue
    '#2ecc71', // green
    '#9b59b6', // purple
    '#f39c12', // orange
    '#1abc9c', // teal
    '#e67e22', // dark orange
    '#34495e', // dark gray
    '#16a085', // dark teal
    '#8e44ad', // dark purple
    '#27ae60', // dark green
    '#2980b9', // dark blue
    '#d35400', // burnt orange
    '#c0392b', // dark red
    '#7f8c8d', // gray
    '#f1c40f', // yellow
    '#95a5a6', // light gray
];

// Lưu trữ màu cho mỗi xe
const carColorMap = {};

// Lấy màu cho xe
function getCarColor(carId) {
    if (carId === 'x') return '#e74c3c'; // Màu đỏ cho xe x
    if (!carColorMap[carId]) {
        const colorIndex = Object.keys(carColorMap).length % CAR_COLORS.length;
        carColorMap[carId] = CAR_COLORS[colorIndex];
    }
    return carColorMap[carId];
}

// Reset màu xe
function resetCarColors() {
    for (const key in carColorMap) {
        delete carColorMap[key];
    }
}

// Phân tích các xe từ grid
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
                        orientation: null, // 'H' horizontal, 'V' vertical
                    };
                }
                cars[carId].cells.push({ row: i, col: j });
            }
        }
    }

    // Xác định orientation của mỗi xe
    for (const carId in cars) {
        const car = cars[carId];
        if (car.cells.length >= 2) {
            if (car.cells[0].row === car.cells[1].row) {
                car.orientation = 'H';
            } else {
                car.orientation = 'V';
            }
        }
        // Sort cells
        car.cells.sort((a, b) => {
            if (car.orientation === 'H') return a.col - b.col;
            return a.row - b.row;
        });
    }

    return cars;
}

// Tạo state key để so sánh trạng thái
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

// Copy cars object
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

// Tạo grid từ cars
function createGridFromCars(cars) {
    const grid = Array(ROWS).fill(null).map(() => Array(COLS).fill(null));
    for (const id in cars) {
        for (const cell of cars[id].cells) {
            grid[cell.row][cell.col] = id === 'x' ? 'x' : parseInt(id);
        }
    }
    return grid;
}

// Kiểm tra xe x đã thoát chưa (ô cuối hàng 2 - index 0-based)
function isGoal(cars) {
    const carX = cars['x'];
    if (!carX) return false;
    // Xe x nằm ở hàng 2 (index), cần đến cột cuối
    const lastCell = carX.cells[carX.cells.length - 1];
    return lastCell.col === COLS - 1 && lastCell.row === 2;
}

// Lấy các nước đi có thể (cho phép di chuyển nhiều ô trong 1 bước)
function getPossibleMoves(cars) {
    const moves = [];
    const grid = createGridFromCars(cars);

    for (const carId in cars) {
        const car = cars[carId];
        const firstCell = car.cells[0];
        const lastCell = car.cells[car.cells.length - 1];

        if (car.orientation === 'H') {
            // Di chuyển sang trái - kiểm tra tất cả các ô có thể
            for (let steps = 1; firstCell.col - steps >= 0; steps++) {
                if (grid[firstCell.row][firstCell.col - steps] === null) {
                    moves.push({ carId, direction: 'left', steps });
                } else {
                    break; // Gặp chướng ngại vật, dừng
                }
            }
            // Di chuyển sang phải
            for (let steps = 1; lastCell.col + steps < COLS; steps++) {
                if (grid[lastCell.row][lastCell.col + steps] === null) {
                    moves.push({ carId, direction: 'right', steps });
                } else {
                    break;
                }
            }
        } else {
            // Di chuyển lên
            for (let steps = 1; firstCell.row - steps >= 0; steps++) {
                if (grid[firstCell.row - steps][firstCell.col] === null) {
                    moves.push({ carId, direction: 'up', steps });
                } else {
                    break;
                }
            }
            // Di chuyển xuống
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

// Thực hiện di chuyển (hỗ trợ nhiều ô trong 1 bước)
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

// Dịch hướng sang tiếng Việt
function translateDirection(dir) {
    const map = {
        'left': 'sang trái',
        'right': 'sang phải',
        'up': 'lên trên',
        'down': 'xuống dưới'
    };
    return map[dir] || dir;
}

// BFS để tìm lời giải
function solvePuzzle(grid) {
    const initialCars = parseCars(grid);

    // Kiểm tra xe x có tồn tại không
    if (!initialCars['x']) {
        return { success: false, message: 'Không tìm thấy xe "x" trong grid!' };
    }

    // Kiểm tra xe x có nằm ở hàng 3 (index 2) không
    const carX = initialCars['x'];
    if (carX.cells[0].row !== 2) {
        return { success: false, message: 'Xe "x" phải nằm ở hàng 3 (hàng số 3 từ trên xuống)!' };
    }

    // Kiểm tra nếu đã ở đích
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

// Gộp các bước di chuyển liên tục cùng xe cùng hướng
function consolidateMoves(moves) {
    if (moves.length === 0) return [];

    const consolidated = [];
    let current = { ...moves[0] };

    for (let i = 1; i < moves.length; i++) {
        const move = moves[i];
        if (move.carId === current.carId && move.direction === current.direction) {
            current.steps++;
        } else {
            consolidated.push(current);
            current = { ...move };
        }
    }
    consolidated.push(current);

    return consolidated;
}

// Tạo HTML grid hiển thị trạng thái
function createStepGridHTML(cars, stepNumber, moveInfo, highlightCarId = null) {
    const grid = createGridFromCars(cars);

    let html = `<div class="step-wrapper">`;
    html += `<div class="step-title">Bước ${stepNumber}</div>`;
    html += `<div class="step-grid">`;

    for (let i = 0; i < ROWS; i++) {
        for (let j = 0; j < COLS; j++) {
            const cell = grid[i][j];
            const isExit = (i === 2 && j === COLS - 1);
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

            if (isExit && i === 2) {
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

// Hiển thị các bước giải
function displaySolutionSteps(initialCars, moves) {
    const stepsContainer = document.getElementById('stepsContainer');
    stepsContainer.innerHTML = '';

    let currentCars = copyCars(initialCars);

    // Hiển thị trạng thái ban đầu
    let html = createStepGridHTML(currentCars, 0, 'Trạng thái ban đầu', null);

    // Áp dụng từng bước và hiển thị
    let moveIndex = 0;
    for (const move of moves) {
        // Áp dụng move
        currentCars = applyMove(currentCars, move);
        moveIndex++;

        const carLabel = move.carId === 'x' ? 'Xe X' : `Xe ${move.carId}`;
        const direction = translateDirection(move.direction);
        const stepText = move.steps > 1 ? `${move.steps} ô` : '1 ô';
        const moveInfo = `${carLabel} ${direction} ${stepText}`;

        // Highlight xe vừa di chuyển
        html += createStepGridHTML(currentCars, moveIndex, moveInfo, move.carId);
    }

    stepsContainer.innerHTML = html;
}

// Xử lý button Giải bài toán
document.getElementById('btnSolve').addEventListener('click', function() {
    const grid = getArray2D();
    console.log('Đang giải bài toán...');
    console.log('Grid:', grid);

    // Reset màu xe
    resetCarColors();

    // Khởi tạo màu cho tất cả xe
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

        let output = `✅ Tìm thấy lời giải!\n`;
        output += `📊 Số bước di chuyển: ${moves.length}\n`;
        output += `🔍 Số trạng thái đã duyệt: ${result.statesExplored || 'N/A'}\n`;
        output += `⏱️ Thời gian: ${(endTime - startTime).toFixed(2)}ms\n\n`;
        output += `📋 Các bước di chuyển:\n`;
        output += `─────────────────────────\n`;

        moves.forEach((move, index) => {
            const carLabel = move.carId === 'x' ? 'Xe X' : `Xe ${move.carId}`;
            const direction = translateDirection(move.direction);
            const stepText = move.steps > 1 ? `${move.steps} ô` : '1 ô';
            output += `Bước ${index + 1}: ${carLabel} di chuyển ${direction} ${stepText}\n`;
        });

        output += `─────────────────────────\n`;
        output += `🎉 Xe X đã thoát khỏi bãi đỗ!`;

        // solutionPre.textContent = output;

        // Hiển thị các bước bằng grid màu
        displaySolutionSteps(initialCars, moves);

        console.log('Lời giải:', result);
        console.log('Các bước:', moves);
    } else {
        solutionPre.textContent = `❌ ${result.message}\n🔍 Số trạng thái đã duyệt: ${result.statesExplored || 'N/A'}`;
        stepsContainer.innerHTML = '';
        console.log('Không tìm được lời giải:', result);
    }
});
