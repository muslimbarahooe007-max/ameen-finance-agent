"""The compliance engine.

A check is one function with one signature, registered in CHECKS. Adding a new
rule is adding a function, which is why contract-derived policy slots in here
later with no refactor.

Every check returns structured findings with a severity, and severity is what
drives the approval level in route.py. Nothing here decides who approves; it
only reports what is true.
"""
from __future__ import annotations

from dataclasses import dataclass

from . import config, store
from .models import Commitment, Document, Finding, Severity


@dataclass
class Context:
    """Everything a check is allowed to know beyond the document itself."""

    commitment: Commitment | None = None
    po: Commitment | None = None


def _pct(a: float, b: float) -> float:
    return abs(a - b) / b if b else 0.0


def _money(v: float, cur: str) -> str:
    return f"{cur} {v:,.2f}"


def check_commitment_mismatch(doc: Document, ctx: Context) -> list[Finding]:
    """The innovation: does the invoice match what was promised in the channel?"""
    c = ctx.commitment
    if not c or c.source != "channel" or not doc.total:
        return []
    delta = _pct(doc.total, c.amount)
    if delta <= config.PRICE_TOLERANCE:
        return []
    direction = "above" if doc.total > c.amount else "below"
    return [
        Finding(
            code="commitment_mismatch",
            severity=Severity.HIGH,
            title="Contradicts what was agreed in this channel",
            detail=(
                f"Invoice is {_money(doc.total, doc.currency)}, which is "
                f"{delta * 100:.0f}% {direction} the {_money(c.amount, c.currency)} agreed here. "
                f"The message said: “{c.text[:180]}”"
            ),
            evidence_url=c.permalink,
        )
    ]


def check_bank_details_changed(doc: Document, ctx: Context) -> list[Finding]:
    """The most expensive fraud in corporate finance, and the cheapest to catch."""
    if not doc.iban or not doc.vendor:
        return []
    known = store.known_iban(doc.vendor)
    if not known:
        return []
    if _norm_iban(doc.iban) == _norm_iban(known):
        return []
    history = store.iban_history(doc.vendor)
    return [
        Finding(
            code="bank_details_changed",
            severity=Severity.BLOCKING,
            title="Vendor bank details have changed",
            detail=(
                f"This invoice pays {_mask(doc.iban)}. The last {max(len(history), 1)} "
                f"invoice(s) from {doc.vendor} paid {_mask(known)}. "
                "Verify by phone, on a number you already hold, before anyone approves this. "
                "No approval button has been offered."
            ),
        )
    ]


def check_po_mismatch(doc: Document, ctx: Context) -> list[Finding]:
    po = ctx.po
    if not po or not doc.total:
        return []
    delta = _pct(doc.total, po.amount)
    if delta <= config.PRICE_TOLERANCE:
        return []
    return [
        Finding(
            code="po_mismatch",
            severity=Severity.MEDIUM,
            title=f"Does not match {po.reference or 'the purchase order'}",
            detail=(
                f"{po.reference or 'PO'} is {_money(po.amount, po.currency)}; "
                f"this invoice is {_money(doc.total, doc.currency)} "
                f"({delta * 100:.0f}% difference)."
            ),
            evidence_url=po.permalink,
        )
    ]


def check_duplicate(doc: Document, ctx: Context) -> list[Finding]:
    prior = store.seen_fingerprint(doc.fingerprint())
    if not prior:
        return []
    return [
        Finding(
            code="duplicate_document",
            severity=Severity.HIGH,
            title="Looks like a document already submitted",
            detail=(
                f"A document with the same vendor and reference was recorded on "
                f"{(prior.get('created_at') or '')[:10]} as {prior.get('id')}."
            ),
        )
    ]


def check_unreadable_fields(doc: Document, ctx: Context) -> list[Finding]:
    """Ameen asks rather than guessing. Illegibility is the normal case."""
    weak = doc.unreadable_fields(config.CONFIDENCE_FLOOR)
    if not weak:
        return []
    return [
        Finding(
            code="unreadable_fields",
            severity=Severity.MEDIUM,
            title="Could not read part of this document",
            detail=(
                "I am not confident about: " + ", ".join(weak) +
                ". Reply in this thread with the correct value and I will update the record. "
                "I have not guessed."
            ),
        )
    ]


def check_uae_tax_fields(doc: Document, ctx: Context) -> list[Finding]:
    """A UAE invoice without a TRN is a real rejection reason, not a nicety."""
    if doc.track != "T2_vendor_invoice" or doc.currency != "AED":
        return []
    if doc.trn:
        return []
    return [
        Finding(
            code="missing_trn",
            severity=Severity.LOW,
            title="No Tax Registration Number on the invoice",
            detail="A UAE VAT invoice needs a TRN. Finance will reject this at payment stage.",
        )
    ]


CHECKS = [
    check_commitment_mismatch,
    check_bank_details_changed,
    check_po_mismatch,
    check_duplicate,
    check_unreadable_fields,
    check_uae_tax_fields,
]


def run(doc: Document, ctx: Context) -> list[Finding]:
    findings: list[Finding] = []
    for fn in CHECKS:
        try:
            findings.extend(fn(doc, ctx))
        except Exception as exc:  # noqa: BLE001 - a broken check must not swallow the document
            findings.append(
                Finding(
                    code=f"check_error:{fn.__name__}",
                    severity=Severity.LOW,
                    title="A compliance check failed to run",
                    detail=f"{fn.__name__} raised {type(exc).__name__}: {exc}",
                )
            )
    return sorted(findings, key=lambda f: -int(f.severity))


def _norm_iban(v: str) -> str:
    return "".join(ch for ch in (v or "") if ch.isalnum()).upper()


def _mask(iban: str) -> str:
    n = _norm_iban(iban)
    return f"{n[:6]}...{n[-4:]}" if len(n) > 10 else n or "unknown"
