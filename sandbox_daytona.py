#!/usr/bin/env python3
"""Replay the audit in a Daytona sandbox (sponsor tool #3): a neutral box neither company controls.

What goes in: score.py, scenarios.json, and the recorded per-group JSON (transcript, both records, judge verdicts).
What does NOT go in: any login, API key, or the harness that talks to the models. The sandbox only re-derives the
ten-row table from the records, so a third party can check the numbers without trusting either side's machine.

  DAYTONA_API_KEY=... .venv/bin/python sandbox_daytona.py --run baseline-2026-09-11
  .venv/bin/python sandbox_daytona.py --run baseline-2026-09-11 --dry-run      # lists the payload, no network
Output: runs/<tag>/daytona_replay.md (sandbox id, region, command, exit code, table) and stdout.
"""
import argparse, hashlib, json, os, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
KEEP = ("meta.json", "transcript.json", "buyer_summary.json", "seller_summary.json",
        "judge_seller.json", "judge_buyer.json", "crew_judge_seller.json", "crew_judge_buyer.json")

def payload(run_tag, groups):
    run_dir = ROOT / "runs" / run_tag
    files = [("score.py", ROOT / "score.py"), ("scenarios.json", ROOT / "scenarios.json")]
    for gdir in sorted(p for p in run_dir.iterdir() if p.is_dir()):
        if groups and gdir.name not in groups:
            continue
        for name in KEEP:
            if (gdir / name).exists():
                files.append((f"runs/{run_tag}/{gdir.name}/{name}", gdir / name))
    return files

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--groups", nargs="*", default=[])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--keep", action="store_true", help="leave the sandbox running (default: delete after replay)")
    a = ap.parse_args()
    files = payload(a.run, a.groups)
    total = sum(p.stat().st_size for _, p in files)
    digest = hashlib.sha256(b"".join(p.read_bytes() for _, p in files)).hexdigest()[:16]
    remote_cmd = f"cd /home/daytona/a2 && python3 score.py --run {a.run}"
    print(f"payload: {len(files)} files, {total/1024:.1f} KB, sha256[:16]={digest}")
    for rel, _ in files:
        print("  ", rel)
    print("command:", remote_cmd)
    if a.dry_run:
        return
    key = os.environ.get("DAYTONA_API_KEY")
    if not key:
        sys.exit("DAYTONA_API_KEY not set (get it at the Daytona desk / app.daytona.io → API keys). Use --dry-run to see the payload.")
    from daytona import Daytona, DaytonaConfig, FileUpload
    cfg = {"api_key": key}
    if os.environ.get("DAYTONA_API_URL"): cfg["api_url"] = os.environ["DAYTONA_API_URL"]
    if os.environ.get("DAYTONA_TARGET"): cfg["target"] = os.environ["DAYTONA_TARGET"]
    d = Daytona(DaytonaConfig(**cfg))
    t0 = time.time()
    sb = d.create()
    created = round(time.time() - t0, 1)
    print(f"sandbox {sb.id} created in {created}s")
    try:
        sb.fs.upload_files([FileUpload(source=p.read_bytes(), destination=f"/home/daytona/a2/{rel}") for rel, p in files])
        r = sb.process.exec(remote_cmd, timeout=120)
        out = r.result if hasattr(r, "result") else str(r)
        code = getattr(r, "exit_code", None)
        print(f"exit {code}, {round(time.time() - t0, 1)}s total")
        print(out)
        region = getattr(sb, "target", None) or getattr(getattr(sb, "instance", None), "target", "?")
        md = [f"# Daytona replay — run `{a.run}`",
              f"sandbox: `{sb.id}`  region: {region}  created in {created}s  payload: {len(files)} files / {total/1024:.1f} KB / sha256[:16] {digest}",
              f"command: `{remote_cmd}`  exit: {code}  ({time.strftime('%Y-%m-%d %H:%M %Z')})",
              "", "Nothing but the recorded JSON and score.py went in: no login, no key, no model call.", "", out]
        (ROOT / "runs" / a.run / "daytona_replay.md").write_text("\n".join(md))
        print(f"wrote runs/{a.run}/daytona_replay.md")
    finally:
        if not a.keep:
            sb.delete()
            print(f"sandbox {sb.id} deleted")

if __name__ == "__main__":
    main()
