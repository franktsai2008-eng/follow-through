#!/usr/bin/env python3
"""You.com grounding: one public market-reference line per scenario, same line on BOTH cards.

Source order: You.com Search API (POST https://ydc-index.io/v1/search, X-API-Key) when YDC_API_KEY is set,
else You.com free MCP (https://api.you.com/mcp?profile=free, 100 calls/day, no key).
The raw results are kept for provenance; a card-blind model compresses them to one line (<=45 words) that may only
use numbers present in the snippets and must name its source domains.

    python3 grounding.py --all            # writes grounding/<GID>.json (cached; --force to refetch)
    python3 grounding.py --groups G01     # one group, prints the line
"""
import argparse, json, os, re, sys, time, urllib.request
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import SCEN, call_claude, call_with_retry
from mcp_http import McpHttp

ROOT = Path(__file__).resolve().parent
GDIR = ROOT / "grounding"
FREE_MCP = "https://api.you.com/mcp?profile=free"

def search_api(query, count=5):
    key = os.environ.get("YDC_API_KEY")
    body = json.dumps({"query": query, "count": count}).encode()
    req = urllib.request.Request("https://ydc-index.io/v1/search", data=body, method="POST",
                                 headers={"Content-Type": "application/json", "X-API-Key": key, "User-Agent": "curl/8.7.1"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return "search_api", json.loads(r.read().decode())

def search_mcp(query, count=5):
    m = McpHttp(FREE_MCP)
    txt, res = m.call("you-search", {"query": query, "count": count})
    try:
        return "free_mcp", json.loads(txt)
    except json.JSONDecodeError:
        return "free_mcp", {"raw": txt}

def flatten(data):
    """→ list of {url,title,snippet} from either API shape."""
    out = []
    web = (data.get("results", {}) or {}).get("web") or data.get("hits") or data.get("web") or []
    for h in web:
        snip = " ".join((h.get("contents", {}) or {}).get("highlights", []) or h.get("snippets", []) or [h.get("description", "")])
        out.append({"url": h.get("url", ""), "title": h.get("title", ""), "snippet": re.sub(r"\s+", " ", snip)[:1200]})
    return out

def compress_prompt(product, hits):
    src = "\n\n".join(f"[{i+1}] {h['url']}\n{h['title']}\n{h['snippet']}" for i, h in enumerate(hits))
    return f"""Below are public web search results about the market for: {product}.
Write ONE line (at most 45 words) a procurement or sales person could put at the top of a task card as "market reference".
Rules: only use prices, ranges or facts that literally appear in the snippets; if no price appears, say so plainly ("no public unit price found; ...") and give whatever market fact is there. Name the source domain(s) in parentheses at the end. No markdown, no preamble.

{src}"""

def ground(g, force=False, model="sonnet"):
    GDIR.mkdir(exist_ok=True)
    out = GDIR / f"{g['id']}.json"
    if out.exists() and not force:
        return json.load(open(out))
    q = f"{g['product']} wholesale price per unit 2026"
    src, data = (search_api(q) if os.environ.get("YDC_API_KEY") else search_mcp(q))
    hits = flatten(data)
    if not hits:
        raise RuntimeError(f"{g['id']}: no hits from {src}: {json.dumps(data)[:300]}")
    line = call_with_retry(call_claude, compress_prompt(g["product"], hits), model).strip().splitlines()[0]
    rec = {"group": g["id"], "product": g["product"], "query": q, "source": src, "fetched": date.today().isoformat(),
           "line": line, "hits": hits}
    out.write_text(json.dumps(rec, indent=2))
    return rec

def load_line(gid):
    p = GDIR / f"{gid}.json"
    return json.load(open(p)) if p.exists() else None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--groups", nargs="*", default=[])
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--model", default="sonnet")
    a = ap.parse_args()
    groups = [g for g in SCEN["groups"] if a.all or g["id"] in a.groups]
    for g in groups:
        rec = ground(g, a.force, a.model)
        print(f"[{g['id']}] ({rec['source']}, {rec['fetched']}) {rec['line']}", flush=True)
        time.sleep(1)

if __name__ == "__main__":
    main()
