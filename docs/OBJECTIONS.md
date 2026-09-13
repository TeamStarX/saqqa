# Every argument against Saqqa, and the answer

For the jury, the mentors, and anyone on the team who gets asked a hard question. Written
12 September 2026.

Two rules for using this:

1. **Concede first when the objection is partly right.** A jury trusts a team that names its own
   limits. Every answer below that begins "Yes, and —" is more persuasive than one that begins
   "No, because."
2. **Never invent a number.** If it is not in this file or traceable to a logged call, say
   "I don't have that number." Section 8 lists what we genuinely cannot answer.

---

## 1. The five that decide it

### 1.1 "Why not just bolt a GPS tracker on the truck?"

**Refuse the premise first.** GPS answers *where was the truck*. Nobody pays for a truck's
location; they pay for **water arriving in a tank**. A tracker cannot report a single litre.

Trip 04 in the demo is exactly this: the truck sits in the tank zone for 22 minutes and the level
never moves. GPS says *delivered, on site, correct duration, pay it*. We say **ESCALATE**.

Then the custody point:

> **A tracker reports its own position. The network observes yours.**

A GPS unit is a device the contractor mounts, powers and can reach, and it computes the number it
then reports about itself. The audited party is holding the instrument. Network location is
computed by the operator from which cells the SIM attaches to — the SIM cannot assert a false
position, only be somewhere. Forging it means defeating a mobile operator, not a box on a dash.

Spoofing a GPS tracker is cheap and well understood; jammers sell as "privacy devices" for tens of
dollars, and you do not even need one — unplug it, foil it, or bolt it to another truck. A flat
battery is deniable.

**And the argument that actually wins it:**

> **Disabling our system produces a non-payment, not an invisible delivery.**

Kill a tracker and the trip is simply unlogged; the contractor invoices anyway and the paperwork
covers it. Kill our cab SIM and the operator never places the truck at the tank, so the gate
cannot release payment — that is trip 05, ghost trip, ESCALATE, zero released. Saqqa is
**fail-secure**. Tampering costs the contractor money instead of hiding fraud. A GPS fleet is
fail-open. That is structural, not a tuning difference.

**Concede honestly:** GPS wins on resolution (5 m vs ~2 km), gives a continuous breadcrumb rather
than zone crossings, and needs no operator agreement. We do not need to beat it on precision —
2 km zones are far smaller than the distance between a licensed well and an illegal one.

**Closing line:** *"GPS is the contractor's word with better resolution. We wanted a witness who
doesn't work for either party."*

### 1.2 "Your sensor is on the buyer's tank. Why should anyone trust your own instrument?"

**We don't.** That is the demo's hero run.

Trip 11: the tank rises 9.7 m³ between 09:05 and 09:27. The operator's timestamps put the truck in
the zone only from 09:35. The agent does not split the difference and it does not believe its own
sensor — it **refuses to credit the measurement**, opens a case, and accuses nobody.

> **"Our own sensor loses to the operator's timestamps, because the sensor is ours and the
> timestamps are nobody's."**

We also check the sensor as hardware, not as truth: Device Reachability (is it alive), Location
Verification on the sensor's own SIM (is it still at its install point), Device Swap (has its SIM
been moved into another handset). Trip 08 is a sensor whose SIM moved — ESCALATE.

A GPS-based system has no equivalent check on its own sensor.

### 1.3 "No operator has all seven of those APIs live."

Correct, and it is the sharpest criticism we have received — it came from a Türk Telekom mentor on
3 September. We answered it in code, not in a sentence.

The agent declares a **deployment profile** and must reach a defensible verdict inside it:

| Profile | APIs | Dwell |
|---|---|---|
| `core` | **3** — Location Verification, Device Reachability, SIM Swap | polled, 15-min cadence |
| `full` | **7** — adds Geofencing, Location Retrieval, Roaming, Device Swap | network-stamped |

**`core` reproduces `full`'s verdict on all twelve trips** (`scripts/compare_profiles.py`). Switch
it live on the dashboard. Three APIs, the smallest set it works on; of the seven, SIM Swap and Device
Roaming Status are the two commercially live in MENA today (GSMA Open Gateway map, dataset 12 September 2026, `shared/evidence/gsma_open_gateway_mena_2026-09-12.md` in the team repository), and SIM Swap is the one
that stops money. The other four make the answer sharper, not possible.

Without geofencing the agent polls instead of being told, so a 28-minute dwell reports as a
45-minute window — and the verdict says so, and names every check the profile could not run.

### 1.4 "Location APIs are heavily regulated. You cannot just look up where people are."

Also correct, and our answer is stronger than most people expect:

