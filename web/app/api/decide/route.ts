import { NextResponse } from "next/server";
import { decide } from "@/lib/slack";

export const dynamic = "force-dynamic";

export async function POST(req: Request) {
  try {
    const { ts, verdict, approver } = await req.json();
    if (!ts || (verdict !== "approved" && verdict !== "rejected")) {
      return NextResponse.json({ ok: false, error: "ts and verdict are required" }, { status: 400 });
    }
    const record = await decide(ts, verdict, approver || "dashboard");
    return NextResponse.json({ ok: true, record });
  } catch (err: any) {
    return NextResponse.json({ ok: false, error: String(err?.message ?? err) }, { status: 400 });
  }
}
