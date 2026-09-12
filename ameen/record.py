"""The tracker. Google Sheets when configured, otherwise local only.

Degrades rather than crashes: if the sheet is not reachable, the approval still
happens and is still persisted, and the caller is told the row did not land.
That is the difference between a demo and something you would run.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from . import config, store
from .models import Decision, Level

log = logging.getLogger("ameen.record")

HEADERS = [
    "recorded_at", "doc_id", "track", "vendor", "reference", "doc_date",
    "currency", "amount", "routing", "findings", "decision", "approver", "evidence",
]


def _ws():
    if not (config.SHEET_ID and config.SERVICE_ACCOUNT_JSON):
        return None
    import gspread

    gc = gspread.service_account(filename=config.SERVICE_ACCOUNT_JSON)
    return gc.open_by_key(config.SHEET_ID).sheet1


def ensure_headers() -> None:
    ws = _ws()
    if ws is None:
        log.info("tracker not configured; approvals will be recorded locally only")
        return
    try:
        if not ws.row_values(1):
            ws.append_row(HEADERS)
    except Exception as exc:  # noqa: BLE001 - the tracker must degrade, never block an approval
        log.warning(
            "could not prepare the tracker sheet (%s): is it shared with the "
            "service account email?", exc,
        )


def row_for(d: Decision, decision: str, approver: str) -> list:
    doc = d.document
    evidence = next((f.evidence_url for f in d.findings if f.evidence_url), "")
    return [
        datetime.now(timezone.utc).isoformat(timespec="seconds"),
        d.doc_id,
        doc.track,
        doc.vendor,
        doc.reference,
        doc.doc_date,
        doc.currency,
        round(doc.total, 2),
        d.level.label,
        "; ".join(f"{f.code}[{f.severity.label}]" for f in d.findings) or "none",
        decision,
        approver,
        evidence,
    ]


def append(d: Decision, decision: str, approver: str) -> tuple[bool, str]:
    """Returns (landed_in_sheet, human_readable_note)."""
    store.record_approval(d.doc_id, int(d.level), approver, decision)

    # A blocked document is never written to the tracker.
    if d.level is Level.BLOCKED:
        return False, "not written to the tracker while blocked"

    ws = _ws()
    if ws is None:
        return False, "tracker not configured; recorded locally only"
    try:
        ws.append_row(row_for(d, decision, approver), value_input_option="USER_ENTERED")
        return True, "row appended to the tracker"
    except Exception as exc:  # noqa: BLE001 - the tracker must degrade, never block an approval
        return False, f"tracker write failed ({type(exc).__name__}); recorded locally"
