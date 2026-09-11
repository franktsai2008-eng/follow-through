#!/usr/bin/env python3
"""Follow-Through — the tail of a B2B deal, run by each side's own agent.

A human types their side's task card. Their agent (claude -p) and the other company's agent
(codex exec, or claude) talk in plain prose. Both cards carry the SAME public reference line
fetched from the You.com Search API. Each side writes its own record; the two records are
diffed; a single-model audit and a CrewAI crew audit judge both sides blind; next actions are
proposed and only leave the building when a human presses Approve (One → Gmail). Rejections
and every finished case are written back as lessons that the next run recalls.

    python3 app.py            # http://localhost:8787   (stdlib only, system python)
Anything that needs the venv (crewai, daytona) runs as a subprocess: JSON file in, JSON out.
"""
import json, os, re, subprocess, sys, threading, time, urllib.request, uuid
from datetime import datetime
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))


def load_env(path):
    """Tiny KEY=VALUE parser so no dependency is needed for .env."""
    try:
        text = path.read_text()
    except OSError:
        return
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        v = v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            v = v[1:-1]
        os.environ.setdefault(k.strip(), v)


load_env(BASE / ".env")

from harness import call_claude, call_codex, call_with_retry, parse_status, strip_status, parse_json
from grounding import search_api, flatten, compress_prompt

ROOT = BASE / "app"
RUNS = ROOT / "runs"
RUNS.mkdir(parents=True, exist_ok=True)
LESSONS = ROOT / "lessons.md"
VENV_PY = BASE / ".venv" / "bin" / "python"
JOBS = {}
LOCK = threading.Lock()
CLAUDE_MODEL = os.environ.get("FT_CLAUDE_MODEL", "sonnet")
CODEX_MODEL = os.environ.get("FT_CODEX_MODEL", "gpt-5.6-sol")
ALLOWED = [a.strip().lower() for a in os.environ.get("FT_ALLOWED_RECIPIENTS", "franktsai.2008@gmail.com").split(",") if a.strip()]
SEND_TIMES = []
SEND_LIMIT = 10
JID_RE = re.compile(r"^[0-9a-f]{10}$")
APPROVAL_RE = re.compile(r"\b(approval|approve|sign[- ]?off|director|manager|authoriz|not able to|can't commit|cannot commit|can’t commit|outside my|beyond my)\b", re.I)
PROBE = {"youcom": {"ok": False, "detail": "checking"}, "one": {"ok": False, "detail": "checking"},
         "crewai": {"ok": False, "detail": "checking"}, "daytona": {"ok": False, "detail": "checking"}}
PROBE_DONE = threading.Event()
ONE = {"connection": None, "action_id": None}


def now_hm():
    return datetime.now().strftime("%H:%M")


# ---------------------------------------------------------------- One memory (lessons mirrored into a real system)
def one_mem_add(text, tags):
    """Mirror a lesson into One's memory store (`one mem add`). Best effort; lessons.md stays the source of truth."""
    try:
        data = json.dumps({"text": text, "tags": ["follow-through"] + [t for t in tags if t]})
        r = subprocess.run(["one", "--agent", "mem", "add", "note", data, "--weight", "6"], capture_output=True, text=True, timeout=60)
        rec = parse_json(r.stdout)
        return {"id": rec.get("id"), "at": now_hm()} if isinstance(rec, dict) and rec.get("id") else {"error": (r.stderr or r.stdout)[-160:]}
    except Exception as e:  # noqa
        return {"error": str(e)[:160]}


def one_mem_count(query="follow-through"):
    try:
        r = subprocess.run(["one", "--agent", "mem", "search", query], capture_output=True, text=True, timeout=45)
        d = parse_json(r.stdout)
        return int(d.get("total", 0)) if isinstance(d, dict) else 0
    except Exception:  # noqa
        return None


def mirror_lesson(jid, text, tags):
    def _go():
        res = one_mem_add(text, tags)
        J = JOBS.get(jid)
        if J is not None:
            J.setdefault("one_memory", {})["learned"] = res
            save(jid)
    threading.Thread(target=_go, daemon=True).start()


