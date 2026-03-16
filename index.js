// ==================== MAIN APP - TAB MANAGEMENT ====================

import { initRushHour } from './rush-hour.js';
import { initMathPuzzle } from './math-puzzle.js';
import { initChess } from './chess.js';

// Tab configuration
const TABS = {
    'rush-hour': {
        id: 'tab-rush-hour',
        btnId: 'tab-btn-rush-hour',
        init: initRushHour,
        initialized: false
    },
    'math-puzzle': {
        id: 'tab-math-puzzle',
        btnId: 'tab-btn-math-puzzle',
        init: initMathPuzzle,
        initialized: false
    },
    'chess': {
        id: 'tab-chess',
        btnId: 'tab-btn-chess',
        init: initChess,
        initialized: false
    }
};

const DEFAULT_TAB = 'rush-hour';

// ==================== URL PARAMS ====================

function getTabFromURL() {
    const params = new URLSearchParams(window.location.search);
    const tab = params.get('tab');
    return TABS[tab] ? tab : DEFAULT_TAB;
}

function updateURL(tabName) {
    const url = new URL(window.location);
    url.searchParams.set('tab', tabName);
    history.pushState({ tab: tabName }, '', url);
}

// ==================== TAB SWITCHING ====================

function switchTab(tabName) {
    if (!TABS[tabName]) return;

    // Update tab buttons
    Object.keys(TABS).forEach(key => {
        const btn = document.getElementById(TABS[key].btnId);
        const panel = document.getElementById(TABS[key].id);

        if (btn) {
            btn.classList.toggle('active', key === tabName);
        }
        if (panel) {
            panel.classList.toggle('active', key === tabName);
        }
    });

    // Initialize tab if needed
    const tab = TABS[tabName];
    if (!tab.initialized && tab.init) {
        tab.init();
        tab.initialized = true;
    }

    // Update URL
    updateURL(tabName);
}

// ==================== INITIALIZATION ====================

function initApp() {
    // Setup tab button click handlers
    Object.keys(TABS).forEach(tabName => {
        const btn = document.getElementById(TABS[tabName].btnId);
        if (btn) {
            btn.addEventListener('click', () => switchTab(tabName));
        }
    });

    // Handle browser back/forward
    window.addEventListener('popstate', (event) => {
        const tabName = event.state?.tab || getTabFromURL();
        switchTabWithoutPush(tabName);
    });

    // Initialize from URL or default
    const initialTab = getTabFromURL();
    switchTab(initialTab);
}

function switchTabWithoutPush(tabName) {
    if (!TABS[tabName]) return;

    // Update tab buttons
    Object.keys(TABS).forEach(key => {
        const btn = document.getElementById(TABS[key].btnId);
        const panel = document.getElementById(TABS[key].id);

        if (btn) {
            btn.classList.toggle('active', key === tabName);
        }
        if (panel) {
            panel.classList.toggle('active', key === tabName);
        }
    });

    // Initialize tab if needed
    const tab = TABS[tabName];
    if (!tab.initialized && tab.init) {
        tab.init();
        tab.initialized = true;
    }
}

// Start app when DOM is ready
document.addEventListener('DOMContentLoaded', initApp);
