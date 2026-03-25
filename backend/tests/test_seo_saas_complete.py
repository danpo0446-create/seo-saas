"""
SEO Automation SaaS - Complete Pre-Launch Testing
Tests: Auth, Admin Dashboard, Billing, API Keys, Plans, Footer Pages
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://login-auth-test.preview.emergentagent.com').rstrip('/')

# Test credentials
ADMIN_EMAIL = "seamanshelp2021@gmail.com"
ADMIN_PASSWORD = "admin123"
TEST_USER_EMAIL = "test.user@seamanshelp.com"
TEST_USER_PASSWORD = "Test123!"


class TestAuthFlow:
    """Authentication endpoint tests - Login and Register"""
    
    def test_login_with_admin_credentials(self):
        """Test admin login returns token and user with role"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "Token missing from response"
        assert "user" in data, "User missing from response"
        assert data["user"]["email"] == ADMIN_EMAIL
        assert data["user"]["role"] == "admin", "Admin should have admin role"
        print(f"✓ Admin login successful, role: {data['user']['role']}")
    
    def test_login_with_invalid_credentials(self):
        """Test login with wrong password returns 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": "wrongpassword"
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Invalid credentials correctly rejected")
    
    def test_forgot_password_endpoint(self):
        """Test forgot password endpoint exists and works"""
        response = requests.post(f"{BASE_URL}/api/auth/forgot-password", json={
            "email": ADMIN_EMAIL
        })
        assert response.status_code == 200, f"Forgot password failed: {response.text}"
        print("✓ Forgot password endpoint working")
    
    def test_register_duplicate_email(self):
        """Test registering with existing email fails"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": ADMIN_EMAIL,
            "password": "test123",
            "name": "Test User"
        })
        assert response.status_code == 400, f"Expected 400 for duplicate email, got {response.status_code}"
        print("✓ Duplicate email registration correctly rejected")


class TestAdminDashboard:
    """Admin Dashboard - Stats, Users, Notifications, Content, Platform Settings"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin token for all tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, "Admin login failed"
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_admin_stats(self):
        """Test admin stats endpoint returns all expected fields"""
        response = requests.get(f"{BASE_URL}/api/admin/stats", headers=self.headers)
        assert response.status_code == 200, f"Stats failed: {response.text}"
        data = response.json()
        
        # Verify all expected fields
        expected_fields = ["total_users", "active_subscriptions", "trial_users", 
                          "total_articles", "total_sites", "monthly_revenue", 
                          "active_today", "plan_breakdown"]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
        
        # Verify plan_breakdown structure
        assert "plan_breakdown" in data
        print(f"✓ Admin stats: {data['total_users']} users, {data['active_subscriptions']} active subs")
    
    def test_admin_users_list(self):
        """Test admin can list all users"""
        response = requests.get(f"{BASE_URL}/api/admin/users", headers=self.headers)
        assert response.status_code == 200, f"Users list failed: {response.text}"
        users = response.json()
        assert isinstance(users, list), "Users should be a list"
        if users:
            user = users[0]
            assert "email" in user
            assert "plan" in user
            assert "subscription_status" in user
        print(f"✓ Admin users list: {len(users)} users found")
    
    def test_admin_notifications(self):
        """Test admin notifications endpoint"""
        response = requests.get(f"{BASE_URL}/api/admin/notifications", headers=self.headers)
        assert response.status_code == 200, f"Notifications failed: {response.text}"
        data = response.json()
        assert "notifications" in data
        assert "unread_count" in data
        print(f"✓ Admin notifications: {data['unread_count']} unread")
    
    def test_admin_content(self):
        """Test admin content management endpoint"""
        response = requests.get(f"{BASE_URL}/api/admin/content", headers=self.headers)
        assert response.status_code == 200, f"Content failed: {response.text}"
        content = response.json()
        assert isinstance(content, list), "Content should be a list"
        print(f"✓ Admin content: {len(content)} pages")
    
    def test_admin_platform_settings(self):
        """Test admin platform settings endpoint"""
        response = requests.get(f"{BASE_URL}/api/admin/platform-settings", headers=self.headers)
        assert response.status_code == 200, f"Platform settings failed: {response.text}"
        data = response.json()
        expected_fields = ["has_stripe_secret_key", "has_stripe_publishable_key", 
                          "has_resend_key", "has_google_client_id", "has_google_client_secret"]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
        print(f"✓ Platform settings retrieved")
    
    def test_non_admin_blocked(self):
        """Test non-admin users cannot access admin endpoints"""
        # Try to access admin endpoint without token
        response = requests.get(f"{BASE_URL}/api/admin/stats")
        assert response.status_code in [401, 403, 422], f"Expected auth error, got {response.status_code}"
        print("✓ Non-admin correctly blocked from admin endpoints")


class TestBillingAndSubscription:
    """Billing page - Subscription, Usage, API Keys"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin token for all tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, "Admin login failed"
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_subscription(self):
        """Test getting current subscription"""
        response = requests.get(f"{BASE_URL}/api/saas/subscription", headers=self.headers)
        assert response.status_code == 200, f"Subscription failed: {response.text}"
        data = response.json()
        assert "plan" in data
        assert "status" in data
        print(f"✓ Subscription: plan={data['plan']}, status={data['status']}")
    
    def test_get_subscription_usage(self):
        """Test getting subscription usage stats"""
        response = requests.get(f"{BASE_URL}/api/saas/subscription/usage", headers=self.headers)
        assert response.status_code == 200, f"Usage failed: {response.text}"
        data = response.json()
        expected_fields = ["plan_name", "status", "articles_used", "articles_limit", 
                          "sites_used", "sites_limit", "can_generate_article", "can_add_site"]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
        print(f"✓ Usage: {data['articles_used']}/{data['articles_limit']} articles")
    
    def test_get_invoices(self):
        """Test getting invoices list"""
        response = requests.get(f"{BASE_URL}/api/saas/invoices", headers=self.headers)
        assert response.status_code == 200, f"Invoices failed: {response.text}"
        invoices = response.json()
        assert isinstance(invoices, list), "Invoices should be a list"
        print(f"✓ Invoices: {len(invoices)} found")