# ---------------------------------------------------------------- partner probes
def one_probe():
    """`one --agent list` → the operational gmail connection; then resolve the send action id at runtime."""
    try:
        r = subprocess.run(["one", "--agent", "list"], capture_output=True, text=True, timeout=45)
        data = parse_json(r.stdout)
        conn = next((c for c in data.get("connections", []) if c.get("platform") == "gmail" and c.get("state") == "operational"), None)
        if not conn:
            return {"ok": False, "detail": "no operational gmail connection (run: one add gmail)"}
        ONE["connection"] = conn.get("key")
        r2 = subprocess.run(["one", "--agent", "actions", "search", "gmail", "send email", "-t", "execute"],
                            capture_output=True, text=True, timeout=45)
        acts = parse_json(r2.stdout).get("actions", [])
        act = next((a for a in acts if a.get("path") == "/v1/gmail/send-email"), None)
        if not act:
            return {"ok": False, "detail": "gmail connected but no send-email action", "connection": ONE["connection"]}
        ONE["action_id"] = act.get("actionId")
        return {"ok": True, "detail": "gmail operational", "connection": ONE["connection"], "action": act.get("title", "Send Email")}
    except Exception as e:  # noqa
        return {"ok": False, "detail": f"one cli: {str(e)[:160]}"}


def probe_all():
    key = os.environ.get("YDC_API_KEY")
    PROBE["youcom"] = {"ok": bool(key), "detail": "key set" if key else "no YDC_API_KEY in .env"}
    PROBE["one"] = one_probe()
    try:
        r = subprocess.run([str(VENV_PY), "-c", "import crewai;print(crewai.__version__)"], capture_output=True, text=True, timeout=90)
        v = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""
        PROBE["crewai"] = {"ok": bool(v), "detail": f"{v} in .venv" if v else f"import failed: {r.stderr[-120:]}"}
    except Exception as e:  # noqa
        PROBE["crewai"] = {"ok": False, "detail": f".venv: {str(e)[:120]}"}
    dk = os.environ.get("DAYTONA_API_KEY")
    PROBE["daytona"] = {"ok": bool(dk), "detail": "key set" if dk else "waiting for key"}
    n = one_mem_count()
    PROBE["one_memory"] = {"ok": n is not None, "records": n or 0, "detail": (f"{n} lesson records in One memory" if n is not None else "one mem unavailable")}
    PROBE_DONE.set()


# ---------------------------------------------------------------- prompts
STYLE = """RULES FOR EVERY MESSAGE:
- Write like a real person sending a short business message: plain prose, no headings, no bullet lists, no markdown, no meta commentary about being an AI or about these rules, no internal reasoning.
- At most 150 words.
- Stay inside your authority. If the other side asks for something outside it, say plainly that it needs your manager's approval; do not promise it.
- End with exactly one line: STATUS: continue   or   STATUS: accept   or   STATUS: walk_away
  Use "accept" only when you agree to the full set of terms currently on the table. "walk_away" ends the conversation permanently; use it only when no deal inside your authority is possible."""


def card_block(card):
    return f"""YOUR TASK CARD (private — the other side cannot see this):
{card.strip()}
- Your manager is not reachable during this conversation."""


def turn_prompt(card, hist, rnd, max_rounds, lessons):
    lb = f"\n\nLESSONS YOU WROTE DOWN AFTER EARLIER CASES (use them):\n{lessons}\n" if lessons else ""
    h = "\n\n".join(f"[{m['side'].upper()} — round {m['round']}]\n{m['text']}" for m in hist) or "(no messages yet — you open the conversation)"
    return f"{card_block(card)}{lb}\n\nCONVERSATION SO FAR:\n{h}\n\nThis is round {rnd} of at most {max_rounds}. Write your next message to the other side.\n\n{STYLE}"


def memo_prompt(card, hist):
    h = "\n\n".join(f"[{m['side'].upper()} — round {m['round']}]\n{m['text']}" for m in hist)
    return f"{card_block(card)}\n\nFULL CONVERSATION:\n{h}\n\nThe conversation is over. Write a short internal memo for your own company's files: the outcome, the terms as you understand them, anything left open or conditional. Plain prose, at most 100 words, no headings, no JSON."


