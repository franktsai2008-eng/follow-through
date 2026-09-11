#!/usr/bin/env python3
"""Follow-Through v3 — meeting notes → strategy talk → draft → the human's edits → send → learn.

One case = one meeting. The agent digests the notes, You.com adds public context about the other
company, a CrewAI crew proposes follow-up strategies, then the agent TALKS the approach through
with the person in a chat. The person locks the strategy, the agent drafts the email, the person
edits it and sends it (One → Gmail, allowlist). Every place a human touched — a correction in the
chat, the edit of the draft, a rejection — is diffed and becomes a lesson in app/lessons.md and in
One's memory. A deterministic harness replays the edit ratio of every sent case inside a Daytona
sandbox; the target is that the person edits less over time.

    python3 app.py            # http://localhost:8787   (stdlib only, system python)
Anything that needs the venv (crewai, daytona) runs as a subprocess: JSON file in, JSON out.
"""
import difflib, json, os, re, subprocess, sys, threading, time, uuid
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

from harness import call_claude, call_with_retry, parse_json
from grounding import search_api, flatten

ROOT = BASE / "app"
CASE_DIR = ROOT / "cases"
CASE_DIR.mkdir(parents=True, exist_ok=True)
LESSONS = ROOT / "lessons.md"
VENV_PY = BASE / ".venv" / "bin" / "python"
CASES = {}
LOCK = threading.RLock()   # re-entrant: the rate-limit blocks answer 429 while still holding it
CLAUDE_MODEL = os.environ.get("FT_CLAUDE_MODEL", "sonnet")
CREW_MODEL = ((BASE / ".crew_model").read_text().strip() if (BASE / ".crew_model").exists() else "") or \
             os.environ.get("FT_CREW_MODEL", "opus")


def one_account_email():
    """The email of the One account this machine is logged into (the demo's default recipient); no address is hardcoded."""
    try:
        cfg = json.loads((Path.home() / ".one" / "config.json").read_text())
        return (cfg.get("whoami", {}).get("user", {}).get("email") or "").strip().lower()
    except Exception:  # noqa
        return ""


ALLOWED = [a.strip().lower() for a in os.environ.get("FT_ALLOWED_RECIPIENTS", one_account_email()).split(",") if a.strip()]
SEND_TIMES = []
SEND_LIMIT = 10
RUN_TIMES = []
RUN_LIMIT = int(os.environ.get("FT_RUN_LIMIT", "12"))
os.environ.setdefault("A2_CREW_LLM", CREW_MODEL)  # the crew thinks with a different model than the chat agent
JID_RE = re.compile(r"^[0-9a-f]{10}$")
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


def mirror_lesson(cid, text, tags):
    """One lesson → One memory, in the background; the record id lands in case.one_memory.learned[]."""
    def _go():
        res = one_mem_add(text, tags)
        C = CASES.get(cid)
        if C is not None:
            C.setdefault("one_memory", {}).setdefault("learned", []).append(res)
            save(cid)
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
            return {"ok": False, "detail": "gmail connected but no send-email action"}
        ONE["action_id"] = act.get("actionId")
        return {"ok": True, "detail": "gmail operational", "connection": "…" + str(ONE["connection"])[-6:], "action": act.get("title", "Send Email")}
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


# ---------------------------------------------------------------- persistence
def load_case(cid):
    """In-memory case, else the persisted app/cases/<id>.json (so chat/lock/send work after a restart)."""
    c = CASES.get(cid)
    if c is None and JID_RE.match(str(cid)):
        f = CASE_DIR / f"{cid}.json"
        if f.exists():
            try:
                c = json.loads(f.read_text())
            except Exception:  # noqa
                return None
            CASES[cid] = c
    return c


def save(cid):
    c = CASES.get(cid)
    if not c or not JID_RE.match(str(cid)):
        return
    with LOCK:
        try:
            (CASE_DIR / f"{cid}.json").write_text(json.dumps(c, indent=2, default=str))
        except Exception:  # noqa
            pass


def stage(cid, s):
    CASES[cid]["stage"] = s
    save(cid)


