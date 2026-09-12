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

      {/* The hero is the confrontation itself: a sentence someone typed, and a
          number that arrived three weeks later. The rule between them is the gap. */}
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

      <section className="thesis">
        <h1>The finance agent that remembers what was promised.</h1>
        <p>
          Finance disputes are almost never arithmetic. They happen because what was agreed
          lives in a conversation and what gets invoiced arrives as a document, and nothing
          connects the two. Ameen sits in the channel where the promise is made. When the
          invoice lands weeks later, it already knows, and it quotes the message back.
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

      <section className="chapter">
        <h2>Why a chat window cannot do this</h2>
        <p>
          To catch that invoice, something has to remember a conversation from three weeks
          ago, know which thread it was in, and find it again. A person who could do all
          that would not need the agent. Ameen&rsquo;s advantage is not intelligence. It is
          that it was in the room when the promise was made.
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
            <p>
              A contradiction escalates one level. A clean match needs nobody at all.
            </p>
          </li>
        </ol>
      </section>

      <section className="chapter">
        <h2>When the bank account changes, there is no button</h2>
        <p>
          Invoice redirection is the most expensive fraud in corporate finance: a
          compromised mailbox, a convincing invoice, one altered account number. Most
          software shows a warning beside the approve button. Ameen removes the button,
          because the button is the thing that gets finance teams defrauded.
        </p>
        <div className="held-notice">
          <p className="stamp held">Held</p>
          <p>
            This invoice pays a different account from the last three from this vendor.
            Verify by phone, on a number you already hold, before anyone approves it.
          </p>
        </div>
      </section>

      <section className="chapter">
        <h2>There is no database</h2>
        <p>
          Ameen attaches the whole structured decision to its own Slack message as
          machine-readable metadata. The channel already holds the record, the evidence and
          the audit trail, so the approval queue simply reads it back. Approve something on
          the web and the Slack message updates in place. One source of truth, kept in the
          same room the promise was made in.
        </p>
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
