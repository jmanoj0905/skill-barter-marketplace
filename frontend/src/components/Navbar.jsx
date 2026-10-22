import { Link, useLocation, useNavigate } from "react-router-dom";
import { useState } from "react";
import { logoutUser } from "../services/authService";

const links = [
  { to: "/dashboard", label: "Overview" },
  { to: "/wallet", label: "Wallet" },
  { to: "/skills", label: "Skills" },
  { to: "/profile", label: "Profile" },
  { to: "/verify-phone", label: "Phone OTP" }
];

export default function Navbar() {
  const location = useLocation();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);

  const logout = async () => {
    try {
      await logoutUser();
    } catch {
      // Logout should still clear local auth state when server logout fails.
    } finally {
      localStorage.removeItem("token");
      navigate("/login");
    }
  };

  return (
    <header className="top-nav">
      <div className="top-nav__inner">
        <Link to="/wallet" className="top-nav__brand">
          Skill Barter
        </Link>

        <nav className="top-nav__links">
          {links.map((item) => {
            const isActive = location.pathname === item.to;

            return (
              <Link
                key={item.to}
                to={item.to}
                className={`top-nav__link ${isActive ? "active" : ""}`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="top-nav__controls">
          <button
            onClick={() => setOpen((prev) => !prev)}
            className="ui-btn ui-btn--secondary"
          >
            Menu
          </button>
          <button
            onClick={logout}
            className="ui-btn ui-btn--secondary"
          >
            Logout
          </button>
        </div>
      </div>

      {open ? (
        <nav className="top-nav__mobile">
          <div className="top-nav__links">
            {links.map((item) => {
              const isActive = location.pathname === item.to;

              return (
                <Link
                  key={item.to}
                  to={item.to}
                  onClick={() => setOpen(false)}
                  className={`top-nav__link ${isActive ? "active" : ""}`}
                >
                  {item.label}
                </Link>
              );
            })}
          </div>
        </nav>
      ) : null}
    </header>
  );
}