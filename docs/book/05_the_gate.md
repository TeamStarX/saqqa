## 5 · The gate

The gate is the part of Saqqa a finance desk can re-run by hand. It reads the signals from chapter 3 and the network facts from chapter 2 and returns one of four decisions with the litres to pay. The rules are ordered by the severity of what would go wrong if we paid; the first rule that fires wins.

### The four decisions

| Decision | Meaning | Money |
|---|---|---|
| RELEASE | Pay the measured litres now. | measured litres, capped at the claim |
| HOLD | Pay only what is verified; hold the rest pending the contractor, or send the trip to the paper process. Never an accusation. | verified litres, or none |
| ESCALATE | Open a case for the payer's supervisor with the full trace; notify the contractor; pay nothing. | none |
| BLOCK | Stop the payment itself: the payee's number is not safely the payee's. | none |

### The rules, in the order they are applied

1. **Payee SIM-swapped** within the 72-hour window → BLOCK. The delivery may be perfect; the money still does not move to a hijacked number.
2. **Ghost trip**: the fleet SIM never entered the tank zone, Location Verification is FALSE or absent, and the tank did not rise → ESCALATE. If the fleet SIM is roaming, the reason names the country: cross-border diversion.
3. **Sensor unreachable** → HOLD. Unverified, never fraud. Maintenance ticket; the trip goes to the F-306 paper process. If the sensor SIM also shows a device swap, that flag is attached to the ticket for a security check rather than turned into an accusation.
4. **Sensor tamper**: the sensor SIM moved into another device, or no longer verifies at its install point → ESCALATE.
5. **Capacity exceeded**: litres credited since the last verified source visit plus this delivery exceed the truck → ESCALATE (trip inflation).
6. **No source visit** before a first delivery off a load → ESCALATE (nothing verifiable was loaded).
7. **Implausible feed**: more than 25 cm in one minute → ESCALATE (feed integrity, no credit).
8. **Trace contradicts the network**: the level rose entirely outside the operator's dwell window → ESCALATE, "measurement not believed", not credited to this truck.
9. **Unregistered delivery**: the tank rose with no contracted truck in the zone → ESCALATE.
10. **Turbidity** above 5 NTU during the fill → ESCALATE (untreated water; the contracted load was diverted).
11. **Impossible fill time**: dwell shorter than 60% of the minutes needed to pump the measured litres → ESCALATE.
12. **Closed valve**: 15 minutes or more of dwell and the level did not move → ESCALATE.
13. **Short fill** (measured under 90% of claimed): if the tank could not have taken more, RELEASE the measured litres and flag dispatch; otherwise HOLD, pay verified litres only, ask the contractor.
14. Otherwise **RELEASE** the measured litres.

Thresholds (72 h, 25 cm, 60%, 5 NTU, 15 min, 90%) are in `gate.py` and `config.py`; they are defensible engineering defaults, not tuned on field data.

### The twelve trips, as they ran live

Every row below is from the last full live run (`runs/*.json`, {{stats.calls_total}} real calls, {{stats.errors}} errors). "Calls" is the number of CAMARA calls the agent made for that trip; "rounds" is how many investigation rounds it took.

