/**
 * Generate Flashcards JavaScript Module
 * Handles form submission, validation, and UI state management
 */

class GenerateFlashcardsController {
    constructor() {
        this.textContent = '';
        this.isGenerating = false;
        this.suggestions = [];
        this.editingCard = null;
        this.toastMessage = null;
        this.errors = [];
        this.hasGeneratedResults = false;
        
        // Configuration
        this.minLength = 1000;
        this.maxLength = 10000;
        this.debounceTimeout = null;
        this.debounceDelay = 500; // ms
        
        // DOM elements
        this.textarea = null;
        this.characterCount = null;
        this.progressBar = null;
        this.counterInfo = null;
        this.generateButton = null;
        this.validationMessage = null;
        this.validationText = null;
        this.loadingSpinner = null;
        this.errorMessage = null;
        this.successMessage = null;
        this.suggestionsSection = null;
        this.flashcardSuggestionsList = null;
        
        this.init();
    }
    
    /**
     * Initialize the controller
     */
    init() {
        this.bindDOMElements();
        this.setupEventListeners();
        this.updateUI();
        
        console.log('GenerateFlashcardsController initialized');
    }
    
    /**
     * Bind DOM elements
     */
    bindDOMElements() {
        this.textarea = document.getElementById('textContent');
        this.characterCount = document.getElementById('characterCount');
        this.progressBar = document.getElementById('progressBar');
        this.counterInfo = document.getElementById('counterInfo');
        this.generateButton = document.getElementById('generateButton');
        this.validationMessage = document.getElementById('validationMessage');
        this.validationText = document.getElementById('validationText');
        this.loadingSpinner = document.getElementById('loadingSpinner');
        this.errorMessage = document.getElementById('errorMessage');
        this.successMessage = document.getElementById('successMessage');
        this.suggestionsSection = document.getElementById('suggestionsSection');
        this.flashcardSuggestionsList = document.getElementById('flashcardSuggestionsList');
    }
    
    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Textarea input with debouncing
        if (this.textarea) {
            this.textarea.addEventListener('input', (e) => {
                this.handleTextInput(e.target.value);
            });
            
            this.textarea.addEventListener('paste', (e) => {
                // Handle paste events with slight delay to get pasted content
                setTimeout(() => {
                    this.handleTextInput(this.textarea.value);
                }, 10);
            });
        }
        
