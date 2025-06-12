/**
 * Study Session JavaScript functionality
 * Manages the spaced repetition learning session with flashcards
 */

// Enums and constants
const CardSide = {
    FRONT: 'front',
    BACK: 'back'
};

const StudySessionState = {
    INITIALIZING: 'initializing',
    LOADING: 'loading',
    SHOWING_CARD: 'showing_card',
    SHOWING_ANSWER: 'showing_answer',
    SUBMITTING_RATING: 'submitting_rating',
    SESSION_COMPLETED: 'session_completed',
    ERROR: 'error'
};

class StudySessionManager {
    constructor() {
        this.flashcards = [];
        this.currentIndex = 0;
        this.currentSide = CardSide.FRONT;
        this.state = StudySessionState.INITIALIZING;
        this.isSubmittingRating = false;
        this.error = null;
        this.sessionCompleted = false;
        this.retryCount = 0;
        this.maxRetries = 3;
        
        this.init();
    }
    
    /**
     * Initialize the study session
     */
    async init() {
        try {
            console.log('Initializing study session...');
            this.setupKeyboardNavigation();
            this.setupErrorHandling();
            
            // Load flashcards due for review
            await this.loadDueFlashcards();
            
            console.log('Study session initialized successfully');
        } catch (error) {
            console.error('Failed to initialize study session:', error);
            this.handleError('Nie udało się zainicjować sesji nauki');
        }
    }
    
