# Ameen — the finance agent that remembers what was promised

Ameen is a Slack agent for accounts payable, with a web approval queue. It lives
in the channel where your team agrees things with vendors, so when the invoice
arrives weeks later it already knows what was promised — and it cites the exact
message.

**Live dashboard:** https://ameen-2oe89m6l7-muslimbarahooe007-maxs-projects.vercel.app
**Demo script:** [DEMO.md](DEMO.md) · **Setup and API notes:** [STACK.md](STACK.md)

*Ameen* (أمين) means trustworthy. *Amīn al-sundūq* is the Arabic for treasurer.

---

## The one idea

Finance disputes are almost never arithmetic errors. They happen because **the
commitment and the invoice live in different universes.** The price is agreed in a
Slack thread on a Tuesday. The purchase order is raised a week later. The invoice
arrives three weeks after that. Nobody checks the conversation, because a
conversation is not data and nobody remembers which thread it was in.

Ameen was in the channel when the promise was made. So it says:

> **[HIGH] Contradicts what was agreed in this channel**
> Invoice is AED 46,000.00, which is 15% above the AED 40,000.00 agreed here.
> The message said: "Spoke to Gulf Supplies — they have agreed AED 40,000 for the
> 12 units, net 30."
> [See the original message]
>
> **Routing:** L3 dual approval
> *AED 46,000 sits at L2 finance approval; escalated one level: contradicts what
> was agreed in this channel*

**A chat window cannot do this.** It would need a human to remember the
conversation happened, find it, and paste it in — and anyone who could do that
would not need the agent. The value is that it was already in the room.

### And when the bank account changes, it removes the button

The most expensive fraud in corporate finance is invoice redirection: a real-looking
invoice arrives with a changed IBAN. Ameen holds each vendor's bank history, and
when it changes it does **not** put a warning next to an Approve button.

It renders no Approve button at all.

> **[BLOCKING] Vendor bank details have changed**
> This invoice pays AE9998...1100. The last invoice from Gulf Supplies LLC paid
> AE0703...3456. Verify by phone, on a number you already hold, before anyone
> approves this. No approval button has been offered.

The button is what gets finance teams defrauded.

---

## The approval queue, and why there is no database

Drop an invoice in Slack and it appears in a live web queue where finance can
approve or reject it. Approving there updates the Slack card in place.

There is **no database**. Ameen attaches the whole structured decision to its own
Slack message as machine-readable metadata, so the channel already holds the
record, the evidence and the audit trail in one place. The dashboard reads it
straight back out with `conversations.history` and writes decisions back with
`chat.update`.

That is the same claim the product makes about commitments, applied to its own
storage: the channel is the system of record.

The dashboard is laid out as a ledger rather than a card grid, because the thing
a controller needs to see is a confrontation between two numbers — what was
agreed, and what was invoiced — with the promise quoted underneath and a link to
the message it came from.

## Run it

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp env.sample .env          # two Slack tokens and an OpenRouter key
python app.py
```

It runs in **Socket Mode**, so there is no public URL, no tunnel and no deploy.
Slack app setup is five to ten minutes; the exact click path, the required scopes
and the five things that waste the most time are in [STACK.md](STACK.md).

### The dashboard

```bash
cd web
npm install
SLACK_BOT_TOKEN=xoxb-... AMEEN_CHANNEL_ID=C0... npx next dev
```

Deployed on Vercel with the same two environment variables. No other services.

### Prove it works without any tokens

```bash
python selftest.py
```

Runs the whole pipeline against fixture documents and fixture channel history,
with no Slack and no model call, and asserts the behaviours that matter:

```
PASSED: 7 checks - citation, blocking, routing, duplicate,
        learn-then-police bank details, trail
```

1. an invoice above the agreed price is caught **and cites the message**
2. a changed bank account is BLOCKED and **offers no approval button**
3. a clean invoice is not over-escalated
4. the same invoice twice is detected as a duplicate
5. a new vendor's bank details are learned only on approval, then policed
6. the decision trail renders every finding with its evidence

---

## Architecture

One path, whatever the source and whatever the document.

```
ingest ──▶ extract ──▶ memory ──▶ checks ──▶ route ──▶ present ──▶ record
  │           │           │          │          │         │          │
  │           │           │          │          │         │          └─ SQLite + Google Sheet
  │           │           │          │          │         └─ Block Kit card; no button if blocked
  │           │           │          │          └─ findings ▸ approval level
  │           │           │          └─ check registry: one function per rule
  │           │           └─ channel history ▸ commitments ▸ permalinks
  │           └─ vision model via OpenRouter, with per-field confidence
  └─ source adapters: Slack upload today, IMAP next
