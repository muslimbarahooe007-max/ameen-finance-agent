"""Document to structured fields, via a vision model routed through OpenRouter.

Returns per-field confidence, because the confidence is what lets Ameen ask a
question instead of guessing. A finance agent that silently returns its best
guess about a number is worse than one that returns nothing.
"""
from __future__ import annotations

import base64
import io
import json
import mimetypes

from . import config
from .models import Document, Source

SYSTEM = """You extract structured data from finance documents for an approval workflow.

Return ONLY a JSON object with these keys:
  doc_type        one of: vendor_invoice, reimbursement_receipt, purchase_order, contract
  vendor          the counterparty's name as written
  reference       invoice number, receipt number or PO number
  doc_date        ISO date YYYY-MM-DD, or "" if absent
  currency        ISO code, e.g. AED
  total           the grand total as a number, no separators
  line_items      list of {description, quantity, unit_price, amount}
  payment_terms   e.g. "net 30", or ""
  iban            the bank account/IBAN shown for payment, or ""
  trn             the Tax Registration Number / VAT number, or ""
  po_reference    a referenced purchase order, e.g. "PO-1043", or ""
  confidence      object mapping each of the above field names to a number 0.0-1.0

Rules:
- Never invent a value. If a field is absent or unreadable, use "" or 0 and set
  its confidence below 0.5.
- Confidence must reflect legibility, not plausibility.
- Amounts are numbers, not strings.
"""


def _client():
    # Imported lazily so the offline self-test needs no model SDK installed.
    from openai import OpenAI

    return OpenAI(
        api_key=config.OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1",
    )


def _pdf_text(data: bytes) -> str:
    try:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))
        return "\n".join((page.extract_text() or "") for page in reader.pages[:5]).strip()
    except Exception:  # noqa: BLE001 - an unreadable document falls through to vision
        return ""


def _content_blocks(data: bytes, filename: str) -> list[dict]:
    mime = mimetypes.guess_type(filename)[0] or ""
    if filename.lower().endswith(".pdf") or mime == "application/pdf":
        text = _pdf_text(data)
        if text:
            return [{"type": "text", "text": f"Document text:\n\n{text[:12000]}"}]
        # A scanned document with no text layer: fall through to vision.
        mime = "image/png"
    if not mime.startswith("image/"):
        mime = "image/png"
    uri = f"data:{mime};base64,{base64.b64encode(data).decode()}"
    return [
        {"type": "text", "text": "Extract the fields from this document."},
        {"type": "image_url", "image_url": {"url": uri}},
    ]


def _coerce(payload: dict, source: Source | None, raw_text: str) -> Document:
    def num(v) -> float:
        try:
            return float(str(v).replace(",", "").strip() or 0)
        except ValueError:
            return 0.0

    doc_type = str(payload.get("doc_type") or "unknown")
    track = {
        "vendor_invoice": "T2_vendor_invoice",
        "reimbursement_receipt": "T1_reimbursement",
        "purchase_order": "T3_purchase_order",
        "contract": "T4_contract",
    }.get(doc_type, "T2_vendor_invoice")

    conf_in = payload.get("confidence") or {}
    confidence = {}
    for key in ("vendor", "reference", "doc_date", "total", "iban", "trn"):
        try:
            confidence[key] = float(conf_in.get(key, 0.9))
        except (TypeError, ValueError):
            confidence[key] = 0.9

    return Document(
        doc_type=doc_type,
        track=track,
        vendor=str(payload.get("vendor") or "").strip(),
        reference=str(payload.get("reference") or "").strip(),
        doc_date=str(payload.get("doc_date") or "").strip(),
        currency=(str(payload.get("currency") or "AED").strip().upper() or "AED"),
        total=num(payload.get("total")),
        line_items=payload.get("line_items") or [],
        payment_terms=str(payload.get("payment_terms") or "").strip(),
        iban=str(payload.get("iban") or "").strip(),
        trn=str(payload.get("trn") or "").strip(),
        po_reference=str(payload.get("po_reference") or "").strip(),
        confidence=confidence,
        raw_text=raw_text,
        source=source,
    )


def extract(data: bytes, filename: str, source: Source | None = None) -> Document:
    blocks = _content_blocks(data, filename)
    raw_text = next((b["text"] for b in blocks if b["type"] == "text"), "")

    resp = _client().chat.completions.create(
        model=config.MODEL,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": blocks},
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )
    body = resp.choices[0].message.content or "{}"
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        start, end = body.find("{"), body.rfind("}")
        payload = json.loads(body[start : end + 1]) if start >= 0 < end else {}

    return _coerce(payload, source, raw_text)
