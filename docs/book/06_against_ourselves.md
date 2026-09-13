## 6 · Against ourselves

The case against Saqqa, made as well as we can make it, because a team that has not attacked its own system will be doing it for the first time in front of a judge. Much of this chapter was first written by Evan on 31 August against the synthetic-era build; it is kept where it still holds and changed where the live evidence changed it. Nothing here is softened.

### The best attacks

**Substitution inside the zone.** The strongest attack anyone has found. Load clean water, drive to the tank zone, discharge dirty water: right truck, right zone, right dwell, right volume. Every network check passes, because every network check is about the truck, not the water. *Answer:* a ten-dollar turbidity probe on the same sensor, which is why the sensor was specified with one from the start; UNHCR's form already asks a human to log turbidity by hand for exactly this reason, so we automate a control the sector already believes in. In the live run the substitution trip escalated on 41 NTU. *Residual:* turbidity is not potability. Clear contaminated water passes. Say so.

**Leave the cab SIM at the depot.** The truck SIM is in the cab, not welded to the tank. Move it to a car that drives the correct route while the tanker goes elsewhere. *Answer:* partial. The tank is the thing that has to rise, and the decoy car cannot make it rise; the attack converts a diversion into "truck attested present, tank did not move", which is the closed-valve rule and a human looks. *Residual:* combined with a tampered sensor it is a genuine hole, which is why the tamper checks are cheap and run on every trip.

**Collusion with the site.** The site representative and the contractor agree to under-deliver and split the difference. *Answer:* this is the attack Saqqa is most effective against, and worth leading with, because it is the one the paper system is worst at. The representative's cooperation is worthless when the measurement comes off an instrument they do not control and the payment comes from a rule they cannot argue with. Removing the signature from the payment path removes the thing being bought.

**Attack the sensor's power.** Do not tamper with the sensor; make it unreachable, so every delivery falls back to paper and the old fraud resumes with a clean conscience. *Answer:* real, and mostly unsolved. The mitigation is that the unverified rate is a monitored metric per site and per contractor, so a site whose sensor is mysteriously offline for a third of deliveries becomes visible as a pattern even though no single trip is ever called fraud. That is a detection story, not a prevention story, and it should be described as such.

**Two trucks, one zone.** Two contracted trucks inside the same 2 km zone; one tank rises. *Answer:* the network cannot say which, and we do not claim it can. Assigned routes, dwell, and capacity accounting decide it. A truck-to-tank handshake is a later, non-CAMARA upgrade we do not pitch. The judge's ceiling analysis in Round 1 scored this as structural, and it is.

**The thresholds are made up.** 25 cm in a minute, 60% of pump time, 5 NTU, 90% fill ratio. *Answer:* yes. They are engineering defaults in one readable file (`gate.py`, `config.py`), not inside a prompt or a trained weight, precisely so they can be argued with and tuned against real outcomes once a pilot produces some. The alternative on offer, a model trained on data nobody has, would hide the assumption instead of printing it.

### The counterfactual that caps us

The Round-1 judge's hardest finding, and it stands: Saqqa is buildable at higher precision with a payer-issued tamper-evident GPS tracker, the same tank sensor and an LTE modem, and no CAMARA at all. Once the payer issues both SIMs as a contract condition, "the audited party owns the hardware" no longer applies to the truck unit either. Our answer is forgeability, not resolution: a tracker reports its own position and can be made to lie; the operator's timestamps belong to nobody in the transaction. That answer is true. It is also an argument about trust rather than about capability, and a judge who scores capability will cap us for it. Know which argument you are making.

The second structural finding follows from the first: the load-bearing proof is a level sensor, which is neither novel nor CAMARA. We concede it in chapter 1. Conceding it does not un-cap it.

### What would make us wrong

Four things could sink this that are not engineering problems.

1. **The location APIs do not go commercially live in MENA.** Today SIM Swap is certified with Asiacell (Iraq) and live with several Gulf operators, Number Verification is live in several markets, Device Roaming is live with e& Egypt; Location Verification, Location Retrieval and Geofencing are live with nobody in the region. Without them the payment-integrity half of Saqqa ships and the delivery-verification half does not. This is the largest external dependency and belongs on a slide, not in a footnote. It is also the reason the mentor call matters (chapter 7).
2. **Sensors break or get stolen faster than assumed.** A high unverified rate turns Saqqa into an expensive way to keep filing the same paper form. Hardware reliability at a camp in Basra is a genuine unknown and we have tested none of it.
3. **The buyer does not want the answer.** The least technical and the most common killer of systems like this. A procurement officer whose department signed the contract may have no appetite for a measured shortfall entering the record. It is why the first customer should be a commercial buyer who keeps the money they save, rather than an institution where the saving accrues to somebody else's line and the embarrassment to theirs.
4. **The unit economics turn on a price we do not know.** Nokia does not publish sandbox pricing and no MENA operator publishes a rate card. Our cost table is indicative. At a few cents a call the margin works; at ten cents per call, at our fee, it does not. This is question one for the operator.

### What the sandbox can and cannot prove

Say this before anyone asks; it is the cheapest credibility available.

- **Proven:** every request and response shape; 125 real calls with no errors in the last full run; median latency under 300 ms; webhook delivery of CloudEvents for every subscription, with subscription ids that match; the agent asks the right questions and parses the real answers, including PARTIAL and UNKNOWN, which it does not round into a decision.
- **Not proven:** that an operator would say those things about a real truck. The simulators have fixed positions and answer per persona; the trip timeline is ours. Location Retrieval returns Budapest for every device. The demo is honest about which is which on every run.
- **Changed since Evan's 31 August version:** "geofence event delivery is unverified" is no longer true; it is verified, hundreds of times. "Every network answer is synthetic" is no longer true; there are no synthetic answers in the canonical build. "The agent ran a written fallback policy" is no longer true; a Gemini model plans, investigates and explains in every logged run, and the run says which provider wrote each note. The remaining honest weakness is smaller and sharper: the sandbox proves plumbing and parsing, not movement.

### Things we explicitly do not claim

- Zone scale, roughly two kilometres, never a single house.
- No pilot has run. There is no impact number in any of our material and there should not be one.
- The tank trace is our model. Hardware is Phase 3.
- The location APIs are not commercially live in the region; Phase 1 runs on the sandbox and says so.
- The model decides what to ask and how to explain. It never decides money.

Disclosing these is not modesty. A team that volunteers its limits is a team whose other claims get believed.

### Two behaviours worth more than any answer

Concede fast and precisely. "Two kilometres is useless in a camp" is correct; agree in four words, then explain that at a camp the tank level carries the weight and the zone check does its work on the intercity leg. Judges are testing whether you know where your own edges are.

Never claim the sandbox was an operator. If it comes out later, and it will, because someone in that room has built on CAMARA, every other claim gets re-examined. The disclosure is cheap; the recovery is not.