```

| Module | Responsibility |
|---|---|
| `ameen/sources/slack_source.py` | download the file, read channel history, build permalinks |
| `ameen/extract.py` | document to fields, **with per-field confidence** |
| `ameen/memory.py` | find what was promised in the channel. Never touches Slack, so it is testable offline |
| `ameen/checks.py` | the check registry. One function per rule |
| `ameen/route.py` | findings to approval level |
| `ameen/present.py` | Block Kit rendering, including the absent button |
| `ameen/record.py` | the tracker. Degrades to local-only rather than failing |
| `ameen/store.py` | SQLite. Bank history and duplicates need memory |
| `ameen/wire.py` | the decision as Slack message metadata — the shared record |
| `web/lib/slack.ts` | reads the queue out of the channel, writes decisions back |
| `web/app/page.tsx` | the approval ledger |

Two decisions make the rest cheap. **Sources are adapters**, so email ingestion is
a second adapter and changes nothing downstream. **Checks are a registry**, so
contract-derived policy is a new function, not a refactor. A personal
reimbursement is the same pipeline with different checks, not a second system.

### Failure handling

Illegibility and fraud are the normal cases here, not the exceptions.

- **Low extraction confidence asks a question in-thread** rather than guessing. A
  finance agent that silently returns its best guess about a number is worse than
  one that returns nothing.
- **A blocking finding removes the Approve button**, and the handler rejects an
  approval anyway if one is ever synthesised.
- **A blocked document is never written to the tracker.**
- **A failing check cannot swallow the document** — it degrades to a LOW finding
  naming the check that broke.
- **The file download retries, and detects Slack's HTML sign-in page**, which is
  returned with HTTP 200 when the token lacks `files:read` and otherwise reads as
  a parsing bug.
- **Duplicate ingestion is guarded**: one upload arrives as both `file_shared` and
  `message`/`file_share`, and is handled once.
- **The tracker degrades rather than failing**: if the sheet is unreachable the
  approval still happens, is still persisted, and the channel is told the row did
  not land.

---

## The compliance checks

| Check | Severity | Effect |
|---|---|---|
| Invoice contradicts the channel commitment | HIGH | escalates one level, cites the message |
| Vendor bank details changed | BLOCKING | no approval button, nothing written |
| Invoice does not match the purchase order | MEDIUM | escalates one level, cites the PO message |
| Duplicate document | HIGH | escalates one level |
| Fields could not be read | MEDIUM | asks in-thread instead of guessing |
| No UAE Tax Registration Number | LOW | flagged; finance rejects these at payment |

**Approval levels:** L0 auto, L1 manager, L2 finance, L3 dual — and BLOCKED, which
is deliberately not an approval level. The rule worth noticing is one line of code:
**any compliance flag escalates the item exactly one level.** A routine claim is
auto-approved; the same claim submitted twice goes to finance.

---

## Built during the hackathon, and what is not built

This repository was initialised on 12 September 2026 and every commit was made
during the event. The commit history is the evidence.

**Built and working**, all verified against the live workspace:
Slack ingest in Socket Mode, file download, vision extraction with per-field
confidence, channel-memory commitment search with permalink citation, six
compliance checks, severity-driven routing, the BLOCKED state, interactive
approvals that update the card in place, the "Why?" decision trail, SQLite
persistence, the Next.js approval dashboard deployed on Vercel reading and
writing through Slack message metadata, a Google Sheets tracker, and an offline
self-test.

**Designed and specified, not built today** — the interfaces exist, the
implementations do not:
- **Email ingestion.** `ameen/sources/` is an adapter directory for exactly this;
  IMAP is adapter two. Verified approach in [STACK.md](STACK.md) section 7.
- **Contracts as policy.** Upload a vendor contract, extract the payment terms and
  caps, and enforce them. It slots into the check registry as one function.
- **The full L0–L3 ladder with real org roles.** Levels are computed; approver
  identity is not yet resolved against a directory.
- **Multi-currency with FX dating.**
- **Multi-workspace SaaS distribution.** Today it holds one bot token. Turning it
  into a product means the OAuth install flow and one token per workspace, which
  is additive rather than a rewrite — see [STACK.md](STACK.md) section 8.

**Building blocks used**, as the rules permit: Slack Bolt, gspread, imap-tools,
pypdf, the OpenAI SDK pointed at OpenRouter.

---

## Limitations, honestly

- Commitment matching is deterministic regex and token matching against the vendor
  name, scoped to one channel and the most recent 1,000 messages. It is built for
  precision over recall: it would rather find nothing than cite the wrong message.
- Extraction quality on a photographed receipt in poor light is the weakest part
  of the system. That is why unreadable fields ask a question rather than guess.
- A real deployment needs a retention policy and consent, because invoices and
  receipts carry other people's personal and banking data. Nothing here should be
  pointed at a production finance channel as it stands.
