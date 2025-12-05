import { BrowserRouter, Route, Routes, Navigate, useLocation } from "react-router-dom";
import React, { useEffect } from "react";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { isTokenExpired } from "./utils/jwt";
import Layout from "./components/Layout";
import HomePage from "./pages/HomePage";
import HistoryPage from "./pages/HistoryPage";
import DetailPage from "./pages/DetailPage";
import LoginPage from "./pages/LoginPage";

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, token, logout } = useAuth();
  const location = useLocation();

  useEffect(() => {
    // Check token expiration on route change
    if (token && isTokenExpired(token)) {
      logout();
    }
  }, [location.pathname, token, logout]);

  if (!isAuthenticated || (token && isTokenExpired(token))) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

const AppRoutes: React.FC = () => {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<HomePage />} />
        <Route path="history" element={<HistoryPage />} />
        <Route path="tailor/:id" element={<DetailPage />} />
      </Route>
    </Routes>
  );
};

const App: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter
        future={{
          v7_startTransition: true,
          v7_relativeSplatPath: true,
        }}
      >
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  );
};

export default App;


