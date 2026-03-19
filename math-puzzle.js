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

// ==================== UI STATE ====================

let showAnalytics = false;
let showRemaining = false;
let lastSolveResult = null;

function formatOperatorForDisplay(op) {
    const displayMap = { '*': '×', '/': '÷' };
    return displayMap[op] || op;
}

// ==================== INITIALIZATION ====================

export function initMathPuzzle() {
    setupNumberInputs();
    setupOperatorInputs();
    setupRequirementInputs();
    setupButtons();
    setupOptionCheckboxes();
    updateExpressionSlots();
}

function setupOptionCheckboxes() {
    const analyticsCheckbox = document.getElementById('chk-show-analytics');
    const remainingCheckbox = document.getElementById('chk-show-remaining');
    const autoRecordCheckbox = document.getElementById('chk-auto-record');
    const analyticsSection = document.getElementById('analytics-section');

    if (analyticsCheckbox) {
        analyticsCheckbox.checked = showAnalytics;
        analyticsCheckbox.addEventListener('change', function () {
            showAnalytics = this.checked;
            if (analyticsSection) {
                analyticsSection.style.display = showAnalytics ? 'block' : 'none';
                if (showAnalytics) {
                    renderAnalyticsChart();
                    renderHistoryList();
                }
            }
        });
    }

    if (remainingCheckbox) {
        remainingCheckbox.checked = showRemaining;
        remainingCheckbox.addEventListener('change', function () {
            showRemaining = this.checked;
            // Re-render solutions if they exist
            const solutionsContainer = document.getElementById('math-solutions');
            if (solutionsContainer && solutionsContainer.style.display !== 'none' && lastSolveResult) {
                displaySolutions(lastSolveResult);
            }
        });
    }

    if (autoRecordCheckbox) {
        autoRecordCheckbox.addEventListener('change', function () {
            autoRecord = this.checked;
        });
    }
}

