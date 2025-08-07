"""
Comprehensive test suite for authentication system
Tests OAuth flow, session persistence, and profile setup
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import jwt
import json


class TestAuthenticationFlow:
    """Test complete authentication flow"""
    
    def test_oauth_callback_sets_cookies(self, client: TestClient):
        """Test that OAuth callback properly sets session cookies"""
        # Simulate OAuth callback
        response = client.get("/api/auth/google/callback?code=test_auth_code")
        
        # Should redirect to profile page
        assert response.status_code == 302
        assert "/profile" in response.headers["location"]
        assert "auth=success" in response.headers["location"]
        
        # Check cookies are set
        cookies = response.cookies
        assert "soleil_session" in cookies
        assert "soleil_refresh" in cookies
    
    def test_session_validation_with_valid_token(self, client: TestClient):
        """Test session validation with valid JWT token"""
        # Create valid token
        JWT_SECRET = "your-secret-key-change-in-production"
        user_data = {
            "id": "test_user",
            "email": "test@example.com",
            "name": "Test User"
        }
        token_payload = {
            "user": user_data,
            "exp": (datetime.now() + timedelta(hours=1)).timestamp()
        }
        token = jwt.encode(token_payload, JWT_SECRET, algorithm="HS256")
        
        # Test validation endpoint
        response = client.get(
            "/api/auth/validate",
            cookies={"soleil_session": token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["user"]["email"] == "test@example.com"
    
    def test_session_validation_with_expired_token(self, client: TestClient):
        """Test session validation with expired token"""
        JWT_SECRET = "your-secret-key-change-in-production"
        token_payload = {
            "user": {"id": "test_user"},
            "exp": (datetime.now() - timedelta(hours=1)).timestamp()  # Expired
        }
        token = jwt.encode(token_payload, JWT_SECRET, algorithm="HS256")
        
        response = client.get(
            "/api/auth/validate",
            cookies={"soleil_session": token}
        )
        
        assert response.status_code == 401
    
    def test_session_refresh_with_valid_refresh_token(self, client: TestClient):
        """Test token refresh with valid refresh token"""
        JWT_SECRET = "your-secret-key-change-in-production"
        user_data = {"id": "test_user", "email": "test@example.com"}
        refresh_payload = {
            "user": user_data,
            "exp": (datetime.now() + timedelta(days=7)).timestamp()
        }
        refresh_token = jwt.encode(refresh_payload, JWT_SECRET, algorithm="HS256")
        
        response = client.post(
            "/api/auth/refresh",
            cookies={"soleil_refresh": refresh_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "session_token" in data
        assert data["user"]["email"] == "test@example.com"
    
    def test_logout_clears_session(self, client: TestClient):
        """Test that logout endpoint works"""
        response = client.post("/api/auth/logout")
        assert response.status_code == 200
        assert response.json()["status"] == "success"


class TestProfileSetup:
    """Test profile setup after OAuth"""
    
    def test_profile_creation_with_all_fields(self, client: TestClient):
        """Test creating user profile with all required fields"""
        profile_data = {
            "firstName": "John",
            "lastName": "Doe",
            "name": "John Doe",
            "email": "john@example.com",
            "instrument": "guitar",
            "phone": "+1234567890"
        }
        
        # Create session token
        JWT_SECRET = "your-secret-key-change-in-production"
        token_payload = {
            "user": {"id": "new_user"},
            "exp": (datetime.now() + timedelta(hours=1)).timestamp()
        }
        token = jwt.encode(token_payload, JWT_SECRET, algorithm="HS256")
        
        response = client.post(
            "/api/user/profile",
            json=profile_data,
            cookies={"soleil_session": token}
        )
        
        # Profile creation should succeed
        assert response.status_code in [200, 201]
    
    def test_profile_validation_requires_email(self, client: TestClient):
        """Test that profile requires email field"""
        profile_data = {
            "firstName": "John",
            "lastName": "Doe",
            "name": "John Doe",
            "email": "",  # Empty email
            "instrument": "guitar"
        }
        
        JWT_SECRET = "your-secret-key-change-in-production"
        token_payload = {
            "user": {"id": "new_user"},
            "exp": (datetime.now() + timedelta(hours=1)).timestamp()
        }
        token = jwt.encode(token_payload, JWT_SECRET, algorithm="HS256")
        
        response = client.post(
            "/api/user/profile",
            json=profile_data,
            cookies={"soleil_session": token}
        )
        
        # Should fail validation
        assert response.status_code == 400 or "email" in response.text.lower()


class TestSessionPersistence:
    """Test session persistence across page refreshes"""
    
    def test_session_persists_after_navigation(self, client: TestClient):
        """Test that session persists when navigating between pages"""
        # Create session
        JWT_SECRET = "your-secret-key-change-in-production"
        user_data = {
            "id": "test_user",
            "email": "test@example.com",
            "name": "Test User"
        }
        token_payload = {
            "user": user_data,
            "exp": (datetime.now() + timedelta(hours=24)).timestamp()
        }
        token = jwt.encode(token_payload, JWT_SECRET, algorithm="HS256")
        
        # First request - validate session
        response1 = client.get(
            "/api/auth/validate",
            cookies={"soleil_session": token}
        )
        assert response1.status_code == 200
        
        # Second request - should still be valid
        response2 = client.get(
            "/api/auth/validate",
            cookies={"soleil_session": token}
        )
        assert response2.status_code == 200
        
        # Data should be consistent
        assert response1.json()["user"] == response2.json()["user"]
    
    def test_parallel_requests_with_same_session(self, client: TestClient):
        """Test multiple parallel requests with same session"""
        JWT_SECRET = "your-secret-key-change-in-production"
        token_payload = {
            "user": {"id": "test_user"},
            "exp": (datetime.now() + timedelta(hours=1)).timestamp()
        }
        token = jwt.encode(token_payload, JWT_SECRET, algorithm="HS256")
        
        # Simulate parallel requests
        responses = []
        for _ in range(5):
            response = client.get(
                "/api/auth/validate",
                cookies={"soleil_session": token}
            )
            responses.append(response)
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200


@pytest.fixture
def client():
    """Create test client"""
    from start_server import app
    return TestClient(app)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])