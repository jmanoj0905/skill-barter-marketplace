// import { useState } from "react";
// import { useNavigate } from "react-router-dom";
// import api from "../api/api";

// export default function CreateSession() {
//   const navigate = useNavigate();

//   const [formData, setFormData] = useState({
//     skill_a: "",
//     skill_b: "",
//     topic: "",
//     scope: "",
//     allowed_concepts: "",
//     disallowed_concepts: "",
//     agreed_duration_minutes: "",
//   });

//   const [loading, setLoading] = useState(false);
//   const [message, setMessage] = useState("");

//   const handleChange = (e) => {
//     setFormData({
//       ...formData,
//       [e.target.name]: e.target.value,
//     });
//   };

//   const handleSubmit = async (e) => {
//     e.preventDefault();
//     setLoading(true);
//     setMessage("");

//     try {
//       const payload = {
//         ...formData,
//         allowed_concepts: formData.allowed_concepts
//           .split(",")
//           .map((item) => item.trim())
//           .filter(Boolean),
//         disallowed_concepts: formData.disallowed_concepts
//           .split(",")
//           .map((item) => item.trim())
//           .filter(Boolean),
//         agreed_duration_minutes: Number(formData.agreed_duration_minutes),
//       };

//       const response = await api.post("/session/create", payload);
//       setMessage("Session created successfully");
//       navigate(`/live/${response.data.barter_id}`);
//     } catch (error) {
//       console.error(error);
//       setMessage(error.response?.data?.detail || "Failed to create session");
//     } finally {
//       setLoading(false);
//     }
//   };

//   return (
//     <div className="page">
//       <h1>Create Session</h1>
//       <form className="form-card" onSubmit={handleSubmit}>
//         <input name="skill_a" placeholder="Skill A" onChange={handleChange} required />
//         <input name="skill_b" placeholder="Skill B" onChange={handleChange} required />
//         <input name="topic" placeholder="Topic" onChange={handleChange} required />
//         <input name="scope" placeholder="Scope" onChange={handleChange} required />
//         <input
//           name="allowed_concepts"
//           placeholder="Allowed Concepts (comma separated)"
//           onChange={handleChange}
//           required
//         />
//         <input
//           name="disallowed_concepts"
//           placeholder="Disallowed Concepts (comma separated)"
//           onChange={handleChange}
//           required
//         />
//         <input
//           name="agreed_duration_minutes"
//           type="number"
//           placeholder="Agreed Duration Minutes"
//           onChange={handleChange}
//           required
//         />
//         <button type="submit" disabled={loading}>
//           {loading ? "Creating..." : "Create Session"}
//         </button>
//       </form>
//       {message && <p>{message}</p>}
//     </div>
//   );
// }

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/api";

export default function CreateSession() {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    skill_a: "",
    skill_b: "",
    topic: "",
    scope: "",
    allowed_concepts: "",
    disallowed_concepts: "",
    agreed_duration_minutes: "",
  });

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage("");

    try {
      const payload = {
        ...formData,
        allowed_concepts: formData.allowed_concepts
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean),
        disallowed_concepts: formData.disallowed_concepts
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean),
        agreed_duration_minutes: Number(formData.agreed_duration_minutes),
      };

      const response = await api.post("/session/create", payload);
      setMessage("Session created successfully");
      navigate(`/live/${response.data.barter_id}`);
    } catch (error) {
      console.error(error);
      setMessage(error.response?.data?.detail || "Failed to create session");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <div className="page-header">
        <div className="top-badge">Skill Barter Marketplace</div>
        <h1 className="page-title">Create Session</h1>
        <p className="page-subtitle">
          Start a structured barter learning session with clear topic boundaries.
        </p>
      </div>

      <form className="form-card" onSubmit={handleSubmit}>
        <div className="form-grid">
          <input name="skill_a" placeholder="Skill A" onChange={handleChange} required />
          <input name="skill_b" placeholder="Skill B" onChange={handleChange} required />
          <input name="topic" placeholder="Topic" onChange={handleChange} required />
          <input name="scope" placeholder="Scope" onChange={handleChange} required />
          <input
            name="allowed_concepts"
            placeholder="Allowed Concepts (comma separated)"
            onChange={handleChange}
            required
            className="full-width"
          />
          <input
            name="disallowed_concepts"
            placeholder="Disallowed Concepts (comma separated)"
            onChange={handleChange}
            required
            className="full-width"
          />
          <input
            name="agreed_duration_minutes"
            type="number"
            placeholder="Agreed Duration Minutes"
            onChange={handleChange}
            required
            className="full-width"
          />
        </div>

        <div style={{ marginTop: "18px" }}>
          <button type="submit" disabled={loading}>
            {loading ? "Creating..." : "Create Session"}
          </button>
        </div>
      </form>

      {message && <div className="message">{message}</div>}
    </div>
  );
}