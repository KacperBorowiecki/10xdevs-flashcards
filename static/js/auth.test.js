/**
 * Client-side tests for AuthManager and form validation.
 * These tests can be run in browser console or with a JS testing framework.
 */

// Mock DOM elements for testing
function createMockDOM() {
    // Create mock elements
    const mockElements = {
        authForm: { addEventListener: jest.fn(), reset: jest.fn() },
        email: { 
            value: '', 
            addEventListener: jest.fn(),
            classList: { add: jest.fn(), remove: jest.fn() }
        },
        password: { 
            value: '', 
            addEventListener: jest.fn(),
            classList: { add: jest.fn(), remove: jest.fn() }
        },
        confirmPassword: { 
            value: '', 
            addEventListener: jest.fn(),
            classList: { add: jest.fn(), remove: jest.fn() }
        },
        submitButton: { 
            disabled: false,
            setAttribute: jest.fn(),
            removeAttribute: jest.fn()
        },
        emailError: { 
            textContent: '',
            classList: { add: jest.fn(), remove: jest.fn() }
        },
        passwordError: { 
            textContent: '',
            classList: { add: jest.fn(), remove: jest.fn() }
        },
        confirmPasswordError: { 
            textContent: '',
            classList: { add: jest.fn(), remove: jest.fn() }
        }
    };
    
    // Mock document.getElementById
    document.getElementById = jest.fn((id) => mockElements[id]);
    document.querySelectorAll = jest.fn(() => []);
    
    return mockElements;
}

