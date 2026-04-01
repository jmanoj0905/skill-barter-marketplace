// import { useEffect, useState } from "react";
// import { useNavigate, useParams } from "react-router-dom";
// import api from "../api/api";

// export default function LiveSession() {
//   const { barterId } = useParams();
//   const navigate = useNavigate();

//   const [statusData, setStatusData] = useState(null);
//   const [warnings, setWarnings] = useState([]);
//   const [message, setMessage] = useState("");

//   const fetchStatus = async () => {
//     try {
//       const response = await api.get(`/session/${barterId}/status`);
//       setStatusData(response.data);
//     } catch (error) {
//       console.error(error);
//     }
//   };

//   const startSession = async () => {
//     try {
//       await api.post(`/session/${barterId}/start`);
//       setMessage("Session started successfully");
//       fetchStatus();
//     } catch (error) {
//       setMessage(error.response?.data?.detail || "Failed to start session");
//     }
//   };

//   const confirmSession = async (userId) => {
//     try {
//       await api.post(`/session/${barterId}/confirm`, { user_id: userId });
//       setMessage(`User ${userId} confirmed successfully`);
//       fetchStatus();
//     } catch (error) {
//       setMessage(error.response?.data?.detail || "Confirmation failed");
//     }
//   };

//   const terminateSession = async () => {
//     try {
//       await api.post(`/session/${barterId}/terminate`, {
//         reason: "Severe drift detected from frontend",
//       });
//       setMessage("Session terminated");
//       fetchStatus();
//     } catch (error) {
//       setMessage(error.response?.data?.detail || "Termination failed");
//     }
//   };

//   useEffect(() => {
//     fetchStatus();

//     const interval = setInterval(fetchStatus, 5000);

//     const ws = new WebSocket(`ws://127.0.0.1:8000/warnings/ws/${barterId}`);

//     ws.onopen = () => {
//       ws.send("hello");
//     };

//     ws.onmessage = (event) => {
//       const data = JSON.parse(event.data);
//       setWarnings((prev) => [data, ...prev]);
//     };

//     ws.onerror = (error) => {
//       console.error("WebSocket error:", error);
//     };

//     return () => {
//       clearInterval(interval);
//       ws.close();
//     };
//   }, [barterId]);

//   return (
//     <div className="page">
//       <h1>Live Session</h1>
//       <h2>Barter ID: {barterId}</h2>

//       {statusData && (
//         <div className="card">
//           <p><strong>Status:</strong> {statusData.status}</p>
//           <p><strong>Elapsed Minutes:</strong> {statusData.elapsed_minutes}</p>
//           <p><strong>Agreed Duration:</strong> {statusData.agreed_duration_minutes}</p>
//           <p><strong>Both Confirmed:</strong> {statusData.both_confirmed ? "Yes" : "No"}</p>
//         </div>
//       )}

//       <div className="button-group">
//         <button onClick={startSession}>Start Session</button>
//         <button onClick={() => confirmSession(1)}>Confirm as Alice</button>
//         <button onClick={() => confirmSession(2)}>Confirm as Bob</button>
//         <button onClick={terminateSession}>Terminate Session</button>
//         <button onClick={() => navigate(`/result/${barterId}`)}>Go to Result</button>
//       </div>

//       {message && <p>{message}</p>}

//       <div className="card">
//         <h3>Live Warnings</h3>
//         {warnings.length === 0 ? (
//           <p>No warnings yet</p>
//         ) : (
//           warnings.map((warning, index) => (
//             <div key={index} className="warning-box">
//               <p><strong>Severity:</strong> {warning.severity}</p>
//               <p><strong>Reason:</strong> {warning.reason}</p>
//               <p><strong>Window IDs:</strong> {warning.window_ids}</p>
//               <p><strong>Timestamp:</strong> {warning.timestamp}</p>
//             </div>
//           ))
//         )}
//       </div>
//     </div>
//   );
// }

import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api from "../api/api";

