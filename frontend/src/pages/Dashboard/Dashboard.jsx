import { useEffect, useState } from "react";
import Card from "../../components/Card";
import Navbar from "../../components/Navbar";
import { getCurrentUserId } from "../../utils/auth";
import { getProfile } from "../../services/userService";
import { getSkills } from "../../services/skillService";
import { getWalletBalance } from "../../services/walletService";

export default function Dashboard() {
  const userId = getCurrentUserId();
  const [summary, setSummary] = useState({
    identityConfidence: "0.00",
    trustScore: "0.00",
    offeredCount: 0,
    desiredCount: 0,
    availableBalance: 0,
    lockedBalance: 0,
    name: ""
  });
  const [error, setError] = useState("");

  useEffect(() => {
    if (!userId) return;

    Promise.all([
      getProfile(userId),
      getSkills(userId),
      getWalletBalance(userId)
    ])
      .then(([profileRes, skillsRes, walletRes]) => {
        const offered = skillsRes.data?.offered || [];
        const desired = skillsRes.data?.desired || [];

        setSummary({
          identityConfidence: Number(profileRes.data?.identity_confidence_score || 0).toFixed(2),
          trustScore: Number(profileRes.data?.trust_score || 0).toFixed(2),
          offeredCount: offered.length,
          desiredCount: desired.length,
          availableBalance: walletRes.data?.available_balance || 0,
          lockedBalance: walletRes.data?.locked_balance || 0,
          name: profileRes.data?.email || `User ${userId}`
        });
      })
      .catch((err) => {
        const detail = err?.response?.data?.detail;
        setError(typeof detail === "string" ? detail : "Unable to load dashboard data.");
      });
  }, [userId]);

  const highlights = [
    { title: "Identity Confidence", value: summary.identityConfidence },
    { title: "Trust Score", value: summary.trustScore },
    { title: "Offered Skills", value: String(summary.offeredCount) },
    { title: "Desired Skills", value: String(summary.desiredCount) },
    { title: "Available Credits", value: String(summary.availableBalance) },
    { title: "Locked Credits", value: String(summary.lockedBalance) }
  ];

  return (
    <div className="page-shell">
      <Navbar />
      <main className="page-container">
        <section className="dashboard-hero animate-float-in">
          <h1>Your Learning Hub</h1>
          <p>
            Track your growth, trust, skills, and wallet activity in one place.
          </p>
          <p className="dashboard-subline">Signed in as {summary.name}</p>
          {!userId ? <p className="status-text error">Session expired. Please login again.</p> : null}
          {error ? <p className="status-text error">{error}</p> : null}
        </section>

        <section className="stats-grid stats-grid--3">
          {highlights.map((item) => (
            <Card key={item.title} className="stat-card animate-float-in">
              <p className="stat-card__label">{item.title}</p>
              <p className="stat-card__value">{item.value}</p>
            </Card>
          ))}
        </section>
      </main>
    </div>
  );
}