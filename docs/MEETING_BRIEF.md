# The mentor meeting: what to ask, what to say, what to show

Furkan Acık, Türk Telekom. Mentorship window closes **10 September**; the phase closes 13 September. So the call
must happen early enough that his answers can still change the build. Contact only the assigned mentor; the
organisers say contacting any other mentor may lead to disqualification. Send a short mail with the one-paragraph
summary and three questions; bring the rest to the call.

This is the critical analysis Evan asked for. It builds on the MENTOR_BRIEF Evan wrote on 31 August and changes it
where the live evidence since then changes the answer.

---

## The one thing to get right

He is an operator engineer. He will not be impressed that it works; he will look for the sentence where we
misunderstand what a network can attest. The whole meeting is won or lost on whether we sound like people who
know exactly what is real, what is scripted, and what is simulated, before he asks. Lead with that. Chapter 0 of the
field manual is the script for it.

Do not ask him to validate the idea. It is shortlisted; that question is answered. Ask the things only somebody
inside a telco knows.

---

## The one paragraph, for the mail

> We are Team StarX, shortlisted with Saqqa (Theme 6). A water delivery in MENA is paid on the word of the person
> being paid: UNHCR's F-306 log book, a hand-written GPS coordinate and a pen signature. We put an organisation SIM in
> the tanker cab and another in a level sensor on the buyer's own tank, and a LangGraph agent uses Geofencing,
> Location Verification, Location Retrieval, Device Reachability, Device Swap, SIM Swap and Device Roaming to work out
> what actually happened before money moves. No household is ever queried. The prototype runs live against the Nokia
> sandbox (125 calls, no errors, real geofence CloudEvents at our webhook) and decides twelve seeded deliveries
> correctly. The questions we most need an operator's view on are about pricing, commercial availability in the
> region, and how these APIs behave for M2M SIMs in production.

---

## The three questions to lead with

**1. What does a CAMARA call actually cost, and is a subscription priced differently from a request?**
Our margin turns on it and it is the one number we are guessing: we assume about a cent per call and carry it as an
indicative cost table; a ten-to-twelve-call trip is about 13 cents against a $30–70 delivery. If a call is five cents
the margin is fine; at ten cents the pricing changes. Ranges, orders of magnitude, or how operators think about pricing
these at volume are all more useful than a rate card. The follow-up matters more than the headline: a standing
geofence subscription that fires four events per trip is the backbone of the design. If subscriptions are priced per
event or per day rather than per creation, the architecture changes.

**2. Which of these seven are commercially live with a MENA operator today, and which are 12–24 months out?**
Our reading of GSMA's deployment database (22 August dataset): SIM Swap and Number Verification are live in several
markets, Device Roaming is live with e& in Egypt, Location Verification, Location Retrieval and Geofencing are not
yet live with any MENA operator. If that is right, the payment-integrity half of Saqqa is deployable now and the
delivery-verification half is not, and we would rather sequence the product around that than pretend otherwise. Türk
Telekom's own Open Gateway position is the thing to ask for directly: which of these does it expose, to whom, and
through which channel (operator-direct, Aduna, Nokia NaC).

