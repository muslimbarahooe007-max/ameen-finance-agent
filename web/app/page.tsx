"use client";

import { useCallback, useEffect, useState } from "react";
import type { Record as Rec } from "@/lib/slack";
import { activity, vendorIntel } from "@/lib/intel";

const money = (n: number, cur = "AED") =>
  `${cur} ${n.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;

const TRACK: { [k: string]: string } = {
  T1_reimbursement: "Reimbursement",
  T2_vendor_invoice: "Vendor invoice",
  T3_purchase_order: "Purchase order",
  T4_contract: "Contract",
};

export default function Queue() {
  const [records, setRecords] = useState<Rec[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [live, setLive] = useState(false);

  const load = useCallback(async () => {
    try {
      const res = await fetch("/api/decisions", { cache: "no-store" });
      const json = await res.json();
      if (!json.ok) throw new Error(json.error);
      setRecords(json.records);
      setError(null);
      setLive(true);
    } catch (err: any) {
      setError(String(err?.message ?? err));
      setLive(false);
    } finally {
      setLoaded(true);
    }
  }, []);

  // An invoice dropped into Slack appears here on its own.
  useEffect(() => {
    load();
    const t = setInterval(load, 4000);
    return () => clearInterval(t);
  }, [load]);

  async function settle(ts: string, verdict: "approved" | "rejected") {
    setBusy(ts);
    try {
      const res = await fetch("/api/decide", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ts, verdict, approver: "Finance" }),
      });
      const json = await res.json();
      if (!json.ok) throw new Error(json.error);
      await load();
    } catch (err: any) {
      setError(String(err?.message ?? err));
    } finally {
      setBusy(null);
    }
  }

  const pending = records.filter((r) => !r.decision);
  const waiting = pending.filter((r) => r.approvable);
  const held = pending.filter((r) => !r.approvable);
  const settled = records.filter((r) => r.decision);

  // Value sitting behind a block, which is a different kind of exposure.
  const heldValue = held.reduce((sum, r) => sum + r.total, 0);

  const queued = pending.reduce((s, r) => s + r.total, 0);
  const act = activity(records);

  return (
    <div className="shell">
      <aside className="rail">
        <div>
          <div className="brand">
            <b>Ameen</b>
            <span>أمين</span>
          </div>
          <p className="brand-sub">Accounts payable, watching the channel where the promises were made.</p>
        </div>

        <section>
          <h2>Connection</h2>
          <div className="wire">
            <span className={`pulse${live ? "" : " cold"}`} aria-hidden />
            {live ? "Reading the channel" : "No connection"}
          </div>
          <div className="wire">
            <b>#ap-review</b>
          </div>
        </section>

        <section>
          <h2>Queue</h2>
          <div className="tally">
            <div>
              Awaiting approval <b>{waiting.length}</b>
            </div>
            <div className={held.length ? "hot" : ""}>
              Held <b>{held.length}</b>
            </div>
            <div>
              Settled today <b>{settled.length}</b>
            </div>
          </div>
        </section>

        <footer>
          No database. Every decision rides along as metadata on Ameen&rsquo;s own Slack
          message, so the channel is the record, the evidence and the audit trail.
        </footer>
      </aside>

      <main className="main">
        <div className="head">
          <div>
            <h1>Approval queue</h1>
            <p>
              Invoices arrive in Slack. What your team agreed in that channel arrives with
              them, quoted and linked.
            </p>
          </div>
          {loaded && records.length > 0 && (
            <p className="activity">
              Ameen reviewed <b>{act.reviewed}</b> document{act.reviewed === 1 ? "" : "s"} in
              #ap-review, escalated <b>{act.escalated}</b>, blocked <b>{act.blocked}</b>, and
              approved <b>{act.autoApproved}</b> without a human.
            </p>
          )}
        </div>

        <div className="band">
          <div className="won">
            <i>Caught before payment</i>
            <b>{money(act.caught)}</b>
          </div>
          <div>
            <i>Awaiting approval</i>
            <b>
              {money(queued)}
              <small>
                {pending.length} document{pending.length === 1 ? "" : "s"}
              </small>
            </b>
          </div>
          <div>
            <i>Needs two approvers</i>
            <b>{pending.filter((r) => r.level >= 3 && r.approvable).length}</b>
          </div>
          <div>
            <i>Blocked</i>
            <b>
              {money(heldValue)}
              <small>
                {held.length} held
              </small>
            </b>
          </div>
        </div>

        {error && <p className="alert">{error}</p>}

        <div className="queue">
          {loaded && records.length === 0 && !error && (
            <div className="void">
              <b>Nothing waiting on you.</b>
              Drop an invoice into #ap-review and it will appear here within a few seconds.
            </div>
          )}

          {records.map((r) => {
            const c = r.commitment;
            const excess = c && r.total > c.amount ? r.total - c.amount : 0;
            const pct = c && c.amount ? ((r.total - c.amount) / c.amount) * 100 : 0;
            const basePct = c ? Math.max(6, Math.min(100, (Math.min(r.total, c.amount) / Math.max(r.total, c.amount)) * 100)) : 100;
            const isOpen = open === r.ts;

            return (
              <article
                key={r.ts}
                className={`entry${!r.approvable && !r.decision ? " held" : ""}${r.decision ? " done" : ""}`}
              >
                <div
                  className="line"
                  role="button"
                  tabIndex={0}
                  aria-expanded={isOpen}
                  onClick={() => setOpen(isOpen ? null : r.ts)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      setOpen(isOpen ? null : r.ts);
                    }
                  }}
                >
                  <div className="who">
                    <b>{r.vendor || "Unknown vendor"}</b>
                    <small>
                      {[r.reference, r.po_reference, r.doc_date].filter(Boolean).map((bit) => (
                        <span key={bit}>{bit}</span>
                      ))}
                    </small>
                    <span className="kind">{TRACK[r.track] ?? "Document"}</span>
                  </div>

                  <div className="gauge">
                    <div className="nums">
                      {c && (
                        <span className="n a">
                          <i>agreed</i>
                          <b>{money(c.amount, c.currency)}</b>
                        </span>
                      )}
                      <span className={`n b${excess ? "" : " level"}`}>
                        <i>invoiced</i>
                        <b>{money(r.total, r.currency)}</b>
                      </span>
                      {excess > 0 && <span className="gap">+{pct.toFixed(0)}%</span>}
                    </div>

                    <div className="track">
                      {excess > 0 ? (
                        <>
                          <span className="base" style={{ width: `${basePct}%` }} />
                          <span className="excess" style={{ width: `${100 - basePct}%` }} />
                        </>
                      ) : (
                        <span className="even" style={{ width: "100%" }} />
                      )}
                    </div>

                    <p className="legend">
                      {excess > 0
                        ? `${money(excess, r.currency)} more than this vendor agreed to in the channel`
                        : c
                          ? "Matches what was agreed in the channel"
                          : "No prior commitment found for this vendor"}
                    </p>
                  </div>

                  <div className={`route${!r.approvable ? " stop" : ""}`}>
                    <b>{r.level_label}</b>
                    <small>{r.reason}</small>
                  </div>

                  {r.decision ? (
                    <div className="done-note">
                      {r.decision} by {r.approver}
                      <span>{r.decided_at}</span>
                    </div>
                  ) : r.approvable ? (
                    <div className="act" onClick={(e) => e.stopPropagation()}>
                      <button className="yes" disabled={busy === r.ts} onClick={() => settle(r.ts, "approved")}>
                        Approve
                      </button>
                      <button className="no" disabled={busy === r.ts} onClick={() => settle(r.ts, "rejected")}>
                        Reject
                      </button>
                    </div>
                  ) : (
                    <p className="stop-note">Verify the bank details by phone before this can be approved.</p>
                  )}
                </div>

                {c && (
                  <div className="promise">
                    <q>{c.text}</q>
                    <footer>
                      Said in #ap-review before this invoice existed.{" "}
                      {c.permalink && (
                        <a href={c.permalink} target="_blank" rel="noreferrer">
                          Open the message
                        </a>
                      )}
                    </footer>
                  </div>
                )}

                {isOpen && (
                  <div className="drawer">
                    {r.findings.map((f) => (
                      <div key={f.code} className={`flag s-${f.severity}`}>
                        <span className="bar" aria-hidden />
                        <div>
                          <b>
                            {f.title}
                            <span className="sev">{f.severity}</span>
                          </b>
                          <p>
                            {f.detail}{" "}
                            {f.evidence_url && (
                              <a href={f.evidence_url} target="_blank" rel="noreferrer">
                                See the evidence
                              </a>
                            )}
                          </p>
                        </div>
                      </div>
                    ))}
                    {r.findings.length === 0 && <p className="legend">Every check passed.</p>}

                    {(() => {
                      const v = vendorIntel(records, r.vendor);
                      const drift = v.timesOver > 0;
                      return (
                        <div className="intel">
                          <h3>What Ameen knows about {v.vendor}</h3>
                          <div className="intel-grid">
                            <div>
                              <i>Documents seen</i>
                              {v.documents}
                            </div>
                            <div>
                              <i>Invoiced in total</i>
                              {money(v.invoiced, v.currency)}
                            </div>
                            <div className={drift ? "bad" : ""}>
                              <i>Billed above agreement</i>
                              {drift
                                ? `${money(v.overCharged, v.currency)} across ${v.timesOver}`
                                : "never"}
                            </div>
                            <div className={v.accounts.length > 1 ? "bad" : ""}>
                              <i>Paying accounts used</i>
                              {v.accounts.length > 1
                                ? `${v.accounts.length} different`
                                : v.accounts[0] || "not stated"}
                            </div>
                          </div>
                          {v.accounts.length > 1 && (
                            <p className="intel-note">
                              This vendor has been paid to more than one account:{" "}
                              {v.accounts.join(", ")}. A vendor's bank details rarely change
                              honestly.
                            </p>
                          )}
                        </div>
                      );
                    })()}
                    <div className="facts">
                      <div>
                        <i>Terms</i>
                        {r.payment_terms || "not stated"}
                      </div>
                      <div>
                        <i>Tax number</i>
                        {r.trn || "missing"}
                      </div>
                      <div>
                        <i>Paying account</i>
                        {r.iban_masked || "not stated"}
                      </div>
                      <div>
                        <i>Record</i>
                        {r.doc_id}
                      </div>
                    </div>
                  </div>
                )}
              </article>
            );
          })}
        </div>
      </main>
    </div>
  );
}
