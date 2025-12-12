#!/usr/bin/env python3
"""
Comprehensive White Label Feature Testing - Plan Change Reflection
Testing the critical bug fix where white label feature wasn't working after admin changed user's plan.
"""

import asyncio
import aiohttp
import json
import uuid
from datetime import datetime, timezone
import os
import sys

# Backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://appearance-persist.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class WhiteLabelTester:
    def __init__(self):
        self.session = None
        self.test_users = []
        self.test_chatbots = []
        self.admin_token = None
        self.user_tokens = {}
        
    async def setup_session(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
            
    async def login_user(self, email: str, password: str = "test123"):
        """Login user and get token"""
        try:
            login_data = {
                "email": email,
                "password": password
            }
            
            async with self.session.post(
                f"{API_BASE}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    token_data = await response.json()
                    token = token_data.get("access_token")
                    print(f"✅ Logged in user: {email}")
                    return token
                else:
                    error_text = await response.text()
                    print(f"❌ Login failed for {email}: {response.status} - {error_text}")
                    return None
        except Exception as e:
            print(f"❌ Login error for {email}: {e}")
            return None
            
    async def create_test_user(self, email: str, name: str, plan_id: str = "free"):
        """Create a test user via admin API"""
        try:
            user_data = {
                "email": email,
                "name": name,
                "password": "test123",
                "role": "user",
                "status": "active",
                "plan_id": plan_id,
                "email_verified": True
            }
            
            async with self.session.post(
                f"{API_BASE}/admin/users/create",
                json=user_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    user_id = result.get("user_id")
                    self.test_users.append(user_id)
                    print(f"✅ Created test user: {email} (ID: {user_id}) with plan: {plan_id}")
                    return user_id
                else:
                    error_text = await response.text()
                    print(f"❌ Failed to create user {email}: {response.status} - {error_text}")
                    return None
        except Exception as e:
            print(f"❌ Error creating user {email}: {e}")
            return None
            
    async def create_test_chatbot(self, user_id: str, name: str = "Test Chatbot"):
        """Create a test chatbot for user"""
        try:
            chatbot_data = {
                "name": name,
                "model": "gpt-4o-mini",
                "provider": "openai",
                "temperature": 0.7,
                "instructions": "You are a helpful assistant.",
                "welcome_message": "Hello! How can I help you today?"
            }
            
            # Mock the current user for this request
            headers = {
                "Content-Type": "application/json",
                "X-Mock-User-ID": user_id  # Custom header for mock auth
            }
            
            async with self.session.post(
                f"{API_BASE}/chatbots",
                json=chatbot_data,
                headers=headers
            ) as response:
                if response.status == 201:
                    chatbot = await response.json()
                    chatbot_id = chatbot.get("id")
                    self.test_chatbots.append(chatbot_id)
                    print(f"✅ Created test chatbot: {name} (ID: {chatbot_id}) for user {user_id}")
                    return chatbot_id
                else:
                    error_text = await response.text()
                    print(f"❌ Failed to create chatbot: {response.status} - {error_text}")
                    return None
        except Exception as e:
            print(f"❌ Error creating chatbot: {e}")
            return None
            
    async def get_user_plan_usage(self, user_id: str):
        """Get user's plan usage stats to check custom_branding flag"""
        try:
            headers = {"X-Mock-User-ID": user_id}
            
            async with self.session.get(
                f"{API_BASE}/plans/usage",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    error_text = await response.text()
                    print(f"❌ Failed to get usage stats for user {user_id}: {response.status} - {error_text}")
                    return None
        except Exception as e:
            print(f"❌ Error getting usage stats: {e}")
            return None
            
    async def update_chatbot_powered_by(self, chatbot_id: str, user_id: str, powered_by_text: str):
        """Try to update chatbot's powered_by_text"""
        try:
            update_data = {"powered_by_text": powered_by_text}
            headers = {
                "Content-Type": "application/json",
                "X-Mock-User-ID": user_id
            }
            
            async with self.session.put(
                f"{API_BASE}/chatbots/{chatbot_id}",
                json=update_data,
                headers=headers
            ) as response:
                if response.status == 200:
                    chatbot = await response.json()
                    print(f"✅ Successfully updated powered_by_text to: '{powered_by_text}'")
                    return True, chatbot
                elif response.status == 403:
                    error_data = await response.json()
                    print(f"🚫 Forbidden (expected for free users): {error_data.get('detail', {}).get('message', 'Access denied')}")
                    return False, error_data
                else:
                    error_text = await response.text()
                    print(f"❌ Failed to update powered_by_text: {response.status} - {error_text}")
                    return False, None
        except Exception as e:
            print(f"❌ Error updating powered_by_text: {e}")
            return False, None
            
    async def admin_update_user_plan(self, user_id: str, new_plan_id: str):
        """Admin updates user's plan via ultimate-update endpoint"""
        try:
            update_data = {"plan_id": new_plan_id}
            
            async with self.session.put(
                f"{API_BASE}/admin/users/{user_id}/ultimate-update",
                json=update_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Admin updated user {user_id} plan to: {new_plan_id}")
                    return True, result
                else:
                    error_text = await response.text()
                    print(f"❌ Failed to update user plan: {response.status} - {error_text}")
                    return False, None
        except Exception as e:
            print(f"❌ Error updating user plan: {e}")
            return False, None
            
    async def verify_database_subscription(self, user_id: str):
        """Verify subscription exists in database"""
        try:
            # Get user details to check subscription
            async with self.session.get(f"{API_BASE}/admin/users/{user_id}/details") as response:
                if response.status == 200:
                    user_data = await response.json()
                    user = user_data.get("user", {})
                    plan_id = user.get("plan_id")
                    print(f"📊 User {user_id} database plan_id: {plan_id}")
                    return plan_id
                else:
                    print(f"❌ Failed to get user details: {response.status}")
                    return None
        except Exception as e:
            print(f"❌ Error verifying database subscription: {e}")
            return None

    async def test_api_response_structure(self):
        """Test 1: API Response Structure Test"""
        print("\n" + "="*60)
        print("🧪 TEST 1: API Response Structure Test")
        print("="*60)
        
        # Create a test user with starter plan
        user_id = await self.create_test_user("test-api-structure@test.com", "API Test User", "starter")
        if not user_id:
            return False
            
        # Get usage stats
        usage_data = await self.get_user_plan_usage(user_id)
        if not usage_data:
            return False
            
        # Verify response structure
        plan = usage_data.get("plan", {})
        limits = plan.get("limits", {})
        custom_branding = limits.get("custom_branding")
        
        print(f"📊 Plan ID: {plan.get('id')}")
        print(f"📊 Plan Name: {plan.get('name')}")
        print(f"📊 Plan Limits: {limits}")
        print(f"📊 Custom Branding: {custom_branding}")
        
        # Verify structure
        if "limits" not in plan:
            print("❌ FAIL: 'limits' object missing from plan response")
            return False
            
        if "custom_branding" not in limits:
            print("❌ FAIL: 'custom_branding' flag missing from limits")
            return False
            
        if not isinstance(custom_branding, bool):
            print("❌ FAIL: 'custom_branding' is not a boolean")
            return False
            
        print("✅ PASS: API response structure is correct")
        return True

    async def test_free_plan_user(self):
        """Test 2: Free Plan User Test"""
        print("\n" + "="*60)
        print("🧪 TEST 2: Free Plan User Test")
        print("="*60)
        
        # Create free plan user
        user_id = await self.create_test_user("test-free@test.com", "Free User", "free")
        if not user_id:
            return False
            
        # Create chatbot for user
        chatbot_id = await self.create_test_chatbot(user_id, "Free User Chatbot")
        if not chatbot_id:
            return False
            
        # Check usage stats
        usage_data = await self.get_user_plan_usage(user_id)
        if not usage_data:
            return False
            
        custom_branding = usage_data.get("plan", {}).get("limits", {}).get("custom_branding")
        print(f"📊 Free plan custom_branding: {custom_branding}")
        
        if custom_branding is not False:
            print("❌ FAIL: Free plan should have custom_branding: false")
            return False
            
        # Try to update powered_by_text (should fail)
        success, result = await self.update_chatbot_powered_by(chatbot_id, user_id, "Custom Branding Text")
        
        if success:
            print("❌ FAIL: Free user should not be able to set powered_by_text")
            return False
            
        print("✅ PASS: Free plan user correctly blocked from custom branding")
        return True

    async def test_paid_plan_user(self):
        """Test 3: Paid Plan User Test"""
        print("\n" + "="*60)
        print("🧪 TEST 3: Paid Plan User Test (Starter)")
        print("="*60)
        
        # Create starter plan user
        user_id = await self.create_test_user("test-starter@test.com", "Starter User", "starter")
        if not user_id:
            return False
            
        # Create chatbot for user
        chatbot_id = await self.create_test_chatbot(user_id, "Starter User Chatbot")
        if not chatbot_id:
            return False
            
        # Check usage stats
        usage_data = await self.get_user_plan_usage(user_id)
        if not usage_data:
            return False
            
        custom_branding = usage_data.get("plan", {}).get("limits", {}).get("custom_branding")
        print(f"📊 Starter plan custom_branding: {custom_branding}")
        
        if custom_branding is not True:
            print("❌ FAIL: Starter plan should have custom_branding: true")
            return False
            
        # Try to update powered_by_text (should succeed)
        success, result = await self.update_chatbot_powered_by(chatbot_id, user_id, "My Custom Brand")
        
        if not success:
            print("❌ FAIL: Starter user should be able to set powered_by_text")
            return False
            
        # Verify it persisted
        if result and result.get("powered_by_text") != "My Custom Brand":
            print("❌ FAIL: powered_by_text did not persist correctly")
            return False
            
        print("✅ PASS: Paid plan user can successfully use custom branding")
        return True

    async def test_admin_plan_change_simulation(self):
        """Test 4: Admin Plan Change Simulation - THE CRITICAL TEST"""
        print("\n" + "="*60)
        print("🧪 TEST 4: Admin Plan Change Simulation (CRITICAL)")
        print("="*60)
        
        # Step 1: Create user with free plan
        user_id = await self.create_test_user("test-upgrade@test.com", "Upgrade Test User", "free")
        if not user_id:
            return False
            
        # Create chatbot for user
        chatbot_id = await self.create_test_chatbot(user_id, "Upgrade Test Chatbot")
        if not chatbot_id:
            return False
            
        # Step 2: Verify free plan restrictions
        print("\n📋 Step 2: Verify initial free plan restrictions")
        usage_data = await self.get_user_plan_usage(user_id)
        if not usage_data:
            return False
            
        custom_branding = usage_data.get("plan", {}).get("limits", {}).get("custom_branding")
        print(f"📊 Initial custom_branding: {custom_branding}")
        
        if custom_branding is not False:
            print("❌ FAIL: User should start with custom_branding: false")
            return False
            
        # Step 3: Admin upgrades user to starter plan
        print("\n📋 Step 3: Admin upgrades user to starter plan")
        success, result = await self.admin_update_user_plan(user_id, "starter")
        if not success:
            return False
            
        # Step 4: Verify subscription in database
        print("\n📋 Step 4: Verify subscription updated in database")
        db_plan_id = await self.verify_database_subscription(user_id)
        if db_plan_id != "starter":
            print(f"❌ FAIL: Database plan_id is {db_plan_id}, expected 'starter'")
            return False
            
        # Step 5: THE CRITICAL TEST - Check if usage API now returns custom_branding: true
        print("\n📋 Step 5: CRITICAL TEST - Check usage API reflects plan change")
        usage_data_after = await self.get_user_plan_usage(user_id)
        if not usage_data_after:
            return False
            
        custom_branding_after = usage_data_after.get("plan", {}).get("limits", {}).get("custom_branding")
        print(f"📊 After upgrade custom_branding: {custom_branding_after}")
        
        if custom_branding_after is not True:
            print("❌ CRITICAL FAIL: custom_branding should be true after upgrade to starter plan")
            print("❌ This is the exact bug that was supposed to be fixed!")
            return False
            
        # Step 6: Verify user can now update powered_by_text
        print("\n📋 Step 6: Verify user can now use custom branding")
        success, result = await self.update_chatbot_powered_by(chatbot_id, user_id, "Upgraded Custom Brand")
        
        if not success:
            print("❌ FAIL: User should be able to set powered_by_text after upgrade")
            return False
            
        print("✅ CRITICAL PASS: Plan change correctly reflects in usage API and enables custom branding")
        return True

    async def test_plan_downgrade(self):
        """Test 5: Plan Downgrade Test"""
        print("\n" + "="*60)
        print("🧪 TEST 5: Plan Downgrade Test")
        print("="*60)
        
        # Create user with starter plan
        user_id = await self.create_test_user("test-downgrade@test.com", "Downgrade Test User", "starter")
        if not user_id:
            return False
            
        # Create chatbot for user
        chatbot_id = await self.create_test_chatbot(user_id, "Downgrade Test Chatbot")
        if not chatbot_id:
            return False
            
        # Verify starter plan allows custom branding
        usage_data = await self.get_user_plan_usage(user_id)
        custom_branding = usage_data.get("plan", {}).get("limits", {}).get("custom_branding")
        
        if custom_branding is not True:
            print("❌ FAIL: Starter plan should have custom_branding: true")
            return False
            
        # Admin downgrades user to free plan
        print("\n📋 Downgrading user to free plan")
        success, result = await self.admin_update_user_plan(user_id, "free")
        if not success:
            return False
            
        # Verify downgrade reflects in usage API
        usage_data_after = await self.get_user_plan_usage(user_id)
        custom_branding_after = usage_data_after.get("plan", {}).get("limits", {}).get("custom_branding")
        print(f"📊 After downgrade custom_branding: {custom_branding_after}")
        
        if custom_branding_after is not False:
            print("❌ FAIL: custom_branding should be false after downgrade to free plan")
            return False
            
        # Verify user can no longer update powered_by_text
        success, result = await self.update_chatbot_powered_by(chatbot_id, user_id, "Should Fail")
        
        if success:
            print("❌ FAIL: User should not be able to set powered_by_text after downgrade")
            return False
            
        print("✅ PASS: Plan downgrade correctly removes custom branding access")
        return True

    async def test_multiple_plan_types(self):
        """Test 6: Multiple Plan Types Test"""
        print("\n" + "="*60)
        print("🧪 TEST 6: Multiple Plan Types Test")
        print("="*60)
        
        plans_to_test = [
            ("professional", True),
            ("enterprise", True),
            ("free", False)
        ]
        
        for plan_id, expected_branding in plans_to_test:
            print(f"\n📋 Testing {plan_id} plan (expected custom_branding: {expected_branding})")
            
            user_id = await self.create_test_user(f"test-{plan_id}@test.com", f"{plan_id.title()} User", plan_id)
            if not user_id:
                return False
                
            usage_data = await self.get_user_plan_usage(user_id)
            if not usage_data:
                return False
                
            custom_branding = usage_data.get("plan", {}).get("limits", {}).get("custom_branding")
            print(f"📊 {plan_id} plan custom_branding: {custom_branding}")
            
            if custom_branding != expected_branding:
                print(f"❌ FAIL: {plan_id} plan should have custom_branding: {expected_branding}")
                return False
                
        print("✅ PASS: All plan types have correct custom_branding settings")
        return True

    async def cleanup_test_data(self):
        """Cleanup test users and chatbots"""
        print("\n" + "="*60)
        print("🧹 CLEANUP: Removing test data")
        print("="*60)
        
        # Delete test users (this will cascade delete chatbots)
        for user_id in self.test_users:
            try:
                async with self.session.delete(f"{API_BASE}/admin/users/{user_id}") as response:
                    if response.status == 200:
                        print(f"✅ Deleted test user: {user_id}")
                    else:
                        print(f"⚠️  Failed to delete user {user_id}: {response.status}")
            except Exception as e:
                print(f"⚠️  Error deleting user {user_id}: {e}")

    async def run_all_tests(self):
        """Run all white label feature tests"""
        print("🚀 STARTING WHITE LABEL FEATURE COMPREHENSIVE TESTING")
        print("🎯 Focus: Plan Change Reflection Bug Fix")
        print("="*80)
        
        await self.setup_session()
        
        try:
            test_results = []
            
            # Run all tests
            tests = [
                ("API Response Structure", self.test_api_response_structure),
                ("Free Plan User", self.test_free_plan_user),
                ("Paid Plan User", self.test_paid_plan_user),
                ("Admin Plan Change Simulation", self.test_admin_plan_change_simulation),
                ("Plan Downgrade", self.test_plan_downgrade),
                ("Multiple Plan Types", self.test_multiple_plan_types)
            ]
            
            for test_name, test_func in tests:
                try:
                    result = await test_func()
                    test_results.append((test_name, result))
                except Exception as e:
                    print(f"❌ ERROR in {test_name}: {e}")
                    test_results.append((test_name, False))
            
            # Cleanup
            await self.cleanup_test_data()
            
            # Summary
            print("\n" + "="*80)
            print("📊 WHITE LABEL FEATURE TEST RESULTS SUMMARY")
            print("="*80)
            
            passed = 0
            failed = 0
            
            for test_name, result in test_results:
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"{status}: {test_name}")
                if result:
                    passed += 1
                else:
                    failed += 1
            
            print(f"\n📈 TOTAL: {passed} passed, {failed} failed out of {len(test_results)} tests")
            
            if failed == 0:
                print("🎉 ALL TESTS PASSED! White label feature is working correctly.")
                return True
            else:
                print("⚠️  SOME TESTS FAILED! White label feature has issues.")
                return False
                
        finally:
            await self.cleanup_session()

async def main():
    """Main test runner"""
    tester = WhiteLabelTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n✅ WHITE LABEL TESTING COMPLETED SUCCESSFULLY")
        sys.exit(0)
    else:
        print("\n❌ WHITE LABEL TESTING FAILED")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())