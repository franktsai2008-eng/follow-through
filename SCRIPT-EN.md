# What to say — Build with YOU hackathon, 2026-09-11

Everything here starts with a normal hackathon question and gets to the real one in two or three steps. Ask, listen, then go one step deeper. Never lead with your experiment. Never say you run a business here.

## If someone asks who you are
I'm a first-year at Fordham. Before I came here I built automation for small companies in Taiwan. Today I'm just here to build and learn.

## Tom Haddock (CrewAI booth) — three steps
Step 1, normal question:
Hi, I'm Frank. What kind of teams are you deploying with these days?

Step 2, one step in (pick whichever fits his answer):
- Do any of them let the agent talk to people outside the company, like a supplier or a customer? Or is it all internal for now?
- What do those teams get nervous about before they let it go live?

Step 3, the real one, said casually:
- When it does talk to someone outside, how do they keep it from promising something it shouldn't?
- And if the two sides remember the deal differently afterwards, what do they look at?

Only if he's chatty, share yours as a story, not a pitch:
Funny thing, I ran ten of these last night, two agents doing a purchase in plain text. The seller never once overstepped. It just walked away. The buyer was the one who quietly gave up its own rule.

Closing (the only ask):
Who else here should I talk to about this?

If he asks what you're building:
Nothing yet, it's an experiment. I'm trying to work out whether the hard part is permissions or the paper trail.

## Jacob Rissman (One) — same shape
1. What's the most common thing people ask One to handle that you don't do yet?
2. Does anyone ask about agents that belong to two different companies? Whose permissions win?
3. Has one of those ever gone wrong on a customer?

## Vedran Jukic (Daytona)
1. What's the weirdest thing someone has run in a sandbox?
2. Has anyone ever run another company's agent in there, rather than their own?
3. What would the other company need to see before they'd trust that?

## Michael Munson (Clean Data Alliance)
1. What's the first thing the alliance is trying to standardize?
2. Does that cover what two organizations' systems agree on, or is it more about data quality?
3. Who keeps the record when two companies' AIs agree on something?

## Any builder in the room — three steps
1. What are you building?
2. Does it talk to anyone outside your team, or is it all your own data?
3. Would you let it send something to a customer without reading it first? What would you need to see?

Step 3 is the whole point. "No, never" plus what they'd need is a full answer. Write it down in their words.

## What each answer tells you
- "All internal for now" or "never" = the cross-company case hasn't happened yet for them. The follow-up "what would you need" is the data.
- "We put a human in front of it" = authorization is the worry.
- "We log everything" or "the CRM is the truth" = the record is the worry.
- "Email is fine" = they don't feel a missing layer. Write that down too, it counts.

## Demo narration, 60 seconds
Two companies' agents, one plain-text deal. Buyer on Claude, seller on GPT, each with a private card, a hidden constraint, a written authority limit, and no director to call. Ten cases, one pass each, a third model auditing blind. The seller never crossed its line. It walked away instead. Records matched, except one deal written in cases on one side and reams on the other. The one breach was the buyer, signing ten days past its own deadline. Then the same ten cases with the seller keeping lessons: it names its limit in ten of ten instead of eight, still zero past its line, and in the one case where the buyer was about to sign a bad deal, it now walks away instead of letting it happen. Price context from You.com's live search sits on each card. Next: fifty cases, and swap the models.

## If a judge asks "where are the four tools", 20 seconds
Each one does one job. You.com puts one line of public price context on both cards, next to the authority limit, so we can see which one the agent obeys. CrewAI runs the blind audit as a crew: one auditor, one task per side. The two negotiators are not in that crew on purpose, they belong to two companies. Daytona replays the scoring in a box neither company controls: only the records go in, no login. One carries the receipt out: both records, both verdicts, the transcript hash, sent through One's MCP so the harness never holds a mailbox token. The gap between those four is the experiment: nobody's tool decides what two companies' agents may promise each other.
