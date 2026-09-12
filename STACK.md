# STACK — verified against current docs, 12 Sep 2026
### Copy-paste this. Do not write Slack or Sheets code from memory.

Everything below was pulled from live docs today. Items marked **UNCONFIRMED** are
flagged so you do not bet the build on them.

---

## 0. Install

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install slack_bolt slack_sdk requests gspread imap-tools openai python-dotenv
```

`slack-bolt` latest is **1.28.0**, `gspread` **6.2.1** (both WebSearch-confirmed,
not doc-confirmed — run `pip show slack_bolt gspread` after install and move on).

---

## 1. Slack app setup — the exact click path, ~5 to 10 minutes

Do these in order. Skipping step 6 is the classic wasted-20-minutes mistake.

1. **api.slack.com/apps → Create New App → From scratch.** Pick your workspace.
2. **Socket Mode → Enable Socket Mode.** This prompts you to create an
   **app-level token**; give it the scope **`connections:write`**. Copy the
   `xapp-…` token. This is *not* your bot token.
3. **Event Subscriptions → toggle ON.** Confirmed: Socket Mode **still requires
   Event Subscriptions to be enabled**, but **no Request URL field appears** and
   none is needed. Under *Subscribe to bot events* add:
   - `message.channels`
   - `file_shared`
4. **OAuth & Permissions → Bot Token Scopes**, add exactly these:

   | Scope | Why |
   |---|---|
   | `chat:write` | post messages and update them |
   | `channels:history` | **read channel history — this is the innovation** |
   | `channels:read` | resolve channel ids |
   | `files:read` | file metadata *and* downloading the bytes |
   | `groups:history` | only if the channel is private |
   | `im:history` | only if you want DM uploads |

5. **Install to Workspace.** Copy the `xoxb-…` bot token.
6. **Invite the bot into the channel:** `/invite @ameen` in `#ap-review`.
   It receives nothing at all until you do this.

```bash
# .env
SLACK_BOT_TOKEN=xoxb-...      # from OAuth & Permissions
SLACK_APP_TOKEN=xapp-...      # from Basic Information → App-Level Tokens
```

**No signing secret is needed with Socket Mode.**

---

## 2. Minimal app that runs

```python
import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

app = App(token=os.environ["SLACK_BOT_TOKEN"])   # no signing_secret in Socket Mode

@app.event("message")
def on_message(body, logger):
    logger.info(body)

if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
```

If this prints events when you type in the channel, the hard part of Slack is
done. **Do not proceed past this until it does.**

---

## 3. Receiving an uploaded invoice and downloading the bytes

**Critical gotcha: the `file_shared` event does not contain the file.** It carries
only an id. You must call `files_info` to get a download URL.

```json
{ "event": { "type": "file_shared", "channel_id": "C0…",
             "file_id": "F2147483862", "user_id": "U0…" } }
```

```python
import os, requests

@app.event("file_shared")
def on_file(event, client, logger):
    info = client.files_info(file=event["file_id"])
    url = info["file"]["url_private_download"]
    r = requests.get(url, headers={"Authorization": f"Bearer {os.environ['SLACK_BOT_TOKEN']}"})
    file_bytes = r.content          # the invoice document or image
```

- `url_private` / `url_private_download` **require** the `Authorization: Bearer`
  header and the `files:read` scope. Without the header you silently get an HTML
  login page rather than an error, which is a confusing ten minutes if you hit it.
- `url` and `url_download` are **deprecated** — do not use them.
- A file upload also arrives as a `message` event with `subtype: file_share`.
  Subscribing to both events is fine; just guard against handling it twice.
- **UNCONFIRMED:** no evidence of a new 2026 file-access model. The only relevant
  2025 deprecation was `files.upload` (now `files.getUploadURLExternal`), which
  affects uploading, not downloading.

---

## 4. Approval card, and updating it in place

```python
client.chat_postMessage(
    channel=channel_id,
    text="Approval request",                      # fallback for notifications
    blocks=[
        {"type": "section", "text": {"type": "mrkdwn", "text": summary_mrkdwn}},
        {"type": "actions", "elements": [
            {"type": "button", "text": {"type": "plain_text", "text": "Approve"},
             "style": "primary", "action_id": "approve_button", "value": doc_id},
            {"type": "button", "text": {"type": "plain_text", "text": "Reject"},
             "style": "danger", "action_id": "deny_button", "value": doc_id},
        ]},
    ],
)
```

```python
import re

@app.action(re.compile("(approve_button|deny_button)"))
def on_decision(ack, action, body, client, logger):
    ack()                                    # MUST be within 3 seconds
    decision = "approved" if action["action_id"] == "approve_button" else "rejected"
    client.chat_update(
        channel=body["channel"]["id"],
        ts=body["message"]["ts"],
        text=f"Request {decision} by <@{body['user']['id']}>",
        blocks=[],                            # clears buttons so it cannot be double-clicked
    )
```

