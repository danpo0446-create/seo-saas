import requests
import sys
import json
from datetime import datetime

class SEOPlatformAPITester:
    def __init__(self, base_url="https://seo-automation-ro-1.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.user_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=test_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Response: {response.text[:200]}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_register(self):
        """Test user registration"""
        timestamp = datetime.now().strftime('%H%M%S')
        test_user = {
            "email": f"test{timestamp}@example.com",
            "password": "test123",
            "name": f"Test User {timestamp}"
        }
        
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data=test_user
        )
        
        if success and 'token' in response:
            self.token = response['token']
            self.user_id = response.get('user', {}).get('id')
            return True, test_user
        return False, test_user

    def test_login(self, user_data):
        """Test user login"""
        success, response = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            data={"email": user_data["email"], "password": user_data["password"]}
        )
        
        if success and 'token' in response:
            self.token = response['token']
            return True
        return False

    def test_get_me(self):
        """Test get current user"""
        success, _ = self.run_test(
            "Get Current User",
            "GET",
            "auth/me",
            200
        )
        return success

    def test_dashboard_stats(self):
        """Test dashboard stats"""
        success, _ = self.run_test(
            "Dashboard Stats",
            "GET",
            "dashboard/stats",
            200
        )
        return success

    def test_search_console_stats(self):
        """Test search console stats (mocked)"""
        success, _ = self.run_test(
            "Search Console Stats",
            "GET",
            "search-console/stats",
            200
        )
        return success

    def test_generate_article(self):
        """Test article generation"""
        article_data = {
            "title": "Test SEO Article",
            "keywords": ["seo", "content", "marketing"],
            "niche": "Digital Marketing",
            "tone": "professional",
            "length": "medium"
        }
        
        success, response = self.run_test(
            "Generate Article",
            "POST",
            "articles/generate",
            200,
            data=article_data
        )
        
        if success and 'id' in response:
            return True, response['id']
        return False, None

    def test_get_articles(self):
        """Test get articles list"""
        success, _ = self.run_test(
            "Get Articles",
            "GET",
            "articles",
            200
        )
        return success

    def test_keyword_research(self):
        """Test keyword research"""
        research_data = {
            "niche": "Digital Marketing",
            "seed_keywords": ["seo", "content"]
        }
        
        success, _ = self.run_test(
            "Keyword Research",
            "POST",
            "keywords/research",
            200,
            data=research_data
        )
        return success

    def test_get_keywords(self):
        """Test get keywords"""
        success, _ = self.run_test(
            "Get Keywords",
            "GET",
            "keywords",
            200
        )
        return success

    def test_create_calendar_entry(self):
        """Test create calendar entry"""
        entry_data = {
            "title": "Test Article",
            "keywords": ["test", "seo"],
            "scheduled_date": "2024-12-20",
            "status": "planned"
        }
        
        success, response = self.run_test(
            "Create Calendar Entry",
            "POST",
            "calendar",
            200,
            data=entry_data
        )
        
        if success and 'id' in response:
            return True, response['id']
        return False, None

    def test_generate_90_day_calendar(self):
        """Test 90-day calendar generation"""
        success, _ = self.run_test(
            "Generate 90-Day Calendar",
            "POST",
            "calendar/generate-90-days?niche=Digital Marketing",
            200
        )
        return success

    def test_get_calendar(self):
        """Test get calendar entries"""
        success, _ = self.run_test(
            "Get Calendar",
            "GET",
            "calendar",
            200
        )
        return success

    def test_get_backlinks(self):
        """Test get backlink sites"""
        success, _ = self.run_test(
            "Get Backlink Sites",
            "GET",
            "backlinks",
            200
        )
        return success

    def test_request_backlink(self):
        """Test request backlink"""
        # First get backlinks to get a site ID
        success, sites = self.run_test(
            "Get Backlinks for Request",
            "GET",
            "backlinks",
            200
        )
        
        if success and sites and len(sites) > 0:
            site_id = sites[0]['id']
            success, _ = self.run_test(
                "Request Backlink",
                "POST",
                f"backlinks/request/{site_id}",
                200
            )
            return success
        return False

    def test_get_backlink_requests(self):
        """Test get backlink requests"""
        success, _ = self.run_test(
            "Get Backlink Requests",
            "GET",
            "backlinks/requests",
            200
        )
        return success

    def test_wordpress_connect(self):
        """Test WordPress connection"""
        wp_config = {
            "site_url": "https://example.com",
            "username": "testuser",
            "app_password": "test-password"
        }
        
        success, _ = self.run_test(
            "WordPress Connect",
            "POST",
            "wordpress/connect",
            200,
            data=wp_config
        )
        return success

    def test_get_wordpress_config(self):
        """Test get WordPress config"""
        success, _ = self.run_test(
            "Get WordPress Config",
            "GET",
            "wordpress/config",
            200
        )
        return success

    def test_get_settings(self):
        """Test get settings"""
        success, _ = self.run_test(
            "Get Settings",
            "GET",
            "settings",
            200
        )
        return success

    def test_update_settings(self):
        """Test update settings"""
        settings_data = {
            "company_name": "Test SEO Agency",
            "primary_color": "#FF5722",
            "email_notifications": True
        }
        
        success, _ = self.run_test(
            "Update Settings",
            "PATCH",
            "settings",
            200,
            data=settings_data
        )
        return success

