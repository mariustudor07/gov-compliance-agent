import { Link } from "react-router-dom";

export default function Cookies() {
  return (
    <div className="docs">
      <div className="docs__head">
        <h1>Cookie policy</h1>
        <p className="docs__intro">
          This cookie policy explains which cookies and similar technologies GovCheck uses. The short
          version: none that track you.
        </p>
      </div>

      <section className="prose-section">
        <h2>Cookies we set</h2>
        <p>
          GovCheck doesn't set any cookies. There's no analytics, no advertising, and no login, so
          there's nothing to remember about you between visits.
        </p>
      </section>

      <section className="prose-section">
        <h2>Similar technologies</h2>
        <ul>
          <li>
            <strong>Session storage</strong> (<code>govcheck:lastResult</code>): holds your most recent
            scan report so it survives a page refresh. It's strictly necessary for the page to work,
            stays on your device, and is deleted when you close the tab.
          </li>
          <li>
            <strong>Google Fonts</strong>: your browser requests the Inter typeface from Google's
            servers, which means Google receives your IP address. This doesn't set a cookie.
          </li>
        </ul>
      </section>

      <section className="prose-section">
        <h2>Why there's no cookie banner</h2>
        <p>
          PECR only requires consent for storage that isn't strictly necessary. Because we don't use
          any non-essential cookies or tracking, there's nothing to ask your consent for, so we don't
          show a banner. If that ever changes, we'll ask first and make rejecting as easy as accepting.
        </p>
      </section>

      <section className="prose-section">
        <h2>Questions</h2>
        <p>
          See our <Link to="/privacy">privacy policy</Link> for how we handle data more generally, or open an
          issue on{" "}
          <a href="https://github.com/mariustudor07/gov-compliance-agent" target="_blank" rel="noreferrer">
            our GitHub repository
          </a>
          .
        </p>
      </section>
    </div>
  );
}