def recall_lessons(use):
    if not (use and LESSONS.exists()):
        return "", []
    text = LESSONS.read_text().strip()
    lines = [re.sub(r"^[-*]\s*", "", l).strip() for l in text.splitlines() if l.strip()]
    return text, lines


def append_lesson(line):
    with LOCK:
        with open(LESSONS, "a") as f:
            f.write(line if line.endswith("\n") else line + "\n")


def me_call(prompt):
    return call_with_retry(call_claude, prompt, CLAUDE_MODEL)


def one_line(text):
    return (text or "").strip().splitlines()[0].strip().strip('"').strip() if (text or "").strip() else ""


# ---------------------------------------------------------------- prompts
def lesson_block(lessons):
    return f"\n\nLESSONS YOU WROTE AFTER EARLIER CASES (follow them):\n{lessons}\n" if lessons else ""


def digest_prompt(p, lessons):
    return f"""You are the follow-up agent for {p['company_me']}. You work for {p['my_role']}, who just came out of a meeting with {p['company_other']} and typed these raw notes.

YOUR SIDE'S AUTHORITY LIMITS: {p['authority'] or '(none stated)'}

RAW MEETING NOTES:
{p['notes']}
{lesson_block(lessons)}
Structure what happened. Use only facts that are in the notes — invent nothing. Anything that was raised but not settled belongs in open_items.

Output ONLY a JSON object:
{{"summary": string at most 60 words, "decisions": [string], "commitments": [{{"who": string, "what": string, "when": string}}], "open_items": [string], "risks": [string]}}
Each list item at most 25 words, plain prose, no markdown."""


def query_prompt(p):
    return f"""Below are meeting notes taken by someone at {p['company_me']} after meeting {p['company_other']}.

{p['notes']}

Write ONE web search query, at most 12 words, that would surface PUBLIC information about {p['company_other']}, its product, or the market for whatever is being bought or sold here. No quotes, no preamble, output the query and nothing else."""


def context_prompt(query, hits):
    src = "\n\n".join(f"[{i+1}] {h['url']}\n{h['title']}\n{h['snippet']}" for i, h in enumerate(hits))
    return f"""Below are public web search results for: {query}

Write at most TWO lines a salesperson could put next to their meeting notes as public context about the other side.
Rules: only state facts, names, numbers or dates that literally appear in the snippets below; if the snippets say nothing useful, write one line that says so plainly. End each line with its source domain in parentheses. At most 35 words per line. No markdown, no bullets, no preamble.

{src}"""


def first_turn_prompt(p, digest, options, lessons):
    opt = ""
    if options and options.get("status") == "done" and options.get("items"):
        items = options["items"]
        rec = options.get("recommended", 0)
        rec = rec if isinstance(rec, int) and 0 <= rec < len(items) else 0
        opt = "\n\nSTRATEGY OPTIONS FROM YOUR STRATEGY CREW (recommended: " + str(items[rec].get("name", "option " + str(rec + 1))) + "):\n" + \
              json.dumps(items, indent=2) + "\nSkeptic's note: " + str(options.get("skeptic_note", ""))
    return f"""You are the follow-up agent for {p['company_me']}. You are talking to {p['my_role']}, the person who was in the meeting with {p['company_other']}. You are about to agree the approach for the follow-up email together.

WHAT HAPPENED (your digest):
{json.dumps(digest, indent=2)}{opt}

YOUR SIDE'S AUTHORITY LIMITS: {p['authority'] or '(none stated)'}
{lesson_block(lessons)}
Write your opening message to that person. Name the approach you recommend and say in one sentence why, then ask exactly ONE question that you need answered before you can draft the email. At most 90 words. Plain prose, no greeting, no sign-off, no markdown, no bullet lists, no meta commentary. Output the message only."""


