# How to demo Ameen

Everything below has been run end to end against the live Slack workspace and
the deployed dashboard. Nothing here is aspirational.

---

## Before you start

**1. Start the agent in your own terminal** and leave it running:

```bash
cd ~/aitinkerers-abudhabi-2026/team-b-ameen
./run-ameen.sh
```

Wait for `⚡️ Bolt app is running!`. That process must stay up for the whole
demo — it is what receives the uploads from Slack.

**2. Start the dashboard** in a second terminal:

```bash
cd ~/aitinkerers-abudhabi-2026/team-b-ameen/web
SLACK_BOT_TOKEN=... AMEEN_CHANNEL_ID=C0C27PKC3RN npx next dev -p 3000
```

Or just use the deployed one, which needs no terminal:
`https://ameen-2oe89m6l7-muslimbarahooe007-maxs-projects.vercel.app`

**3. Reset the channel** so the demo starts clean. Delete Ameen's previous
cards from `#ap-review`, but **keep the two commitment messages** — they are the
fixture the whole demo depends on:

> Spoke to Gulf Supplies — they have agreed AED 40,000 for the 12 units, net 30.
>
> Raised PO-1043 for Gulf Supplies at AED 40,000.

**4. Have the three documents ready to drag** from `demo/`:
`invoice-1-overcharge.png`, `invoice-2-bank-change.png`, `receipt-taxi.png`.

**5. Screen layout:** Slack on the left, the dashboard on the right, side by
side. The whole point is that both move at once.

---

## The two-minute script

Say these words. Do not improvise at 15:50.

### 0:00–0:15 — the setup, not the product

Scroll `#ap-review` to the two commitment messages.

> "Three weeks ago someone on this team agreed a price with a vendor, in a Slack
> thread. That is where finance disputes are born: what was agreed lives in a
> conversation, what gets invoiced arrives as a document, and nothing connects
> the two."

### 0:15–0:25 — the invoice arrives

Drag `invoice-1-overcharge.png` into `#ap-review`.

> "The invoice arrives."

### 0:25–0:55 — the moment that matters

Ameen replies with a card. Point at the citation and click the link; Slack jumps
to the original message.

> "Ameen was already in the channel when the promise was made. So it says: this
> invoice is fifteen percent above what was agreed here — and here is the exact
> message. It also does not match PO-1043. The finding changed who has to
> approve it: this is now dual approval, not a manager."

**This is where the project is won. Do not rush it.**

### 0:55–1:20 — it is a product, not a bot

Switch to the dashboard. The row is already there.

> "Everything Ameen sees lands in the approval queue. Agreed, forty thousand.
> Invoiced, forty-six. Fifteen percent over, with the promise quoted underneath
> and a link back to the message."

Worth saying out loud, because judges notice architecture:

> "There is no database behind this. Ameen attaches the whole structured record
> to its own Slack message as metadata, so the channel is the store, the
> evidence and the audit trail. The dashboard just reads it back."

### 1:20–1:40 — the one that must not be approved

Drag in `invoice-2-bank-change.png`. Correct price this time. Different bank
account.

> "This one is the right amount, but it pays a different bank account from the
> last invoice from this vendor. That is the most expensive fraud in corporate
> finance. There is no Approve button. We removed it, because the button is what
> gets finance teams defrauded. Verify by phone first."

Show the row on the dashboard: it is held, and there is no approve control there
either.

### 1:40–1:55 — close the loop

Go back to the first row and click **Approve** on the dashboard. Switch to Slack:
the card has updated in place.

> "Approve it here, and the Slack card updates in place. One record, two
> surfaces."

### 1:55–2:00 — the line to end on

> "Nobody left the tools they were already in. The agent lives in the channel
> where the promise was made, which is the only place this check can be made at
> all."

---

## If something goes wrong mid-recording

- **No card appears.** The agent process has died. Restart `./run-ameen.sh`.
  Check the terminal shows `Bolt app is running`.
- **The card appears but finds no commitment.** The two fixture messages were
  deleted, or the vendor name in the message no longer matches the invoice.
- **The dashboard is empty.** It reads the last 100 messages of the channel;
  make sure `AMEEN_CHANNEL_ID` is `C0C27PKC3RN`.
- **The bank-change invoice is not blocked.** The vendor's previous bank details
  have to be on file first. Approve invoice 1 before uploading invoice 2, or run
  `python -c "from ameen import store; store.init(); store.seed_vendor('Gulf Supplies LLC','AE070331234567890123456')"`.
- **Nothing works at all.** `python selftest.py` proves the logic offline with no
  Slack and no model call. It is a legitimate fallback to show on camera.

---

## What to say if a judge asks "is this not just OCR?"

Two answers, in this order:

1. **It routes, it does not just read.** Upload a delivery note and a safety
   checklist and the same agent sends them to different places. Here, a finding
   changed the approval level from manager to dual approval without anyone
   configuring a rule.
2. **It cites a conversation that happened before the document existed.** No
   scanner can do that, because the information is not on the page. It is in the
   channel, and the agent was there.

## What to say if asked what is not built

Be straight about it; it scores better than bluffing.

> "Email ingestion is designed as a second source adapter and not built today.
> Contracts-as-policy slots into the check registry as one more function. The
> approval ladder computes levels but does not resolve approver identity against
> a directory yet. Everything demoed is real."