        // Form submission
        const form = document.getElementById('generateForm');
        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleFormSubmit();
            });
        }
        
        // Button click
        if (this.generateButton) {
            this.generateButton.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleFormSubmit();
            });
        }
    }
    
    /**
     * Handle text input with debouncing
     */
    handleTextInput(value) {
        this.textContent = value;
        
        // Clear previous debounce timeout
        if (this.debounceTimeout) {
            clearTimeout(this.debounceTimeout);
        }
        
        // Immediate character counter update
        this.updateCharacterCounter();
        
        // Debounced validation
        this.debounceTimeout = setTimeout(() => {
            this.validateInput();
        }, this.debounceDelay);
    }
    
    /**
     * Update character counter display
     */
    updateCharacterCounter() {
        if (!this.textarea || !this.characterCount || !this.progressBar || !this.counterInfo) return;
        
        const length = this.textContent.length;
        
        // Update counter display
        this.characterCount.textContent = length;
        
        // Update progress bar
        const progress = Math.min((length / this.maxLength) * 100, 100);
        this.progressBar.style.width = progress + '%';
        
        // Update counter info and styling
        this.updateCounterInfo(length);
        this.updateProgressBarColor(length);
    }
    
    /**
     * Update counter info text and styling
     */
    updateCounterInfo(length) {
        if (!this.counterInfo) return;
        
        let message = '';
        let className = 'text-xs';
        
        if (length === 0) {
            message = 'Wprowadź tekst...';
            className += ' text-gray-400';
        } else if (length < this.minLength) {
            message = `Potrzebujesz jeszcze ${this.minLength - length} znaków`;
            className += ' counter-warning';
        } else if (length > this.maxLength) {
            message = `Przekroczono limit o ${length - this.maxLength} znaków`;
            className += ' counter-error';
        } else {
            message = 'Gotowe do generowania';
            className += ' counter-success';
        }
        
        this.counterInfo.textContent = message;
        this.counterInfo.className = className;
    }
    
    /**
     * Update progress bar color based on length
     */
    updateProgressBarColor(length) {
        if (!this.progressBar) return;
        
        let colorClass = 'bg-purple-500';
        
        if (length >= this.minLength && length <= this.maxLength) {
            colorClass = 'bg-green-500';
        } else if (length > 0) {
            colorClass = 'bg-orange-500';
        }
        
        this.progressBar.className = `${colorClass} h-1 rounded-full transition-all duration-300`;
    }
    
    /**
     * Validate input and update UI
     */
    validateInput() {
        const length = this.textContent.length;
        const trimmedText = this.textContent.trim();
        
        // Clear previous errors
        this.errors = [];
        
        // Validation checks
        if (length === 0) {
            // Empty input - no error needed
        } else if (trimmedText.length === 0) {
            this.errors.push('Tekst nie może składać się tylko z białych znaków');
        } else if (length < this.minLength) {
            this.errors.push(`Tekst musi mieć co najmniej ${this.minLength} znaków`);
        } else if (length > this.maxLength) {
            this.errors.push(`Tekst nie może przekraczać ${this.maxLength} znaków`);
            // Auto-truncate
            this.truncateText();
            return; // Early return as truncation will trigger validation again
        }
        
        // Update validation display
        this.updateValidationDisplay();
        
        // Update button state
        this.updateButtonState();
    }
    
    /**
     * Truncate text to maximum length
     */
    truncateText() {
        if (this.textarea && this.textContent.length > this.maxLength) {
            const truncated = this.textContent.substring(0, this.maxLength);
            this.textarea.value = truncated;
            this.textContent = truncated;
            
            // Show warning about truncation
            this.showToast({
                type: 'warning',
                title: 'Tekst został skrócony',
                message: `Tekst został automatycznie skrócony do ${this.maxLength} znaków`,
                duration: 5000
            });
            
            // Re-run validation
            setTimeout(() => this.validateInput(), 10);
        }
    }
    
    /**
     * Update validation display
     */
    updateValidationDisplay() {
        if (!this.validationMessage || !this.validationText) return;
        
        if (this.errors.length > 0) {
            this.validationText.textContent = this.errors[0];
            this.validationMessage.classList.remove('hidden');
        } else {
            this.validationMessage.classList.add('hidden');
        }
    }
    
    /**
     * Update button state
     */
    updateButtonState() {
        if (!this.generateButton) return;
        
        const isValid = this.errors.length === 0 && 
                        this.textContent.length >= this.minLength && 
                        this.textContent.length <= this.maxLength;
        
        this.generateButton.disabled = !isValid || this.isGenerating;
        
        // Update button text and icon
        this.updateButtonDisplay();
    }
    
    /**
     * Update button display
     */
    updateButtonDisplay() {
        const buttonText = document.getElementById('buttonText');
        const buttonIcon = document.getElementById('buttonIcon');
        
        if (!buttonText || !buttonIcon) return;
        
        if (this.isGenerating) {
            buttonText.textContent = 'Generuję fiszki...';
            buttonIcon.innerHTML = '<svg class="w-5 h-5 mr-2 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m-15.357-2A8.001 8.001 0 0019.418 15m0 0H15"></path></svg>';
        } else {
            buttonText.textContent = 'Generuj fiszki';
            buttonIcon.innerHTML = '<svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"></path></svg>';
        }
    }
    
    /**
     * Handle form submission
     */
    async handleFormSubmit() {
        if (this.isGenerating) return;
        
        // Final validation
        this.validateInput();
        if (this.errors.length > 0) {
            this.showToast({
                type: 'error',
                title: 'Błąd walidacji',
                message: this.errors[0],
                duration: 5000
            });
            return;
        }
        
        try {
            await this.generateFlashcards(this.textContent);
        } catch (error) {
            console.error('Error generating flashcards:', error);
            this.showToast({
                type: 'error',
                title: 'Błąd generowania',
                message: 'Wystąpił błąd podczas generowania fiszek. Spróbuj ponownie.',
                duration: 5000
            });
        }
    }
    
    /**
     * Generate flashcards from text
     */
    async generateFlashcards(textContent) {
        this.isGenerating = true;
        this.updateUI();
        
        // Show loading spinner
        this.showLoading();
        
        try {
            const response = await this.makeAuthenticatedRequest('/api/v1/ai/generate-flashcards', {
                method: 'POST',
                body: JSON.stringify({
                    text_content: textContent
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            // Update state
            this.suggestions = data.suggested_flashcards || [];
            this.hasGeneratedResults = true;
            
            // Show success message
            this.showToast({
                type: 'success',
                title: 'Fiszki wygenerowane!',
                message: `Pomyślnie wygenerowano ${this.suggestions.length} propozycji fiszek`,
                duration: 5000
            });
            
            // Render suggestions
            this.renderSuggestions();
            
        } catch (error) {
            console.error('Generation error:', error);
            
            // Handle specific error types
            let errorMessage = 'Wystąpił nieoczekiwany błąd';
            
            if (error.message.includes('503')) {
                errorMessage = 'AI jest tymczasowo niedostępne. Spróbuj ponownie za chwilę.';
            } else if (error.message.includes('422')) {
                errorMessage = 'Nieprawidłowe dane wejściowe. Sprawdź tekst i spróbuj ponownie.';
            } else if (error.message.includes('429')) {
                errorMessage = 'Osiągnąłeś limit generowań. Spróbuj ponownie za godzinę.';
            } else if (error.message.includes('401')) {
                errorMessage = 'Sesja wygasła. Zaloguj się ponownie.';
                // Redirect to login after delay
                setTimeout(() => {
                    window.location.href = '/login';
                }, 3000);
            }
            
            this.showToast({
                type: 'error',
                title: 'Błąd generowania',
                message: errorMessage,
                duration: 8000
            });
        } finally {
            this.isGenerating = false;
            this.hideLoading();
            this.updateUI();
        }
    }
    
    /**
     * Make authenticated API request with retry logic
     */
    async makeAuthenticatedRequest(url, options = {}) {
        const defaultOptions = {
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                ...options.headers
            }
        };
        
        const finalOptions = { ...defaultOptions, ...options };
        
        // Retry logic
        const maxRetries = 3;
        let lastError;
        
        for (let i = 0; i < maxRetries; i++) {
            try {
                const response = await fetch(url, finalOptions);
                
                // Check if we need to refresh auth
                if (response.status === 401 && i < maxRetries - 1) {
                    // Wait a bit before retry
                    await new Promise(resolve => setTimeout(resolve, 1000));
                    continue;
                }
                
                return response;
            } catch (error) {
                lastError = error;
                if (i < maxRetries - 1) {
                    // Exponential backoff
                    await new Promise(resolve => setTimeout(resolve, Math.pow(2, i) * 1000));
                }
            }
        }
        
        throw lastError || new Error('Request failed after retries');
    }
    
    /**
     * Show loading spinner
     */
    showLoading() {
        if (this.loadingSpinner) {
            this.loadingSpinner.classList.remove('hidden');
        }
        
        // Hide form during loading
        const textInputSection = document.getElementById('textInputSection');
        if (textInputSection) {
            textInputSection.style.opacity = '0.5';
            textInputSection.style.pointerEvents = 'none';
        }
        
        // Show skeleton loading for suggestions
        this.showSkeletonLoading();
    }
    
    /**
     * Show skeleton loading cards
     */
    showSkeletonLoading() {
        if (!this.flashcardSuggestionsList || !this.suggestionsSection) return;
        
        // Clear existing content
        this.flashcardSuggestionsList.innerHTML = '';
        
        // Show suggestions section
        this.suggestionsSection.classList.remove('hidden');
        
        // Add skeleton cards
        for (let i = 0; i < 3; i++) {
            const skeleton = this.createSkeletonCard();
            this.flashcardSuggestionsList.appendChild(skeleton);
        }
    }
    
    /**
     * Create skeleton loading card
     */
    createSkeletonCard() {
        const div = document.createElement('div');
        div.className = 'bg-gray-50 border border-gray-200 rounded-lg p-4 animate-pulse';
        div.innerHTML = `
            <div class="flex justify-between items-start mb-3">
                <div class="h-4 bg-gray-300 rounded w-20"></div>
                <div class="flex space-x-2">
                    <div class="h-8 bg-gray-300 rounded w-16"></div>
                    <div class="h-8 bg-gray-300 rounded w-20"></div>
                    <div class="h-8 bg-gray-300 rounded w-16"></div>
                </div>
            </div>
            <div class="space-y-3">
                <div>
                    <div class="h-3 bg-gray-300 rounded w-16 mb-2"></div>
                    <div class="h-10 bg-gray-200 rounded"></div>
                </div>
                <div>
                    <div class="h-3 bg-gray-300 rounded w-16 mb-2"></div>
                    <div class="h-10 bg-gray-200 rounded"></div>
                </div>
            </div>
        `;
        return div;
    }
    
    /**
     * Hide loading spinner
     */
    hideLoading() {
        if (this.loadingSpinner) {
            this.loadingSpinner.classList.add('hidden');
        }
        
        // Restore form
        const textInputSection = document.getElementById('textInputSection');
        if (textInputSection) {
            textInputSection.style.opacity = '1';
            textInputSection.style.pointerEvents = 'auto';
        }
    }
    
    /**
     * Render flashcard suggestions
     */
    renderSuggestions() {
        if (!this.flashcardSuggestionsList || !this.suggestionsSection) return;
        
        // Clear existing suggestions
        this.flashcardSuggestionsList.innerHTML = '';
        
        if (this.suggestions.length === 0) {
            this.renderEmptyState();
            return;
        }
        
        // Update the section header with count and batch actions
        this.updateSuggestionsHeader();
        
        // Render each suggestion with staggered animation
        this.suggestions.forEach((suggestion, index) => {
            const suggestionElement = this.createSuggestionElement(suggestion, index);
            // Add animation delay
            suggestionElement.style.animationDelay = `${index * 100}ms`;
            suggestionElement.classList.add('animate-fadeIn');
            this.flashcardSuggestionsList.appendChild(suggestionElement);
        });
        
        // Show suggestions section
        this.suggestionsSection.classList.remove('hidden');
        
        // Scroll to suggestions
        setTimeout(() => {
            this.suggestionsSection.scrollIntoView({ 
                behavior: 'smooth',
                block: 'start'
            });
        }, 300);
    }
    
    /**
     * Update suggestions header with count and actions
     */
    updateSuggestionsHeader() {
        const suggestionsSection = document.getElementById('suggestionsSection');
        if (!suggestionsSection) return;
        
        const headerHTML = `
            <div class="bg-white shadow-lg rounded-xl p-6">
                <div class="flex justify-between items-center mb-6">
                    <h2 class="text-xl font-semibold text-gray-900">Propozycje fiszek</h2>
                    <div class="flex items-center space-x-4">
                        <span class="text-sm text-gray-500">${this.suggestions.length} propozycji</span>
                        <div class="flex space-x-2">
                            <button onclick="acceptAllSuggestions()" 
                                    class="text-green-600 hover:text-green-800 text-sm px-3 py-1 rounded border border-green-300 hover:bg-green-50 transition-colors focus:outline-none focus:ring-2 focus:ring-green-300">
                                Akceptuj wszystkie
                            </button>
                            <button onclick="rejectAllSuggestions()" 
                                    class="text-red-600 hover:text-red-800 text-sm px-3 py-1 rounded border border-red-300 hover:bg-red-50 transition-colors focus:outline-none focus:ring-2 focus:ring-red-300">
                                Odrzuć wszystkie
                            </button>
                        </div>
                    </div>
                </div>
                <div id="flashcardSuggestionsList" class="space-y-4"></div>
            </div>
        `;
        
        suggestionsSection.innerHTML = headerHTML;
        
        // Re-bind the suggestions list element
        this.flashcardSuggestionsList = document.getElementById('flashcardSuggestionsList');
    }
    
    /**
     * Create suggestion element
     */
    createSuggestionElement(suggestion, index) {
        const div = document.createElement('div');
        div.className = 'bg-gray-50 border border-gray-200 rounded-lg p-4 hover:shadow-md transition-all duration-300';
        div.setAttribute('data-suggestion-id', suggestion.id);
        div.innerHTML = `
            <div class="flex justify-between items-start mb-3">
                <h3 class="text-sm font-medium text-gray-900">Fiszka ${index + 1}</h3>
                <div class="flex space-x-2">
                    <button onclick="editSuggestion('${suggestion.id}')" 
                            class="text-blue-600 hover:text-blue-800 text-sm px-2 py-1 rounded hover:bg-blue-50 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-300">
                        Edytuj
                    </button>
                    <button onclick="acceptSuggestion('${suggestion.id}')" 
                            class="text-green-600 hover:text-green-800 text-sm px-2 py-1 rounded hover:bg-green-50 transition-colors focus:outline-none focus:ring-2 focus:ring-green-300">
                        Akceptuj
                    </button>
                    <button onclick="rejectSuggestion('${suggestion.id}')" 
                            class="text-red-600 hover:text-red-800 text-sm px-2 py-1 rounded hover:bg-red-50 transition-colors focus:outline-none focus:ring-2 focus:ring-red-300">
                        Odrzuć
                    </button>
                </div>
            </div>
            <div class="space-y-3">
                <div>
                    <label class="block text-xs font-medium text-gray-700 mb-1">Przód:</label>
                    <div class="front-content text-sm text-gray-900 bg-white p-2 rounded border">${this.escapeHtml(suggestion.front_content)}</div>
                </div>
                <div>
                    <label class="block text-xs font-medium text-gray-700 mb-1">Tył:</label>
                    <div class="back-content text-sm text-gray-900 bg-white p-2 rounded border">${this.escapeHtml(suggestion.back_content)}</div>
                </div>
            </div>
        `;
        return div;
    }
    
    /**
     * Render empty state
     */
    renderEmptyState() {
        this.flashcardSuggestionsList.innerHTML = `
            <div class="text-center py-8">
                <div class="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                    </svg>
                </div>
                <h3 class="text-lg font-medium text-gray-900 mb-2">Brak propozycji</h3>
                <p class="text-gray-600">AI nie wygenerowało żadnych propozycji fiszek z tego tekstu. Spróbuj z innym materiałem.</p>
            </div>
        `;
        this.suggestionsSection.classList.remove('hidden');
    }
    
    /**
     * Show toast notification
     */
    showToast(toast) {
        console.log(`Toast [${toast.type}]: ${toast.title} - ${toast.message}`);
        
        // Use the HTML toast elements for better UX
        if (toast.type === 'success') {
            this.showSuccessMessage(toast.message);
        } else if (toast.type === 'error') {
            this.showErrorMessage(toast.message);
        } else if (toast.type === 'warning') {
            this.showErrorMessage(toast.message); // Use error styling for warnings
        }
    }
    
    /**
     * Show success message
     */
    showSuccessMessage(message) {
        const successMessage = document.getElementById('successMessage');
        const successText = document.getElementById('successText');
        
        if (successMessage && successText) {
            successText.textContent = message;
            successMessage.classList.remove('hidden');
            
            // Auto-hide after 5 seconds
            setTimeout(() => {
                successMessage.classList.add('hidden');
            }, 5000);
        }
    }
    
    /**
     * Show error message
     */
    showErrorMessage(message) {
        const errorMessage = document.getElementById('errorMessage');
        const errorText = document.getElementById('errorText');
        
        if (errorMessage && errorText) {
            errorText.textContent = message;
            errorMessage.classList.remove('hidden');
        }
    }
    
    /**
     * Update UI based on current state
     */
    updateUI() {
        this.updateCharacterCounter();
        this.updateButtonState();
        this.updateValidationDisplay();
    }
    
    /**
     * Escape HTML for safe rendering
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    /**
     * Accept suggestion and convert to active flashcard
     */
    async acceptSuggestion(suggestionId) {
        const suggestion = this.suggestions.find(s => s.id === suggestionId);
        if (!suggestion) {
            console.error('Suggestion not found:', suggestionId);
            return;
        }
        
        try {
            // Optimistic update
            this.markSuggestionAsProcessing(suggestionId, true);
            
            const response = await this.makeAuthenticatedRequest(`/api/v1/flashcards/${suggestionId}`, {
                method: 'PATCH',
                body: JSON.stringify({
                    status: 'active'
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            // Remove suggestion from list
            this.removeSuggestionFromUI(suggestionId);
            
            this.showToast({
                type: 'success',
                title: 'Fiszka zaakceptowana',
                message: 'Fiszka została dodana do Twojej kolekcji',
                duration: 3000
            });
            
        } catch (error) {
            console.error('Error accepting suggestion:', error);
            
            // Rollback optimistic update
            this.markSuggestionAsProcessing(suggestionId, false);
            
            this.showToast({
                type: 'error',
                title: 'Błąd akceptacji',
                message: 'Nie udało się zaakceptować fiszki. Spróbuj ponownie.',
                duration: 5000
            });
        }
    }
    
    /**
     * Reject suggestion
     */
    async rejectSuggestion(suggestionId) {
        const suggestion = this.suggestions.find(s => s.id === suggestionId);
        if (!suggestion) {
            console.error('Suggestion not found:', suggestionId);
            return;
        }
        
        try {
            // Optimistic update
            this.markSuggestionAsProcessing(suggestionId, true);
            
            const response = await this.makeAuthenticatedRequest(`/api/v1/flashcards/${suggestionId}`, {
                method: 'PATCH',
                body: JSON.stringify({
                    status: 'rejected'
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            // Remove suggestion from list
            this.removeSuggestionFromUI(suggestionId);
            
            this.showToast({
                type: 'success',
                title: 'Fiszka odrzucona',
                message: 'Propozycja fiszki została odrzucona',
                duration: 3000
            });
            
        } catch (error) {
            console.error('Error rejecting suggestion:', error);
            
            // Rollback optimistic update
            this.markSuggestionAsProcessing(suggestionId, false);
            
            this.showToast({
                type: 'error',
                title: 'Błąd odrzucenia',
                message: 'Nie udało się odrzucić fiszki. Spróbuj ponownie.',
                duration: 5000
            });
        }
    }
    
    /**
     * Edit suggestion (opens modal or inline edit)
     */
    editSuggestion(suggestionId) {
        const suggestion = this.suggestions.find(s => s.id === suggestionId);
        if (!suggestion) {
            console.error('Suggestion not found:', suggestionId);
            return;
        }
        
        // For now, use a simple prompt-based edit
        // In a full implementation, this would open a modal
        const newFrontContent = prompt('Edytuj przód fiszki:', suggestion.front_content);
        if (newFrontContent === null) return; // User cancelled
        
        const newBackContent = prompt('Edytuj tył fiszki:', suggestion.back_content);
        if (newBackContent === null) return; // User cancelled
        
        // Validate input
        if (newFrontContent.trim().length === 0 || newBackContent.trim().length === 0) {
            this.showToast({
                type: 'error',
                title: 'Błąd walidacji',
                message: 'Przód i tył fiszki nie mogą być puste',
                duration: 5000
            });
            return;
        }
        
        if (newFrontContent.length > 500 || newBackContent.length > 1000) {
            this.showToast({
                type: 'error',
                title: 'Błąd walidacji',
                message: 'Przód fiszki może mieć max 500 znaków, tył max 1000 znaków',
                duration: 5000
            });
            return;
        }
        
        this.saveEditedSuggestion(suggestionId, newFrontContent.trim(), newBackContent.trim());
    }
    
    /**
     * Save edited suggestion
     */
    async saveEditedSuggestion(suggestionId, frontContent, backContent) {
        try {
            // Optimistic update
            this.updateSuggestionInUI(suggestionId, frontContent, backContent);
            
            const response = await this.makeAuthenticatedRequest(`/api/v1/flashcards/${suggestionId}`, {
                method: 'PATCH',
                body: JSON.stringify({
                    front_content: frontContent,
                    back_content: backContent
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const updatedSuggestion = await response.json();
            
            // Update local state with server response
            const suggestionIndex = this.suggestions.findIndex(s => s.id === suggestionId);
            if (suggestionIndex !== -1) {
                this.suggestions[suggestionIndex] = updatedSuggestion;
            }
            
            this.showToast({
                type: 'success',
                title: 'Fiszka zaktualizowana',
                message: 'Zmiany zostały zapisane',
                duration: 3000
            });
            
        } catch (error) {
            console.error('Error saving edited suggestion:', error);
            
            // Rollback optimistic update
            this.renderSuggestions();
            
            this.showToast({
                type: 'error',
                title: 'Błąd zapisywania',
                message: 'Nie udało się zapisać zmian. Spróbuj ponownie.',
                duration: 5000
            });
        }
    }
    
    /**
     * Mark suggestion as processing (show loading state)
     */
    markSuggestionAsProcessing(suggestionId, isProcessing) {
        const suggestionElement = document.querySelector(`[data-suggestion-id="${suggestionId}"]`);
        if (suggestionElement) {
            const buttons = suggestionElement.querySelectorAll('button');
            buttons.forEach(button => {
                button.disabled = isProcessing;
                if (isProcessing) {
                    button.style.opacity = '0.5';
                } else {
                    button.style.opacity = '1';
                }
            });
        }
    }
    
    /**
     * Remove suggestion from UI
     */
    removeSuggestionFromUI(suggestionId) {
        // Remove from local state
        this.suggestions = this.suggestions.filter(s => s.id !== suggestionId);
        
        // Remove from DOM
        const suggestionElement = document.querySelector(`[data-suggestion-id="${suggestionId}"]`);
        if (suggestionElement) {
            suggestionElement.style.opacity = '0';
            suggestionElement.style.transform = 'translateX(-100%)';
            setTimeout(() => {
                suggestionElement.remove();
                
                // Check if all suggestions are gone
                if (this.suggestions.length === 0) {
                    this.renderEmptyState();
                }
            }, 300);
        }
    }
    
    /**
     * Update suggestion in UI (optimistic update)
     */
    updateSuggestionInUI(suggestionId, frontContent, backContent) {
        // Update local state
        const suggestionIndex = this.suggestions.findIndex(s => s.id === suggestionId);
        if (suggestionIndex !== -1) {
            this.suggestions[suggestionIndex].front_content = frontContent;
            this.suggestions[suggestionIndex].back_content = backContent;
        }
        
        // Update DOM
        const suggestionElement = document.querySelector(`[data-suggestion-id="${suggestionId}"]`);
        if (suggestionElement) {
            const frontDiv = suggestionElement.querySelector('.front-content');
            const backDiv = suggestionElement.querySelector('.back-content');
            
            if (frontDiv) frontDiv.textContent = frontContent;
            if (backDiv) backDiv.textContent = backContent;
        }
    }
    
    /**
     * Accept all suggestions at once
     */
    async acceptAllSuggestions() {
        if (this.suggestions.length === 0) return;
        
        const confirmMessage = `Czy na pewno chcesz zaakceptować wszystkie ${this.suggestions.length} propozycje fiszek?`;
        if (!confirm(confirmMessage)) return;
        
        // Mark all as processing
        this.suggestions.forEach(s => this.markSuggestionAsProcessing(s.id, true));
        
        const results = await Promise.allSettled(
            this.suggestions.map(suggestion => 
                this.acceptSuggestion(suggestion.id).catch(err => ({ error: err }))
            )
        );
        
        // Count successes
        const successCount = results.filter(r => r.status === 'fulfilled').length;
        const failedCount = results.filter(r => r.status === 'rejected').length;
        
        if (successCount > 0) {
            this.showToast({
                type: 'success',
                title: 'Operacja zakończona',
                message: `Zaakceptowano ${successCount} fiszek${failedCount > 0 ? `, ${failedCount} błędów` : ''}`,
                duration: 5000
            });
        } else {
            this.showToast({
                type: 'error',
                title: 'Błąd operacji',
                message: 'Nie udało się zaakceptować żadnej fiszki',
                duration: 5000
            });
        }
    }
    
    /**
     * Reject all suggestions at once
     */
    async rejectAllSuggestions() {
        if (this.suggestions.length === 0) return;
        
        const confirmMessage = `Czy na pewno chcesz odrzucić wszystkie ${this.suggestions.length} propozycje fiszek?`;
        if (!confirm(confirmMessage)) return;
        
        // Mark all as processing
        this.suggestions.forEach(s => this.markSuggestionAsProcessing(s.id, true));
        
        const results = await Promise.allSettled(
            this.suggestions.map(suggestion => 
                this.rejectSuggestion(suggestion.id).catch(err => ({ error: err }))
            )
        );
        
        // Count successes
        const successCount = results.filter(r => r.status === 'fulfilled').length;
        const failedCount = results.filter(r => r.status === 'rejected').length;
        
        if (successCount > 0) {
            this.showToast({
                type: 'success',
                title: 'Operacja zakończona',
                message: `Odrzucono ${successCount} fiszek${failedCount > 0 ? `, ${failedCount} błędów` : ''}`,
                duration: 5000
            });
        } else {
            this.showToast({
                type: 'error',
                title: 'Błąd operacji',
                message: 'Nie udało się odrzucić żadnej fiszki',
                duration: 5000
            });
        }
    }
    
    /**
     * Reset form to initial state
     */
    reset() {
        this.textContent = '';
        this.isGenerating = false;
        this.suggestions = [];
        this.editingCard = null;
        this.errors = [];
        this.hasGeneratedResults = false;
        
        if (this.textarea) {
            this.textarea.value = '';
        }
        
        if (this.suggestionsSection) {
            this.suggestionsSection.classList.add('hidden');
        }
        
        this.updateUI();
    }
}

// Global controller instance
let generateFlashcardsController = null;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    generateFlashcardsController = new GenerateFlashcardsController();
});

// Global functions for suggestion actions (called from HTML)
function acceptSuggestion(suggestionId) {
    if (generateFlashcardsController) {
        generateFlashcardsController.acceptSuggestion(suggestionId);
    }
}

function rejectSuggestion(suggestionId) {
    if (generateFlashcardsController) {
        generateFlashcardsController.rejectSuggestion(suggestionId);
    }
}

function editSuggestion(suggestionId) {
    if (generateFlashcardsController) {
        generateFlashcardsController.editSuggestion(suggestionId);
    }
}

// Override the handleFormSubmit function from the inline script
window.handleFormSubmit = function() {
    if (generateFlashcardsController) {
        generateFlashcardsController.handleFormSubmit();
    }
};

// Global functions for batch operations
function acceptAllSuggestions() {
    if (generateFlashcardsController) {
        generateFlashcardsController.acceptAllSuggestions();
    }
}

function rejectAllSuggestions() {
    if (generateFlashcardsController) {
        generateFlashcardsController.rejectAllSuggestions();
    }
} 