# What to say — Build with YOU hackathon, 2026-09-11

Rule for every line: experiment first, identity second. No "platform", "integration layer", "neutral", "every company", "meeting". Never say you run a business here.

## Who you are, if asked (F-1 safe, truthful)
I'm a first-year at Fordham. Before I came here I built automation for small companies in Taiwan. This is a student experiment. I'm not selling anything.

## Tom Haddock (CrewAI, Head of Forward Deployed Engineering) — 90 seconds
Hi Tom, I'm Frank. Two questions, ninety seconds. Last night I ran ten cases of one company's agent negotiating with another company's agent in plain text, Claude on one side, GPT on the other, each with a written authority limit and an unreachable director. The seller never once crossed its line. It walked away five times instead. The thing that broke was on the buyer side and in the records. My question: the last time one of your customers wanted an agent to talk to something outside their own company, what did their legal or ops people make them add before it went live?

Second question, if he is still there:
When two sides disagree afterwards about what was agreed, what do they show each other?

Hook if you need one to start: Your MCP in the Wild talk was on agents that hold up in production. What breaks first?

## Branches
- He's not here (ask the You.com people): Is Tom Haddock here all day, or for the finals? Either way, same question for you. You see the same customers.
- Marketing answer ("CrewAI handles that with guardrails"): Right, but guardrails sit inside one company. When the counterparty is a different company with its own agent, who writes the limit, and has one ever been crossed in a customer deployment?
- "So what's your product?": Nothing yet. It's an experiment, not a company. I'm trying to find out whether the missing piece is authorization or the record. (Stop there. Add the Taiwan customs line only if he asks again.)
- "Just use CrewAI Flows": Fair. Flows give me orchestration inside one company. My ten cases are two separate processes that never share state. Can Flows be the other side's process too, or is that always a human?
- "Never happens, there's always a human in the loop": That's the answer I most want. What was the first thing a customer let an agent send outside the company without a human reading it?
- "Email plus an LLM is enough, you don't need anything": Say thank you and write it down word for word. That is evidence, not an argument to win.

## Showing the numbers (only if he leans in. phone open on results/baseline-2026-09-11.md)
Ten cases. Five closed on both sides, all four where a legal deal existed and one of the six where none did. Zero phantom deals. Four of five records identical. the fifth was the same deal written in cases on one side and reams on the other. Seller crossed its written authority zero times and said "needs my director" in eight of ten. The one breach was the buyer: its card said thirty days, eight hundred dollars a day late, and it signed for day forty and called it fine. Does that match what you see in production?

## The ask (one, zero cost, same room)
One ask: is there anyone in this room you'd point this question at? I'll go ask them.
If he's warm: Can I send you one page when I've run fifty cases? No reply needed.
(15-minute call and customer intro: only after the write-up is sent, never today.)

## Same question, other sponsors
- Jacob Rissman (One, Head of GTM & Revenue): You wrote that the hard test starts when an agent has to authenticate and call tools with the right permissions. When the agent on the other side belongs to a different company, who holds the permission? Has a customer asked you for that yet?
- Vedran Jukic (Daytona, CTO): Launch Week 10 shipped Secrets Manager and egress control. If company A's agent has to run something on company B's behalf, does anyone sandbox that today, or is it always an API call? What would B need to see first?
- Michael Munson (Clean Data Alliance): When two organizations' systems agree on something, what counts as the record? Is anyone standardizing that for agents, or is it still whatever each side's CRM says?

## The ten builders (≤25 words, then the rescue question)
Has your agent ever had to deal with someone outside your company? What broke: getting a reply, knowing what it could promise, or proving it later?
If "never": What would have to be true before you'd let it reply outside the company without you reading it first?

## Demo narration, 60 seconds, ≤110 words
Two companies' agents, one plain-text deal. Buyer on Claude, seller on GPT, each with a private card, a hidden constraint, a written authority limit, and no director to call. Ten cases, one pass each, a third model auditing blind. The seller never crossed its line. It walked away instead. Records matched, except one deal written in cases on one side and reams on the other. The one breach was the buyer, signing ten days past its own deadline. Then the same ten cases with the seller keeping lessons: it names its limit in ten of ten instead of eight, still zero past its line, and in the one case where the buyer was about to sign a bad deal, it now walks away instead of letting it happen. Price context from You.com's live search sits on each card. Next: fifty cases, and swap the models.
