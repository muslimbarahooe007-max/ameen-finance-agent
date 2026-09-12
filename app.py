"""Ameen - the finance agent that remembers what was promised.

Runs in Socket Mode, so there is no public URL, no tunnel and no deploy needed.

    cp env.sample .env      # fill in the two Slack tokens and an OpenRouter key
    python app.py

See STACK.md section 1 for the exact Slack app click path, and section 9 for the
five things that waste the most time.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from ameen import config, pipeline, present, record, store
from ameen.models import Decision, Document, Level
from ameen.sources import slack_source

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("ameen")

# Socket Mode carries no inbound HTTP requests, so there is nothing to verify a
# signature against. Bolt still demands a signing secret unless verification is
# explicitly turned off, which is a 15-minute trap if you do not know it.
app = App(token=config.SLACK_BOT_TOKEN, request_verification_enabled=False)

# A single upload arrives as both file_shared and message/file_share. Handle once.
_handled: set[str] = set()


def _once(file_id: str) -> bool:
    if file_id in _handled:
        return False
    _handled.add(file_id)
    return True


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


# --------------------------------------------------------------------------
# Ingest: a document lands in the channel
# --------------------------------------------------------------------------

@app.event("file_shared")
def on_file_shared(event, client, logger):
    file_id = event.get("file_id") or (event.get("file") or {}).get("id")
    channel_id = event.get("channel_id") or event.get("channel")
    if not file_id or not channel_id or not _once(file_id):
        return
    _handle_document(client, file_id, channel_id, event.get("user_id", ""))


@app.event("message")
def on_message(event, client, logger):
    """Uploads also arrive here with subtype file_share. Everything else is context."""
    if event.get("subtype") != "file_share":
        return
    channel_id = event.get("channel", "")
    for f in event.get("files", []) or []:
        if f.get("id") and _once(f["id"]):
            _handle_document(client, f["id"], channel_id, event.get("user", ""))


def _handle_document(client, file_id: str, channel_id: str, user_id: str) -> None:
    thinking = None
    try:
        thinking = client.chat_postMessage(
            channel=channel_id, text="Looking at this and checking what we agreed."
        )

        data, filename, source = slack_source.fetch(client, file_id, channel_id, user_id)
        messages = slack_source.channel_history(client, channel_id)
        permalink_for = slack_source.permalink_getter(client, channel_id)

        decision = pipeline.process_bytes(data, filename, source, messages, permalink_for)

        client.chat_update(
            channel=channel_id,
            ts=thinking["ts"],
            text=present.summary_text(decision),
            blocks=present.card(decision),
        )
        log.info(
            "processed %s: %s %s level=%s findings=%s",
            filename, decision.document.vendor, decision.document.total,
            decision.level.name, [f.code for f in decision.findings],
        )

        # Auto-approved items still get recorded, with no human in the loop.
        if decision.level is Level.L0_AUTO:
            _, note = record.append(decision, "auto-approved", "ameen")
            client.chat_postMessage(
                channel=channel_id, thread_ts=thinking["ts"],
                text=f"Auto-approved within policy; {note}.",
            )

    except Exception as exc:  # surface the failure in the channel, never swallow it
        log.exception("failed to process file %s", file_id)
        msg = f"I could not process that document: {type(exc).__name__}: {exc}"
        if thinking:
            client.chat_update(channel=channel_id, ts=thinking["ts"], text=msg, blocks=[])
        else:
            client.chat_postMessage(channel=channel_id, text=msg)


# --------------------------------------------------------------------------
# Decisions
# --------------------------------------------------------------------------

def _rebuild(doc_id: str) -> Decision | None:
    """Reconstruct the decision from storage, so a restart cannot orphan a card."""
    row = store.load_document(doc_id)
    if not row:
        return None
    try:
        fields = json.loads(row["fields_json"] or "{}")
    except (TypeError, ValueError):
        fields = {}
    doc = Document(
        track=row["track"] or "T2_vendor_invoice",
        vendor=row["vendor"] or "",
        reference=row["reference"] or "",
        doc_date=row["doc_date"] or "",
        currency=row["currency"] or "AED",
        total=float(row["total"] or 0),
        iban=fields.get("iban", "") or "",
        trn=fields.get("trn", "") or "",
        po_reference=fields.get("po_reference", "") or "",
        payment_terms=fields.get("payment_terms", "") or "",
        confidence=fields.get("confidence") or {},
    )
    return Decision(
        document=doc,
        findings=store.load_findings(doc_id),
        level=Level(int(row["level"] or 0)),
        reason=row["reason"] or "",
        doc_id=doc_id,
    )


@app.action(re.compile("(approve_button|deny_button)"))
def on_decision(ack, action, body, client, logger):
    ack()  # must be within 3 seconds
    doc_id = action.get("value") or ""
    user_id = body["user"]["id"]
    channel_id = body["channel"]["id"]
    ts = body["message"]["ts"]
    verdict = "approved" if action["action_id"] == "approve_button" else "rejected"

    decision = _rebuild(doc_id)
    if decision is None:
        client.chat_postMessage(
            channel=channel_id, thread_ts=ts,
            text=f"I no longer have a record for {doc_id}. Re-upload the document.",
        )
        return

    if not decision.approvable:
        # Defence in depth: the button was never rendered, but never trust that.
        client.chat_postMessage(
            channel=channel_id, thread_ts=ts,
            text="This one is blocked and cannot be approved here. Verify out of band first.",
        )
        return

    _, note = record.append(decision, verdict, user_id)

    # Learn the vendor's bank details only once a human has accepted them. This is
    # what arms the bank-change check for every future invoice from this vendor.
    if verdict == "approved" and decision.document.iban:
        store.remember_iban(decision.document.vendor, decision.document.iban)

    client.chat_update(
        channel=channel_id, ts=ts,
        text=f"{verdict.capitalize()} by <@{user_id}>",
        blocks=present.decided_blocks(decision, verdict, user_id, _now()),
    )
    client.chat_postMessage(channel=channel_id, thread_ts=ts, text=note.capitalize() + ".")


@app.action("why_button")
def on_why(ack, action, body, client, logger):
    ack()
    doc_id = action.get("value") or ""
    row = store.load_document(doc_id)
    channel_id = body["channel"]["id"]
    ts = body["message"]["ts"]
    if not row:
        client.chat_postMessage(channel=channel_id, thread_ts=ts,
                               text=f"No record for {doc_id}.")
        return
    client.chat_postMessage(
        channel=channel_id,
        thread_ts=ts,
        text=present.trail_text(row, store.load_findings(doc_id), store.approvals_for(doc_id)),
    )


if __name__ == "__main__":
    missing = [n for n, v in (
        ("SLACK_BOT_TOKEN", config.SLACK_BOT_TOKEN),
        ("SLACK_APP_TOKEN", config.SLACK_APP_TOKEN),
        ("OPENROUTER_API_KEY", config.OPENROUTER_API_KEY),
    ) if not v]
    if missing:
        raise SystemExit(
            "Missing environment variables: " + ", ".join(missing) +
            "\nCopy env.sample to .env and fill it in. See STACK.md section 1."
        )

    store.init()
    record.ensure_headers()
    log.info("Ameen is listening. Invite the bot to #%s if you have not already.",
             config.CHANNEL_NAME)
    SocketModeHandler(app, config.SLACK_APP_TOKEN).start()
