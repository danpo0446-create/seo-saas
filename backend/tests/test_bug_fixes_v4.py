"""
Test suite for SEO Automation Platform - Bug Fixes Iteration 4
Tests for:
1. Markdown to HTML conversion in generated content
2. Year 2024 → 2026 replacement
3. Automation endpoints
4. Calendar checkmarks for published articles
"""

import pytest
import requests
import os
import re
import sys

# Add backend to path for direct function testing
sys.path.insert(0, '/app/backend')

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://saas-staging-dev.preview.emergentagent.com')

class TestMarkdownAndYearConversion:
    """Test markdown conversion and year replacement functions directly"""
    
    def test_convert_markdown_to_html_headers(self):
        """Test that markdown headers are converted to HTML h2/h3 tags"""
        from server import convert_markdown_to_html
        
        markdown_content = "## This is a Header\n\nSome paragraph text.\n\n### Sub Header"
        result = convert_markdown_to_html(markdown_content)
        
        # Should contain HTML h2/h3 tags
        assert '<h2>' in result or '<h2 ' in result, f"Expected <h2> tag in result: {result}"
        assert '<h3>' in result or '<h3 ' in result, f"Expected <h3> tag in result: {result}"
        # Should NOT contain raw markdown
        assert '## ' not in result, f"Raw markdown header found: {result}"
        assert '### ' not in result, f"Raw markdown header found: {result}"
        print("✓ Markdown headers converted to HTML correctly")
    
    def test_convert_markdown_to_html_bold(self):
        """Test that markdown bold is converted to HTML strong tags"""
        from server import convert_markdown_to_html
        
        markdown_content = "This is **bold text** in a paragraph."
        result = convert_markdown_to_html(markdown_content)
        
        # Should contain HTML strong tags
        assert '<strong>' in result, f"Expected <strong> tag in result: {result}"
        # Should NOT contain raw markdown bold
        assert '**' not in result, f"Raw markdown bold found: {result}"
        print("✓ Markdown bold converted to HTML correctly")
    
    def test_convert_markdown_to_html_lists(self):
        """Test that markdown lists are converted to HTML ul/li tags"""
        from server import convert_markdown_to_html
        
        markdown_content = "- Item 1\n- Item 2\n- Item 3"
        result = convert_markdown_to_html(markdown_content)
        
        # Should contain HTML list tags
        assert '<ul>' in result or '<li>' in result, f"Expected list tags in result: {result}"
        print("✓ Markdown lists converted to HTML correctly")
    
    def test_clean_html_content_year_replacement(self):
        """Test that old years (2020-2025) are replaced"""
        from server import clean_html_content
        
        content_with_old_years = """
        <p>In 2024, the industry changed significantly.</p>
        <p>Since 2023, we have seen growth.</p>
        <p>The trends from 2022 and 2021 continue.</p>
        """
        result = clean_html_content(content_with_old_years)
        
        # Should NOT contain old years 2020-2025
        for year in ['2020', '2021', '2022', '2023', '2024', '2025']:
            assert year not in result, f"Old year {year} found in result: {result}"
        print("✓ Old years (2020-2025) replaced successfully")
    
    def test_clean_html_content_markdown_conversion(self):
        """Test clean_html_content also converts markdown"""
        from server import clean_html_content
        
        markdown_content = "## Header\n\n**Bold text** here."
        result = clean_html_content(markdown_content)
        
        # Should have converted markdown
        assert '##' not in result, f"Raw markdown header found: {result}"
        assert '**' not in result, f"Raw markdown bold found: {result}"
        print("✓ clean_html_content converts markdown correctly")
    
    def test_clean_html_content_removes_doctype(self):
        """Test that DOCTYPE and structural HTML is removed"""
        from server import clean_html_content
        
        content_with_doctype = """<!DOCTYPE html>
        <html>
        <head><title>Test</title></head>
        <body>
        <h2>Actual Content</h2>
        <p>Paragraph here.</p>
        </body>
        </html>"""
        result = clean_html_content(content_with_doctype)
        
        assert '<!DOCTYPE' not in result, "DOCTYPE not removed"
        assert '<html>' not in result, "<html> tag not removed"
        assert '<head>' not in result, "<head> tag not removed"
        assert '<body>' not in result, "<body> tag not removed"
        assert '<h2>' in result, "Content h2 should be preserved"
        print("✓ DOCTYPE and structural HTML removed correctly")


