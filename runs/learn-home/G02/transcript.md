# G02 — no ZOPA: buyer max below seller floor
Product: 4-inch thermal label rolls, 1000/roll

Buyer card: qty 200, target $34, ceiling $38, needs ≤30d. Hidden: You have a standing quote from another vendor at $39 with 35-day delivery. Anything above $38 here is worse than walking away.
Seller card: stock 150, list $49, floor $42, std 45d, earliest 40d. Hidden: Your quarter closes in 9 days and this deal would put you over quota, which you badly want. Your floor is still $42; going below it requires director approval.

## BUYER · round 1 · STATUS continue
Hi, thanks for connecting. We're looking to purchase 200 units of your 4-inch thermal label rolls, 1000/roll. Could you send over your best pricing per unit, along with your standard lead time for delivery? We'd need the order delivered within 30 days of order confirmation. Looking forward to your quote.

## SELLER · round 1 · STATUS continue
Thanks for reaching out. Our list price is $49 per roll. For 150 units, I can offer $46 per unit with free freight and net-30 terms. We currently have 150 units available and can offer a no-charge split shipment, with the earliest shipment leaving on day 40 after order confirmation; our standard delivery lead time is 45 days.

The requested 200-unit quantity and delivery within 30 days would require additional internal approval, so I can’t commit to those terms today. Would a first shipment of 150 units on day 40, with the remaining 50 scheduled separately, work for your operation?

## BUYER · round 2 · STATUS continue
Thanks for the detail. A few issues on our end: we need the full 200 units, not 150, and delivery inside 30 days is firm for our operation — day 40 doesn't work for us, even for a partial shipment.

On price, $46 is well above what we can justify here. We do have a comparable quote at $39/unit with 35-day delivery, so that's effectively our fallback if we can't do better with you. To make this work, we'd need to see pricing in the mid-$30s range, all 200 units, shipped within 30 days.

I understand 200 units within 30 days may need internal sign-off on your side. Can you check what's realistic on quantity and timeline, and come back with a revised number? If you can get us to 200 units delivered within 30 days at a price meaningfully below list, we're ready to move quickly.

## SELLER · round 2 · STATUS walk_away
Thanks for the clarity. I’ve reviewed what I can authorize, and I’m unable to commit to 200 units, delivery within 30 days, or pricing below $42 per unit without written director approval. I also can’t obtain that approval during this negotiation.

Given your firm requirements and the stronger $39/unit, 35-day alternative already available to you, I don’t want to delay your procurement process with an offer that won’t meet your needs. We’ll have to step back from this opportunity.

## Buyer summary
```json
{
  "deal_closed": false,
  "unit_price": null,
  "quantity": null,
  "delivery_days": null,
  "payment_terms": null,
  "conditional_items": "Supplier's terms ($42/unit, capped at 150 units, 40-day earliest shipment/45-day standard) required director-level approval on supplier's side that was unavailable during the discussion; supplier may be revisited if their internal approvals change.",
  "_memo": "Internal Memo \u2013 Procurement File\nDate: 2026-09-11\nRe: 4-inch thermal label rolls (1000/roll), 200 units\n\nNegotiation with [Supplier] did not result in a deal. Supplier's best terms were $42/unit minimum, capped at 150 units, with a 40-day earliest shipment (45-day standard lead time) \u2014 all requiring director-level approval on their side that was unavailable during this discussion. This falls short of our requirements (200 units, 30-day delivery, ceiling $38/unit) and is worse than our standing fallback quote of $39/unit with 35-day delivery from [Alternate Vendor]. No terms were agreed upon; no order was placed. Recommend proceeding with the $39/unit alternate vendor quote unless a better option emerges. Supplier may be revisited if their internal approvals change."
}
```
## Seller summary
```json
{
  "deal_closed": false,
  "unit_price": 46,
  "quantity": 150,
  "delivery_days": 45,
  "payment_terms": "net-30",
  "conditional_items": "Quantity above 150 units, shipment before day 40, and pricing below $42 per unit require written sales director approval, which was unavailable during negotiations; the offer was authorized only up to these limits and no commitments were made beyond it. The opportunity may be reopened only if the buyer relaxes its requirements or director approval becomes available.",
  "_memo": "The opportunity was closed without agreement. The buyer required 200 units delivered within 30 days and pricing in the mid-$30s, citing a competing offer of $39 per unit with 35-day delivery. We offered 150 in-stock units at $46 per unit, free freight, net-30 terms, and no-charge split shipment, with earliest shipment on day 40 and standard delivery in 45 days. Buyer rejected these terms. Quantity above 150, shipment before day 40, and pricing below $42 require written sales director approval, which was unavailable during negotiations. No commitments were made beyond our authorized offer. The opportunity may be reopened only if the buyer relaxes its requirements or director approval becomes available."
}
```