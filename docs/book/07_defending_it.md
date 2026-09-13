## 7 · Defending it

What to say when it is your turn to talk: to a judge, and to the operator engineer in the mentor call. The mentor-specific analysis (what to ask, what to show, what not to do) is also a standalone document, `docs/MEETING_BRIEF.md`, so it can be read in five minutes without the book.

### The questions coming, and where the answer lives

Do not memorise wording; memorise which chapter the answer comes from, so it is reconstructed rather than recited.

| Question | The answer, in one line | Ch. |
|---|---|---|
| Why not a GPS tracker? | A tracker reports its own position; anything that reports its own position can be made to lie. A trust problem, not a resolution problem. | 1 |
| Two kilometres is useless in a camp. | Agreed. At a camp the tank level is load-bearing; the zone check does its work on the source and the intercity leg. | 2, 6 |
| Is the AI actually doing anything? | It decides which paid checks to buy for this trip, what to ask next when the evidence contradicts itself, and when to stop; then it writes the note. A checklist buys everything every time. | 4 |
| What if the model hallucinates? | It cannot move money. Ordered rules do that, and an auditor can re-run them from the ledger without a model. | 5 |
| Did you run this against the real network? | Against Nokia's sandbox: 125 real calls, no errors, real CloudEvents. It proves plumbing and parsing, not that an operator said those things about a real truck. | 0, 2 |
| What about consent and privacy? | Every SIM belongs to an organisation the payer contracts with. No household is queried, and Location Verification never returns coordinates. | 2 |
| What stops someone tampering with the sensor? | Nothing stops it; the network detects it. A sensor cannot clear itself: its own trace never counts in its favour against the operator's timestamps. | 3, 5 |
| What if the sensor is just broken? | HOLD, back to paper, nobody penalised. Unverified is never fraud. | 5 |
| Two trucks in one zone? | The network cannot say which; assigned routes, dwell and capacity accounting decide it. | 6 |
| Who pays for it? | The party already paying against paper, out of the first month of recoveries. Per verified delivery, per instrumented tank, and a share for the operator. | 1, 7 |
| Why would a contractor accept this? | Same-day settlement instead of a weekly paper cycle, and a record the operator stands behind when a tank comes up short. It only bites the ones who were stealing. | 3 |
| What is your impact number? | We have not run a pilot, so we do not have one. Here is what a pilot would measure. | 6 |
| What is the biggest risk? | That the location APIs are not commercially live in MENA on a useful timescale. | 6 |
| Which of the seven is dispensable? | Any single one is nearly useless on its own; the value is in the sequence: source visited, truck present, sensor honest, litres measured, payee intact. | 2 |

### For the judges: the three minutes

Prior GSMA, Nokia and CAMARA hackathons have a documented pattern, and it is not the one an engineering team's instincts point at.

- **They opened on one person, not a statistic.** Ontime (first, MWC Barcelona 2025 Talent Arena) opened with a teammate's own problem; market size appeared at the end. Team Malaai (second, India Mobile Congress 2025) opened on a phone call from a mother. Nokia's own judge, on tape, on why a runner-up placed: "something that I personally face quite frequently." Impact is recognised, not measured.
- **Winners solve trust problems for the informal or underserved.** Africa Ignite went TrustScore (informal lending), SafeRide, GridGuard; TIM Brazil went Carteiro Amigo (address validation in favelas). Every one is the network vouching for something a formal system cannot see. Saqqa is in that lineage; say so.
- **Multiple APIs are rewarded here, unusually.** This contest's own Good-to-Have section says "utilise multiple CAMARA APIs" and "demonstrate intelligent orchestration across multiple network APIs". Seven is fine, provided we can say, as we can, that any one of them is nearly useless alone.

So: open on the form, not on Jordan's $176 million. The scan of F-306 and the sentence about a field officer who signed for water she did not see. Then the honest delivery released in one screen. Then the agent doubting its own sensor. Then the trip we deliberately do not call fraud. Close on why a coarse answer you cannot forge beats a precise one you wrote yourself. The number goes at the end, if at all. The video script in `docs/DEMO_SCRIPT.md` is built on exactly this order.

### For the operator: the mentor call

Furkan Acık of Türk Telekom; the window closes 10 September. He is an operator engineer and will look for the sentence where we misunderstand what a network can attest. Win the meeting by sounding like people who know exactly what is real, scripted and simulated before he asks.

**Do not ask him to validate the idea.** It is shortlisted. Ask the things only somebody inside a telco knows.

**Three questions to lead with:**

1. **Price.** What does a CAMARA call cost at volume, and is a standing subscription priced per creation, per event or per day? Our margin turns on it and it is the one number we are guessing. Four geofence events per trip are the backbone of the design; if subscriptions are priced per event, the architecture changes.
2. **Availability.** Which of the seven are commercially live with a MENA operator today, and which are 12–24 months out? Our reading of GSMA's deployment database: SIM Swap and Number Verification live in several markets, Device Roaming live in Egypt, the location family live with nobody. If that holds, the payment-integrity half ships first and the delivery-verification half is sequenced on operator readiness. What is Türk Telekom's own Open Gateway position, and through which channel?
3. **M2M and consent.** Every SIM we query is in a cab or a sensor. Do Device Swap and Reachability behave the way we think for M2M SIMs? Is two-legged authorisation agreed at onboarding the right consent model for organisation-owned lines, the way operators already sell SIM Swap to banks? Tell us if we are wrong before a judge does.

**State, do not ask:** webhook delivery works; every subscription produced a CloudEvent at our sink within eight seconds. Then ask the production questions: latency from a real boundary crossing to the webhook, behaviour when the sink is down, replay or dead-letter, and what `subscription-ends` with `NETWORK_TERMINATED` means in practice.

**If there is time:** who inside an operator buys this and whether a UN agency is a customer the enterprise team wants; what kills submissions at this stage; whether 2,000 m is the network's floor or the sandbox's; how tight Location Retrieval's returned radius gets in a district like Al-Zubair.

**What to show:** the live dashboard on the trip that doubts its own sensor, one calls-table row expanded to the raw request and response, the webhook list against the subscription ids, and chapter 0's table of what is real and what is not, offered before he asks.

**Afterwards:** write his answers down the same day and put them in chapter 6 as "what the operator said". There are three days between the end of the mentorship window and the deadline to act on anything that changes the build.

### The sentence to return to

If you are ever lost in a question, go back to it: the only record of a delivery is created by the party being paid for it. Every design decision downstream follows from taking that seriously. Organisation SIMs only. A sensor on the buyer's tank, not the seller's truck. The network read before the sensor. A deterministic gate. A fallback to paper rather than a penalty.
