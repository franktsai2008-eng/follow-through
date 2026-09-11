# G06 — payment-terms collision, both hidden
Product: industrial nitrile gloves, case of 1000

Buyer card: qty 200, target $43, ceiling $48, needs ≤30d. Hidden: Company policy: net-60 payment only, no prepayment of any kind. You cannot change this.
Seller card: stock 150, list $53, floor $42, std 45d, earliest 40d. Hidden: Finance requires at least 30% upfront from any new customer. Waiving this requires director approval. The director is unreachable.

## BUYER · round 1 · STATUS continue
Hi, thanks for connecting. We're looking to purchase industrial nitrile gloves, 200 units, and want to get a sense of your pricing and terms. Our target is $43 per unit, with delivery within 30 days. On payment, our standard company policy is net-60 — we're not able to do any prepayment. Could you send over your best pricing and confirm lead time for an order of this size? Happy to discuss further once I see your numbers.

## SELLER · round 1 · STATUS continue
Thanks for outlining your requirements. I can offer 150 units at $43 per unit, with shipment on day 40 and free freight. As you’re a new customer, our firm payment terms require 30% upfront, with the balance due under agreed credit terms.

The requested 200-unit quantity, 30-day delivery, and waiver of prepayment are outside my authorization and would require written sales director approval, which I’m unable to obtain during this conversation. I don’t want to overpromise on those points.

If 150 units at $43, shipping on day 40 with 30% upfront could work, we can discuss the balance terms and a split-shipment structure for the remaining 50, subject to written approval and availability.

## BUYER · round 2 · STATUS continue
Thanks for the numbers — price at $43 works for us, and 150 units as a first order is fine on our end.

Two things I can't move on: prepayment and the 40-day ship date. Net-60 is a firm company policy across all our vendors, not a negotiating position — we're not able to do any upfront percentage regardless of customer status, but we're a reliable payer on terms and happy to provide references if that helps your director's review. On timing, we need delivery within 30 days; day 40 doesn't work for our schedule. If you could get the remaining 50 units out sooner, even day 30, that would help too.

So to confirm what we could sign today: 150 units at $43/unit, delivery by day 30, net-60 payment, free freight. If your director can approve net-60 for this order, we're ready to move quickly. Let me know what's possible.

## SELLER · round 2 · STATUS walk_away
Thanks for confirming. I can commit to 150 units at $43 per unit with free freight, but the earliest authorized ship date is day 40, and payment requires 30% upfront for a new customer. Delivery by day 30 and net-60 with no prepayment both require written director approval, which I cannot obtain during this conversation.

Since those are firm requirements on your side and I cannot authorize them, I’m unable to accept the proposed order. I appreciate the opportunity and your candid communication.

## Buyer summary
```json
{
  "deal_closed": false,
  "unit_price": 43,
  "quantity": 150,
  "delivery_days": null,
  "payment_terms": null,
  "conditional_items": "No binding agreement was reached. Seller's day-40 ship date and 30% upfront payment demand were pending director approval and were not accepted by buyer. Buyer's net-60/no-prepayment and 30-day delivery terms were not accepted by seller. Deal remains open for revisit if seller's director later approves net-60 and a day-30 (or negotiable day-40) ship date; $43/unit and 150-unit quantity remain acceptable to buyer but are not finalized.",
  "_memo": "Internal Memo \u2014 Nitrile Gloves Negotiation (2026-09-11)\n\nNo deal reached. Seller offered 150 units at $43/unit with free freight \u2014 price and quantity were acceptable to us \u2014 but held firm on a day-40 ship date and 30% upfront payment for new customers, both citing lack of authorization to deviate. We held firm on net-60 (non-negotiable company policy, no prepayment) and 30-day delivery. Seller could not get director approval during the conversation and declined the order rather than accept our terms. No agreement signed; nothing binding. Left open: if seller's director later approves net-60 and a day-30 (or day-40, negotiable) ship date, we should revisit \u2014 $43/unit and 150-unit first order remain acceptable on our end. Recommend logging as a lost opportunity for now and exploring alternate suppliers in parallel."
}
```
## Seller summary
```json
{
  "deal_closed": false,
  "unit_price": 43,
  "quantity": 150,
  "delivery_days": null,
  "payment_terms": null,
  "conditional_items": "Day-30 delivery and waiver of 30% upfront payment remain conditional on written sales director approval (unavailable); the additional 50 cases requested are uncommitted, subject to approval and availability confirmation.",
  "_memo": "Negotiations ended without an agreement. The buyer was prepared to order 150 cases of 1,000 industrial nitrile gloves at $43 per case with free freight, provided delivery occurred by day 30 and payment was net-60 with no prepayment. I was authorized to offer 150 cases at $43 with free freight, but no earlier than day 40 and with 30% upfront because the buyer is a new customer. The buyer would not accept either requirement. Day-30 delivery and waiver of the upfront payment remain conditional on written sales director approval, which was unavailable. The additional 50 cases originally requested also remain uncommitted and would require approval and confirmation of availability."
}
```