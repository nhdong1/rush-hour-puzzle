// ==================== MATH EXPRESSION PUZZLE MODULE ====================

// Game state
let gameState = {
    // Available resources
    numbers: { 0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0 },
    operators: { '+': 0, '-': 0, '*': 0, '/': 0 },

    // Puzzle requirements
    numDigits: 4,
    numOperators: 3,
    targetResult: 22
};

// ==================== INITIALIZATION ====================

export function initMathPuzzle() {
    setupNumberInputs();
    setupOperatorInputs();
    setupRequirementInputs();
    setupButtons();
    updateExpressionSlots();
}

function setupNumberInputs() {
    for (let i = 0; i <= 9; i++) {
        const input = document.getElementById(`num-qty-${i}`);
        if (input) {
            input.value = gameState.numbers[i];
            input.addEventListener('change', function () {
                gameState.numbers[i] = parseInt(this.value) || 0;
            });
        }
    }
}

function setupOperatorInputs() {
    const ops = ['+', '-', '*', '/'];
    const opIds = ['plus', 'minus', 'multiply', 'divide'];

    ops.forEach((op, index) => {
        const input = document.getElementById(`op-qty-${opIds[index]}`);
        if (input) {
            input.value = gameState.operators[op];
            input.addEventListener('change', function () {
                gameState.operators[op] = parseInt(this.value) || 0;
            });
        }
    });
}

function setupRequirementInputs() {
    const numDigitsInput = document.getElementById('req-num-digits');
    const numOpsInput = document.getElementById('req-num-ops');
    const targetInput = document.getElementById('req-target');

    if (numDigitsInput) {
        numDigitsInput.value = gameState.numDigits;
        numDigitsInput.addEventListener('change', function () {
            gameState.numDigits = parseInt(this.value) || 2;
            updateExpressionSlots();
        });
    }

    if (numOpsInput) {
        numOpsInput.value = gameState.numOperators;
        numOpsInput.addEventListener('change', function () {
            gameState.numOperators = parseInt(this.value) || 1;
            updateExpressionSlots();
        });
    }

    if (targetInput) {
        targetInput.value = gameState.targetResult;
        targetInput.addEventListener('change', function () {
            gameState.targetResult = parseInt(this.value) || 0;
            updateTargetDisplay();
        });
    }
}

// ==================== UI UPDATES ====================

function updateExpressionSlots() {
    const container = document.getElementById('expression-builder');
    if (!container) return;

    container.innerHTML = '';

    // Create visual slots: num op num op num ... = target
    const totalSlots = gameState.numDigits + gameState.numOperators;

    for (let i = 0; i < totalSlots; i++) {
        const slot = document.createElement('div');
        const isNumberSlot = i % 2 === 0;
        slot.className = `expr-slot ${isNumberSlot ? 'slot-number' : 'slot-operator'}`;
        slot.textContent = isNumberSlot ? '?' : '○';
        container.appendChild(slot);
    }

    // Add equals sign and target
    const equals = document.createElement('span');
    equals.className = 'expr-equals';
    equals.textContent = '=';
    container.appendChild(equals);

    const target = document.createElement('span');
    target.className = 'expr-target';
    target.textContent = gameState.targetResult;
    container.appendChild(target);
}

function updateTargetDisplay() {
    const targetEl = document.querySelector('.expr-target');
    if (targetEl) {
        targetEl.textContent = gameState.targetResult;
    }
}

// ==================== EXPRESSION EVALUATION ====================

function evaluateExpression(expr) {
    if (expr.length === 0) return null;

    // Convert to values array
    const values = expr.map(e => e.value);

    // Build expression string and use Function to evaluate with proper precedence
    try {
        const exprString = values.join('');
        // Use Function for safe evaluation (still need to validate input)
        const result = Function('"use strict"; return (' + exprString + ')')();

        // Check for integer result (for division)
        if (!Number.isInteger(result)) {
            return null; // Only allow integer results
        }

        return result;
    } catch (e) {
        return null;
    }
}

// ==================== SOLVER ====================

