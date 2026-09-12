import Link from "next/link";

export const metadata = {
  title: "Ameen — the finance agent that remembers what was promised",
};

export default function Landing() {
  return (
    <main className="lp">
      <nav className="lp-nav">
        <div className="lp-brand">
          <b>Ameen</b>
          <span>أمين</span>
        </div>
        <Link href="/app" className="lp-cta-small">
          Open the queue →
        </Link>
      </nav>

      <section className="lp-hero">
        <p className="lp-eyebrow">Accounts payable, inside Slack</p>
        <h1>
          The finance agent that remembers
          <br />
          what was promised.
        </h1>
        <p className="lp-sub">
          Finance disputes are almost never arithmetic. They happen because what was agreed
          lives in a Slack conversation, and what gets invoiced arrives as a document — and
          nothing connects the two. Ameen lives in the channel where the promise was made, so
          when the invoice lands, it already knows.
        </p>
        <div className="lp-actions">
          <Link href="/app" className="lp-cta">
            Open the approval queue
          </Link>
          <a
            href="https://github.com/muslimbarahooe007-max/ameen-finance-agent"
            className="lp-cta-ghost"
            target="_blank"
            rel="noreferrer"
          >
            View the source
          </a>
        </div>

        <div className="lp-card">
          <div className="lp-card-row">
            <div>
              <b className="lp-card-vendor">Gulf Supplies LLC</b>
              <small className="lp-card-ref">INV-2291 · PO-1043 · 2026-09-12</small>
            </div>
            <span className="lp-card-tag">Vendor invoice</span>
          </div>
          <div className="lp-card-figures">
            <div className="lp-fig agreed">
              <i>agreed</i>
              <b>AED 40,000</b>
            </div>
            <div className="lp-fig over">
              <i>invoiced</i>
              <b>AED 46,000</b>
            </div>
            <span className="lp-gap">+15%</span>
          </div>
          <div className="lp-track">
            <span className="lp-track-base" style={{ width: "87%" }} />
            <span className="lp-track-excess" style={{ width: "13%" }} />
          </div>
          <div className="lp-quote">
            <q>Spoke to Gulf Supplies — they have agreed AED 40,000 for the 12 units, net 30.</q>
            <footer>Said in #ap-review, three weeks before this invoice existed.</footer>
          </div>
          <div className="lp-card-route">
            <b>L3 dual approval</b>
            <small>Escalated one level: contradicts what was agreed in this channel</small>
          </div>
        </div>
      </section>

      <section className="lp-section">
        <p className="lp-kicker">The problem</p>
        <h2>The promise and the invoice never meet.</h2>
        <p className="lp-lede">
          A price gets agreed in a thread on a Tuesday. A purchase order is raised a week
          later. The invoice arrives three weeks after that, as a PDF. Nobody cross-checks the
          conversation, because a conversation is not data, and nobody remembers which thread
          it was in. A chat window cannot fix this — it would need a human to remember, find,
          and paste the thread in. Anyone who could do that would not need the agent.
        </p>
      </section>

      <section className="lp-section">
        <p className="lp-kicker">How it works</p>
        <h2>Ameen was already in the room.</h2>
        <div className="lp-steps">
          <div className="lp-step">
            <i>01</i>
            <b>A promise gets made</b>
            <p>Someone agrees a price or a term with a vendor, in the open, in Slack.</p>
          </div>
          <div className="lp-step">
            <i>02</i>
            <b>An invoice arrives</b>
            <p>Dropped into the channel, or forwarded from the inbox — a photo, a PDF, either.</p>
          </div>
          <div className="lp-step">
            <i>03</i>
            <b>Ameen cites the promise</b>
            <p>It searches the channel, finds what was agreed, and links the exact message.</p>
          </div>
          <div className="lp-step">
            <i>04</i>
            <b>It routes, not just flags</b>
            <p>A contradiction escalates the approval level. A clean match needs no one at all.</p>
          </div>
        </div>
      </section>

      <section className="lp-section lp-highlight">
        <p className="lp-kicker">Control, expressed as a constraint</p>
        <h2>When the bank account changes, there is no button.</h2>
        <p className="lp-lede">
          Invoice redirection is the most expensive fraud in corporate finance: a
          compromised email, a real-looking invoice, a changed account. Most tools show a
          warning next to an Approve button. Ameen does not offer the button at all.
        </p>
        <div className="lp-blocked">
          <b>Blocked</b>
          <p>
            This invoice pays a different account from the last three from this vendor.
            Verify by phone, on a number you already hold, before anyone approves this. No
            approval button has been offered.
          </p>
        </div>
      </section>

      <section className="lp-section">
        <p className="lp-kicker">Architecture</p>
        <h2>No database. The channel is the record.</h2>
        <p className="lp-lede">
          Ameen attaches the whole structured decision to its own Slack message as
          machine-readable metadata. The channel already holds the record, the evidence and
          the audit trail — the approval queue just reads it back. Approve it on the web, and
          the Slack card updates in place. One source of truth, in the place the promise was
          made.
        </p>
        <div className="lp-flow" aria-hidden>
          <span>Slack channel</span>
          <span className="lp-arrow">→</span>
          <span>Ameen</span>
          <span className="lp-arrow">→</span>
          <span>Message metadata</span>
          <span className="lp-arrow">→</span>
          <span>Approval queue</span>
        </div>
      </section>

      <footer className="lp-footer">
        <div>
          <b>Ameen</b> <span>أمين</span> — trustworthy. The Arabic root of{" "}
          <i>amīn al-sundūq</i>, treasurer.
        </div>
        <div className="lp-footer-links">
          <Link href="/app">Approval queue</Link>
          <a
            href="https://github.com/muslimbarahooe007-max/ameen-finance-agent"
            target="_blank"
            rel="noreferrer"
          >
            Source on GitHub
          </a>
        </div>
      </footer>
    </main>
  );
}
