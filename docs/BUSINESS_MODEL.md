# Who pays, who earns, and how much

Written 3 September 2026, after the mentor session. He asked the revenue question three times
and we did not have an answer. This is the answer, with the arithmetic shown so anyone can
disagree with a specific number rather than with the conclusion.

Every figure is labelled **sourced** or **derived**. Do not quote a derived number without the
assumption attached to it.

## The market, from the paper we already cite

| Quantity | Value | Basis |
|---|---|---|
| Tanker water sold in Jordan | **58.7 million m³/yr** | **sourced** — Klassert et al., *Nature Sustainability* 6:1406 (2023), ensemble mean for 2015; the same model projects 94.9 Mm³/yr by 2050 |
| Value of that market | **US$176 million/yr** | **sourced** — same paper |
| Unregulated sales vs licences | **10.7×** | **sourced** — same paper |
| Price per m³ | $3.00 | derived: 176 ÷ 58.7 |
| Truckload | 10 m³ | assumption: our scenario truck; Jordanian tankers run 10–12 m³ |
| Trips per year | **5.87 million** | derived: 58.7 Mm³ ÷ 10 m³ |
| Value of one trip | **$30** | derived: $3.00 × 10 m³ |

**A trip is worth about thirty dollars, not hundreds.** This matters: it sets the ceiling on what
verification can cost per trip, and it is the number that makes per-call operator pricing work.

## What Saqqa spends per trip

Measured across the twelve seeded trips, not estimated. Conditions are stated because they
change the number:

| Profile | Conditions | Calls/trip | Cost/trip | Share of trip value |
|---|---|---|---|---|
| `core` — 3 APIs | fixture, stub planner | 8.2 | 7.58¢ | **0.25%** |
| `full` — 7 APIs | fixture, stub planner | 9.6 | 13.21¢ | **0.44%** |
| `full` — 7 APIs | **live sandbox, Gemini planner** | 10.4 | 13.62¢ | **0.45%** |

The first two rows are the like-for-like comparison; the third is production behaviour, from the
committed run logs. Quote the third for "what it costs us", the first two for "core versus full".

**Correction to an earlier assumption.** We expected polling to cost *more* calls than geofencing,
since the agent has to ask repeatedly instead of being told once. Measured, it does not: `core`
runs 8.2 calls to `full`'s 9.6, and costs 43% less, because four Geofencing subscriptions at 2¢
are replaced by four Location Verification polls at 1¢.

That has a consequence worth putting to an operator directly: **geofencing earns them more per
trip and gives the buyer a better answer.** Both sides want it deployed. It is the rare case
where the accuracy argument and the revenue argument point the same way, and it is a better
reason for an operator to ship the API than anything we could say about water.

## Operator revenue, three ways to charge

At Jordan's 5.87 M trips/yr that is **48.1 M CAMARA calls/yr** on `core` and **56.4–61.0 M**
on `full` — from one country.

| Model | Operator revenue/yr (`full`) | Operator revenue/yr (`core`) |
|---|---|---|
| **Per API call @ 1¢** | $0.56–0.61 M | $0.48 M |
| **Per API call @ 2¢** | **$1.13–1.22 M** | $0.96 M |
| Per API call @ 5¢ | $2.82–3.05 M | $2.41 M |
| Per truck @ $5/month | $0.20 M | $0.20 M |
| Per truck @ $10/month | $0.39 M | $0.39 M |

Fleet size for the subscription rows is **derived**: 5.87 M trips ÷ (6 trips/truck/day × 300 days)
≈ **3,300 trucks**. At 4 trips/day it is 4,900 trucks; at 8, 2,400. We could not find a published
fleet count, so this is arithmetic from volume, and it should be presented as such.

**Recommendation, one sentence for every surface: the buyer pays per verified delivery with a per-truck monthly floor; the operator is paid per call.** Per-call is 3–6× better for the operator
than a per-truck subscription at any plausible subscription price, and it scales with the thing
that actually drives operator cost. The floor exists because the buyer needs a predictable line
item in an annual budget, and a UN agency cannot sign an open-ended metered contract. So:
a committed monthly minimum per enrolled truck, drawn down against metered calls.

There is no published MENA price list for CAMARA APIs — the mentor confirmed pricing is
negotiated per deal, and for fraud APIs it is typically set against the value of the fraud
prevented rather than the cost of the call. That is the frame to negotiate in, and it favours us.

## Why the buyer signs

| If Saqqa stops… | Recovered/yr | Against $0.78 M of verification |
|---|---|---|
| 1% of overbilling | $1.76 M | **2.3×** |
| 2% of overbilling | $3.52 M | **4.5×** |
| 5% of overbilling | $8.80 M | **11.3×** |

Against a market where unregulated sales run **10.7× licensed volume**, catching 2% is a modest
claim, not an aggressive one. This is the slide that closes.

The buyer is the payer, never the contractor: UNHCR, UNICEF, WFP, a municipality, a hotel group.
They already pay for water they cannot verify. Saqqa is the cheapest line on that invoice.

## Scaling beyond Jordan

Jordan is 58.7 Mm³/yr and is the market with the best data, which is why the model is built on it.
It is not the biggest. Basra alone has 4.5 million people on daily deliveries; Yemen has 215,000
IDPs across 97 sites dependent on trucked water. Jordan is the unit economics, not the ceiling.

## What to say if asked the question we got wrong

The mentor's question was *"what is the revenue for the operator?"* — not *"what does it cost
you?"*. Lead with **$1.2 M/yr from one country at 2¢/call**, then say it is 48–61 million calls a
year on SIMs that are already in the operator's network, on hardware the operator has already
deployed, with no consumer consent flow to build. That is the sentence that makes an operator
care.