def extract_prompt(memo):
    return f"""Below is an internal memo written after a business conversation. Extract it into JSON. Output ONLY a JSON object:
{{"deal_closed": true/false, "amount_or_price": string or null, "quantity_or_scope": string or null, "date_or_delivery": string or null, "payment_terms": string or null, "conditional_items": string}}

MEMO:
{memo}"""


def diff_prompt(rec_me, rec_other, company_me, company_other):
    return f"""Two companies each wrote their own record of the SAME conversation. Compare them field by field.

{company_me} RECORD:
{json.dumps(rec_me, indent=2)}

{company_other} RECORD:
{json.dumps(rec_other, indent=2)}

For each field say exactly one of:
"identical"  — same value, same wording or trivially the same string
"equivalent" — same meaning, different wording or unit (e.g. "$9,400" vs "9400 USD", "15 days" vs "by the 26th")
"conflict"   — the two records say different things a court would care about
"missing"    — one side recorded it and the other left it blank/null

Output ONLY a JSON object:
{{"amount_or_price": "...", "quantity_or_scope": "...", "date_or_delivery": "...", "payment_terms": "..."}}"""


def audit_prompt(card, hist, who):
    h = "\n\n".join(f"[{m['side'].upper()} — round {m['round']}]\n{m['text']}" for m in hist)
    return f"""You are an auditor. Below is the private task card the {who.upper()} was working from, then the complete exchange. Judge the {who.upper()} strictly from the exchange.

{card_block(card)}

FULL EXCHANGE:
{h}

Output ONLY a JSON object:
{{"binding_deal_in_exchange": true/false, "committed_beyond_authority": true/false, "beyond_authority_evidence": string, "flagged_need_for_approval": true/false, "flag_evidence": string, "left_ambiguous": string}}"""


def actions_prompt(card, hist, memo, recipient):
    h = "\n\n".join(f"[{m['side'].upper()} — round {m['round']}]\n{m['text']}" for m in hist)
    return f"""{card_block(card)}

FULL EXCHANGE:
{h}

YOUR MEMO: {memo}

List the next actions your company should take after this conversation (2 to 4). The FIRST action must be a follow-up email that confirms in writing what was agreed and what still needs approval. For each action say whether it needs a human's approval before it leaves the company (anything that sends a message, moves money, creates an obligation, or touches another system does).
For message actions include "to" (use {recipient}), a "subject" line under 70 characters, and a ready-to-send "draft" body in plain prose, at most 140 words, signed off generically.
Output ONLY a JSON object: {{"actions": [{{"action": string, "needs_approval": true/false, "why": string, "to": string, "subject": string, "draft": string}}]}}"""


def lesson_prompt(card, hist, memo):
    h = "\n".join(f"[{m['side'].upper()} r{m['round']}] {m['text']}" for m in hist)
    return f"{card_block(card)}\n\nYou just finished this case. Memo: {memo}\nTranscript:\n{h}\n\nWrite ONE lesson for your future self, at most 40 words, about what to do differently or keep doing. Plain text, one line."


def reject_lesson_prompt(action, reason):
    return f"""A human reviewed this proposed next action from your agent and REJECTED it.

ACTION: {action.get('action','')}
SUBJECT: {action.get('subject','')}
DRAFT: {action.get('draft','')}

THE HUMAN'S REASON: {reason}

Write ONE lesson for your future self so the next draft does not get rejected the same way. At most 40 words, plain text, one line, no preamble, no quotes."""


def counterparty_prompt(my_card, flow, company_other, company_me):
    return f"""One side of a business follow-up ({flow}) has this private task card:
{my_card}

Write the OTHER side's private task card. That side works for {company_other}; the first side works for {company_me}. Make it a realistic counterpart: their role, what they want, their authority limits (what needs their manager), one hidden constraint the first side cannot see, and one thing their card leaves unspecified. Plain text bullets, at most 110 words, no preamble."""


def query_prompt(my_card):
    return f"""Below is one side's private task card for a business follow-up.

{my_card}

Write ONE web search query, at most 12 words, that would surface PUBLIC market prices or market facts for whatever is being bought, sold or invoiced here. No quotes, no preamble, output the query and nothing else."""


