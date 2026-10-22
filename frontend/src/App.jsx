import { BrowserRouter, Routes, Route } from "react-router-dom";

import Register from "./pages/Auth/Register";
import Login from "./pages/Auth/Login";
import VerifyOTP from "./pages/Auth/VerifyOTP";
import VerifyPhoneOTP from "./pages/Auth/VerifyPhoneOTP";
import ForgotPassword from "./pages/Auth/ForgotPassword";
import ResetPassword from "./pages/Auth/ResetPassword";
import Wallet from "./pages/Dashboard/Wallet";
import Dashboard from "./pages/Dashboard/Dashboard";
import Skills from "./pages/Dashboard/Skills";
import Profile from "./pages/Dashboard/Profile";
import ProtectedRoute from "./components/ProtectedRoute";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Register />} />
        <Route path="/login" element={<Login />} />
        <Route path="/verify" element={<VerifyOTP />} />
        <Route path="/verify-phone" element={<VerifyPhoneOTP />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />
        <Route
          path="/wallet"
          element={(
            <ProtectedRoute>
              <Wallet />
            </ProtectedRoute>
          )}
        />
        <Route
          path="/dashboard"
          element={(
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          )}
        />
        <Route
          path="/skills"
          element={(
            <ProtectedRoute>
              <Skills />
            </ProtectedRoute>
          )}
        />
        <Route
          path="/profile"
          element={(
            <ProtectedRoute>
              <Profile />
            </ProtectedRoute>
          )}
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;