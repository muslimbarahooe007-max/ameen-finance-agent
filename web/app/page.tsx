import Link from "next/link";

export default function Landing() {
  return (
    <main className="doc">
      <nav className="doc-nav">
        <div className="doc-mark">
          Ameen <span lang="ar">أمين</span>
        </div>
        <Link href="/app">Open the approval queue</Link>
      </nav>

      <section className="lede">
        <h1>Your invoices are checked against what your team actually promised.</h1>
        <p>
          Ameen is an accounts payable agent that sits in the Slack channel where prices get
          agreed. When the invoice arrives weeks later, it already knows what was said, quotes
          the message back, and decides who needs to approve it.
        </p>
        <div className="doc-actions">
          <Link href="/app" className="btn-solid">
            Open the approval queue
          </Link>
          <a
            href="https://github.com/muslimbarahooe007-max/ameen-finance-agent"
            className="btn-plain"
            target="_blank"
            rel="noreferrer"
          >
            Read the source
          </a>
        </div>
      </section>

      {/* The hero image is the product's whole argument: a sentence someone
          typed, and a number that turned up three weeks later. */}
      <section className="confront">
        <div className="said">
          <p className="stamp">2 September, in #ap-review</p>
          <blockquote>
            They have agreed AED 40,000 for the 12 units, net 30.
          </blockquote>
        </div>

        <div className="gap-rule">
          <span>three weeks pass</span>
        </div>

        <div className="billed">
          <p className="stamp">23 September, invoice INV-2291</p>
          <p className="amount">AED 46,000</p>
          <p className="over">AED 6,000 more than was agreed</p>
        </div>
      </section>

      <section className="figures">
        <div>
          <b>AED 6,000</b>
          <p>caught on the first invoice put through it</p>
        </div>
        <div>
          <b>7 seconds</b>
          <p>from document dropped in Slack to a decision</p>
        </div>
        <div>
          <b>6 checks</b>
          <p>run on every document, each one able to change the approver</p>
        </div>
        <div>
          <b>No database</b>
          <p>the Slack channel is the record and the audit trail</p>
        </div>
      </section>

      <section className="module">
        <h2>It reads the conversation, not just the document</h2>
        <ul>
          <li>Searches the channel for what was agreed with this vendor</li>
          <li>Quotes the exact message and links straight back to it</li>
          <li>Compares the invoice against the purchase order raised in the same channel</li>
          <li>Flags a price that drifted, with the percentage and the amount</li>
        </ul>
        <p className="case">
          A supplier agrees AED 40,000 in a thread on the second. The invoice arrives on the
          twenty-third for AED 46,000. Nobody remembers the thread, and nobody would think to
          look. Ameen posts the difference with the original message attached, and moves the
          approval from a manager to two signatures.
        </p>
      </section>

      <section className="module">
        <h2>It removes the approve button when the bank details change</h2>
        <ul>
          <li>Keeps every account a vendor has ever been paid to</li>
          <li>Refuses to render an approval control when the account changes</li>
          <li>Writes nothing to the tracker while the document is held</li>
          <li>Rejects an approval at the API even if the button is forced</li>
        </ul>
        <p className="case">
          Invoice redirection is the most expensive fraud in corporate finance: a compromised
          mailbox, a convincing invoice, one altered account number. Most software shows a
          warning beside the approve button. The warning does not work, because the button is
          still there. Ameen takes the button away and tells you to phone the vendor on a
          number you already hold.
        </p>
      </section>

      <section className="module">
        <h2>It decides who approves, and says why</h2>
        <ul>
          <li>Routes on amount first, then on what the checks found</li>
          <li>Escalates exactly one level for any finding, every time</li>
          <li>Auto-approves a clean document under the threshold with no human at all</li>
          <li>States the reason in plain language on the card and in the queue</li>
        </ul>
        <p className="case">
          A routine taxi receipt clears itself. The same receipt submitted twice goes to
          finance. The rule is four lines of code and it is the part most policy engines get
          wrong, because they flag without changing what happens next.
        </p>
      </section>

      <section className="compare">
        <h2>Why a document scanner cannot do this</h2>
        <div className="compare-grid">
          <div>
            <p className="stamp">A scanner</p>
            <ul>
              <li>Reads what is printed on the page</li>
              <li>Returns its best guess when the page is unclear</li>
              <li>Matches against records you remembered to load</li>
              <li>Hands you a row to check by hand</li>
            </ul>
          </div>
          <div>
            <p className="stamp">Ameen</p>
            <ul>
              <li>Reads the page and the room it arrived in</li>
              <li>Asks in the thread rather than guessing a number</li>
              <li>Matches against a conversation nobody filed anywhere</li>
              <li>Changes who has to sign, and explains the change</li>
            </ul>
          </div>
        </div>
        <p className="case">
          To catch that invoice, something has to remember a conversation from three weeks
          ago, know which thread it was in, and find it again. A person who could do all that
          would not need the agent. Ameen&rsquo;s advantage is not intelligence. It is that it
          was in the room when the promise was made.
        </p>
      </section>

      <section className="chapter">
        <h2>What happens when a document arrives</h2>
        <ol className="sequence">
          <li>
            <h3>Someone agrees a price</h3>
            <p>In the open, in Slack, the way it already happens.</p>
          </li>
          <li>
            <h3>An invoice is dropped in the channel</h3>
            <p>A photograph or a PDF. Ameen reads either.</p>
          </li>
          <li>
            <h3>It finds the promise and links it</h3>
            <p>The exact message, quoted, with a permalink back to the thread.</p>
          </li>
          <li>
            <h3>The finding changes who approves</h3>
            <p>A contradiction escalates one level. A clean match needs nobody at all.</p>
          </li>
          <li>
            <h3>The decision lands in the queue</h3>
            <p>Approve it on the web and the Slack message updates in place.</p>
          </li>
        </ol>
      </section>

      <section className="chapter">
        <h2>There is no database</h2>
        <p>
          Ameen attaches the whole structured decision to its own Slack message as
          machine-readable metadata. The channel already holds the record, the evidence and
          the audit trail, so the approval queue simply reads it back. One source of truth,
          kept in the same room the promise was made in.
        </p>
        <div className="flow">
          <span>a promise in Slack</span>
          <span>an invoice arrives</span>
          <span>Ameen checks and routes</span>
          <span>the queue reads it back</span>
        </div>
      </section>

      <footer className="doc-foot">
        <p>
          <em>Ameen</em> <span lang="ar">أمين</span> — trustworthy. The root of{" "}
          <em>amīn al&#8209;sundūq</em>, the Arabic for treasurer.
        </p>
        <p className="doc-foot-links">
          <Link href="/app">Approval queue</Link>
          <a
            href="https://github.com/muslimbarahooe007-max/ameen-finance-agent"
            target="_blank"
            rel="noreferrer"
          >
            Source
          </a>
        </p>
      </footer>
    </main>
  );
}