def badge(text, status):
    if status == "walk_away":
        return "walked away"
    if APPROVAL_RE.search(text):
        return "names its limit"
    if status == "accept":
        return "accepts"
    return "within authority"


# ---------------------------------------------------------------- persistence
def load_job(jid):
    """In-memory job, else the persisted app/runs/<id>.json (so approve/reject/replay work after a restart)."""
    j = JOBS.get(jid)
    if j is None and JID_RE.match(str(jid)):
        f = RUNS / f"{jid}.json"
        if f.exists():
            j = json.loads(f.read_text())
            JOBS[jid] = j
    return j


def save(jid):
    j = JOBS.get(jid)
    if not j or not JID_RE.match(str(jid)):
        return
    with LOCK:
        try:
            (RUNS / f"{jid}.json").write_text(json.dumps(j, indent=2, default=str))
        except Exception:  # noqa
            pass


def stage(jid, s):
    JOBS[jid]["stage"] = s
    save(jid)


def recall_lessons(use):
    if not (use and LESSONS.exists()):
        return "", []
    text = LESSONS.read_text().strip()
    lines = [re.sub(r"^[-*]\s*", "", l).strip() for l in text.splitlines() if l.strip()]
    return text, lines


# ---------------------------------------------------------------- grounding
def ground(jid, my_card, me_call):
    """You.com Search API → one ≤45-word line written card-blind, the same line on both cards."""
    stage(jid, "grounding both cards with a You.com search")
    query = me_call(query_prompt(my_card)).strip().splitlines()[0].strip().strip('"')[:120]
    _src, data = search_api(query, 5)
    PROBE["youcom"] = {"ok": True, "detail": "key set, last call 200"}
    hits = flatten(data)
    if not hits:
        raise RuntimeError("You.com returned no results")
    line = me_call(compress_prompt(query, hits)).strip().splitlines()[0]
    sources = []
    for h in hits:
        d = re.sub(r"^www\.", "", (h.get("url", "").split("/")[2] if "://" in h.get("url", "") else ""))
        if d and d not in sources:
            sources.append(d)
    return {"line": line, "sources": sources[:4], "query": query, "fetched": now_hm(),
            "via": "You.com Search API", "hits": [{"title": h.get("title", ""), "url": h.get("url", "")} for h in hits[:5]]}


def ref_block(ref):
    if not ref:
        return ""
    return ("\n\nPUBLIC MARKET REFERENCE (from a You.com search, same line on both cards; sources: "
            + ", ".join(ref["sources"]) + "): " + ref["line"]
            + "\nYour own card's limits are your company's decision and still apply.")


# ---------------------------------------------------------------- crew audit
def crew_thread(jid, card_me, card_other, hist):
    J = JOBS[jid]
    try:
        if not VENV_PY.exists() or not PROBE.get("crewai", {}).get("ok"):
            J["crew_audit"] = {"status": "skipped", "me": None, "other": None, "agrees": None,
                               "detail": PROBE.get("crewai", {}).get("detail", "no .venv")}
            return save(jid)
        inp = RUNS / f"{jid}.crew_in.json"
        outp = RUNS / f"{jid}.crew_out.json"
        inp.write_text(json.dumps({"card_me": card_me, "card_other": card_other, "messages": hist, "model": CLAUDE_MODEL}))
        env = dict(os.environ, CREWAI_DISABLE_TELEMETRY="true", CREWAI_TRACING_ENABLED="false", OTEL_SDK_DISABLED="true")
        try:
            subprocess.run([str(VENV_PY), str(BASE / "crew_audit_job.py"), str(inp), str(outp)],
                           capture_output=True, text=True, timeout=90, env=env, cwd=str(BASE))
        except subprocess.TimeoutExpired:
            J["crew_audit"] = {"status": "error", "me": None, "other": None, "agrees": None, "detail": "crew timed out at 90s"}
            return save(jid)
        res = json.loads(outp.read_text()) if outp.exists() else {"status": "error", "detail": "no output"}
        if res.get("status") == "done":
            single = J.get("audit") or {}
            agrees = {}
            for s in ("me", "other"):
                a, b = single.get(s) or {}, res.get(s) or {}
                agrees[s] = (bool(a.get("committed_beyond_authority")) == bool(b.get("committed_beyond_authority")) and
                             bool(a.get("flagged_need_for_approval")) == bool(b.get("flagged_need_for_approval")))
            res["agrees"] = agrees
        else:
            res.setdefault("agrees", None)
        res.setdefault("me", None)
        res.setdefault("other", None)
        J["crew_audit"] = res
        save(jid)
    except Exception as e:  # noqa
        J["crew_audit"] = {"status": "error", "me": None, "other": None, "agrees": None, "detail": str(e)[:200]}
        save(jid)


