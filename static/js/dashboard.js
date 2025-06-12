/**
 * Dashboard JavaScript functionality
 * Handles auto-refresh, loading states, error handling, and keyboard navigation
 */

class DashboardManager {
    constructor() {
        this.refreshInterval = null;
        this.refreshIntervalMs = 5 * 60 * 1000; // 5 minutes
        this.isRefreshing = false;
        this.retryCount = 0;
        this.maxRetries = 3;
        
        this.init();
    }
    
    init() {
        this.setupAutoRefresh();
        this.setupKeyboardNavigation();
        this.setupErrorHandling();
        this.setupVisibilityChangeHandling();
        this.logInitialization();
    }
    
    /**
     * Setup auto-refresh timer for dashboard statistics
     */
    setupAutoRefresh() {
        // Start auto-refresh timer
        this.refreshInterval = setInterval(() => {
            this.refreshStats();
        }, this.refreshIntervalMs);
        
        // Add manual refresh capability
        this.addManualRefreshButton();
        
        console.log('Dashboard auto-refresh setup completed (5 minute intervals)');
    }
    
    /**
     * Add manual refresh button to dashboard header
     */
    addManualRefreshButton() {
        const header = document.querySelector('header');
        if (header) {
            const refreshButton = document.createElement('button');
            refreshButton.innerHTML = `
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                </svg>
                <span class="ml-1 hidden sm:inline">Odśwież</span>
            `;
            refreshButton.className = 'flex items-center px-3 py-1 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2';
            refreshButton.onclick = () => this.refreshStats(true);
            refreshButton.setAttribute('aria-label', 'Odśwież statystyki dashboard');
            
            // Insert before logout button
            const logoutForm = header.querySelector('form');
            if (logoutForm) {
                logoutForm.parentNode.insertBefore(refreshButton, logoutForm);
            }
        }
    }
    
