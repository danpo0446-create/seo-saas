"""
Backend Tests for Refactored Routes
Tests the modular routes extracted from server.py:
- /api/health
- /api/auth/login
- /api/dashboard/stats
- /api/dashboard/all
- /api/settings
- /api/pagespeed/all-sites
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from review request
ADMIN_EMAIL = "seamanshelp2021@gmail.com"
ADMIN_PASSWORD = "admin123"


class TestHealthEndpoint:
    """Test /api/health endpoint"""
    
    def test_health_check_returns_200(self):
        """Health endpoint should return 200 and healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "status" in data, "Response should contain 'status' field"
        assert data["status"] == "healthy", f"Expected 'healthy', got {data['status']}"
        assert "database" in data, "Response should contain 'database' field"
        assert "timestamp" in data, "Response should contain 'timestamp' field"
        print(f"PASS: Health check returned: {data}")


class TestAuthLogin:
    """Test /api/auth/login endpoint"""
    
    def test_login_with_valid_credentials(self):
        """Login should return token and user info"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
        
        data = response.json()
        # Check for token (could be 'token' or 'access_token')
        has_token = "token" in data or "access_token" in data
        assert has_token, f"Response should contain token. Got: {data.keys()}"
        assert "user" in data, "Response should contain 'user' field"
        assert data["user"]["email"] == ADMIN_EMAIL, f"Email mismatch"
        print(f"PASS: Login successful for {ADMIN_EMAIL}")
        return data.get("token") or data.get("access_token")
    
    def test_login_with_invalid_credentials(self):
        """Login with wrong password should return 401"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": "wrongpassword"}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("PASS: Invalid credentials correctly rejected")


class TestDashboardRoutes:
    """Test /api/dashboard/* endpoints (requires authentication)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("token") or data.get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Could not authenticate - skipping dashboard tests")
    
    def test_dashboard_stats_requires_auth(self):
        """Dashboard stats should require authentication"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("PASS: Dashboard stats correctly requires authentication")
    
    def test_dashboard_stats_with_auth(self):
        """Dashboard stats should return stats with valid auth"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
        
        data = response.json()
        # Verify expected fields from dashboard.py
        expected_fields = ["total_articles", "published_articles", "draft_articles", 
                          "total_keywords", "scheduled_posts", "monthly_quota"]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}. Got: {data.keys()}"
        print(f"PASS: Dashboard stats returned: {data}")
    
    def test_dashboard_all_with_auth(self):
        """Dashboard all endpoint should return combined data"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/all",
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
        
        data = response.json()
        # Verify expected sections from dashboard.py
        assert "stats" in data, "Response should contain 'stats' section"
        assert "automation" in data, "Response should contain 'automation' section"
        assert "site_stats" in data, "Response should contain 'site_stats' section"
        print(f"PASS: Dashboard all returned sections: {list(data.keys())}")


class TestSettingsRoutes:
    """Test /api/settings endpoints (requires authentication)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("token") or data.get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Could not authenticate - skipping settings tests")
    
    def test_settings_requires_auth(self):
        """Settings should require authentication"""
        response = requests.get(f"{BASE_URL}/api/settings")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("PASS: Settings correctly requires authentication")
    
    def test_get_settings_with_auth(self):
        """GET settings should return user settings"""
        response = requests.get(
            f"{BASE_URL}/api/settings",
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
        
        data = response.json()
        # Verify expected fields from settings.py SettingsResponse
        expected_fields = ["id", "company_name", "primary_color", "email_notifications", "user_id"]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}. Got: {data.keys()}"
        print(f"PASS: Settings returned: company_name={data.get('company_name')}")
    
    def test_patch_settings_with_auth(self):
        """PATCH settings should update user settings"""
        # First get current settings
        get_response = requests.get(
            f"{BASE_URL}/api/settings",
            headers=self.headers
        )
        original_data = get_response.json()
        original_company = original_data.get("company_name", "")
        
        # Update settings
        test_company_name = "TEST_Company_Updated"
        response = requests.patch(
            f"{BASE_URL}/api/settings",
            headers=self.headers,
            json={"company_name": test_company_name}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
        
        data = response.json()
        assert data.get("company_name") == test_company_name, f"Company name not updated. Got: {data.get('company_name')}"
        print(f"PASS: Settings updated successfully")
        
        # Verify persistence with GET
        verify_response = requests.get(
            f"{BASE_URL}/api/settings",
            headers=self.headers
        )
        verify_data = verify_response.json()
        assert verify_data.get("company_name") == test_company_name, "Settings not persisted"
        print("PASS: Settings persisted correctly")
        
        # Restore original value
        requests.patch(
            f"{BASE_URL}/api/settings",
            headers=self.headers,
            json={"company_name": original_company or "My SEO Agency"}
        )


class TestPagespeedRoutes:
    """Test /api/pagespeed/* endpoints (requires authentication)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("token") or data.get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Could not authenticate - skipping pagespeed tests")
    
    def test_pagespeed_all_sites_requires_auth(self):
        """Pagespeed all-sites should require authentication"""
        response = requests.get(f"{BASE_URL}/api/pagespeed/all-sites")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("PASS: Pagespeed all-sites correctly requires authentication")
    
    def test_pagespeed_all_sites_with_auth(self):
        """GET pagespeed/all-sites should return sites list"""
        response = requests.get(
            f"{BASE_URL}/api/pagespeed/all-sites",
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
        
        data = response.json()
        assert "sites" in data, f"Response should contain 'sites' field. Got: {data.keys()}"
        assert isinstance(data["sites"], list), "Sites should be a list"
        print(f"PASS: Pagespeed all-sites returned {len(data['sites'])} sites")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