> **Every SIM in Saqqa belongs to an organisation.** One bolted into a tanker cab by the fleet
> operator, one inside a fixed level sensor on the buyer's tank. There is no consumer handset
> anywhere in the system.

No household is located, messaged, or asked to consent. That puts us in M2M/IoT territory, where
consent is given once by the asset owner at onboarding — the same posture as any fleet telematics
contract — not the consumer location regime that carries the regulatory load.

The one number the payee check touches is the contractor's **business** number, and that consent is
part of the payment contract: *we verify the number we are about to pay.*

### 1.5 "There's an LLM in the loop. What stops it paying out wrongly?"

**The model never decides money.** A deterministic gate does — an ordered rule set, same input,
same verdict, every time, re-runnable by an auditor without a model.

The model does three things it is actually good at: **plan** which checks are worth buying,
**investigate** when evidence conflicts, and **explain** in English and Arabic. If the model is
unavailable the audit note falls back to a template and says so on screen; the decision is
unchanged.

Say this before they ask. It is the first question a bank or a UN finance officer raises.

---

## 2. "Why not just —"

**"…put a flow meter on the truck?"** It is the contractor's meter, on the contractor's vehicle,
serviced by the contractor. Same custody problem as GPS, plus calibration drift you cannot audit
remotely. Our meter is on the **buyer's** tank and the buyer owns it.

**"…use a weighbridge?"** Fixed infrastructure, one location, tens of thousands of dollars, and it
weighs the truck at the depot — not at the camp fifty kilometres away where the fraud happens.

**"…have the driver check in on an app with a photo?"** That is the signed delivery note with
extra steps. The person being paid is still the person producing the evidence. Photos are trivially
staged or reused.

**"…put cameras at the tank?"** Bandwidth, power and privacy at an informal settlement, plus
someone to watch the footage. And a camera still cannot tell you volume.

**"…seal the tanker hatch?"** A seal stops a screwdriver, not a spoofed signal, and it proves the
hatch was shut, not that the water went into the right tank.

**"…blockchain?"** Our problem is not that the ledger can be edited. It is that the **input** to
the ledger is a signature from someone who was not there. Notarising a lie does not help. We fixed
the input.

**"…just audit better?"** UNHCR's F-306 already exists and says on its face that it is "used as part
of the payment justification process to the contractor." Auditing paper harder is what everyone is
already doing, against a market where unregulated sales run **10.7× licensed volume**.

---

## 3. The network layer

**"2 km is far too coarse. Two tanks could be 500 m apart."** True, and we would not claim
otherwise. Two things: the fraud we are catching is a truck at an unregistered farm or never
leaving town, which is kilometres of error, not hundreds of metres. And the tank sensor
disambiguates — a zone says *plausibly here*, the level rise says *this specific tank, this
volume*. Neither alone is enough; that is the design.

**"What if there's no coverage at the site?"** Then the sensor is unreachable and the trip goes to
**HOLD** and back to the paper process. Unverified is never fraud. Trip 07 is exactly this. We fail
to the status quo, never to an accusation.

**"What if the operator's data is wrong or late?"** Geofence events arrive as CloudEvents within
seconds — we verified this end to end, every subscription produced an event, the first 8 seconds
after creation. If they do not arrive, the agent falls back to polling and labels the run
"polling fallback used" on screen.

**"You're locked into Nokia."** We call **CAMARA** APIs — a Linux Foundation standard under GSMA
Open Gateway. Nokia Network as Code is one aggregator. The client is one thin wrapper
(`saqqa/nac/client.py`); swapping aggregator is a day's work, not a rewrite.

**"The API calls will cost more than they save."** Measured, not estimated: **10.4 calls and 13.6¢
per trip** live. A Jordanian truckload is worth about **$30**, so verification is **0.45%** of
transaction value. Stopping 2% of overbilling returns **4.5×** the verification spend.

---

## 4. The sensor and the hardware

**"Who buys and installs the sensors?"** The buyer — the party who is currently paying for water
they cannot verify. It is capex on the tank they already own, not on the contractor's fleet, which
is precisely why it is adoptable without the contractor's permission.

**"What if the sensor breaks?"** HOLD, maintenance ticket, paper fallback. Never an accusation.

**"Tanks are shared. What if two trucks fill one tank at once?"** **This is a genuine gap.** Our
model attributes the whole rise in a window to one trip, so two overlapping deliveries into one
tank would be credited twice. None of our twelve scenarios covers it. The fix is dwell-window
attribution — split the rise by which cab SIMs the network places in the zone and when — but it is
not built. Say so plainly if asked; do not improvise an answer.

