"""
Test Password Change Functionality
- User change password via /api/auth/change-password
- Admin reset user password via /api/admin/users/{user_id}/reset-password
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://saas-staging-dev.preview.emergentagent.com').rstrip('/')

# Test credentials from review request
ADMIN_EMAIL = "seamanshelp2021@gmail.com"
ADMIN_PASSWORD = "admin123"
TEST_USER_ID = "a30378cd-0364-49b0-8bce-fb786ccff8e0"
TEST_USER_EMAIL = "test091853@example.com"
TEST_USER_PASSWORD = "test123"


class TestUserChangePassword:
    """Tests for user password change endpoint /api/auth/change-password"""
    
    @pytest.fixture
    def test_user_token(self):
        """Login as test user and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip(f"Test user login failed: {response.status_code} - {response.text}")
    
    def test_change_password_wrong_current_password(self, test_user_token):
        """Test change password with wrong current password returns 400"""
        response = requests.put(
            f"{BASE_URL}/api/auth/change-password",
            json={
                "current_password": "wrongpassword123",
                "new_password": "newpassword123"
            },
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        data = response.json()
        assert "detail" in data
        assert "incorectă" in data["detail"].lower() or "incorrect" in data["detail"].lower()
        print(f"✓ Wrong current password correctly rejected: {data['detail']}")
    
    def test_change_password_short_new_password(self, test_user_token):
        """Test change password with too short new password returns 400"""
        response = requests.put(
            f"{BASE_URL}/api/auth/change-password",
            json={
                "current_password": TEST_USER_PASSWORD,
                "new_password": "12345"  # Less than 6 characters
            },
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        data = response.json()
        assert "detail" in data
        assert "6" in data["detail"] or "minim" in data["detail"].lower()
        print(f"✓ Short password correctly rejected: {data['detail']}")
    
    def test_change_password_no_auth(self):
        """Test change password without authentication returns 401/403"""
        response = requests.put(
            f"{BASE_URL}/api/auth/change-password",
            json={
                "current_password": "oldpass",
                "new_password": "newpass123"
            }
        )
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"✓ Unauthenticated request correctly rejected with {response.status_code}")
    
    def test_change_password_success(self, test_user_token):
        """Test successful password change and revert"""
        new_password = "newtest123"
        
        # Change password
        response = requests.put(
            f"{BASE_URL}/api/auth/change-password",
            json={
                "current_password": TEST_USER_PASSWORD,
                "new_password": new_password
            },
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "message" in data
        print(f"✓ Password changed successfully: {data['message']}")
        
        # Verify new password works
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": new_password
        })
        assert login_response.status_code == 200, f"Login with new password failed: {login_response.text}"
        new_token = login_response.json().get("token")
        print("✓ Login with new password successful")
        
        # Revert password back to original
        revert_response = requests.put(
            f"{BASE_URL}/api/auth/change-password",
            json={
                "current_password": new_password,
                "new_password": TEST_USER_PASSWORD
            },
            headers={"Authorization": f"Bearer {new_token}"}
        )
        assert revert_response.status_code == 200, f"Password revert failed: {revert_response.text}"
        print("✓ Password reverted to original")


class TestAdminResetUserPassword:
    """Tests for admin reset user password endpoint /api/admin/users/{user_id}/reset-password"""
    
    @pytest.fixture
    def admin_token(self):
        """Login as admin and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            assert data.get("user", {}).get("role") == "admin", "User is not admin"
            return data.get("token")
        pytest.skip(f"Admin login failed: {response.status_code} - {response.text}")
    
    @pytest.fixture
    def test_user_token(self):
        """Login as test user and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip(f"Test user login failed: {response.status_code}")
    
    def test_admin_reset_password_no_auth(self):
        """Test admin reset password without authentication returns 401/403"""
        response = requests.post(
            f"{BASE_URL}/api/admin/users/{TEST_USER_ID}/reset-password",
            json={"new_password": "newpass123"}
        )
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"✓ Unauthenticated request correctly rejected with {response.status_code}")
    
    def test_admin_reset_password_non_admin(self, test_user_token):
        """Test non-admin user cannot reset passwords"""
        response = requests.post(
            f"{BASE_URL}/api/admin/users/{TEST_USER_ID}/reset-password",
            json={"new_password": "newpass123"},
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print("✓ Non-admin user correctly blocked from resetting passwords")
    
    def test_admin_reset_password_short_password(self, admin_token):
        """Test admin reset with too short password returns 400"""
        response = requests.post(
            f"{BASE_URL}/api/admin/users/{TEST_USER_ID}/reset-password",
            json={"new_password": "12345"},  # Less than 6 characters
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        data = response.json()
        assert "detail" in data
        print(f"✓ Short password correctly rejected: {data['detail']}")
    
    def test_admin_reset_password_invalid_user(self, admin_token):
        """Test admin reset for non-existent user returns 404"""
        response = requests.post(
            f"{BASE_URL}/api/admin/users/invalid-user-id-12345/reset-password",
            json={"new_password": "newpass123"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        print("✓ Invalid user ID correctly returns 404")
    
    def test_admin_reset_password_success(self, admin_token):
        """Test successful admin password reset and revert"""
        temp_password = "adminreset123"
        
        # Admin resets user password
        response = requests.post(
            f"{BASE_URL}/api/admin/users/{TEST_USER_ID}/reset-password",
            json={"new_password": temp_password},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "message" in data
        print(f"✓ Admin reset password successful: {data['message']}")
        
        # Verify user can login with new password
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": temp_password
        })
        assert login_response.status_code == 200, f"Login with reset password failed: {login_response.text}"
        user_token = login_response.json().get("token")
        print("✓ User can login with admin-reset password")
        
        # User changes password back to original
        revert_response = requests.put(
            f"{BASE_URL}/api/auth/change-password",
            json={
                "current_password": temp_password,
                "new_password": TEST_USER_PASSWORD
            },
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert revert_response.status_code == 200, f"Password revert failed: {revert_response.text}"
        print("✓ Password reverted to original by user")


class TestAdminChangeOwnPassword:
    """Tests for admin changing their own password via /api/admin/change-password"""
    
    @pytest.fixture
    def admin_token(self):
        """Login as admin and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip(f"Admin login failed: {response.status_code}")
    
    def test_admin_change_password_wrong_current(self, admin_token):
        """Test admin change password with wrong current password"""
        response = requests.put(
            f"{BASE_URL}/api/admin/change-password",
            json={
                "current_password": "wrongpassword",
                "new_password": "newadmin123"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        print("✓ Admin wrong current password correctly rejected")
    
    def test_admin_change_password_endpoint_exists(self, admin_token):
        """Test that admin change password endpoint exists and validates"""
        response = requests.put(
            f"{BASE_URL}/api/admin/change-password",
            json={
                "current_password": ADMIN_PASSWORD,
                "new_password": "short"  # Too short
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Should return 400 for short password, not 404
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        print("✓ Admin change password endpoint exists and validates password length")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
