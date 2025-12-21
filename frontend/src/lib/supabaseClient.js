/**
 * Supabase Client Configuration for Google OAuth Authentication
 * 
 * This file initializes the Supabase client for authentication.
 * To use in production:
 * 1. Set REACT_APP_SUPABASE_URL in .env
 * 2. Set REACT_APP_SUPABASE_ANON_KEY in .env
 * 3. Configure Google OAuth in Supabase Dashboard
 */

import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.REACT_APP_SUPABASE_URL || '';
const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY || '';

// Check if Supabase is configured
export const isSupabaseConfigured = Boolean(supabaseUrl && supabaseAnonKey);

// Create Supabase client
export const supabase = isSupabaseConfigured
  ? createClient(supabaseUrl, supabaseAnonKey)
  : null;

/**
 * Sign in with Google OAuth
 * @returns {Promise<void>}
 */
export const signInWithGoogle = async () => {
  if (!supabase) {
    throw new Error('Supabase is not configured');
  }

  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo: `${window.location.origin}/auth/callback`,
    },
  });

  if (error) {
    throw error;
  }

  return data;
};

/**
 * Sign out from Supabase
 * @returns {Promise<void>}
 */
export const signOut = async () => {
  if (!supabase) {
    throw new Error('Supabase is not configured');
  }

  const { error } = await supabase.auth.signOut();

  if (error) {
    throw error;
  }
};

/**
 * Get current Supabase session
 * @returns {Promise<Session | null>}
 */
export const getSession = async () => {
  if (!supabase) {
    return null;
  }

  const { data: { session } } = await supabase.auth.getSession();
  return session;
};

/**
 * Get current Supabase user
 * @returns {Promise<User | null>}
 */
export const getCurrentUser = async () => {
  if (!supabase) {
    return null;
  }

  const { data: { user } } = await supabase.auth.getUser();
  return user;
};

/**
 * Listen to auth state changes
 * @param {Function} callback - Callback function to handle auth state changes
 * @returns {Object} Subscription object with unsubscribe method
 */
export const onAuthStateChange = (callback) => {
  if (!supabase) {
    return { data: { subscription: { unsubscribe: () => {} } } };
  }

  return supabase.auth.onAuthStateChange(callback);
};