**"Hardware is Phase 3 — so this is simulated."** The tank trace is a pump model with its
parameters on screen and labelled as simulated. Every CAMARA call is real: **125 live calls,
0 errors, median 291 ms** in the last full run, with real CloudEvents at our webhook. We are
explicit about the boundary on the page itself.

---

## 5. The agent

**"Why an agent at all? These are just rules."** The gate is rules, deliberately. The agent exists
for the two things rules cannot do: deciding **which checks are worth buying** for this trip given
site type, contractor history and cost, and deciding **what to ask next** when evidence conflicts.
Trip 11 runs three investigation rounds and then stops because nothing more the network can say
would change the decision. A fixed rule set either buys every check every time (expensive) or
misses the conflict entirely.

**"Is it reproducible for an audit?"** The decision is. The gate is deterministic and every call's
request, response, latency and mode is recorded verbatim. The model's prose varies; the verdict
does not.

**"What if the model is down?"** Per-call fallback chain — Flash-Lite, then Flash, then Groq Llama 3.3 70B when a key is set, then a template.
The dashboard prints which one wrote the note. We caught a real bug where one timeout permanently
demoted the whole run to template, precisely because the page says.

---

## 6. Business and adoption

**"Why would a contractor ever agree to this?"** They do not have to like it; the buyer makes it a
condition of the contract, the way fleet telematics already is in logistics. And there is a real
upside for an honest contractor: **faster payment**. Today an honest trip waits on a paper cycle.
With Saqqa a clean trip releases the same day, with the evidence attached. Trip 03 — the
over-scheduled tank — releases and flags **dispatch**, not the contractor.

**"They'll collude with the site storekeeper."** Collusion at the tank is exactly what the network
layer breaks: the storekeeper cannot make the operator say the truck was there, and the truck
cannot make the tank rise. Trip 09, trip inflation, catches a fourth delivery off one 10 m³ load
using capacity accounting the storekeeper has no control over.

**"Fraud will just move somewhere else."** Probably, and we would say so. It moves to attacks that
are harder and more expensive than a signature — which is the entire point. We are raising the cost
of fraud, not claiming to end it.

**"What if the buyer's own staff are complicit?"** A real limit. Saqqa makes the evidence external
and immutable, so complicity becomes visible in the record rather than invisible in a signature —
but it does not stop a payer who wants to be defrauded. Nothing technical does.

**"Why hasn't anyone done this?"** Network APIs for location and fraud only became commercially
reachable through CAMARA and GSMA Open Gateway in the last couple of years. The primitive is new;
the problem is old.

---

## 7. Ethics and law

**"This is surveillance of drivers."** No household or personal handset is in the system. The cab
SIM belongs to the fleet operator, and what is read is zone crossings of a **commercial vehicle on
a contracted trip** — narrower than the GPS telematics those fleets often already run.

**"What if you wrongly escalate an honest contractor?"** ESCALATE is not a verdict of fraud. It
opens a case for the payer's supervisor with the full trace attached and notifies the contractor.
The audit note is written in English **and Arabic** so the accused can read the reasoning. The
investigate step is explicitly instructed to prefer checks that could **exonerate** an honest
contractor.

**"Could this delay water reaching people who need it?"** The most important question in the set,
and the reason HOLD exists. An unverified trip is not blocked — it goes back to the paper process
it came from. The only decision that stops money outright is BLOCK, and that is triggered by the
**payee's** identity changing, not by anything about the water. Water delivery is never gated on
our verdict; payment is.

---

## 8. What we concede

Do not defend these. Name them.

1. **Concurrent deliveries into one tank are not handled** (§4). Real, unbuilt.
2. **No hardware yet.** The sensor is a model; Phase 3.
3. **The trip timeline is scripted.** Sandbox simulators have fixed positions and cannot drive a
   truck through two zones, so the *timeline* is ours — the calls that attest to it are real, and
   the dashboard says which is which on every run.
4. **Most of our APIs are not commercially live in MENA yet.** Sourced (GSMA Open Gateway map, dataset 12 September 2026, `shared/evidence/gsma_open_gateway_mena_2026-09-12.md` in the team repository): only SIM Swap
   and Device Roaming Status are; Location Verification, which `core` depends on, is not. Pricing is
   per-deal; there is no published price list. We model 1–5¢ and say it is indicative.
5. **On `core`, a sensor SIM moved into a device still sitting at the tank would pass.** It fails
   on `full` via Device Swap.
6. **Twelve scenarios are ours.** They are seeded, not sampled from a real fleet.

---

## The three sentences to end on

> The tank sensor is the meter. The network is the meter-reader nobody can bribe. The agent is the
> billing engine.
