# Demo documents

Drag the PNGs into the Slack channel. They are rendered from the HTML beside
them, so you can edit any figure and re-render.

| File | Amount | What it triggers |
|---|---|---|
| `invoice-1-overcharge.png` | **AED 46,000** | Contradicts the AED 40,000 agreed in the channel, and PO-1043. Escalates to dual approval and cites the message. |
| `invoice-2-bank-change.png` | AED 40,000 | Correct price, **different IBAN**. BLOCKED, no Approve button. |
| `receipt-taxi.png` | AED 100.80 | Personal reimbursement track. Auto-approved within policy. Upload twice to show duplicate detection. |

Post this in the channel first, so Ameen has a commitment to find and cite:

> Spoke to Gulf Supplies - they have agreed AED 40,000 for the 12 units, net 30.

And, a little later:

> Raised PO-1043 for Gulf Supplies at AED 40,000.

Re-render after editing:

    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless \
      --disable-gpu --hide-scrollbars --window-size=900,700 \
      --screenshot="$PWD/invoice-1-overcharge.png" "file://$PWD/invoice-1-overcharge.html"

All figures, vendors and bank details are invented for this demo.