// AuthManager Tests
describe('AuthManager', () => {
    let authManager;
    let mockElements;
    
    beforeEach(() => {
        // Reset mocks
        jest.clearAllMocks();
        mockElements = createMockDOM();
        
        // Mock window.location
        delete window.location;
        window.location = { pathname: '/login', href: '/login' };
        
        // Mock history API
        window.history = { pushState: jest.fn() };
        
        // Create AuthManager instance (assuming the class is available)
        // In real testing, you'd import the AuthManager class
        authManager = new AuthManager();
    });
    
    describe('Email Validation', () => {
        test('should validate correct email format', () => {
            mockElements.email.value = 'test@example.com';
            const result = authManager.validateEmail();
            expect(result).toBe(true);
        });
        
        test('should reject empty email', () => {
            mockElements.email.value = '';
            const result = authManager.validateEmail();
            expect(result).toBe(false);
            expect(mockElements.emailError.textContent).toBe('Adres email jest wymagany');
        });
        
        test('should reject invalid email format', () => {
            mockElements.email.value = 'invalid-email';
            const result = authManager.validateEmail();
            expect(result).toBe(false);
            expect(mockElements.emailError.textContent).toBe('Wprowadź prawidłowy adres email');
        });
        
        test('should reject email too long', () => {
            mockElements.email.value = 'a'.repeat(250) + '@example.com';
            const result = authManager.validateEmail();
            expect(result).toBe(false);
            expect(mockElements.emailError.textContent).toBe('Adres email jest za długi (max 254 znaków)');
        });
    });
    
    describe('Password Validation', () => {
        test('should validate correct password', () => {
            mockElements.password.value = 'validPassword123';
            const result = authManager.validatePassword();
            expect(result).toBe(true);
        });
        
        test('should reject empty password', () => {
            mockElements.password.value = '';
            const result = authManager.validatePassword();
            expect(result).toBe(false);
            expect(mockElements.passwordError.textContent).toBe('Hasło jest wymagane');
        });
        
        test('should reject too short password', () => {
            mockElements.password.value = '12345';
            const result = authManager.validatePassword();
            expect(result).toBe(false);
            expect(mockElements.passwordError.textContent).toBe('Hasło musi mieć co najmniej 6 znaków');
        });
        
        test('should reject too long password', () => {
            mockElements.password.value = 'a'.repeat(129);
            const result = authManager.validatePassword();
            expect(result).toBe(false);
            expect(mockElements.passwordError.textContent).toBe('Hasło jest za długie (max 128 znaków)');
        });
    });
    
    describe('Confirm Password Validation', () => {
        beforeEach(() => {
            authManager.currentMode = 'register';
        });
        
        test('should validate matching passwords', () => {
            mockElements.password.value = 'password123';
            mockElements.confirmPassword.value = 'password123';
            const result = authManager.validateConfirmPassword();
            expect(result).toBe(true);
        });
        
        test('should reject empty confirm password', () => {
            mockElements.password.value = 'password123';
            mockElements.confirmPassword.value = '';
            const result = authManager.validateConfirmPassword();
            expect(result).toBe(false);
            expect(mockElements.confirmPasswordError.textContent).toBe('Potwierdzenie hasła jest wymagane');
        });
        
        test('should reject mismatched passwords', () => {
            mockElements.password.value = 'password123';
            mockElements.confirmPassword.value = 'different123';
            const result = authManager.validateConfirmPassword();
            expect(result).toBe(false);
            expect(mockElements.confirmPasswordError.textContent).toBe('Hasła nie są identyczne');
        });
        
        test('should skip validation in login mode', () => {
            authManager.currentMode = 'login';
            const result = authManager.validateConfirmPassword();
            expect(result).toBe(true);
        });
    });
    
    describe('Form Validation', () => {
        test('should validate complete login form', () => {
            authManager.currentMode = 'login';
            mockElements.email.value = 'test@example.com';
            mockElements.password.value = 'password123';
            
            const result = authManager.validateForm();
            expect(result).toBe(true);
        });
        
        test('should validate complete register form', () => {
            authManager.currentMode = 'register';
            mockElements.email.value = 'test@example.com';
            mockElements.password.value = 'password123';
            mockElements.confirmPassword.value = 'password123';
            
            const result = authManager.validateForm();
            expect(result).toBe(true);
        });
        
        test('should reject incomplete form', () => {
            authManager.currentMode = 'login';
            mockElements.email.value = '';
            mockElements.password.value = 'password123';
            
            const result = authManager.validateForm();
            expect(result).toBe(false);
        });
    });
    
    describe('Mode Switching', () => {
        test('should switch from login to register', () => {
            authManager.currentMode = 'login';
            authManager.switchMode('register');
            
            expect(authManager.currentMode).toBe('register');
            expect(window.history.pushState).toHaveBeenCalledWith(
                { mode: 'register' }, 
                '', 
                '/register'
            );
        });
        
        test('should not switch to same mode', () => {
            authManager.currentMode = 'login';
            authManager.switchMode('login');
            
            expect(window.history.pushState).not.toHaveBeenCalled();
        });
        
        test('should clear errors when switching modes', () => {
            authManager.validationErrors = { email: 'Some error' };
            authManager.switchMode('register');
            
            expect(authManager.validationErrors).toEqual({});
        });
    });
    
    describe('Error Handling', () => {
        test('should set field error correctly', () => {
            authManager.setFieldError('email', 'Test error message');
            
            expect(authManager.validationErrors.email).toBe('Test error message');
            expect(mockElements.emailError.textContent).toBe('Test error message');
            expect(mockElements.emailError.classList.remove).toHaveBeenCalledWith('hidden');
            expect(mockElements.email.classList.add).toHaveBeenCalledWith('border-red-500');
        });
        
        test('should clear field error correctly', () => {
            authManager.validationErrors.email = 'Some error';
            authManager.clearFieldError('email');
            
            expect(authManager.validationErrors.email).toBeUndefined();
            expect(mockElements.emailError.classList.add).toHaveBeenCalledWith('hidden');
            expect(mockElements.email.classList.remove).toHaveBeenCalledWith('border-red-500');
        });
        
        test('should clear all errors', () => {
            authManager.validationErrors = {
                email: 'Error 1',
                password: 'Error 2'
            };
            
            authManager.clearAllErrors();
            expect(authManager.validationErrors).toEqual({});
        });
    });
    
    describe('Loading State Management', () => {
        test('should set loading state correctly', () => {
            authManager.setLoadingState(true);
            
            expect(authManager.isLoading).toBe(true);
            expect(mockElements.submitButton.disabled).toBe(true);
            expect(mockElements.submitButton.setAttribute).toHaveBeenCalledWith('aria-busy', 'true');
        });
        
        test('should clear loading state correctly', () => {
            authManager.setLoadingState(false);
            
            expect(authManager.isLoading).toBe(false);
            expect(mockElements.submitButton.disabled).toBe(false);
            expect(mockElements.submitButton.removeAttribute).toHaveBeenCalledWith('aria-busy');
        });
    });
    
    describe('Form Data Extraction', () => {
        test('should extract form data correctly', () => {
            mockElements.email.value = 'test@example.com';
            mockElements.password.value = 'password123';
            mockElements.confirmPassword.value = 'password123';
            
            const formData = authManager.getFormData();
            
            expect(formData).toEqual({
                email: 'test@example.com',
                password: 'password123',
                confirmPassword: 'password123'
            });
        });
        
        test('should trim email whitespace', () => {
            mockElements.email.value = '  test@example.com  ';
            mockElements.password.value = 'password123';
            
            const formData = authManager.getFormData();
            expect(formData.email).toBe('test@example.com');
        });
    });
});