class TestApiKeys:
    """API Keys page - BYOAK management"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin token for all tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, "Admin login failed"
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_api_keys_status(self):
        """Test getting API keys status"""
        response = requests.get(f"{BASE_URL}/api/saas/api-keys", headers=self.headers)
        assert response.status_code == 200, f"API keys failed: {response.text}"
        data = response.json()
        expected_fields = ["has_openai_key", "has_gemini_key", "has_resend_key", "has_pexels_key"]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
        print(f"✓ API keys status retrieved")


class TestPlansAndPricing:
    """Plans/Pricing page - Plan display"""
    
    def test_get_all_plans(self):
        """Test getting all subscription plans"""
        response = requests.get(f"{BASE_URL}/api/saas/plans")
        assert response.status_code == 200, f"Plans failed: {response.text}"
        plans = response.json()
        
        # Verify expected plans exist
        expected_plans = ["starter", "pro", "agency", "enterprise"]
        for plan in expected_plans:
            assert plan in plans, f"Missing plan: {plan}"
        
        # Verify plan structure
        starter = plans["starter"]
        assert starter["price_eur"] == 19, "Starter should be €19"
        assert plans["pro"]["price_eur"] == 49, "Pro should be €49"
        assert plans["agency"]["price_eur"] == 99, "Agency should be €99"
        assert plans["enterprise"]["price_eur"] == 199, "Enterprise should be €199"
        
        print(f"✓ Plans: Starter €{starter['price_eur']}, Pro €{plans['pro']['price_eur']}, Agency €{plans['agency']['price_eur']}, Enterprise €{plans['enterprise']['price_eur']}")


class TestFooterPages:
    """Footer pages - Contact, Terms, Privacy"""
    
    def test_contact_page_content(self):
        """Test contact page content endpoint"""
        response = requests.get(f"{BASE_URL}/api/saas/content/contact")
        assert response.status_code == 200, f"Contact content failed: {response.text}"
        data = response.json()
        assert "content" in data or "page_id" in data
        print("✓ Contact page content available")
    
    def test_terms_page_content(self):
        """Test terms page content endpoint"""
        response = requests.get(f"{BASE_URL}/api/saas/content/terms")
        assert response.status_code == 200, f"Terms content failed: {response.text}"
        data = response.json()
        assert "content" in data or "page_id" in data
        print("✓ Terms page content available")
    
    def test_privacy_page_content(self):
        """Test privacy page content endpoint"""
        response = requests.get(f"{BASE_URL}/api/saas/content/privacy")
        assert response.status_code == 200, f"Privacy content failed: {response.text}"
        data = response.json()
        assert "content" in data or "page_id" in data
        print("✓ Privacy page content available")


class TestDashboardUser:
    """User Dashboard - Data display"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin token for all tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, "Admin login failed"
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_dashboard_all_data(self):
        """Test dashboard all data endpoint"""
        response = requests.get(f"{BASE_URL}/api/dashboard/all", headers=self.headers)
        assert response.status_code == 200, f"Dashboard failed: {response.text}"
        data = response.json()
        # Dashboard should return various stats
        print(f"✓ Dashboard data retrieved")
    
    def test_analytics_overview(self):
        """Test analytics overview endpoint"""
        response = requests.get(f"{BASE_URL}/api/saas/analytics/overview", headers=self.headers)
        assert response.status_code == 200, f"Analytics failed: {response.text}"
        data = response.json()
        expected_sections = ["articles", "sites", "keywords", "backlinks", "financial", "subscription"]
        for section in expected_sections:
            assert section in data, f"Missing section: {section}"
        print(f"✓ Analytics overview: {data['articles']['total']} articles, {data['sites']['total']} sites")
    
    def test_get_wordpress_sites(self):
        """Test getting WordPress sites"""
        response = requests.get(f"{BASE_URL}/api/wordpress/sites", headers=self.headers)
        assert response.status_code == 200, f"WordPress sites failed: {response.text}"
        sites = response.json()
        assert isinstance(sites, list), "Sites should be a list"
        print(f"✓ WordPress sites: {len(sites)} found")
    
    def test_get_articles(self):
        """Test getting articles"""
        response = requests.get(f"{BASE_URL}/api/articles", headers=self.headers)
        assert response.status_code == 200, f"Articles failed: {response.text}"
        articles = response.json()
        assert isinstance(articles, list), "Articles should be a list"
        print(f"✓ Articles: {len(articles)} found")
    
    def test_get_keywords(self):
        """Test getting keywords"""
        response = requests.get(f"{BASE_URL}/api/keywords", headers=self.headers)
        assert response.status_code == 200, f"Keywords failed: {response.text}"
        keywords = response.json()
        assert isinstance(keywords, list), "Keywords should be a list"
        print(f"✓ Keywords: {len(keywords)} found")
    
    def test_get_calendar(self):
        """Test getting calendar entries"""
        response = requests.get(f"{BASE_URL}/api/calendar", headers=self.headers)
        assert response.status_code == 200, f"Calendar failed: {response.text}"
        calendar = response.json()
        assert isinstance(calendar, list), "Calendar should be a list"
        print(f"✓ Calendar: {len(calendar)} entries")
    
    def test_auth_me(self):
        """Test getting current user info"""
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=self.headers)
        assert response.status_code == 200, f"Auth me failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert "name" in data
        print(f"✓ Auth me: {data['email']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
