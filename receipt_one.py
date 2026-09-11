#!/usr/bin/env python3
"""Portable receipt delivered through One (sponsor tool #4; formerly Pica).

After a run, every closed deal gets one receipt: run tag, group, terms as each side recorded them, the blind
verdicts, and the sha256 of the transcript. The receipt leaves the harness through One's MCP (Gmail, Sheets,
Slack: whatever the account has connected); the harness never holds a mailbox token. Claude Code is the MCP
client (`claude -p` + One's stdio server), so nothing new is installed.

  ONE_SECRET=... ONE_RECEIPT_TO=you@example.com python3 receipt_one.py --run baseline-2026-09-11 --groups G01
  python3 receipt_one.py --run baseline-2026-09-11 --dry-run       # prints receipts + command, no network
Output: runs/<tag>/<GID>/receipt.md (the receipt) and receipt_delivery.json (what One reported back).
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

def deliver(text, subject, to, secret, timeout=300):
    mcp = {"mcpServers": {"one": {"command": "npx", "args": ["-y", "@withone/mcp"], "env": {"ONE_SECRET": secret}}}}
    prompt = (f"Using only the One tools available to you, send an email to {to} with subject \"{subject}\" and this exact plain-text body "
              f"(do not reword it):\n\n{text}\n\nUse Gmail if it is connected; otherwise use whatever messaging platform is connected. "
              f"When done, reply with one line: DELIVERED via <platform>, id <message or thread id>. If it cannot be sent, reply FAILED: <reason>.")
    env = {k: v for k, v in os.environ.items() if k not in ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT")}
    cmd = ["claude", "-p", "--model", "sonnet", "--setting-sources", "", "--strict-mcp-config", "--mcp-config", json.dumps(mcp),
           "--allowedTools", "mcp__one__*", "--no-session-persistence", "--output-format", "text", prompt]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
    return r.stdout.strip(), r.stderr[-500:], cmd

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--groups", nargs="*", default=[])
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    run_dir = ROOT / "runs" / a.run
    secret, to = os.environ.get("ONE_SECRET"), os.environ.get("ONE_RECEIPT_TO")
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
        if a.dry_run:
            print("   " + text.replace("\n", "\n   "))
            print(f"   would send via: claude -p --mcp-config '{{one: npx -y @withone/mcp, ONE_SECRET}}' --allowedTools mcp__one__*  → {to or '<ONE_RECEIPT_TO unset>'}")
            continue
        if not (secret and to):
            sys.exit("ONE_SECRET and ONE_RECEIPT_TO must be set (secret from app.withone.ai → API keys, and connect Gmail there first). Use --dry-run to preview.")
        out, err, _ = deliver(text, subject, to, secret)
        (gdir / "receipt_delivery.json").write_text(json.dumps({"subject": subject, "to": to, "result": out, "stderr": err}, indent=2))
        print(f"[{gdir.name}] {out or 'no output'}{('  stderr: ' + err) if err and not out else ''}")

if __name__ == "__main__":
    main()