**3. How do these APIs behave for M2M SIMs, and how does consent work for organisation-owned lines?**
Every SIM we query is in a truck cab or a tank sensor, not a phone. We use Device Swap to detect that a sensor's SIM
has been moved into another device, and Reachability sampled over time as a sensor-health signal. Does that work the
way we think on a real network, and are M2M SIMs treated differently by these APIs? On consent: our position is that
every line belongs to an organisation that signed the contract and there is no natural person in the system, so
two-legged authorisation agreed at onboarding applies, the way operators already sell SIM Swap to banks. We want to be
told if we are wrong before a judge tells us. (Evan's brief flagged UAE TDRA Art. 24.6 as the place this might bite.)

The question Evan's brief led with on event delivery is answered since 2 September and should be *stated*, not asked:
every geofence subscription we create produces a CloudEvent at our sink within eight seconds. What remains to ask is
production behaviour: realistic latency from a boundary crossing to the webhook, what happens to events when the sink
is down, whether there is a replay or dead-letter path, and what `subscription-ends` with `NETWORK_TERMINATED` means in
practice (we receive it on the sandbox and do not yet know its production semantics).

---

## If there is time, in this order

4. **Who inside an operator buys this?** Is a UN agency or a municipality paying for API calls a customer the
   enterprise team wants, or is the volume too small to be interesting? Our revenue-share line assumes it is
   attractive; that assumption is ours, not theirs.
5. **What kills submissions at this stage?** He has seen the field. Ask it plainly.
6. **Geofence minimum radius in production.** Nokia's sandbox enforces 2,000 m. Is that the network's floor or the
   sandbox's? Our attribution argument is built on designing for coarseness; if production is finer, the argument
   only gets easier, and it is worth knowing.
7. **Location Retrieval's returned radius.** In the sandbox it is a fixed 1 km circle. On a real network, how tight
   does it get in a district like Al-Zubair, and does it degrade with density?

---

## What to say, in the order it lands

1. The sentence: a water delivery is paid for on the word of the person being paid.
2. The division of labour: the sensor is the meter; the network is the meter-reader nobody can bribe; the agent is
   the billing engine. The network does not measure water and we never say it does.
3. What is real: 125 live calls, 0 errors, real CloudEvents; what is scripted: the trip timeline; what is simulated:
   the tank trace. Say this before he asks.
4. The run to watch: the agent doubting its own sensor. Judgement in the investigation, rules where money moves.
5. The commercial line: somebody already pays for all of this against a piece of paper; we attach verification to a
   payment that already happens hundreds of times a day, and the operator gets a customer category it does not have.
6. Then the questions.

---

## What to show, if he wants to see it

- The live dashboard, the "agent doubts its own sensor" trip, with the calls table expanded on one row so he sees a
  real request and response. Then the webhook list against the subscription ids.
- The events table count (chapter 2 of the field manual): hundreds of real CloudEvents from the platform.
- Evan's CLI `catalogue` view if he asks about the economics of each question: what each check costs and what it is
  worth, which is the argument for an agent instead of a checklist.
- Chapter 0's table of what is real, scripted, simulated and stubbed. Lead with it rather than being asked for it.

---

## What he will push on, and the answers

| He says | We say |
|---|---|
| "The network is garnish; the sensor does the work." | True for litres, and we say so. The network answers whose truck, from which well, whether the sensor is still where we put it and still in its own housing, and whether the payee is still the payee. Those are the questions a self-reporting device cannot answer honestly, because the device belongs to the party being audited. |
| "A GPS tracker gives you metres." | Resolution is the wrong axis. A tracker reports its own position and can be made to lie; the operator's timestamps are coarse and belong to nobody in the transaction. Two thousand metres you cannot forge beats five metres you report yourself. |
| "Two trucks in one zone, one tank rises. Which one?" | The network cannot say, and we do not claim it can. Assigned routes, dwell, and capacity accounting (litres credited to a truck since its last verified load cannot exceed the truck) decide it. A truck-to-tank handshake is a later, non-CAMARA upgrade we do not pitch. |
| "Your sensor is your own hardware. Why should I trust it?" | You should not, and neither does the agent. It reads the network first and the sensor second, and when they disagree the network wins. The run to watch is exactly that. |
| "None of the location APIs are live in the region." | Correct, and stated on every screen. SIM Swap is certified in Iraq and live in the Gulf; the payment-integrity half deploys first. The location half is sequenced on operator readiness, and Saqqa gives an operator a reason to expose it. |
| "The sandbox cannot move a truck." | Correct. The trip clock is ours; the calls that attest to it are real; the events prove delivery, not movement. We say this unprompted. |
| "Why an LLM at all?" | It decides what to ask and when to stop asking, and it writes the audit note. It never decides money; the gate is deterministic and an auditor can re-run it without a model. |
| "Who pays?" | The party that already pays against paper: hotels and businesses buying by the cubic metre in Jordan (three quarters of sales), agencies funded at a fifth of need who must show donors where every dollar went. Cents per verified delivery, a flat fee per instrumented tank, and a share for the operator. |

---

## What not to do

- Do not ask him to validate the idea.
- Do not send him the deck and ask for feedback on the deck. Send the three questions.
- Do not claim a number that is not in chapter 0's table. If you do not have it, say so.
- Do not soften a weakness he raises. Agree, then say what the design does about it (chapter 6).
- Do not describe the field officer or the driver as corrupt. The failure is structural: the wrong party holds the
  pen. Rooms that contain people who work for those agencies hear the difference.

---

## After the call

Write down his answers to questions 1–3 the same day, verbatim where you can, and put them in the field manual's
chapter 6 as "what the operator said". If any answer changes the build (subscription pricing, M2M behaviour), there
are three days between the end of the mentorship window and the deadline to act on it.
