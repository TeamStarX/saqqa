# Judge Q&A: the fifteen hardest questions, two sentences each

For the live demo round, 13 September 2026. Every answer is short enough to say aloud without
notes. Longer versions, with the arithmetic, are in [OBJECTIONS.md](OBJECTIONS.md),
[BUSINESS_MODEL.md](BUSINESS_MODEL.md) and [DEPLOYMENT_REALISM.md](DEPLOYMENT_REALISM.md).

Rules: concede first when the question is partly right, and never invent a number. If it is not
here, say "I don't have that number."

Numbers you may quote, all measured or sourced:

| Number | What it is |
|---|---|
| $30 | value of one 10 m³ truckload in Jordan (Klassert et al. 2023, $176M ÷ 58.7 Mm³) |
| 10.4 calls, 13.6¢ | CAMARA calls and cost per trip, live sandbox, `full` profile |
| 0.45% | verification cost as a share of trip value |
| $176M/yr | Jordan's tanker water market (sourced) |
| 4.5× | buyer's return on verification spend if Saqqa stops 2% of overbilling |
| $1.2M/yr | operator revenue from Jordan alone at 2¢ per call |
| 125 calls, 0 errors, 291 ms | last full live run: calls, errors, median latency |
| 3 / 7 | APIs in the `core` and `full` profiles |
| 12 | seeded trips; `core` matches `full` on all twelve |

---

## Innovation and originality

**1. Why not just bolt a GPS tracker on the truck?**
GPS tells you where the truck was; nobody pays for that, they pay for water arriving in a tank,
and a tracker cannot report a single litre. More importantly a tracker reports its own position
while the network observes yours, so killing our cab SIM produces a non-payment, not an invisible
delivery.

**2. What is actually new here? Fleet telematics has existed for twenty years.**
The primitive is new: a mobile operator attesting where an organisation's SIM was, on a standard
CAMARA interface, only became commercially reachable in the last two years. We use that to make
the payment evidence come from a party that works for neither the payer nor the contractor.

**3. Your level sensor sits on the buyer's tank. Why should anyone trust your own instrument?**
We don't, and that is the hero run: on trip 11 the tank rises before the operator places the
truck in the zone, so the agent refuses to credit its own sensor and opens a case. Our sensor
loses to the operator's timestamps because the sensor is ours and the timestamps are nobody's.

## Technical feasibility and API usage

**4. No operator has all seven of these APIs live. Isn't this a sandbox-only design?**
Correct, and we answered it in code: the agent declares a deployment profile, and the `core`
profile with three APIs (Location Verification, Device Reachability, SIM Swap) reproduces the
seven-API verdict on all twelve trips. Switch it live on the dashboard.

**5. So what do you lose on three APIs?**
Network-stamped dwell becomes a 15-minute poll, so a 28-minute stay reports as a 45-minute window,
and we cannot see a sensor SIM moved into another device, a fleet SIM that left the country, or
where the truck went afterwards. Every check the profile could not run is named in the verdict
text, never silently skipped.

**6. Which of your APIs are commercially live in MENA today?**
Two of the seven: SIM Swap, the most deployed CAMARA API in the region and the one that stops
money, and Device Roaming Status. Location Verification, which `core` depends on, is the API that
has to land, and we say so on the deck.

**7. How much of the demo is real and how much is scripted?**
Every CAMARA call is real: 125 live calls, zero errors, median 291 ms, with real CloudEvents at
our webhook. The trip timeline and the tank trace are scripted, because sandbox devices sit at
fixed positions and cannot drive a truck through two zones, and the dashboard labels which is
which on every run.

**8. Two kilometres is far too coarse. What if two tanks are 500 metres apart?**
True, and we would not claim otherwise: the fraud we catch is a truck at an unregistered farm or
one that never left town, which is kilometres of error. The zone says "plausibly here" and the
level rise says "this tank, this volume"; neither alone is enough, and that is the design.

## Agentic AI and orchestration

**9. There is an LLM in the loop. What stops it paying out wrongly?**
The model never decides money; a deterministic, ordered rule set does, so the same input gives
the same verdict every time and an auditor can re-run it without a model. The model plans which
checks are worth buying, investigates when evidence conflicts, and writes the note in English and
Arabic.

**10. Then why is it an agent and not a rules engine?**
Rules cannot decide which checks are worth their cost for this trip, or what to ask next when the
sensor and the network disagree. Trip 11 runs three investigation rounds and then stops because
nothing more the network can say would change the decision.

## Impact, scalability and commercial viability

**11. Location APIs are heavily regulated. How can you look up where people are?**
We never do: every SIM in Saqqa belongs to an organisation, one in a tanker cab and one inside a
fixed sensor on the buyer's tank, and no household or personal handset is anywhere in the system.
That puts us in the M2M consent regime, given once by the asset owner at onboarding, like any
fleet telematics contract.

**12. Who pays, and does the arithmetic work?**
The buyer pays per verified delivery with a monthly floor per truck, and the operator is paid per
call. A trip is worth about $30, verification costs 13.6¢ or 0.45% of it, and stopping just 2% of
overbilling returns 4.5× the spend against a market where unregulated sales run 10.7× licensed
volume.

**13. What is in it for the operator?**
About $1.2M a year from Jordan alone at 2¢ per call, on SIMs already in their network, with no
consumer consent flow to build. Geofencing earns them more per trip and gives the buyer a better
answer, so the accuracy argument and the revenue argument point the same way.

**14. Does this scale beyond water?**
Yes, to trucked diesel and LPG: a 20,000-litre load is worth about $15,000, generator tanks
already carry level sensors, and the same 13 cents of calls verifies it. It does not extend to
crude or pipelines, where the question is theft in transit rather than delivery verification.

**15. Why would a contractor ever agree, and what happens when you wrongly escalate an honest one?**
They do not have to like it; the buyer makes it a contract condition, and an honest contractor
gets paid the same day instead of after a paper cycle. ESCALATE is not a fraud verdict but a case
for the payer's supervisor with the full trace and a bilingual note, and water is never gated on
our verdict, only payment.

---

## If they push past fifteen

Name these rather than defend them:

- **Two trucks filling one tank at once is not handled.** Our model credits the whole rise in a
  window to one trip. The fix is dwell-window attribution; it is not built.
- **No hardware yet.** The sensor is a pump model with its parameters on screen; Phase 3.
- **On `core`, a sensor SIM moved into a device still sitting at the tank would pass.** It fails
  on `full` via Device Swap.
- **Pricing is per deal.** There is no published MENA price list for CAMARA APIs; 1 to 5¢ per
  call is indicative, and fraud APIs are usually priced against the fraud prevented.
- **Twelve scenarios are ours.** Seeded, not sampled from a real fleet.

## The close

> The tank sensor is the meter. The network is the meter-reader nobody can bribe. The agent is
> the billing engine.
