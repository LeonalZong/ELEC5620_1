import { useEffect, useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Spin } from 'antd';
import { useAuthStore } from './stores/authStore';
import Login from './pages/auth/Login';
import Register from './pages/auth/Register';
import InvestorLayout from './pages/investor/InvestorLayout';
import AdvisorLayout from './pages/advisor/AdvisorLayout';
import AdminLayout from './pages/admin/AdminLayout';
import { UserRole } from './types';
import { startTokenRefresh, stopTokenRefresh } from './utils/tokenRefresh';

// Private Route Component
interface PrivateRouteProps {
  children: React.ReactNode;
  allowedRoles?: UserRole[];
}

const PrivateRoute: React.FC<PrivateRouteProps> = ({ children, allowedRoles }) => {
  const { isAuthenticated, user } = useAuthStore();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && user && !allowedRoles.includes(user.role)) {
    // Redirect to appropriate dashboard based on role
    switch (user.role) {
      case UserRole.INVESTOR:
        return <Navigate to="/investor" replace />;
      case UserRole.ADVISOR:
        return <Navigate to="/advisor" replace />;
      case UserRole.ADMIN:
        return <Navigate to="/admin" replace />;
      default:
        return <Navigate to="/login" replace />;
    }
  }

  return <>{children}</>;
};

function App() {
  const { isAuthenticated, user, checkAuth } = useAuthStore();
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);

  // Check authentication status on app mount
  useEffect(() => {
    const initAuth = async () => {
      try {
        await checkAuth();
      } finally {
        setIsCheckingAuth(false);
      }
    };
    
    initAuth();
  }, [checkAuth]);

  // Start automatic token refresh when authenticated
  useEffect(() => {
    if (isAuthenticated) {
      startTokenRefresh();
    }

    return () => {
      stopTokenRefresh();
    };
  }, [isAuthenticated]);

  // Show loading spinner while checking authentication
  if (isCheckingAuth) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh' 
      }}>
        <Spin size="large" tip="Loading..." />
      </div>
    );
  }

  return (
    <Routes>
      {/* Public Routes */}
      <Route
        path="/login"
        element={isAuthenticated ? <Navigate to={`/${user?.role.toLowerCase()}`} replace /> : <Login />}
      />
      <Route
        path="/register"
        element={isAuthenticated ? <Navigate to={`/${user?.role.toLowerCase()}`} replace /> : <Register />}
      />

      {/* Investor Routes */}
      <Route
        path="/investor/*"
        element={
          <PrivateRoute allowedRoles={[UserRole.INVESTOR]}>
            <InvestorLayout />
          </PrivateRoute>
        }
      />

      {/* Advisor Routes */}
      <Route
        path="/advisor/*"
        element={
          <PrivateRoute allowedRoles={[UserRole.ADVISOR]}>
            <AdvisorLayout />
          </PrivateRoute>
        }
      />

      {/* Admin Routes */}
      <Route
        path="/admin/*"
        element={
          <PrivateRoute allowedRoles={[UserRole.ADMIN]}>
            <AdminLayout />
          </PrivateRoute>
        }
      />

      {/* Default Route */}
      <Route
        path="/"
        element={
          isAuthenticated && user ? (
            <Navigate to={`/${user.role.toLowerCase()}`} replace />
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />

      {/* 404 Route */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;

