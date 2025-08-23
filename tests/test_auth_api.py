"""Test authentication API flow."""
import pytest
import requests
from datetime import datetime

API = "http://localhost:8000/api/v1"


class TestAuth:
    """Test authentication flow."""
    
    @pytest.fixture
    def user_data(self):
        """Generate unique user data."""
        timestamp = int(datetime.now().timestamp())
        return {
            "email": f"test{timestamp}@example.com",
            "username": f"test{timestamp}",
            "password": "Test123!",
            "confirm_password": "Test123!"
        }
    
    def test_register(self, user_data):
        """Test user registration."""
        r = requests.post(f"{API}/auth/register", json=user_data)
        assert r.status_code == 201
        assert "access_token" in r.json()
    
    def test_login(self, user_data):
        """Test user login."""
        # Register first
        requests.post(f"{API}/auth/register", json=user_data)
        
        # Login
        r = requests.post(f"{API}/auth/login", json={
            "email_or_username": user_data["username"],
            "password": user_data["password"]
        })
        assert r.status_code == 200
        assert "access_token" in r.json()
        return r.json()["access_token"]
    
    def test_protected_endpoint(self, user_data):
        """Test accessing protected endpoint."""
        token = self.test_login(user_data)
        
        r = requests.get(
            f"{API}/auth/profile",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert r.status_code == 200
        assert r.json()["email"] == user_data["email"]
    
    def test_unauthorized_access(self):
        """Test access without token."""
        r = requests.get(f"{API}/auth/profile")
        assert r.status_code == 401