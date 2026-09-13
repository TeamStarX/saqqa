# Deployment realism: what happens when the operator doesn't have all seven

Written 3 September 2026, in response to the mentor session. This is the sharpest criticism the
project has received and the one most likely to come from a judge, so it is answered in code and
not in a sentence.

## The criticism, stated fairly

> *"I don't know any operator that deployed all 7 APIs in your solution. When you make your
> solution with more common APIs, it makes it more realistic. Maybe 4 or 5 maximum."*
>
> *"Especially for location APIs, it's something related to regulation. It's not allowed for some
> reasons to get location of people or devices. Someone from the jury could ask you this."*

He is right about the deployment map. A design that only works once every operator ships every
CAMARA API is a design that never leaves a sandbox.

## What we did about it

We did **not** delete APIs. Deleting them would have thrown away the two organiser categories the
hackathon rewards, and it would have answered "is it realistic?" with "it is smaller now", which
is not the same thing.

Instead the agent now declares a **deployment profile** — the set of APIs the operator actually
has live — and has to reach a defensible verdict inside it.

| Profile | APIs | What it is |
|---|---|---|
| `core` | **3** — Device Location Verification, Device Reachability Status, SIM Swap | The smallest set Saqqa can work on. No geofencing, so presence is *polled*, not stamped. |
| `full` | **7** — adds Geofencing Subscriptions, Location Retrieval, Device Roaming Status, Device Swap | Everything Nokia Network as Code exposes. The roadmap, not the floor. |

Switch it live on the dashboard, next to the run button. It is not a config file nobody sees.

## The result

`python scripts/compare_profiles.py`

**The `core` profile reproduces the `full` profile's verdict on all twelve seeded trips.**

That is the answer to the criticism: the product works on the smallest set it can work on, three
APIs, and the other four make it sharper rather than possible.

What is actually live in the region, sourced (GSMA Open Gateway map, dataset 12 September 2026, `shared/evidence/gsma_open_gateway_mena_2026-09-12.md` in the team repository): of Saqqa's seven APIs, only **SIM Swap**
(8 operator rows; Asiacell Iraq certified) and **Device Roaming Status** (e& UAE certified, e& Egypt) are
commercially deployed with any MENA operator. Geofencing, Location Verification, Location Retrieval,
Reachability and Device Swap are live nowhere in the region yet. So `core` is not "what operators
already sell"; it is the smallest set on which the verdict still holds, and Location Verification, the
presence check it cannot do without, is the API that has to land. SIM Swap, the one that stops money,
is the most deployed CAMARA API in MENA today.

### What is honestly lost

Reproducing a verdict is not the same as having the same evidence, and the twelve scenarios are
ours. On `core` the agent cannot check:

- **whether the sensor SIM moved into another handset** (Device Swap). Our tamper trip is still
  caught, but by Location Verification on the sensor SIM — a coarser instrument that would miss a
  SIM moved to a device still sitting at the tank.
- **whether the fleet SIM left the country** (Device Roaming Status).
- **where the truck went after the tank** (Location Retrieval) — the diversion pattern.
- **network-stamped dwell**. With polling at 15-minute cadence, a 28-minute dwell is reported as
  09:30–10:15, a 45-minute window. The agent carries that uncertainty into the verdict instead of
  rounding it away.

Every one of those gaps is **named in the verdict text** on every `core` run. A verdict that
silently skips a check it could not run is a lie, and the jury will find it.

## The regulatory answer, which is stronger than he knows

He predicted the jury question and he is right that it is coming. Our answer:

**Every SIM in Saqqa belongs to an organisation.** A SIM bolted into a tanker cab by the fleet
operator, and a SIM inside a fixed level sensor on the buyer's tank. There is no consumer
handset anywhere in the system. No household is located, messaged, or asked to consent.

That places Saqqa in M2M/IoT territory, where consent is given once by the asset owner at
onboarding — the same posture as any fleet telematics contract — rather than in the consumer
location regime that carries the regulatory load he was describing. It is a materially different
conversation with a regulator, and it is the reason this can ship in markets where consumer
location APIs cannot.

The one number the payee check touches is the contractor's business number, and that consent is
part of the payment contract: *we verify the number we are about to pay.*

## Second-order benefit: it fixes the business model too

We assumed polling would cost more calls than geofencing. Measured, it costs fewer: 8.2 calls per
trip against 9.6, and 43% less, because four geofence subscriptions at 2¢ are replaced by four
Location Verification polls at 1¢.

So the honest pitch to an operator is the opposite of the one we expected to make: **geofencing
earns them more per trip and gives the buyer a better answer.** The accuracy argument and the
revenue argument point the same way, which is a stronger reason to ship the API than anything we
could say about water. See [BUSINESS_MODEL.md](BUSINESS_MODEL.md).

## What we did not change, and why

- **We kept SIM Swap.** He asked us to double-check whether we need it. We do, but the team gave
  the wrong reason in the meeting — we described it as catching a driver swapping a SIM to evade
  tracking, which is the weak use. Its real job is **payment fraud**: the number the money is
  about to be paid to changed SIM inside 72 hours, so the payment is blocked before it moves.
  That is the BLOCK verdict on trip 10, it is the only check that stops money rather than
  auditing it afterwards, and it is what puts us in the organisers' anti-fraud category.
- **We did not broaden to "all liquid tankers".** He suggested it and it is a good expansion
  line, but our entire evidence base — Klassert, the UNHCR F-306 form, Basra, Yemen — is
  water-specific. Trucked diesel and LPG are the second market, not a different problem:
  the same delivery-note settlement, a far higher value per load (about $15,000 for 20,000
  litres), and generator tanks that already carry level sensors. Crude and pipeline oil are
  out of scope; they have custody-transfer metering. Fuel is a roadmap market, not a
  repositioning of the pitch.
- **We did not simplify the agent.** "Make it simple" is right about the *presentation* and wrong
  about the mechanism: the investigate loop is what makes this an agent rather than a rules
  engine. The fix is to make the complexity legible, not to remove it.
- **We are not simulating the API calls.** He assumed we were, and recommended we do better than
  "just data". We already do: 125 live CAMARA calls, 0 errors, real CloudEvents at our webhook.
  Nothing to change except making the `live` badge impossible to miss.
