import { NavLink } from "react-router-dom";
import { ShieldIcon } from "./icons";

export default function Nav() {
  return (
    <header className="nav">
      <NavLink to="/" className="nav__brand">
        <ShieldIcon width={20} height={20} />
        Compliance Checker
      </NavLink>
      <nav className="nav__links">
        <NavLink to="/" end className={({ isActive }) => (isActive ? "active" : "")}>
          Scan
        </NavLink>
        <NavLink to="/history" className={({ isActive }) => (isActive ? "active" : "")}>
          History
        </NavLink>
        <NavLink to="/docs" className={({ isActive }) => (isActive ? "active" : "")}>
          Docs
        </NavLink>
      </nav>
    </header>
  );
}
