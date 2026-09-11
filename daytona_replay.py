#!/usr/bin/env python3
"""Run replay_job.py inside a fresh Daytona sandbox (sponsor tool #4). Runs under .venv/bin/python.

    .venv/bin/python daytona_replay.py app/runs/<id>.json
stdout: {"sandbox_id": "...", "exit_code": 0, "output": "..."}   (the sandbox is deleted in finally)
Only the run's recorded JSON and the pure-stdlib replay script go in — no key, no login, no model.
"""
import json, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REMOTE = "/home/daytona/ft"


def main():
    job_path = Path(sys.argv[1])
    key = os.environ.get("DAYTONA_API_KEY")
    if not key:
        print(json.dumps({"sandbox_id": None, "exit_code": None, "output": "DAYTONA_API_KEY not set"}))
        return
    from daytona import Daytona, DaytonaConfig, FileUpload
    cfg = {"api_key": key}
    if os.environ.get("DAYTONA_API_URL"):
        cfg["api_url"] = os.environ["DAYTONA_API_URL"]
    if os.environ.get("DAYTONA_TARGET"):
        cfg["target"] = os.environ["DAYTONA_TARGET"]
    d = Daytona(DaytonaConfig(**cfg))
    sb = d.create()
    try:
        sb.fs.upload_files([
            FileUpload(source=job_path.read_bytes(), destination=f"{REMOTE}/job.json"),
            FileUpload(source=(ROOT / "replay_job.py").read_bytes(), destination=f"{REMOTE}/replay_job.py"),
        ])
        r = sb.process.exec(f"python3 {REMOTE}/replay_job.py {REMOTE}/job.json", timeout=120)
        out = r.result if hasattr(r, "result") else str(r)
        print(json.dumps({"sandbox_id": sb.id, "exit_code": getattr(r, "exit_code", None), "output": out}))
    finally:
        try:
            sb.delete()
        except Exception:  # noqa
            pass


if __name__ == "__main__":
    main()
