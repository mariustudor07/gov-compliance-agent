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
        <h2>Who we are</h2>
        <p>
          The data controller for GovCheck is the GovCheck project team: four students building this
          tool at the Encode London 2026 hackathon. We are responsible for deciding how the personal
          data described below is collected and used.
        </p>
      </section>

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
        <h2>Our lawful basis</h2>
        <p>
          Our lawful basis for processing this data under Article 6(1)(f) of the UK GDPR is legitimate
          interests: we need to store the scan you asked for in order to show you the report and keep
          a history of past scans. We keep the data we hold to the minimum needed for that purpose.
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
        <h2>Your rights</h2>
        <p>
          Under the UK GDPR you have the right to access the personal data we hold about you, to ask us
          to correct it or erase it, to restrict or object to how we process it, and to data
          portability. You can ask us to delete a scan result at any time.
        </p>
      </section>

      <section className="prose-section">
        <h2>Contact us</h2>
        <p>
          You can contact the GovCheck project team about any data protection question by opening an
          issue at{" "}
          <a
            href="https://github.com/mariustudor07/gov-compliance-agent/issues"
            target="_blank"
            rel="noreferrer"
          >
            github.com/mariustudor07/gov-compliance-agent/issues
          </a>
          . We have not appointed a Data Protection Officer, so questions about your personal data go
          directly to the project team. At the scale of a hackathon prototype the UK GDPR doesn't
          require one.
        </p>
      </section>

      <section className="prose-section">
        <h2>Complaints</h2>
        <p>
          If you're unhappy with how we've handled your data, you have the right to complain to the
          Information Commissioner's Office (ICO), the UK's data protection regulator, at{" "}
          <a href="https://ico.org.uk/make-a-complaint/" target="_blank" rel="noreferrer">
            ico.org.uk/make-a-complaint
          </a>
          . We'd appreciate the chance to fix things first, but you don't have to contact us before
          going to the ICO.
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
