#!/usr/bin/env python3
"""The learning harness: how much of the agent's draft did the person have to change?

Pure stdlib, no network, no model call, no key — this is what runs inside the Daytona sandbox, a
box neither the agent nor the person controls. In goes a list of finished cases, out goes one
number per case (the edit ratio) and the trend across them. Lower is better: the whole product is
a bet that the person edits less each time.

    python3 harness_job.py harness_in.json
in: [{"id":…, "created_at":…, "company_other":…, "draft_body":…, "final_body":…}, …]
Exit 0 on success.
"""
import difflib, json, sys

W = 78


def changed_chars(a, b):
    """Characters the person added, removed or replaced — counted from the diff, not guessed from the ratio."""
    n = 0
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b).get_opcodes():
        if op != "equal":
            n += max(i2 - i1, j2 - j1)
    return n


def cell(v, w):
    s = " ".join(str("—" if v is None else v).split())
    return (s[: w - 2] + "… ") if len(s) > w - 1 else s.ljust(w)


def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def main():
    rows = json.loads(open(sys.argv[1]).read())
    out = []
    out.append("FOLLOW-THROUGH — EDIT-RATIO HARNESS")
    out.append("=" * W)
    out.append(f"cases replayed: {len(rows)}   source: each case's recorded draft vs what the person actually sent")
    out.append("")
    out.append(f"{'case'.ljust(12)}{'date'.ljust(12)}{'other side'.ljust(20)}{'draft'.rjust(7)}{'changed'.rjust(9)}{'edit %'.rjust(9)}")
    out.append("-" * W)

    ratios = []
    for r in rows:
        d = r.get("draft_body") or ""
        f = r.get("final_body") or ""
        ratio = 1 - difflib.SequenceMatcher(None, d, f).ratio()
        ratios.append(ratio)
        out.append(f"{cell(r.get('id'), 12)}{cell(str(r.get('created_at') or '')[:10], 12)}"
                   f"{cell(r.get('company_other'), 20)}{str(len(d)).rjust(7)}{str(changed_chars(d, f)).rjust(9)}"
                   f"{(f'{ratio * 100:.1f}%').rjust(9)}")
    out.append("-" * W)

    if ratios:
        half = len(ratios) // 2
        first, second = ratios[:half] or ratios[:1], ratios[half:] or ratios[-1:]
        fm, sm = mean(first) * 100, mean(second) * 100
        arrow = "down" if sm < fm else ("up" if sm > fm else "flat")
        out.append(f"mean edit ratio: {mean(ratios) * 100:.1f}%   "
                   f"first {len(first)} case(s): {fm:.1f}%   last {len(second)} case(s): {sm:.1f}%   trend: {arrow} ({sm - fm:+.1f} pts)")
    else:
        out.append("no cases yet — send one follow-up and run this again")
    out.append("target: the person edits less over time")
    out.append("")
    out.append("Nothing but the recorded drafts came in here: no login, no key, no model call.")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
