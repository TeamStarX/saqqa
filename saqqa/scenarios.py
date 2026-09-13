"""Seeded delivery scenarios (README §5.7 of the Round-1 dossier, plus the runs the judges asked for).

Each scenario is one trip: what the dispatch system claims, what the operator's network says (geofence event
timestamps for the truck SIM), and what the tank sensor reports. The simulator numbers route to Nokia's
scripted personas (see saqqa/nac/fixtures.py), so the same scenario behaves identically in fixture and live mode.

Times are HH:MM on the day of delivery; the sensor trace covers 08:30-10:30.
"""
from __future__ import annotations

from copy import deepcopy

CLEAN, DIRTY, PARTIAL, LOST = "+99999991001", "+99999991000", "+99999991002", "+99999991003"

_BASE_TRIP = {
    "trip_id": "4821",
    "contractor": "Al-Furat Water Transport",
    "contractor_history": "clean",          # clean | mixed | flagged
    "site_type": "camp",                    # camp | city | hotel
    "truck_id": "T-14",
    "truck_sim": CLEAN,
    "truck_capacity_m3": 10.0,
    "source_id": "S1",
    "tank_id": "K7",
    "tank_sim": CLEAN,
    "payee_msisdn": CLEAN,
    "claimed_m3": 10.0,
    "scheduled": "08:40",
    "credited_since_source_m3": 0.0,        # litres already credited to this truck since its last verified source visit
}

_BASE_NETWORK = {"S1": {"entered": "08:41", "left": "08:58"}, "K1": {"entered": "09:35", "left": "10:03"}}

_BASE_SENSOR = {"level0_cm": 38.0, "rise_cm": 98.0, "rise_start": "09:40", "rise_minutes": 22, "turbidity_ntu": 1.2,
                "offline": False, "step": False}


_TRIP_NO = 4821


def _mk(id: str, title: str, story: str, expect: str, trip: dict | None = None, network: dict | None = None,
        sensor: dict | None = None, tags: list[str] | None = None, label: str | None = None) -> dict:
    """One seeded trip. `label` is the short name the trip list shows; `title` is the full sentence."""
    global _TRIP_NO
    t, n, s = deepcopy(_BASE_TRIP), deepcopy(_BASE_NETWORK), deepcopy(_BASE_SENSOR)
    _TRIP_NO += 1
    t["trip_id"] = str(_TRIP_NO)          # each trip is its own record, not twelve copies of #4821
    t.update(trip or {})
    if network is not None:
        n = network
    s.update(sensor or {})
    return {"id": id, "label": label or title.split(":")[0], "title": title, "story": story, "expect": expect,
            "trip": t, "network": n, "sensor": s, "tags": tags or []}


SCENARIOS: list[dict] = [
    _mk("honest", "Honest delivery",
        "T-14 loads at the licensed well, drives to Camp Al-Zubair, discharges 9.7 m³ into Tank 7 in 22 minutes. Every check is clean.",
        "RELEASE"),
    _mk("short_fill", "Short fill: 6 of 10",
        "The truck arrives and discharges, but the tank rises 60 cm, not 100. The contractor claims 10 m³.",
        "HOLD", network={"S1": {"entered": "08:41", "left": "08:58"}, "K1": {"entered": "09:35", "left": "09:52"}},
        sensor={"rise_cm": 60.0, "rise_minutes": 14}, label="Short fill, 6 of 10"),
    _mk("tank_full", "Tank was nearly full: 5.8 m³ was all it could take",
        "Dispatch over-scheduled the tank. The truck delivered what fit. Short fill by the number, not by intent.",
        "RELEASE", network={"S1": {"entered": "08:41", "left": "08:58"}, "K1": {"entered": "09:35", "left": "09:51"}},
        sensor={"level0_cm": 140.0, "rise_cm": 58.0, "rise_minutes": 13}, label="Tank was nearly full"),
    _mk("valve_closed", "Showed up, never opened the valve",
        "The truck dwells 22 minutes in the tank zone. The level does not move.",
        "ESCALATE", network={"S1": {"entered": "08:41", "left": "08:58"}, "K1": {"entered": "09:35", "left": "09:57"}},
        sensor={"rise_cm": 0.6}, label="Never opened the valve"),
    _mk("ghost_trip", "Ghost trip: truck never at the tank",
        "The dispatch claims a delivery. The operator's network never saw the fleet SIM enter the tank zone.",
        "ESCALATE", trip={"truck_sim": DIRTY}, network={"S1": {"entered": "08:41", "left": "08:58"}, "K1": None},
        sensor={"rise_cm": 0.0, "rise_start": None}, tags=["investigate"], label="Ghost trip"),
    _mk("substitution", "Substitution: clean load sold, dirty water dumped",
        "The level rises 9.7 m³ but turbidity jumps to 41 NTU. The contracted water went somewhere else.",
        "ESCALATE", sensor={"turbidity_ntu": 41.0}, tags=["investigate"], label="Substitution: dirty water"),
    _mk("sensor_offline", "Sensor offline: unverified, not fraud",
        "The tank SIM is unreachable during the delivery window. Nobody is accused; the trip falls back to the paper process.",
        "HOLD", trip={"tank_sim": LOST}, sensor={"offline": True}, label="Sensor offline"),
    _mk("sensor_tamper", "Sensor SIM moved into another device",
        "The tank rises on cue, but the sensor's SIM has changed handsets and no longer verifies at its install point.",
        "ESCALATE", trip={"tank_sim": DIRTY}, label="Sensor SIM moved"),
    _mk("trip_inflation", "Trip inflation: 4th delivery off one 10 m³ load",
        "The truck has already been credited 9.8 m³ since its last verified source visit. It cannot have 8 m³ more on board.",
        "ESCALATE", trip={"claimed_m3": 8.0, "credited_since_source_m3": 9.8},
        network={"S1": None, "K1": {"entered": "09:35", "left": "09:55"}}, sensor={"rise_cm": 80.0, "rise_minutes": 18}, label="Trip inflation"),
    _mk("payee_swapped", "Payee number SIM-swapped yesterday",
        "The delivery is perfect. The number the money would go to changed SIM 19 hours ago.",
        "BLOCK", trip={"payee_msisdn": DIRTY}, label="Payee SIM-swapped"),
    _mk("sensor_contradicts_network", "The agent doubts its own sensor",
        "Tank 7 rises 9.7 m³ between 09:05 and 09:27. The operator's timestamps put T-14 in the zone only from 09:35. The measurement is not believed.",
        "ESCALATE", sensor={"rise_start": "09:04"}, tags=["investigate", "hero"], label="Agent doubts its sensor"),
    _mk("manipulated_feed", "Manipulated sensor feed",
        "The whole 98 cm arrives in a single one-minute sample. Water does not do that; a spoofed feed does.",
        "ESCALATE", sensor={"step": True}, label="Manipulated feed"),
]

BY_ID = {s["id"]: s for s in SCENARIOS}


def get(id: str) -> dict:
    return deepcopy(BY_ID[id])
