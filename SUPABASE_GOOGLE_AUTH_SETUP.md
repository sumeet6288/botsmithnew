# Supabase Google OAuth Authentication Setup Guide

This guide will help you configure Google OAuth authentication using Supabase for your BotSmith AI application.

## 📋 Overview

The application includes complete code for Supabase Google OAuth authentication. You just need to:
1. Create a Supabase project
2. Enable Google OAuth provider
3. Add environment variables
4. Install Supabase client library

## 🚀 Step 1: Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Sign up or log in
3. Click "New Project"
4. Fill in project details:
   - Project name: `botsmith-ai` (or your choice)
   - Database password: (save this securely)
   - Region: Choose closest to your users
5. Click "Create new project"
6. Wait for project to be ready (~2 minutes)

## 🔑 Step 2: Get Supabase Credentials

1. In your Supabase project dashboard:
2. Go to **Settings** → **API**
3. Find and copy:
   - **Project URL** (e.g., `https://xxxxx.supabase.co`)
   - **anon public key** (starts with `eyJ...`)
4. Go to **Settings** → **API** → **JWT Settings**
5. Copy the **JWT Secret**

## 🔐 Step 3: Configure Google OAuth in Supabase

### A. Create Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing one
3. Navigate to **APIs & Services** → **Credentials**
4. Click **Create Credentials** → **OAuth client ID**
5. If prompted, configure OAuth consent screen:
   - User Type: External
   - App name: BotSmith AI
   - User support email: your-email@example.com
   - Developer contact: your-email@example.com
   - Add scopes: email, profile
   - Add test users (if needed)
6. Create OAuth client ID:
   - Application type: **Web application**
   - Name: BotSmith AI
   - Authorized redirect URIs: `https://[YOUR-PROJECT-REF].supabase.co/auth/v1/callback`
     (Replace `[YOUR-PROJECT-REF]` with your actual Supabase project reference from Project URL)
7. Click **Create**
8. Copy **Client ID** and **Client Secret**

### B. Enable Google Provider in Supabase

1. In Supabase dashboard, go to **Authentication** → **Providers**
2. Find **Google** in the list
3. Enable Google provider
4. Paste your Google OAuth:
   - **Client ID**
   - **Client Secret**
5. Click **Save**

## 🛠️ Step 4: Configure Environment Variables

### Backend (.env)

Add these to `/app/backend/.env`:

```bash
# Supabase Configuration
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_JWT_SECRET=your-jwt-secret-here
```

### Frontend (.env)

Add these to `/app/frontend/.env`:

```bash
# Supabase Configuration
REACT_APP_SUPABASE_URL=https://xxxxx.supabase.co
REACT_APP_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## 📦 Step 5: Install Supabase Client Library

### Frontend

```bash
cd /app/frontend
yarn add @supabase/supabase-js
```

### Backend (Optional - if you want to use Supabase Admin SDK)

```bash
cd /app/backend
pip install supabase
```

Add to `requirements.txt`:
```
supabase==2.10.0
```

## 🔄 Step 6: Update Application Routes

The route for OAuth callback is already created. Just make sure to add it to your App.js:

```javascript
import AuthCallback from './pages/AuthCallback';

// In your routes:
<Route path="/auth/callback" element={<AuthCallback />} />
```

## 🎨 Step 7: Add Google Sign-In Button to Sign In Page

Update your SignIn page to include the GoogleAuthButton:

```javascript
import GoogleAuthButton from '../components/GoogleAuthButton';

// In your SignIn component:
<div className="space-y-4">
  <GoogleAuthButton />
  
  <div className="relative">
    <div className="absolute inset-0 flex items-center">
      <div className="w-full border-t border-gray-300" />
    </div>
    <div className="relative flex justify-center text-sm">
      <span className="px-2 bg-white text-gray-500">Or continue with email</span>
    </div>
  </div>
  
  {/* Your existing email/password form */}
</div>
```

## ✅ Step 8: Test Google OAuth

1. Restart both frontend and backend:
   ```bash
   sudo supervisorctl restart all
   ```

2. Navigate to the sign-in page
3. Click "Continue with Google" button
4. You should be redirected to Google OAuth consent screen
5. After authorization, you'll be redirected back to your app
6. The user will be automatically created in your MongoDB database

## 🔍 Verify Setup

Check if Supabase is configured correctly:

1. Backend status endpoint:
   ```bash
   curl http://localhost:8001/api/auth/supabase/status
   ```

2. Frontend check in browser console:
   ```javascript
   import { isSupabaseConfigured } from './lib/supabaseClient';
   console.log('Supabase configured:', isSupabaseConfigured);
   ```

## 📚 Code Files Created

### Backend
- `/app/backend/supabase_config.py` - Supabase configuration and JWT verification
- `/app/backend/routers/supabase_auth.py` - Authentication routes

### Frontend
- `/app/frontend/src/lib/supabaseClient.js` - Supabase client setup
- `/app/frontend/src/components/GoogleAuthButton.jsx` - Google sign-in button
- `/app/frontend/src/pages/AuthCallback.jsx` - OAuth callback handler

## 🐛 Troubleshooting

### Issue: "Supabase is not configured" error
**Solution:** Make sure all environment variables are set correctly and restart services.

### Issue: OAuth redirect doesn't work
**Solution:** 
1. Verify redirect URI in Google Cloud Console matches Supabase callback URL exactly
2. Check that the URL includes `/auth/v1/callback` path

### Issue: Token verification fails
**Solution:** 
1. Ensure JWT Secret is correct in backend .env
2. Check token format (should be Bearer token)

### Issue: User not created in MongoDB
**Solution:**
1. Check backend logs: `tail -f /var/log/supervisor/backend.err.log`
2. Verify MongoDB connection
3. Check `/api/auth/supabase/verify` endpoint

## 🔒 Security Best Practices

1. **Never commit .env files** to version control
2. **Rotate secrets regularly** in production
3. **Use HTTPS** in production (required for OAuth)
4. **Configure OAuth consent screen** properly
5. **Limit OAuth scopes** to only what you need (email, profile)
6. **Enable email verification** in Supabase settings
7. **Set up proper CORS** in Supabase dashboard

## 📖 Additional Resources

- [Supabase Authentication Docs](https://supabase.com/docs/guides/auth)
- [Google OAuth 2.0 Guide](https://developers.google.com/identity/protocols/oauth2)
- [Supabase JavaScript Client](https://supabase.com/docs/reference/javascript/introduction)

## 🎯 What's Next?

1. Add more OAuth providers (GitHub, Facebook, etc.)
2. Implement email/password authentication via Supabase
3. Add user profile management
4. Set up Row Level Security (RLS) in Supabase
5. Configure email templates in Supabase

---

**Note:** This setup is ready for production. Just add your Supabase credentials and Google OAuth keys to activate Google authentication!