def chat_prompt(p, C, lessons, human_text):
    hist = "\n\n".join(f"[{m['role'].upper()}] {m['text']}" for m in C.get("chat", []))
    opts = C.get("options") or {}
    opt = json.dumps(opts.get("items", []), indent=2) if opts.get("status") == "done" else "(the strategy crew has no options yet)"
    ctx = "\n".join((C.get("context") or {}).get("lines", [])) or "(none)"
    return f"""You are the follow-up agent for {p['company_me']}, talking with {p['my_role']} about the follow-up to the meeting with {p['company_other']}. You are agreeing the approach before you write the email.

DIGEST:
{json.dumps(C.get('digest'), indent=2)}

PUBLIC CONTEXT: {ctx}

STRATEGY OPTIONS:
{opt}

STRATEGY AGREED SO FAR: {json.dumps(C.get('strategy'), indent=2)}

CONVERSATION SO FAR:
{hist}

THE PERSON JUST SAID: {human_text}

YOUR SIDE'S AUTHORITY LIMITS: {p['authority'] or '(none stated)'}
{lesson_block(lessons)}
Reply to them. Take their direction seriously — they were in the room. At most 120 words, plain prose, no markdown, no bullet lists, no sign-off, at most ONE question.
Also judge whether what they just said disagrees with, corrects or changes the approach you had proposed.

Output ONLY a JSON object:
{{"reply": string, "human_changed_something": true/false, "what_changed": string at most 20 words}}"""


def strategy_prompt(p, C):
    hist = "\n\n".join(f"[{m['role'].upper()}] {m['text']}" for m in C.get("chat", []))
    return f"""You are the follow-up agent for {p['company_me']}. Below is the whole conversation in which you and {p['my_role']} agreed the approach for the follow-up email to {p['company_other']}. The person has just locked it in.

DIGEST:
{json.dumps(C.get('digest'), indent=2)}

CONVERSATION:
{hist}

YOUR SIDE'S AUTHORITY LIMITS: {p['authority'] or '(none stated)'}

Write down the locked approach exactly as the person agreed it, in their direction, not yours. Output ONLY a JSON object:
{{"summary": string at most 50 words, "asks": [string], "tone": string at most 8 words, "do_not_concede": [string]}}"""


def draft_prompt(p, C, extra_lesson=""):
    ctx = "\n".join((C.get("context") or {}).get("lines", [])) or "(none)"
    ex = f"\n\nTHE PERSON REJECTED YOUR LAST DRAFT. THE LESSON FROM THAT: {extra_lesson}\nDo not repeat that mistake.\n" if extra_lesson else ""
    lessons = "\n".join(f"- {l}" for l in C.get("recalled", []))
    return f"""You are the follow-up agent for {p['company_me']}. Write the follow-up email to {p['company_other']} after the meeting.

DIGEST:
{json.dumps(C.get('digest'), indent=2)}

PUBLIC CONTEXT: {ctx}

THE LOCKED STRATEGY (follow it exactly):
{json.dumps(C.get('strategy'), indent=2)}

YOUR SIDE'S AUTHORITY LIMITS (never promise past them): {p['authority'] or '(none stated)'}
{lesson_block(lessons)}{ex}
Write it as the person would send it: plain prose, at most 180 words, no markdown, no headings, no bullet lists, no placeholders in brackets. Confirm in writing what was agreed, say plainly what still needs approval, and sign off with the person's role ({p['my_role']}) and company ({p['company_me']}).

Output ONLY a JSON object: {{"subject": string under 70 characters, "body": string}}"""


def edit_lessons_prompt(p, C):
    ed = []
    for e in C.get("edits", []):
        ed.append(f"[{e.get('stage')}] WHAT THE AGENT PRODUCED:\n{e.get('before','')}\n\nWHAT THE HUMAN CHANGED IT TO:\n{e.get('after','')}\n")
    return f"""A person at {p['company_me']} worked with you on the follow-up to a meeting with {p['company_other']}, then corrected you. Every place they touched is below: corrections in the strategy chat, and their edit of the email you drafted.

{chr(10).join(ed)}

Write the lessons you should carry into the NEXT case, so the next person has to change less. Write them as rules for yourself, general enough to apply to a different company and a different deal: no company names, no people's names, no amounts from this case.

Output ONLY a JSON object: {{"lessons": [string]}}   1 to 3 lessons, each at most 40 words, plain text, no quotes."""


def reject_lesson_prompt(C, reason):
    d = C.get("draft") or {}
    return f"""A person reviewed this follow-up email your agent drafted and REJECTED it outright.

SUBJECT: {d.get('subject','')}
BODY: {d.get('body','')}

THEIR REASON: {reason}

Write ONE lesson for your future self so the next draft does not get rejected the same way. At most 40 words, plain text, one line, no preamble, no quotes, no company names."""


