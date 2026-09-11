# Follow-Through — build plan v2 (2026-09-11 14:45, Fable plans / Opus+Sonnet execute)

Deadline: final submission 16:15. Tom finals 17:10. Every minute here is real.

## 0. Locked decisions (Frank, 14:40)
- One sends the follow-up email for real after a human presses Approve. The human can edit recipient, subject and body before pressing it. (1A + edit)
- Visual direction: space-black, Grok-style. Pure black, white text, hairlines, one cool accent for the counterparty. No orange, no lime, no gradients.
- Daytona key arrives later. Code is wired and tested in dry-run; the UI shows "waiting for key" until `DAYTONA_API_KEY` lands in `.env`, then it goes live with zero code change.
- Video: Claude records a 90-second real run and burns captions; Frank uploads to YouTube (unlisted is fine) and pastes the link.
- Roles: Fable plans and verifies. Opus agents build backend and frontend in parallel. Sonnet does README + 200 words.
- Not built today: lessons in `one mem` (its embedded postgres does not start on this Mac; 5-minute retry only), CrewAI through One MCP, Daytona through One.

## 1. What the judges score, and where each point lands
| Criterion | Where it lands in the app |
|---|---|
| Completed the loop (changed a real system) | Approve → One sends Gmail, message id shown. Lesson written to `app/lessons.md` and recalled on the next run. Reject → reason becomes a lesson. Daytona sandbox created, ran, deleted (once key lands). |
| Technical implementation | Four partner calls in code, action ids resolved at runtime, secrets in `.env` only, recipient allowlist, README setup reproducible. |
| Innovation | Two companies' agents, written authority line, two records of one deal, cross-model blind audit, learning that makes the agent more explicit about its limit, not more willing to close. |
| Impact | The tail of every B2B deal: confirm, chase delivery, chase money. |
| Presentation | 1–3 min YouTube video of a real run, README, 200-word description. |
| Clean Data | README section: synthetic task cards only; the only outside data is You.com public results with source domains shown; no personal data stored; recipient addresses stay in local gitignored run files. |

## 2. Architecture (unchanged core, four real edges)
```
 browser (app/index.html)  ──HTTP──  app.py (stdlib http.server, port 8787, python 3.14)
                                        │
   your agent = claude -p (sonnet)      │   their agent = codex exec (gpt-5.6-sol)   [both already work, 2.5s / 5.6s per turn]
                                        │
   ① You.com Search API  ─ reference line on both cards (direct HTTPS, YDC_API_KEY)
   ② CrewAI audit crew   ─ subprocess `.venv/bin/python crew_audit_job.py` (py3.12; crewai 1.15.21; LLM = claude -p)
   ③ One                 ─ subprocess `one --agent actions execute gmail <id> <key> -d {...}`  (ids resolved at startup)
   ④ Daytona             ─ `daytona` SDK in .venv (subprocess `.venv/bin/python replay_job.py --job <id>`); waiting_for_key until env has the key
```
Rule: app.py stays stdlib-only and runs on the system python; anything that needs the venv runs as a subprocess with a JSON file in and JSON out.

