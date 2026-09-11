#!/usr/bin/env python3
"""CrewAI strategy crew for one case (sponsor tool #2). Runs under .venv/bin/python (py3.12).

    .venv/bin/python crew_options_job.py <in.json> <out.json>
in : {"digest":{…}, "context":{…}|null, "company_me":…, "company_other":…, "my_role":…, "authority":…, "lessons":[…]}
out: {"status":"done"|"error", "items":[{name,goal,tone,asks[],do_not_concede[],risk}], "recommended":0,
      "skeptic_note":"…", "model":"…", "seconds":n, "detail":"…"}

Two agents, sequential: a strategist drafts three follow-up strategies from the digest, then a
skeptic reads them cold, writes the risk of each and picks the one to recommend. The strategist
never gets to mark its own homework — that is the whole point of the second agent.
"""
import json, os, sys, time
from pathlib import Path

os.environ.setdefault("CREWAI_DISABLE_TELEMETRY", "true")
os.environ.setdefault("CREWAI_TRACING_ENABLED", "false")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def brief(cfg):
    ctx = cfg.get("context") or {}
    lines = "\n".join(ctx.get("lines") or []) or "(no public context)"
    lessons = "\n".join(f"- {l}" for l in (cfg.get("lessons") or [])) or "(none yet)"
    return f"""THE SIDE YOU WORK FOR: {cfg.get('company_me')} — the person is the {cfg.get('my_role')}.
THE OTHER SIDE: {cfg.get('company_other')}.
THEIR AUTHORITY LIMITS (a strategy that breaks these is worthless): {cfg.get('authority') or '(none stated)'}

DIGEST OF THE MEETING:
{json.dumps(cfg.get('digest'), indent=2)}

PUBLIC CONTEXT ABOUT THE OTHER SIDE:
{lines}

LESSONS FROM EARLIER CASES:
{lessons}"""


def strategist_prompt(cfg):
    return f"""{brief(cfg)}

Draft THREE genuinely different strategies for the follow-up message to {cfg.get('company_other')}. They must differ in what they lead with, not only in wording. Every strategy must stay inside the authority limits above.

Output ONLY a JSON object:
{{"items": [{{"name": string at most 5 words, "goal": string at most 25 words, "tone": string at most 8 words, "asks": [string], "do_not_concede": [string]}}]}}
Exactly three items. Each ask at most 15 words."""


def skeptic_prompt(cfg):
    return f"""{brief(cfg)}

The strategist just produced three strategies (they are in the previous task's output). Read them cold. For each one, write the single most likely way it goes wrong with this counterpart. Then pick the one you would actually send and say why in one sentence.

Keep each strategy's name, goal, tone, asks and do_not_concede exactly as the strategist wrote them, and add your "risk" to each.

Output ONLY a JSON object:
{{"items": [{{"name": string, "goal": string, "tone": string, "asks": [string], "do_not_concede": [string], "risk": string at most 25 words}}], "recommended": 0, "skeptic_note": string at most 35 words}}
"recommended" is the 0-based index of the strategy you would send."""


def clean(items):
    out = []
    for it in items if isinstance(items, list) else []:
        if not isinstance(it, dict):
            continue
        out.append({"name": str(it.get("name", "")).strip()[:60],
                    "goal": str(it.get("goal", "")).strip(),
                    "tone": str(it.get("tone", "")).strip()[:60],
                    "asks": [str(a).strip() for a in (it.get("asks") or []) if str(a).strip()],
                    "do_not_concede": [str(a).strip() for a in (it.get("do_not_concede") or []) if str(a).strip()],
                    "risk": str(it.get("risk", "")).strip()})
    return out


def main():
    inp, outp = Path(sys.argv[1]), Path(sys.argv[2])
    t0 = time.time()
    model_id = "sonnet"
    try:
        cfg = json.loads(inp.read_text())
        from audit_crew import make_llm
        from harness import parse_json
        from crewai import Agent, Crew, Task, Process
        override = (ROOT / ".crew_model").read_text().strip() if (ROOT / ".crew_model").exists() else ""
        model_id = os.environ.get("FT_CREW_MODEL_OVERRIDE") or override or os.environ.get("A2_CREW_LLM") or cfg.get("model") or "sonnet"
        llm = make_llm(model_id)
        strategist = Agent(
            role="Follow-up strategist",
            goal="Turn the record of a meeting into three genuinely different ways to play the follow-up, all inside the authority limits.",
            backstory="You have written thousands of follow-up messages after commercial meetings. You know a follow-up is a move, not a summary.",
            llm=llm, allow_delegation=False, verbose=False, max_iter=2,
        )
        skeptic = Agent(
            role="Deal skeptic",
            goal="Find how each proposed strategy goes wrong with this counterpart, then pick the one worth sending.",
            backstory="You have watched good follow-ups kill deals. You never accept a strategy because it sounds confident; you name the failure first.",
            llm=llm, allow_delegation=False, verbose=False, max_iter=2,
        )
        t1 = Task(description=strategist_prompt(cfg),
                  expected_output="A single JSON object with an 'items' array of exactly three strategies, nothing else.",
                  agent=strategist, name="draft_options")
        t2 = Task(description=skeptic_prompt(cfg),
                  expected_output="A single JSON object with 'items' (each with a risk), 'recommended' and 'skeptic_note', nothing else.",
                  agent=skeptic, name="mark_risks", context=[t1])
        crew = Crew(agents=[strategist, skeptic], tasks=[t1, t2], process=Process.sequential, verbose=False)
        crew.kickoff()

        def parsed(task):
            raw = task.output.raw if task.output else ""
            return parse_json(raw.split("Final Answer:")[-1] if "Final Answer:" in raw else raw)

        final = parsed(t2)
        items = clean(final.get("items"))
        if not items:  # the skeptic mangled the JSON — fall back to the strategist's three, without risks
            items = clean(parsed(t1).get("items"))
        rec = final.get("recommended", 0)
        rec = rec if isinstance(rec, int) and 0 <= rec < len(items) else 0
        res = {"status": "done" if items else "error", "framework": "crewai", "agents": 2, "tasks": 2,
               "items": items, "recommended": rec, "skeptic_note": str(final.get("skeptic_note", "")).strip(),
               "model": model_id, "seconds": round(time.time() - t0)}
        if not items:
            res["detail"] = "the crew returned no usable strategies"
        outp.write_text(json.dumps(res, indent=2))
    except Exception as e:  # noqa
        outp.write_text(json.dumps({"status": "error", "items": [], "recommended": 0, "skeptic_note": "",
                                    "model": model_id, "detail": str(e)[:300], "seconds": round(time.time() - t0)}))
    print(outp.read_text())


if __name__ == "__main__":
    main()
