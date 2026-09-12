import { NextResponse } from "next/server";
import { listRecords } from "@/lib/slack";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export async function GET() {
  try {
    const records = await listRecords();
    return NextResponse.json({ ok: true, records });
  } catch (err: any) {
    // Surface the real reason rather than an empty table that looks like
    // "nothing to approve".
    return NextResponse.json(
      { ok: false, error: String(err?.message ?? err), records: [] },
      { status: 500 },
    );
  }
}