function solvePuzzle() {
    // Clone available resources
    const availableNums = { ...gameState.numbers };
    const availableOps = { ...gameState.operators };

    const solutions = [];
    const maxIterations = 1000; // Safety limit
    let iterations = 0;

    while (iterations < maxIterations) {
        iterations++;

        // Build arrays from remaining resources
        const numsArray = [];
        const opsArray = [];

        for (let i = 0; i <= 9; i++) {
            for (let j = 0; j < availableNums[i]; j++) {
                numsArray.push(i);
            }
        }

        const ops = ['+', '-', '*', '/'];
        ops.forEach(op => {
            for (let j = 0; j < availableOps[op]; j++) {
                opsArray.push(op);
            }
        });

        // Check if we have enough resources
        if (numsArray.length < gameState.numDigits) {
            break; // Not enough numbers left
        }
        if (opsArray.length < gameState.numOperators) {
            break; // Not enough operators left
        }

        // Try to find one valid solution
        const solution = findOneSolution(numsArray, opsArray);

        if (!solution) {
            break; // No more solutions possible
        }

        solutions.push(solution);

        // Deduct used resources
        solution.numbers.forEach(num => {
            availableNums[num]--;
        });
        solution.operators.forEach(op => {
            availableOps[op]--;
        });

        // Store remaining resources after this solution
        solution.remainingNums = { ...availableNums };
        solution.remainingOps = { ...availableOps };
    }

    if (solutions.length === 0) {
        return {
            success: false,
            maxCorrect: 0,
            message: 'Không tìm được lời giải nào với các số và phép tính hiện có!'
        };
    }

    return {
        success: true,
        solutions,
        maxCorrect: solutions.length,
        message: `Số phép tính đúng tối đa: ${solutions.length}`
    };
}

function findOneSolution(numsArray, opsArray) {
    // Generate all permutations
    const numCombinations = getPermutations(numsArray, gameState.numDigits);
    const opCombinations = getPermutations(opsArray, gameState.numOperators);

    const seen = new Set();

    for (const nums of numCombinations) {
        for (const opsArr of opCombinations) {
            // Build expression
            const expr = [];
            for (let i = 0; i < nums.length; i++) {
                expr.push({ value: nums[i], type: 'number' });
                if (i < opsArr.length) {
                    expr.push({ value: opsArr[i], type: 'operator' });
                }
            }

            // Create string representation
            const exprStr = expr.map(e => e.value).join(' ');

            // Skip duplicates
            if (seen.has(exprStr)) continue;
            seen.add(exprStr);

            // Evaluate
            const result = evaluateExpression(expr);

            if (result === gameState.targetResult) {
                return {
                    expression: exprStr,
                    numbers: [...nums],
                    operators: [...opsArr]
                };
            }
        }
    }

    return null; // No solution found
}

function getPermutations(arr, length) {
    if (length === 0) return [[]];
    if (arr.length === 0) return [];

    const result = [];
    const used = new Array(arr.length).fill(false);

    function backtrack(current) {
        if (current.length === length) {
            result.push([...current]);
            return;
        }

        for (let i = 0; i < arr.length; i++) {
            if (used[i]) continue;

            // Skip duplicates
            if (i > 0 && arr[i] === arr[i - 1] && !used[i - 1]) continue;

            used[i] = true;
            current.push(arr[i]);
            backtrack(current);
            current.pop();
            used[i] = false;
        }
    }

    // Sort for duplicate detection
    const sorted = [...arr].sort();
    backtrack([]);

    return result;
}

// ==================== DISPLAY SOLUTIONS ====================

function displaySolutions(result) {
    const container = document.getElementById('math-solutions');
    if (!container) return;

    container.innerHTML = '';
    container.style.display = 'block';

    if (!result.success) {
        container.innerHTML = `<div class="no-solution">❌ ${result.message}</div>`;
        return;
    }

    const header = document.createElement('div');
    header.className = 'solutions-header';
    header.innerHTML = `✅ ${result.message}`;
    container.appendChild(header);

    const list = document.createElement('div');
    list.className = 'solutions-list';

    result.solutions.forEach((sol, index) => {
        const item = document.createElement('div');
        item.className = 'solution-item';
        item.innerHTML = `
            <span class="solution-index">${index + 1}.</span>
            <span class="solution-expr">${sol.expression} = ${gameState.targetResult}</span>
        `;
        list.appendChild(item);

        // Show remaining resources after this solution
        const remainingDiv = document.createElement('div');
        remainingDiv.className = 'remaining-resources';
        remainingDiv.innerHTML = '<span class="remaining-label">Còn lại:</span>';

        // Number chips
        const numChips = document.createElement('span');
        numChips.className = 'remaining-chips';
        for (let i = 0; i <= 9; i++) {
            const count = sol.remainingNums[i];
            if (count > 0) {
                numChips.innerHTML += `<span class="chip-mini chip-number">${i}<sup>${count}</sup></span>`;
            }
        }
        remainingDiv.appendChild(numChips);

        // Operator chips
        const opChips = document.createElement('span');
        opChips.className = 'remaining-chips';
        const ops = ['+', '-', '*', '/'];
        ops.forEach(op => {
            const count = sol.remainingOps[op];
            if (count > 0) {
                opChips.innerHTML += `<span class="chip-mini chip-operator">${op}<sup>${count}</sup></span>`;
            }
        });
        remainingDiv.appendChild(opChips);

        list.appendChild(remainingDiv);
    });

    container.appendChild(list);
}