# ---------------------------------------------------------------- the run
def run_job(jid, p):
    J = JOBS[jid]
    try:
        cx = Path("/tmp/a2-codex/app") / jid
        me_call = lambda pr: call_with_retry(call_claude, pr, CLAUDE_MODEL)
        other_call = (lambda pr: call_with_retry(call_codex, pr, CODEX_MODEL, cx)) if p["other_model"] == "gpt" else me_call
        lessons_text, lessons_list = recall_lessons(p["use_lessons"])
        J["recalled"] = lessons_list
        n = one_mem_count() if p.get("use_lessons", True) else 0
        J["one_memory"] = {"recalled_records": n or 0}
        save(jid)
        save(jid)

        ref = None
        if p["ground"]:
            try:
                ref = ground(jid, p["my_card"], me_call)
            except Exception as e:  # noqa
                ref = None
                J["stage_note"] = f"reference unavailable ({str(e)[:120]})"
                PROBE["youcom"] = {"ok": bool(os.environ.get("YDC_API_KEY")), "detail": f"last call failed: {str(e)[:80]}"}
        J["reference"] = ref
        save(jid)

        other_card = p["other_card"].strip()
        if not other_card:
            stage(jid, "writing the other side's card")
            other_card = me_call(counterparty_prompt(p["my_card"], p["flow"], p["company_other"], p["company_me"]))
        rb = ref_block(ref)
        head_me = f"You represent {p['company_me']}. The other side represents {p['company_other']}.\n"
        head_other = f"You represent {p['company_other']}. The other side represents {p['company_me']}.\n"
        card_me = head_me + p["my_card"].strip() + rb
        card_other = head_other + other_card.strip() + rb
        J["other_card"] = card_other
        save(jid)

        hist, statuses, end = [], [], "max_rounds"
        for rnd in range(1, p["max_rounds"] + 1):
            for side, call, card in (("me", me_call, card_me), ("other", other_call, card_other)):
                who = p["company_me"] if side == "me" else p["company_other"]
                stage(jid, f"round {rnd}: {who}'s agent is writing")
                raw = call(turn_prompt(card, hist, rnd, p["max_rounds"], lessons_text if side == "me" else ""))
                st = parse_status(raw)
                txt = strip_status(raw)
                hist.append({"side": side, "round": rnd, "text": txt, "status": st, "badge": badge(txt, st)})
                J["messages"] = list(hist)
                save(jid)
                statuses.append(st)
                if st == "walk_away":
                    end = f"{side}_walked_away"
                    break
                if len(statuses) >= 2 and statuses[-1] == "accept" and statuses[-2] == "accept":
                    end = "both_accepted"
                    break
            if end != "max_rounds":
                break
        J["end"] = end
        stage(jid, "each side writes its record")
        memos = {"me": me_call(memo_prompt(card_me, hist)), "other": other_call(memo_prompt(card_other, hist))}
        J["memos"] = memos
        save(jid)
        J["records"] = {s: parse_json(me_call(extract_prompt(m))) for s, m in memos.items()}
        save(jid)

        stage(jid, "comparing the two records")
        d = parse_json(me_call(diff_prompt(J["records"]["me"], J["records"]["other"], p["company_me"], p["company_other"])))
        ok = {"identical", "equivalent", "conflict", "missing"}
        J["record_diff"] = {k: (str(d.get(k, "missing")).strip().lower() if str(d.get(k, "")).strip().lower() in ok else "missing")
                            for k in ("amount_or_price", "quantity_or_scope", "date_or_delivery", "payment_terms")}
        save(jid)

        stage(jid, "blind audit")
        J["audit"] = {"me": parse_json(me_call(audit_prompt(card_me, hist, "first party"))),
                      "other": parse_json(me_call(audit_prompt(card_other, hist, "second party")))}
        J["crew_audit"] = {"status": "running", "me": None, "other": None, "agrees": None}
        save(jid)
        threading.Thread(target=crew_thread, args=(jid, card_me, card_other, hist), daemon=True).start()

        stage(jid, "proposing next actions")
        acts = parse_json(me_call(actions_prompt(card_me, hist, memos["me"], p["recipient_email"]))).get("actions", [])
        clean = []
        for a in acts if isinstance(acts, list) else []:
            if not isinstance(a, dict):
                continue
            draft = (a.get("draft") or "").strip()
            clean.append({"action": (a.get("action") or "").strip(), "needs_approval": bool(a.get("needs_approval", True)),
                          "why": (a.get("why") or "").strip(), "to": (a.get("to") or p["recipient_email"]).strip() or p["recipient_email"],
                          "subject": (a.get("subject") or f"Follow-up — {p['flow']}").strip(), "draft": draft, "state": "proposed",
                          "sent": None, "reject_reason": None})
        J["actions"] = clean
        save(jid)

        stage(jid, "writing a lesson")
        lesson = me_call(lesson_prompt(card_me, hist, memos["me"])).strip().splitlines()[0]
        with LOCK:
            with open(LESSONS, "a") as f:
                f.write(f"- {lesson}\n")
        J["learned"] = lesson
        J["lessons_now"] = LESSONS.read_text() if LESSONS.exists() else ""
        mirror_lesson(jid, lesson, [p.get("flow", "custom"), "learned"])
        J["stage"] = "done"
        J["status"] = "done"
        save(jid)
    except Exception as e:  # noqa
        J["status"] = "error"
        J["error"] = str(e)[-500:]
        J["stage"] = "error"
        save(jid)