function setupNumberInputs() {
    for (let i = 0; i <= 9; i++) {
        const input = document.getElementById(`num-qty-${i}`);
        if (input) {
            input.value = gameState.numbers[i];
            input.addEventListener('change', function () {
                gameState.numbers[i] = parseInt(this.value) || 0;
            });
            // Clear 0 on focus, restore if empty on blur
            input.addEventListener('focus', function () {
                if (this.value === '0') {
                    this.value = '';
                }
                this.select();
            });
            input.addEventListener('blur', function () {
                if (this.value === '') {
                    this.value = '0';
                    gameState.numbers[i] = 0;
                }
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
            // Clear 0 on focus, restore if empty on blur
            input.addEventListener('focus', function () {
                if (this.value === '0') {
                    this.value = '';
                }
                this.select();
            });
            input.addEventListener('blur', function () {
                if (this.value === '') {
                    this.value = '0';
                    gameState.operators[op] = 0;
                }
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

const SOLVER_CONFIG = {
    maxExpressions: 10000,      // Giới hạn số biểu thức tìm được
    maxBacktrackIterations: 100000  // Giới hạn số bước backtrack
};

async function solvePuzzle() {
    // Step 1: Find ALL valid expressions (with limit)
    const allValidExpressions = findAllValidExpressions();

    if (allValidExpressions.length === 0) {
        return {
            success: false,
            maxCorrect: 0,
            message: 'Không tìm được lời giải nào với các số và phép tính hiện có!'
        };
    }

    // Step 2: Use backtracking to find the maximum set of non-overlapping expressions
    const availableNums = { ...gameState.numbers };
    const availableOps = { ...gameState.operators };

    const bestSet = findMaximalExpressionSet(allValidExpressions, availableNums, availableOps);

    // Calculate remaining resources for each solution in the set
    const solutions = [];
    const runningNums = { ...gameState.numbers };
    const runningOps = { ...gameState.operators };

    for (const sol of bestSet) {
        // Deduct used resources
        sol.numbers.forEach(num => runningNums[num]--);
        sol.operators.forEach(op => runningOps[op]--);

        solutions.push({
            ...sol,
            remainingNums: { ...runningNums },
            remainingOps: { ...runningOps }
        });
    }

    return {
        success: true,
        solutions,
        maxCorrect: solutions.length,
        message: `Số phép tính đúng tối đa: ${solutions.length}`
    };
}

function findAllValidExpressions() {
    // Build arrays from all available resources
    const numsArray = [];
    const opsArray = [];

    for (let i = 0; i <= 9; i++) {
        for (let j = 0; j < gameState.numbers[i]; j++) {
            numsArray.push(i);
        }
    }

    const ops = ['+', '-', '*', '/'];
    ops.forEach(op => {
        for (let j = 0; j < gameState.operators[op]; j++) {
            opsArray.push(op);
        }
    });

    // Check if we have enough resources
    if (numsArray.length < gameState.numDigits || opsArray.length < gameState.numOperators) {
        return [];
    }

    const validExpressions = [];
    const seen = new Set();

    // Generate unique combinations (not permutations) first, then permute
    const numCombinations = getCombinations(numsArray, gameState.numDigits);
    const opCombinations = getCombinations(opsArray, gameState.numOperators);

    outer:
    for (const numCombo of numCombinations) {
        // Get all permutations of this combination
        const numPerms = getUniquePermutations(numCombo);

        for (const nums of numPerms) {
            for (const opCombo of opCombinations) {
                const opPerms = getUniquePermutations(opCombo);

                for (const opsArr of opPerms) {
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
                        validExpressions.push({
                            expression: exprStr,
                            numbers: [...nums],
                            operators: [...opsArr]
                        });

                        // Limit number of expressions
                        if (validExpressions.length >= SOLVER_CONFIG.maxExpressions) {
                            break outer;
                        }
                    }
                }
            }
        }
    }

    return validExpressions;
}

function getCombinations(arr, length) {
    // Get unique combinations (order doesn't matter, no duplicates)
    const result = [];
    const seen = new Set();

    function backtrack(start, current) {
        if (current.length === length) {
            const key = [...current].sort().join(',');
            if (!seen.has(key)) {
                seen.add(key);
                result.push([...current]);
            }
            return;
        }

        for (let i = start; i < arr.length; i++) {
            current.push(arr[i]);
            backtrack(i + 1, current);
            current.pop();
        }
    }

    backtrack(0, []);
    return result;
}

function getUniquePermutations(arr) {
    // Get all unique permutations of an array
    const result = [];
    const seen = new Set();

    function permute(current, remaining) {
        if (remaining.length === 0) {
            const key = current.join(',');
            if (!seen.has(key)) {
                seen.add(key);
                result.push([...current]);
            }
            return;
        }

        for (let i = 0; i < remaining.length; i++) {
            current.push(remaining[i]);
            const newRemaining = [...remaining.slice(0, i), ...remaining.slice(i + 1)];
            permute(current, newRemaining);
            current.pop();
        }
    }

    permute([], arr);
    return result;
}

function findMaximalExpressionSet(allExpressions, availableNums, availableOps) {
    let bestSet = [];
    let iterations = 0;

    function canUseExpression(expr, nums, ops) {
        // Check if we have enough resources for this expression
        const tempNums = { ...nums };
        const tempOps = { ...ops };

        for (const n of expr.numbers) {
            if (tempNums[n] <= 0) return null;
            tempNums[n]--;
        }

        for (const o of expr.operators) {
            if (tempOps[o] <= 0) return null;
            tempOps[o]--;
        }

        return { tempNums, tempOps };
    }

    function backtrack(index, currentSet, nums, ops) {
        iterations++;

        // Stop if too many iterations
        if (iterations >= SOLVER_CONFIG.maxBacktrackIterations) {
            return;
        }

        // Update best if current is better
        if (currentSet.length > bestSet.length) {
            bestSet = currentSet.map(expr => ({ ...expr }));
        }

        // Pruning: if remaining expressions can't beat the best, stop
        const remainingExpressions = allExpressions.length - index;
        if (currentSet.length + remainingExpressions <= bestSet.length) {
            return;
        }

        for (let i = index; i < allExpressions.length; i++) {
            if (iterations >= SOLVER_CONFIG.maxBacktrackIterations) return;

            const expr = allExpressions[i];
            const result = canUseExpression(expr, nums, ops);

            if (result) {
                currentSet.push(expr);
                backtrack(i + 1, currentSet, result.tempNums, result.tempOps);
                currentSet.pop();
            }
        }
    }

    backtrack(0, [], availableNums, availableOps);

    return bestSet;
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

    const isLastIndex = result.solutions.length - 1;

    result.solutions.forEach((sol, index) => {
        const item = document.createElement('div');
        item.className = 'solution-item';
        // Format expression with proper symbols
        const formattedExpr = sol.expression.replace(/\*/g, '×').replace(/\//g, '÷');
        item.innerHTML = `
            <span class="solution-index">${index + 1}.</span>
            <span class="solution-expr">${formattedExpr} = ${gameState.targetResult}</span>
        `;
        list.appendChild(item);

        // Show remaining resources only for the last solution (when checkbox is checked)
        if (showRemaining && index === isLastIndex) {
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
                    opChips.innerHTML += `<span class="chip-mini chip-operator">${formatOperatorForDisplay(op)}<sup>${count}</sup></span>`;
                }
            });
            remainingDiv.appendChild(opChips);

            list.appendChild(remainingDiv);
        }
    });

    container.appendChild(list);
}

// ==================== SAVE/LOAD STATE ====================

const STORAGE_KEY_STATE = 'math-puzzle-state';
const STORAGE_KEY_RECORDS = 'math-puzzle-records';
const MAX_RECORDS = 50;

function saveCurrentState() {
    const state = {
        numbers: { ...gameState.numbers },
        operators: { ...gameState.operators },
        numDigits: gameState.numDigits,
        numOperators: gameState.numOperators,
        targetResult: gameState.targetResult
    };
    try {
        localStorage.setItem(STORAGE_KEY_STATE, JSON.stringify(state));
        showFeedback('Đã lưu trạng thái!', 'success');
    } catch (e) {
        console.error('Save error:', e);
        showFeedback('Lỗi khi lưu trạng thái!', 'error');
    }
}

function loadSavedState() {
    try {
        const saved = localStorage.getItem(STORAGE_KEY_STATE);
        if (!saved) {
            showFeedback('Chưa có trạng thái đã lưu!', 'error');
            return false;
        }

        const state = JSON.parse(saved);

        // Restore gameState
        gameState.numbers = { ...state.numbers };
        gameState.operators = { ...state.operators };
        gameState.numDigits = state.numDigits;
        gameState.numOperators = state.numOperators;
        gameState.targetResult = state.targetResult;

        // Update all UI inputs
        updateAllInputsFromState();
        updateExpressionSlots();

        showFeedback('Đã tải trạng thái!', 'success');
        return true;
    } catch (e) {
        console.error('Load error:', e);
        showFeedback('Lỗi khi tải trạng thái!', 'error');
        return false;
    }
}

function updateAllInputsFromState() {
    // Update number inputs
    for (let i = 0; i <= 9; i++) {
        const input = document.getElementById(`num-qty-${i}`);
        if (input) input.value = gameState.numbers[i];
    }

    // Update operator inputs
    const ops = ['+', '-', '*', '/'];
    const opIds = ['plus', 'minus', 'multiply', 'divide'];
    ops.forEach((op, index) => {
        const input = document.getElementById(`op-qty-${opIds[index]}`);
        if (input) input.value = gameState.operators[op];
    });

    // Update requirement inputs
    const numDigitsInput = document.getElementById('req-num-digits');
    const numOpsInput = document.getElementById('req-num-ops');
    const targetInput = document.getElementById('req-target');

    if (numDigitsInput) numDigitsInput.value = gameState.numDigits;
    if (numOpsInput) numOpsInput.value = gameState.numOperators;
    if (targetInput) targetInput.value = gameState.targetResult;
}

// ==================== RECORD MANAGER ====================

function getRecords() {
    try {
        const saved = localStorage.getItem(STORAGE_KEY_RECORDS);
        return saved ? JSON.parse(saved) : [];
    } catch (e) {
        console.error('Get records error:', e);
        return [];
    }
}

function saveRecord(record) {
    try {
        const records = getRecords();
        records.push(record);

        // Keep only last MAX_RECORDS (FIFO)
        while (records.length > MAX_RECORDS) {
            records.shift();
        }

        localStorage.setItem(STORAGE_KEY_RECORDS, JSON.stringify(records));
        return true;
    } catch (e) {
        console.error('Save record error:', e);
        return false;
    }
}

function clearRecords() {
    try {
        localStorage.removeItem(STORAGE_KEY_RECORDS);
        showFeedback('Đã xóa lịch sử!', 'success');
        return true;
    } catch (e) {
        console.error('Clear records error:', e);
        return false;
    }
}

function getBaselineInputs() {
    // Get the first record's inputs as baseline for current requirements
    const records = getRecords();
    const filtered = records.filter(r =>
        r.inputs.numDigits === gameState.numDigits &&
        r.inputs.numOperators === gameState.numOperators &&
        r.inputs.targetResult === gameState.targetResult
    );

    if (filtered.length === 0) {
        return null;
    }

    // Sort by timestamp ascending, get first
    filtered.sort((a, b) => a.id - b.id);
    return filtered[0].inputs;
}

function computeDelta(currentInputs, baselineInputs) {
    if (!baselineInputs) return null;

    const deltaNumbers = {};
    const deltaOperators = {};

    // Compute number deltas (compared to baseline/first record)
    for (let i = 0; i <= 9; i++) {
        const diff = currentInputs.numbers[i] - baselineInputs.numbers[i];
        if (diff !== 0) {
            deltaNumbers[i] = diff;
        }
    }

    // Compute operator deltas (compared to baseline/first record)
    const ops = ['+', '-', '*', '/'];
    ops.forEach(op => {
        const diff = currentInputs.operators[op] - baselineInputs.operators[op];
        if (diff !== 0) {
            deltaOperators[op] = diff;
        }
    });

    // Return null if no changes from baseline
    if (Object.keys(deltaNumbers).length === 0 && Object.keys(deltaOperators).length === 0) {
        return null;
    }

    return { deltaNumbers, deltaOperators };
}

function createRecord(solveResult) {
    const currentInputs = {
        numbers: { ...gameState.numbers },
        operators: { ...gameState.operators },
        numDigits: gameState.numDigits,
        numOperators: gameState.numOperators,
        targetResult: gameState.targetResult
    };

    // Get baseline (first record) to compute delta
    const baselineInputs = getBaselineInputs();
    const delta = computeDelta(currentInputs, baselineInputs);

    // Get final remaining from last solution
    let finalRemaining = null;
    if (solveResult.success && solveResult.solutions.length > 0) {
        const lastSol = solveResult.solutions[solveResult.solutions.length - 1];
        finalRemaining = {
            numbers: { ...lastSol.remainingNums },
            operators: { ...lastSol.remainingOps }
        };
    }

    const record = {
        id: Date.now(),
        timestamp: new Date().toISOString(),
        inputs: currentInputs,
        result: {
            success: solveResult.success,
            maxCorrect: solveResult.maxCorrect,
            solutionCount: solveResult.solutions ? solveResult.solutions.length : 0
        },
        remaining: finalRemaining,
        delta: delta // Delta compared to FIRST record (baseline)
    };

    return record;
}

// ==================== ANALYTICS ENGINE ====================

let analyticsChart = null;

function generateRemainingKey(remaining) {
    if (!remaining) return 'none';

    const numParts = [];
    for (let i = 0; i <= 9; i++) {
        if (remaining.numbers[i] > 0) {
            numParts.push(`${i}:${remaining.numbers[i]}`);
        }
    }

    const opParts = [];
    const ops = ['+', '-', '*', '/'];
    ops.forEach(op => {
        if (remaining.operators[op] > 0) {
            opParts.push(`${op}:${remaining.operators[op]}`);
        }
    });

    if (numParts.length === 0 && opParts.length === 0) {
        return 'empty';
    }

    return `${numParts.join(',')}|${opParts.join(',')}`;
}

function groupByExactRemaining(records) {
    const groups = new Map();

    records.forEach(record => {
        const key = generateRemainingKey(record.remaining);
        if (!groups.has(key)) {
            groups.set(key, []);
        }
        groups.get(key).push(record);
    });

    return groups;
}

function prepareChartData(records) {
    // Filter records matching current requirements
    const filtered = records.filter(r =>
        r.inputs.numDigits === gameState.numDigits &&
        r.inputs.numOperators === gameState.numOperators &&
        r.inputs.targetResult === gameState.targetResult
    );

    // Sort by timestamp
    filtered.sort((a, b) => a.id - b.id);

    const labels = [];
    const data = [];
    const tooltipData = [];

    filtered.forEach((record, index) => {
        labels.push(`#${index + 1}`);
        data.push(record.result.maxCorrect);

        // Build tooltip info - delta compared to FIRST record (baseline)
        let deltaStr = '';
        if (index === 0) {
            deltaStr = 'Baseline (lần đầu)';
        } else if (record.delta) {
            const parts = [];
            Object.entries(record.delta.deltaNumbers || {}).forEach(([num, diff]) => {
                parts.push(`${diff > 0 ? '+' : ''}${diff} số ${num}`);
            });
            Object.entries(record.delta.deltaOperators || {}).forEach(([op, diff]) => {
                parts.push(`${diff > 0 ? '+' : ''}${diff} phép ${formatOperatorForDisplay(op)}`);
            });
            deltaStr = parts.length > 0 ? parts.join(', ') : 'Không đổi so với baseline';
        } else {
            deltaStr = 'Không đổi so với baseline';
        }

        tooltipData.push({
            delta: deltaStr,
            maxCorrect: record.result.maxCorrect,
            timestamp: new Date(record.timestamp).toLocaleString('vi-VN')
        });
    });

    return { labels, data, tooltipData, recordCount: filtered.length };
}

function renderAnalyticsChart() {
    const canvas = document.getElementById('analytics-chart');
    if (!canvas) return;

    const records = getRecords();
    const chartData = prepareChartData(records);

    if (chartData.recordCount === 0) {
        // Show message instead of chart
        const container = canvas.parentElement;
        container.innerHTML = '<div class="no-records">Chưa có dữ liệu. Hãy "Xem Cách Giải" để ghi nhận kết quả!</div>';
        return;
    }

    // Ensure canvas exists
    if (!document.getElementById('analytics-chart')) {
        const container = document.getElementById('analytics-chart-container');
        if (container) {
            container.innerHTML = '<canvas id="analytics-chart"></canvas>';
        }
    }

    const ctx = document.getElementById('analytics-chart');
    if (!ctx) return;

    // Destroy existing chart
    if (analyticsChart) {
        analyticsChart.destroy();
    }

    // Create new chart
    analyticsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: chartData.labels,
            datasets: [{
                label: 'Số phép tính đúng',
                data: chartData.data,
                borderColor: '#007bff',
                backgroundColor: 'rgba(0, 123, 255, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.3,
                pointRadius: 5,
                pointHoverRadius: 8,
                pointBackgroundColor: '#007bff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        title: (items) => {
                            const idx = items[0].dataIndex;
                            return `Lần thử ${chartData.labels[idx]}`;
                        },
                        label: (item) => {
                            const idx = item.dataIndex;
                            const info = chartData.tooltipData[idx];
                            return [
                                `Kết quả: ${info.maxCorrect} phép tính`,
                                `So với baseline: ${info.delta}`,
                                `Thời gian: ${info.timestamp}`
                            ];
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    },
                    title: {
                        display: true,
                        text: 'Số phép tính đúng'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Lần thử'
                    }
                }
            }
        }
    });
}

