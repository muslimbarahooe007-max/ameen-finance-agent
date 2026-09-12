"""The pipeline. One path, whatever the source and whatever the track.

    ingest -> extract -> memory -> checks -> route -> present -> record

Slack upload is source adapter one; IMAP is adapter two and changes nothing
downstream. A vendor invoice and a personal reimbursement are the same pipeline
with different checks, not two systems.
"""
from __future__ import annotations

import uuid

from . import checks, memory, route, store
from . import extract as extract_mod
from .models import Decision, Document, Source


def build_context(doc: Document, messages: list[dict], permalink_for) -> checks.Context:
    """Ask the channel what was promised about this vendor."""
    if not doc.vendor:
        return checks.Context()
    commitments = memory.candidates_from_messages(
        messages, doc.vendor, permalink_for, po_reference=doc.po_reference
    )
    return checks.Context(
        commitment=memory.best_commitment(commitments, prefer="channel"),
        po=memory.find_po(commitments),
    )


def assess(doc: Document, messages: list[dict], permalink_for) -> Decision:
    ctx = build_context(doc, messages, permalink_for)
    findings = checks.run(doc, ctx)
    level, reason = route.decide(doc, findings)

    decision = Decision(
        document=doc,
        findings=findings,
        level=level,
        reason=reason,
        commitment=ctx.commitment,
        doc_id=uuid.uuid4().hex[:10],
    )
    # Persist before presenting, so the Why button always has something to read
    # even if rendering fails.
    decision.doc_id = store.save(decision)
    return decision


def process_bytes(
    data: bytes,
    filename: str,
    source: Source,
    messages: list[dict],
    permalink_for,
) -> Decision:
    doc = extract_mod.extract(data, filename, source)
    return assess(doc, messages, permalink_for)
