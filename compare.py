#!/usr/bin/env python3
"""Compare two runs group by group (e.g. baseline vs --learn): closed?, rounds to end, seller price, margin over floor.
python3 compare.py --a baseline-2026-09-11 --b learn-home
"""
import argparse, json
from pathlib import Path
ROOT = Path(__file__).resolve().parent
SCEN = {g["id"]: g for g in json.load(open(ROOT / "scenarios.json"))["groups"]}

def rows(tag):
    out = {}
    for gdir in sorted(p for p in (ROOT / "runs" / tag).iterdir() if p.is_dir() and (p / "meta.json").exists()):
        m = json.load(open(gdir / "meta.json")); s = json.load(open(gdir / "seller_summary.json")); b = json.load(open(gdir / "buyer_summary.json"))
        js = (gdir / "judge_seller.json"); js = json.load(open(js)) if js.exists() else {}
        out[gdir.name] = dict(end=m["end_reason"], rounds=m["rounds"], msgs=m["messages"], s_closed=bool(s.get("deal_closed")), b_closed=bool(b.get("deal_closed")),
                              price=s.get("unit_price"), qty=s.get("quantity"), days=s.get("delivery_days"), beyond=js.get("committed_beyond_authority"), flagged=js.get("flagged_need_for_approval"))
    return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--a", required=True); ap.add_argument("--b", required=True); args = ap.parse_args()
    A, B = rows(args.a), rows(args.b)
    md = [f"# {args.a} vs {args.b}", "", "| group | A end (rounds) | B end (rounds) | A seller price / margin over floor | B seller price / margin over floor | A beyond/flagged | B beyond/flagged |", "|---|---|---|---|---|---|---|"]
    def marg(r, gid):
        f = SCEN[gid]["seller"]["floor_price"]
        return f"${r['price']} / {('+' if r['price'] >= f else '') + str(round(r['price'] - f, 2))}" if r["price"] is not None else "—"
    for gid in sorted(set(A) | set(B)):
        a, b = A.get(gid), B.get(gid)
        md.append(f"| {gid} | {a['end']} ({a['rounds']}) | {b['end']} ({b['rounds']}) | {marg(a, gid)} | {marg(b, gid)} | {a['beyond']}/{a['flagged']} | {b['beyond']}/{b['flagged']} |" if a and b else f"| {gid} | {a and a['end']} | {b and b['end']} | | | | |")
    ca = sum(r['s_closed'] and r['b_closed'] for r in A.values()); cb = sum(r['s_closed'] and r['b_closed'] for r in B.values())
    md += ["", f"both-closed: A {ca}/{len(A)} vs B {cb}/{len(B)}; mean rounds: A {sum(r['rounds'] for r in A.values())/max(len(A),1):.1f} vs B {sum(r['rounds'] for r in B.values())/max(len(B),1):.1f}"]
    (ROOT / "results" / f"compare-{args.a}-vs-{args.b}.md").write_text("\n".join(md)); print("\n".join(md))

if __name__ == "__main__":
    main()
