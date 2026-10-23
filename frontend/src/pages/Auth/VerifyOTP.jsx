import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import Button from "../../components/Button";
import Card from "../../components/Card";
import Input from "../../components/Input";
import { generateEmailOTP, resendEmailOTP, verifyOTP } from "../../services/authService";

export default function VerifyOTP() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [email, setEmail] = useState(searchParams.get("email") || "");
  const [otp, setOtp] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [devOtp, setDevOtp] = useState("");

  useEffect(() => {
    if (!email) return;

    generateEmailOTP(email)
      .then((res) => {
        if (res.data?.otp) {
          setDevOtp(String(res.data.otp));
          setInfo("OTP generated and sent to email.");
        }
      })
      .catch(() => {
        // OTP may already be sent; user can still resend manually.
      });
  }, [email]);

  const verify = async (e) => {
    e.preventDefault();

    try {
      setLoading(true);
      setError("");
      await verifyOTP({ email, otp });
      navigate("/login");
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Invalid or expired OTP. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const resendOtp = async () => {
    try {
      setInfo("");
      setError("");
      const res = await resendEmailOTP(email);
      if (res.data?.otp) {
        setDevOtp(String(res.data.otp));
      }
      setInfo("A new OTP has been sent to your email.");
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Unable to resend OTP right now.");
    }
  };

  return (
    <main className="auth-layout">
      <Card variant="glass" className="auth-form-card animate-float-in" style={{ width: "min(520px, 92vw)" }}>
        <h2>Verify OTP</h2>
        <p className="muted-text">
          Enter the 6-digit code sent to your email to complete onboarding.
        </p>

        <form onSubmit={verify} className="auth-form">
          <Input
            label="Email"
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <Input
            label="One-Time Password"
            placeholder="123456"
            value={otp}
            onChange={(e) => setOtp(e.target.value)}
            required
          />

          {error ? <p className="status-text error">{error}</p> : null}
          {info ? <p className="status-text success">{info}</p> : null}
          {devOtp ? (
            <div className="inline-token-box">
              <p className="inline-token-box__label">Development OTP</p>
              <p className="inline-token-box__value">{devOtp}</p>
            </div>
          ) : null}

          <Button type="submit" className="ui-btn--block" disabled={loading}>
            {loading ? "Verifying..." : "Verify OTP"}
          </Button>
          <Button type="button" variant="secondary" className="ui-btn--block" onClick={resendOtp}>
            Resend OTP
          </Button>
        </form>

        <p className="auth-link-row">
          Verify phone at{" "}
          <Link to="/verify-phone">
            Phone OTP
          </Link>
          {" "}or back to{" "}
          <Link to="/login">
            Login
          </Link>
        </p>
      </Card>
    </main>
  );
}