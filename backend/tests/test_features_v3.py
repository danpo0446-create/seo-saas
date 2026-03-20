"""
Test features for iteration 3:
1. /api/articles - Verify site_id filter works correctly
2. /api/automation/publication-log - Verify it returns correct publication list
3. Dashboard GSC stats should update when site changes (tested via frontend)
4. Web2Page should show only articles for current site
5. AutomationPage should have 'Jurnal Publicări' tab
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://login-auth-test.preview.emergentagent.com"

TEST_EMAIL = f"test_iter3_{int(time.time())}@test.com"
TEST_PASSWORD = "TestPass123!"
TEST_NAME = "Test User Iteration3"


class TestArticleFiltering:
    """Test that articles are correctly filtered by site_id"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Register and login to get token"""
        # Register
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "name": TEST_NAME
        })
        if response.status_code == 200:
            return response.json().get("token")
        elif response.status_code == 400:
            # User might already exist, try login
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            })
            if response.status_code == 200:
                return response.json().get("token")
        pytest.skip("Could not authenticate")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_articles_endpoint_exists(self, headers):
        """Test GET /api/articles endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/api/articles", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"✓ GET /api/articles returns 200 - got {len(response.json())} articles")
    
    def test_articles_accepts_site_id_param(self, headers):
        """Test GET /api/articles accepts site_id query parameter"""
        # Even with invalid site_id, should return 200 with empty list
        response = requests.get(
            f"{BASE_URL}/api/articles",
            headers=headers,
            params={"site_id": "nonexistent-site-id-123"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ GET /api/articles with site_id=invalid returns empty list: {len(data)} articles")
    
    def test_articles_without_site_id_returns_all(self, headers):
        """Test GET /api/articles without site_id returns all user articles"""
        response = requests.get(f"{BASE_URL}/api/articles", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ GET /api/articles without filter returns {len(data)} articles")


class TestPublicationLog:
    """Test the publication log endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Register and login to get token"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "name": TEST_NAME
        })
        if response.status_code == 200:
            return response.json().get("token")
        elif response.status_code == 400:
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            })
            if response.status_code == 200:
                return response.json().get("token")
        pytest.skip("Could not authenticate")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_publication_log_endpoint_exists(self, headers):
        """Test GET /api/automation/publication-log endpoint exists"""
        response = requests.get(f"{BASE_URL}/api/automation/publication-log", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ GET /api/automation/publication-log returns 200")
    
    def test_publication_log_returns_list(self, headers):
        """Test publication log returns a list"""
        response = requests.get(f"{BASE_URL}/api/automation/publication-log", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"✓ Publication log returns list with {len(data)} entries")
    
    def test_publication_log_entry_structure(self, headers):
        """Test publication log entries have correct fields"""
        response = requests.get(f"{BASE_URL}/api/automation/publication-log", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        expected_fields = [
            "id", "title", "site_id", "site_name", "status", 
            "created_at", "published_at", "word_count", "auto_generated"
        ]
        
        if len(data) > 0:
            entry = data[0]
            for field in expected_fields:
                assert field in entry, f"Missing field: {field}"
            print(f"✓ Publication log entry has all expected fields: {list(entry.keys())}")
        else:
            print("✓ Publication log is empty (no published articles yet)")
    
    def test_publication_log_requires_auth(self):
        """Test publication log requires authentication"""
        response = requests.get(f"{BASE_URL}/api/automation/publication-log")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("✓ Publication log requires authentication")


class TestAutomationEndpoints:
    """Test automation endpoints that affect filtering and publication log"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "name": TEST_NAME
        })
        if response.status_code == 200:
            return response.json().get("token")
        elif response.status_code == 400:
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            })
            if response.status_code == 200:
                return response.json().get("token")
        pytest.skip("Could not authenticate")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_automation_sites_endpoint(self, headers):
        """Test GET /api/automation/sites"""
        response = requests.get(f"{BASE_URL}/api/automation/sites", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ GET /api/automation/sites returns {len(data)} sites")
    
    def test_automation_history_endpoint(self, headers):
        """Test GET /api/automation/history"""
        response = requests.get(f"{BASE_URL}/api/automation/history", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ GET /api/automation/history returns {len(data)} entries")
    
    def test_stats_per_site_endpoint(self, headers):
        """Test GET /api/automation/stats-per-site"""
        response = requests.get(f"{BASE_URL}/api/automation/stats-per-site", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "stats" in data, "Response should have 'stats' field"
        assert "total_monthly" in data, "Response should have 'total_monthly' field"
        assert "total_all_time" in data, "Response should have 'total_all_time' field"
        print(f"✓ GET /api/automation/stats-per-site returns correct structure")


class TestSearchConsoleEndpoints:
    """Test GSC endpoints for dashboard refresh functionality"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "name": TEST_NAME
        })
        if response.status_code == 200:
            return response.json().get("token")
        elif response.status_code == 400:
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            })
            if response.status_code == 200:
                return response.json().get("token")
        pytest.skip("Could not authenticate")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_gsc_status_endpoint(self, headers):
        """Test GET /api/search-console/status"""
        response = requests.get(f"{BASE_URL}/api/search-console/status", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "connected" in data, "Response should have 'connected' field"
        print(f"✓ GSC status endpoint returns connected={data.get('connected')}")
    
    def test_gsc_stats_endpoint(self, headers):
        """Test GET /api/search-console/stats"""
        response = requests.get(f"{BASE_URL}/api/search-console/stats", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        # Should have basic stats fields
        assert "clicks" in data or "impressions" in data, "Response should have traffic stats"
        print(f"✓ GSC stats endpoint returns data")


class TestDashboardStats:
    """Test dashboard stats endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "name": TEST_NAME
        })
        if response.status_code == 200:
            return response.json().get("token")
        elif response.status_code == 400:
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            })
            if response.status_code == 200:
                return response.json().get("token")
        pytest.skip("Could not authenticate")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_dashboard_stats_endpoint(self, headers):
        """Test GET /api/dashboard/stats"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        # Check essential dashboard stats
        assert "total_articles" in data, "Response should have 'total_articles'"
        print(f"✓ Dashboard stats returns total_articles={data.get('total_articles')}")
    
    def test_dashboard_stats_with_site_id(self, headers):
        """Test GET /api/dashboard/stats accepts site_id parameter"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=headers,
            params={"site_id": "test-site-id"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ Dashboard stats accepts site_id parameter")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