# ---------------------------------------------------------------- the case thread
def web_context(cid, p):
    """You.com Search API → at most two public-context lines, written card-blind from the snippets alone."""
    stage(cid, "web context")
    query = one_line(me_call(query_prompt(p)))[:120]
    _src, data = search_api(query, 5)
    PROBE["youcom"] = {"ok": True, "detail": "key set, last call 200"}
    hits = flatten(data)
    if not hits:
        raise RuntimeError("You.com returned no results")
    raw = me_call(context_prompt(query, hits))
    lines = [re.sub(r"^[-*]\s*", "", l).strip() for l in raw.strip().splitlines() if l.strip()][:2]
    sources = []
    for h in hits:
        d = re.sub(r"^www\.", "", (h.get("url", "").split("/")[2] if "://" in h.get("url", "") else ""))
        if d and d not in sources:
            sources.append(d)
    return {"lines": lines, "sources": sources[:4], "query": query, "fetched": now_hm(), "via": "You.com Search API"}


def crew_options(cid, p):
    """CrewAI: strategist drafts 3 follow-up strategies, skeptic marks the risks and picks one."""
    C = CASES[cid]
    if not VENV_PY.exists() or not PROBE.get("crewai", {}).get("ok"):
        return {"status": "error", "items": [], "recommended": 0, "skeptic_note": "",
                "model": CREW_MODEL, "seconds": 0, "detail": PROBE.get("crewai", {}).get("detail", "no .venv")}
    inp = CASE_DIR / f"{cid}.options_in.json"
    outp = CASE_DIR / f"{cid}.options_out.json"
    inp.write_text(json.dumps({"digest": C.get("digest"), "context": C.get("context"), "company_me": p["company_me"],
                               "company_other": p["company_other"], "my_role": p["my_role"], "authority": p["authority"],
                               "lessons": C.get("recalled", []), "model": CREW_MODEL}, indent=2))
    env = dict(os.environ, CREWAI_DISABLE_TELEMETRY="true", CREWAI_TRACING_ENABLED="false", OTEL_SDK_DISABLED="true")
    try:
        subprocess.run([str(VENV_PY), str(BASE / "crew_options_job.py"), str(inp), str(outp)],
                       capture_output=True, text=True, timeout=150, env=env, cwd=str(BASE))
    except subprocess.TimeoutExpired:
        return {"status": "error", "items": [], "recommended": 0, "skeptic_note": "", "model": CREW_MODEL,
                "seconds": 150, "detail": "crew timed out at 150s"}
    res = json.loads(outp.read_text()) if outp.exists() else {"status": "error", "detail": "no output"}
    res.setdefault("items", [])
    res.setdefault("recommended", 0)
    res.setdefault("skeptic_note", "")
    res.setdefault("model", CREW_MODEL)
    res.setdefault("seconds", 0)
    return res


def case_thread(cid, p):
    C = CASES[cid]
    try:
        lessons_text, lessons_list = recall_lessons(p["use_lessons"])
        C["recalled"] = lessons_list
        n = one_mem_count() if p.get("use_lessons", True) else 0
        C["one_memory"] = {"recalled_records": n or 0, "learned": []}
        stage(cid, "digesting")

        digest = parse_json(me_call(digest_prompt(p, lessons_text)))
        if digest.get("parse_error"):
            raise RuntimeError("the digest did not come back as JSON")
        C["digest"] = {"summary": str(digest.get("summary", "")).strip(),
                       "decisions": [str(x) for x in (digest.get("decisions") or []) if str(x).strip()],
                       "commitments": [{"who": str(c.get("who", "")), "what": str(c.get("what", "")), "when": str(c.get("when", ""))}
                                       for c in (digest.get("commitments") or []) if isinstance(c, dict)],
                       "open_items": [str(x) for x in (digest.get("open_items") or []) if str(x).strip()],
                       "risks": [str(x) for x in (digest.get("risks") or []) if str(x).strip()]}
        save(cid)

        if p["ground"]:
            try:
                C["context"] = web_context(cid, p)
            except Exception as e:  # noqa
                C["context"] = None
                C["stage_note"] = f"public context unavailable ({str(e)[:120]})"
                PROBE["youcom"] = {"ok": bool(os.environ.get("YDC_API_KEY")), "detail": f"last call failed: {str(e)[:80]}"}
        save(cid)

        C["status"] = "discuss"
        C["options"] = {"status": "running", "items": [], "recommended": 0, "skeptic_note": "", "model": CREW_MODEL, "seconds": 0}
        stage(cid, "a strategy crew is drafting options")
        C["options"] = crew_options(cid, p)
        stage(cid, "agreeing the approach with you")

        text = me_call(first_turn_prompt(p, C["digest"], C["options"], lessons_text)).strip()
        C["chat"] = C.get("chat", []) + [{"role": "agent", "text": text, "at": now_hm()}]
        stage(cid, "waiting for you")
        save(cid)
    except Exception as e:  # noqa
        C["status"] = "error"
        C["error"] = str(e)[-500:]
        C["stage"] = "error"
        save(cid)


