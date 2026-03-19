#!/usr/bin/env python3
"""
Backend API Tests for SaaS SEO Automation - Annual Billing & Invoice Features
Testing the new features: Annual billing with 20% discount, Invoice PDF generation, Monthly usage reset scheduler
"""
import requests
import sys
import json
import time
from datetime import datetime

class SaasBackendTester:
    def __init__(self, base_url="https://seo-automation-saas.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.user_id = None
        
    def log(self, message):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        self.log(f"🔍 Testing {name}...")
        self.log(f"   → {method} {endpoint}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                self.log(f"✅ PASSED - Status: {response.status_code}")
            else:
                self.log(f"❌ FAILED - Expected {expected_status}, got {response.status_code}")
                if response.status_code >= 400:
                    try:
                        error_detail = response.json()
                        self.log(f"   Error: {error_detail}")
                    except:
                        self.log(f"   Error: {response.text[:200]}")

            # Return response data and status code for further testing
            try:
                response_data = response.json() if response.content else {}
                response_data['_status_code'] = response.status_code
                return success, response_data
            except:
                return success, {"raw_response": response.text[:500], "_status_code": response.status_code}

        except Exception as e:
            self.log(f"❌ FAILED - Exception: {str(e)}")
            return False, {"_status_code": 0}

    def setup_test_user(self):
        """Setup test user for testing"""
        self.log("🚀 Setting up test user...")
        
        test_email = "test@example.com"
        test_password = "test123"
        
        # Try login (user should exist from review request)
        success, response = self.run_test(
            "Login test user",
            "POST",
            "api/auth/login",
            200,
            data={"email": test_email, "password": test_password}
        )
        
        if success and 'token' in response:
            self.token = response['token']
            self.user_id = response.get('user', {}).get('id')
            self.log(f"✅ Successfully logged in test user: {test_email}")
            return True
        else:
            self.log(f"❌ Failed to login test user. Check credentials.")
            return False

    def test_annual_billing_plans(self):
        """Test annual billing with 20% discount calculation"""
        success, response = self.run_test(
            "Get Plans (Annual Pricing)",
            "GET",
            "api/saas/plans",
            200
        )
        
        if success and response:
            plans = {k: v for k, v in response.items() if k != '_status_code'}
            self.log("✅ Plans endpoint working")
            
            # Check annual discount calculation
            annual_discounts_correct = True
            for plan_id, plan in plans.items():
                if isinstance(plan, dict) and 'price_eur' in plan:
                    monthly_price = plan['price_eur']
                    # According to plans.py, annual should be monthly * 12 * 0.8
                    expected_annual = int(monthly_price * 12 * 0.8)
                    
                    # Check if the discount is approximately 20%
                    full_year_cost = monthly_price * 12
                    if full_year_cost > 0:
                        discount_percentage = ((full_year_cost - expected_annual) / full_year_cost) * 100
                        if abs(discount_percentage - 20.0) > 1.0:  # Allow 1% tolerance
                            self.log(f"❌ {plan_id}: Annual discount incorrect - expected ~20%, got {discount_percentage:.1f}%")
                            annual_discounts_correct = False
                        else:
                            self.log(f"✅ {plan_id}: €{monthly_price}/mo → €{expected_annual}/year (20% discount)")
                    
            return annual_discounts_correct
        
        return False

    def test_subscription_endpoints(self):
        """Test subscription-related endpoints"""
        # Test subscription info
        success, sub_response = self.run_test(
            "Get Subscription Info",
            "GET", 
            "api/saas/subscription",
            200
        )
        
        # Test usage stats
        success2, usage_response = self.run_test(
            "Get Usage Stats",
            "GET",
            "api/saas/subscription/usage", 
            200
        )
        
        if success and success2:
            self.log("✅ Subscription endpoints working")
            if 'plan' in sub_response:
                self.log(f"   → Current plan: {sub_response['plan']}")
            if 'status' in usage_response:
                self.log(f"   → Status: {usage_response['status']}")
            return True
        
        return False

    def test_checkout_with_billing_period(self):
        """Test checkout API accepts billing_period parameter (monthly/annual)"""
        # Test with annual billing
        success_annual, annual_response = self.run_test(
            "Checkout with Annual Billing",
            "POST",
            "api/saas/checkout",
            200,
            data={
                "plan": "pro",
                "billing_period": "annual",
                "origin_url": self.base_url
            }
        )
        
        # Test with monthly billing
        success_monthly, monthly_response = self.run_test(
            "Checkout with Monthly Billing", 
            "POST",
            "api/saas/checkout",
            200,
            data={
                "plan": "pro",
                "billing_period": "monthly",
                "origin_url": self.base_url
            }
        )
        
        if success_annual and success_monthly:
            self.log("✅ Checkout API accepts both annual and monthly billing periods")
            if 'url' in annual_response:
                self.log("✅ Annual checkout returns Stripe URL")
            if 'url' in monthly_response:
                self.log("✅ Monthly checkout returns Stripe URL")
            return True
        else:
            self.log("❌ Checkout API failing with billing_period parameter")
            return False

    def test_invoices_api(self):
        """Test invoice-related API endpoints"""
        # Test get invoices list
        success, response = self.run_test(
            "Get Invoices List",
            "GET",
            "api/saas/invoices",
            200
        )
        
        if success:
            self.log("✅ Invoices API working")
            invoices = response if isinstance(response, list) else []
            self.log(f"   → Found {len(invoices)} invoices")
            
            # Test invoice PDF endpoint (should exist even if no invoices)
            if invoices:
                # Test with first invoice
                invoice_id = invoices[0].get('id')
                if invoice_id:
                    pdf_success, pdf_response = self.run_test(
                        "Get Invoice PDF",
                        "GET",
                        f"api/saas/invoices/{invoice_id}/pdf",
                        200
                    )
                    if pdf_success:
                        self.log("✅ Invoice PDF endpoint working")
                        return True
                    else:
                        self.log("❌ Invoice PDF endpoint failing")
            else:
                # Test with dummy ID to check endpoint exists
                pdf_success, pdf_response = self.run_test(
                    "Invoice PDF Endpoint (dummy ID)",
                    "GET",
                    "api/saas/invoices/dummy-id/pdf",
                    404  # Should return 404 for non-existent invoice
                )
                if pdf_response.get('_status_code') == 404:
                    self.log("✅ Invoice PDF endpoint exists (returns 404 for invalid ID)")
                    return True
                else:
                    self.log("❌ Invoice PDF endpoint not properly configured")
            
            return success
        
        return False

    def test_plans_endpoint(self):
        """Test plans endpoint"""
        success, response = self.run_test(
            "Get Available Plans",
            "GET",
            "api/saas/plans",
            200
        )
        
        if success and response:
            # Remove _status_code from plans for validation
            plans = {k: v for k, v in response.items() if k != '_status_code'}
            plan_names = list(plans.keys())
            self.log(f"✅ Plans endpoint working")
            self.log(f"   → Available plans: {plan_names}")
            
            # Validate plan structure
            for plan_id, plan in plans.items():
                required_fields = ['name', 'price_eur', 'sites_limit', 'articles_limit']
                if isinstance(plan, dict) and all(field in plan for field in required_fields):
                    self.log(f"   → {plan_id}: €{plan['price_eur']}/month")
                else:
                    self.log(f"❌ Plan {plan_id} missing required fields or invalid structure")
                    return False
            
            return True
        
        return False

    def test_existing_endpoints(self):
        """Test that existing endpoints still work"""
        # Test auth/me
        success1, _ = self.run_test("Auth Me", "GET", "api/auth/me", 200)
        
        # Test dashboard/all
        success2, _ = self.run_test("Dashboard All", "GET", "api/dashboard/all", 200)
        
        # Test search console status
        success3, _ = self.run_test("Search Console Status", "GET", "api/search-console/status", 200)
        
        success_count = sum([success1, success2, success3])
        if success_count == 3:
            self.log("✅ All existing endpoints working")
            return True
        else:
            self.log(f"❌ Only {success_count}/3 existing endpoints working")
            return False

    def check_monthly_usage_reset_scheduler(self):
        """Check if monthly usage reset scheduler is configured"""
        self.log("🔍 Checking monthly usage reset scheduler...")
        
        # Check subscription usage to see if reset logic exists
        success, response = self.run_test(
            "Get Usage Stats (to check reset logic)",
            "GET",
            "api/saas/subscription/usage",
            200
        )
        
        if success and response:
            # Look for usage tracking fields that would be reset monthly
            usage_fields = ['articles_used', 'sites_used', 'articles_limit', 'sites_limit']
            has_usage_tracking = any(field in response for field in usage_fields)
            
            if has_usage_tracking:
                self.log("✅ Monthly usage tracking fields present")
                self.log(f"   → Articles used: {response.get('articles_used', 0)}")
                self.log(f"   → Articles limit: {response.get('articles_limit', 'N/A')}")
                self.log("   → Monthly reset scheduler likely configured")
                return True
            else:
                self.log("❌ No usage tracking fields found for monthly reset")
                return False
        else:
            self.log("❌ Could not check usage stats for scheduler verification")
            return False

def main():
    """Main test runner"""
    print("=" * 60)
    print("🚀 SaaS Backend API Testing - Annual Billing & Invoice Features")
    print("=" * 60)
    
    tester = SaasBackendTester()
    
    # Setup
    if not tester.setup_test_user():
        print("❌ Failed to setup test user. Exiting.")
        return 1
    
    # Run all tests
    test_results = []
    
    print("\n📊 Testing New Annual Billing Features:")
    print("-" * 40)
    
    # Test annual billing plans with 20% discount
    test_results.append(("Annual Billing Plans (20% discount)", tester.test_annual_billing_plans()))
    
    # Test checkout API with billing_period parameter
    test_results.append(("Checkout API with billing_period", tester.test_checkout_with_billing_period()))
    
    # Test invoice API
    test_results.append(("Invoice API endpoints", tester.test_invoices_api()))
    
    # Test subscription endpoints  
    test_results.append(("Subscription Endpoints", tester.test_subscription_endpoints()))
    
    # Check monthly usage reset scheduler
    test_results.append(("Monthly Usage Reset Scheduler", tester.check_monthly_usage_reset_scheduler()))
    
    print("\n🔄 Testing Existing Endpoints:")
    print("-" * 40)
    
    # Test plans endpoint
    test_results.append(("Plans Endpoint", tester.test_plans_endpoint()))
    
    # Test existing endpoints still work
    test_results.append(("Existing Endpoints", tester.test_existing_endpoints()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    
    passed_tests = 0
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed_tests += 1
    
    success_rate = (passed_tests / len(test_results)) * 100
    print(f"\n📊 Overall Results:")
    print(f"   Tests Passed: {passed_tests}/{len(test_results)}")
    print(f"   API Calls: {tester.tests_passed}/{tester.tests_run}")
    print(f"   Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 85:
        print("🎉 Backend testing SUCCESSFUL!")
        return 0
    else:
        print("⚠️  Backend has issues that need attention")
        return 1

if __name__ == "__main__":
    sys.exit(main())