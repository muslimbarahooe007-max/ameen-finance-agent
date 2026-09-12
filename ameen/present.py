"""Block Kit rendering.

Two rules drive everything here:
  1. Every claim carries its evidence, inline. A finding without a link to the
     message it relies on is arithmetic.
  2. A BLOCKED document renders no Approve button at all. Not a warning beside a
     button. The button is what gets finance teams defrauded.
"""
from __future__ import annotations

from .models import Decision, Finding, Level, Severity

_SEV = {
    Severity.BLOCKING: "BLOCKING",
    Severity.HIGH: "HIGH",
    Severity.MEDIUM: "MEDIUM",
    Severity.LOW: "LOW",
    Severity.INFO: "INFO",
}

_TRACK = {
    "T1_reimbursement": "Personal reimbursement",
    "T2_vendor_invoice": "Vendor invoice",
    "T3_purchase_order": "Purchase order",
    "T4_contract": "Contract",
}


def _finding_line(f: Finding) -> str:
    line = f"*[{_SEV[f.severity]}] {f.title}*\n{f.detail}"
    if f.evidence_url:
        line += f"\n<{f.evidence_url}|See the original message>"
    return line


def summary_text(d: Decision) -> str:
    doc = d.document
    who = doc.vendor or "unknown vendor"
    return f"{_TRACK.get(doc.track, 'Document')} from {who}: {doc.currency} {doc.total:,.2f} - {d.level.label}"


def card(d: Decision) -> list[dict]:
    doc = d.document
    blocks: list[dict] = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": _TRACK.get(doc.track, "Document")},
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Vendor*\n{doc.vendor or '-'}"},
                {"type": "mrkdwn", "text": f"*Amount*\n{doc.currency} {doc.total:,.2f}"},
                {"type": "mrkdwn", "text": f"*Reference*\n{doc.reference or '-'}"},
                {"type": "mrkdwn", "text": f"*Date*\n{doc.doc_date or '-'}"},
            ],
        },
    ]

    if doc.payment_terms or doc.po_reference or doc.trn:
        extra = "  ".join(
            p for p in (
                f"Terms: {doc.payment_terms}" if doc.payment_terms else "",
                f"PO: {doc.po_reference}" if doc.po_reference else "",
                f"TRN: {doc.trn}" if doc.trn else "",
            ) if p
        )
        blocks.append({"type": "context", "elements": [{"type": "mrkdwn", "text": extra}]})

    if d.findings:
        blocks.append({"type": "divider"})
        for f in d.findings:
            blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": _finding_line(f)}})
    else:
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "No compliance findings. Matches the channel record."},
            }
        )

    blocks.append({"type": "divider"})
    blocks.append(
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Routing*\n{d.level.label}\n_{d.reason}_"},
        }
    )

    elements: list[dict] = []
    if d.approvable and d.level is not Level.L0_AUTO:
        elements += [
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "Approve"},
                "style": "primary",
                "action_id": "approve_button",
                "value": d.doc_id,
            },
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "Reject"},
                "style": "danger",
                "action_id": "deny_button",
                "value": d.doc_id,
            },
        ]
    elements.append(
        {
            "type": "button",
            "text": {"type": "plain_text", "text": "Why?"},
            "action_id": "why_button",
            "value": d.doc_id,
        }
    )
    blocks.append({"type": "actions", "elements": elements})

    if not d.approvable:
        blocks.append(
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": (
                            "*No approval button has been offered on purpose.* "
                            "This needs out-of-band verification first, then re-submit."
                        ),
                    }
                ],
            }
        )
    elif d.level is Level.L0_AUTO:
        blocks.append(
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": "Auto-approved within policy. Posted for visibility only."}
                ],
            }
        )

    return blocks


def decided_blocks(d: Decision, decision: str, user_id: str, when: str) -> list[dict]:
    """The card after a human has decided. The card becomes the audit trail."""
    doc = d.document
    verb = "Approved" if decision == "approved" else "Rejected"
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*{verb}* by <@{user_id}> at {when}\n"
                    f"{_TRACK.get(doc.track, 'Document')} - {doc.vendor} - "
                    f"{doc.currency} {doc.total:,.2f} ({doc.reference or 'no reference'})"
                ),
            },
        },
        {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": f"{d.level.label} - {d.reason}"}],
        },
    ]


def trail_text(doc_row: dict, findings: list[Finding], approvals: list[dict]) -> str:
    """The 'Why?' answer: every check, its severity, its evidence."""
    lines = [f"*Decision trail for {doc_row.get('id')}*"]
    lines.append(
        f"{doc_row.get('vendor')} - {doc_row.get('currency')} "
        f"{float(doc_row.get('total') or 0):,.2f} - reference {doc_row.get('reference') or '-'}"
    )
    lines.append(f"Routing: {Level(int(doc_row.get('level') or 0)).label}")
    lines.append(f"Reason: {doc_row.get('reason') or '-'}")
    lines.append("")
    lines.append("*Checks that produced a finding*")
    if findings:
        for f in findings:
            entry = f"- `{f.code}` [{_SEV[f.severity]}] {f.title}: {f.detail}"
            if f.evidence_url:
                entry += f" <{f.evidence_url}|evidence>"
            lines.append(entry)
    else:
        lines.append("- none; every check passed")
    if approvals:
        lines.append("")
        lines.append("*Decisions*")
        for a in approvals:
            lines.append(f"- {a['decision']} by <@{a['approver']}> at {a['decided_at']}")
    return "\n".join(lines)
