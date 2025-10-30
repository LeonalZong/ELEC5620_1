import { authService } from '@/services/authService';

let refreshTimer: NodeJS.Timeout | null = null;

/**
 * Decode JWT token to get expiration time
 */
function decodeToken(token: string): { exp: number } | null {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch (error) {
    console.error('Failed to decode token:', error);
    return null;
  }
}

/**
 * Start automatic token refresh
 */
export function startTokenRefresh() {
  // Clear existing timer
  if (refreshTimer) {
    clearInterval(refreshTimer);
  }

  // Check token every minute
  refreshTimer = setInterval(async () => {
    const token = localStorage.getItem('access_token');
    const refreshToken = localStorage.getItem('refresh_token');

    if (!token || !refreshToken) {
      return;
    }

    const decoded = decodeToken(token);
    if (!decoded) {
      return;
    }

    // Get expiration time in milliseconds
    const expiresAt = decoded.exp * 1000;
    const now = Date.now();
    const timeUntilExpiry = expiresAt - now;

    // Refresh token if it expires in less than 5 minutes
    if (timeUntilExpiry < 5 * 60 * 1000 && timeUntilExpiry > 0) {
      try {
        console.log('Token expiring soon, refreshing...');
        const response = await authService.refreshToken(refreshToken);
        localStorage.setItem('access_token', response.access_token);
        console.log('Token refreshed successfully');
      } catch (error) {
        console.error('Failed to refresh token:', error);
        // Token refresh failed, redirect to login
        localStorage.clear();
        window.location.href = '/login';
      }
    } else if (timeUntilExpiry <= 0) {
      // Token already expired
      console.log('Token expired, redirecting to login');
      localStorage.clear();
      window.location.href = '/login';
    }
  }, 60000); // Check every minute
}

/**
 * Stop automatic token refresh
 */
export function stopTokenRefresh() {
  if (refreshTimer) {
    clearInterval(refreshTimer);
    refreshTimer = null;
  }
}