    /**
     * Load flashcards that are due for review
     */
    async loadDueFlashcards() {
        this.setState(StudySessionState.LOADING);
        this.showLoadingSpinner('Ładowanie fiszek do powtórki...');
        
        try {
            const response = await fetch('/api/v1/spaced-repetition/due-cards?limit=20', {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'Cache-Control': 'no-cache'
                },
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                if (response.status === 401) {
                    this.handleAuthError();
                    return;
                }
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const flashcards = await response.json();
            
            if (flashcards.length === 0) {
                this.handleEmptySession();
                return;
            }
            
            this.flashcards = flashcards;
            this.currentIndex = 0;
            this.currentSide = CardSide.FRONT;
            this.sessionCompleted = false;
            
            this.hideLoadingSpinner();
            this.setState(StudySessionState.SHOWING_CARD);
            this.renderCurrentCard();
            
            console.log(`Loaded ${flashcards.length} flashcards for review`);
            
        } catch (error) {
            console.error('Error loading due flashcards:', error);
            this.hideLoadingSpinner();
            this.handleError('Nie udało się załadować fiszek do powtórki');
        }
    }
    

    
    /**
     * Handle empty session (no cards due for review)
     */
    handleEmptySession() {
        this.sessionCompleted = true;
        this.setState(StudySessionState.SESSION_COMPLETED);
        this.hideLoadingSpinner();
        this.showEmptyState();
        console.log('No cards due for review - showing empty state');
    }
    
    /**
     * Show answer for current flashcard
     */
    showAnswer() {
        if (this.state !== StudySessionState.SHOWING_CARD) return;
        
        this.currentSide = CardSide.BACK;
        this.setState(StudySessionState.SHOWING_ANSWER);
        this.renderCurrentCard();
        
        console.log(`Showing answer for card ${this.currentIndex + 1}/${this.flashcards.length}`);
    }
    
    /**
     * Submit rating for current flashcard
     */
    async submitRating(rating) {
        if (this.state !== StudySessionState.SHOWING_ANSWER || this.isSubmittingRating) return;
        
        const currentCard = this.flashcards[this.currentIndex];
        if (!currentCard) return;
        
        this.isSubmittingRating = true;
        this.setState(StudySessionState.SUBMITTING_RATING);
        this.showRatingLoadingState(rating);
        
        try {
            const response = await fetch('/api/v1/spaced-repetition/reviews', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                credentials: 'same-origin',
                body: JSON.stringify({
                    flashcard_id: currentCard.id,
                    performance_rating: rating
                })
            });
            
            if (!response.ok) {
                if (response.status === 401) {
                    this.handleAuthError();
                    return;
                }
                if (response.status === 404) {
                    console.warn('Flashcard not found, skipping to next card');
                    this.proceedToNextCard();
                    return;
                }
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            console.log(`Rating ${rating} submitted successfully for card ${currentCard.id}`);
            
            // Proceed to next card
            this.proceedToNextCard();
            
        } catch (error) {
            console.error('Error submitting rating:', error);
            this.handleRatingError(rating);
        } finally {
            this.isSubmittingRating = false;
            this.hideRatingLoadingState();
        }
    }
    
    /**
     * Proceed to next card or complete session
     */
    proceedToNextCard() {
        this.currentIndex++;
        
        if (this.currentIndex >= this.flashcards.length) {
            // Session completed
            this.sessionCompleted = true;
            this.setState(StudySessionState.SESSION_COMPLETED);
            this.showCompletionState();
            console.log('Study session completed');
        } else {
            // Show next card
            this.currentSide = CardSide.FRONT;
            this.setState(StudySessionState.SHOWING_CARD);
            this.renderCurrentCard();
            console.log(`Showing card ${this.currentIndex + 1}/${this.flashcards.length}`);
        }
    }
    
    /**
     * Render current flashcard
     */
    renderCurrentCard() {
        const currentCard = this.flashcards[this.currentIndex];
        if (!currentCard) return;
        
        // Update progress indicator
        this.updateProgressIndicator();
        
        // Update card content
        this.updateCardContent(currentCard);
        
        // Update visibility of show answer button and rating scale
        this.updateControlsVisibility();
    }
    
    /**
     * Update progress indicator
     */
    updateProgressIndicator() {
        const progressElement = document.getElementById('progressIndicator');
        const progressBar = document.getElementById('progressBar');
        
        if (progressElement) {
            const current = this.currentIndex + 1;
            const total = this.flashcards.length;
            progressElement.textContent = `${current}/${total} fiszek`;
            
            // Update progress bar
            if (progressBar) {
                const percentage = (current / total) * 100;
                progressBar.style.width = `${percentage}%`;
            }
        }
    }
    
    /**
     * Update card content
     */
    updateCardContent(flashcard) {
        const cardElement = document.getElementById('studyCard');
        const frontContent = document.getElementById('cardContent');
        const backContent = document.getElementById('cardContentBack');
        
        if (!cardElement || !frontContent) return;
        
        // Always update both sides of the card
        frontContent.innerHTML = `
            <div class="text-center">
                <h3 class="text-lg font-semibold mb-4 text-gray-800">Pytanie:</h3>
                <div class="text-gray-700 text-base leading-relaxed">${this.escapeHtml(flashcard.front_content)}</div>
            </div>
        `;
        
        if (backContent) {
            backContent.innerHTML = `
                <div class="text-center">
                    <h3 class="text-lg font-semibold mb-4 text-gray-800">Odpowiedź:</h3>
                    <div class="text-gray-700 text-base leading-relaxed">${this.escapeHtml(flashcard.back_content)}</div>
                </div>
            `;
        }
        
        // Control flip animation
        if (this.currentSide === CardSide.FRONT) {
            cardElement.classList.remove('flipped');
        } else {
            cardElement.classList.add('flipped');
        }
    }
    
    /**
     * Update visibility of controls
     */
    updateControlsVisibility() {
        const showAnswerButton = document.getElementById('showAnswerButton');
        const ratingScale = document.getElementById('ratingScale');
        
        if (this.currentSide === CardSide.FRONT) {
            if (showAnswerButton) showAnswerButton.style.display = 'block';
            if (ratingScale) ratingScale.style.display = 'none';
        } else {
            if (showAnswerButton) showAnswerButton.style.display = 'none';
            if (ratingScale) ratingScale.style.display = 'block';
        }
    }
    
    /**
     * Setup keyboard navigation
     */
    setupKeyboardNavigation() {
        document.addEventListener('keydown', (e) => {
            // Prevent default for handled keys
            if (['Space', 'Enter', 'Digit1', 'Digit2', 'Digit3', 'Digit4', 'Digit5'].includes(e.code)) {
                e.preventDefault();
            }
            
            // Show answer with Space or Enter
            if ((e.code === 'Space' || e.code === 'Enter') && this.state === StudySessionState.SHOWING_CARD) {
                this.showAnswer();
            }
            
            // Submit rating with number keys 1-5
            if (this.state === StudySessionState.SHOWING_ANSWER && !this.isSubmittingRating) {
                const ratingMap = {
                    'Digit1': 1,
                    'Digit2': 2,
                    'Digit3': 3,
                    'Digit4': 4,
                    'Digit5': 5
                };
                
                if (ratingMap[e.code]) {
                    this.submitRating(ratingMap[e.code]);
                }
            }
        });
        
        console.log('Keyboard navigation setup completed');
    }
    
    /**
     * Set current state
     */
    setState(newState) {
        this.state = newState;
        console.log(`State changed to: ${newState}`);
    }
    
    /**
     * Show loading spinner
     */
    showLoadingSpinner(message = 'Ładowanie...') {
        const spinner = document.getElementById('loadingSpinner');
        const messageElement = document.getElementById('loadingMessage');
        
        if (spinner) spinner.style.display = 'flex';
        if (messageElement) messageElement.textContent = message;
    }
    
    /**
     * Hide loading spinner
     */
    hideLoadingSpinner() {
        const spinner = document.getElementById('loadingSpinner');
        if (spinner) spinner.style.display = 'none';
    }
    
    /**
     * Show empty state
     */
    showEmptyState() {
        const emptyState = document.getElementById('emptyState');
        const mainContent = document.getElementById('mainContent');
        
        if (emptyState) emptyState.style.display = 'block';
        if (mainContent) mainContent.style.display = 'none';
    }
    
    /**
     * Show completion state
     */
    showCompletionState() {
        const completionState = document.getElementById('completionState');
        const mainContent = document.getElementById('mainContent');
        
        if (completionState) completionState.style.display = 'block';
        if (mainContent) mainContent.style.display = 'none';
    }
    
    /**
     * Show rating loading state
     */
    showRatingLoadingState(rating) {
        const button = document.querySelector(`[data-rating="${rating}"]`);
        if (button) {
            button.disabled = true;
            button.innerHTML = '<div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>';
        }
    }
    
    /**
     * Hide rating loading state
     */
    hideRatingLoadingState() {
        const ratingButtons = document.querySelectorAll('[data-rating]');
        ratingButtons.forEach((button, index) => {
            button.disabled = false;
            button.innerHTML = index + 1;
        });
    }
    
    /**
     * Handle authentication errors
     */
    handleAuthError() {
        console.log('Authentication error detected, redirecting to login');
        window.location.href = '/login?next=' + encodeURIComponent(window.location.pathname);
    }
    
    /**
     * Handle rating submission errors
     */
    handleRatingError(rating) {
        console.error(`Error submitting rating ${rating}, allowing retry`);
        this.setState(StudySessionState.SHOWING_ANSWER);
        
        // Show error message
        this.showErrorMessage('Nie udało się zapisać oceny. Spróbuj ponownie.');
    }
    
    /**
     * Handle general errors
     */
    handleError(message) {
        this.setState(StudySessionState.ERROR);
        this.error = message;
        this.showErrorState(message);
    }
    
    /**
     * Show error state
     */
    showErrorState(message) {
        const errorState = document.getElementById('errorState');
        const errorMessage = document.getElementById('errorMessage');
        const mainContent = document.getElementById('mainContent');
        
        if (errorState) errorState.style.display = 'block';
        if (errorMessage) errorMessage.textContent = message;
        if (mainContent) mainContent.style.display = 'none';
    }
    
    /**
     * Show temporary error message
     */
    showErrorMessage(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'fixed top-4 right-4 bg-red-500 text-white px-4 py-2 rounded-md shadow-lg z-50';
        errorDiv.textContent = message;
        
        document.body.appendChild(errorDiv);
        
        setTimeout(() => {
            document.body.removeChild(errorDiv);
        }, 5000);
    }
    
    /**
     * Restart session
     */
    async restartSession() {
        this.flashcards = [];
        this.currentIndex = 0;
        this.currentSide = CardSide.FRONT;
        this.sessionCompleted = false;
        this.error = null;
        
        // Hide all states and show main content
        document.getElementById('emptyState').style.display = 'none';
        document.getElementById('completionState').style.display = 'none';
        document.getElementById('errorState').style.display = 'none';
        document.getElementById('mainContent').style.display = 'block';
        
        await this.loadDueFlashcards();
    }
    
    /**
     * Navigate to dashboard
     */
    navigateToDashboard() {
        window.location.href = '/dashboard';
    }
    
    /**
     * Setup error handling
     */
    setupErrorHandling() {
        window.addEventListener('error', (e) => {
            console.error('Study session JavaScript error:', e.error);
        });
        
        window.addEventListener('unhandledrejection', (e) => {
            console.error('Study session unhandled promise rejection:', e.reason);
        });
    }
    
    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    /**
     * Cleanup when page is unloaded
     */
    cleanup() {
        console.log('Study session cleanup completed');
    }
}

// Initialize Study Session Manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Check if we're on the study session page
    if (window.location.pathname === '/study-session') {
        window.studySessionManager = new StudySessionManager();
        
        // Cleanup on page unload
        window.addEventListener('beforeunload', () => {
            window.studySessionManager.cleanup();
        });
    }
});

// Export for testing purposes
if (typeof module !== 'undefined' && module.exports) {
    module.exports = StudySessionManager;
} 