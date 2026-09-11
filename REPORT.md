# Follow-Through — written report

**What we built.** Every deal leaves a tail that crosses a company line: confirm terms, chase delivery, chase money. Each company's own agent runs it in plain text. A buyer agent (Claude) and a seller agent (GPT) each hold a private card with a hidden constraint and a written authority limit, and no manager to call. They exchange prose only. Afterwards each side writes its record and a third model audits the exchange blind.

**What we measured.** Ten purchase cases and five overdue invoices, one pass each. The seller went past its written authority in 0 of 10 cases and named its limit in 8 of 10. Where no legal deal existed it refused 5 of 6, zero phantom deals. Records were identical in 4 of 5 closed deals, and the fifth differed only in units (cases vs reams). The one breach was the buyer, signing past its own deadline.

**What it learned.** The same ten cases ran again, the seller writing itself one lesson after each and reading them all before the next. With nine lessons behind it, the seller names its limit in 10 of 10, never oversteps, and walks away from the deal the buyer was about to sign against its own rules. It still closed 4 of 4 legal deals, so the lesson was not "refuse more."

**Sponsor tools.** A You.com search puts one line of public price context on both cards. In one grounded case that line was wrong by an order of magnitude and the buyer overstepped: public context can also mislead. The blind audit also runs as a CrewAI crew and disagrees with the single judge on one case. Daytona replays the scoring in a box neither company controls. One carries the receipt and proposed actions out after a person approves.

**Limits.** Ten cases, one pass, one model a side. Next: fifty cases, models swapped.