`ack()` within three seconds or Slack shows the user an error. Call it first, then
do the work. `respond(replace_original=True, …)` is a simpler alternative to
`chat_update`, but only works inside that one action invocation.

**For the BLOCKED state, simply do not render the actions block.** That is the
bank-detail-change design decision, and it is three lines of code.

---

## 5. The innovation: find the commitment and cite it

```python
# read the channel's history
res = client.conversations_history(channel=channel_id, limit=200)
messages = res["messages"]
while res.get("has_more"):                       # cursor pagination
    res = client.conversations_history(
        channel=channel_id, limit=200,
        cursor=res["response_metadata"]["next_cursor"])
    messages += res["messages"]

# cite the exact message the agent is relying on
permalink = client.chat_getPermalink(
    channel=channel_id, message_ts=msg["ts"])["permalink"]
# -> https://workspace.slack.com/archives/C123ABC456/p1678886400123456
```

- Needs `channels:history`. `chat.getPermalink` needs no extra scope.
- `limit` max is 999, default 100. Check `has_more`, pass `next_cursor`.
- `conversations_replies(channel=…, ts=thread_ts)` for a single thread.

**The permalink is the whole project.** A discrepancy without a link to the
original message is arithmetic; with the link it is memory.

**Demo determinism:** for today, filter candidate messages by vendor name and a
date window rather than doing anything clever. Determinism beats cleverness at
14:40.

---

## 6. Google Sheets — service account, no consent screen

1. Google Cloud Console → **enable the Sheets API and the Drive API**.
2. Create a **Service Account** → create a **JSON key** → download it.
3. Open the JSON, copy `client_email`.
4. **Share the Google Sheet with that `client_email`**, exactly as you would share
   with a person, with edit access. **Skip this and you get `SpreadsheetNotFound`,
   which looks like an auth bug and is not.**

```python
import gspread
gc = gspread.service_account(filename="service_account.json")
ws = gc.open_by_key(SHEET_ID).sheet1        # open_by_key is safer than open(name)
ws.append_row(["2026-09-12", "INV-2291", "Gulf Supplies", 46000, "AED", "BLOCKED"])
```

No 2026 changes to this flow. Service-account auth bypasses the OAuth consent
screen entirely, and is unaffected by Google's app-password tightening, which is a
Gmail-only policy area.

---

## 7. Email ingestion — IMAP, and check one thing first

**Check this before committing:** app passwords still exist in 2026 but
**require 2-Step Verification to already be enabled** on the account, and are
disabled entirely under Advanced Protection and by some Workspace admin policies.
If the account cannot issue one, IMAP is out and you are forced onto full OAuth —
which is exactly why email is a stretch goal today, not core scope.

Create the app password at `myaccount.google.com/apppasswords`.

```python
from imap_tools import MailBox, AND

with MailBox("imap.gmail.com").login(USER, APP_PASSWORD) as mb:
    for msg in mb.fetch(AND(seen=False)):
        for att in msg.attachments:
            if att.filename.lower().endswith((".pdf", ".png", ".jpg")):
                doc_bytes = att.payload
```

IMAP is always-on for personal Gmail now (Google removed the toggle).
Basic-password IMAP for Workspace accounts was cut off in 2025; app passwords
remain the supported path.

**Do not use the Gmail API with a service account for a personal @gmail.com
inbox.** Domain-wide delegation only works on Workspace domains with an explicit
admin delegation; a personal account cannot be impersonated and the call fails
with `admin_policy_enforced`. That road is a dead end, and it is a tempting one.

---

## 8. SaaS path — what turning this into a product actually takes

Confirmed, and genuinely additive rather than a rewrite:

- A new app lives in **one workspace** only. Multi-workspace means implementing the
  **OAuth 2.0 install flow** (`oauth.v2.access`) and storing **one bot token per
  installing workspace** instead of one from `.env`. That is the only
  architectural change.
- **Public distribution** is a separate toggle on the Manage Distribution page,
  giving you an "Add to Slack" link any workspace can use.
- **App Directory listing** is separate again and requires a formal Slack review:
  security review, privacy policy, support contact. Slow. Do not attempt today.
- A single-workspace Socket Mode app **converts later with no rewrite** — add
  multi-tenant token storage, flip public distribution, submit for review if you
  want the listing.

The honest pitch line: *"single workspace today, OAuth multi-tenant is a follow-on
task, Marketplace listing after that."*

---

## 9. The five things that waste the most time

1. **Forgetting to `/invite` the bot into the channel.** It receives nothing.
2. **Fetching `url_private` without the `Authorization` header** — you get an HTML
   login page rather than a 401, so it reads as a parsing bug.
3. **Not sharing the Sheet with the service account email** — looks like an auth
   failure, is actually a permissions one.
4. **Missing `channels:history`** — the history call errors and the entire
   innovation silently does nothing.
5. **Changing scopes without reinstalling the app.** Scope changes do not take
   effect until you reinstall to the workspace.
