"use client";

import { useCallback, useEffect, useState } from "react";
import type { Record as Rec } from "@/lib/slack";

const money = (n: number, cur: string) =>
  `${cur} ${n.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;

export default function Queue() {
  const [records, setRecords] = useState<Rec[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  const load = useCallback(async () => {
    try {
      const res = await fetch("/api/decisions", { cache: "no-store" });
      const json = await res.json();
      if (!json.ok) throw new Error(json.error);
      setRecords(json.records);
      setError(null);
    } catch (err: any) {
      setError(String(err?.message ?? err));
    } finally {
      setLoaded(true);
    }
  }, []);

  // The queue is live: an invoice dropped in Slack shows up here on its own.
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

  const openCount = records.filter((r) => !r.decision && r.approvable).length;
  const heldCount = records.filter((r) => !r.approvable && !r.decision).length;

  return (
    <main className="sheet">
      <div className="masthead">
        <div>
          <h1>
            Ameen<span>أمين</span>
          </h1>
          <p className="strap">
            Invoices arrive in Slack. What your team promised in that channel arrives with
            them.
          </p>
        </div>
        <div className="count">
          <span className="beat" aria-hidden />
          {openCount} awaiting you
          {heldCount > 0 ? `, ${heldCount} held` : ""}
        </div>
      </div>

      {error && <p className="notice">{error}</p>}

      <div className="ledger">
        {loaded && records.length === 0 && !error && (
          <div className="blank">
            <b>Nothing in the queue.</b>
            Drop an invoice into the Slack channel and it will appear here.
          </div>
        )}

        {records.map((r) => {
          const cited = r.commitment;
          const over = cited && r.total > cited.amount;
          const delta = cited && cited.amount ? (r.total - cited.amount) / cited.amount : 0;
          const isOpen = open === r.ts;

          return (
            <article
              key={r.ts}
              className={`entry${!r.approvable ? " is-blocked" : ""}${r.decision ? " is-settled" : ""}`}
            >
              <div
                className="line"
                role="button"
                tabIndex={0}
                onClick={() => setOpen(isOpen ? null : r.ts)}
                onKeyDown={(e) => e.key === "Enter" && setOpen(isOpen ? null : r.ts)}
              >
                <div className="party">
                  <b>{r.vendor || "Unknown vendor"}</b>
                  <small>
                    {[r.reference, r.po_reference, r.doc_date].filter(Boolean).join("  ")}
                  </small>
                </div>

                <div className="figures">
                  {cited && (
                    <span className="fig agreed">
                      <i>agreed</i>
                      <b>{money(cited.amount, cited.currency)}</b>
                    </span>
                  )}
                  <span className={`fig ${over ? "billed" : "plain"}`}>
                    <i>invoiced</i>
                    <b>{money(r.total, r.currency)}</b>
                  </span>
                  {cited && Math.abs(delta) > 0.001 && (
                    <span className="delta">
                      {delta > 0 ? "+" : ""}
                      {(delta * 100).toFixed(0)}%
                    </span>
                  )}
                </div>

                <div className={`routing${!r.approvable ? " blocked" : ""}`}>
                  <b>{r.level_label}</b>
                  <small>{r.reason}</small>
                </div>

                {r.decision ? (
                  <div className="settled">
                    {r.decision} by {r.approver}
                    <br />
                    {r.decided_at}
                  </div>
                ) : r.approvable ? (
                  <div className="act" onClick={(e) => e.stopPropagation()}>
                    <button
                      className="settle"
                      disabled={busy === r.ts}
                      onClick={() => settle(r.ts, "approved")}
                    >
                      Approve
                    </button>
                    <button
                      className="refuse"
                      disabled={busy === r.ts}
                      onClick={() => settle(r.ts, "rejected")}
                    >
                      Reject
                    </button>
                  </div>
                ) : (
                  <p className="held">
                    Held. Verify the bank details by phone before this can be approved.
                  </p>
                )}
              </div>

              {cited && (
                <div className="quote">
                  <blockquote>
                    {cited.text}
                    <cite>
                      Said in the channel before this invoice existed.{" "}
                      {cited.permalink && (
                        <a href={cited.permalink} target="_blank" rel="noreferrer">
                          Open the message
                        </a>
                      )}
                    </cite>
                  </blockquote>
                </div>
              )}

              {isOpen && (
                <div className="detail">
                  {r.findings.map((f) => (
                    <div key={f.code} className={`flag s-${f.severity}`}>
                      <b>{f.title}</b>
                      <p>
                        {f.detail}{" "}
                        {f.evidence_url && (
                          <a href={f.evidence_url} target="_blank" rel="noreferrer">
                            See the evidence
                          </a>
                        )}
                      </p>
                    </div>
                  ))}
                  {r.findings.length === 0 && (
                    <p className="strap">Every check passed. Nothing to look at.</p>
                  )}
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
                      <i>Reference</i>
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
  );
}
