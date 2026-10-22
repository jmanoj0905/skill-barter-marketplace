import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { loginUser } from "../../services/authService";
import Button from "../../components/Button";
import Card from "../../components/Card";
import Input from "../../components/Input";
import { generateFingerprint } from "../../utils/fingerprint";

export default function Login() {
  const navigate = useNavigate();
  const [data, setData] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const login = async (e) => {
    e.preventDefault();

    try {
      setLoading(true);
      setError("");
      const fingerprint = generateFingerprint();
      const res = await loginUser(data, fingerprint);

      localStorage.setItem("token", res.data.access_token);

      navigate("/wallet");
    } catch (err) {
      const detail =
        err?.response?.data?.detail ||
        err?.message ||
        "Login failed. Check email/password and try again.";

      setError(typeof detail === "string" ? detail : "Login failed. Try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="auth-layout">
      <Card variant="glass" className="auth-form-card animate-float-in" style={{ width: "min(520px, 92vw)" }}>
        <p className="auth-chip" style={{ borderColor: "#9fd6df", color: "#0a707d", background: "#e8f7fb" }}>
          Secure Sign In
        </p>
        <h2>Welcome Back</h2>
        <p className="muted-text">Continue your learning and teaching journey.</p>

        <form onSubmit={login} className="auth-form">
          <Input
            label="Email"
            type="email"
            placeholder="you@example.com"
            value={data.email}
            onChange={(e) => setData({ ...data, email: e.target.value })}
            required
          />
          <Input
            label="Password"
            type="password"
            placeholder="Your password"
            value={data.password}
            onChange={(e) => setData({ ...data, password: e.target.value })}
            required
          />

          {error ? <p className="status-text error">{error}</p> : null}

          <Button type="submit" className="ui-btn--block" disabled={loading}>
            {loading ? "Signing in..." : "Sign In"}
          </Button>
        </form>

        <p className="auth-link-row">
          New here?{" "}
          <Link to="/">
            Create an account
          </Link>
          {" "}•{" "}
          <Link to="/forgot-password">
            Forgot password?
          </Link>
        </p>
      </Card>
    </main>
  );
}