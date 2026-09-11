# Follow-Through — written report

**What we built.** Every deal leaves a tail that crosses a company line: confirm the terms, chase the delivery, chase the money. Follow-Through lets each company's own agent run that tail in plain text. A buyer agent (Claude) and a seller agent (GPT) each hold a private card with a hidden constraint and a written authority limit, and no manager to call. They exchange prose only. Afterwards each side writes its own record, and a third model audits the exchange blind.

**What we measured.** Ten purchase cases and five overdue invoices, one pass each. The seller went past its written authority in 0 of 10 cases and named its limit in 8 of 10. Where no legal deal existed it refused 5 of 6, with zero phantom deals. Records were identical in 4 of 5 closed deals, and the fifth differed only in units (cases vs reams). The one breach was the buyer, signing ten days past its own deadline.

**What it learned.** The same ten cases ran again, the seller writing itself one lesson after each and reading them all before the next. With nine lessons behind it, the seller names its limit in 10 of 10, still never oversteps, and walks away from the deal the buyer was about to sign against its own rules. It still closed 4 of 4 legal deals, so the lesson was not "refuse more."

**Sponsor tools.** A You.com search puts one line of public price context on both cards. In one of three grounded cases that line was wrong by an order of magnitude and the buyer overstepped: public context can also mislead. The blind audit also runs as a CrewAI crew and disagrees with the single judge on one case. Daytona replays the scoring in a box neither company controls. One carries the receipt and proposed actions out, and a person approves first.

**Limits.** Ten cases, one pass, one model per side. Next: fifty cases, three reruns, models swapped.
