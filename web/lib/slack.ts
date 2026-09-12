// Reading the approval queue straight out of the Slack channel.
//
// There is no database. Ameen attaches the full structured decision to its
// Slack message as machine-readable metadata, so the channel already holds the
// record, the evidence and the audit trail. This module just reads it back.

export type Finding = {
  code: string;
  severity: "BLOCKING" | "HIGH" | "MEDIUM" | "LOW" | "INFO";
  title: string;
  detail: string;
  evidence_url?: string;
};

export type Commitment = {
  text: string;
  amount: number;
  currency: string;
  permalink: string;
};

export type Record = {
  doc_id: string;
  track: string;
  vendor: string;
  reference: string;
  doc_date: string;
  currency: string;
  total: number;
  payment_terms?: string;
  po_reference?: string;
  trn?: string;
  iban_masked?: string;
  level: number;
  level_label: string;
  approvable: boolean;
  reason: string;
  findings: Finding[];
  commitment: Commitment | null;
  decision?: string;
  approver?: string;
  decided_at?: string;
  // added on read
  ts: string;
  permalink?: string;
};

const API = "https://slack.com/api";

function token(): string {
  const t = process.env.SLACK_BOT_TOKEN;
  if (!t) throw new Error("SLACK_BOT_TOKEN is not set");
  return t;
}

function channel(): string {
  const c = process.env.AMEEN_CHANNEL_ID;
  if (!c) throw new Error("AMEEN_CHANNEL_ID is not set");
  return c;
}

async function slack(method: string, params: Record2 = {}, post = false) {
  const url = post ? `${API}/${method}` : `${API}/${method}?${new URLSearchParams(params as any)}`;
  const res = await fetch(url, {
    method: post ? "POST" : "GET",
    headers: {
      Authorization: `Bearer ${token()}`,
      "Content-Type": post
        ? "application/json; charset=utf-8"
        : "application/x-www-form-urlencoded",
    },
    body: post ? JSON.stringify(params) : undefined,
    cache: "no-store",
  });
  const json = await res.json();
  if (!json.ok) throw new Error(`slack ${method}: ${json.error}`);
  return json;
}

type Record2 = { [k: string]: unknown };

export async function listRecords(): Promise<Record[]> {
  const res = await slack("conversations.history", {
    channel: channel(),
    limit: "100",
    include_all_metadata: "true",
  });

  const out: Record[] = [];
  for (const m of res.messages ?? []) {
    const meta = m.metadata;
    if (!meta || meta.event_type !== "ameen_decision") continue;
    const raw = meta.event_payload?.record;
    if (!raw) continue;
    try {
      const rec = JSON.parse(raw) as Record;
      rec.ts = m.ts;
      out.push(rec);
    } catch {
      // A malformed record must not take the whole queue down.
    }
  }
  // Newest first.
  return out.sort((a, b) => Number(b.ts) - Number(a.ts));
}

export async function decide(ts: string, verdict: "approved" | "rejected", approver: string) {
  const records = await listRecords();
  const rec = records.find((r) => r.ts === ts);
  if (!rec) throw new Error("no record for that message");
  if (!rec.approvable) throw new Error("this document is blocked and cannot be approved");

  const decided_at = new Date().toISOString().replace("T", " ").slice(0, 16) + " UTC";
  const updated = { ...rec, decision: verdict, approver, decided_at };
  delete (updated as any).ts;

  const verb = verdict === "approved" ? "Approved" : "Rejected";
  await slack(
    "chat.update",
    {
      channel: channel(),
      ts,
      text: `${verb} by ${approver} in the dashboard`,
      blocks: [
        {
          type: "section",
          text: {
            type: "mrkdwn",
            text:
              `*${verb}* by ${approver} at ${decided_at}, from the Ameen dashboard\n` +
              `${rec.vendor} - ${rec.currency} ${rec.total.toLocaleString()} (${rec.reference || "no reference"})`,
          },
        },
        {
          type: "context",
          elements: [{ type: "mrkdwn", text: `${rec.level_label} - ${rec.reason}` }],
        },
      ],
      metadata: {
        event_type: "ameen_decision",
        event_payload: { record: JSON.stringify(updated) },
      },
    },
    true,
  );

  return updated;
}
