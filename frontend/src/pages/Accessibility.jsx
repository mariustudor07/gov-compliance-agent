export default function Accessibility() {
  return (
    <div className="docs">
      <div className="docs__head">
        <h1>Accessibility statement</h1>
        <p className="docs__intro">
          This accessibility statement applies to GovCheck at uk-compliance-checker.vercel.app. It
          follows the{" "}
          <a
            className="inline-link"
            href="https://www.gov.uk/government/publications/sample-accessibility-statement"
            target="_blank"
            rel="noreferrer"
          >
            GOV.UK sample accessibility statement
          </a>
          .
        </p>
      </div>

      <section className="prose-section">
        <h2>How accessible this website is</h2>
        <p>
          We want as many people as possible to be able to use this website. Every control is a
          standard HTML link, button or form field, so it can be reached with a keyboard. Text meets
          the WCAG AA contrast ratio, and animations are switched off if your device asks for reduced
          motion.
        </p>
      </section>

      <section className="prose-section">
        <h2>Compliance status</h2>
        <p>
          This website is partially compliant with the Web Content Accessibility Guidelines version 2.2
          AA standard, due to the limitations listed below.
        </p>
      </section>

      <section className="prose-section">
        <h2>Known limitations</h2>
        <ul>
          <li>
            The score rings and severity chart on report pages are visual. Every score and count is also
            shown as text, but the charts themselves have not been tested with a range of screen
            readers.
          </li>
          <li>
            We have tested the site with automated checks (axe-core, run through our own scanner) but
            have not yet had a full manual audit by an accessibility specialist.
          </li>
        </ul>
      </section>

      <section className="prose-section">
        <h2>Feedback and contact</h2>
        <p>
          If you find a problem not listed here, or need information on this site in a different
          format, open an issue on{" "}
          <a href="https://github.com/mariustudor07/gov-compliance-agent" target="_blank" rel="noreferrer">
            our GitHub repository
          </a>
          . We'll aim to respond during the hackathon.
        </p>
      </section>

      <section className="prose-section">
        <h2>Enforcement</h2>
        <p>
          The Equality and Human Rights Commission (EHRC) enforces the Public Sector Bodies (Websites and
          Mobile Applications) Accessibility Regulations 2018. GovCheck is a student project rather than
          a public sector body, so those regulations don't legally apply to us, but we publish this
          statement because a tool that checks other sites for it should meet the same bar.
        </p>
      </section>

      <section className="prose-section">
        <h2>Preparation of this statement</h2>
        <p>
          This statement was prepared on 24 October 2026 and last reviewed on 24 October 2026. The site
          was last tested on 24 October 2026 using automated WCAG 2.2 AA checks.
        </p>
      </section>
    </div>
  );
}
