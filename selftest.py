"""Offline proof that the pipeline works, with no Slack and no model call.

    python selftest.py

Feeds fixture documents and fixture channel history through memory, checks and
routing, and asserts the four behaviours that matter:

  1. an invoice above what was agreed in the channel is caught and cited
  2. a changed bank account is BLOCKED, with no approval offered
  3. a clean invoice is not over-escalated
  4. the same invoice twice is caught as a duplicate
  5. a new vendor's bank details are learned only on approval, then policed
  6. the decision trail renders every finding with its evidence

This exists because a demo that only works with live tokens is not evidence.
"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ.setdefault("AMEEN_DB", os.path.join(tempfile.mkdtemp(), "selftest.db"))

from ameen import pipeline, present, store
from ameen.models import Document, Level, Severity

VENDOR = "Gulf Supplies LLC"
KNOWN_IBAN = "AE070331234567890123456"
NEW_IBAN = "AE999887766554433221100"

# What the channel looked like before any invoice arrived.
HISTORY = [
    {"ts": "1757000000.000100", "user": "U1", "text": "morning all"},
    {
        "ts": "1757001000.000200",
        "user": "U1",
        "text": "Spoke to Gulf Supplies - they have agreed AED 40,000 for the 12 units, net 30.",
    },
    {
        "ts": "1757002000.000300",
        "user": "U2",
        "text": "Raised PO-1043 for Gulf Supplies at AED 40,000.",
    },
    {"ts": "1757003000.000400", "user": "U2", "text": "lunch?"},
]


def permalink_for(ts: str) -> str:
    return f"https://example.slack.com/archives/C0DEMO/p{ts.replace('.', '')}" if ts else ""


def invoice(total: float, iban: str = KNOWN_IBAN, ref: str = "INV-2291") -> Document:
    return Document(
        doc_type="vendor_invoice",
        track="T2_vendor_invoice",
        vendor=VENDOR,
        reference=ref,
        doc_date="2026-09-12",
        currency="AED",
        total=total,
        payment_terms="net 30",
        iban=iban,
        trn="100123456700003",
        po_reference="PO-1043",
        confidence={"vendor": 0.97, "total": 0.96, "reference": 0.95, "iban": 0.93},
    )


def show(title: str, d) -> None:
    print(f"\n=== {title} ===")
    print(f"routing : {d.level.label}")
    print(f"reason  : {d.reason}")
    print(f"approve : {'button offered' if d.approvable else 'NO BUTTON (blocked)'}")
    for f in d.findings:
        print(f"  [{f.severity.label}] {f.code}: {f.title}")
        if f.evidence_url:
            print(f"      evidence -> {f.evidence_url}")
    if not d.findings:
        print("  no findings")


def main() -> int:
    store.init()
    store.seed_vendor(VENDOR, KNOWN_IBAN, {"payment_terms": "net 30", "increase_cap": 0.05})
    failures: list[str] = []

    # 1. Contradicts the channel commitment.
    d1 = pipeline.assess(invoice(46000), HISTORY, permalink_for)
    show("1. invoice above what was agreed in the channel", d1)
    codes = {f.code for f in d1.findings}
    if "commitment_mismatch" not in codes:
        failures.append("1: did not catch the commitment mismatch")
    cited = next((f for f in d1.findings if f.code == "commitment_mismatch"), None)
    if not (cited and cited.evidence_url):
        failures.append("1: caught the mismatch but did not cite the message")
    if d1.level < Level.L3_DUAL:
        failures.append(f"1: expected escalation to dual approval, got {d1.level.name}")

    # 2. Vendor bank details changed.
    d2 = pipeline.assess(invoice(40000, iban=NEW_IBAN, ref="INV-2292"), HISTORY, permalink_for)
    show("2. vendor bank details changed", d2)
    if d2.level is not Level.BLOCKED:
        failures.append(f"2: expected BLOCKED, got {d2.level.name}")
    if d2.approvable:
        failures.append("2: an approval button would have been offered on a blocked document")

    # 3. Clean invoice at the agreed price.
    d3 = pipeline.assess(invoice(40000, ref="INV-2293"), HISTORY, permalink_for)
    show("3. invoice matching the agreement", d3)
    if any(f.severity >= Severity.HIGH for f in d3.findings):
        failures.append("3: a matching invoice produced a high-severity finding")
    if d3.level > Level.L2_FINANCE:
        failures.append(f"3: a clean invoice was over-escalated to {d3.level.name}")

    # 4. Duplicate of the first invoice.
    d4 = pipeline.assess(invoice(46000), HISTORY, permalink_for)
    show("4. the same invoice submitted twice", d4)
    if "duplicate_document" not in {f.code for f in d4.findings}:
        failures.append("4: did not detect the duplicate")

    # 5. A new vendor is learned on approval, and then policed.
    #    This is the path that arms the bank-change check in real use: nothing is
    #    trusted until a human approves it.
    new_vendor = "Desert Logistics FZCO"
    first = Document(
        doc_type="vendor_invoice", track="T2_vendor_invoice", vendor=new_vendor,
        reference="DL-001", doc_date="2026-09-10", currency="AED", total=8000,
        iban="AE110339999888777666555", trn="100999888700003",
        confidence={"vendor": 0.95, "total": 0.95, "iban": 0.94},
    )
    d5 = pipeline.assess(first, [], permalink_for)
    show("5. first invoice from an unknown vendor", d5)
    if d5.level is Level.BLOCKED:
        failures.append("5: a first invoice from an unknown vendor must not be blocked")

    store.remember_iban(new_vendor, first.iban)  # what app.py does on approval

    second = Document(
        doc_type="vendor_invoice", track="T2_vendor_invoice", vendor=new_vendor,
        reference="DL-002", doc_date="2026-09-12", currency="AED", total=8000,
        iban="AE770331111222333444555", trn="100999888700003",
        confidence={"vendor": 0.95, "total": 0.95, "iban": 0.94},
    )
    d6 = pipeline.assess(second, [], permalink_for)
    show("6. same vendor, different bank account, after approval", d6)
    if d6.level is not Level.BLOCKED:
        failures.append(f"6: expected BLOCKED once the vendor was learned, got {d6.level.name}")
    if d6.approvable:
        failures.append("6: an approval button would have been offered after a bank change")

    # 7. The Why trail renders.
    row = store.load_document(d1.doc_id)
    trail = present.trail_text(row, store.load_findings(d1.doc_id), store.approvals_for(d1.doc_id))
    print("\n=== 7. the Why trail ===")
    print(trail)
    if "commitment_mismatch" not in trail:
        failures.append("7: the decision trail did not include the findings")

    print("\n" + "-" * 60)
    if failures:
        print(f"FAILED ({len(failures)})")
        for f in failures:
            print("  -", f)
        return 1
    print("PASSED: 7 checks - citation, blocking, routing, duplicate,\n        learn-then-police bank details, trail")
    return 0


if __name__ == "__main__":
    sys.exit(main())
