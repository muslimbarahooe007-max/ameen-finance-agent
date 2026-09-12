"""Findings in, approval level out.

The rule worth noticing: a compliance flag escalates the item exactly one level.
A routine taxi claim is auto-approved; the same claim submitted twice goes to
finance. Almost no policy engine behaves this way, and it is four lines of code.
"""
from __future__ import annotations

from . import config
from .models import Document, Finding, Level, Severity


def base_level(doc: Document) -> Level:
    amount = doc.total or 0.0
    if amount <= config.L1_MAX:
        return Level.L0_AUTO
    if amount <= config.L2_MAX:
        return Level.L1_MANAGER
    if amount <= config.L3_MAX:
        return Level.L2_FINANCE
    return Level.L3_DUAL


def decide(doc: Document, findings: list[Finding]) -> tuple[Level, str]:
    base = base_level(doc)

    if any(f.severity is Severity.BLOCKING for f in findings):
        blocker = next(f for f in findings if f.severity is Severity.BLOCKING)
        return Level.BLOCKED, f"blocked: {blocker.title.lower()}"

    level = base
    reasons: list[str] = [f"{doc.currency} {doc.total:,.0f} sits at {base.label}"]

    highs = [f for f in findings if f.severity is Severity.HIGH]
    mediums = [f for f in findings if f.severity is Severity.MEDIUM]

    if highs:
        level = Level(min(int(level) + 1, int(Level.L3_DUAL)))
        reasons.append(f"escalated one level: {highs[0].title.lower()}")
    elif mediums:
        level = Level(min(int(level) + 1, int(Level.L3_DUAL)))
        reasons.append(f"escalated one level: {mediums[0].title.lower()}")

    return level, "; ".join(reasons)
