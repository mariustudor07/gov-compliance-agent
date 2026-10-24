export default function Privacy() {
  return (
    <div className="docs">
      <div className="docs__head">
        <h1>Privacy policy</h1>
        <p className="docs__intro">
          We built a tool that checks other sites for compliance gaps, so it would be a bit rich to ship
          one without a straight answer about what we do with your data. Here it is.
        </p>
      </div>

      <section className="prose-section">
        <h2>What we collect</h2>
        <p>
          When you scan a URL, we store the scan result: the URL you submitted, when it ran, the
          scores, and the findings (including evidence like header values or HTML snippets from the
          site being scanned). This is what powers the History page and stops us re-scanning the same
          URL every time.
        </p>
        <p>
          We don't require an account, a name, or an email address to use GovCheck. We don't know who
          you are beyond whatever your browser or network already reveals to any website you visit
          (standard web server logs, kept by our hosting provider, Vercel, and GitHub for the backend,
          not by us specifically).
        </p>
      </section>

      <section className="prose-section">
        <h2>What we don't do</h2>
        <p>
          No tracking cookies, no analytics, no advertising. We don't sell or share scan data with
          third parties for marketing. The one thing stored locally in your browser is the result of
          your most recent scan (via <code>sessionStorage</code>), so the report survives a page
          refresh. It's cleared when you close the tab and never leaves your device.
        </p>
      </section>

      <section className="prose-section">
        <h2>About the sites you scan</h2>
        <p>
          When you ask us to scan a URL, our scanner visits that site the way a browser would: it
          reads cookies, response headers, and public page content (including the privacy policy text,
          to check it against UK GDPR). We process that information to generate your report. We are
          not collecting data from that site's own visitors: we're auditing the site itself, not
          harvesting the people who use it.
        </p>
      </section>

      <section className="prose-section">
        <h2>Who else sees it</h2>
        <p>Processing a scan involves a few third-party services, each doing one specific job:</p>
        <ul>
          <li>
            <strong>MongoDB Atlas</strong>: stores scan results and the regulation text our agent
            cites from.
          </li>
          <li>
            <strong>Google Gemini</strong>: writes the plain-English explanation for each finding and
            judges cookie-banner screenshots. It sees the scan evidence, not anything about you.
          </li>
          <li>
            <strong>Voyage AI</strong>: generates the embeddings used to search the regulation text.
          </li>
          <li>
            <strong>Vercel</strong> hosts this site. <strong>Google Fonts</strong> serves the
            typeface, which means your browser makes a request to Google's servers to load it.
          </li>
        </ul>
      </section>

      <section className="prose-section">
        <h2>How long we keep it</h2>
        <p>
          This is a prototype built for a hackathon weekend (Encode London, October 2026), not a
          production service with a formal retention policy. Scan results are kept for as long as the
          project's database exists, which may not be very long after the event ends.
        </p>
      </section>

      <section className="prose-section">
        <h2>Your rights, and getting in touch</h2>
        <p>
          If you'd like a scan result removed, or have a question about this policy, the most reliable
          way to reach us during the hackathon is to open an issue on{" "}
          <a href="https://github.com/mariustudor07/gov-compliance-agent" target="_blank" rel="noreferrer">
            the GitHub repository
          </a>
          . We don't have a dedicated support inbox set up for a weekend project; we're a team of
          students, not a company.
        </p>
      </section>

      <div className="docs__disclaimer">
        <strong>This is a student hackathon project</strong>, not a registered company, and this policy
        isn't a substitute for professional legal advice. It's a genuine, good-faith description of
        what the tool actually does, written for transparency, not as a formal legal instrument.
      </div>
    </div>
  );
}
