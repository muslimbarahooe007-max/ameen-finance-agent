// Vendor intelligence, computed from what is already in the channel.
//
// Every decision Ameen has ever posted lives in #ap-review as message metadata.
// Group those by vendor and you get a history: how much you have been invoiced,
// how often the price drifted from what was agreed, and which bank accounts
// have ever been used. No warehouse, no sync, no second source of truth.

import type { Record as Rec } from "./slack";

export type VendorIntel = {
  vendor: string;
  documents: number;
  invoiced: number;
  currency: string;
  overCharged: number; // total billed above what was agreed
  timesOver: number;
  accounts: string[]; // distinct paying accounts ever seen
  firstSeen?: string;
  lastSeen?: string;
};

export function vendorIntel(records: Rec[], vendor: string): VendorIntel {
  const mine = records.filter(
    (r) => (r.vendor || "").toLowerCase() === (vendor || "").toLowerCase(),
  );

  let overCharged = 0;
  let timesOver = 0;
  const accounts: string[] = [];

  for (const r of mine) {
    const c = r.commitment;
    if (c && r.total > c.amount) {
      overCharged += r.total - c.amount;
      timesOver += 1;
    }
    const acct = r.iban_masked;
    if (acct && !accounts.includes(acct)) accounts.push(acct);
  }

  const dates = mine.map((r) => r.doc_date).filter(Boolean).sort();

  return {
    vendor,
    documents: mine.length,
    invoiced: mine.reduce((s, r) => s + r.total, 0),
    currency: mine[0]?.currency ?? "AED",
    overCharged,
    timesOver,
    accounts,
    firstSeen: dates[0],
    lastSeen: dates[dates.length - 1],
  };
}

export type Activity = {
  reviewed: number;
  escalated: number;
  blocked: number;
  autoApproved: number;
  caught: number; // money stopped above what was agreed, across everything seen
};

export function activity(records: Rec[]): Activity {
  return {
    reviewed: records.length,
    escalated: records.filter((r) => r.level >= 2 && r.approvable).length,
    blocked: records.filter((r) => !r.approvable).length,
    autoApproved: records.filter((r) => r.level === 0).length,
    caught: records.reduce((s, r) => {
      const c = r.commitment;
      return s + (c && r.total > c.amount ? r.total - c.amount : 0);
    }, 0),
  };
}
