import { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import ProtectedRoute from './components/ProtectedRoute';
import { useAuthStore } from './stores';
import {
  Home,
  Login,
  Register,
  Dashboard,
  Skills,
  Discover,
  Barters,
  BarterDetail,
  Wallet,
  Profile,
} from './pages';


function App() {
  const { initializeAuth } = useAuthStore();

  useEffect(() => {
    // Auto-login as User A on app start
    initializeAuth();
  }, [initializeAuth]);

  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route
          path="/login"
          element={ <Login />}
        />
        <Route
          path="/register"
          element={ <Register />}
        />
        <Route
          path="/dashboard"
          element={<ProtectedRoute><Dashboard /></ProtectedRoute>}
        />
        <Route
          path="/skills"
          element={<ProtectedRoute><Skills /></ProtectedRoute>}
        />
        <Route
          path="/discover"
          element={<ProtectedRoute><Discover /></ProtectedRoute>}
        />
        <Route
          path="/barters"
          element={<ProtectedRoute><Barters /></ProtectedRoute>}
        />
        <Route
          path="/barters/:barterId"
          element={<ProtectedRoute><BarterDetail /></ProtectedRoute>}
        />
        <Route
          path="/wallet"
          element={<ProtectedRoute><Wallet /></ProtectedRoute>}
        />
        <Route
          path="/profile"
          element={<ProtectedRoute><Profile /></ProtectedRoute>}
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
