"""
Phase 3 Routes Testing - Articles, Keywords, Calendar, Reports CRUD
Tests the refactored routes extracted from server.py to /app/backend/routes/
"""
import pytest
import requests
import os
import uuid
from datetime import datetime, timedelta

# Get BASE_URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    raise ValueError("REACT_APP_BACKEND_URL environment variable not set")

# Test credentials
TEST_EMAIL = "seamanshelp2021@gmail.com"
TEST_PASSWORD = "admin123"


class TestAuth:
    """Authentication tests - get token for subsequent tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in response"
        return data["token"]
    
    def test_login_success(self):
        """Test login returns token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data


class TestArticlesRoutes:
    """Test /api/articles CRUD routes (Phase 3)"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers for requests"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_articles_requires_auth(self):
        """GET /api/articles requires authentication"""
        response = requests.get(f"{BASE_URL}/api/articles")
        assert response.status_code == 403 or response.status_code == 401
    
    def test_get_articles_list(self, auth_headers):
        """GET /api/articles returns list of articles"""
        response = requests.get(f"{BASE_URL}/api/articles", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} articles")
    
    def test_get_articles_with_site_filter(self, auth_headers):
        """GET /api/articles?site_id=xxx filters by site"""
        # First get all articles to find a site_id
        response = requests.get(f"{BASE_URL}/api/articles", headers=auth_headers)
        assert response.status_code == 200
        articles = response.json()
        
        if articles and articles[0].get("site_id"):
            site_id = articles[0]["site_id"]
            response = requests.get(
                f"{BASE_URL}/api/articles?site_id={site_id}",
                headers=auth_headers
            )
            assert response.status_code == 200
            filtered = response.json()
            assert isinstance(filtered, list)
            print(f"Filtered articles for site {site_id}: {len(filtered)}")
    
    def test_get_single_article(self, auth_headers):
        """GET /api/articles/{id} returns single article"""
        # First get list to find an article ID
        response = requests.get(f"{BASE_URL}/api/articles", headers=auth_headers)
        articles = response.json()
        
        if articles:
            article_id = articles[0]["id"]
            response = requests.get(
                f"{BASE_URL}/api/articles/{article_id}",
                headers=auth_headers
            )
            assert response.status_code == 200
            article = response.json()
            assert article["id"] == article_id
            assert "title" in article
            assert "content" in article
            print(f"Got article: {article['title'][:50]}...")
        else:
            pytest.skip("No articles found to test single article GET")
    
    def test_get_nonexistent_article(self, auth_headers):
        """GET /api/articles/{id} returns 404 for non-existent article"""
        fake_id = str(uuid.uuid4())
        response = requests.get(
            f"{BASE_URL}/api/articles/{fake_id}",
            headers=auth_headers
        )
        assert response.status_code == 404
    
    def test_update_article(self, auth_headers):
        """PUT /api/articles/{id} updates article"""
        # First get list to find an article ID
        response = requests.get(f"{BASE_URL}/api/articles", headers=auth_headers)
        articles = response.json()
        
        if articles:
            article_id = articles[0]["id"]
            original_title = articles[0]["title"]
            
            # Update with same title (to not break anything)
            response = requests.put(
                f"{BASE_URL}/api/articles/{article_id}",
                headers=auth_headers,
                json={"title": original_title, "status": "draft"}
            )
            assert response.status_code == 200
            updated = response.json()
            assert updated["id"] == article_id
            print(f"Updated article: {updated['title'][:50]}...")
        else:
            pytest.skip("No articles found to test update")
    
    def test_update_nonexistent_article(self, auth_headers):
        """PUT /api/articles/{id} returns 404 for non-existent article"""
        fake_id = str(uuid.uuid4())
        response = requests.put(
            f"{BASE_URL}/api/articles/{fake_id}",
            headers=auth_headers,
            json={"title": "Test Title"}
        )
        assert response.status_code == 404
    
    def test_delete_nonexistent_article(self, auth_headers):
        """DELETE /api/articles/{id} returns 404 for non-existent article"""
        fake_id = str(uuid.uuid4())
        response = requests.delete(
            f"{BASE_URL}/api/articles/{fake_id}",
            headers=auth_headers
        )
        assert response.status_code == 404


class TestKeywordsRoutes:
    """Test /api/keywords CRUD routes (Phase 3)"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers for requests"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_keywords_requires_auth(self):
        """GET /api/keywords requires authentication"""
        response = requests.get(f"{BASE_URL}/api/keywords")
        assert response.status_code == 403 or response.status_code == 401
    
    def test_get_keywords_list(self, auth_headers):
        """GET /api/keywords returns list of keywords"""
        response = requests.get(f"{BASE_URL}/api/keywords", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} keywords")
    
    def test_get_keywords_with_site_filter(self, auth_headers):
        """GET /api/keywords?site_id=xxx filters by site"""
        response = requests.get(f"{BASE_URL}/api/keywords", headers=auth_headers)
        keywords = response.json()
        
        if keywords and keywords[0].get("site_id"):
            site_id = keywords[0]["site_id"]
            response = requests.get(
                f"{BASE_URL}/api/keywords?site_id={site_id}",
                headers=auth_headers
            )
            assert response.status_code == 200
            filtered = response.json()
            assert isinstance(filtered, list)
            print(f"Filtered keywords for site {site_id}: {len(filtered)}")
    
    def test_delete_nonexistent_keyword(self, auth_headers):
        """DELETE /api/keywords/{id} returns 404 for non-existent keyword"""
        fake_id = str(uuid.uuid4())
        response = requests.delete(
            f"{BASE_URL}/api/keywords/{fake_id}",
            headers=auth_headers
        )
        assert response.status_code == 404