export default function LiveSession() {
  const { barterId } = useParams();
  const navigate = useNavigate();

  const [statusData, setStatusData] = useState(null);
  const [warnings, setWarnings] = useState([]);
  const [message, setMessage] = useState("");

  const fetchStatus = async () => {
    try {
      const response = await api.get(`/session/${barterId}/status`);
      setStatusData(response.data);
    } catch (error) {
      console.error(error);
    }
  };

  const startSession = async () => {
    try {
      await api.post(`/session/${barterId}/start`);
      setMessage("Session started successfully");
      fetchStatus();
    } catch (error) {
      setMessage(error.response?.data?.detail || "Failed to start session");
    }
  };

  const confirmSession = async (userId) => {
    try {
      await api.post(`/session/${barterId}/confirm`, { user_id: userId });
      setMessage(`User ${userId} confirmed successfully`);
      fetchStatus();
    } catch (error) {
      setMessage(error.response?.data?.detail || "Confirmation failed");
    }
  };

  const terminateSession = async () => {
    try {
      await api.post(`/session/${barterId}/terminate`, {
        reason: "Severe drift detected from frontend",
      });
      setMessage("Session terminated successfully");
      fetchStatus();
    } catch (error) {
      setMessage(error.response?.data?.detail || "Termination failed");
    }
  };

  useEffect(() => {
    fetchStatus();

    const interval = setInterval(fetchStatus, 5000);
    const ws = new WebSocket(`ws://127.0.0.1:8000/warnings/ws/${barterId}`);

    ws.onopen = () => {
      ws.send("hello");
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setWarnings((prev) => [data, ...prev]);
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    return () => {
      clearInterval(interval);
      ws.close();
    };
  }, [barterId]);

  return (
    <div className="page">
      <div className="page-header">
        <div className="top-badge">Live Monitoring</div>
        <h1 className="page-title">Live Session</h1>
        <p className="page-subtitle">Track session progress, confirmations, and warnings in real time.</p>
      </div>

      <div className="card">
        <h3 className="section-title">Session Info</h3>
        <div className="info-grid">
          <div className="info-item">
            <span className="info-label">Barter ID</span>
            <span className="info-value">{barterId}</span>
          </div>

          <div className="info-item">
            <span className="info-label">Status</span>
            <span className="info-value">{statusData?.status || "Not loaded"}</span>
          </div>

          <div className="info-item">
            <span className="info-label">Elapsed Minutes</span>
            <span className="info-value">{statusData?.elapsed_minutes ?? "-"}</span>
          </div>

          <div className="info-item">
            <span className="info-label">Agreed Duration</span>
            <span className="info-value">{statusData?.agreed_duration_minutes ?? "-"} min</span>
          </div>

          <div className="info-item">
            <span className="info-label">Both Confirmed</span>
            <span className="info-value">{statusData?.both_confirmed ? "Yes" : "No"}</span>
          </div>
        </div>
      </div>

      <div className="button-group">
        <button onClick={startSession}>Start Session</button>
        <button className="btn-success" onClick={() => confirmSession(1)}>
          Confirm as Alice
        </button>
        <button className="btn-success" onClick={() => confirmSession(2)}>
          Confirm as Bob
        </button>
        <button className="btn-danger" onClick={terminateSession}>
          Terminate Session
        </button>
        <button className="btn-secondary" onClick={() => navigate(`/result/${barterId}`)}>
          Go to Result
        </button>
      </div>

      {message && <div className="message">{message}</div>}

      <div className="card">
        <h3 className="section-title">Live Warnings</h3>
        {warnings.length === 0 ? (
          <p style={{ color: "#94a3b8" }}>No warnings received yet.</p>
        ) : (
          warnings.map((warning, index) => (
            <div key={index} className="warning-box">
              <p><strong>Severity:</strong> {warning.severity}</p>
              <p><strong>Reason:</strong> {warning.reason}</p>
              <p><strong>Window IDs:</strong> {warning.window_ids}</p>
              <p><strong>Timestamp:</strong> {warning.timestamp}</p>
            </div>
          ))
        )}
      </div>
    </div>
  );
}