def main():
    print("🚀 Starting SEO Automation Platform API Tests")
    print("=" * 60)
    
    tester = SEOPlatformAPITester()
    
    # Test authentication flow
    print("\n📝 AUTHENTICATION TESTS")
    print("-" * 30)
    
    reg_success, user_data = tester.test_register()
    if not reg_success:
        print("❌ Registration failed, stopping tests")
        return 1
    
    login_success = tester.test_login(user_data)
    if not login_success:
        print("❌ Login failed, stopping tests")
        return 1
    
    tester.test_get_me()
    
    # Test dashboard
    print("\n📊 DASHBOARD TESTS")
    print("-" * 30)
    tester.test_dashboard_stats()
    tester.test_search_console_stats()
    
    # Test articles
    print("\n📄 ARTICLES TESTS")
    print("-" * 30)
    article_success, article_id = tester.test_generate_article()
    tester.test_get_articles()
    
    # Test keywords
    print("\n🔍 KEYWORDS TESTS")
    print("-" * 30)
    tester.test_keyword_research()
    tester.test_get_keywords()
    
    # Test calendar
    print("\n📅 CALENDAR TESTS")
    print("-" * 30)
    entry_success, entry_id = tester.test_create_calendar_entry()
    tester.test_generate_90_day_calendar()
    tester.test_get_calendar()
    
    # Test backlinks
    print("\n🔗 BACKLINKS TESTS")
    print("-" * 30)
    tester.test_get_backlinks()
    tester.test_request_backlink()
    tester.test_get_backlink_requests()
    
    # Test WordPress
    print("\n🌐 WORDPRESS TESTS")
    print("-" * 30)
    tester.test_wordpress_connect()
    tester.test_get_wordpress_config()
    
    # Test settings
    print("\n⚙️ SETTINGS TESTS")
    print("-" * 30)
    tester.test_get_settings()
    tester.test_update_settings()
    
    # Print results
    print("\n" + "=" * 60)
    print(f"📊 FINAL RESULTS")
    print(f"Tests passed: {tester.tests_passed}/{tester.tests_run}")
    success_rate = (tester.tests_passed / tester.tests_run) * 100 if tester.tests_run > 0 else 0
    print(f"Success rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("✅ Backend API tests mostly successful!")
        return 0
    else:
        print("❌ Backend API tests have significant failures")
        return 1

if __name__ == "__main__":
    sys.exit(main())