function renderHistoryList() {
    const container = document.getElementById('history-list');
    if (!container) return;

    const records = getRecords();

    // Filter records matching current requirements
    const filtered = records.filter(r =>
        r.inputs.numDigits === gameState.numDigits &&
        r.inputs.numOperators === gameState.numOperators &&
        r.inputs.targetResult === gameState.targetResult
    );

    // Sort by timestamp descending, take last 10
    filtered.sort((a, b) => b.id - a.id);
    const recent = filtered.slice(0, 10);

    if (recent.length === 0) {
        container.innerHTML = '<div class="no-records">Chưa có lịch sử cho yêu cầu hiện tại.</div>';
        return;
    }

    container.innerHTML = '';

    recent.forEach((record, index) => {
        const item = document.createElement('div');
        item.className = 'history-item';

        // Get record's position in the full filtered list (for determining if it's baseline)
        const recordPosition = filtered.length - index;
        const isBaseline = recordPosition === 1;

        // Build delta display - compared to FIRST record (baseline)
        let deltaHtml = '';
        if (isBaseline) {
            deltaHtml = '<span class="delta-first">Baseline</span>';
        } else if (record.delta) {
            const chips = [];
            Object.entries(record.delta.deltaNumbers || {}).forEach(([num, diff]) => {
                const sign = diff > 0 ? '+' : '';
                chips.push(`<span class="delta-chip num">${sign}${diff} số ${num}</span>`);
            });
            Object.entries(record.delta.deltaOperators || {}).forEach(([op, diff]) => {
                const sign = diff > 0 ? '+' : '';
                chips.push(`<span class="delta-chip op">${sign}${diff} ${formatOperatorForDisplay(op)}</span>`);
            });
            deltaHtml = chips.length > 0 ? chips.join(' ') : '<span class="delta-none">Không đổi</span>';
        } else {
            deltaHtml = '<span class="delta-none">Không đổi</span>';
        }

        item.innerHTML = `
            <div class="history-main">
                <span class="history-index">#${recordPosition}</span>
                <span class="history-result">${record.result.maxCorrect} phép tính</span>
                <span class="history-delta">Δ: ${deltaHtml}</span>
            </div>
        `;

        container.appendChild(item);
    });
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

let autoRecord = false;

function setupButtons() {
    const btnReset = document.getElementById('btnMathReset');
    const btnSolve = document.getElementById('btnMathSolve');
    const btnExample = document.getElementById('btnMathExample');
    const btnSave = document.getElementById('btnMathSave');
    const btnLoad = document.getElementById('btnMathLoad');
    const btnAnalytics = document.getElementById('btnAnalytics');
    const btnClearHistory = document.getElementById('btnClearHistory');

    if (btnReset) {
        btnReset.addEventListener('click', resetGame);
    }

    if (btnSolve) {
        btnSolve.addEventListener('click', async () => {
            btnSolve.disabled = true;
            btnSolve.textContent = 'Đang giải...';

            // Allow UI to update before heavy computation
            await new Promise(resolve => setTimeout(resolve, 10));

            try {
                const result = await solvePuzzle();
                lastSolveResult = result;
                displaySolutions(result);

                // Auto-record if enabled
                if (autoRecord && result.success) {
                    const record = createRecord(result);
                    saveRecord(record);

                    // Update analytics if visible
                    const analyticsSection = document.getElementById('analytics-section');
                    if (analyticsSection && analyticsSection.style.display !== 'none') {
                        renderAnalyticsChart();
                        renderHistoryList();
                    }
                }
            } catch (error) {
                console.error('Solver error:', error);
                showFeedback('Có lỗi xảy ra khi giải!', 'error');
            } finally {
                btnSolve.disabled = false;
                btnSolve.textContent = 'Xem Cách Giải';
            }
        });
    }

    if (btnExample) {
        btnExample.addEventListener('click', loadExample);
    }

    // Save/Load handlers
    if (btnSave) {
        btnSave.addEventListener('click', saveCurrentState);
    }

    if (btnLoad) {
        btnLoad.addEventListener('click', loadSavedState);
    }

    // Analytics handlers
    if (btnAnalytics) {
        btnAnalytics.addEventListener('click', () => {
            renderAnalyticsChart();
            renderHistoryList();
        });
    }

    if (btnClearHistory) {
        btnClearHistory.addEventListener('click', () => {
            if (confirm('Bạn có chắc muốn xóa toàn bộ lịch sử?')) {
                clearRecords();
                renderAnalyticsChart();
                renderHistoryList();
            }
        });
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
    lastSolveResult = null;

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