// ==================== FEEDBACK ====================

function showFeedback(message, type) {
    const feedback = document.getElementById('math-feedback');
    if (!feedback) return;

    feedback.textContent = message;
    feedback.className = `feedback feedback-${type}`;
    feedback.style.display = 'block';

    setTimeout(() => {
        feedback.style.display = 'none';
    }, 2000);
}

// ==================== BUTTON HANDLERS ====================

function setupButtons() {
    const btnReset = document.getElementById('btnMathReset');
    const btnSolve = document.getElementById('btnMathSolve');
    const btnExample = document.getElementById('btnMathExample');

    if (btnReset) {
        btnReset.addEventListener('click', resetGame);
    }

    if (btnSolve) {
        btnSolve.addEventListener('click', () => {
            const result = solvePuzzle();
            displaySolutions(result);
        });
    }

    if (btnExample) {
        btnExample.addEventListener('click', loadExample);
    }
}

function resetGame() {
    // Reset to initial values
    gameState.numbers = { 0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0 };
    gameState.operators = { '+': 0, '-': 0, '*': 0, '/': 0 };
    gameState.numDigits = 3;
    gameState.numOperators = 2;
    gameState.targetResult = 10;

    // Update input fields
    for (let i = 0; i <= 9; i++) {
        const input = document.getElementById(`num-qty-${i}`);
        if (input) input.value = 0;
    }

    const opIds = ['plus', 'minus', 'multiply', 'divide'];
    opIds.forEach(id => {
        const input = document.getElementById(`op-qty-${id}`);
        if (input) input.value = 0;
    });

    const numDigitsInput = document.getElementById('req-num-digits');
    const numOpsInput = document.getElementById('req-num-ops');
    const targetInput = document.getElementById('req-target');

    if (numDigitsInput) numDigitsInput.value = 3;
    if (numOpsInput) numOpsInput.value = 2;
    if (targetInput) targetInput.value = 10;

    // Clear solutions
    const solutionsContainer = document.getElementById('math-solutions');
    if (solutionsContainer) {
        solutionsContainer.innerHTML = '';
        solutionsContainer.style.display = 'none';
    }

    updateExpressionSlots();
}

function loadExample() {
    // Set example values
    gameState.numbers = { 0: 0, 1: 2, 2: 2, 3: 2, 4: 2, 5: 2, 6: 2, 7: 2, 8: 2, 9: 2 };
    gameState.operators = { '+': 5, '-': 3, '*': 2, '/': 2 };
    gameState.numDigits = 3;
    gameState.numOperators = 2;
    gameState.targetResult = 15;

    // Update input fields
    for (let i = 0; i <= 9; i++) {
        const input = document.getElementById(`num-qty-${i}`);
        if (input) input.value = gameState.numbers[i];
    }

    const ops = ['+', '-', '*', '/'];
    const opIds = ['plus', 'minus', 'multiply', 'divide'];
    ops.forEach((op, index) => {
        const input = document.getElementById(`op-qty-${opIds[index]}`);
        if (input) input.value = gameState.operators[op];
    });

    const numDigitsInput = document.getElementById('req-num-digits');
    const numOpsInput = document.getElementById('req-num-ops');
    const targetInput = document.getElementById('req-target');

    if (numDigitsInput) numDigitsInput.value = 3;
    if (numOpsInput) numOpsInput.value = 2;
    if (targetInput) targetInput.value = 15;

    // Clear solutions
    const solutionsContainer = document.getElementById('math-solutions');
    if (solutionsContainer) {
        solutionsContainer.innerHTML = '';
        solutionsContainer.style.display = 'none';
    }

    updateExpressionSlots();
    showFeedback('Đã tải ví dụ! Nhấn "Xem Cách Giải" để xem số phép tính đúng tối đa', 'success');
}
