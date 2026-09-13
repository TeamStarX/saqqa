# API usage synopsis

Seven CAMARA APIs, all on Nokia Network as Code, called through the official `network_as_code` 10.0.0 Python SDK.
Every call the agent makes is recorded with its request, response, latency and mode (`live` against the sandbox or
`fixture`), and shown verbatim in the dashboard's calls table. Method names were verified against the installed SDK.

| # | CAMARA API | Category (organisers') | SDK call | Whose SIM | What Saqqa asks | Load-bearing? |
|---|---|---|---|---|---|---|
| 1 | Geofencing Subscriptions | Device intelligence | `geofencing.create_subscription(protocol="HTTP", sink, types=[area-entered \| area-left], config={subscription_detail:{device, area(CIRCLE, 2000 m)}, initial_event, subscription_max_events})` | cab SIM | Operator-stamped entry and exit of the licensed well zone and the tank zone. Entry-to-exit is **dwell**, and dwell is what capacity accounting is built on. Four subscriptions per trip. | yes |
| 2 | Location Verification | Digital identity & anti-fraud | `location.verify_v1(device, area(CIRCLE), max_age)` → TRUE / FALSE / PARTIAL(+match_rate) / UNKNOWN | cab SIM and sensor SIM | Polling fallback for presence at the tank zone; and "the sensor is still at its install point" (anti-relocation). | yes |
| 3 | Device Reachability Status | Device intelligence | `device_status.retrieve_reachability_status(device)` → reachable, connectivity [DATA/SMS] | sensor SIM | Can the sensor be believed at all. Unreachable makes the trip *unverified*, never a penalty, and is re-asked before a trace is rejected. | yes |
| 4 | Device Swap | Digital identity & anti-fraud | `device_swap.check(phone_number, max_age=720)` → swapped | sensor SIM | The SIM is still inside the sensor, not in someone's phone. | yes |
| 5 | SIM Swap | Digital identity & anti-fraud | `sim_swap.check(phone_number, max_age=72)` → swapped; `sim_swap.retrieve_date(phone_number)` | payee number | No payment to a number hijacked since the contract was signed; the date goes on the ticket. | yes |
| 6 | Location Retrieval | Device intelligence | `location.retrieve(device, max_age)` → area (CIRCLE or POLYGON) + last_location_time | cab SIM | Where the truck was when the tank rose without it, or where it went after a short fill. Chosen by the investigate step, not run on every trip. | supporting |
| 7 | Device Roaming Status | Device intelligence | `device_status.retrieve_roaming_status(device)` → roaming, country_code, country_name | cab SIM | A fleet SIM that has left the country: cross-border diversion. Chosen by the investigate step on ghost trips. | supporting |

Subscriptions deliver CloudEvents to `POST /webhooks/camara` (verified 2 Sep 2026: a subscription created with
`initial_event=true` produced `{"type": "…area-entered", "source": "/geofencing-subscriptions/v0.3/subscriptions/<id>",
"data": {"subscriptionId", "device", "area"}}` at our sink 8 s later, from Nokia's platform). The receiver stores each
event (`events` table); the agent waits up to 12 s for its own subscriptions' events and lists them with their ids.
The sandbox fires the subscribed type on creation for every persona, so the trip clock stays the scenario's, and the
Location Verification poll stays in the plan.

## What the agent does with them

* **plan**: the four geofence subscriptions, the presence poll, the three sensor checks and the payee check are
  mandatory. Location Retrieval and Roaming are optional; the planner buys them for non-clean contractor history or city
  sites, at the cost per call shown in the trace.
* **investigate**: when the evidence contradicts itself, the agent chooses from a menu: re-ask reachability, re-verify the
  sensor's location, check device swap, retrieve the truck's location, check roaming, retrieve the SIM-swap date. It may
  ask Location Verification and Reachability twice (before rejecting a sensor) and everything else once. Up to three rounds.
* **decide**: the gate reads the signals derived from those responses. Order of severity: payee swapped → ghost trip →
  sensor unreachable (HOLD) → sensor tamper → capacity exceeded → no source visit → implausible feed → trace contradicts
  the network → unregistered delivery → turbidity → impossible fill time → closed valve → short fill → RELEASE.

## Sandbox behaviour we rely on (verified)

`…1001` clean (TRUE / not swapped / not roaming / DATA), `…1000` compromised (FALSE / swapped / roaming HU / SMS only),
`…1002` UNKNOWN (swapped, roaming), `…1003` PARTIAL and unreachable. Location Retrieval returns one fixed 1 km circle for
every simulator. SIM Swap retrieve-date returns a timestamp about ten minutes old for every number. Verified 2 Sep 2026
with 28 calls and no errors; `scripts/probe_live.py` re-verifies this from the account in use and prints the table.

## Operator readiness (GSMA Open Gateway deployment map, dataset of 22 Aug 2026)

36 commercial CAMARA deployments in MENA. SIM Swap is certified with Asiacell (Iraq, Oct 2025) and live with several Gulf
operators; Device Roaming is live with e& Egypt. The location family Saqqa leans on (Geofencing, Location Verification,
Location Retrieval) is not yet commercially live with a MENA operator, so Phase 1 runs on the Nokia sandbox and says so.
The route to market is Iraq (Asiacell / Ooredoo), then Jordan (Orange), then the Gulf.
