# Demo video script · under 3 minutes

Screen recording of the dashboard at 1600×900, one presenter voice, no slides. `scripts/record_demo.py` films it with a wall-clock budget: live model latency varies by minutes between runs, so the third trip is filmed only if the first two left room, and is summarised in a caption otherwise. Record with the sandbox key set
(badge reads **network: live · Nokia NaC sandbox**) and Gemini configured. Say the bold sentences exactly.

| t | On screen | Say |
|---|---|---|
| 0:00 | Dashboard, "Honest delivery" selected, nothing run | **"A water delivery is paid for on the word of the person being paid."** "This is Saqqa. A sensor on the buyer's tank, a SIM in the tanker's cab, and the operator's network as the witness. Every SIM you'll see belongs to an organisation. Nobody's phone is involved." |
| 0:15 | Click **Run verification**. Trace starts: PLAN, then the four geofence subscriptions and the sensor checks stream in; the calls table fills; badge says live | "The agent plans which checks to buy, then makes them. Live, against Nokia Network as Code: four geofence subscriptions on the cab SIM, a presence check, three checks on the sensor SIM, and a SIM-swap check on the number the money would go to. Every request and response is on screen." Click one calls row to expand the raw JSON. |
| 0:45 | Truck marker moves S1 → K1; chart shows the level rising inside the green dwell window | **"Entry and exit stamps from the operator give us dwell. The tank rising inside that dwell gives us litres. Those two facts have to agree."** |
| 1:00 | DECIDE line: RELEASE · pay 9.7 m³ · 31,040 IQD; ledger row; audit note EN/AR | "Nine point seven cubic metres measured against a claim of ten. Released, same day, with the reasoning stored. The gate that released it is deterministic. The model never touches money." |
| 1:15 | Select **"The agent doubts its own sensor"**. Run. | **"Now the run that matters."** "Tank 7 rises nine point eight cubic metres between 09:05 and 09:27. The operator's timestamps put the truck in the zone from 09:35." |
| 1:35 | SCORE: "does not fit: tank rose 09:05-09:27 but the truck was in the zone 09:35-10:03". INVESTIGATE round 1: reachability re-asked, Location Retrieval on the truck | "The evidence contradicts itself, so the agent doesn't decide. It asks the sensor again whether it can be believed, and asks the network where the truck actually was." |
| 1:55 | DECIDE: ESCALATE, "measurement not believed" | **"The measurement is not believed. Our own sensor loses to the operator's timestamps, because the sensor is ours and the timestamps are nobody's."** "Not credited, case opened, nobody accused." |
| 2:10 | Select **"Sensor offline"**. Run. HOLD. | "And when the sensor is simply unreachable: unverified, never fraud. The trip goes back to the paper process it came from." |
| 2:25 | Select **"Payee SIM-swapped"**. Run. BLOCK. | "A perfect delivery, and the number the money would go to changed SIM nineteen hours ago. Blocked before a dinar moves." |
| 2:25 | Click **core · 3 APIs**, then select **"Payee SIM-swapped"**. Run. | "Twelve trips run this way. Two release, two hold, seven escalate, one blocks." **"And almost no operator has all seven of these APIs live today. So: three APIs. The ones that are."** |
| 2:40 | BLOCK, with the unchecked capabilities named in the verdict | "A perfect delivery, and the number the money would go to changed SIM inside the last 72 hours." **"Blocked, on three APIs, before a dinar moves. The agent names every check the smaller profile could not run, instead of pretending it ran them."** |
| 2:50 | Zoom out: calls table footer; the badge row | **"Seven CAMARA APIs across two categories — and every verdict still reached on the three that deploy today."** "The tank sensor is the meter. The network is the meter-reader nobody can bribe. The agent is the billing engine." |
| 2:50 | Title card | "Saqqa. Team StarX." |

Recording notes: fixture mode is acceptable if the sandbox is down, and the badge will say so; do not hide it. Keep
the cursor still while the trace streams. If Gemini is slow, the paced playback covers it.
