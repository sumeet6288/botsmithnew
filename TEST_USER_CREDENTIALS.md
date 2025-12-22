# 🧪 Test User with Expiring Subscription

## Overview
Created a test user with a subscription that expires in **3 days** to demonstrate the subscription expiry warning system and renewal functionality.

---

## 🔑 Login Credentials

**URL**: https://renewal-tester.preview.emergentagent.com/signin

**Email**: `testuser@botsmith.com`  
**Password**: `test123`

---

## 📊 User Details

### Account Information
- **User ID**: `test-user-ea0dbc29`
- **Name**: Test User
- **Email**: testuser@botsmith.com
- **Company**: Test Company
- **Role**: User (Regular User)
- **Status**: Active, Verified

### Subscription Details
- **Plan**: Professional (₹24,999/month)
- **Status**: 🟠 **EXPIRING SOON**
- **Started**: November 25, 2025 (27 days ago)
- **Expires**: December 25, 2025
- **Days Remaining**: **3 DAYS**
- **Auto Renew**: Disabled

### Usage Statistics
- **Chatbots**: 2 (actively using the platform)
- **Messages This Month**: 5,432
- **File Uploads**: 8
- **Website Sources**: 5
- **Text Sources**: 12

### Sample Chatbot
- **Name**: Customer Support Bot
- **Description**: 24/7 customer support chatbot
- **AI Provider**: OpenAI
- **Model**: GPT-4o Mini
- **Status**: Active
- **Created**: 15 days ago

---

## 🎨 What You'll See in Dashboard

### 1. **Expiring Soon Warning Banner**
```
┌──────────────────────────────────────────────────────────────┐
│ ⏰ Your subscription is expiring in 3 days!    [Renew Now] 🟠│
└──────────────────────────────────────────────────────────────┘
```
- **Color**: Orange background
- **Position**: Top of dashboard
- **Action**: "Renew Now" button

### 2. **Subscription Status Card**
```
┌───────────────────────────────────────┐
│ 📊 Current Subscription Status        │
│                                       │
│ Plan: Professional 🟠                 │
│ Status: Expiring Soon                 │
│ Expires: Dec 25, 2025                 │
│ 3 days left 🟠                        │
│                                       │
│ ⏰ Expiring Soon!      [Renew Now] 🟠 │
└───────────────────────────────────────┘
```
- **Border**: Orange (warning color)
- **Days Counter**: "3 days left" in orange
- **Prominent "Renew Now" button**

### 3. **Subscription Modal (Automatic)**
If you navigate to different pages, you might see an automatic modal popup:

```
┌─────────────────────────────────────────────┐
│ ⏰ Subscription Expiring Soon               │
│                                             │
│ Your subscription expires in 3 days.        │
│ Renew to avoid interruption.                │
│                                             │
│ [Renew Professional]  [Upgrade to Better]   │
│                                             │
│ [I'll decide later]                         │
└─────────────────────────────────────────────┘
```

### 4. **Subscription Page**
Navigate to `/subscription` to see:
- Professional plan card with 🟠 **"Expiring Soon"** badge
- Orange border around current plan
- Detailed expiration information
- Large "Renew Now" button
- Comparison with other plans

---

## 🧪 Testing Scenarios

### Scenario 1: View Dashboard Warning
1. Login with test credentials
2. Observe orange warning banner at top
3. See "3 days remaining" counter
4. Notice "Renew Now" button

### Scenario 2: Navigate to Subscription Page
1. Click "Subscription" from sidebar or warning banner
2. See Professional plan with "Expiring Soon" badge
3. Review expiration date and details
4. Test "Renew Now" button

### Scenario 3: Test Renewal Functionality
1. Click "Renew Now" button
2. Watch loading state
3. Confirm renewal success
4. Verify new expiration date = Current + 30 days
5. Check that 3 remaining days are preserved (total 33 days)

