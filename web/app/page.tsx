import Link from "next/link";

export default function Landing() {
  return (
    <main className="pm">
      <nav className="pm-nav">
        <div className="pm-mark">
          Ameen <span lang="ar">أمين</span>
        </div>
        <div className="pm-nav-links">
          <a href="#how">How it works</a>
          <a href="#checks">Checks</a>
          <a href="#routing">Routing</a>
          <Link href="/app" className="pm-nav-cta">Open the queue</Link>
        </div>
      </nav>

      <header className="pm-hero">
        <div className="pm-hero-copy">
          <p className="pm-tag"><span className="pm-dot" />Live in Slack</p>
          <h1>
            Your invoices, checked against
            <br />
            <em>what your team actually promised.</em>
          </h1>
          <p className="pm-sub">
            Ameen sits in the channel where prices get agreed. When the invoice arrives weeks
            later it already knows what was said, quotes the message back, and decides who
            needs to sign.
          </p>
          <div className="pm-cta-row">
            <Link href="/app" className="pm-btn">Open the approval queue</Link>
            <a
              href="https://github.com/muslimbarahooe007-max/ameen-finance-agent"
              className="pm-btn-ghost"
              target="_blank"
              rel="noreferrer"
            >
              Read the source
            </a>
          </div>
        </div>

        {/* The hero plays the product rather than describing it. */}
        <div className="stage" aria-label="Ameen catching an invoice that contradicts an agreement">
          <div className="stage-chrome">
            <span className="stage-channel"># ap-review</span>
            <span className="stage-live"><i />live</span>
          </div>

          <div className="msg m1">
            <div className="av av-p">RK</div>
            <div className="msg-body">
              <b>Rashid <time>2 Sep, 11:04</time></b>
              <p>Spoke to Gulf Supplies — they have agreed AED 40,000 for the 12 units, net 30.</p>
            </div>
          </div>

          <div className="msg m2">
            <div className="av av-p">LM</div>
            <div className="msg-body">
              <b>Layla <time>23 Sep, 09:12</time></b>
              <p className="file">
                <span className="file-ico">PDF</span>
                INV-2291-gulf-supplies.pdf
              </p>
            </div>
          </div>

          <div className="msg m3">
            <div className="av av-a">A</div>
            <div className="msg-body">
              <b>Ameen <span className="bot">APP</span></b>
              <p className="thinking">
                <i /><i /><i /> reading the document and the channel
              </p>
            </div>
          </div>

          <div className="msg m4">
            <div className="av av-a">A</div>
            <div className="msg-body">
              <b>Ameen <span className="bot">APP</span></b>
              <div className="verdict">
                <div className="v-top">
                  <div>
                    <b>Gulf Supplies LLC</b>
                    <small>INV-2291 · PO-1043</small>
                  </div>
                  <span className="v-pill">+15%</span>
                </div>
                <div className="v-figs">
                  <span className="vf ok"><i>agreed</i><b>AED 40,000</b></span>
                  <span className="vf bad"><i>invoiced</i><b>AED 46,000</b></span>
                </div>
                <div className="v-bar"><span /><em /></div>
                <div className="v-quote">
                  “They have agreed AED 40,000 for the 12 units, net 30.”
                  <small>Said in this channel on 2 Sep · Open the message</small>
                </div>
                <div className="v-route">
                  <b>Escalated to dual approval</b>
                  <small>Contradicts what was agreed in this channel</small>
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      <section className="pm-stats">
        <div><b>AED 6,000</b><p>caught on the first invoice tested</p></div>
        <div><b>7s</b><p>document dropped to decision made</p></div>
        <div><b>6</b><p>compliance checks on every document</p></div>
        <div><b>0</b><p>databases — the channel is the record</p></div>
      </section>

      <section className="pm-sec" id="how">
        <p className="pm-kick">How it works</p>
        <h2>Four steps, none of which anyone has to remember.</h2>
        <div className="steps">
          {[
            ["A price is agreed", "In the open, in Slack, the way it already happens. Ameen is in the channel and files it as a commitment."],
            ["A document arrives", "A photograph or a PDF, dropped in the channel or forwarded from the finance inbox."],
            ["The promise is found", "Ameen searches the channel history, matches the vendor, and links the exact message."],
            ["The approver changes", "A contradiction escalates one level. A clean document under the limit needs nobody."],
          ].map(([t, d], i) => (
            <div className="step" key={t}>
              <span className="step-n">{i + 1}</span>
              <b>{t}</b>
              <p>{d}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="pm-sec" id="checks">
        <p className="pm-kick">Compliance</p>
        <h2>Six checks run on every document. Each one can change who signs.</h2>
        <div className="checks">
          {[
            ["Contradicts the channel", "HIGH", "The invoice does not match what this vendor agreed to in conversation. Quoted and linked.", "hi"],
            ["Bank details changed", "BLOCKING", "Paying a different account than last time. The approve button is not rendered at all.", "bl"],
            ["Does not match the PO", "MEDIUM", "Checked against the purchase order raised in the same channel.", "me"],
            ["Duplicate document", "HIGH", "The same vendor and reference has been submitted before.", "hi"],
            ["Could not be read", "MEDIUM", "Low confidence on a field. Ameen asks in the thread instead of guessing.", "me"],
            ["No tax registration number", "LOW", "A UAE VAT invoice without a TRN gets rejected at payment stage.", "lo"],
          ].map(([t, sev, d, cls]) => (
            <div className={`check c-${cls}`} key={t as string}>
              <div className="check-head">
                <b>{t}</b>
                <span className="sev">{sev}</span>
              </div>
              <p>{d}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="pm-sec" id="routing">
        <p className="pm-kick">Routing</p>
        <h2>It decides who approves, and says why.</h2>
        <div className="ladder">
          {[
            ["L0", "Auto-approved", "Clean, under the limit. No human sees it.", "l0"],
            ["L1", "Manager", "Routine spend inside policy.", "l1"],
            ["L2", "Finance", "Above the manager limit, or a category that needs review.", "l2"],
            ["L3", "Two approvers", "Large amounts, or anything a check flagged.", "l3"],
            ["—", "Blocked", "Bank details changed. No approval control exists.", "lx"],
          ].map(([lvl, name, d, cls]) => (
            <div className={`rung r-${cls}`} key={name as string}>
              <span className="lvl">{lvl}</span>
              <b>{name}</b>
              <p>{d}</p>
            </div>
          ))}
        </div>
        <p className="pm-note">
          Any finding escalates the document exactly one level. A routine taxi receipt clears
          itself; the same receipt submitted twice goes to finance.
        </p>
      </section>

      <section className="pm-sec">
        <p className="pm-kick">Architecture</p>
        <h2>There is no database.</h2>
        <p className="pm-lede">
          Ameen attaches the whole structured decision to its own Slack message as
          machine-readable metadata. The channel already holds the record, the evidence and the
          audit trail, so the approval queue simply reads it back. Approve on the web and the
          Slack message updates in place.
        </p>
        <div className="pipe">
          <span>promise in Slack</span>
          <span>invoice arrives</span>
          <span>checks and routing</span>
          <span>message metadata</span>
          <span>approval queue</span>
        </div>
      </section>

      <section className="pm-close">
        <h2>See it running on live Slack data.</h2>
        <div className="pm-cta-row">
          <Link href="/app" className="pm-btn">Open the approval queue</Link>
          <a
            href="https://github.com/muslimbarahooe007-max/ameen-finance-agent"
            className="pm-btn-ghost"
            target="_blank"
            rel="noreferrer"
          >
            Read the source
          </a>
        </div>
      </section>

      <footer className="pm-foot">
        <p><b>Ameen</b> <span lang="ar">أمين</span> — trustworthy, the root of the Arabic for treasurer.</p>
        <p className="pm-foot-links">
          <Link href="/app">Approval queue</Link>
          <a href="https://github.com/muslimbarahooe007-max/ameen-finance-agent" target="_blank" rel="noreferrer">Source</a>
        </p>
      </footer>
    </main>
  );
}
