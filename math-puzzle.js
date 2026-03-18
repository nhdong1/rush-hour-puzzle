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

let showSuggest = false;
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
    const suggestCheckbox = document.getElementById('chk-show-suggest');
    const remainingCheckbox = document.getElementById('chk-show-remaining');
    const suggestSection = document.getElementById('suggest-section');

    if (suggestCheckbox) {
        suggestCheckbox.checked = showSuggest;
        suggestCheckbox.addEventListener('change', function () {
            showSuggest = this.checked;
            if (suggestSection) {
                suggestSection.style.display = showSuggest ? 'block' : 'none';
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

// ==================== SUGGEST FEATURE ====================

async function suggestBestAdditions(extraTotal) {
    // Get current baseline result
    const baselineResult = await solvePuzzleWithState(gameState.numbers, gameState.operators);
    const baselineCount = baselineResult.success ? baselineResult.maxCorrect : 0;

    if (extraTotal <= 0) {
        return {
            baseline: baselineCount,
            suggestions: [],
            message: 'Vui lòng nhập số lượng muốn thêm!'
        };
    }

    const allNumbers = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9];
    const allOperators = ['+', '-', '*', '/'];
    const allItems = [...allNumbers.map(n => ({ type: 'num', value: n })),
    ...allOperators.map(op => ({ type: 'op', value: op }))];

    // Generate all possible combinations of items to add
    const suggestions = [];
    const itemCombinations = generateAdditionCombinations(allItems, extraTotal);

    // Limit total combinations to avoid performance issues
    const maxCombinations = 500;
    let testedCount = 0;

    for (const combo of itemCombinations) {
        if (testedCount >= maxCombinations) break;
        testedCount++;

        // Create modified state
        const modifiedNums = { ...gameState.numbers };
        const modifiedOps = { ...gameState.operators };
        const addedNumbers = [];
        const addedOperators = [];

        // Add items
        for (const item of combo) {
            if (item.type === 'num') {
                modifiedNums[item.value]++;
                addedNumbers.push(item.value);
            } else {
                modifiedOps[item.value]++;
                addedOperators.push(item.value);
            }
        }

        // Solve with modified state
        const result = await solvePuzzleWithState(modifiedNums, modifiedOps);
        const count = result.success ? result.maxCorrect : 0;

        if (count > baselineCount) {
            suggestions.push({
                addedNumbers,
                addedOperators,
                resultCount: count,
                improvement: count - baselineCount
            });
        }
    }

    // Sort by improvement (descending)
    suggestions.sort((a, b) => b.improvement - a.improvement ||
        (a.addedNumbers.length + a.addedOperators.length) - (b.addedNumbers.length + b.addedOperators.length));

    // Keep top 5 unique suggestions
    const uniqueSuggestions = [];
    const seen = new Set();
    for (const sug of suggestions) {
        const key = JSON.stringify([sug.addedNumbers.sort(), sug.addedOperators.sort()]);
        if (!seen.has(key)) {
            seen.add(key);
            uniqueSuggestions.push(sug);
            if (uniqueSuggestions.length >= 5) break;
        }
    }

    return {
        baseline: baselineCount,
        suggestions: uniqueSuggestions,
        testedCombinations: testedCount,
        message: uniqueSuggestions.length > 0
            ? `Tìm thấy ${uniqueSuggestions.length} gợi ý tốt nhất!`
            : 'Không tìm thấy cách thêm nào cải thiện kết quả.'
    };
}

function generateAdditionCombinations(items, count) {
    if (count === 0) return [[]];

    const result = [];

    function backtrack(start, current) {
        if (current.length === count) {
            result.push([...current]);
            return;
        }

        for (let i = start; i < items.length; i++) {
            current.push(items[i]);
            backtrack(i, current); // Allow same item multiple times
            current.pop();
        }
    }

    backtrack(0, []);
    return result;
}

async function solvePuzzleWithState(numbers, operators) {
    // Build arrays from resources
    const numsArray = [];
    const opsArray = [];

    for (let i = 0; i <= 9; i++) {
        for (let j = 0; j < numbers[i]; j++) {
            numsArray.push(i);
        }
    }

    const ops = ['+', '-', '*', '/'];
    ops.forEach(op => {
        for (let j = 0; j < operators[op]; j++) {
            opsArray.push(op);
        }
    });

    // Check if we have enough resources
    if (numsArray.length < gameState.numDigits || opsArray.length < gameState.numOperators) {
        return { success: false, maxCorrect: 0 };
    }

    // Find all valid expressions
    const validExpressions = [];
    const seen = new Set();

    const numCombinations = getCombinations(numsArray, gameState.numDigits);
    const opCombinations = getCombinations(opsArray, gameState.numOperators);

    outer:
    for (const numCombo of numCombinations) {
        const numPerms = getUniquePermutations(numCombo);

        for (const nums of numPerms) {
            for (const opCombo of opCombinations) {
                const opPerms = getUniquePermutations(opCombo);

                for (const opsArr of opPerms) {
                    const expr = [];
                    for (let i = 0; i < nums.length; i++) {
                        expr.push({ value: nums[i], type: 'number' });
                        if (i < opsArr.length) {
                            expr.push({ value: opsArr[i], type: 'operator' });
                        }
                    }

                    const exprStr = expr.map(e => e.value).join(' ');
                    if (seen.has(exprStr)) continue;
                    seen.add(exprStr);

                    const result = evaluateExpression(expr);

                    if (result === gameState.targetResult) {
                        validExpressions.push({
                            expression: exprStr,
                            numbers: [...nums],
                            operators: [...opsArr]
                        });

                        if (validExpressions.length >= SOLVER_CONFIG.maxExpressions) {
                            break outer;
                        }
                    }
                }
            }
        }
    }

    if (validExpressions.length === 0) {
        return { success: false, maxCorrect: 0 };
    }

    // Find maximal set
    const bestSet = findMaximalExpressionSet(validExpressions, numbers, operators);

    return {
        success: true,
        maxCorrect: bestSet.length
    };
}

function displaySuggestions(result) {
    const container = document.getElementById('suggest-result');
    if (!container) return;

    container.style.display = 'block';
    container.innerHTML = '';

    const content = document.createElement('div');
    content.className = 'suggest-result-content';

    // Header with baseline
    const header = document.createElement('div');
    header.className = 'suggest-header';
    header.innerHTML = `📊 Kết quả hiện tại: <strong>${result.baseline}</strong> phép tính đúng`;
    content.appendChild(header);

    if (result.suggestions.length === 0) {
        const noResult = document.createElement('div');
        noResult.className = 'suggest-no-improvement';
        noResult.innerHTML = result.message;
        content.appendChild(noResult);
    } else {
        const sugList = document.createElement('div');

        result.suggestions.forEach((sug, index) => {
            const item = document.createElement('div');
            item.className = 'suggest-item';

            // Build add chips
            let addHtml = '<div class="suggest-add">';

            if (sug.addedNumbers.length > 0) {
                addHtml += '<span>Thêm số: </span>';
                sug.addedNumbers.forEach(n => {
                    addHtml += `<span class="suggest-chip num">${n}</span>`;
                });
            }

            if (sug.addedOperators.length > 0) {
                addHtml += '<span style="margin-left: 10px;">Thêm phép: </span>';
                sug.addedOperators.forEach(op => {
                    addHtml += `<span class="suggest-chip op">${formatOperatorForDisplay(op)}</span>`;
                });
            }

            addHtml += '</div>';

            item.innerHTML = `
                <span class="solution-index">${index + 1}.</span>
                ${addHtml}
                <span class="suggest-improvement">→ ${sug.resultCount} phép tính (+${sug.improvement})</span>
            `;
            sugList.appendChild(item);
        });

        content.appendChild(sugList);
    }

    container.appendChild(content);
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
    const btnSuggest = document.getElementById('btnMathSuggest');

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

    if (btnSuggest) {
        btnSuggest.addEventListener('click', async () => {
            btnSuggest.disabled = true;
            btnSuggest.textContent = 'Đang tính...';

            await new Promise(resolve => setTimeout(resolve, 10));

            try {
                const extraTotal = parseInt(document.getElementById('suggest-extra-total').value) || 1;
                const result = await suggestBestAdditions(extraTotal);
                displaySuggestions(result);
            } catch (error) {
                console.error('Suggest error:', error);
                showFeedback('Có lỗi xảy ra khi tính gợi ý!', 'error');
            } finally {
                btnSuggest.disabled = false;
                btnSuggest.textContent = 'Gợi Ý';
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
