"""
Backend Tests for Phase 2 Refactored Routes
Tests the modular routes extracted from server.py in Phase 2:
- /api/notifications - Notifications CRUD
- /api/trends - Google Trends integration
- /api/templates - Article templates CRUD

Also verifies Phase 1 routes still work:
- /api/dashboard
- /api/settings
- /api/pagespeed
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "seamanshelp2021@gmail.com"
ADMIN_PASSWORD = "admin123"


class TestHealthAndAuth:
    """Basic health and auth tests to ensure API is working"""
    
    def test_health_check(self):
        """Health endpoint should return 200"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data["status"] == "healthy"
        print(f"PASS: Health check - status={data['status']}, database={data.get('database')}")
    
    def test_login_returns_token(self):
        """Login should return token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
        data = response.json()
        assert "token" in data or "access_token" in data
        print("PASS: Login returns token")


class TestNotificationsRoutes:
    """Test /api/notifications/* endpoints (Phase 2)"""
    
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
            pytest.skip("Could not authenticate - skipping notifications tests")
    
    def test_notifications_requires_auth(self):
        """GET /api/notifications should require authentication"""
        response = requests.get(f"{BASE_URL}/api/notifications")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("PASS: Notifications correctly requires authentication")
    
    def test_get_notifications_with_auth(self):
        """GET /api/notifications should return notifications list"""
        response = requests.get(
            f"{BASE_URL}/api/notifications",
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
        
        data = response.json()
        assert "notifications" in data, f"Response should contain 'notifications'. Got: {data.keys()}"
        assert "unread_count" in data, f"Response should contain 'unread_count'. Got: {data.keys()}"
        assert isinstance(data["notifications"], list), "notifications should be a list"
        print(f"PASS: GET /api/notifications returned {len(data['notifications'])} notifications, unread_count={data['unread_count']}")
    
    def test_mark_all_notifications_read(self):
        """PUT /api/notifications/read-all should mark all as read"""
        response = requests.put(
            f"{BASE_URL}/api/notifications/read-all",
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
        
        data = response.json()
        assert "success" in data, f"Response should contain 'success'. Got: {data.keys()}"
        assert data["success"] == True, f"Expected success=True, got {data['success']}"
        print(f"PASS: PUT /api/notifications/read-all - updated_count={data.get('updated_count', 0)}")


class TestTrendsRoutes:
    """Test /api/trends/* endpoints (Phase 2)"""
    
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
            pytest.skip("Could not authenticate - skipping trends tests")
    
    def test_trends_requires_auth(self):
        """GET /api/trends/trending should require authentication"""
        response = requests.get(f"{BASE_URL}/api/trends/trending")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("PASS: Trends correctly requires authentication")
    
    def test_get_trending_searches(self):
        """GET /api/trends/trending should return trending searches"""
        response = requests.get(
            f"{BASE_URL}/api/trends/trending",
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
        
        data = response.json()
        assert "trending" in data, f"Response should contain 'trending'. Got: {data.keys()}"
        assert "count" in data, f"Response should contain 'count'. Got: {data.keys()}"
        # Note: trending might be empty if Google Trends API has issues, but endpoint should work
        print(f"PASS: GET /api/trends/trending returned count={data['count']}")
    
    def test_get_trends_for_niche(self):
        """GET /api/trends/niche/{niche} should return niche-specific trends"""
        test_niche = "technology"
        response = requests.get(
            f"{BASE_URL}/api/trends/niche/{test_niche}",
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
        
        data = response.json()
        # Should return niche in response
        assert "niche" in data or "topic_ideas" in data or "error" in data, f"Response should contain niche data. Got: {data.keys()}"
        print(f"PASS: GET /api/trends/niche/{test_niche} returned data")


class TestTemplatesRoutes:
    """Test /api/templates/* endpoints (Phase 2)"""
    
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
            pytest.skip("Could not authenticate - skipping templates tests")
    
    def test_templates_requires_auth(self):
        """GET /api/templates should require authentication"""
        response = requests.get(f"{BASE_URL}/api/templates")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("PASS: Templates correctly requires authentication")
    
    def test_get_templates_list(self):
        """GET /api/templates should return templates list"""
        response = requests.get(
            f"{BASE_URL}/api/templates",
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), f"Response should be a list. Got: {type(data)}"
        # Should have default templates if user has none
        if len(data) > 0:
            template = data[0]
            assert "id" in template, "Template should have 'id'"
            assert "name" in template, "Template should have 'name'"
            assert "prompt_template" in template, "Template should have 'prompt_template'"
        print(f"PASS: GET /api/templates returned {len(data)} templates")
    
    def test_create_template(self):
        """POST /api/templates should create a new template"""
        test_template = {
            "name": f"TEST_Template_{uuid.uuid4().hex[:8]}",
            "description": "Test template for automated testing",
            "default_tone": "professional",
            "default_length": "medium",
            "prompt_template": "Write an article about {topic}. Include key points and examples.",
            "keywords_hint": "test, automation, pytest"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/templates",
            headers=self.headers,
            json=test_template
        )
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}. Response: {response.text}"
        
        data = response.json()
        assert "id" in data, f"Response should contain 'id'. Got: {data.keys()}"
        assert data["name"] == test_template["name"], f"Name mismatch"
        assert data["prompt_template"] == test_template["prompt_template"], f"Prompt template mismatch"
        
        # Store template_id for cleanup
        self.created_template_id = data["id"]
        print(f"PASS: POST /api/templates created template with id={data['id']}")
        
        # Cleanup - delete the test template
        delete_response = requests.delete(
            f"{BASE_URL}/api/templates/{data['id']}",
            headers=self.headers
        )
        if delete_response.status_code == 200:
            print(f"PASS: Cleanup - deleted test template")
    
    def test_delete_template_not_found(self):
        """DELETE /api/templates/{id} should return 404 for non-existent template"""
        fake_id = str(uuid.uuid4())
        response = requests.delete(
            f"{BASE_URL}/api/templates/{fake_id}",
            headers=self.headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("PASS: DELETE /api/templates returns 404 for non-existent template")


class TestPhase1RoutesStillWork:
    """Verify Phase 1 routes (dashboard, settings, pagespeed) still work after Phase 2 refactoring"""
    
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
            pytest.skip("Could not authenticate - skipping Phase 1 verification tests")
    
    def test_dashboard_stats_still_works(self):
        """GET /api/dashboard/stats should still work"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
        
        data = response.json()
        assert "total_articles" in data, f"Missing 'total_articles'. Got: {data.keys()}"
        print(f"PASS: Dashboard stats still works - total_articles={data.get('total_articles')}")
    
    def test_dashboard_all_still_works(self):
        """GET /api/dashboard/all should still work"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/all",
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
        
        data = response.json()
        assert "stats" in data, f"Missing 'stats'. Got: {data.keys()}"
        print("PASS: Dashboard all still works")
    
    def test_settings_still_works(self):
        """GET /api/settings should still work"""
        response = requests.get(
            f"{BASE_URL}/api/settings",
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
        
        data = response.json()
        assert "company_name" in data, f"Missing 'company_name'. Got: {data.keys()}"
        print(f"PASS: Settings still works - company_name={data.get('company_name')}")
    
    def test_pagespeed_all_sites_still_works(self):
        """GET /api/pagespeed/all-sites should still work"""
        response = requests.get(
            f"{BASE_URL}/api/pagespeed/all-sites",
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
        
        data = response.json()
        assert "sites" in data, f"Missing 'sites'. Got: {data.keys()}"
        print(f"PASS: Pagespeed all-sites still works - {len(data['sites'])} sites")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
