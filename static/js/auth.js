// Auth State Management
class AuthManager {
    constructor() {
        this.currentMode = 'login';
        this.isLoading = false;
        this.supabaseClient = null;
        this.validationErrors = {};
        
        this.init();
    }
    
    async init() {
        // Initialize Supabase client
        // Note: These should be loaded from environment or config
        const SUPABASE_URL = 'YOUR_SUPABASE_URL'; // TODO: Replace with actual config
        const SUPABASE_ANON_KEY = 'YOUR_SUPABASE_ANON_KEY'; // TODO: Replace with actual config
        
        // this.supabaseClient = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
        
        this.setupEventListeners();
        this.detectCurrentMode();
        
        // Check if user is already authenticated
        await this.checkAuthState();
    }
    
    setupEventListeners() {
        // Auth toggle buttons
        const toggleButtons = document.querySelectorAll('#authToggle button');
        toggleButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const mode = e.target.dataset.mode;
                this.switchMode(mode);
            });
        });
        
        // Form submission
        const form = document.getElementById('authForm');
        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleFormSubmit();
            });
        }
        
        // Password toggle
        const togglePassword = document.getElementById('togglePassword');
        if (togglePassword) {
            togglePassword.addEventListener('click', this.togglePasswordVisibility);
        }
        
        // Forgot password
        const forgotPasswordBtn = document.getElementById('forgotPasswordBtn');
        const forgotPasswordModal = document.getElementById('forgotPasswordModal');
        const cancelForgotPassword = document.getElementById('cancelForgotPassword');
        const forgotPasswordForm = document.getElementById('forgotPasswordForm');
        
        if (forgotPasswordBtn) {
            forgotPasswordBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.showForgotPasswordModal();
            });
        }
        
        if (cancelForgotPassword) {
            cancelForgotPassword.addEventListener('click', () => {
                this.hideForgotPasswordModal();
            });
        }
        
        if (forgotPasswordModal) {
            forgotPasswordModal.addEventListener('click', (e) => {
                if (e.target === forgotPasswordModal) {
                    this.hideForgotPasswordModal();
                }
            });
        }
        
        // Real-time validation
        const emailField = document.getElementById('email');
        const passwordField = document.getElementById('password');
        const confirmPasswordField = document.getElementById('confirmPassword');
        
        if (emailField) {
            emailField.addEventListener('blur', () => this.validateEmail());
            emailField.addEventListener('input', () => this.clearFieldError('email'));
        }
        
        if (passwordField) {
            passwordField.addEventListener('blur', () => this.validatePassword());
            passwordField.addEventListener('input', () => this.clearFieldError('password'));
        }
        
        if (confirmPasswordField) {
            confirmPasswordField.addEventListener('blur', () => this.validateConfirmPassword());
            confirmPasswordField.addEventListener('input', () => this.clearFieldError('confirmPassword'));
        }
    }
    
    detectCurrentMode() {
        // Detect mode from URL or template context
        const url = window.location.pathname;
        if (url.includes('/register')) {
            this.currentMode = 'register';
        } else {
            this.currentMode = 'login';
        }
    }
    
    switchMode(newMode) {
        if (this.currentMode === newMode) return;
        
        this.currentMode = newMode;
        this.clearAllErrors();
        
        // Update URL without reload
        const newUrl = `/${newMode}`;
        window.history.pushState({ mode: newMode }, '', newUrl);
        
        // Update UI
        this.updateModeUI();
        
        // Reset form
        this.resetForm();
        
        // Manage focus for accessibility
        this.manageFocus();
    }
    
    updateModeUI() {
        // Update toggle buttons
        const toggleButtons = document.querySelectorAll('#authToggle button');
        toggleButtons.forEach(button => {
            const buttonMode = button.dataset.mode;
            if (buttonMode === this.currentMode) {
                button.className = "flex-1 py-2 px-4 rounded-md text-sm font-medium auth-transition bg-white text-gray-900 shadow-sm";
            } else {
                button.className = "flex-1 py-2 px-4 rounded-md text-sm font-medium auth-transition text-gray-500 hover:text-gray-700";
            }
        });
        
        // Update form action
        const form = document.getElementById('authForm');
        if (form) {
            form.action = `/${this.currentMode}`;
        }
        
        // Show/hide confirm password field
        const confirmPasswordField = document.getElementById('confirmPasswordField');
        const confirmPasswordInput = document.getElementById('confirmPassword');
        const forgotPasswordLink = document.getElementById('forgotPasswordLink');
        
        if (this.currentMode === 'register') {
            confirmPasswordField.classList.remove('hidden');
            confirmPasswordInput.required = true;
            if (forgotPasswordLink) forgotPasswordLink.classList.add('hidden');
        } else {
            confirmPasswordField.classList.add('hidden');
            confirmPasswordInput.required = false;
            if (forgotPasswordLink) forgotPasswordLink.classList.remove('hidden');
        }
        
        // Update submit button text
        const submitText = document.getElementById('submitText');
        if (submitText) {
            submitText.textContent = this.currentMode === 'login' ? 'Zaloguj się' : 'Zarejestruj się';
        }
        
        // Update page title
        document.title = `${this.currentMode === 'login' ? 'Zaloguj się' : 'Zarejestruj się'} - 10x Cards`;
    }
    
    resetForm() {
        const form = document.getElementById('authForm');
        if (form) {
            form.reset();
        }
        this.clearAllErrors();
    }
    
    // Validation Methods
    validateEmail() {
        const emailField = document.getElementById('email');
        const email = emailField.value.trim();
        
        if (!email) {
            this.setFieldError('email', 'Adres email jest wymagany');
            return false;
        }
        
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            this.setFieldError('email', 'Wprowadź prawidłowy adres email');
            return false;
        }
        
        if (email.length > 254) {
            this.setFieldError('email', 'Adres email jest za długi (max 254 znaków)');
            return false;
        }
        
        this.clearFieldError('email');
        return true;
    }
    
    validatePassword() {
        const passwordField = document.getElementById('password');
        const password = passwordField.value;
        
        if (!password) {
            this.setFieldError('password', 'Hasło jest wymagane');
            return false;
        }
        
        if (password.length < 6) {
            this.setFieldError('password', 'Hasło musi mieć co najmniej 6 znaków');
            return false;
        }
        
        if (password.length > 128) {
            this.setFieldError('password', 'Hasło jest za długie (max 128 znaków)');
            return false;
        }
        
        this.clearFieldError('password');
        return true;
    }
    
    validateConfirmPassword() {
        if (this.currentMode !== 'register') return true;
        
        const passwordField = document.getElementById('password');
        const confirmPasswordField = document.getElementById('confirmPassword');
        
        const password = passwordField.value;
        const confirmPassword = confirmPasswordField.value;
        
        if (!confirmPassword) {
            this.setFieldError('confirmPassword', 'Potwierdzenie hasła jest wymagane');
            return false;
        }
        
        if (password !== confirmPassword) {
            this.setFieldError('confirmPassword', 'Hasła nie są identyczne');
            return false;
        }
        
        this.clearFieldError('confirmPassword');
        return true;
    }
    
    validateForm() {
        let isValid = true;
        
        if (!this.validateEmail()) isValid = false;
        if (!this.validatePassword()) isValid = false;
        if (this.currentMode === 'register' && !this.validateConfirmPassword()) isValid = false;
        
        return isValid;
    }
    
    // Error handling
    setFieldError(fieldName, message) {
        this.validationErrors[fieldName] = message;
        
        const errorElement = document.getElementById(`${fieldName}Error`);
        const fieldElement = document.getElementById(fieldName);
        
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.classList.remove('hidden');
        }
        
        if (fieldElement) {
            fieldElement.classList.add('border-red-500');
            fieldElement.classList.remove('border-gray-300');
        }
    }
    
    clearFieldError(fieldName) {
        delete this.validationErrors[fieldName];
        
        const errorElement = document.getElementById(`${fieldName}Error`);
        const fieldElement = document.getElementById(fieldName);
        
        if (errorElement) {
            errorElement.classList.add('hidden');
        }
        
        if (fieldElement) {
            fieldElement.classList.remove('border-red-500');
            fieldElement.classList.add('border-gray-300');
        }
    }
    
    clearAllErrors() {
        this.validationErrors = {};
        
        const errorElements = document.querySelectorAll('[id$="Error"]');
        errorElements.forEach(element => {
            element.classList.add('hidden');
        });
        
        const fieldElements = document.querySelectorAll('input[type="email"], input[type="password"]');
        fieldElements.forEach(element => {
            element.classList.remove('border-red-500');
            element.classList.add('border-gray-300');
        });
    }
    
    showGeneralError(message) {
        // Create error display if it doesn't exist
        let errorDisplay = document.getElementById('errorDisplay');
        if (!errorDisplay) {
            const form = document.getElementById('authForm');
            const errorHTML = `
                <div class="bg-red-50 border border-red-200 rounded-md p-4 mb-4" id="errorDisplay">
                    <div class="flex items-center">
                        <svg class="h-5 w-5 text-red-400 mr-3" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
                        </svg>
                        <span class="text-red-800 text-sm" id="errorMessage">${message}</span>
                        <button type="button" class="ml-auto text-red-400 hover:text-red-600" onclick="document.getElementById('errorDisplay').style.display='none'">
                            <svg class="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
                            </svg>
                        </button>
                    </div>
                </div>
            `;
            if (form && form.parentNode) {
                form.parentNode.insertBefore(document.createElement('div'), form);
                form.previousSibling.innerHTML = errorHTML;
                errorDisplay = document.getElementById('errorDisplay');
            }
        } else {
            const errorMessage = document.getElementById('errorMessage');
            if (errorMessage) {
                errorMessage.textContent = message;
            }
            errorDisplay.style.display = 'block';
        }
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            if (errorDisplay) {
                errorDisplay.style.display = 'none';
            }
        }, 5000);
    }

    showGeneralSuccess(message) {
        // Hide error display if visible
        const errorDisplay = document.getElementById('errorDisplay');
        if (errorDisplay) {
            errorDisplay.style.display = 'none';
        }
        
        // Create success display if it doesn't exist
        let successDisplay = document.getElementById('successDisplay');
        if (!successDisplay) {
            const form = document.getElementById('authForm');
            const successHTML = `
                <div class="bg-green-50 border border-green-200 rounded-md p-4 mb-4 fade-in" id="successDisplay">
                    <div class="flex items-center">
                        <svg class="h-5 w-5 text-green-400 mr-3" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                        </svg>
                        <span class="text-green-800 text-sm" id="successMessage">${message}</span>
                        <button type="button" class="ml-auto text-green-400 hover:text-green-600" onclick="document.getElementById('successDisplay').style.display='none'">
                            <svg class="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
                            </svg>
                        </button>
                    </div>
                </div>
            `;
            if (form && form.parentNode) {
                form.parentNode.insertBefore(document.createElement('div'), form);
                form.previousSibling.innerHTML = successHTML;
                successDisplay = document.getElementById('successDisplay');
            }
        } else {
            const successMessage = document.getElementById('successMessage');
            if (successMessage) {
                successMessage.textContent = message;
            }
            successDisplay.style.display = 'block';
        }
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            if (successDisplay) {
                successDisplay.style.display = 'none';
            }
        }, 5000);
    }
    
    // UI State Management
    setLoadingState(loading) {
        this.isLoading = loading;
        
        const submitButton = document.getElementById('submitButton');
        const submitText = document.getElementById('submitText');
        const submitSpinner = document.getElementById('submitSpinner');
        const loadingOverlay = document.getElementById('loadingOverlay');
        const formInputs = document.querySelectorAll('#authForm input, #authForm button');
        
        if (loading) {
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.setAttribute('aria-busy', 'true');
            }
            if (submitSpinner) submitSpinner.classList.remove('hidden');
            if (loadingOverlay) {
                loadingOverlay.classList.remove('hidden');
                loadingOverlay.classList.add('flex');
            }
            
            // Disable all form inputs during loading
            formInputs.forEach(input => {
                if (input.id !== 'submitButton') {
                    input.disabled = true;
                    input.setAttribute('aria-busy', 'true');
                }
            });
        } else {
            if (submitButton) {
                submitButton.disabled = false;
                submitButton.removeAttribute('aria-busy');
            }
            if (submitSpinner) submitSpinner.classList.add('hidden');
            if (loadingOverlay) {
                loadingOverlay.classList.add('hidden');
                loadingOverlay.classList.remove('flex');
            }
            
            // Re-enable all form inputs
            formInputs.forEach(input => {
                input.disabled = false;
                input.removeAttribute('aria-busy');
            });
        }
    }
    
    // Focus Management
    manageFocus() {
        // Focus first input field when switching modes
        setTimeout(() => {
            const emailField = document.getElementById('email');
            if (emailField) {
                emailField.focus();
            }
        }, 100);
    }
    
    // Enhanced Error Display with Animation
    showFieldErrorWithAnimation(fieldName, message) {
        this.setFieldError(fieldName, message);
        
        const errorElement = document.getElementById(`${fieldName}Error`);
        const fieldElement = document.getElementById(fieldName);
        
        if (errorElement) {
            // Add animation class
            errorElement.classList.add('animate-shake');
            setTimeout(() => {
                errorElement.classList.remove('animate-shake');
            }, 500);
        }
        
        if (fieldElement) {
            // Add shake animation to field
            fieldElement.classList.add('animate-shake');
            setTimeout(() => {
                fieldElement.classList.remove('animate-shake');
            }, 500);
        }
    }
    
    // Authentication Methods
    async handleFormSubmit() {
        if (this.isLoading) return;
        
        // Clear previous errors
        this.clearAllErrors();
        
        // Validate form
        if (!this.validateForm()) {
            return;
        }
        
        // Get form data
        const formData = this.getFormData();
        
        try {
            this.setLoadingState(true);
            
            if (this.currentMode === 'login') {
                await this.handleLogin(formData);
            } else {
                await this.handleRegister(formData);
            }
            
        } catch (error) {
            console.error('Auth error:', error);
            this.handleAuthError(error);
        } finally {
            this.setLoadingState(false);
        }
    }
    
    getFormData() {
        const emailField = document.getElementById('email');
        const passwordField = document.getElementById('password');
        const confirmPasswordField = document.getElementById('confirmPassword');
        
        return {
            email: emailField.value.trim(),
            password: passwordField.value,
            confirmPassword: confirmPasswordField ? confirmPasswordField.value : null
        };
    }
    
    async handleLogin(formData) {
        try {
            console.log('Login attempt:', { email: formData.email });
            
            // Create form data
            const formDataToSend = new FormData();
            formDataToSend.append('email', formData.email);
            formDataToSend.append('password', formData.password);
            
            // Send POST request to backend
            const response = await fetch('/login', {
                method: 'POST',
                body: formDataToSend,
                credentials: 'include' // Include cookies
            });
            
            // Check if response is a redirect
            if (response.redirected) {
                // Backend sent a redirect, follow it
                window.location.href = response.url;
                return;
            }
            
            // If response is not redirect, it might be an error
            if (!response.ok) {
                // Try to parse error from response
                const responseText = await response.text();
                
                // Check if response contains error message
                if (responseText.includes('error_message')) {
                    // Parse HTML to extract error message
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(responseText, 'text/html');
                    const errorElement = doc.querySelector('[id*="error"]');
                    
                    if (errorElement) {
                        throw new Error(errorElement.textContent.trim());
                    }
                }
                
                throw new Error('Nieprawidłowe dane logowania');
            }
            
            // If we get here, something unexpected happened
            const responseText = await response.text();
            if (responseText.includes('dashboard') || responseText.includes('Dashboard')) {
                // Probably successful login but no redirect
                window.location.href = '/dashboard';
            } else {
                throw new Error('Nieoczekiwana odpowiedź serwera');
            }
            
        } catch (error) {
            console.error('Login error:', error);
            
            // Show error to user
            if (error.message.includes('fetch')) {
                this.showGeneralError('Błąd połączenia z serwerem. Sprawdź połączenie internetowe.');
            } else {
                this.showGeneralError(error.message || 'Wystąpił błąd podczas logowania');
            }
            
            throw error;
        }
    }
    
    async handleRegister(formData) {
        try {
            console.log('Register attempt:', { email: formData.email });
            
            // Create form data
            const formDataToSend = new FormData();
            formDataToSend.append('email', formData.email);
            formDataToSend.append('password', formData.password);
            formDataToSend.append('confirm_password', formData.confirmPassword);
            
            // Send POST request to backend
            const response = await fetch('/register', {
                method: 'POST',
                body: formDataToSend,
                credentials: 'include' // Include cookies
            });
            
            // Check if response is a redirect
            if (response.redirected) {
                // POC/Local Development: Backend automatically logs user in after registration
                // and redirects to dashboard - follow the redirect
                window.location.href = response.url;
                return;
            }
            
            // If response is not redirect, parse the response
            const responseText = await response.text();
            
            if (response.ok) {
                // Success - For POC this should normally redirect automatically,
                // but handle any success messages just in case
                if (responseText.includes('success_message')) {
                    // Parse HTML to extract success message
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(responseText, 'text/html');
                    const successElement = doc.querySelector('[id*="success"]');
                    
                    if (successElement) {
                        this.showGeneralSuccess(successElement.textContent.trim());
                    } else {
                        this.showGeneralSuccess('Konto zostało utworzone i zostałeś automatycznie zalogowany!');
                    }
                } else {
                    // POC: Account created and user should be logged in automatically
                    this.showGeneralSuccess('Konto zostało utworzone i zostałeś automatycznie zalogowany!');
                    
                    // Redirect to dashboard after a short delay
                    setTimeout(() => {
                        window.location.href = '/dashboard';
                    }, 1500);
                }
                
            } else {
                // Error - try to parse error from response
                if (responseText.includes('error_message')) {
                    // Parse HTML to extract error message
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(responseText, 'text/html');
                    const errorElement = doc.querySelector('[id*="error"]');
                    
                    if (errorElement) {
                        throw new Error(errorElement.textContent.trim());
                    }
                }
                
                throw new Error('Wystąpił błąd podczas rejestracji');
            }
            
        } catch (error) {
            console.error('Register error:', error);
            
            // Show error to user
            if (error.message.includes('fetch')) {
                this.showGeneralError('Błąd połączenia z serwerem. Sprawdź połączenie internetowe.');
            } else {
                this.showGeneralError(error.message || 'Wystąpił błąd podczas rejestracji');
            }
            
            throw error;
        }
    }
    
    handleAuthError(error) {
        let message = 'Wystąpił błąd podczas uwierzytelniania';
        
        // Map common errors to user-friendly messages
        if (error.message) {
            const errorMsg = error.message.toLowerCase();
            
            if (errorMsg.includes('invalid') || errorMsg.includes('credentials') || errorMsg.includes('nieprawidłowe')) {
                message = 'Nieprawidłowy email lub hasło';
            } else if (errorMsg.includes('already registered') || errorMsg.includes('already exists') || errorMsg.includes('istnieje')) {
                message = 'Użytkownik z tym adresem email już istnieje';
            } else if (errorMsg.includes('email not confirmed') || errorMsg.includes('weryfikacji')) {
                message = 'Potwierdź swój adres email, aby się zalogować';
                // Show email verification notice
                this.showEmailVerificationNotice();
                return;
            } else if (errorMsg.includes('network') || errorMsg.includes('connection') || errorMsg.includes('fetch') || errorMsg.includes('połączenia')) {
                message = 'Wystąpił błąd połączenia. Sprawdź połączenie internetowe i spróbuj ponownie.';
            } else if (errorMsg.includes('hasła nie są identyczne')) {
                message = 'Hasła nie są identyczne';
            } else if (errorMsg.includes('co najmniej 6 znaków')) {
                message = 'Hasło musi mieć co najmniej 6 znaków';
            } else {
                // Use the actual error message if it's user-friendly
                message = error.message;
            }
        }
        
        this.showGeneralError(message);
    }
    
    showEmailVerificationNotice() {
        // Hide error display if visible
        const errorDisplay = document.getElementById('errorDisplay');
        if (errorDisplay) {
            errorDisplay.style.display = 'none';
        }
        
        // Show email verification notice
        const verificationNotice = document.getElementById('emailVerificationNotice');
        if (verificationNotice) {
            verificationNotice.classList.remove('hidden');
            
            // Set email for resend form
            const emailField = document.getElementById('email');
            const resendEmailField = document.getElementById('resendEmail');
            if (emailField && resendEmailField) {
                resendEmailField.value = emailField.value.trim();
            }
        }
    }
    
    showForgotPasswordModal() {
        const modal = document.getElementById('forgotPasswordModal');
        const emailField = document.getElementById('email');
        const forgotEmailField = document.getElementById('forgotEmail');
        
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
            
            // Pre-fill email if available
            if (emailField && forgotEmailField && emailField.value) {
                forgotEmailField.value = emailField.value.trim();
            }
            
            // Focus on email field
            setTimeout(() => {
                if (forgotEmailField) {
                    forgotEmailField.focus();
                }
            }, 100);
        }
    }
    
    hideForgotPasswordModal() {
        const modal = document.getElementById('forgotPasswordModal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
    }
    
    async checkAuthState() {
        // TODO: Check if user is already authenticated
        // const { data: { session } } = await this.supabaseClient.auth.getSession();
        // if (session) {
        //     window.location.href = '/dashboard';
        // }
    }
    
    // Utility Methods
    togglePasswordVisibility() {
        const passwordField = document.getElementById('password');
        const eyeIcon = document.getElementById('eyeIcon');
        
        if (passwordField.type === 'password') {
            passwordField.type = 'text';
            // Update icon to "eye-off"
            eyeIcon.innerHTML = `
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L8.464 8.464M9.878 9.878l-1.414-1.414m4.242 4.242l1.414 1.414m0 0l1.414 1.414m-1.414-1.414L14.5 14.5"/>
            `;
        } else {
            passwordField.type = 'password';
            // Update icon back to "eye"
            eyeIcon.innerHTML = `
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
            `;
        }
    }
}

// Handle browser back/forward navigation
window.addEventListener('popstate', (event) => {
    if (event.state && event.state.mode) {
        authManager.currentMode = event.state.mode;
        authManager.updateModeUI();
        authManager.resetForm();
    }
});

// Initialize Auth Manager when DOM is loaded
let authManager;
document.addEventListener('DOMContentLoaded', () => {
    authManager = new AuthManager();
}); 