## 3. API contract (backend builds it, frontend consumes it; both agents work from this)
### GET /status
```json
{"youcom":{"ok":true,"detail":"key set, last call 200"},
 "one":{"ok":true,"detail":"gmail operational","connection":"live::gmail::default::…a74"},
 "crewai":{"ok":true,"detail":"1.15.21 in .venv"},
 "daytona":{"ok":false,"detail":"waiting for key"},
 "models":{"me":"claude sonnet","other":"gpt-5.6-sol"}}
```
### POST /run  → {"id": "<10 hex>"}
Body: `{company_me, company_other, flow, my_card, other_card, other_model:"gpt"|"claude", max_rounds:2..8, use_lessons:bool, ground:bool, recipient_email}`
### GET /job?id=… → the job object (polled every 1.5 s)
```json
{"status":"running|done|error","stage":"…","end":"both_accepted|me_walked_away|other_walked_away|max_rounds","error":"…",
 "params":{…as posted…},
 "recalled":["lesson 1","lesson 2"],
 "reference":{"line":"…≤45 words…","sources":["made-in-china.com","globalsources.com"],"query":"…","fetched":"14:52","via":"You.com Search API","hits":[{"title":"…","url":"…"}]} ,
 "other_card":"…",
 "messages":[{"side":"me|other","round":1,"text":"…","status":"continue|accept|walk_away","badge":"within authority|names its limit|accepts|walked away"}],
 "memos":{"me":"…","other":"…"},
 "records":{"me":{"deal_closed":true,"amount_or_price":"…","quantity_or_scope":"…","date_or_delivery":"…","payment_terms":"…","conditional_items":"…"},"other":{…}},
 "record_diff":{"amount_or_price":"identical|equivalent|conflict|missing","quantity_or_scope":"…","date_or_delivery":"…","payment_terms":"…"},
 "audit":{"me":{"binding_deal_in_exchange":bool,"committed_beyond_authority":bool,"beyond_authority_evidence":"…","flagged_need_for_approval":bool,"flag_evidence":"…","left_ambiguous":"…"},"other":{…}},
 "crew_audit":{"status":"running|done|error|skipped","me":{…same keys…},"other":{…},"agrees":{"me":true,"other":false}},
 "actions":[{"action":"…","needs_approval":true,"why":"…","to":"…","subject":"…","draft":"…","state":"proposed|sent|rejected","sent":{"message_id":"…","thread_id":"…","at":"15:02"},"reject_reason":"…"}],
 "learned":"…one line…","lessons_now":"…file text…",
 "replay":{"status":"waiting_for_key|running|done|error","sandbox_id":"…","exit_code":0,"output":"…","files":["job.json","replay_job.py"],"command":"python3 replay_job.py job.json"}}
```
### POST /approve `{id, i, to, subject, body}` → `{ok:true, sent:{message_id,thread_id,at}}` or `{error}`
- Executes One Send Email. Recipient must be in `FT_ALLOWED_RECIPIENTS` (comma list in `.env`, default the owner's address); otherwise 403 with a clear message. Max 10 sends per hour per process.
### POST /reject `{id, i, reason}` → `{ok:true, learned:"…"}`  (writes "- (human feedback) …" to lessons.md)
### POST /replay `{id}` → the `replay` object above (waiting_for_key when no key)
### GET /lessons, POST /lessons/clear, GET /runs → `[{id, created, flow, company_me, company_other, end, status}]`

## 4. Work packages
### WP1 backend — Opus agent, 35 min, files: app.py, crew_audit_job.py (new), replay_job.py (new), grounding_app.py (new or reuse grounding.py functions)
1. `/status`: You.com = key present (+ cache last call code); One = run `one --agent list`, pick `platform=="gmail"` and `state=="operational"`, keep key; CrewAI = `.venv/bin/python -c "import crewai"` once at startup; Daytona = env key present.
2. Resolve One action id at startup: `one --agent actions search gmail "send email" -t execute`, pick the row with `path == "/v1/gmail/send-email"`. Never hardcode. Cache in memory.
3. `/run` additions: company names, recipient, `ground`. If `ground`: one claude call writes a ≤12-word public-price search query from `my_card`; call `https://ydc-index.io/v1/search` (POST, `X-API-Key`, `{"query","count":5}`, `User-Agent: curl/8.7.1`); a card-blind claude call compresses hits to one ≤45-word line that only uses numbers present in the snippets and names its source domains; inject the same line into BOTH cards as `PUBLIC MARKET REFERENCE (from a You.com search, same line on both cards; sources: …): …`. Store `reference`. On any You.com failure: `reference=null`, run continues, stage note "reference unavailable".
4. `recalled` = lessons list at start (if use_lessons). Keep the existing STYLE / prompts. Company names go into the prompts as "You represent {company}. The other side represents {other company}."
5. After the exchange: memos, records (existing) + `record_diff`: one claude call comparing the two records field by field → identical / equivalent (same meaning, different wording or unit) / conflict / missing. Then single-model audit (existing). Then spawn `crew_audit_job.py` as a background thread (subprocess, JSON in/out) so the UI is not blocked; `crew_audit.status` goes running → done; `agrees` = both booleans (`committed_beyond_authority`, `flagged_need_for_approval`) equal.
6. Actions: keep the prompt but require `to` (default recipient), `subject`, `draft` for message actions; state `proposed`.
7. `/approve`: allowlist check, then `one --agent actions execute gmail <id> <key> -d '{"to":…, "subject":…, "body":…}'` via subprocess with a 60 s timeout; parse stdout JSON; store `sent` (message id from the response, whatever field One returns; keep the raw response under `sent.raw`). Persist job JSON to `app/runs/<id>.json` after every state change.
8. `/reject`: claude call turns the reason into one ≤40-word lesson; append `- (human feedback) …` to lessons.md; store `reject_reason`, state `rejected`, return `learned`.
9. `replay_job.py`: pure python, no third-party imports. Input: job JSON path. Output: a text table (records field by field with identical/equivalent/conflict from `record_diff`; both audits; sha256 of the messages array) and exit 0. `/replay`: if no `DAYTONA_API_KEY` → `waiting_for_key` with `files` and `command`. Else in a thread: `Daytona(DaytonaConfig(api_key=…))`, `create()`, `fs.upload_files([FileUpload(source=bytes, destination="/home/daytona/ft/…")])`, `process.exec("python3 /home/daytona/ft/replay_job.py /home/daytona/ft/job.json", timeout=120)`, store exit code + result, `delete()` in `finally`. Do not pass cpu/memory/disk.
10. `crew_audit_job.py`: run with `.venv/bin/python`; reuse `make_llm` from audit_crew.py; one auditor agent, two tasks (first party, second party), same JSON schema as `audit_prompt`; env `CREWAI_DISABLE_TELEMETRY=true`. Time budget ≤60 s; on failure write `{"status":"error"}`.
11. Keep `--learn` semantics: `learned` written after every run, appended to lessons.md.
12. Self-test before returning: start server on a spare port, POST a short run (max_rounds 2, other_model claude to save time), poll to done, call /reject with a reason, call /replay (expect waiting_for_key), GET /status. Do NOT call /approve in the self-test (that sends real email); instead unit-test the allowlist path with a disallowed address and expect 403.

### WP2 frontend — Opus agent, 40 min, file: app/index.html (single file, no build step, Google Fonts only external)
Design tokens (Grok space-black):
```
--bg:#000000; --surface:#0a0a0a; --surface2:#111111; --hairline:#1f1f1f; --hairline2:#2a2a2a;
--ink:#f2f2f2; --muted:#8c8c8c; --faint:#4d4d4d;
--me:#ffffff;  /* your agent marker */   --them:#6b7cff; /* their agent marker, indigo */
--ok:#3ddc84; --warn:#ffb020; --bad:#ff5c5c;
font UI: "Inter", system-ui;  font record: "JetBrains Mono", ui-monospace   (both via fonts.googleapis.com)
radius: 8 / 12 / 16, pills 999;  spacing: 4 8 12 16 24 32 48;  no shadows, no gradients, 1px hairlines only
motion: transform/opacity only, 160ms ease-out, @media (prefers-reduced-motion) → none
contrast: body text ≥ 4.5:1 (muted #8c8c8c on #000 passes); faint only for decoration
```
Shell: sticky 56px top bar (wordmark "Follow-Through", tagline "the tail of a deal, run by each side's own agent"; center run-state pill; right four tool dots from /status with label on hover/tap: You.com, CrewAI, One, Daytona; green = ok, amber = waiting for key). Under it a grid `320px 1fr 400px` at ≥1280, `320px 1fr` at ≥900 with the right rail stacking below the thread, one column below 900. Body never scrolls horizontally; long text wraps; mono blocks scroll inside.
Left rail (the form): company names (two inputs, defaults "Northline Procurement" / "Harbor Packaging"), flow presets as segmented pills (agree a price / chase an invoice / chase a delivery / blank — keep the three preset card texts already in the file), your card textarea, "their card" collapsible, recipient email (default from /status or `franktsai.2008@gmail.com`), their agent model select (GPT via Codex / Claude), rounds (2–8, default 6), two toggles (use lessons from earlier cases; ground both cards with a You.com search — default on), Run (white pill, black text). Below: "Recalled" block: the lessons that will be used, numbered, with a count chip; "clear lessons" ghost button. Bottom: "Past runs" list from /runs; clicking loads that job into the main view.
Center (the thread): if `reference` present, a mono card at the top: label "PUBLIC MARKET REFERENCE · You.com Search API · fetched 14:52", the line, source domains as chips, "same line on both cards". Messages as chat rows: your agent left-aligned, 2px left border `--me`, header "Northline · your agent · Claude · round 1"; their agent right-aligned with `--them` border, header "Harbor · their agent · GPT · round 1". Badge chips per message: within authority (muted), names its limit (warn), accepts (ok), walked away (bad). While running: a row "their agent is writing…" with a three-dot opacity pulse. On done: end banner (both accepted / walked away / round limit). On error: red banner with the message.
Right rail (stacked cards, each with a small mono eyebrow):
1. RECORDS — two columns "your record / their record", five rows; row background tint by `record_diff` (identical ok, equivalent warn, conflict bad, missing faint) with a one-word chip at row end.
2. BLIND AUDIT — table: rows your agent / their agent; columns single model / CrewAI crew; cells show "beyond authority: no" and "named its limit: yes" as chips; a "disagree" chip in bad when `agrees` is false; crew column shows "running…" until done, "not run" if skipped.
3. NEXT ACTIONS — one card per action: title, "requires your approval" chip, why; for message actions an editable To input, Subject input, Body textarea prefilled with the draft; buttons: Approve & send (white pill) and Reject (ghost). After approve: card turns to a receipt: "sent via One · Gmail message id … · 15:02" in ok. After reject: reveals a reason input + Submit; on response shows "Learned: …" in warn. Disabled states while in flight.
4. THIRD-PARTY REPLAY — copy: "Replay the scoring in a box neither company controls. Only the records go in." Button "Replay in a Daytona sandbox". States: waiting for key (shows the file list and command it would run), running, done (exit code chip + mono output block), error.
5. LEARNED — the lesson written after this case, larger text, mono eyebrow "LEARNED · used on the next run".
Also: `Recalled:` and `Learned:` must be visible without scrolling on a 1440×900 screen once a run is done (judges look for exactly these two lines).
Empty state before the first run: the thread area shows three short lines explaining the loop (type your side → two agents talk → you approve what leaves) and nothing else.
No emoji, no icons libraries; use text chips and 1px lines. Escape all model text (`replace(/</g,'&lt;')`). Keep everything in one file under 40 KB.
Self-test: open against the running backend (port 8787) with playwright-cli or the browse skill at 1440×900 and 390×844, run one short case (2 rounds, Claude as the other model), screenshot both viewports to `app/shots/`. Then run impeccable-detect on the file and fix everything it flags.

### WP3 docs — Sonnet agent, 15 min, files: README.md, REPORT-200.md, .gitignore (already has .env)
- README top section "Run it" — exact commands: `.venv` creation with uv (py3.12), `pip install crewai daytona`, `.env` keys (YDC_API_KEY, DAYTONA_API_KEY optional, FT_ALLOWED_RECIPIENTS), `one login` + `one add gmail`, `python3 app.py`, optional `cloudflared tunnel --url http://localhost:8787`. Then "What happens in a run" (six steps, one line each), "Four partners, one step each", "Clean Data" paragraph, "Known limits" (n small, one pass, Daytona live only with key).
- REPORT-200.md: exactly ≤200 words: problem, tech stack, API use (name all four partners and the You.com endpoint). Run `python3 ~/.claude/skills/slopmonster/tools/deslop.py` on it; must score 5/5; rewrite until it does.
- Do not touch app.py or index.html.

### WP4 integrate + verify — Fable, 15 min (15:30–15:45)
- Restart app.py, keep the same tunnel. Run one full case through the public URL with GPT as the other side and grounding on. Approve one action to the owner's address (this is the one real send; it is the demo proof). Reject one action with a reason; confirm the lesson appears in Recalled on the next run start.
- `impeccable-detect` on index.html: 0 findings or fixed. Security six points: keys server-side only; no DB; recipient allowlist; no PII in repo (runs/ gitignored); rate limit on sends; anyone with the tunnel URL can start runs but cannot mail outside the allowlist.
- Fresh-context refute check (one Opus agent, read-only): "does the app actually change a real system, can a judge reproduce it from README, where does it break in the first 60 seconds".
- Commit + push.

### WP5 video + submit — 15:45–16:05
- playwright-cli / browse: record the browser at 1280×720 doing one real run (rounds 4, grounding on, approve → sent, learned line), ~90 s. Burn six captions with the existing PIL approach (`demo/` has the pattern) or leave raw if behind. Hand the mp4 to Frank → YouTube unlisted → link into README and the form.
- Submission form: repo URL, video URL, REPORT-200 text.

## 5. Timeline and kill order
14:45 dispatch WP1 + WP2 + WP3 in parallel → 15:25 WP1/WP2 back → 15:30–15:45 WP4 → 15:45–16:05 WP5 → 16:05 buffer → 16:15 submit.
Kill order if behind: Past-runs list → CrewAI in-app (page falls back to the three offline crew results already in results/) → reject-to-lesson → video captions. Never cut: One real send, You.com line, Recalled/Learned lines, the video itself, the 200 words.

## 6. Definition of done
- [ ] A judge can open the tunnel URL, type a card, watch two agents talk, see two records, both audits, edit and approve an action, and a real email lands in the recipient's inbox with the id shown on screen.
- [ ] The second run shows `Recalled:` with the first run's lesson; a rejection shows `Learned:`.
- [ ] /status shows You.com, CrewAI, One green; Daytona amber "waiting for key" (green the moment the key is in .env).
- [ ] impeccable-detect clean; no key in the frontend; runs/ and .env gitignored; recipient allowlist on.
- [ ] README setup reproducible; REPORT-200 at 5/5; YouTube link in README; repo pushed.
