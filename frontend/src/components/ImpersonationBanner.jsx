import React, { useEffect, useState } from 'react';
import { AlertTriangle, LogOut, Shield } from 'lucide-react';

const ImpersonationBanner = () => {
  const [isImpersonating, setIsImpersonating] = useState(false);
  const [impersonatedUser, setImpersonatedUser] = useState(null);

  useEffect(() => {
    // Check if in impersonation mode
    const impersonationMode = localStorage.getItem('impersonationMode');
    const userStr = localStorage.getItem('user');
    
    if (impersonationMode === 'true' && userStr) {
      try {
        const user = JSON.parse(userStr);
        if (user.impersonated) {
          setIsImpersonating(true);
          setImpersonatedUser(user);
        }
      } catch (error) {
        console.error('Error parsing user data:', error);
      }
    }
  }, []);

  const handleExitImpersonation = () => {
    // Clear impersonation data
    localStorage.removeItem('impersonationMode');
    localStorage.removeItem('user');
    localStorage.removeItem('isAuthenticated');
    
    // Close this tab
    window.close();
    
    // If window.close() doesn't work (some browsers prevent it), redirect to signin
    setTimeout(() => {
      window.location.href = '/signin';
    }, 100);
  };

  if (!isImpersonating || !impersonatedUser) {
    return null;
  }

  return (
    <div className="fixed top-0 left-0 right-0 z-50 bg-gradient-to-r from-yellow-500 via-orange-500 to-red-500 text-white shadow-lg">
      <div className="container mx-auto px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 bg-white/20 backdrop-blur-sm px-3 py-1.5 rounded-full">
              <Shield className="w-4 h-4" />
              <span className="text-sm font-semibold">ADMIN IMPERSONATION MODE</span>
            </div>
            
            <div className="flex items-center gap-2 text-sm">
              <AlertTriangle className="w-4 h-4" />
              <span>
                Viewing as: <strong>{impersonatedUser.name || impersonatedUser.email}</strong>
              </span>
            </div>
          </div>

          <button
            onClick={handleExitImpersonation}
            className="flex items-center gap-2 bg-white text-red-600 px-4 py-2 rounded-lg font-semibold hover:bg-red-50 transition-colors shadow-md"
          >
            <LogOut className="w-4 h-4" />
            Exit Impersonation
          </button>
        </div>
      </div>
    </div>
  );
};

export default ImpersonationBanner;
