"""
Test Admin Dashboard Features - Backend API Tests
- Admin stats endpoint
- Admin users list endpoint
- Admin user role management
- Admin subscription management
- Admin user deletion
- Non-admin access restriction
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "seamanshelp2021@gmail.com"
ADMIN_PASSWORD = "admin123"
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "test123"


class TestAdminAuthentication:
    """Test admin login and role verification"""
    
    def test_admin_login(self):
        """Test admin user can login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        print(f"Admin login status: {response.status_code}")
        print(f"Admin login response: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        # Verify admin role is returned
        assert data["user"].get("role") == "admin", f"Expected role='admin', got {data['user'].get('role')}"
    
    def test_regular_user_login(self):
        """Test regular user can login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        print(f"Regular user login status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            assert "token" in data
            assert "user" in data
            # Regular user should have 'user' role or no role
            role = data["user"].get("role", "user")
            assert role != "admin", f"Regular user should not be admin, got role={role}"
        elif response.status_code == 401:
            pytest.skip("Test user not registered yet")


class TestAdminStatsEndpoint:
    """Test /api/admin/stats endpoint"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin login failed")
    
    @pytest.fixture
    def user_token(self):
        """Get regular user authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        return None
    
    def test_admin_can_access_stats(self, admin_token):
        """Admin should be able to access stats endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        print(f"Admin stats status: {response.status_code}")
        print(f"Admin stats response: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify all expected fields are present
        assert "total_users" in data
        assert "active_subscriptions" in data
        assert "trial_users" in data
        assert "total_articles" in data
        assert "total_sites" in data
        assert "monthly_revenue" in data
        assert "active_today" in data
        assert "plan_breakdown" in data
        
        # Verify data types
        assert isinstance(data["total_users"], int)
        assert isinstance(data["monthly_revenue"], (int, float))
        assert isinstance(data["plan_breakdown"], dict)
    
    def test_non_admin_cannot_access_stats(self, user_token):
        """Regular user should get 403 on stats endpoint"""
        if not user_token:
            pytest.skip("Test user not available")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        print(f"Non-admin stats status: {response.status_code}")
        
        assert response.status_code == 403
    
    def test_unauthenticated_cannot_access_stats(self):
        """Unauthenticated request should get 403/401"""
        response = requests.get(f"{BASE_URL}/api/admin/stats")
        print(f"Unauthenticated stats status: {response.status_code}")
        
        assert response.status_code in [401, 403]


class TestAdminUsersEndpoint:
    """Test /api/admin/users endpoint"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin login failed")
    
    @pytest.fixture
    def user_token(self):
        """Get regular user authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        return None
    
    def test_admin_can_list_users(self, admin_token):
        """Admin should be able to list all users"""
        response = requests.get(
            f"{BASE_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        print(f"Admin users list status: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Response should be a list
        assert isinstance(data, list)
        
        # If there are users, verify structure
        if len(data) > 0:
            user = data[0]
            assert "id" in user
            assert "email" in user
            assert "password" not in user  # Password should not be returned
            print(f"Found {len(data)} users")
            print(f"First user: {user.get('email')}, role: {user.get('role')}")
    
    def test_admin_users_search(self, admin_token):
        """Admin should be able to search users"""
        response = requests.get(
            f"{BASE_URL}/api/admin/users?search={ADMIN_EMAIL}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        print(f"Admin users search status: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Search result should contain the admin user
        if len(data) > 0:
            found_admin = any(u.get("email") == ADMIN_EMAIL for u in data)
            assert found_admin, f"Admin user {ADMIN_EMAIL} should be in search results"
    
    def test_non_admin_cannot_list_users(self, user_token):
        """Regular user should get 403 on users endpoint"""
        if not user_token:
            pytest.skip("Test user not available")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        print(f"Non-admin users list status: {response.status_code}")
        
        assert response.status_code == 403


class TestAdminUserActions:
    """Test admin actions on users (role toggle, subscription edit, delete)"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin login failed")
    
    @pytest.fixture
    def user_token(self):
        """Get regular user authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        return None
    
    @pytest.fixture
    def test_user_id(self, admin_token):
        """Get test user ID from admin users list"""
        response = requests.get(
            f"{BASE_URL}/api/admin/users?search={TEST_USER_EMAIL}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        if response.status_code == 200:
            users = response.json()
            for user in users:
                if user.get("email") == TEST_USER_EMAIL:
                    return user.get("id")
        return None
    
    def test_admin_can_update_user_subscription(self, admin_token, test_user_id):
        """Admin should be able to update user subscription"""
        if not test_user_id:
            pytest.skip("Test user not found")
        
        response = requests.patch(
            f"{BASE_URL}/api/admin/users/{test_user_id}/subscription",
            json={"plan": "pro", "status": "active"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        print(f"Update subscription status: {response.status_code}")
        print(f"Update subscription response: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    def test_admin_can_toggle_user_role(self, admin_token, test_user_id):
        """Admin should be able to toggle user role"""
        if not test_user_id:
            pytest.skip("Test user not found")
        
        # First, set role to user
        response = requests.patch(
            f"{BASE_URL}/api/admin/users/{test_user_id}/role",
            json={"role": "user"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        print(f"Set role to user status: {response.status_code}")
        
        assert response.status_code in [200, 404]  # 404 if user not found
        
        if response.status_code == 200:
            data = response.json()
            assert "message" in data
    
    def test_non_admin_cannot_update_subscription(self, user_token, test_user_id):
        """Regular user should get 403 when trying to update subscription"""
        if not user_token:
            pytest.skip("Test user not available")
        
        response = requests.patch(
            f"{BASE_URL}/api/admin/users/{test_user_id}/subscription",
            json={"plan": "pro", "status": "active"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        print(f"Non-admin update subscription status: {response.status_code}")
        
        assert response.status_code == 403
    
    def test_non_admin_cannot_toggle_role(self, user_token, test_user_id):
        """Regular user should get 403 when trying to toggle role"""
        if not user_token:
            pytest.skip("Test user not available")
        
        response = requests.patch(
            f"{BASE_URL}/api/admin/users/{test_user_id}/role",
            json={"role": "admin"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        print(f"Non-admin toggle role status: {response.status_code}")
        
        assert response.status_code == 403
    
    def test_admin_cannot_delete_self(self, admin_token):
        """Admin should not be able to delete themselves"""
        # First get admin's own ID
        response = requests.get(
            f"{BASE_URL}/api/admin/users?search={ADMIN_EMAIL}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        if response.status_code != 200:
            pytest.skip("Could not get admin user ID")
        
        users = response.json()
        admin_id = None
        for user in users:
            if user.get("email") == ADMIN_EMAIL:
                admin_id = user.get("id")
                break
        
        if not admin_id:
            pytest.skip("Admin user ID not found")
        
        response = requests.delete(
            f"{BASE_URL}/api/admin/users/{admin_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        print(f"Admin self-delete status: {response.status_code}")
        
        assert response.status_code == 400  # Should be rejected


class TestAdminInvalidRole:
    """Test invalid role values"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin login failed")
    
    def test_invalid_role_rejected(self, admin_token):
        """Invalid role value should be rejected"""
        response = requests.patch(
            f"{BASE_URL}/api/admin/users/some-user-id/role",
            json={"role": "superadmin"},  # Invalid role
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        print(f"Invalid role status: {response.status_code}")
        
        assert response.status_code == 400
    
    def test_invalid_subscription_status_rejected(self, admin_token):
        """Invalid subscription status should be rejected"""
        response = requests.patch(
            f"{BASE_URL}/api/admin/users/some-user-id/subscription",
            json={"status": "invalid_status"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        print(f"Invalid status status: {response.status_code}")
        
        assert response.status_code == 400


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
