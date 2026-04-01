import { Routes, Route } from "react-router-dom";
import CreateSession from "./pages/CreateSession";
import LiveSession from "./pages/LiveSession";
import SessionResult from "./pages/SessionResult";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<CreateSession />} />
      <Route path="/live/:barterId" element={<LiveSession />} />
      <Route path="/result/:barterId" element={<SessionResult />} />
    </Routes>
  );
}