// Integration Tests
describe('Auth Integration', () => {
    test('should handle complete login flow', async () => {
        const mockElements = createMockDOM();
        const authManager = new AuthManager();
        
        // Set form values
        mockElements.email.value = 'test@example.com';
        mockElements.password.value = 'password123';
        
        // Mock successful API response
        global.fetch = jest.fn(() => 
            Promise.resolve({
                ok: true,
                redirected: true,
                url: '/dashboard'
            })
        );
        
        // Simulate form submission
        await authManager.handleFormSubmit();
        
        // Verify loading state was set and cleared
        expect(authManager.isLoading).toBe(false);
    });
    
    test('should handle API errors gracefully', async () => {
        const mockElements = createMockDOM();
        const authManager = new AuthManager();
        
        // Set form values
        mockElements.email.value = 'test@example.com';
        mockElements.password.value = 'password123';
        
        // Mock API error
        global.fetch = jest.fn(() => 
            Promise.reject(new Error('Network error'))
        );
        
        // Simulate form submission
        await authManager.handleFormSubmit();
        
        // Verify error handling
        expect(authManager.isLoading).toBe(false);
    });
});

// Accessibility Tests
describe('Accessibility Features', () => {
    test('should manage focus correctly', () => {
        const mockElements = createMockDOM();
        mockElements.email.focus = jest.fn();
        
        const authManager = new AuthManager();
        authManager.manageFocus();
        
        // Focus should be set after timeout
        setTimeout(() => {
            expect(mockElements.email.focus).toHaveBeenCalled();
        }, 150);
    });
    
    test('should set proper ARIA attributes during loading', () => {
        const mockElements = createMockDOM();
        const authManager = new AuthManager();
        
        authManager.setLoadingState(true);
        
        expect(mockElements.submitButton.setAttribute).toHaveBeenCalledWith('aria-busy', 'true');
    });
});

// Performance Tests
describe('Performance', () => {
    test('should not perform unnecessary validation', () => {
        const mockElements = createMockDOM();
        const authManager = new AuthManager();
        
        // Mock validation methods to track calls
        const validateEmailSpy = jest.spyOn(authManager, 'validateEmail');
        const validatePasswordSpy = jest.spyOn(authManager, 'validatePassword');
        
        // Switching to same mode should not trigger validation
        authManager.currentMode = 'login';
        authManager.switchMode('login');
        
        expect(validateEmailSpy).not.toHaveBeenCalled();
        expect(validatePasswordSpy).not.toHaveBeenCalled();
    });
    
    test('should debounce validation calls', (done) => {
        const mockElements = createMockDOM();
        const authManager = new AuthManager();
        
        // Mock rapid input changes
        let validationCalls = 0;
        const originalValidate = authManager.validateEmail;
        authManager.validateEmail = () => {
            validationCalls++;
            return originalValidate.call(authManager);
        };
        
        // Simulate rapid typing
        for (let i = 0; i < 10; i++) {
            setTimeout(() => {
                authManager.validateEmail();
                if (i === 9) {
                    // After all calls, validation should be optimized
                    expect(validationCalls).toBeLessThan(10);
                    done();
                }
            }, i * 10);
        }
    });
});

// Export for use in testing frameworks
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        createMockDOM,
        // Add other test utilities
    };
} 