import { Navigate } from "react-router-dom";
import { getCurrentUserId, getToken } from "../utils/auth";

export default function ProtectedRoute({ children }) {
  const token = getToken();
  const userId = getCurrentUserId();

  if (!token || !userId) {
    return <Navigate to="/login" replace />;
  }

  return children;
}
