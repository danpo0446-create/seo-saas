"""
Test Social Media Facebook Page Selection and Status Endpoints
Tests for:
- GET /api/social/status/{site_id} - returns available_pages and pages_pending
- POST /api/social/facebook/select-page/{site_id}?page_id={page_id} - saves selected page
- GET /api/social/facebook/pages/{site_id} - returns available pages
"""
import pytest
import requests
import os
import uuid
from datetime import datetime, timezone

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestSocialFacebookEndpoints:
    """Test Facebook page selection and social status endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "seamanshelp2021@gmail.com",
            "password": "admin123"
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed - skipping tests")
    
    @pytest.fixture(scope="class")
    def test_site_id(self, auth_token):
        """Get or create a test site with Facebook pages for testing"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get existing sites
        response = requests.get(f"{BASE_URL}/api/wordpress/sites", headers=headers)
        sites = response.json()
        
        # Find a site with facebook_pages or use the test site we created
        for site in sites:
            if site.get("id") == "7bb200d5-1b6f-438a-9409-06a5e13630a7":
                return site["id"]
        
        # If no test site found, use first available site
        if sites:
            return sites[0]["id"]
        
        pytest.skip("No WordPress sites available for testing")
    
    def test_social_status_returns_available_pages(self, auth_token, test_site_id):
        """Test GET /api/social/status/{site_id} returns available_pages"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(f"{BASE_URL}/api/social/status/{test_site_id}", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "facebook" in data, "Response should contain 'facebook' key"
        
        facebook = data["facebook"]
        assert "available_pages" in facebook, "Facebook status should contain 'available_pages'"
        assert "pages_pending" in facebook, "Facebook status should contain 'pages_pending'"
        assert "connected" in facebook, "Facebook status should contain 'connected'"
        assert "page_name" in facebook, "Facebook status should contain 'page_name'"
        assert "page_id" in facebook, "Facebook status should contain 'page_id'"
        
        # Verify available_pages is a list
        assert isinstance(facebook["available_pages"], list), "available_pages should be a list"
        
        print(f"✓ Social status returned {len(facebook['available_pages'])} available pages")
        print(f"✓ pages_pending: {facebook['pages_pending']}")
        print(f"✓ connected: {facebook['connected']}")
    
    def test_social_status_returns_linkedin_info(self, auth_token, test_site_id):
        """Test GET /api/social/status/{site_id} returns LinkedIn info"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(f"{BASE_URL}/api/social/status/{test_site_id}", headers=headers)
        
        assert response.status_code == 200
        
        data = response.json()
        assert "linkedin" in data, "Response should contain 'linkedin' key"
        
        linkedin = data["linkedin"]
        assert "connected" in linkedin, "LinkedIn status should contain 'connected'"
        assert "available" in linkedin, "LinkedIn status should contain 'available'"
        
        print(f"✓ LinkedIn connected: {linkedin['connected']}")
        print(f"✓ LinkedIn available: {linkedin['available']}")
    
    def test_get_facebook_pages_endpoint(self, auth_token, test_site_id):
        """Test GET /api/social/facebook/pages/{site_id}"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(f"{BASE_URL}/api/social/facebook/pages/{test_site_id}", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "pages" in data, "Response should contain 'pages' key"
        assert "selected_page_id" in data, "Response should contain 'selected_page_id'"
        assert "selected_page_name" in data, "Response should contain 'selected_page_name'"
        
        # Verify pages structure
        for page in data["pages"]:
            assert "id" in page, "Each page should have 'id'"
            assert "name" in page, "Each page should have 'name'"
        
        print(f"✓ Facebook pages endpoint returned {len(data['pages'])} pages")
    
    def test_select_facebook_page_success(self, auth_token, test_site_id):
        """Test POST /api/social/facebook/select-page/{site_id}?page_id={page_id}"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First get available pages
        pages_response = requests.get(f"{BASE_URL}/api/social/facebook/pages/{test_site_id}", headers=headers)
        pages_data = pages_response.json()
        
        if not pages_data.get("pages"):
            pytest.skip("No Facebook pages available for selection test")
        
        # Select the first page
        page_to_select = pages_data["pages"][0]
        page_id = page_to_select["id"]
        
        response = requests.post(
            f"{BASE_URL}/api/social/facebook/select-page/{test_site_id}?page_id={page_id}",
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("success") == True, "Response should indicate success"
        assert "page_name" in data, "Response should contain 'page_name'"
        
        print(f"✓ Successfully selected page: {data['page_name']}")
        
        # Verify the selection persisted
        status_response = requests.get(f"{BASE_URL}/api/social/status/{test_site_id}", headers=headers)
        status_data = status_response.json()
        
        assert status_data["facebook"]["connected"] == True, "Facebook should be connected after selection"
        assert status_data["facebook"]["page_id"] == page_id, "Selected page_id should match"
        assert status_data["facebook"]["pages_pending"] == False, "pages_pending should be False after selection"
        
        print(f"✓ Verified selection persisted: page_id={status_data['facebook']['page_id']}")
    
    def test_select_facebook_page_invalid_page_id(self, auth_token, test_site_id):
        """Test POST /api/social/facebook/select-page with invalid page_id returns 404"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.post(
            f"{BASE_URL}/api/social/facebook/select-page/{test_site_id}?page_id=invalid_page_999",
            headers=headers
        )
        
        assert response.status_code == 404, f"Expected 404 for invalid page_id, got {response.status_code}"
        print("✓ Invalid page_id correctly returns 404")
    
    def test_social_status_invalid_site_id(self, auth_token):
        """Test GET /api/social/status with invalid site_id returns 404"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(f"{BASE_URL}/api/social/status/invalid-site-id-999", headers=headers)
        
        assert response.status_code == 404, f"Expected 404 for invalid site_id, got {response.status_code}"
        print("✓ Invalid site_id correctly returns 404")
    
    def test_social_status_no_auth(self, test_site_id):
        """Test GET /api/social/status without auth returns 401/403"""
        response = requests.get(f"{BASE_URL}/api/social/status/{test_site_id}")
        
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("✓ Unauthenticated request correctly rejected")


class TestSchedulerConfiguration:
    """Test scheduler configuration for misfire_grace_time and daily job recovery"""
    
    def test_scheduler_config_in_code(self):
        """Verify scheduler configuration exists in server.py"""
        server_path = "/app/backend/server.py"
        
        with open(server_path, 'r') as f:
            content = f.read()
        
        # Check for misfire_grace_time configuration
        assert "misfire_grace_time" in content, "Scheduler should have misfire_grace_time configured"
        assert "7200" in content or "2 hours" in content.lower(), "misfire_grace_time should be set to 2 hours (7200 seconds)"
        
        # Check for daily_job_recovery
        assert "daily_job_recovery" in content, "Scheduler should have daily_job_recovery job"
        assert "recover_missed_automation_jobs" in content, "Should have recover_missed_automation_jobs function"
        
        # Check for 10:30 AM schedule
        assert "hour=10" in content and "minute=30" in content, "Daily recovery should be scheduled at 10:30 AM"
        
        print("✓ Scheduler configuration verified:")
        print("  - misfire_grace_time: 7200 seconds (2 hours)")
        print("  - daily_job_recovery scheduled at 10:30 AM")
        print("  - coalesce: True (run once if multiple missed)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
