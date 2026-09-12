"""Persistence. SQLite, because the fraud checks genuinely need history.

A bank-detail change is only detectable if you remember the last one, and a
duplicate is only detectable if you remember the first.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

from . import config
from .models import Decision, Document, Finding, Severity

SCHEMA = """
CREATE TABLE IF NOT EXISTS vendors (
    name         TEXT PRIMARY KEY,
    iban         TEXT,
    iban_history TEXT NOT NULL DEFAULT '[]',
    terms_json   TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS documents (
    id           TEXT PRIMARY KEY,
    track        TEXT,
    vendor       TEXT,
    reference    TEXT,
    doc_date     TEXT,
    currency     TEXT,
    total        REAL,
    fingerprint  TEXT,
    level        INTEGER,
    reason       TEXT,
    fields_json  TEXT,
    created_at   TEXT
);
CREATE INDEX IF NOT EXISTS idx_documents_fp ON documents(fingerprint);
CREATE TABLE IF NOT EXISTS findings (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id  TEXT,
    code         TEXT,
    severity     INTEGER,
    title        TEXT,
    detail       TEXT,
    evidence_url TEXT
);
CREATE TABLE IF NOT EXISTS approvals (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id  TEXT,
    level        INTEGER,
    approver     TEXT,
    decision     TEXT,
    decided_at   TEXT
);
"""


@contextmanager
def conn():
    c = sqlite3.connect(config.DB_PATH)
    c.row_factory = sqlite3.Row
    try:
        yield c
        c.commit()
    finally:
        c.close()


def init() -> None:
    with conn() as c:
        c.executescript(SCHEMA)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# --- vendors -------------------------------------------------------------

def known_iban(vendor: str) -> str | None:
    with conn() as c:
        row = c.execute("SELECT iban FROM vendors WHERE name = ?", (vendor.lower(),)).fetchone()
    return row["iban"] if row and row["iban"] else None


def iban_history(vendor: str) -> list[str]:
    with conn() as c:
        row = c.execute(
            "SELECT iban_history FROM vendors WHERE name = ?", (vendor.lower(),)
        ).fetchone()
    return json.loads(row["iban_history"]) if row else []


def remember_iban(vendor: str, iban: str) -> None:
    """Record a vendor's bank details. Only called once a human has accepted them."""
    if not vendor or not iban:
        return
    key = vendor.lower()
    history = iban_history(key)
    if iban not in history:
        history.append(iban)
    with conn() as c:
        c.execute(
            """INSERT INTO vendors(name, iban, iban_history) VALUES(?,?,?)
               ON CONFLICT(name) DO UPDATE SET iban=excluded.iban,
                                               iban_history=excluded.iban_history""",
            (key, iban, json.dumps(history)),
        )


def seed_vendor(vendor: str, iban: str, terms: dict | None = None) -> None:
    """Used by the demo fixture and the self-test to establish prior history."""
    with conn() as c:
        c.execute(
            """INSERT INTO vendors(name, iban, iban_history, terms_json) VALUES(?,?,?,?)
               ON CONFLICT(name) DO UPDATE SET iban=excluded.iban,
                                               iban_history=excluded.iban_history,
                                               terms_json=excluded.terms_json""",
            (vendor.lower(), iban, json.dumps([iban]), json.dumps(terms or {})),
        )


# --- documents -----------------------------------------------------------

def seen_fingerprint(fp: str) -> dict | None:
    with conn() as c:
        row = c.execute(
            "SELECT id, reference, doc_date, created_at FROM documents WHERE fingerprint = ?"
            " ORDER BY created_at LIMIT 1",
            (fp,),
        ).fetchone()
    return dict(row) if row else None


def save(decision: Decision) -> str:
    doc: Document = decision.document
    doc_id = decision.doc_id or uuid.uuid4().hex[:10]
    with conn() as c:
        c.execute(
            """INSERT OR REPLACE INTO documents
               (id, track, vendor, reference, doc_date, currency, total, fingerprint,
                level, reason, fields_json, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                doc_id, doc.track, doc.vendor, doc.reference, doc.doc_date, doc.currency,
                doc.total, doc.fingerprint(), int(decision.level), decision.reason,
                json.dumps({
                    "confidence": doc.confidence,
                    "iban": doc.iban,
                    "trn": doc.trn,
                    "po_reference": doc.po_reference,
                    "payment_terms": doc.payment_terms,
                }),
                _now(),
            ),
        )
        c.execute("DELETE FROM findings WHERE document_id = ?", (doc_id,))
        for f in decision.findings:
            c.execute(
                """INSERT INTO findings(document_id, code, severity, title, detail, evidence_url)
                   VALUES (?,?,?,?,?,?)""",
                (doc_id, f.code, int(f.severity), f.title, f.detail, f.evidence_url),
            )
    return doc_id


def load_findings(doc_id: str) -> list[Finding]:
    with conn() as c:
        rows = c.execute(
            "SELECT code, severity, title, detail, evidence_url FROM findings"
            " WHERE document_id = ? ORDER BY severity DESC",
            (doc_id,),
        ).fetchall()
    return [
        Finding(r["code"], Severity(r["severity"]), r["title"], r["detail"], r["evidence_url"])
        for r in rows
    ]


def load_document(doc_id: str) -> dict | None:
    with conn() as c:
        row = c.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
    return dict(row) if row else None


def record_approval(doc_id: str, level: int, approver: str, decision: str) -> None:
    with conn() as c:
        c.execute(
            """INSERT INTO approvals(document_id, level, approver, decision, decided_at)
               VALUES (?,?,?,?,?)""",
            (doc_id, level, approver, decision, _now()),
        )


def approvals_for(doc_id: str) -> list[dict]:
    with conn() as c:
        rows = c.execute(
            "SELECT * FROM approvals WHERE document_id = ? ORDER BY id", (doc_id,)
        ).fetchall()
    return [dict(r) for r in rows]
