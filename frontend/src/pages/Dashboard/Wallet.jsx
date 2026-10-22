import { useEffect, useState } from "react";
import Navbar from "../../components/Navbar";
import Card from "../../components/Card";
import { getCurrentUserId } from "../../utils/auth";
import { getWallet, getWalletHistory } from "../../services/walletService";

export default function Wallet() {
  const [wallet, setWallet] = useState({
    available_balance: 0,
    locked_balance: 0,
    total_earned: 0,
    total_spent: 0
  });
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const userId = getCurrentUserId();

    if (!userId) {
      setError("Session expired. Please login again.");
      setLoading(false);
      return;
    }

    getWallet(userId)
      .then((walletRes) => {
        setWallet((prev) => ({ ...prev, ...walletRes.data }));
      })
      .catch((err) => {
        const detail = err?.response?.data?.detail;
        setError(typeof detail === "string" ? detail : "Unable to load wallet data right now.");
      })
      .finally(() => setLoading(false));

    getWalletHistory(userId, 1)
      .then((historyRes) => {
        const txs = Array.isArray(historyRes.data)
          ? historyRes.data
          : historyRes.data?.transactions || historyRes.data?.items || [];
        setHistory(txs);
      })
      .catch(() => {
        setHistory([]);
      });
  }, []);

  const cards = [
    { label: "Available", value: wallet.available_balance ?? 0, tone: "text-emerald-700" },
    { label: "Locked", value: wallet.locked_balance ?? 0, tone: "text-amber-700" },
    { label: "Total Earned", value: wallet.total_earned ?? 0, tone: "text-cyan-700" },
    { label: "Total Spent", value: wallet.total_spent ?? 0, tone: "text-rose-700" }
  ];

  return (
    <div className="page-shell">
      <Navbar />

      <main className="page-container">
        <section className="dashboard-hero animate-float-in">
          <p className="auth-chip">Credit Wallet</p>
          <h1>Track your marketplace balance</h1>
          <p>
            Manage credits earned from teaching sessions and credits locked in escrow.
          </p>
        </section>

        <section className="stats-grid">
          {cards.map((item) => (
            <Card key={item.label} className="stat-card animate-float-in">
              <p className="stat-card__label">{item.label}</p>
              <p className={`stat-card__value ${item.tone}`}>{item.value}</p>
            </Card>
          ))}
        </section>

        <Card className="wallet-table-wrap" style={{ padding: 0 }}>
          <div className="wallet-table-head">
            <h2>Recent Transactions</h2>
            <p className="muted-text" style={{ marginTop: 6 }}>Your latest wallet activity</p>
          </div>

          {loading ? (
            <p className="status-text muted-text" style={{ padding: "12px 20px" }}>Loading wallet details...</p>
          ) : error ? (
            <p className="status-text error" style={{ padding: "12px 20px" }}>{error}</p>
          ) : history.length === 0 ? (
            <p className="status-text muted-text" style={{ padding: "12px 20px" }}>No transactions yet.</p>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table className="wallet-table">
                <thead>
                  <tr>
                    <th>Amount</th>
                    <th>Type</th>
                    <th>Description</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((tx, index) => (
                    <tr key={tx.id || tx.transaction_id || index}>
                      <td style={{ fontWeight: 700 }}>{tx.amount ?? 0}</td>
                      <td>
                        <span className="wallet-pill">
                          {tx.type || "transaction"}
                        </span>
                      </td>
                      <td className="muted-text">{tx.description || "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </main>
    </div>
  );
}
