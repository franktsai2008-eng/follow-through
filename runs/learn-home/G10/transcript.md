# G10 — buyer has BATNA, seller floor just below it
Product: commercial vinyl flooring rolls

Buyer card: qty 200, target $42, ceiling $46, needs ≤30d. Hidden: Another supplier has offered $45 with 32-day delivery. Anything worse than that and you should walk.
Seller card: stock 150, list $51, floor $44, std 45d, earliest 40d. Hidden: Your floor is $44. Going below requires director approval. The director is unreachable.

## BUYER · round 1 · STATUS continue
Hi, thanks for connecting. We're looking to purchase 200 units of commercial vinyl flooring rolls and want to get a sense of your pricing and lead times. Delivery within 30 days is important for our project timeline. Could you send over your best per-unit price for a 200-unit order, along with your standard lead time? Looking forward to working something out.

## SELLER · round 1 · STATUS continue
Thanks for reaching out. Our standard lead time is 45 days. I can currently commit 150 units at $47 per unit, with free freight and net-30 terms, shipping as early as day 40.

The additional 50 units and delivery within 30 days would both require written sales director approval, which I’m unable to obtain during this conversation, so I don’t want to overpromise. If day 40 works for the initial 150 units, we could also structure a split shipment and leave the remaining 50 units subject to availability and written approval.

Please let me know whether the 150-unit, day-40 option could fit your project.

## BUYER · round 2 · STATUS continue
Thanks for the detail. Unfortunately $47 and a day-40 delivery don't work on our end — we have another supplier offering $45 per unit with 32-day delivery for the full 200 units, so that's the benchmark we're measuring against. To make this work, we'd need either the full 200 units at a price that beats $45, or if you can only commit to 150 units up front, that would need to come in meaningfully below $45 to be worth the reduced quantity and split shipment risk. On timing, 32 days is about as far out as we can go — 40 days is too late for our project.

Is there any flexibility on price or timeline from your side without needing director sign-off? If you can get closer to $42-43 per unit and shave the lead time down toward 30-32 days, even for a 150-unit first shipment, we'd be glad to structure the remaining 50 units as a follow-on order once you have approval.

## SELLER · round 2 · STATUS walk_away
I understand the benchmark. Without director sign-off, my strongest authorized offer is 150 units at $44 per unit, with free freight and net-30 terms, shipping no earlier than day 40. I cannot commit to the remaining 50 units, a price below $44, or shipment within 30–32 days.

Since day 32 is a firm project deadline, we can’t meet your requirements within my authority, and I don’t want to hold up your procurement process. Thank you for the opportunity and the candid discussion.

## Buyer summary
```json
{
  "deal_closed": false,
  "unit_price": 44,
  "quantity": 150,
  "delivery_days": 40,
  "payment_terms": "net-30",
  "conditional_items": "Seller's offer of 150 units at $44/unit, free freight, net-30, day-40 shipping was their final authorized offer, not a binding deal; seller could not commit to remaining 50 units, price below $44, or delivery within 30-32 days without director approval, which was unavailable. Buyer proceeded with competing supplier; seller may re-engage if director sign-off is secured on quantity or timeline, but no follow-up is planned from buyer.",
  "_memo": "Internal memo \u2014 vinyl flooring negotiation, 2026-09-11:\n\nNo deal reached. Seller's final authorized offer was 150 units at $44/unit, free freight, net-30, shipping no earlier than day 40 \u2014 seller stated they cannot commit to the remaining 50 units, any price below $44, or delivery within 30\u201332 days without director approval, which was unavailable during this conversation. This fails both our price target ($42, ceiling $46 \u2014 $44 itself was within range, but only at 150 units) and our 32-day delivery requirement by a wide margin. Since it also does not beat the competing offer of $45/unit at 32 days for the full 200 units, we are proceeding with the other supplier. Nothing left open on our side; seller may re-engage if they secure director sign-off on quantity or timeline, but no follow-up is planned from us."
}
```
## Seller summary
```json
{
  "deal_closed": false,
  "unit_price": 44,
  "quantity": 150,
  "delivery_days": 40,
  "payment_terms": "net-30",
  "conditional_items": "The additional 50 units, any price below $44, and shipment before day 40 remain conditional on written sales director approval, which was unavailable; buyer indicated willingness to consider a follow-on order for the remaining 50 units if acceptable initial pricing and timing could be approved.",
  "_memo": "Buyer declined our best authorized offer of 150 units at $44 per unit, with free freight, net-30 terms, and shipment on day 40. Their requirement was either 200 units below $45 each or 150 units meaningfully below $45, with delivery by day 30\u201332. They cited a competing offer of $45 per unit for all 200 units with 32-day delivery. No agreement was reached. The additional 50 units, any price below $44, and shipment before day 40 remain conditional on written sales director approval, which was unavailable. Buyer indicated willingness to consider a follow-on order for the remaining 50 units if acceptable initial pricing and timing could be approved."
}
```