    /**
     * Refresh dashboard statistics
     */
    async refreshStats(isManual = false) {
        if (this.isRefreshing) {
            console.log('Refresh already in progress, skipping');
            return;
        }
        
        this.isRefreshing = true;
        
        try {
            if (isManual) {
                console.log('Manual refresh triggered');
            } else {
                console.log('Auto-refresh triggered');
            }
            
            // Show loading states
            this.showLoadingStates();
            
            // Fetch fresh stats from server
            const response = await fetch('/api/dashboard/refresh-stats', {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'Cache-Control': 'no-cache'
                },
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            // Update stats in DOM
            this.updateStatsInDOM(data.stats);
            
            // Reset retry count on success
            this.retryCount = 0;
            
            // Hide loading states
            this.hideLoadingStates();
            
            // Show success feedback for manual refresh
            if (isManual) {
                this.showRefreshFeedback('success', 'Statystyki zostały odświeżone');
            }
            
            console.log('Dashboard stats refreshed successfully');
            
        } catch (error) {
            console.error('Error refreshing dashboard stats:', error);
            
            this.retryCount++;
            
            // Hide loading states
            this.hideLoadingStates();
            
            // Handle different error scenarios
            if (error.message.includes('401')) {
                // Authentication error - redirect to login
                this.handleAuthError();
            } else if (error.message.includes('NetworkError') || error.name === 'TypeError') {
                // Network error
                this.handleNetworkError(isManual);
            } else {
                // Generic server error
                this.handleServerError(isManual);
            }
        } finally {
            this.isRefreshing = false;
        }
    }
    
    /**
     * Show loading states on all stat cards
     */
    showLoadingStates() {
        const statsCards = document.querySelectorAll('#statsSection .bg-white');
        
        statsCards.forEach(card => {
            // Find the number element and add loading spinner
            const numberElement = card.querySelector('.text-2xl');
            if (numberElement) {
                const originalText = numberElement.textContent;
                numberElement.dataset.originalText = originalText;
                numberElement.innerHTML = `
                    <div class="flex items-center">
                        <div class="w-4 h-4 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin mr-2"></div>
                        <span class="text-gray-400">...</span>
                    </div>
                `;
            }
            
            // Add visual feedback
            card.style.opacity = '0.7';
            card.style.pointerEvents = 'none';
        });
        
        // Show main loading spinner if exists
        const mainSpinner = document.getElementById('statsLoadingSpinner');
        if (mainSpinner) {
            mainSpinner.classList.remove('hidden');
        }
    }
    
    /**
     * Hide loading states
     */
    hideLoadingStates() {
        const statsCards = document.querySelectorAll('#statsSection .bg-white');
        
        statsCards.forEach(card => {
            card.style.opacity = '1';
            card.style.pointerEvents = 'auto';
        });
        
        // Hide main loading spinner
        const mainSpinner = document.getElementById('statsLoadingSpinner');
        if (mainSpinner) {
            mainSpinner.classList.add('hidden');
        }
    }
    
    /**
     * Update statistics in DOM with new data
     */
    updateStatsInDOM(stats) {
        if (!stats) return;
        
        // Update total flashcards
        const flashcardsElement = document.querySelector('#statsSection .bg-white:nth-child(1) .text-2xl');
        if (flashcardsElement && flashcardsElement.dataset.originalText !== undefined) {
            flashcardsElement.textContent = stats.total_flashcards;
            delete flashcardsElement.dataset.originalText;
        }
        
        // Update due cards today
        const dueCardsElement = document.querySelector('#statsSection .bg-white:nth-child(2) .text-2xl');
        if (dueCardsElement && dueCardsElement.dataset.originalText !== undefined) {
            dueCardsElement.textContent = stats.due_cards_today;
            delete dueCardsElement.dataset.originalText;
        }
        
        // Update AI stats
        const aiStatsElement = document.querySelector('#statsSection .bg-white:nth-child(3) .text-2xl');
        if (aiStatsElement && aiStatsElement.dataset.originalText !== undefined) {
            const ratio = `${stats.ai_stats.total_accepted}/${stats.ai_stats.total_generated}`;
            aiStatsElement.textContent = ratio;
            delete aiStatsElement.dataset.originalText;
        }
        
        // Update secondary text for due cards
        const dueCardsSecondary = document.querySelector('#statsSection .bg-white:nth-child(2) .text-xs');
        if (dueCardsSecondary) {
            dueCardsSecondary.textContent = stats.due_cards_today > 0 ? 'Gotowe do nauki!' : 'Wszystko na bieżąco';
        }
        
        // Update AI stats secondary text
        const aiStatsSecondary = document.querySelector('#statsSection .bg-white:nth-child(3) .text-xs');
        if (aiStatsSecondary && stats.ai_stats.total_generated > 0) {
            const percentage = ((stats.ai_stats.total_accepted / stats.ai_stats.total_generated) * 100).toFixed(1);
            aiStatsSecondary.textContent = `${percentage}% akceptacja`;
        } else if (aiStatsSecondary) {
            aiStatsSecondary.textContent = 'Brak generacji AI';
        }
    }
    
    /**
     * Show refresh feedback message
     */
    showRefreshFeedback(type, message) {
        const feedback = document.createElement('div');
        feedback.className = `fixed top-4 right-4 px-4 py-2 rounded-md shadow-lg z-50 ${
            type === 'success' ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
        }`;
        feedback.textContent = message;
        
        document.body.appendChild(feedback);
        
        // Animate in
        feedback.style.transform = 'translateX(100%)';
        feedback.style.transition = 'transform 0.3s ease-out';
        setTimeout(() => {
            feedback.style.transform = 'translateX(0)';
        }, 10);
        
        // Remove after 3 seconds
        setTimeout(() => {
            feedback.style.transform = 'translateX(100%)';
            setTimeout(() => {
                document.body.removeChild(feedback);
            }, 300);
        }, 3000);
    }
    
    /**
     * Handle authentication errors
     */
    handleAuthError() {
        console.log('Authentication error detected, redirecting to login');
        this.clearAutoRefresh();
        window.location.href = '/login?next=' + encodeURIComponent(window.location.pathname);
    }
    
    /**
     * Handle network errors
     */
    handleNetworkError(isManual) {
        const message = 'Brak połączenia z internetem';
        console.warn('Network error during refresh');
        
        if (isManual) {
            this.showRefreshFeedback('error', message);
        }
        
        // Implement exponential backoff for retries
        if (this.retryCount < this.maxRetries) {
            const retryDelay = Math.pow(2, this.retryCount) * 1000; // 1s, 2s, 4s
            console.log(`Retrying refresh in ${retryDelay}ms (attempt ${this.retryCount}/${this.maxRetries})`);
            
            setTimeout(() => {
                this.refreshStats(false);
            }, retryDelay);
        }
    }
    
    /**
     * Handle server errors
     */
    handleServerError(isManual) {
        const message = 'Wystąpił błąd serwera podczas odświeżania';
        console.error('Server error during refresh');
        
        if (isManual) {
            this.showRefreshFeedback('error', message);
        }
    }
    
    /**
     * Setup keyboard navigation enhancement
     */
    setupKeyboardNavigation() {
        document.addEventListener('keydown', (e) => {
            // Enhanced tab navigation
            if (e.key === 'Tab') {
                this.enhanceTabNavigation();
            }
            
            // Arrow key navigation for cards
            if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
                this.handleArrowNavigation(e);
            }
            
            // Quick action shortcuts
            if (e.ctrlKey || e.metaKey) {
                this.handleQuickShortcuts(e);
            }
        });
        
        console.log('Keyboard navigation setup completed');
    }
    