def lock_thread(cid, p):
    C = CASES[cid]
    try:
        s = parse_json(me_call(strategy_prompt(p, C)))
        C["strategy"] = {"locked": True, "summary": str(s.get("summary", "")).strip(),
                         "asks": [str(x) for x in (s.get("asks") or []) if str(x).strip()],
                         "tone": str(s.get("tone", "")).strip(),
                         "do_not_concede": [str(x) for x in (s.get("do_not_concede") or []) if str(x).strip()]}
        C["status"] = "drafting"
        stage(cid, "writing the draft")
        write_draft(cid, p)
        C["status"] = "draft"
        stage(cid, "your draft is ready to edit")
        save(cid)
    except Exception as e:  # noqa
        C["status"] = "error"
        C["error"] = str(e)[-500:]
        C["stage"] = "error"
        save(cid)


def write_draft(cid, p, extra_lesson=""):
    C = CASES[cid]
    d = parse_json(me_call(draft_prompt(p, C, extra_lesson)))
    if d.get("parse_error"):
        raise RuntimeError("the draft did not come back as JSON")
    C["draft"] = {"to": p["recipient_email"], "subject": str(d.get("subject", "")).strip()[:120],
                  "body": str(d.get("body", "")).strip()}
    save(cid)


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


# ---------------------------------------------------------------- harness replay (Daytona)
HARNESS_FILES = ["harness_job.py", "harness_in.json"]
HARNESS_CMD = "python3 harness_job.py harness_in.json"
HARNESS_IN = CASE_DIR / "_harness_in.json"


def harness_idle():
    return {"status": "waiting_for_key" if not os.environ.get("DAYTONA_API_KEY") else "idle", "sandbox_id": None,
            "exit_code": None, "output": "", "cases": 0, "files": HARNESS_FILES, "command": HARNESS_CMD}


def sent_cases():
    """Every case on disk that was actually sent — the harness only looks at draft vs final."""
    rows = []
    for f in CASE_DIR.glob("*.json"):
        if not JID_RE.match(f.stem):
            continue
        try:
            j = json.loads(f.read_text())
        except Exception:  # noqa
            continue
        if j.get("status") != "sent" or not (j.get("draft") and j.get("final")):
            continue
        rows.append({"id": j.get("id"), "created_at": j.get("created_at", ""),
                     "company_other": (j.get("params") or {}).get("company_other", ""),
                     "draft_body": (j.get("draft") or {}).get("body", ""),
                     "final_body": (j.get("final") or {}).get("body", "")})
    rows.sort(key=lambda r: r.get("created_at") or "")
    return rows


