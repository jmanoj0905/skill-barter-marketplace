import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import Button from "../../components/Button";
import Card from "../../components/Card";
import Input from "../../components/Input";
import { registerUser, generateEmailOTP } from "../../services/authService";
import { checkUsernameAvailability } from "../../services/userService";
import { generateFingerprint } from "../../utils/fingerprint";

export default function Register() {
  const navigate = useNavigate();
  const [data, setData] = useState({
    email: "",
    password: "",
    name: "",
    phone: ""
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [nameStatus, setNameStatus] = useState("");

  const passwordRuleText =
    "At least 8 chars, one uppercase, one number, and one special character.";

  const isPasswordStrong = (value) => {
    return /^(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$/.test(value);
  };

  const checkUsername = async () => {
    const name = data.name.trim();

    if (!name) {
      setNameStatus("");
      return;
    }

    try {
      const res = await checkUsernameAvailability(name);
      setNameStatus(res.data?.available ? "Name is available" : "Name is already taken");
    } catch {
      setNameStatus("Could not check name right now");
    }
  };

  const register = async (e) => {
    e.preventDefault();

    if (!isPasswordStrong(data.password)) {
      setMessage(`Password is weak. ${passwordRuleText}`);
      return;
    }

    try {
      setLoading(true);
      setMessage("");
      const fingerprint = generateFingerprint();
      await registerUser(data, fingerprint);
      await generateEmailOTP(data.email);
      navigate(`/verify?email=${encodeURIComponent(data.email)}`);
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setMessage(typeof detail === "string" ? detail : "Registration failed. Please check your details and try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="auth-layout">
      <div className="auth-shell animate-float-in">
        <section className="auth-hero">
          <p className="auth-chip">
            Learn. Share. Grow.
          </p>
          <h1>
            Find people to learn with and teach what you love.
          </h1>
          <p>
            Exchange skills with trusted learners, build your profile, and grow through real sessions.
          </p>
          <div className="auth-points">
            <p className="auth-point">Discover skill partners based on your goals</p>
            <p className="auth-point">Plan flexible sessions that fit your schedule</p>
            <p className="auth-point">Earn credits and build a strong reputation</p>
          </div>
        </section>

        <section className="auth-form-wrap">
          <Card variant="glass" className="auth-form-card">
            <h2>Create Account</h2>
            <p className="muted-text">Set up your profile to start bartering skills.</p>

            <form onSubmit={register} className="auth-form">
              <Input
                label="Name"
                placeholder="Your full name"
                value={data.name}
                onChange={(e) => setData({ ...data, name: e.target.value })}
                onBlur={checkUsername}
                required
              />
              {nameStatus ? (
                <p className={`status-text ${nameStatus.includes("available") ? "success" : "error"}`}>{nameStatus}</p>
              ) : null}
              <Input
                label="Email"
                type="email"
                placeholder="you@example.com"
                value={data.email}
                onChange={(e) => setData({ ...data, email: e.target.value })}
                required
              />
              <Input
                label="Phone"
                placeholder="+91 XXXXX XXXXX"
                value={data.phone}
                onChange={(e) => setData({ ...data, phone: e.target.value })}
                required
              />
              <Input
                label="Password"
                type="password"
                placeholder="Create a strong password"
                value={data.password}
                onChange={(e) => setData({ ...data, password: e.target.value })}
                required
              />
              <p className="status-text muted-text" style={{ marginTop: 0 }}>{passwordRuleText}</p>

              {message ? <p className="status-text error">{message}</p> : null}

              <Button type="submit" className="ui-btn--block" disabled={loading}>
                {loading ? "Creating account..." : "Create Account"}
              </Button>
            </form>

            <p className="auth-link-row">
              Already have an account?{" "}
              <Link to="/login">
                Sign in
              </Link>
            </p>
          </Card>
        </section>
      </div>
    </main>
  );
}