import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import Card from "../../components/Card";
import Button from "../../components/Button";
import Input from "../../components/Input";
import { generatePhoneOTP, verifyPhoneOTP } from "../../services/authService";

export default function VerifyPhoneOTP() {
  const [searchParams] = useSearchParams();
  const [phone, setPhone] = useState(searchParams.get("phone") || "");
  const [otp, setOtp] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    try {
      setError("");
      const res = await generatePhoneOTP(phone);
      const generated = res.data?.otp ? ` OTP: ${res.data.otp}` : "";
      setMessage(`Phone OTP generated.${generated}`);
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Unable to generate phone OTP.");
    }
  };

  const handleVerify = async (e) => {
    e.preventDefault();

    try {
      setLoading(true);
      setError("");
      setMessage("");
      await verifyPhoneOTP(phone, otp);
      setMessage("Phone verified successfully.");
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Invalid or expired OTP.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="auth-layout">
      <Card variant="glass" className="auth-form-card animate-float-in" style={{ width: "min(560px, 92vw)" }}>
        <h2>Verify Phone OTP</h2>
        <p className="muted-text">Generate and verify OTP for phone verification.</p>

        <form onSubmit={handleVerify} className="auth-form">
          <Input
            label="Phone"
            placeholder="+91XXXXXXXXXX"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            required
          />
          <Input
            label="OTP"
            placeholder="123456"
            value={otp}
            onChange={(e) => setOtp(e.target.value)}
            required
          />

          {message ? <p className="status-text success">{message}</p> : null}
          {error ? <p className="status-text error">{error}</p> : null}

          <div className="form-actions-inline">
            <Button type="button" variant="secondary" onClick={handleGenerate}>
              Generate OTP
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? "Verifying..." : "Verify Phone"}
            </Button>
          </div>
        </form>

        <p className="auth-link-row">
          Back to <Link to="/verify">Email OTP</Link>
        </p>
      </Card>
    </main>
  );
}
