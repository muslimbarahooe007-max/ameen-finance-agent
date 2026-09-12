"""The shapes that move through the pipeline.

Deliberately small. Every stage takes one of these and returns one of these,
which is what lets a new source or a new check slot in without a refactor.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any


class Severity(IntEnum):
    """Ordered so that max() picks the worst finding."""

    INFO = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    BLOCKING = 4

    @property
    def label(self) -> str:
        return self.name


class Level(IntEnum):
    """Who has to approve. BLOCKED is deliberately not an approval level."""

    L0_AUTO = 0
    L1_MANAGER = 1
    L2_FINANCE = 2
    L3_DUAL = 3
    BLOCKED = 4

    @property
    def label(self) -> str:
        return {
            Level.L0_AUTO: "L0 auto-approved",
            Level.L1_MANAGER: "L1 manager approval",
            Level.L2_FINANCE: "L2 finance approval",
            Level.L3_DUAL: "L3 dual approval",
            Level.BLOCKED: "BLOCKED - cannot be approved here",
        }[self]


@dataclass
class Source:
    """Where a document came from. Slack today, IMAP tomorrow, same downstream."""

    kind: str  # "slack" | "imap"
    channel_id: str = ""
    user_id: str = ""
    file_id: str = ""
    filename: str = ""
    message_ts: str = ""


@dataclass
class Commitment:
    """Something somebody promised, found in the channel.

    `permalink` is the most important field in this codebase. A discrepancy
    without a link to the original message is arithmetic; with the link it is
    memory.
    """

    source: str  # "channel" | "po"
    vendor: str
    amount: float
    currency: str
    text: str
    permalink: str
    ts: str
    reference: str = ""  # e.g. PO-1043


@dataclass
class Finding:
    code: str
    severity: Severity
    title: str
    detail: str
    evidence_url: str = ""


@dataclass
class Document:
    doc_type: str = "unknown"
    track: str = "T2_vendor_invoice"
    vendor: str = ""
    reference: str = ""  # invoice number
    doc_date: str = ""
    currency: str = "AED"
    total: float = 0.0
    line_items: list[dict[str, Any]] = field(default_factory=list)
    payment_terms: str = ""
    iban: str = ""
    trn: str = ""
    po_reference: str = ""
    confidence: dict[str, float] = field(default_factory=dict)
    raw_text: str = ""
    source: Source | None = None

    def fingerprint(self) -> str:
        """Used to catch the same document submitted twice."""
        if self.reference:
            return f"{self.vendor.lower()}|{self.reference.lower()}"
        return f"{self.vendor.lower()}|{self.doc_date}|{self.total:.2f}"

    def unreadable_fields(self, floor: float) -> list[str]:
        return sorted(k for k, v in self.confidence.items() if v < floor)


@dataclass
class Decision:
    """The result of the whole pipeline, ready to be rendered."""

    document: Document
    findings: list[Finding]
    level: Level
    reason: str
    commitment: Commitment | None = None
    doc_id: str = ""

    @property
    def worst(self) -> Severity:
        return max((f.severity for f in self.findings), default=Severity.INFO)

    @property
    def approvable(self) -> bool:
        """BLOCKED documents render no Approve button at all.

        Not a warning beside a button. The button is absent, because the button
        is what gets finance teams defrauded.
        """
        return self.level is not Level.BLOCKED
