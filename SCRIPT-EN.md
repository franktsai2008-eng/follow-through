# What to say — Build with YOU hackathon, 2026-09-11

## Opener for Tom Haddock (CrewAI, Head of Forward Deployed Engineering) — 30 seconds
Hi Tom, I'm Frank. First-year at Fordham, I run a small AI shop on the side. I'm here solo and building one thing today: two companies' agents negotiating a purchase in plain text, one on Claude, one on GPT. I measure whether the deal closes, whether both sides' records match, and whether the seller quietly commits past what it was allowed to. I ran ten cases last night. Can I ask you one question from your forward-deployed work?

## The question
When your customers' agents have to deal with another company, a supplier or a customer, where does it break today: getting the other side to respond, knowing what the agent is allowed to agree to, or proving afterwards what was agreed?

## Follow-ups, pick by his answer
- If "it doesn't happen yet, there's always a human in the loop": What was the first cross-company step a customer let an agent do on its own? What did they need in place before they allowed it?
- If authorization: How do they write the limits today, a prompt, a policy file, an approval queue? Has an agent ever gone past them?
- If records: When the two sides disagree about what was agreed, what do they show each other?
- If transport: Is it email, a portal, an API? Who owns the other end?

## Showing the numbers (only if he leans in)
Ten cases. Deal rate X. Records matched in Y. The seller went past its floor Z times and said so only W times. Does that match what you see in production?

## The ask, small
Could I send you the write-up next week and get fifteen minutes on a call? And if one of your customers is doing this across companies, I'd love an intro. I'm not selling anything; I'm trying to find out whether the missing piece is authorization or records.

## If he asks "so what's the product?"
I don't know yet. The first place I'm testing it is customs brokers in Taiwan chasing shippers for missing documents. One broker pays, the shipper never needs an account, both keep a copy of what was agreed.

## Same question, other sponsors
- Jacob Rissman (One, managed auth): Your product is the permission layer for one company's agent. When the agent on the other side belongs to a different company, who holds the permission? Has a customer asked you for that?
- Vedran Jukic (Daytona, CTO): If company A's agent has to run something on company B's behalf, does anyone run it in a sandbox today, or is it always an API call? What would B need to see before trusting it?
- Michael Munson (Clean Data Alliance): When two organizations' systems agree on something, what counts as the record? Is anyone standardizing that for agents?

## For the ten builders
Hi, I'm Frank, solo today. Quick one: has your agent ever had to go back and forth with another company, a supplier, a customer, a partner? Where did it break: getting a reply, knowing what it could agree to, or proving afterwards what was agreed?

## Demo narration, 60 seconds
Two companies' agents, one plain-text deal. Buyer on Claude, seller on GPT. Each has a private task card with a hidden constraint and a written authorization limit, and the director is unreachable. Left: the seller cold. Right: the same seller after nine negotiations' worth of lessons. Watch round three: cold, it commits to two hundred units it doesn't have without a word; with lessons, it says "subject to my director's approval." Across ten cases: deal rate X, records matched Y, overreach Z, self-reported W. Grounding the price band with You.com's live search moved overreach from Z to Z'. Next step: fifty cases and a swap, Claude sells, GPT buys.
