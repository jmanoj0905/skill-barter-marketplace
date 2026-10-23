import { useState } from "react";
import { Link } from "react-router-dom";
import Card from "../../components/Card";
import Button from "../../components/Button";
import Input from "../../components/Input";
import { forgotPassword } from "../../services/authService";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [resetToken, setResetToken] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      setLoading(true);
      setError("");
      setMessage("");
      const res = await forgotPassword(email);
      setResetToken(res.data?.reset_token || "");
      setMessage("Reset token generated. Use it on the reset password page.");
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Unable to process request.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="auth-layout">
      <Card variant="glass" className="auth-form-card animate-float-in" style={{ width: "min(560px, 92vw)" }}>
        <h2>Forgot Password</h2>
        <p className="muted-text">Enter your registered email to generate a reset token.</p>

        <form onSubmit={handleSubmit} className="auth-form">
          <Input
            label="Email"
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />

          {message ? <p className="status-text success">{message}</p> : null}
          {error ? <p className="status-text error">{error}</p> : null}

          {resetToken ? (
            <div className="inline-token-box">
              <p className="inline-token-box__label">Reset token</p>
              <p className="inline-token-box__value">{resetToken}</p>
            </div>
          ) : null}

          <Button type="submit" className="ui-btn--block" disabled={loading}>
            {loading ? "Generating..." : "Generate Reset Token"}
          </Button>
        </form>

        <p className="auth-link-row">
          Go to <Link to="/reset-password">Reset Password</Link> or <Link to="/login">Sign In</Link>
        </p>
      </Card>
    </main>
  );
}
