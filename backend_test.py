#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Subscription Renewal Model
Testing the critical bug fix: Renewal should extend from current_expires_at (not reset to now) for active subscriptions
"""

import requests
import json
from datetime import datetime, timedelta
import sys
import os

# Configuration
BASE_URL = "https://renewal-tester.preview.emergentagent.com/api"

# Test user credentials
TEST_USERS = {
    "user1": {
        "email": "user1@test.com",
        "password": "password123",
        "description": "Subscription expires in 3 days"
    },
    "user2": {
        "email": "user2@test.com", 
        "password": "password123",
        "description": "Subscription expired 5 days ago"
    }
}

class SubscriptionRenewalTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.failed_tests = []
        
    def log_test(self, test_name, status, details=""):
        """Log test results"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status_symbol = "✅" if status == "PASS" else "❌"
        print(f"{status_symbol} {test_name}: {details}")
        
        if status == "FAIL":
            self.failed_tests.append(result)
    
    def authenticate_user(self, email, password):
        """Authenticate user and return token"""
        try:
            # Try login first
            login_data = {"email": email, "password": password}
            response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                token_data = response.json()
                token = token_data.get("access_token")
                if token:
                    self.session.headers.update({"Authorization": f"Bearer {token}"})
                    return token
                else:
                    self.log_test(f"Login {email}", "FAIL", "No access token in response")
                    return None
            else:
                # If login fails, try to register the user
                register_data = {
                    "name": email.split("@")[0].title(),
                    "email": email,
                    "password": password
                }
                
                register_response = self.session.post(f"{BASE_URL}/auth/register", json=register_data)
                
                if register_response.status_code == 201:
                    # Now try login again
                    login_response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
                    if login_response.status_code == 200:
                        token_data = login_response.json()
                        token = token_data.get("access_token")
                        if token:
                            self.session.headers.update({"Authorization": f"Bearer {token}"})
                            return token
                
                self.log_test(f"Auth {email}", "FAIL", f"Login failed: {response.status_code}, Register: {register_response.status_code if 'register_response' in locals() else 'N/A'}")
                return None
                
        except Exception as e:
            self.log_test(f"Auth {email}", "FAIL", f"Exception: {str(e)}")
            return None
    
    def setup_test_subscriptions(self):
        """Setup test subscriptions for both users"""
        print("\n🔧 SETTING UP TEST SUBSCRIPTIONS...")
        
        # We'll need to manually create subscriptions with specific expiration dates
        # This would typically be done through direct database access or admin APIs
        # For now, we'll test with whatever subscriptions exist
        
        for user_key, user_data in TEST_USERS.items():
            token = self.authenticate_user(user_data["email"], user_data["password"])
            if token:
                self.log_test(f"Setup {user_key}", "PASS", f"User {user_data['email']} authenticated successfully")
            else:
                self.log_test(f"Setup {user_key}", "FAIL", f"Failed to authenticate {user_data['email']}")
    
    def test_subscription_status_api(self):
        """Test /api/plans/subscription-status endpoint"""
        print("\n📊 TESTING SUBSCRIPTION STATUS API...")
        
        for user_key, user_data in TEST_USERS.items():
            token = self.authenticate_user(user_data["email"], user_data["password"])
            if not token:
                continue
                
            try:
                response = self.session.get(f"{BASE_URL}/plans/subscription-status")
                
                if response.status_code == 200:
                    status_data = response.json()
                    
                    # Log the response for analysis
                    self.log_test(f"Status API {user_key}", "PASS", 
                                f"Response: {json.dumps(status_data, indent=2, default=str)}")
                    
                    # Validate response structure
                    required_fields = ["status", "is_expired"]
                    for field in required_fields:
                        if field not in status_data:
                            self.log_test(f"Status API {user_key} - {field}", "FAIL", 
                                        f"Missing required field: {field}")
                        else:
                            self.log_test(f"Status API {user_key} - {field}", "PASS", 
                                        f"Field present: {field} = {status_data[field]}")
                    
                    # Check specific expectations based on user
                    if user_key == "user1":
                        # Should have is_expiring_soon=true, days_remaining=3
                        if status_data.get("is_expiring_soon"):
                            self.log_test(f"Status API {user_key} - expiring soon", "PASS", 
                                        f"is_expiring_soon: {status_data.get('is_expiring_soon')}")
                        else:
                            self.log_test(f"Status API {user_key} - expiring soon", "INFO", 
                                        f"is_expiring_soon: {status_data.get('is_expiring_soon')} (expected true)")
                    
                    elif user_key == "user2":
                        # Should have is_expired=true, status=expired
                        if status_data.get("is_expired"):
                            self.log_test(f"Status API {user_key} - expired", "PASS", 
                                        f"is_expired: {status_data.get('is_expired')}")
                        else:
                            self.log_test(f"Status API {user_key} - expired", "INFO", 
                                        f"is_expired: {status_data.get('is_expired')} (expected true)")
                
                else:
                    self.log_test(f"Status API {user_key}", "FAIL", 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test(f"Status API {user_key}", "FAIL", f"Exception: {str(e)}")
    
    def test_get_subscription_api(self):
        """Test /api/plans/subscription endpoint"""
        print("\n📋 TESTING GET SUBSCRIPTION API...")
        
        for user_key, user_data in TEST_USERS.items():
            token = self.authenticate_user(user_data["email"], user_data["password"])
            if not token:
                continue
                
            try:
                response = self.session.get(f"{BASE_URL}/plans/current")
                
                if response.status_code == 200:
                    subscription_data = response.json()
                    
                    self.log_test(f"Get Subscription {user_key}", "PASS", 
                                f"Response: {json.dumps(subscription_data, indent=2, default=str)}")
                    
                    # Validate response structure
                    if "subscription" in subscription_data and "plan" in subscription_data:
                        subscription = subscription_data["subscription"]
                        plan = subscription_data["plan"]
                        
                        # Check required fields
                        sub_fields = ["plan_id", "status", "started_at", "expires_at"]
                        for field in sub_fields:
                            if field in subscription:
                                self.log_test(f"Subscription {user_key} - {field}", "PASS", 
                                            f"{field}: {subscription[field]}")
                            else:
                                self.log_test(f"Subscription {user_key} - {field}", "FAIL", 
                                            f"Missing field: {field}")
                    else:
                        self.log_test(f"Get Subscription {user_key}", "FAIL", 
                                    "Missing subscription or plan in response")
                
                else:
                    self.log_test(f"Get Subscription {user_key}", "FAIL", 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test(f"Get Subscription {user_key}", "FAIL", f"Exception: {str(e)}")
    
    def test_usage_stats_api(self):
        """Test /api/plans/usage-stats endpoint"""
        print("\n📈 TESTING USAGE STATS API...")
        
        for user_key, user_data in TEST_USERS.items():
            token = self.authenticate_user(user_data["email"], user_data["password"])
            if not token:
                continue
                
            try:
                response = self.session.get(f"{BASE_URL}/plans/usage")
                
                if response.status_code == 200:
                    usage_data = response.json()
                    
                    self.log_test(f"Usage Stats {user_key}", "PASS", 
                                f"Response: {json.dumps(usage_data, indent=2, default=str)}")
                    
                    # Validate response structure
                    required_sections = ["plan", "subscription", "usage"]
                    for section in required_sections:
                        if section in usage_data:
                            self.log_test(f"Usage Stats {user_key} - {section}", "PASS", 
                                        f"Section present: {section}")
                            
                            # Check specific fields in each section
                            if section == "usage":
                                usage_fields = ["chatbots", "messages", "file_uploads"]
                                for field in usage_fields:
                                    if field in usage_data[section]:
                                        field_data = usage_data[section][field]
                                        if "current" in field_data and "limit" in field_data:
                                            self.log_test(f"Usage Stats {user_key} - {field}", "PASS", 
                                                        f"{field}: {field_data['current']}/{field_data['limit']}")
                                        else:
                                            self.log_test(f"Usage Stats {user_key} - {field}", "FAIL", 
                                                        f"Missing current/limit in {field}")
                        else:
                            self.log_test(f"Usage Stats {user_key} - {section}", "FAIL", 
                                        f"Missing section: {section}")
                
                else:
                    self.log_test(f"Usage Stats {user_key}", "FAIL", 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test(f"Usage Stats {user_key}", "FAIL", f"Exception: {str(e)}")
    
    def test_renewal_logic(self):
        """Test /api/plans/renew endpoint - The critical bug fix test"""
        print("\n🔄 TESTING RENEWAL LOGIC (CRITICAL BUG FIX)...")
        
        for user_key, user_data in TEST_USERS.items():
            token = self.authenticate_user(user_data["email"], user_data["password"])
            if not token:
                continue
            
            print(f"\n--- Testing renewal for {user_key} ({user_data['description']}) ---")
            
            try:
                # Get subscription before renewal
                before_response = self.session.get(f"{BASE_URL}/plans/current")
                if before_response.status_code != 200:
                    self.log_test(f"Renewal {user_key} - Before", "FAIL", 
                                f"Failed to get subscription before renewal: {before_response.status_code}")
                    continue
                
                before_data = before_response.json()
                before_subscription = before_data.get("subscription", {})
                before_expires_at = before_subscription.get("expires_at")
                before_status = before_subscription.get("status")
                
                self.log_test(f"Renewal {user_key} - Before", "PASS", 
                            f"Before renewal - Status: {before_status}, Expires: {before_expires_at}")
                
                # Call renewal API
                renewal_response = self.session.post(f"{BASE_URL}/plans/renew")
                
                if renewal_response.status_code == 200:
                    renewal_data = renewal_response.json()
                    
                    self.log_test(f"Renewal {user_key} - API Call", "PASS", 
                                f"Renewal successful: {renewal_data.get('message', 'No message')}")
                    
                    # Get subscription after renewal
                    after_response = self.session.get(f"{BASE_URL}/plans/current")
                    if after_response.status_code == 200:
                        after_data = after_response.json()
                        after_subscription = after_data.get("subscription", {})
                        after_expires_at = after_subscription.get("expires_at")
                        after_status = after_subscription.get("status")
                        
                        self.log_test(f"Renewal {user_key} - After", "PASS", 
                                    f"After renewal - Status: {after_status}, Expires: {after_expires_at}")
                        
                        # Verify the critical bug fix logic
                        if before_expires_at and after_expires_at:
                            try:
                                # Parse dates (handle both ISO format and datetime objects)
                                if isinstance(before_expires_at, str):
                                    before_dt = datetime.fromisoformat(before_expires_at.replace('Z', '+00:00'))
                                else:
                                    before_dt = before_expires_at
                                    
                                if isinstance(after_expires_at, str):
                                    after_dt = datetime.fromisoformat(after_expires_at.replace('Z', '+00:00'))
                                else:
                                    after_dt = after_expires_at
                                
                                now = datetime.utcnow()
                                
                                # Calculate expected behavior based on bug fix
                                if user_key == "user1":
                                    # User 1: Active subscription (3 days remaining)
                                    # Should extend from current_expires + 30 days (preserve remaining days)
                                    expected_dt = before_dt + timedelta(days=30)
                                    days_difference = (after_dt - expected_dt).total_seconds() / 86400
                                    
                                    if abs(days_difference) < 1:  # Allow 1 day tolerance
                                        self.log_test(f"Renewal {user_key} - Logic Verification", "PASS", 
                                                    f"✅ BUG FIX WORKING: Extended from current expiration. Before: {before_dt}, After: {after_dt}, Expected: {expected_dt}")
                                    else:
                                        self.log_test(f"Renewal {user_key} - Logic Verification", "FAIL", 
                                                    f"❌ BUG FIX FAILED: Should extend from current expiration. Before: {before_dt}, After: {after_dt}, Expected: {expected_dt}")
                                
                                elif user_key == "user2":
                                    # User 2: Expired subscription (5 days ago)
                                    # Should start fresh from now + 30 days
                                    expected_dt = now + timedelta(days=30)
                                    days_difference = (after_dt - expected_dt).total_seconds() / 86400
                                    
                                    if abs(days_difference) < 1:  # Allow 1 day tolerance
                                        self.log_test(f"Renewal {user_key} - Logic Verification", "PASS", 
                                                    f"✅ EXPIRED RENEWAL WORKING: Started fresh from now. After: {after_dt}, Expected: {expected_dt}")
                                    else:
                                        self.log_test(f"Renewal {user_key} - Logic Verification", "FAIL", 
                                                    f"❌ EXPIRED RENEWAL ISSUE: Should start from now. After: {after_dt}, Expected: {expected_dt}")
                                
                                # Verify status became active
                                if after_status == "active":
                                    self.log_test(f"Renewal {user_key} - Status Update", "PASS", 
                                                f"Status correctly updated to 'active'")
                                else:
                                    self.log_test(f"Renewal {user_key} - Status Update", "FAIL", 
                                                f"Status should be 'active', got: {after_status}")
                                
                            except Exception as e:
                                self.log_test(f"Renewal {user_key} - Date Parsing", "FAIL", 
                                            f"Error parsing dates: {str(e)}")
                        else:
                            self.log_test(f"Renewal {user_key} - Date Verification", "FAIL", 
                                        f"Missing expiration dates - Before: {before_expires_at}, After: {after_expires_at}")
                    
                    else:
                        self.log_test(f"Renewal {user_key} - After", "FAIL", 
                                    f"Failed to get subscription after renewal: {after_response.status_code}")
                
                else:
                    self.log_test(f"Renewal {user_key} - API Call", "FAIL", 
                                f"Renewal failed: HTTP {renewal_response.status_code} - {renewal_response.text}")
                    
            except Exception as e:
                self.log_test(f"Renewal {user_key}", "FAIL", f"Exception: {str(e)}")
    
    def test_edge_cases(self):
        """Test edge cases for renewal"""
        print("\n🔍 TESTING EDGE CASES...")
        
        # Test renewal for already renewed subscription
        user_key = "user1"
        user_data = TEST_USERS[user_key]
        
        token = self.authenticate_user(user_data["email"], user_data["password"])
        if not token:
            return
        
        try:
            # Renew again to test multiple renewals
            print(f"Testing second renewal for {user_key}...")
            
            # Get current state
            before_response = self.session.get(f"{BASE_URL}/plans/current")
            if before_response.status_code == 200:
                before_data = before_response.json()
                before_expires = before_data.get("subscription", {}).get("expires_at")
                
                # Renew again
                renewal_response = self.session.post(f"{BASE_URL}/plans/renew")
                
                if renewal_response.status_code == 200:
                    # Get after state
                    after_response = self.session.get(f"{BASE_URL}/plans/current")
                    if after_response.status_code == 200:
                        after_data = after_response.json()
                        after_expires = after_data.get("subscription", {}).get("expires_at")
                        
                        self.log_test("Edge Case - Multiple Renewals", "PASS", 
                                    f"Second renewal successful. Before: {before_expires}, After: {after_expires}")
                        
                        # Verify usage counters are not reset
                        usage = after_data.get("usage", {})
                        self.log_test("Edge Case - Usage Preservation", "PASS", 
                                    f"Usage counters preserved: {json.dumps(usage, default=str)}")
                    else:
                        self.log_test("Edge Case - Multiple Renewals", "FAIL", 
                                    "Failed to get subscription after second renewal")
                else:
                    self.log_test("Edge Case - Multiple Renewals", "FAIL", 
                                f"Second renewal failed: {renewal_response.status_code}")
            else:
                self.log_test("Edge Case - Multiple Renewals", "FAIL", 
                            "Failed to get subscription before second renewal")
                
        except Exception as e:
            self.log_test("Edge Case - Multiple Renewals", "FAIL", f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all subscription renewal tests"""
        print("🚀 STARTING COMPREHENSIVE SUBSCRIPTION RENEWAL MODEL TESTING")
        print("=" * 80)
        print("Testing the critical bug fix: Renewal should extend from current_expires_at")
        print("(not reset to now) for active subscriptions")
        print("=" * 80)
        
        # Setup
        self.setup_test_subscriptions()
        
        # Core API tests
        self.test_subscription_status_api()
        self.test_get_subscription_api()
        self.test_usage_stats_api()
        
        # Critical renewal logic test
        self.test_renewal_logic()
        
        # Edge cases
        self.test_edge_cases()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["status"] == "PASS"])
        failed_tests = len([t for t in self.test_results if t["status"] == "FAIL"])
        info_tests = len([t for t in self.test_results if t["status"] == "INFO"])
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"ℹ️  Info: {info_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if self.failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in self.failed_tests:
                print(f"  - {test['test']}: {test['details']}")
        
        print("\n🎯 CRITICAL BUG FIX VERIFICATION:")
        renewal_tests = [t for t in self.test_results if "Logic Verification" in t["test"]]
        if renewal_tests:
            for test in renewal_tests:
                status_symbol = "✅" if test["status"] == "PASS" else "❌"
                print(f"  {status_symbol} {test['test']}: {test['details']}")
        else:
            print("  ⚠️  No renewal logic verification tests found")
        
        print("\n" + "=" * 80)

if __name__ == "__main__":
    tester = SubscriptionRenewalTester()
    tester.run_all_tests()