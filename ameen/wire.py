"""Slack message metadata as the shared record.

Ameen attaches the whole structured decision to its Slack message as machine
readable metadata. Slack does not render it, humans never see it, and any other
surface can read it straight back out of the channel.

That is why the web dashboard needs no database: the channel already holds the
record, the evidence and the audit trail in one place, which is the same claim
the product makes about commitments.

Metadata payload values must be primitives, so the record travels as one JSON
string under `record`.
"""
from __future__ import annotations

import json

from .models import Decision

EVENT_TYPE = "ameen_decision"


def to_metadata(d: Decision, file_url: str = "") -> dict:
    doc = d.document
    record = {
        "doc_id": d.doc_id,
        "track": doc.track,
        "vendor": doc.vendor,
        "reference": doc.reference,
        "doc_date": doc.doc_date,
        "currency": doc.currency,
        "total": round(doc.total, 2),
        "payment_terms": doc.payment_terms,
        "po_reference": doc.po_reference,
        "trn": doc.trn,
        "iban_masked": _mask(doc.iban),
        "level": int(d.level),
        "level_label": d.level.label,
        "approvable": d.approvable,
        "reason": d.reason,
        "file_url": file_url,
        "findings": [
            {
                "code": f.code,
                "severity": f.severity.label,
                "title": f.title,
                "detail": f.detail,
                "evidence_url": f.evidence_url,
            }
            for f in d.findings
        ],
        "commitment": (
            {
                "text": d.commitment.text,
                "amount": d.commitment.amount,
                "currency": d.commitment.currency,
                "permalink": d.commitment.permalink,
            }
            if d.commitment
            else None
        ),
    }
    return {"event_type": EVENT_TYPE, "event_payload": {"record": json.dumps(record)}}


def _mask(iban: str) -> str:
    n = "".join(c for c in (iban or "") if c.isalnum()).upper()
    return f"{n[:6]}...{n[-4:]}" if len(n) > 10 else n
