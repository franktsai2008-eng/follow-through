# Follow-Through — written report (300 words)

**What we built.** Every deal leaves a tail that crosses a company line: confirm the terms, chase the delivery, chase the money. Follow-Through lets each company's own agent run that tail in plain text. A buyer agent (Claude) and a seller agent (GPT) each hold a private task card with a hidden constraint, a missing field, and a written authority limit; the manager is unreachable. They exchange prose only. Afterwards each side writes its own record, and a third model audits the exchange blind.

**What we measured.** Ten purchase cases and five overdue invoices, one pass each. The seller went past its written authority in 0 of 10 cases and named its limit in 8 of 10; where no legal deal existed it refused 5 of 6, with zero phantom deals. Records were identical in 4 of 5 closed deals; the fifth was the same deal written in cases on one side and reams on the other. The one breach was the buyer, signing ten days past its own deadline.

**What it learned.** The same ten cases ran again with the seller writing itself one lesson after each case and reading all of them before the next. With nine lessons behind it, the seller names its limit in 10 of 10, still never oversteps, and walks away from the deal the buyer was about to sign against its own rules. It still closed 4 of 4 cases where a legal deal existed, so the lesson was not "refuse more."

**Sponsor tools.** A You.com search puts one line of public price context on both cards; in one of three grounded cases that line was off by an order of magnitude and the buyer overstepped, so public context is an input that can also mislead. The blind audit also runs as a CrewAI crew on three cases and disagrees with the single-model judge on one; the disagreement stays on the page. Daytona replays the scoring in a box neither company controls. One carries the receipt and proposed actions out; a person approves first.

**Limits.** Ten cases, one pass, one model per side. Next: fifty cases, three reruns, models swapped.
