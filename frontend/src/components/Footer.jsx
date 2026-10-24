import { Link } from "react-router-dom";
import { ShieldIcon } from "./icons";

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer__row">
        <span className="footer__brand">
          <ShieldIcon width={16} height={16} />
          Compliance Checker
        </span>
        <nav className="footer__links">
          <Link to="/docs">Docs</Link>
          <Link to="/docs#faq">FAQ</Link>
          <a href="https://github.com/mariustudor07/gov-compliance-agent" target="_blank" rel="noreferrer">
            GitHub
          </a>
        </nav>
      </div>
      <p className="footer__disclaimer">
        Not legal advice: an automated first pass, built for Encode London 2026. Verify anything
        important with a qualified professional.
      </p>
    </footer>
  );
}
