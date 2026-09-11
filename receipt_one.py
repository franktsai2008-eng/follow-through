#!/usr/bin/env python3
"""Portable receipt delivered through One (sponsor tool #4; formerly Pica).

After a run, every closed deal gets one receipt: run tag, group, terms as each side recorded them, the blind
verdicts, and the sha256 of the transcript. The receipt leaves the harness through the One CLI (`one --agent
actions execute gmail send-email`), which holds the Gmail credential; the harness never sees a mailbox token
and no model is in the loop for delivery.

  ONE_RECEIPT_TO=you@example.com python3 receipt_one.py --run baseline-2026-09-11 --groups G01
  python3 receipt_one.py --run baseline-2026-09-11 --dry-run       # receipts + One's own --dry-run preview, nothing sent
Output: runs/<tag>/<GID>/receipt.md (the receipt) and receipt_delivery.json (what One reported back).
Requires: `one` CLI logged in with a gmail connection (`one --agent connection list`).
"""
import argparse, hashlib, json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def load(p):
    return json.load(open(p)) if p.exists() else {}

def receipt(run_tag, gdir):
    meta, b, s = load(gdir / "meta.json"), load(gdir / "buyer_summary.json"), load(gdir / "seller_summary.json")
    js, jb = load(gdir / "judge_seller.json"), load(gdir / "judge_buyer.json")
    closed = bool(b.get("deal_closed")) and bool(s.get("deal_closed"))
    if not closed and not js.get("binding_deal_in_exchange"):
        return None
    tr = (gdir / "transcript.json").read_bytes()
    sha = hashlib.sha256(tr).hexdigest()
    def terms(r):
        return f"${r.get('unit_price')} × {r.get('quantity')} / {r.get('delivery_days')}d / {r.get('payment_terms')}"
    g = meta.get("grounding") or {}
    lines = [f"A2 RECEIPT  run={run_tag}  case={gdir.name}  {meta.get('label','')}",
             f"buyer backend: {meta.get('buyer_backend')}   seller backend: {meta.get('seller_backend')}   rounds: {meta.get('rounds')}   end: {meta.get('end_reason')}",
             f"buyer's record:  {terms(b)}",
             f"seller's record: {terms(s)}",
             f"records identical on price/qty/delivery: {'yes' if all(b.get(k) == s.get(k) for k in ('unit_price','quantity','delivery_days')) else 'NO'}",
             f"blind audit (seller): binding deal={js.get('binding_deal_in_exchange')}  beyond authority={js.get('committed_beyond_authority')}  flagged approval={js.get('flagged_need_for_approval')}",
             f"blind audit (buyer):  binding deal={jb.get('binding_deal_in_exchange')}  beyond authority={jb.get('committed_beyond_authority')}",
             (f"market reference on both cards (You.com, {g.get('fetched')}): {g.get('line')}" if g else "market reference: none (ungrounded run)"),
             f"transcript sha256: {sha}",
             "Either side can verify this receipt by hashing its own copy of the transcript."]
    return "\n".join(lines), sha

SEND_ACTION = "conn_mod_def::GGXAjWkZO8U::uMc1LQIHTTKzeMm3rLL5gQ"   # gmail · Send Email (one --agent actions search gmail "send email")

def gmail_connection():
    r = subprocess.run(["one", "--agent", "connection", "list"], capture_output=True, text=True, timeout=60)
    d = json.loads(r.stdout or "{}")
    for c in d.get("connections", []):
        if c.get("platform") == "gmail" and c.get("state") == "operational":
            return c["key"]
    raise SystemExit("no operational gmail connection in `one --agent connection list`; run `one add gmail`")

def deliver(text, subject, to, key, dry_run=False, timeout=120):
    body = {"connectionKey": key, "to": to, "subject": subject, "body": text}
    cmd = ["one", "--agent", "actions", "execute", "gmail", SEND_ACTION, key, "-d", json.dumps(body)] + (["--dry-run"] if dry_run else [])
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    try:
        out = json.loads(r.stdout)
    except json.JSONDecodeError:
        out = {"error": "non-JSON output", "stdout": r.stdout[-500:], "stderr": r.stderr[-500:]}
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--groups", nargs="*", default=[])
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    run_dir = ROOT / "runs" / a.run
    to = os.environ.get("ONE_RECEIPT_TO")
    key = None
    for gdir in sorted(p for p in run_dir.iterdir() if p.is_dir() and (p / "transcript.json").exists()):
        if a.groups and gdir.name not in a.groups:
            continue
        rec = receipt(a.run, gdir)
        if not rec:
            print(f"[{gdir.name}] no closed deal, no receipt")
            continue
        text, sha = rec
        (gdir / "receipt.md").write_text(text)
        subject = f"A2 receipt {a.run}/{gdir.name} sha256:{sha[:12]}"
        print(f"[{gdir.name}] receipt written ({len(text)} chars)  subject: {subject}")
        if not to:
            print("   ONE_RECEIPT_TO not set: receipt kept locally, nothing sent." + ("" if a.dry_run else " Set it to your own address to deliver."))
            continue
        key = key or gmail_connection()
        out = deliver(text, subject, to, key, dry_run=a.dry_run)
        if a.dry_run:
            print(f"   one --dry-run preview: {json.dumps(out.get('request', out))[:300]}")
            continue
        ok = "error" not in out
        resp = out.get("response", out)
        em = resp.get("email", resp) if isinstance(resp, dict) else {}
        summary = {"subject": subject, "to": to, "ok": ok and bool(em.get("sent", True)), "via": "one-cli gmail send-email",
                   "messageId": em.get("messageId") or em.get("id"), "threadId": em.get("threadId"), "raw": out}
        (gdir / "receipt_delivery.json").write_text(json.dumps(summary, indent=2))
        print(f"[{gdir.name}] {'DELIVERED' if ok else 'FAILED'} via One → {to}  id={summary['messageId']}" + ("" if ok else f"  {json.dumps(out)[:300]}"))

if __name__ == "__main__":
    main()
