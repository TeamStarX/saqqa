## 2 · The witness

The operator's network is the one party to a trucked-water contract that is neither paying nor being paid. This chapter is what it can tell us, what it cannot, and the proof that it answered us.

### The seven APIs, and the question each one answers

All seven are CAMARA APIs exposed on Nokia Network as Code, called through the official Python SDK (`network_as_code` 10.0.0). Two of the organisers' four categories: Device intelligence, and Digital identity & anti-fraud. Median latency per API in the last full run is from `runs/*.json`.

| API | Whose SIM | The question | Load-bearing? | Median ms | Calls in run |
|---|---|---|---|---|---|
| Geofencing Subscriptions | cab | Did the truck enter and leave the well zone and the tank zone, and when. Entry-to-exit is dwell. Four subscriptions per trip. | yes | {{stats.per_api_median.geofence_subscribe}} | {{stats.per_api_count.geofence_subscribe}} |
| Location Verification | cab, sensor | Is the truck in the tank zone now (the polling fallback). Is the sensor still at its install point. | yes | {{stats.per_api_median.location_verify}} | {{stats.per_api_count.location_verify}} |
| Device Reachability Status | sensor | Can the sensor be believed at all. Unreachable makes a trip unverified, never a penalty, and is re-asked before a trace is rejected. | yes | {{stats.per_api_median.reachability_status}} | {{stats.per_api_count.reachability_status}} |
| Device Swap | sensor | Is the sensor's SIM still inside the sensor, or in someone's handset. | yes | {{stats.per_api_median.device_swap_check}} | {{stats.per_api_count.device_swap_check}} |
| SIM Swap | payee | Has the payee's number been taken over since the contract was signed. Retrieve-date puts the change on the ticket. | yes | {{stats.per_api_median.sim_swap_check}} | {{stats.per_api_count.sim_swap_check}} |
| Location Retrieval | cab | Where was the truck when the tank rose without it; where did it go after a short fill. Chosen by the investigation, not run on every trip. | supporting | {{stats.per_api_median.location_retrieve}} | {{stats.per_api_count.location_retrieve}} |
| Device Roaming Status | cab | Has the fleet SIM left the country. Cross-border diversion. | supporting | {{stats.per_api_median.roaming_status}} | {{stats.per_api_count.roaming_status}} |

Two are bought by the planner only when the trip calls for it, which is why their counts are lower: the agent does not run every check on every load, because every call costs money (chapter 4).

### What a call looks like

This is the Location Verification call the agent made on the cab SIM in the "{{calls.location_verify.scenario}}" trip, exactly as logged: the request we sent, the response the sandbox returned, {{calls.location_verify.latency_ms}} ms.

{{calls.location_verify.request}}

{{calls.location_verify.response}}

`verification_result` is one of TRUE, FALSE, PARTIAL (with a match rate) or UNKNOWN. It never returns coordinates. The area is a circle of at least 2,000 m, because that is the minimum Nokia's geofencing accepts; we design for that coarseness rather than apologising for it (chapter 1, "forgeability, not resolution").

### The proof that the operator answers us: a real CloudEvent

The question nobody in the team could answer in Round 1 was whether the sandbox delivers webhook events at all. It does. Every Geofencing subscription the agent creates names our server as the sink; within seconds the operator platform POSTs a CloudEvent to it. This one arrived on {{event.received}} from source `{{event.body.source}}`:

{{event.body}}

The `subscriptionId` in `data` matches the subscription the agent created, so the dashboard can list each event against the call that caused it. Across all runs so far the events table holds {{stats.events_total}} real events ({{stats.events_entered}} area-entered, {{stats.events_left}} area-left, {{stats.events_ends}} subscription-ends), the first at {{stats.events_first}}.

What the events do and do not prove:

- **They prove the plumbing.** Subscription creation, sink registration, CloudEvents delivery and our receiver all work end to end against a third-party platform we do not control.
- **They do not prove the truck moved.** The sandbox simulators have fixed positions and fire the subscribed event type once, on creation, for every persona. So the agent treats live events as delivery receipts, lists them by subscription id, and keeps the scenario's timeline as the trip clock. The trace says so on every run. In production the events *are* the trip clock.

### The sandbox's personas, verified

The sandbox routes any `+9999…` number to simulators whose answers depend on the suffix. We verified the table below by calling every API on every persona (`scripts/probe_live.py`, 2 September, 28 calls, no errors), rather than reading it from documentation, because the documentation was wrong in two places.

| Persona | Location Verification | SIM / Device Swap | Roaming | Reachability |
|---|---|---|---|---|
| `…1001` (the clean subscriber) | TRUE | not swapped | not roaming | reachable, DATA |
| `…1000` (the compromised one) | FALSE | swapped | roaming, HU | reachable, SMS only |
| `…1002` | UNKNOWN | swapped | roaming | reachable, SMS and DATA |
| `…1003` | PARTIAL | swapped | roaming | unreachable |

Two things follow. Location Retrieval returns the same 1 km circle near Budapest for every number, so "where the truck was" is a real call with a meaningless answer in the sandbox, and the agent labels it. And SIM Swap's retrieve-date returns a timestamp about ten minutes old for every number, including the clean one, so the date is inert here and only the boolean is used in the gate.

The scenarios are built on these personas: an honest truck is `…1001`, a ghost truck is `…1000`, an unreachable sensor is `…1003`. That is why the same trip behaves identically in fixture mode and live mode, and why the fixtures in `saqqa/nac/fixtures.py` are a copy of this table, not an invention.

### What the network cannot do, said plainly

- It cannot measure water. The sensor does.
- It cannot tell which of two trucks inside one 2 km zone filled a tank. Attribution inside a zone rests on assigned routes, dwell, and capacity accounting (litres credited to a truck since its last verified source visit cannot exceed the truck).
- It cannot see an illegal well within 2 km of the licensed one.
- It cannot, in the sandbox, move a device. Every location answer is scripted per persona.
- It is not commercially live in the region for the location family. GSMA's own deployment database (dataset of 22 August 2026) lists 36 commercial CAMARA deployments in MENA: SIM Swap is certified with Asiacell in Iraq (October 2025) and live with several Gulf operators; Device Roaming is live with e& in Egypt; Geofencing, Location Verification and Location Retrieval are not yet live with any MENA operator. Phase 1 therefore runs on the sandbox and says so.

### How consent works, in one paragraph

Every SIM Saqqa queries belongs to an organisation: the payer issues the cab SIM and the sensor SIM as a condition of the contract, so it is the subscriber of every device it queries, and the payee check runs on the contractor's business number, agreed at onboarding. Two-legged authorisation for fraud-prevention use of SIM Swap and Device Status is the commercial norm operators already sell to banks. No household is located, messaged or asked to consent, which is what lets the same code run in a camp, a hotel and a municipality.
