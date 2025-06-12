/**
 * Test scenarios for Auth JavaScript functionality
 * Can be run in browser console for manual testing
 */

// Test scenarios object
const AuthTestScenarios = {
    
    // Test email validation
    testEmailValidation() {
        console.log('=== Testing Email Validation ===');
        
        const tests = [
            { email: 'test@example.com', expected: true, desc: 'Valid email' },
            { email: '', expected: false, desc: 'Empty email' },
            { email: 'invalid-email', expected: false, desc: 'Invalid format' },
            { email: 'test@', expected: false, desc: 'Incomplete domain' },
            { email: 'a'.repeat(250) + '@example.com', expected: false, desc: 'Too long' }
        ];
        
        tests.forEach(test => {
            document.getElementById('email').value = test.email;
            const result = authManager.validateEmail();
            const status = result === test.expected ? '✅ PASS' : '❌ FAIL';
            console.log(`${status}: ${test.desc} - "${test.email}"`);
        });
    },
    
    // Test password validation
    testPasswordValidation() {
        console.log('=== Testing Password Validation ===');
        
        const tests = [
            { password: 'validpass123', expected: true, desc: 'Valid password' },
            { password: '', expected: false, desc: 'Empty password' },
            { password: '12345', expected: false, desc: 'Too short' },
            { password: 'a'.repeat(129), expected: false, desc: 'Too long' },
            { password: 'password', expected: true, desc: 'Minimum length' }
        ];
        
        tests.forEach(test => {
            document.getElementById('password').value = test.password;
            const result = authManager.validatePassword();
            const status = result === test.expected ? '✅ PASS' : '❌ FAIL';
            console.log(`${status}: ${test.desc} - length: ${test.password.length}`);
        });
    },
    
    // Test confirm password validation
    testConfirmPasswordValidation() {
        console.log('=== Testing Confirm Password Validation ===');
        
        authManager.currentMode = 'register';
        
        const tests = [
            { password: 'test123', confirm: 'test123', expected: true, desc: 'Matching passwords' },
            { password: 'test123', confirm: '', expected: false, desc: 'Empty confirm' },
            { password: 'test123', confirm: 'different', expected: false, desc: 'Non-matching passwords' },
            { password: '', confirm: '', expected: false, desc: 'Both empty' }
        ];
        
        tests.forEach(test => {
            document.getElementById('password').value = test.password;
            document.getElementById('confirmPassword').value = test.confirm;
            const result = authManager.validateConfirmPassword();
            const status = result === test.expected ? '✅ PASS' : '❌ FAIL';
            console.log(`${status}: ${test.desc}`);
        });
    },
    
    // Test mode switching
    testModeSwitching() {
        console.log('=== Testing Mode Switching ===');
        
        const initialMode = authManager.currentMode;
        console.log(`Initial mode: ${initialMode}`);
        
        // Switch to opposite mode
        const newMode = initialMode === 'login' ? 'register' : 'login';
        authManager.switchMode(newMode);
        console.log(`✅ Switched to: ${authManager.currentMode}`);
        
        // Try switching to same mode (should be no-op)
        const currentMode = authManager.currentMode;
        authManager.switchMode(currentMode);
        console.log(`✅ No-op switch: ${authManager.currentMode}`);
        
        // Switch back
        authManager.switchMode(initialMode);
        console.log(`✅ Switched back to: ${authManager.currentMode}`);
    },
    
    // Test error handling
    testErrorHandling() {
        console.log('=== Testing Error Handling ===');
        
        // Test setting and clearing errors
        authManager.setFieldError('email', 'Test error message');
        console.log('✅ Set email error');
        
        authManager.clearFieldError('email');
        console.log('✅ Cleared email error');
        
        // Test multiple errors
        authManager.setFieldError('email', 'Email error');
        authManager.setFieldError('password', 'Password error');
        console.log('✅ Set multiple errors');
        
        authManager.clearAllErrors();
        console.log('✅ Cleared all errors');
        
        // Test general error
        authManager.showGeneralError('Test general error');
        console.log('✅ Showed general error');
    },
    
    // Test loading states
    testLoadingStates() {
        console.log('=== Testing Loading States ===');
        
        console.log('Setting loading state...');
        authManager.setLoadingState(true);
        console.log(`✅ Loading state: ${authManager.isLoading}`);
        
        setTimeout(() => {
            authManager.setLoadingState(false);
            console.log(`✅ Loading cleared: ${authManager.isLoading}`);
        }, 2000);
    },
    
    // Test form validation
    testFormValidation() {
        console.log('=== Testing Complete Form Validation ===');
        
        // Test valid login form
        authManager.currentMode = 'login';
        document.getElementById('email').value = 'test@example.com';
        document.getElementById('password').value = 'password123';
        
        let result = authManager.validateForm();
        console.log(`✅ Valid login form: ${result}`);
        
        // Test valid register form
        authManager.currentMode = 'register';
        document.getElementById('confirmPassword').value = 'password123';
        
        result = authManager.validateForm();
        console.log(`✅ Valid register form: ${result}`);
        
        // Test invalid form
        document.getElementById('email').value = '';
        result = authManager.validateForm();
        console.log(`✅ Invalid form: ${result}`);
    },
    
    // Test accessibility features
    testAccessibility() {
        console.log('=== Testing Accessibility Features ===');
        
        // Test ARIA attributes
        const submitButton = document.getElementById('submitButton');
        authManager.setLoadingState(true);
        
        if (submitButton.getAttribute('aria-busy') === 'true') {
            console.log('✅ ARIA busy attribute set correctly');
        }
        
        authManager.setLoadingState(false);
        if (!submitButton.getAttribute('aria-busy')) {
            console.log('✅ ARIA busy attribute cleared correctly');
        }
        
        // Test focus management
        authManager.manageFocus();
        console.log('✅ Focus management triggered');
    },
    
    // Test password visibility toggle
    testPasswordToggle() {
        console.log('=== Testing Password Visibility Toggle ===');
        
        const passwordField = document.getElementById('password');
        const initialType = passwordField.type;
        console.log(`Initial password type: ${initialType}`);
        
        authManager.togglePasswordVisibility();
        console.log(`After toggle: ${passwordField.type}`);
        
        authManager.togglePasswordVisibility();
        console.log(`After second toggle: ${passwordField.type}`);
        
        console.log('✅ Password toggle test completed');
    },
    
    // Run all tests
    runAllTests() {
        console.log('🚀 Running all Auth tests...\n');
        
        this.testEmailValidation();
        console.log('');
        
        this.testPasswordValidation();
        console.log('');
        
        this.testConfirmPasswordValidation();
        console.log('');
        
        this.testModeSwitching();
        console.log('');
        
        this.testErrorHandling();
        console.log('');
        
        this.testFormValidation();
        console.log('');
        
        this.testAccessibility();
        console.log('');
        
        this.testPasswordToggle();
        console.log('');
        
        console.log('🎉 All tests completed!');
        
        // Test loading states last (has timeout)
        this.testLoadingStates();
    },
    
    // Stress test with rapid input
    stressTest() {
        console.log('=== Stress Testing ===');
        
        const emailField = document.getElementById('email');
        const testEmails = [
            'test1@example.com',
            'test2@example.com', 
            'invalid-email',
            'test3@example.com',
            '',
            'test4@example.com'
        ];
        
        testEmails.forEach((email, index) => {
            setTimeout(() => {
                emailField.value = email;
                authManager.validateEmail();
                console.log(`Stress test ${index + 1}/6: ${email}`);
            }, index * 100);
        });
        
        console.log('✅ Stress test initiated');
    }
};

// Make available globally for browser console testing
window.AuthTestScenarios = AuthTestScenarios;

// Auto-run instruction
console.log(`
🧪 Auth Test Scenarios loaded!

Run tests in browser console:
- AuthTestScenarios.runAllTests() - Run all tests
- AuthTestScenarios.testEmailValidation() - Test email validation
- AuthTestScenarios.testPasswordValidation() - Test password validation
- AuthTestScenarios.stressTest() - Run stress test

Make sure authManager is loaded first!
`); 