### Scenario 4: Automatic Modal Popup
1. Navigate between different pages
2. Observe if subscription modal appears
3. Test modal actions (Renew, Upgrade, Dismiss)
4. Verify session-based dismissal (doesn't show again for same session)

---

## ✅ Expected Renewal Behavior

### Before Renewal
```
Current Date: Dec 22, 2025
Expires: Dec 25, 2025
Days Remaining: 3
```

### After Renewal (With Fixed Logic)
```
New Expiration: Dec 25 + 30 days = Jan 24, 2026
Total Days from Now: 33 days
Benefit: User gets 3 remaining + 30 new = 33 total days ✅
```

### If Renewal was Buggy (Old Logic)
```
New Expiration: Dec 22 + 30 days = Jan 21, 2026
Total Days from Now: 30 days
Problem: User LOSES 3 days ❌
```

---

## 🎯 What to Test

### Visual Elements
- [ ] Orange warning banner appears on dashboard
- [ ] "3 days left" counter displays correctly
- [ ] Orange border on subscription status card
- [ ] "Expiring Soon" badge on plan card
- [ ] "Renew Now" button is prominent and visible

### Functionality
- [ ] "Renew Now" button is clickable
- [ ] Loading state shows during renewal
- [ ] Success message appears after renewal
- [ ] Subscription extends to 33 days (3 + 30)
- [ ] Warning disappears after renewal
- [ ] Plan details update correctly

### User Experience
- [ ] Warning is noticeable but not intrusive
- [ ] Renewal process is smooth (one click)
- [ ] Clear messaging about consequences
- [ ] Easy access to upgrade options
- [ ] Consistent design with rest of app

---

## 📋 Comparison Users

### Admin User (For Comparison)
**Email**: `admin@botsmith.com`  
**Password**: `admin123`  
**Subscription**: Starter plan, expires in 2 days  
**Purpose**: Compare admin vs regular user experience

### Test User (Current)
**Email**: `testuser@botsmith.com`  
**Password**: `test123`  
**Subscription**: Professional plan, expires in 3 days  
**Purpose**: Test subscription expiry warnings

---

## 🔄 Reset Test User (If Needed)

To reset the test user subscription back to 3 days:

```bash
cd /app/backend && python3 << 'EOF'
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
import os

async def reset_test_subscription():
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'chatbase_db')
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Reset subscription to 3 days remaining
    expires_at = datetime.utcnow() + timedelta(days=3)
    started_at = datetime.utcnow() - timedelta(days=27)
    
    await db.subscriptions.update_one(
        {"user_id": {"$regex": "test-user-"}},
        {
            "$set": {
                "status": "active",
                "expires_at": expires_at,
                "started_at": started_at
            }
        }
    )
    
    print(f"✅ Test subscription reset to 3 days remaining")
    print(f"   Expires: {expires_at}")
    
    client.close()

asyncio.run(reset_test_subscription())
EOF
```

---

## 🎨 Color Coding Guide

### Subscription Status Colors
- 🟢 **Green**: Active, healthy (7+ days remaining)
- 🟠 **Orange**: Warning, expiring soon (≤3 days remaining)
- 🔴 **Red**: Critical, expired (0 days or negative)

### Visual Hierarchy
1. **Most Urgent**: Red border + Red badge + Red button
2. **Warning**: Orange border + Orange badge + Orange button
3. **Normal**: Green border + Green badge + No special button

---

## 📱 Responsive Testing

### Desktop (1920x1080)
- Full dashboard layout
- Sidebar visible
- Large warning banner
- All cards displayed

### Tablet (768x1024)
- Responsive sidebar
- Stacked cards
- Warning banner adapts
- Touch-friendly buttons

### Mobile (375x667)
- Mobile menu
- Vertical stack
- Full-width warning
- Easy-to-tap buttons

---

## 🚀 Quick Start

1. **Open Browser**: https://renewal-tester.preview.emergentagent.com/signin
2. **Login**: testuser@botsmith.com / test123
3. **Observe**: Dashboard with orange expiring warning
4. **Test**: Click "Renew Now" and verify renewal works
5. **Compare**: Login as admin to see different expiry state

---

## 📞 Support

If you encounter any issues:
- Check backend logs: `tail -50 /var/log/supervisor/backend.err.log`
- Check frontend logs: `tail -50 /var/log/supervisor/frontend.out.log`
- Verify services: `sudo supervisorctl status`
- Health check: `curl http://localhost:8001/api/health`

---

## ✅ Summary

Test user **testuser@botsmith.com** is ready with:
- ✅ Professional plan subscription
- ✅ 3 days remaining (expiring soon)
- ✅ Realistic usage data
- ✅ Sample chatbot
- ✅ All features enabled

**Purpose**: Demonstrate subscription expiry warnings and test renewal functionality with the fixed renewal model that properly extends subscriptions without losing remaining days.

**Expected Result**: User sees clear, orange-colored warnings about upcoming expiration and can renew with one click to extend subscription by 30 days while preserving the 3 remaining days (total 33 days).