def replay_thread(cid):
    C = CASES[cid]
    rows = sent_cases()
    HARNESS_IN.write_text(json.dumps(rows, indent=2))
    try:
        r = subprocess.run([str(VENV_PY), str(BASE / "daytona_replay.py"), str(BASE / "harness_job.py"), str(HARNESS_IN)],
                           capture_output=True, text=True, timeout=240, cwd=str(BASE))
        out = parse_json(r.stdout)
        if out.get("parse_error"):
            C["harness"] = {"status": "error", "sandbox_id": None, "exit_code": None, "output": (r.stderr or r.stdout)[-1500:],
                            "cases": len(rows), "files": HARNESS_FILES, "command": HARNESS_CMD}
        else:
            C["harness"] = {"status": "done" if out.get("exit_code") == 0 else "error", "sandbox_id": out.get("sandbox_id"),
                            "exit_code": out.get("exit_code"), "output": (out.get("output") or "")[-4000:],
                            "cases": len(rows), "files": HARNESS_FILES, "command": HARNESS_CMD}
    except Exception as e:  # noqa
        C["harness"] = {"status": "error", "sandbox_id": None, "exit_code": None, "output": str(e)[:500],
                        "cases": len(rows), "files": HARNESS_FILES, "command": HARNESS_CMD}
    save(cid)


