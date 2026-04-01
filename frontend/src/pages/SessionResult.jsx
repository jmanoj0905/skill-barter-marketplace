// import { useState } from "react";
// import { useParams } from "react-router-dom";
// import api from "../api/api";

// export default function SessionResult() {
//   const { barterId } = useParams();

//   const [driftResult, setDriftResult] = useState(null);
//   const [verdictResult, setVerdictResult] = useState(null);
//   const [trustResult, setTrustResult] = useState(null);
//   const [message, setMessage] = useState("");

//   const sendDriftSummary = async () => {
//     try {
//       const response = await api.post(`/session/${barterId}/drift-summary`, {
//         total_windows: 10,
//         incorrect_windows: 1,
//         percent_incorrect: 10.0,
//         max_consecutive_incorrect: 1,
//         warning_count: 1,
//         terminated_early: false,
//       });
//       setDriftResult(response.data);
//       setMessage("Drift summary submitted successfully");
//     } catch (error) {
//       setMessage(error.response?.data?.detail || "Failed to submit drift summary");
//     }
//   };

//   const generateVerdict = async () => {
//     try {
//       const response = await api.post(`/verdict/${barterId}/generate`);
//       setVerdictResult(response.data);
//       setMessage("Verdict generated successfully");
//     } catch (error) {
//       setMessage(error.response?.data?.detail || "Failed to generate verdict");
//     }
//   };

//   const updateTrust = async () => {
//     try {
//       const response = await api.post(`/trust/${barterId}/update`);
//       setTrustResult(response.data);
//       setMessage("Trust updated successfully");
//     } catch (error) {
//       setMessage(error.response?.data?.detail || "Failed to update trust");
//     }
//   };

//   return (
//     <div className="page">
//       <h1>Session Result</h1>
//       <h2>Barter ID: {barterId}</h2>

//       <div className="button-group">
//         <button onClick={sendDriftSummary}>Submit Drift Summary</button>
//         <button onClick={generateVerdict}>Generate Verdict</button>
//         <button onClick={updateTrust}>Update Trust</button>
//       </div>

//       {message && <p>{message}</p>}

//       {driftResult && (
//         <div className="card">
//           <h3>Drift Summary Result</h3>
//           <pre>{JSON.stringify(driftResult, null, 2)}</pre>
//         </div>
//       )}

//       {verdictResult && (
//         <div className="card">
//           <h3>Verdict Result</h3>
//           <pre>{JSON.stringify(verdictResult, null, 2)}</pre>
//         </div>
//       )}

//       {trustResult && (
//         <div className="card">
//           <h3>Trust Update Result</h3>
//           <pre>{JSON.stringify(trustResult, null, 2)}</pre>
//         </div>
//       )}
//     </div>
//   );
// }

import { useState } from "react";
import { useParams } from "react-router-dom";
import api from "../api/api";

export default function SessionResult() {
  const { barterId } = useParams();

  const [driftResult, setDriftResult] = useState(null);
  const [verdictResult, setVerdictResult] = useState(null);
  const [trustResult, setTrustResult] = useState(null);
  const [message, setMessage] = useState("");

  const sendDriftSummary = async () => {
    try {
      const response = await api.post(`/session/${barterId}/drift-summary`, {
        total_windows: 10,
        incorrect_windows: 1,
        percent_incorrect: 10.0,
        max_consecutive_incorrect: 1,
        warning_count: 1,
        terminated_early: false,
      });
      setDriftResult(response.data);
      setMessage("Drift summary submitted successfully");
    } catch (error) {
      setMessage(error.response?.data?.detail || "Failed to submit drift summary");
    }
  };

  const generateVerdict = async () => {
    try {
      const response = await api.post(`/verdict/${barterId}/generate`);
      setVerdictResult(response.data);
      setMessage("Verdict generated successfully");
    } catch (error) {
      setMessage(error.response?.data?.detail || "Failed to generate verdict");
    }
  };

  const updateTrust = async () => {
    try {
      const response = await api.post(`/trust/${barterId}/update`);
      setTrustResult(response.data);
      setMessage("Trust updated successfully");
    } catch (error) {
      setMessage(error.response?.data?.detail || "Failed to update trust");
    }
  };

  return (
    <div className="page">
      <div className="page-header">
        <div className="top-badge">Session Outcome</div>
        <h1 className="page-title">Session Result</h1>
        <p className="page-subtitle">Review drift summary, generate verdict, and update trust score.</p>
      </div>

      <div className="button-group">
        <button onClick={sendDriftSummary}> Drift Summary</button>
        <button className="btn-success" onClick={generateVerdict}>
          Generate Verdict
        </button>
        <button className="btn-secondary" onClick={updateTrust}>
          Update Trust
        </button>
      </div>

      {message && <div className="message">{message}</div>}

      {driftResult && (
        <div className="card">
          <h3 className="section-title">Drift Summary Result</h3>
          <div className="result-box">
            <pre>{JSON.stringify(driftResult, null, 2)}</pre>
          </div>
        </div>
      )}

      {verdictResult && (
        <div className="card">
          <h3 className="section-title">Verdict Result</h3>
          <div className="result-box">
            <pre>{JSON.stringify(verdictResult, null, 2)}</pre>
          </div>
        </div>
      )}

      {trustResult && (
        <div className="card">
          <h3 className="section-title">Trust Update Result</h3>
          <div className="result-box">
            <pre>{JSON.stringify(trustResult, null, 2)}</pre>
          </div>
        </div>
      )}
    </div>
  );
}