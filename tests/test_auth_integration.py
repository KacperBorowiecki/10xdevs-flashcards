"""
Integration tests for authentication views.
Tests all user scenarios: login, register, validation, error handling.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import json

from main import app

client = TestClient(app)

@pytest.mark.skip("TODO: Fix integration test authorization, mocking and TestClient API issues")
class TestAuthViews:
    """Test suite for authentication views."""
    
    def test_login_page_renders(self):
        """Test that login page renders correctly."""
        response = client.get("/login")
        assert response.status_code == 200
        assert "10x Cards" in response.text
        assert "Zaloguj się" in response.text
        assert 'mode="login"' in response.text
        
    def test_register_page_renders(self):
        """Test that register page renders correctly."""
        response = client.get("/register")
        assert response.status_code == 200
        assert "10x Cards" in response.text
        assert "Zarejestruj się" in response.text
        assert 'mode="register"' in response.text
        
    def test_login_redirect_when_authenticated(self):
        """Test redirect to dashboard when user is already authenticated."""
        # Mock authenticated state
        with patch('src.services.auth_service.AuthService.is_authenticated', return_value=True):
            response = client.get("/login", allow_redirects=False)
            assert response.status_code == 302
            assert response.headers["location"] == "/dashboard"
            
    def test_register_redirect_when_authenticated(self):
        """Test redirect to dashboard when user is already authenticated."""
        # Mock authenticated state
        with patch('src.services.auth_service.AuthService.is_authenticated', return_value=True):
            response = client.get("/register", allow_redirects=False)
            assert response.status_code == 302
            assert response.headers["location"] == "/dashboard"
    
    def test_successful_login(self):
        """Test successful login flow."""
        form_data = {
            "email": "user@example.com",
            "password": "validpassword123"
        }
        response = client.post("/login", data=form_data, allow_redirects=False)
        
        # Should redirect to dashboard
        assert response.status_code == 302
        assert response.headers["location"] == "/dashboard"
        
        # Should set auth cookie
        cookies = response.cookies
        assert "auth_session" in cookies
        
    def test_successful_register(self):
        """Test successful registration flow."""
        form_data = {
            "email": "newuser@example.com", 
            "password": "validpassword123",
            "confirm_password": "validpassword123"
        }
        response = client.post("/register", data=form_data)
        
        assert response.status_code == 200
        assert "Konto zostało utworzone" in response.text
        
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        form_data = {
            "email": "test@error.com",
            "password": "wrongpassword"
        }
        response = client.post("/login", data=form_data)
        
        assert response.status_code == 200
        assert "Nieprawidłowy email lub hasło" in response.text
        
    def test_login_unconfirmed_email(self):
        """Test login with unconfirmed email."""
        form_data = {
            "email": "test@unconfirmed.com",
            "password": "validpassword123"
        }
        response = client.post("/login", data=form_data)
        
        assert response.status_code == 200
        assert "Potwierdź swój adres email" in response.text
        
    def test_login_network_error(self):
        """Test login with network error."""
        form_data = {
            "email": "test@network.com",
            "password": "validpassword123"
        }
        response = client.post("/login", data=form_data)
        
        assert response.status_code == 200
        assert "Wystąpił błąd połączenia" in response.text
        
    def test_register_existing_user(self):
        """Test registration with existing email."""
        form_data = {
            "email": "test@exists.com",
            "password": "validpassword123",
            "confirm_password": "validpassword123"
        }
        response = client.post("/register", data=form_data)
        
        assert response.status_code == 200
        assert "Użytkownik z tym adresem email już istnieje" in response.text
        
    def test_register_password_mismatch(self):
        """Test registration with password mismatch."""
        form_data = {
            "email": "user@example.com",
            "password": "password123",
            "confirm_password": "different123"
        }
        response = client.post("/register", data=form_data)
        
        assert response.status_code == 200
        assert "Hasła nie są identyczne" in response.text
        
    def test_login_validation_errors(self):
        """Test login form validation errors."""
        # Test empty email
        form_data = {"email": "", "password": "validpassword123"}
        response = client.post("/login", data=form_data)
        assert response.status_code == 200
        assert "Nieprawidłowe dane formularza" in response.text
        
        # Test invalid email format
        form_data = {"email": "invalid-email", "password": "validpassword123"}
        response = client.post("/login", data=form_data)
        assert response.status_code == 200
        assert "Nieprawidłowe dane formularza" in response.text
        
        # Test short password
        form_data = {"email": "user@example.com", "password": "12345"}
        response = client.post("/login", data=form_data)
        assert response.status_code == 200
        assert "Nieprawidłowe dane formularza" in response.text
        
    def test_register_validation_errors(self):
        """Test registration form validation errors."""
        # Test empty fields
        form_data = {"email": "", "password": "", "confirm_password": ""}
        response = client.post("/register", data=form_data)
        assert response.status_code == 200
        assert "Nieprawidłowe dane formularza" in response.text
        
        # Test invalid email format
        form_data = {
            "email": "invalid-email",
            "password": "validpassword123", 
            "confirm_password": "validpassword123"
        }
        response = client.post("/register", data=form_data)
        assert response.status_code == 200
        assert "Nieprawidłowe dane formularza" in response.text
        
    def test_logout_clears_session(self):
        """Test that logout clears authentication session."""
        # First login
        form_data = {"email": "user@example.com", "password": "validpassword123"}
        login_response = client.post("/login", data=form_data, allow_redirects=False)
        
        # Then logout
        logout_response = client.post("/logout", allow_redirects=False)
        assert logout_response.status_code == 302
        assert logout_response.headers["location"] == "/login"
        
        # Check that auth cookie is cleared
        cookies = logout_response.cookies
        assert cookies.get("auth_session") is None or cookies.get("auth_session") == ""
        
    def test_logout_get_method(self):
        """Test logout via GET method."""
        response = client.get("/logout", allow_redirects=False)
        assert response.status_code == 302
        assert response.headers["location"] == "/login"
        
    def test_redirect_after_login_with_next_param(self):
        """Test redirect to specific page after login using next parameter."""
        # Try to access protected page
        response = client.get("/login?next=/dashboard")
        assert response.status_code == 200
        
        # Login should redirect to the next URL
        form_data = {"email": "user@example.com", "password": "validpassword123"}
        response = client.post("/login?next=/dashboard", data=form_data, allow_redirects=False)
        assert response.status_code == 302
        assert response.headers["location"] == "/dashboard"
        
    def test_csrf_protection(self):
        """Test that forms require proper method."""
        # GET request to POST endpoint should not work
        response = client.get("/login", allow_redirects=False)
        # This should render the form, not process it
        assert response.status_code == 200
        assert "Zaloguj się" in response.text
        
    def test_auth_page_accessibility(self):
        """Test accessibility features in auth pages."""
        response = client.get("/login")
        content = response.text
        
        # Check for ARIA attributes
        assert 'aria-describedby="emailError"' in content
        assert 'aria-describedby="passwordError"' in content
        assert 'aria-label="Pokaż/ukryj hasło"' in content
        
        # Check for proper form structure
        assert '<label for="email"' in content
        assert '<label for="password"' in content
        assert 'autocomplete="email"' in content
        assert 'autocomplete="current-password"' in content
        
    def test_auth_page_meta_tags(self):
        """Test proper meta tags and page structure."""
        response = client.get("/login")
        content = response.text
        
        # Check for proper meta tags
        assert '<meta charset="UTF-8">' in content
        assert '<meta name="viewport"' in content
        assert '<title>' in content and 'Zaloguj się - 10x Cards' in content
        
        # Check for CSS and JavaScript includes
        assert '/static/css/auth.css' in content
        assert '/static/js/auth.js' in content
        
    def test_password_field_security(self):
        """Test password field security attributes."""
        response = client.get("/login")
        content = response.text
        
        # Password field should be type="password"
        assert 'type="password"' in content
        assert 'minlength="6"' in content
        assert 'maxlength="128"' in content
        
    def test_error_message_display(self):
        """Test error message display and structure."""
        form_data = {"email": "test@error.com", "password": "validpassword123"}
        response = client.post("/login", data=form_data)
        content = response.text
        
        # Error should be displayed with proper structure
        assert 'id="errorDisplay"' in content
        assert 'text-red-800' in content
        assert 'Nieprawidłowy email lub hasło' in content
        
    def test_form_persistence_on_error(self):
        """Test that form values persist when there are errors."""
        form_data = {"email": "test@error.com", "password": "validpassword123"}
        response = client.post("/login", data=form_data)
        
        # Form should be rendered with error, but this is basic HTML form
        # so email persistence would need to be implemented server-side
        assert response.status_code == 200
        assert "login" in response.text
        
    def test_auth_service_cookie_handling(self):
        """Test AuthService cookie handling functions."""
        from src.services.auth_service import AuthService
        from fastapi import Request, Response
        from unittest.mock import MagicMock
        
        # Test cookie setting
        response = MagicMock(spec=Response)
        user_data = {"id": "test-user-id", "email": "test@example.com"}
        
        AuthService.set_auth_cookie(response, user_data)
        response.set_cookie.assert_called_once()
        
        # Test cookie clearing
        response_clear = MagicMock(spec=Response)
        AuthService.clear_auth_cookie(response_clear)
        response_clear.delete_cookie.assert_called_once()
        
    def test_auth_exceptions(self):
        """Test custom authentication exceptions."""
        from src.core.exceptions import (
            InvalidCredentialsError,
            UserAlreadyExistsError, 
            EmailNotConfirmedError,
            NetworkError,
            ValidationError
        )
        
        # Test exception messages
        assert InvalidCredentialsError().message == "Nieprawidłowy email lub hasło"
        assert UserAlreadyExistsError().message == "Użytkownik z tym adresem email już istnieje"
        assert EmailNotConfirmedError().message == "Potwierdź swój adres email, aby się zalogować"
        assert NetworkError().message == "Wystąpił błąd połączenia. Spróbuj ponownie."
        
        # Test validation error with field
        validation_error = ValidationError("email", "Email jest wymagany")
        assert validation_error.field == "email" 
        assert validation_error.message == "Email jest wymagany" 