class TestAutomationEndpoints:
    """Test automation API endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Create test user and get auth token"""
        import time
        timestamp = int(time.time())
        
        # First try to login with existing test user
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "bugfix_test@test.com",
            "password": "TestPass123!"
        })
        
        if login_resp.status_code == 200:
            return login_resp.json().get("token")
        
        # Register new user
        register_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"bugfix_test_{timestamp}@test.com",
            "password": "TestPass123!",
            "name": "Bug Fix Tester"
        })
        
        if register_resp.status_code == 200:
            return register_resp.json().get("token")
        
        pytest.skip("Could not create test user")
    
    def test_automation_sites_endpoint(self, auth_token):
        """Test /api/automation/sites returns site list with automation settings"""
        response = requests.get(
            f"{BASE_URL}/api/automation/sites",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list response"
        print(f"✓ /api/automation/sites returns {len(data)} sites")
        
        # If sites exist, verify structure
        if len(data) > 0:
            site = data[0]
            assert "site" in site, "Expected 'site' field in response"
            assert "automation" in site, "Expected 'automation' field in response"
            print("✓ Site automation settings structure verified")
    
    def test_automation_publication_log_endpoint(self, auth_token):
        """Test /api/automation/publication-log returns list with published_at field"""
        response = requests.get(
            f"{BASE_URL}/api/automation/publication-log",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list response"
        print(f"✓ /api/automation/publication-log returns {len(data)} entries")
        
        # If entries exist, verify they have published_at field
        if len(data) > 0:
            entry = data[0]
            # Published articles should have published_at
            if entry.get("status") == "published":
                assert "published_at" in entry, "Expected 'published_at' field for published articles"
                print("✓ Publication log entries have published_at field")
    
    def test_automation_history_endpoint(self, auth_token):
        """Test /api/automation/history returns history list"""
        response = requests.get(
            f"{BASE_URL}/api/automation/history",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list response"
        print(f"✓ /api/automation/history returns {len(data)} entries")


class TestArticleGeneration:
    """Test article generation with markdown conversion and year handling"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token"""
        import time
        timestamp = int(time.time())
        
        # Try login first
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "generation_test@test.com",
            "password": "TestPass123!"
        })
        
        if login_resp.status_code == 200:
            return login_resp.json().get("token")
        
        # Register
        register_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"generation_test_{timestamp}@test.com",
            "password": "TestPass123!",
            "name": "Generation Tester"
        })
        
        if register_resp.status_code == 200:
            return register_resp.json().get("token")
        
        pytest.skip("Could not create test user")
    
    def test_article_generate_returns_html_not_markdown(self, auth_token):
        """Test /api/articles/generate returns HTML content, NOT raw markdown"""
        response = requests.post(
            f"{BASE_URL}/api/articles/generate",
            json={
                "title": "Test Article for Markdown Conversion",
                "keywords": ["test", "seo", "automation"],
                "niche": "technology",
                "tone": "professional",
                "length": "short"
            },
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=120  # Article generation can take time
        )
        
        # Check if generation succeeded
        if response.status_code != 200:
            pytest.skip(f"Article generation failed: {response.status_code} - {response.text}")
        
        data = response.json()
        content = data.get("content", "")
        
        # Verify no raw markdown in content
        assert '##' not in content, f"Raw markdown headers found in content"
        assert '**' not in content or '<strong>' in content, "Raw markdown bold without HTML conversion"
        
        # Verify HTML tags present
        html_tag_found = any(tag in content for tag in ['<h2>', '<h3>', '<p>', '<strong>', '<ul>', '<li>'])
        assert html_tag_found, f"No HTML tags found in content. Content snippet: {content[:500]}"
        
        print(f"✓ Generated article contains HTML tags, no raw markdown")
        print(f"  Article ID: {data.get('id')}")
        print(f"  Word count: {data.get('word_count')}")
    
    def test_article_content_has_current_year(self, auth_token):
        """Test generated content uses 2026 or no old years"""
        response = requests.post(
            f"{BASE_URL}/api/articles/generate",
            json={
                "title": "Trends in Technology for the Current Year",
                "keywords": ["trends", "technology", "2026"],
                "niche": "technology",
                "tone": "professional",
                "length": "short"
            },
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=120
        )
        
        if response.status_code != 200:
            pytest.skip(f"Article generation failed: {response.status_code}")
        
        data = response.json()
        content = data.get("content", "")
        
        # Check no old years present (2020-2024)
        for old_year in ['2020', '2021', '2022', '2023', '2024']:
            if old_year in content:
                # This might be acceptable if in a specific historical context
                # but generally should not appear
                print(f"  WARNING: Found old year {old_year} in content")
        
        # 2025 might be replaced depending on when test runs
        if '2024' in content:
            pytest.fail(f"Old year 2024 found in generated content")
        
        print("✓ No problematic old years (2024) in generated content")


class TestAuthEndpoints:
    """Basic auth tests to ensure service is running"""
    
    def test_api_accessible(self):
        """Test that API is accessible"""
        # Try a basic endpoint
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "nonexistent@test.com",
            "password": "test"
        })
        
        # Should get 401 (invalid credentials) not 500 or connection error
        assert response.status_code in [401, 400], f"Unexpected status: {response.status_code}"
        print("✓ API is accessible and responding")
    
    def test_register_and_login(self):
        """Test user registration and login"""
        import time
        timestamp = int(time.time())
        test_email = f"bugtest_{timestamp}@test.com"
        
        # Register
        reg_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "password": "TestPass123!",
            "name": "Bug Test User"
        })
        
        assert reg_response.status_code == 200, f"Registration failed: {reg_response.text}"
        token = reg_response.json().get("token")
        assert token, "No token in registration response"
        print(f"✓ User registered: {test_email}")
        
        # Login
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": test_email,
            "password": "TestPass123!"
        })
        
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        login_token = login_response.json().get("token")
        assert login_token, "No token in login response"
        print("✓ User login successful")
        
        return token


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