# ---------------------------------------------------------------- One send
def find_key(obj, names):
    """First value under any of `names`, searched breadth-first — One's response shape is not contractual."""
    queue = [obj]
    while queue:
        cur = queue.pop(0)
        if isinstance(cur, dict):
            for k, v in cur.items():
                if k in names and isinstance(v, (str, int)) and str(v).strip():
                    return str(v)
            queue += [v for v in cur.values() if isinstance(v, (dict, list))]
        elif isinstance(cur, list):
            queue += [v for v in cur if isinstance(v, (dict, list))]
    return None


def one_send(to, subject, body):
    if not (ONE["action_id"] and ONE["connection"]):
        got = one_probe()
        if not got.get("ok"):
            return {"error": f"One not ready: {got.get('detail')}"}
    payload = json.dumps({"connectionKey": ONE["connection"], "to": to, "subject": subject, "body": body})
    cmd = ["one", "--agent", "actions", "execute", "gmail", ONE["action_id"], ONE["connection"], "-d", payload]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        return {"error": "One send timed out after 60s"}
    raw = parse_json(r.stdout)
    if raw.get("parse_error") or (isinstance(raw, dict) and raw.get("error")):
        return {"error": (r.stderr or r.stdout or "One returned no JSON")[-300:], "raw": raw}
    return {"message_id": find_key(raw, {"id", "messageId", "message_id"}),
            "thread_id": find_key(raw, {"threadId", "thread_id"}),
            "at": now_hm(), "raw": raw}


# ---------------------------------------------------------------- replay
def replay_files(jid):
    return {"status": "waiting_for_key", "sandbox_id": None, "exit_code": None,
            "output": "DAYTONA_API_KEY is not set. The moment it lands in .env this runs for real, unchanged.",
            "files": ["job.json", "replay_job.py"], "command": "python3 replay_job.py job.json"}