class TestCalendarRoutes:
    """Test /api/calendar CRUD routes (Phase 3)"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers for requests"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_calendar_requires_auth(self):
        """GET /api/calendar requires authentication"""
        response = requests.get(f"{BASE_URL}/api/calendar")
        assert response.status_code == 403 or response.status_code == 401
    
    def test_get_calendar_list(self, auth_headers):
        """GET /api/calendar returns list of calendar entries"""
        response = requests.get(f"{BASE_URL}/api/calendar", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} calendar entries")
    
    def test_create_calendar_entry(self, auth_headers):
        """POST /api/calendar creates new calendar entry"""
        test_entry = {
            "title": f"TEST_Calendar_Entry_{uuid.uuid4().hex[:8]}",
            "keywords": ["test", "keyword"],
            "scheduled_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "status": "planned"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/calendar",
            headers=auth_headers,
            json=test_entry
        )
        assert response.status_code == 200
        created = response.json()
        assert "id" in created
        assert created["title"] == test_entry["title"]
        assert created["keywords"] == test_entry["keywords"]
        print(f"Created calendar entry: {created['id']}")
        
        # Cleanup - delete the test entry
        delete_response = requests.delete(
            f"{BASE_URL}/api/calendar/{created['id']}",
            headers=auth_headers
        )
        assert delete_response.status_code == 200
        print(f"Cleaned up test entry: {created['id']}")
    
    def test_delete_nonexistent_calendar_entry(self, auth_headers):
        """DELETE /api/calendar/{id} returns 404 for non-existent entry"""
        fake_id = str(uuid.uuid4())
        response = requests.delete(
            f"{BASE_URL}/api/calendar/{fake_id}",
            headers=auth_headers
        )
        assert response.status_code == 404


class TestReportsRoutes:
    """Test /api/reports routes (Phase 3)"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers for requests"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_weekly_report_requires_auth(self):
        """GET /api/reports/weekly requires authentication"""
        response = requests.get(f"{BASE_URL}/api/reports/weekly")
        assert response.status_code == 403 or response.status_code == 401
    
    def test_monthly_report_requires_auth(self):
        """GET /api/reports/monthly requires authentication"""
        response = requests.get(f"{BASE_URL}/api/reports/monthly")
        assert response.status_code == 403 or response.status_code == 401
    
    def test_get_weekly_report(self, auth_headers):
        """GET /api/reports/weekly returns weekly report data"""
        response = requests.get(
            f"{BASE_URL}/api/reports/weekly",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify report structure
        assert "period" in data
        assert "summary" in data
        assert data["period"]["days"] == 7
        
        # Verify summary fields
        summary = data["summary"]
        assert "total_articles" in summary
        assert "published" in summary
        assert "drafts" in summary
        print(f"Weekly report: {summary['total_articles']} articles, {summary['published']} published")
    
    def test_get_monthly_report(self, auth_headers):
        """GET /api/reports/monthly returns monthly report data"""
        response = requests.get(
            f"{BASE_URL}/api/reports/monthly",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify report structure
        assert "period" in data
        assert "summary" in data
        assert data["period"]["days"] == 30
        
        # Verify summary fields
        summary = data["summary"]
        assert "total_articles" in summary
        assert "published" in summary
        assert "drafts" in summary
        assert "avg_seo_score" in summary
        print(f"Monthly report: {summary['total_articles']} articles, avg SEO score: {summary['avg_seo_score']}")


class TestPreviousRoutesStillWork:
    """Verify Phase 1 and Phase 2 routes still work after Phase 3 refactoring"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers for requests"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_health_endpoint(self):
        """GET /api/health still works"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_dashboard_stats(self, auth_headers):
        """GET /api/dashboard/stats still works (Phase 1)"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=auth_headers
        )
        assert response.status_code == 200
    
    def test_settings(self, auth_headers):
        """GET /api/settings still works (Phase 1)"""
        response = requests.get(
            f"{BASE_URL}/api/settings",
            headers=auth_headers
        )
        assert response.status_code == 200
    
    def test_notifications(self, auth_headers):
        """GET /api/notifications still works (Phase 2)"""
        response = requests.get(
            f"{BASE_URL}/api/notifications",
            headers=auth_headers
        )
        assert response.status_code == 200
    
    def test_templates(self, auth_headers):
        """GET /api/templates still works (Phase 2)"""
        response = requests.get(
            f"{BASE_URL}/api/templates",
            headers=auth_headers
        )
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