    /**
     * Enhance tab navigation with visual feedback
     */
    enhanceTabNavigation() {
        setTimeout(() => {
            const focused = document.activeElement;
            if (focused && (focused.hasAttribute('role') || focused.tagName === 'A' || focused.tagName === 'BUTTON')) {
                // Add enhanced focus ring
                focused.style.boxShadow = '0 0 0 3px rgba(99, 102, 241, 0.5)';
                focused.style.transition = 'box-shadow 0.2s ease';
                
                // Remove enhanced focus on blur
                const removeEnhancement = () => {
                    focused.style.boxShadow = '';
                    focused.removeEventListener('blur', removeEnhancement);
                };
                focused.addEventListener('blur', removeEnhancement);
            }
        }, 10);
    }
    
    /**
     * Handle arrow key navigation between cards
     */
    handleArrowNavigation(e) {
        const cards = document.querySelectorAll('#statsSection .cursor-pointer, [role="button"]');
        const currentIndex = Array.from(cards).indexOf(document.activeElement);
        
        if (currentIndex >= 0) {
            e.preventDefault();
            let nextIndex;
            
            if (e.key === 'ArrowRight') {
                nextIndex = (currentIndex + 1) % cards.length;
            } else {
                nextIndex = (currentIndex - 1 + cards.length) % cards.length;
            }
            
            cards[nextIndex].focus();
        }
    }
    
    /**
     * Handle keyboard shortcuts
     */
    handleQuickShortcuts(e) {
        switch (e.key) {
            case 'r':
                e.preventDefault();
                this.refreshStats(true);
                break;
            case 'g':
                e.preventDefault();
                window.location.href = '/generate';
                break;
            case 'f':
                e.preventDefault();
                window.location.href = '/flashcards';
                break;
            case 's':
                e.preventDefault();
                window.location.href = '/study-session';
                break;
        }
    }
    
    /**
     * Setup error handling for uncaught errors
     */
    setupErrorHandling() {
        window.addEventListener('error', (e) => {
            console.error('Dashboard JavaScript error:', e.error);
        });
        
        window.addEventListener('unhandledrejection', (e) => {
            console.error('Dashboard unhandled promise rejection:', e.reason);
        });
    }
    
    /**
     * Handle page visibility changes (pause refresh when tab is hidden)
     */
    setupVisibilityChangeHandling() {
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                // Page is hidden, pause auto-refresh
                this.clearAutoRefresh();
                console.log('Dashboard auto-refresh paused (tab hidden)');
            } else {
                // Page is visible again, resume auto-refresh
                this.setupAutoRefresh();
                console.log('Dashboard auto-refresh resumed (tab visible)');
                
                // Trigger immediate refresh if page was hidden for more than 1 minute
                const lastRefresh = this.lastRefreshTime || Date.now();
                if (Date.now() - lastRefresh > 60000) {
                    this.refreshStats(false);
                }
            }
        });
    }
    
    /**
     * Clear auto-refresh timer
     */
    clearAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }
    
    /**
     * Log initialization info
     */
    logInitialization() {
        console.log('Dashboard Manager initialized successfully');
        console.log('Features enabled:', {
            autoRefresh: true,
            keyboardNavigation: true,
            errorHandling: true,
            visibilityHandling: true,
            shortcuts: 'Ctrl+R (refresh), Ctrl+G (generate), Ctrl+F (flashcards), Ctrl+S (study)'
        });
        
        this.lastRefreshTime = Date.now();
    }
    
    /**
     * Cleanup when page is unloaded
     */
    cleanup() {
        this.clearAutoRefresh();
        console.log('Dashboard Manager cleanup completed');
    }
}

// Initialize Dashboard Manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Check if we're on the dashboard page
    if (window.location.pathname === '/dashboard') {
        window.dashboardManager = new DashboardManager();
        
        // Cleanup on page unload
        window.addEventListener('beforeunload', () => {
            window.dashboardManager.cleanup();
        });
    }
});

// Export for testing purposes
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DashboardManager;
} 