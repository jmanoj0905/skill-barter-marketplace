import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import Card from "../../components/Card";
import Button from "../../components/Button";
import Input from "../../components/Input";
import { resetPassword } from "../../services/authService";

export default function ResetPassword() {
  const navigate = useNavigate();
  const [token, setToken] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      setLoading(true);
      setError("");
      setMessage("");
      await resetPassword(token, newPassword);
      setMessage("Password reset successful. Redirecting to login...");
      setTimeout(() => navigate("/login"), 900);
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Unable to reset password.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="auth-layout">
      <Card variant="glass" className="auth-form-card animate-float-in" style={{ width: "min(560px, 92vw)" }}>
        <h2>Reset Password</h2>
        <p className="muted-text">Use the reset token and create your new password.</p>

        <form onSubmit={handleSubmit} className="auth-form">
          <Input
            label="Reset Token"
            placeholder="Paste token"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            required
          />
          <Input
            label="New Password"
            type="password"
            placeholder="Create a strong password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            required
          />

          {message ? <p className="status-text success">{message}</p> : null}
          {error ? <p className="status-text error">{error}</p> : null}

          <Button type="submit" className="ui-btn--block" disabled={loading}>
            {loading ? "Updating..." : "Reset Password"}
          </Button>
        </form>

        <p className="auth-link-row">
          Back to <Link to="/login">Sign In</Link>
        </p>
      </Card>
    </main>
  );
}
