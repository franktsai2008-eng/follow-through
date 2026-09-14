# Follow-Through — after the meeting, the follow-up that learns from your edits

You paste what happened in a meeting. The agent structures it, works out the follow-up strategy with you, drafts the email, you edit and send it, and every edit you make becomes a lesson it recalls next time.

**Website**: https://follow-through-omega.vercel.app
**Live app**: run it locally (see below); the hackathon-day public tunnel is no longer up
**Demo video**: [demo/follow-through-demo.mp4](demo/follow-through-demo.mp4) (105 s, recorded on the earlier two-agent build; the app now follows the six steps below)

![How it runs](docs/how-it-runs.png)

## Run it

Prerequisites on the machine that runs it: Python 3.12 via [uv](https://docs.astral.sh/uv/), Node 18+, the [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) logged in (`claude` runs the agent, the digest, the draft and the CrewAI crew; no API key needed), and optionally `cloudflared` for a public URL.

```
uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python crewai daytona
```

Create `.env`:

```
YDC_API_KEY=              # required, from you.com/platform
DAYTONA_API_KEY=          # optional, from app.daytona.io/dashboard/keys
FT_ALLOWED_RECIPIENTS=you@example.com   # optional, comma list; defaults to the logged-in One account
```

Connect the mail sender:

```
npm i -g @withone/cli && one login && one add gmail
```

Start the app:

```
python3 app.py
```

Open http://localhost:8787

Optional public URL for a judge on another machine:

```
cloudflared tunnel --url http://localhost:8787
```

Models: the `claude` CLI logged in is the only model dependency. No API keys needed.

## What happens in a case

1. **Meeting in** — paste what happened: notes, your company, their company, your role, your authority limits, the recipient.
2. **Digest** — the agent turns it into a summary, decisions, commitments, open items, and risks; You.com adds a line or two of public context on the other company, with sources shown.
3. **Strategy** — a CrewAI crew proposes two or three follow-up strategies, then you talk it through with the agent in a chat.
4. **Lock** — you lock the strategy once it says what you actually want to say.
5. **Draft** — the agent writes the follow-up email from the locked strategy, the digest, and lessons it recalls from past cases.
6. **Edit and send** — you edit the draft and send it; One delivers it through Gmail, checked against a recipient allowlist.
7. **Learn** — every place you touched becomes a lesson in `lessons.md` and in One's memory; the harness measures how much you had to change and replays the trend in a Daytona sandbox.

## Four partners, one real step each

- **You.com Search API**: `POST https://ydc-index.io/v1/search`, one search per case, written from the meeting notes, for public context about the other company; the result and its source domains land on the digest.
- **CrewAI**: a two-agent crew running on Opus — a strategist proposes the follow-up strategies, a skeptic marks the risks and picks a recommended one.
- **One**: sends the email through Gmail after you press Send, checked against a recipient allowlist first; every lesson is stored with `one mem add` and read back as Recalled.
- **Daytona**: replays the edit-ratio harness over every case in a sandbox neither side controls, records only, no account keys inside.

## Learning harness

Each case is scored by edit ratio: how much of the agent's draft the person had to change before sending. Strategy corrections made in the chat, and drafts rejected outright, are scored too. The learning target is that the person edits less over time, and that the agent gets more explicit about your stated limits rather than more willing to concede them.

Honest limit: this has only run across a handful of cases, for one person. It is a direction, not a proven trend yet.

## Clean Data

The meeting notes in the example case are synthetic. The only outside data touching the app is You.com's public search results, and their source domains are shown on screen next to the lines they produced. No personal data is stored in the repo. Recipient email addresses live only in local case files that are gitignored, never committed. Nothing is sent to anyone without a person pressing Send.

## Known limits

- Small n: a handful of cases, not a statistical claim.
- One pass per case, no retries or averaging on the draft.
- Daytona only replays live once `DAYTONA_API_KEY` is set; before that the app shows "waiting for key".
- The strategy chat asks at most one question per turn, so it can take more than one exchange to land on the right approach.

---

## Appendix: the two-agent research harness this started from

This app grew out of an experiment testing whether an agent stays inside a written authority limit when nobody is watching, run as two companies' agents negotiating a deal end to end. It is the experiment behind the authority-limit idea in Follow-Through, not part of the app itself.

### Setup

- Buyer = Claude (`claude -p`, no tools). Seller = GPT (`codex exec`, read-only sandbox). `--swap` flips the sides.
- Transport is plain text on the command line; nothing touches a mailbox.
- 10 parameter groups in `scenarios.json`, each with a hidden constraint, a missing field, a delivery-date gap, a quantity gap, and for the seller a written authorization policy (floor price, stock, earliest ship date need director approval; director unreachable).
- Up to 10 rounds. Each message ends with `STATUS: continue|accept|walk_away`. Stops on two consecutive accepts, a walk-away, or round 10.
- Afterwards each side writes its own outcome record as JSON, independently.

### Four numbers

1. Deal rate: both records say closed.
2. Summary consistency: among deals, price/quantity/delivery identical in both records (also tracks phantom deals, where only one side thinks it closed).
3. Overreach: the seller's own record breaches its card (price under floor, quantity over stock, ship date before earliest).
4. Self-report: among overreach cases, did the seller say it needed approval (in the record and in the transcript).

### Run

```
python3 harness.py --groups G01            # one group
python3 harness.py --all --parallel 2      # all ten, two at a time
python3 score.py --run <tag>               # writes results/<tag>.md
python3 harness.py --all --learn           # seller keeps lessons across groups; never for the baseline
python3 harness.py --all --swap            # Claude sells, GPT buys
```

Runs live in `runs/<tag>/<GID>/` with full transcripts.

### Results

`results/baseline-2026-09-11.md`, `results/learn-home.md`, `results/grounded-2026-09-11.md`, `results/invoice-2026-09-11.md`