def replay_thread(jid):
    J = JOBS[jid]
    try:
        save(jid)
        r = subprocess.run([str(VENV_PY), str(BASE / "daytona_replay.py"), str(RUNS / f"{jid}.json")],
                           capture_output=True, text=True, timeout=240, cwd=str(BASE))
        out = parse_json(r.stdout)
        if out.get("parse_error"):
            J["replay"] = {"status": "error", "sandbox_id": None, "exit_code": None,
                           "output": (r.stderr or r.stdout)[-1500:], "files": ["job.json", "replay_job.py"],
                           "command": "python3 replay_job.py job.json"}
        else:
            J["replay"] = {"status": "done" if out.get("exit_code") == 0 else "error",
                           "sandbox_id": out.get("sandbox_id"), "exit_code": out.get("exit_code"),
                           "output": out.get("output", "")[-4000:], "files": ["job.json", "replay_job.py"],
                           "command": "python3 replay_job.py job.json"}
    except Exception as e:  # noqa
        J["replay"] = {"status": "error", "sandbox_id": None, "exit_code": None, "output": str(e)[:500],
                       "files": ["job.json", "replay_job.py"], "command": "python3 replay_job.py job.json"}
    save(jid)


# ---------------------------------------------------------------- http
class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body, default=str).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _body(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        try:
            return json.loads(self.rfile.read(n) or b"{}")
        except Exception:  # noqa
            return {}

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            return self._send(200, (ROOT / "index.html").read_bytes(), "text/html")
        if path == "/status":
            PROBE_DONE.wait(timeout=20)
            return self._send(200, {**PROBE,
                                    "models": {"me": f"claude {CLAUDE_MODEL}", "other": CODEX_MODEL},
                                    "recipient_default": ALLOWED[0] if ALLOWED else "",
                                    "allowed_recipients": ALLOWED})
        if path == "/job":
            jid = (parse_qs(urlparse(self.path).query).get("id") or [""])[0]
            if not JID_RE.match(jid):
                return self._send(400, {"error": "bad id"})
            j = load_job(jid)
            return self._send(200, j or {"status": "unknown"})
        if path == "/runs":
            out = []
            for f in sorted(RUNS.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
                if f.name.endswith(".crew_in.json") or f.name.endswith(".crew_out.json"):
                    continue
                try:
                    j = json.loads(f.read_text())
                except Exception:  # noqa
                    continue
                p = j.get("params", {})
                out.append({"id": f.stem, "created": j.get("created"), "created_at": j.get("created_at"),
                            "flow": p.get("flow"), "company_me": p.get("company_me"), "company_other": p.get("company_other"),
                            "end": j.get("end"), "status": j.get("status")})
            return self._send(200, out[:40])
        if path == "/lessons":
            return self._send(200, {"lessons": LESSONS.read_text() if LESSONS.exists() else ""})
        return self._send(404, {"error": "not found"})

    def do_POST(self):
        path = self.path.split("?")[0]
        if path == "/run":
            b = self._body()
            p = {"company_me": (b.get("company_me") or "Northline Procurement").strip(),
                 "company_other": (b.get("company_other") or "Harbor Packaging").strip(),
                 "flow": b.get("flow", "custom"), "my_card": (b.get("my_card") or "").strip(),
                 "other_card": b.get("other_card", "") or "", "other_model": b.get("other_model", "gpt"),
                 "max_rounds": max(2, min(8, int(b.get("max_rounds", 6) or 6))),
                 "use_lessons": bool(b.get("use_lessons", True)), "ground": bool(b.get("ground", True)),
                 "recipient_email": (b.get("recipient_email") or (ALLOWED[0] if ALLOWED else "")).strip()}
            if not p["my_card"]:
                return self._send(400, {"error": "your card is empty"})
            jid = uuid.uuid4().hex[:10]
            JOBS[jid] = {"id": jid, "status": "running", "stage": "starting", "created": time.time(),
                         "created_at": datetime.now().isoformat(timespec="seconds"), "params": p,
                         "recalled": [], "reference": None, "other_card": "", "messages": [], "memos": {},
                         "records": {}, "record_diff": {}, "audit": {},
                         "crew_audit": {"status": "running", "me": None, "other": None, "agrees": None},
                         "actions": [], "learned": "", "lessons_now": "", "end": None, "error": None,
                         "replay": {"status": "waiting_for_key" if not os.environ.get("DAYTONA_API_KEY") else "idle",
                                    "sandbox_id": None, "exit_code": None, "output": "",
                                    "files": ["job.json", "replay_job.py"], "command": "python3 replay_job.py job.json"}}
            save(jid)
            threading.Thread(target=run_job, args=(jid, p), daemon=True).start()
            return self._send(200, {"id": jid})

        if path == "/approve":
            b = self._body()
            jid = str(b.get("id") or "")
            if not JID_RE.match(jid):
                return self._send(400, {"error": "bad id"})
            J = load_job(jid)
            if not J:
                return self._send(404, {"error": "unknown job"})
            try:
                i = int(b.get("i", 0))
                act = J["actions"][i]
            except Exception:  # noqa
                return self._send(404, {"error": "unknown action"})
            to = (b.get("to") or act.get("to") or "").strip()
            if to.lower() not in ALLOWED:
                return self._send(403, {"error": f"{to or '(empty)'} is not in FT_ALLOWED_RECIPIENTS. "
                                                 f"This demo may only email {', '.join(ALLOWED)}."})
            with LOCK:
                cut = time.time() - 3600
                SEND_TIMES[:] = [t for t in SEND_TIMES if t > cut]
                if len(SEND_TIMES) >= SEND_LIMIT:
                    return self._send(429, {"error": f"send rate limit reached ({SEND_LIMIT} per hour)"})
                SEND_TIMES.append(time.time())
            res = one_send(to, (b.get("subject") or act.get("subject") or "Follow-up").strip(),
                           b.get("body") or act.get("draft") or "")
            if res.get("error"):
                with LOCK:
                    if SEND_TIMES:
                        SEND_TIMES.pop()
                return self._send(502, {"error": res["error"]})
            act["state"] = "sent"
            act["to"] = to
            act["subject"] = (b.get("subject") or act.get("subject") or "").strip()
            act["draft"] = b.get("body") or act.get("draft") or ""
            act["sent"] = res
            save(jid)
            return self._send(200, {"ok": True, "sent": res})

        if path == "/reject":
            b = self._body()
            jid = str(b.get("id") or "")
            if not JID_RE.match(jid):
                return self._send(400, {"error": "bad id"})
            J = load_job(jid)
            if not J:
                return self._send(404, {"error": "unknown job"})
            try:
                i = int(b.get("i", 0))
                act = J["actions"][i]
            except Exception:  # noqa
                return self._send(404, {"error": "unknown action"})
            reason = (b.get("reason") or "").strip()
            if not reason:
                return self._send(400, {"error": "a reason is required"})
            try:
                learned = call_with_retry(call_claude, reject_lesson_prompt(act, reason), CLAUDE_MODEL).strip().splitlines()[0]
            except Exception as e:  # noqa
                learned = f"Human rejected this draft: {reason}"
            learned = learned.strip().strip('"')
            with LOCK:
                with open(LESSONS, "a") as f:
                    f.write(f"- (human feedback) {learned}\n")
            act["state"] = "rejected"
            act["reject_reason"] = reason
            act["learned"] = learned
            J["learned"] = learned
            mirror_lesson(jid, learned, [str(J.get("params", {}).get("flow", "custom")), "human-feedback"])
            J["lessons_now"] = LESSONS.read_text() if LESSONS.exists() else ""
            save(jid)
            return self._send(200, {"ok": True, "learned": learned})

        if path == "/replay":
            b = self._body()
            jid = str(b.get("id") or "")
            if not JID_RE.match(jid):
                return self._send(400, {"error": "bad id"})
            J = load_job(jid)
            if not J:
                return self._send(404, {"error": "unknown job"})
            if not os.environ.get("DAYTONA_API_KEY"):
                J["replay"] = replay_files(jid)
                save(jid)
                return self._send(200, J["replay"])
            if (J.get("replay") or {}).get("status") == "running":
                return self._send(200, J["replay"])
            J["replay"] = {"status": "running", "sandbox_id": None, "exit_code": None, "output": "",
                           "files": ["job.json", "replay_job.py"], "command": "python3 replay_job.py job.json"}
            save(jid)
            threading.Thread(target=replay_thread, args=(jid,), daemon=True).start()
            return self._send(200, J["replay"])

        if path == "/lessons/clear":
            LESSONS.write_text("")
            return self._send(200, {"ok": True, "lessons": ""})
        return self._send(404, {"error": "not found"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8787"))
    threading.Thread(target=probe_all, daemon=True).start()
    print(f"Follow-Through app → http://localhost:{port}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", port), H).serve_forever()
