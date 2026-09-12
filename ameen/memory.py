"""Channel memory — the reason this project is not an expense bot.

Ameen lives in the channel where commitments are made, so weeks later it can
say what was agreed and link to the exact message. A chat window cannot do
this: it would need a human to remember the conversation happened, find it and
paste it in, and anyone who could do that would not need the agent.

Deliberately deterministic. At 14:40 on a hackathon clock, a regex that always
finds the right message beats a clever retrieval scheme that sometimes does.
"""
from __future__ import annotations

import re

from .models import Commitment

# "AED 40,000" / "40,000 AED" / "40000" / "40k"
_CURRENCIES = r"(?:AED|USD|EUR|GBP|SAR|QAR|Dhs?)"
_NUM = r"\d{1,3}(?:[,\s]\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?"
_AMOUNT_RE = re.compile(
    rf"(?:{_CURRENCIES}\s*)?(?P<num>{_NUM})\s*(?P<k>k\b)?\s*(?P<cur>{_CURRENCIES})?",
    re.IGNORECASE,
)
_PO_RE = re.compile(r"\b(PO[-\s]?\d{2,8})\b", re.IGNORECASE)
_AGREE_RE = re.compile(
    r"\b(agree|agreed|quoted|quote|confirm|confirmed|price|rate|net\s*\d+|"
    r"approved at|settled on|will charge|charging)\b",
    re.IGNORECASE,
)


def parse_amounts(text: str) -> list[tuple[float, str]]:
    """Every plausible money amount in a message, largest first."""
    out: list[tuple[float, str]] = []
    for m in _AMOUNT_RE.finditer(text or ""):
        raw = m.group("num").replace(",", "").replace(" ", "")
        try:
            value = float(raw)
        except ValueError:
            continue
        if m.group("k"):
            value *= 1000
        # Ignore bare small integers; they are quantities, dates or line numbers.
        if value < 100 and not m.group("cur"):
            continue
        out.append((value, (m.group("cur") or "").upper()))
    return sorted(out, key=lambda t: -t[0])


def _vendor_tokens(vendor: str) -> list[str]:
    noise = {"llc", "fzco", "fze", "ltd", "limited", "co", "company", "trading",
             "general", "est", "establishment", "the", "and"}
    return [t for t in re.findall(r"[a-z]+", (vendor or "").lower())
            if len(t) > 2 and t not in noise]


def _mentions_vendor(text: str, vendor: str) -> bool:
    low = (text or "").lower()
    tokens = _vendor_tokens(vendor)
    return bool(tokens) and any(t in low for t in tokens)


def candidates_from_messages(
    messages: list[dict],
    vendor: str,
    permalink_for,
    po_reference: str = "",
) -> list[Commitment]:
    """Turn raw channel history into commitments relevant to this vendor.

    `permalink_for(ts)` is injected so this module never touches the Slack
    client, which is what makes it testable offline.
    """
    found: list[Commitment] = []
    for msg in messages:
        if msg.get("subtype") == "channel_join":
            continue
        text = msg.get("text") or ""
        if not text:
            continue

        po_match = _PO_RE.search(text)
        po_ref = po_match.group(1).upper().replace(" ", "-") if po_match else ""
        po_hit = bool(po_reference) and po_ref.replace("-", "") == po_reference.upper().replace("-", "").replace(" ", "")

        vendor_hit = _mentions_vendor(text, vendor)
        if not (vendor_hit or po_hit):
            continue
        if not (_AGREE_RE.search(text) or po_ref):
            continue

        amounts = parse_amounts(text)
        if not amounts:
            continue

        value, currency = amounts[0]
        found.append(
            Commitment(
                source="po" if po_ref else "channel",
                vendor=vendor,
                amount=value,
                currency=currency or "AED",
                text=text.strip(),
                permalink=permalink_for(msg.get("ts", "")),
                ts=msg.get("ts", ""),
                reference=po_ref,
            )
        )

    # Newest first: the most recent agreement supersedes older ones.
    return sorted(found, key=lambda c: float(c.ts or 0), reverse=True)


def best_commitment(commitments: list[Commitment], prefer: str = "channel") -> Commitment | None:
    if not commitments:
        return None
    preferred = [c for c in commitments if c.source == prefer]
    return (preferred or commitments)[0]


def find_po(commitments: list[Commitment]) -> Commitment | None:
    return next((c for c in commitments if c.source == "po"), None)