# ---------------------------------------------------------------- http
class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json"):
        # serialise under the same lock the writers use: a poll that lands mid-mutation still gets one whole case
        if isinstance(body, bytes):
            data = body
        else:
            with LOCK:
                data = json.dumps(body, default=str).encode()
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

    def _case(self, cid):
        """(case, error_response_sent) — every id goes through JID_RE first."""
        if not JID_RE.match(str(cid or "")):
            self._send(400, {"error": "bad id"})
            return None
        C = load_case(cid)
        if not C:
            self._send(404, {"error": "unknown case"})
            return None
        return C

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            return self._send(200, (ROOT / "index.html").read_bytes(), "text/html")
        if path == "/status":
            PROBE_DONE.wait(timeout=20)
            return self._send(200, {**PROBE,
                                    "models": {"agent": f"claude {CLAUDE_MODEL}", "crew": f"claude {CREW_MODEL}"},
                                    "recipient_default": ALLOWED[0] if ALLOWED else "",
                                    "allowed_recipients": ALLOWED})
        if path == "/case":
            cid = (parse_qs(urlparse(self.path).query).get("id") or [""])[0]
            C = self._case(cid)
            return None if C is None else self._send(200, C)
        if path == "/cases":
            out = []
            for f in CASE_DIR.glob("*.json"):
                if not JID_RE.match(f.stem):
                    continue
                try:
                    j = json.loads(f.read_text())
                except Exception:  # noqa
                    continue
                # the edit ratio is a property of a sent case: draft vs what the person actually sent
                ratio = next((e.get("ratio") for e in reversed(j.get("edits") or [])
                              if e.get("stage") == "draft" and isinstance(e.get("ratio"), (int, float))), None) \
                    if j.get("status") == "sent" else None
                out.append({"id": f.stem, "created_at": j.get("created_at"),
                            "company_other": (j.get("params") or {}).get("company_other", ""),
                            "status": j.get("status"), "edit_ratio": ratio})
            out.sort(key=lambda r: r.get("created_at") or "", reverse=True)
            return self._send(200, out[:40])
        if path == "/lessons":
            return self._send(200, {"lessons": LESSONS.read_text() if LESSONS.exists() else ""})
        return self._send(404, {"error": "not found"})

    def do_POST(self):
        path = self.path.split("?")[0]

        if path == "/case":
            with LOCK:
                cut = time.time() - 3600
                RUN_TIMES[:] = [t for t in RUN_TIMES if t > cut]
                if len(RUN_TIMES) >= RUN_LIMIT:
                    return self._send(429, {"error": f"case rate limit reached ({RUN_LIMIT} per hour); try again later"})
                RUN_TIMES.append(time.time())
            b = self._body()
            p = {"company_me": (b.get("company_me") or "Northline Supply").strip(),
                 "company_other": (b.get("company_other") or "").strip(),
                 "my_role": (b.get("my_role") or "account manager").strip(),
                 "authority": (b.get("authority") or "").strip(),
                 "notes": (b.get("notes") or "").strip(),
                 "use_lessons": bool(b.get("use_lessons", True)), "ground": bool(b.get("ground", True)),
                 "recipient_email": (b.get("recipient_email") or (ALLOWED[0] if ALLOWED else "")).strip()}
            if not p["notes"]:
                return self._send(400, {"error": "meeting notes are empty"})
            if not p["company_other"]:
                return self._send(400, {"error": "the other company is empty"})
            cid = uuid.uuid4().hex[:10]
            CASES[cid] = {"id": cid, "status": "digesting", "stage": "recalling lessons", "error": None,
                          "created": time.time(), "created_at": datetime.now().isoformat(timespec="seconds"),
                          "params": p, "recalled": [], "digest": None, "context": None,
                          "options": {"status": "running", "items": [], "recommended": 0, "skeptic_note": "",
                                      "model": CREW_MODEL, "seconds": 0},
                          "chat": [], "strategy": {"locked": False, "summary": "", "asks": [], "tone": "", "do_not_concede": []},
                          "draft": None, "final": None, "sent": None, "edits": [], "learned": [],
                          "one_memory": {"recalled_records": 0, "learned": []}, "harness": harness_idle()}
            save(cid)
            threading.Thread(target=case_thread, args=(cid, p), daemon=True).start()
            return self._send(200, {"id": cid})

        if path == "/chat":
            b = self._body()
            cid = str(b.get("id") or "")
            C = self._case(cid)
            if C is None:
                return None
            text = (b.get("text") or "").strip()
            if not text:
                return self._send(400, {"error": "empty message"})
            p = C["params"]
            before = next((m["text"] for m in reversed(C.get("chat", [])) if m["role"] == "agent"), "")
            lessons_text = "\n".join(f"- {l}" for l in C.get("recalled", []))
            try:
                out = parse_json(me_call(chat_prompt(p, C, lessons_text, text)))
            except Exception as e:  # noqa
                return self._send(502, {"error": str(e)[:300]})
            reply = str(out.get("reply") or "").strip()
            if not reply:
                return self._send(502, {"error": "the agent did not reply"})
            C["chat"] = C.get("chat", []) + [{"role": "human", "text": text, "at": now_hm()},
                                             {"role": "agent", "text": reply, "at": now_hm()}]
            if bool(out.get("human_changed_something")) and before:
                C["edits"] = C.get("edits", []) + [{"stage": "strategy", "before": before, "after": text, "ratio": round(1 - difflib.SequenceMatcher(None, before or "", text or "").ratio(), 4),
                                                    "at": now_hm(), "note": str(out.get("what_changed", ""))[:120]}]
            save(cid)
            return self._send(200, {"reply": reply})

        if path == "/lock":
            b = self._body()
            cid = str(b.get("id") or "")
            C = self._case(cid)
            if C is None:
                return None
            if C.get("status") in ("drafting",):
                return self._send(200, {"ok": True})
            C["strategy"]["locked"] = True
            C["status"] = "drafting"
            C["stage"] = "writing down the locked approach"
            save(cid)
            threading.Thread(target=lock_thread, args=(cid, C["params"]), daemon=True).start()
            return self._send(200, {"ok": True})

        if path == "/send":
            b = self._body()
            cid = str(b.get("id") or "")
            C = self._case(cid)
            if C is None:
                return None
            d = C.get("draft") or {}
            to = (b.get("to") or d.get("to") or "").strip()
            if to.lower() not in ALLOWED:
                return self._send(403, {"error": f"{to or '(empty)'} is not in FT_ALLOWED_RECIPIENTS. "
                                                 f"This demo may only email {', '.join(ALLOWED)}."})
            subject = (b.get("subject") or d.get("subject") or "Follow-up").strip()
            body = b.get("body") if b.get("body") is not None else d.get("body", "")
            if not str(body).strip():
                return self._send(400, {"error": "the email body is empty"})
            with LOCK:
                cut = time.time() - 3600
                SEND_TIMES[:] = [t for t in SEND_TIMES if t > cut]
                if len(SEND_TIMES) >= SEND_LIMIT:
                    return self._send(429, {"error": f"send rate limit reached ({SEND_LIMIT} per hour)"})
                SEND_TIMES.append(time.time())
            res = one_send(to, subject, body)
            if res.get("error"):
                with LOCK:
                    if SEND_TIMES:
                        SEND_TIMES.pop()
                return self._send(502, {"error": res["error"]})
            C["final"] = {"to": to, "subject": subject, "body": body}
            C["sent"] = res
            ratio = round(1 - difflib.SequenceMatcher(None, d.get("body", ""), body).ratio(), 4)
            C["edits"] = C.get("edits", []) + [{"stage": "draft", "before": d.get("body", ""), "after": body,
                                                "ratio": ratio, "at": now_hm()}]
            C["status"] = "sent"
            C["stage"] = "learning from your edits"
            save(cid)
            learned = []
            try:
                out = parse_json(me_call(edit_lessons_prompt(C["params"], C)))
                learned = [str(x).strip().strip('"') for x in (out.get("lessons") or []) if str(x).strip()][:3]
            except Exception as e:  # noqa
                C["stage_note"] = f"lesson write-up failed ({str(e)[:120]})"
            stages = sorted({str(e.get("stage")) for e in C.get("edits", []) if e.get("stage")})
            for l in learned:
                append_lesson(f"- (from your edits) {l}")
                mirror_lesson(cid, l, ["edit"] + stages)
            C["learned"] = learned
            C["stage"] = "sent"
            save(cid)
            return self._send(200, {"ok": True, "sent": res, "learned": learned})

        if path == "/reject":
            b = self._body()
            cid = str(b.get("id") or "")
            C = self._case(cid)
            if C is None:
                return None
            reason = (b.get("reason") or "").strip()
            if not reason:
                return self._send(400, {"error": "a reason is required"})
            try:
                learned = one_line(me_call(reject_lesson_prompt(C, reason)))
            except Exception:  # noqa
                learned = f"Do not draft it that way again: {reason}"[:200]
            append_lesson(f"- (from your rejection) {learned}")
            mirror_lesson(cid, learned, ["edit", "draft"])
            C["learned"] = list(C.get("learned") or []) + [learned]
            C["edits"] = C.get("edits", []) + [{"stage": "draft", "before": (C.get("draft") or {}).get("body", ""),
                                                "after": f"(rejected) {reason}", "ratio": 1.0, "at": now_hm()}]
            C["stage"] = "redrafting with your note"
            save(cid)

            def _redraft():
                try:
                    write_draft(cid, C["params"], learned)
                    C["stage"] = "your draft is ready to edit"
                except Exception as e:  # noqa
                    C["stage"] = f"redraft failed ({str(e)[:100]})"
                save(cid)
            threading.Thread(target=_redraft, daemon=True).start()
            return self._send(200, {"ok": True, "learned": learned})

        if path == "/replay":
            b = self._body()
            cid = str(b.get("id") or "")
            C = self._case(cid)
            if C is None:
                return None
            rows = sent_cases()
            if not os.environ.get("DAYTONA_API_KEY"):
                C["harness"] = {"status": "waiting_for_key", "sandbox_id": None, "exit_code": None,
                                "output": "DAYTONA_API_KEY is not set. The moment it lands in .env this runs for real, unchanged.",
                                "cases": len(rows), "files": HARNESS_FILES, "command": HARNESS_CMD}
                save(cid)
                return self._send(200, C["harness"])
            if (C.get("harness") or {}).get("status") == "running":
                return self._send(200, C["harness"])
            if not rows:
                C["harness"] = {"status": "error", "sandbox_id": None, "exit_code": None,
                                "output": "no sent cases yet — send one follow-up first", "cases": 0,
                                "files": HARNESS_FILES, "command": HARNESS_CMD}
                save(cid)
                return self._send(200, C["harness"])
            C["harness"] = {"status": "running", "sandbox_id": None, "exit_code": None, "output": "",
                            "cases": len(rows), "files": HARNESS_FILES, "command": HARNESS_CMD}
            save(cid)
            threading.Thread(target=replay_thread, args=(cid,), daemon=True).start()
            return self._send(200, C["harness"])

        if path == "/lessons/clear":
            tok = os.environ.get("FT_ADMIN_TOKEN")
            if not tok or self.headers.get("X-FT-Token") != tok:
                return self._send(403, {"error": "clearing lessons needs FT_ADMIN_TOKEN (header X-FT-Token)"})
            LESSONS.write_text("")
            return self._send(200, {"ok": True, "lessons": ""})
        return self._send(404, {"error": "not found"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8787"))
    threading.Thread(target=probe_all, daemon=True).start()
    print(f"Follow-Through app → http://localhost:{port}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", port), H).serve_forever()