| Trip | Decision | Paid | Calls | Rounds | Why, in the gate's words |
|---|---|---|---|---|---|
| {{runs.honest.title}} | {{runs.honest.decision}} | {{runs.honest.pay_m3}} m³ · {{runs.honest.amount_iqd}} IQD | {{runs.honest.calls}} | {{runs.honest.investigations}} | {{runs.honest.reason}} |
| {{runs.short_fill.title}} | {{runs.short_fill.decision}} | {{runs.short_fill.pay_m3}} m³ | {{runs.short_fill.calls}} | {{runs.short_fill.investigations}} | {{runs.short_fill.reason}} |
| {{runs.tank_full.title}} | {{runs.tank_full.decision}} | {{runs.tank_full.pay_m3}} m³ | {{runs.tank_full.calls}} | {{runs.tank_full.investigations}} | {{runs.tank_full.reason}} |
| {{runs.valve_closed.title}} | {{runs.valve_closed.decision}} | 0 | {{runs.valve_closed.calls}} | {{runs.valve_closed.investigations}} | {{runs.valve_closed.reason}} |
| {{runs.ghost_trip.title}} | {{runs.ghost_trip.decision}} | 0 | {{runs.ghost_trip.calls}} | {{runs.ghost_trip.investigations}} | {{runs.ghost_trip.reason}} |
| {{runs.substitution.title}} | {{runs.substitution.decision}} | 0 | {{runs.substitution.calls}} | {{runs.substitution.investigations}} | {{runs.substitution.reason}} |
| {{runs.sensor_offline.title}} | {{runs.sensor_offline.decision}} | 0 | {{runs.sensor_offline.calls}} | {{runs.sensor_offline.investigations}} | {{runs.sensor_offline.reason}} |
| {{runs.sensor_tamper.title}} | {{runs.sensor_tamper.decision}} | 0 | {{runs.sensor_tamper.calls}} | {{runs.sensor_tamper.investigations}} | {{runs.sensor_tamper.reason}} |
| {{runs.trip_inflation.title}} | {{runs.trip_inflation.decision}} | 0 | {{runs.trip_inflation.calls}} | {{runs.trip_inflation.investigations}} | {{runs.trip_inflation.reason}} |
| {{runs.payee_swapped.title}} | {{runs.payee_swapped.decision}} | 0 | {{runs.payee_swapped.calls}} | {{runs.payee_swapped.investigations}} | {{runs.payee_swapped.reason}} |
| {{runs.sensor_contradicts_network.title}} | {{runs.sensor_contradicts_network.decision}} | 0 | {{runs.sensor_contradicts_network.calls}} | {{runs.sensor_contradicts_network.investigations}} | {{runs.sensor_contradicts_network.reason}} |
| {{runs.manipulated_feed.title}} | {{runs.manipulated_feed.decision}} | 0 | {{runs.manipulated_feed.calls}} | {{runs.manipulated_feed.investigations}} | {{runs.manipulated_feed.reason}} |

Two RELEASE, two HOLD, seven ESCALATE, one BLOCK. The two RELEASE rows are the point of the system as much as the seven ESCALATE rows: an honest hauler is paid the same day, and a short fill caused by dispatch over-scheduling the tank is paid for what fit and flagged against dispatch, not the contractor.

### How the scenarios map to the sandbox

Each trip is built from the four sandbox personas (chapter 2): the honest truck and sensor are `…1001`; a ghost truck or a moved sensor SIM is `…1000` (Location Verification FALSE, swapped, roaming); an unreachable sensor is `…1003`. The trip timeline (when the truck entered and left each zone) and the sensor trace are the scenario's. So the network evidence in every row is real, and the story it is asked about is scripted; the dashboard says which is which on every run.

### The run to watch, step by step

"The agent doubts its own sensor." Tank 7 rises 9.8 m³ between 09:05 and 09:27. The operator's stamps put the truck in the zone from 09:35 to 10:03.

1. `score` finds the contradiction: the rise and the dwell do not overlap at all.
2. `investigate`, round 1: the model re-asks the sensor's reachability (could the timestamps be a reporting lag?) and retrieves the truck's location.
3. `investigate`, round 2: nothing more the network can tell us; the model says so and stops.
4. `decide`: rule 8 fires. Measurement not believed. Not credited to this truck. Case opened.
5. `explain`: the note says exactly that, in English and Arabic, and names the strongest network evidence.

Our own sensor loses to the operator's timestamps, because the sensor is ours and the timestamps are nobody's. Nobody is accused; the case names a possible unregistered delivery or a manipulated trace and leaves it to a person.
