"""Deterministic part of the agent: signals and the payment gate.

The LLM plans, investigates and explains. It never decides money. Every RELEASE / HOLD / ESCALATE / BLOCK
comes from the rules below, applied to signals computed from the network evidence and the sensor trace, so an
auditor can re-run the decision from the ledger without a model.
"""
from __future__ import annotations

from .. import config
from ..sensor.simulator import Trace, minutes


def _resp(evidence: list[dict], api: str, number: str | None = None) -> dict | None:
    for e in reversed(evidence):
        if e["api"] == api and (number is None or e.get("phone_number") == number):
            return e["response"]
    return None


def _overlap_min(a: tuple[str, str] | None, b: tuple[str, str] | None) -> int:
    if not a or not b:
        return 0
    a0, a1, b0, b1 = minutes(a[0]), minutes(a[1]), minutes(b[0]), minutes(b[1])
    return max(0, min(a1, b1) - max(a0, b0))


_CAPABILITY = {
    "geofence_subscribe": "network-stamped dwell (polled instead, with an uncertainty band)",
    "device_swap_check": "whether the sensor SIM has moved into another handset",
    "roaming_status": "whether the fleet SIM left the country",
    "location_retrieve": "where the truck went after the tank",
}


def _unchecked(prof: dict) -> list[str]:
    """Named capability gaps. A verdict that silently skips a check it could not run is a lie."""
    have = prof.get("tools", set())
    return [why for api, why in _CAPABILITY.items() if api not in have]


def observe_network(network: dict, prof: dict) -> tuple[dict, str, int]:
    """What the agent can actually see of the truck's movements on this deployment profile.

    With geofencing the operator stamps entry and exit, so the window is exact. Without it the
    agent polls Location Verification on a fixed cadence and only knows the truck was inside
    somewhere within a poll interval either side. We widen the window to the poll grid rather
    than quietly reusing the exact timestamps, because claiming stamped precision from polled
    evidence is the failure mode this profile exists to expose.
    """
    if prof.get("dwell") != "polling":
        return network, "geofence", 0
    step = config.POLL_MINUTES
    seen: dict = {}
    for zone, w in network.items():
        if not w:
            seen[zone] = None
            continue
        a, b = minutes(w["entered"]), minutes(w["left"])
        lo = (a // step) * step                      # first poll that could have caught the entry
        hi = -(-b // step) * step                    # first poll after the exit
        if hi - lo < step:                           # a dwell shorter than one interval can be missed entirely
            hi = lo + step
        seen[zone] = {"entered": _hhmm(lo), "left": _hhmm(hi)}
    return seen, "polling", step


def _hhmm(t: int) -> str:
    m = 30 + max(0, int(t))
    return f"{8 + m // 60:02d}:{m % 60:02d}"


def compute_signals(trip: dict, network: dict, trace: Trace | None, evidence: list[dict], prof: dict | None = None) -> dict:
    tank = config.TANKS[trip["tank_id"]]
    prof = prof or config.profile()
    observed, dwell_source, poll_min = observe_network(network, prof)
    k1, s1 = observed.get("K1"), observed.get("S1")
    dwell_window = (k1["entered"], k1["left"]) if k1 else None
    dwell_min = (minutes(k1["left"]) - minutes(k1["entered"])) if k1 else 0

    # --- sensor facts
    offline = trace is None or not trace.samples
    rise_window = None if offline else trace.rise_window()
    delta_cm = 0.0 if offline else (trace.delta_cm(*rise_window) if rise_window else trace.delta_cm())
    delta_m3 = round(delta_cm * tank.litres_per_cm / 1000, 1) + 0.0
    level0 = None if offline else trace.samples[0]["level_cm"]
    room_m3 = None if level0 is None else round((tank.height_cm - level0) * tank.litres_per_cm / 1000, 1)
    max_step = 0.0 if offline else trace.max_step_cm()
    turb = None if offline else trace.max_turbidity()

    # --- physics
    claimed = float(trip["claimed_m3"])
    needed_min = delta_m3 * 1000 / config.PUMP_RATE_L_PER_S / 60 if delta_m3 > 0 else 0.0
    overlap = _overlap_min(rise_window, dwell_window)
    rise_len = (minutes(rise_window[1]) - minutes(rise_window[0])) if rise_window else 0

    # --- network facts
    lv_truck = (_resp(evidence, "location_verify", trip["truck_sim"]) or {}).get("verification_result")
    lv_tank = (_resp(evidence, "location_verify", trip["tank_sim"]) or {}).get("verification_result")
    reach = _resp(evidence, "reachability_status", trip["tank_sim"]) or {}
    roam = _resp(evidence, "roaming_status", trip["truck_sim"]) or {}
    retrieve = _resp(evidence, "location_retrieve", trip["truck_sim"]) or {}

    return {
        "claimed_m3": claimed,
        "delta_m3": delta_m3,
        "fill_ratio": round(delta_m3 / claimed, 2) if claimed else None,
        "tank_room_m3": room_m3,
        "level0_cm": level0,
        "turbidity_ntu": turb,
        "max_step_cm": max_step,
        "rise_window": rise_window,
        "dwell_window": dwell_window,
        "dwell_min": dwell_min,
        "dwell_source": dwell_source,
        "unchecked": _unchecked(prof),
        "dwell_uncertainty_min": poll_min,
        "profile": prof.get("label", ""),
        "checkable": sorted(prof.get("tools", set())),
        "rise_dwell_overlap_min": overlap,
        "rise_minutes": rise_len,
        "min_minutes_to_pump_delta": round(needed_min, 1),
        "source_visited": bool(s1),
        "truck_entered_tank_zone": bool(k1),
        "truck_location_verify": lv_truck,
        "truck_roaming": roam.get("roaming"),
        "truck_roaming_country": (roam.get("country_name") or [None])[0] if roam else None,
        "truck_last_area": retrieve.get("area"),
        "sensor_online": (not offline) and reach.get("reachable", True) is not False,
        "sensor_reachable": reach.get("reachable"),
        "sensor_connectivity": reach.get("connectivity"),
        "sensor_in_place": lv_tank,
        "sensor_swapped": (_resp(evidence, "device_swap_check", trip["tank_sim"]) or {}).get("swapped"),
        "payee_swapped": (_resp(evidence, "sim_swap_check", trip["payee_msisdn"]) or {}).get("swapped"),
        "payee_swap_date": (_resp(evidence, "sim_swap_date", trip["payee_msisdn"]) or {}).get("latest_sim_change"),
        "capacity_ok": float(trip.get("credited_since_source_m3", 0)) + delta_m3 <= float(trip["truck_capacity_m3"]) + 0.3,
        "credited_since_source_m3": float(trip.get("credited_since_source_m3", 0)),
        "truck_capacity_m3": float(trip["truck_capacity_m3"]),
    }


def contradictions(sg: dict) -> list[str]:
    """Things that do not fit together. The investigate loop feeds on these."""
    out = []
    if sg["delta_m3"] >= 0.5 and not sg["truck_entered_tank_zone"]:
        out.append("tank rose but the fleet SIM never entered the tank zone")
    if sg["rise_window"] and sg["dwell_window"] and sg["rise_dwell_overlap_min"] == 0:
        out.append(f"tank rose {sg['rise_window'][0]}-{sg['rise_window'][1]} but the truck was in the zone {sg['dwell_window'][0]}-{sg['dwell_window'][1]}")
    if sg["truck_entered_tank_zone"] and sg["truck_location_verify"] == "FALSE":
        out.append("geofence says the truck entered the zone but Location Verification says FALSE")
    if sg["delta_m3"] > 0 and sg["dwell_min"] and sg["dwell_min"] < 0.6 * sg["min_minutes_to_pump_delta"]:
        out.append(f"{sg['delta_m3']} m³ needs ~{sg['min_minutes_to_pump_delta']} min at pump rate; dwell was {sg['dwell_min']} min")
    if sg["turbidity_ntu"] is not None and sg["turbidity_ntu"] > 5:
        out.append(f"turbidity {sg['turbidity_ntu']} NTU during the fill; contracted source is treated water")
    if sg["max_step_cm"] > 25:
        out.append(f"level jumped {sg['max_step_cm']} cm in one minute; a pump cannot do that")
    if sg["fill_ratio"] is not None and 0 < sg["fill_ratio"] < 0.9:
        out.append(f"claimed {sg['claimed_m3']} m³, measured {sg['delta_m3']} m³")
    if not sg["capacity_ok"]:
        out.append(f"{sg['credited_since_source_m3']} m³ already credited since last source visit; capacity {sg['truck_capacity_m3']} m³")
    return out


def gate(sg: dict) -> tuple[str, str, float]:
    """(decision, reason, pay_m3). The order is the order of severity of what would go wrong if we paid."""
    if sg["payee_swapped"]:
        when = f" (latest change {sg['payee_swap_date']})" if sg.get("payee_swap_date") else ""
        return "BLOCK", f"payee number SIM-swapped inside the 72 h window{when}: identity re-check before any payment", 0.0
    if not sg["truck_entered_tank_zone"] and sg["truck_location_verify"] in ("FALSE", None) and sg["delta_m3"] < 0.5:
        extra = ""
        if sg.get("truck_roaming"):
            extra = f"; the fleet SIM is roaming ({sg.get('truck_roaming_country')}) - cross-border diversion suspected"
        return "ESCALATE", "fleet SIM never entered the tank zone: ghost trip" + extra, 0.0
    if not sg["sensor_online"]:
        flag = "; device-swap flag on the sensor SIM attached to the ticket for a security check" if sg["sensor_swapped"] else ""
        return "HOLD", "tank sensor unreachable: unverified, not fraud; maintenance ticket raised; this trip goes to the F-306 paper process" + flag, 0.0
    if sg["sensor_swapped"] or sg["sensor_in_place"] == "FALSE":
        return "ESCALATE", "tank sensor SIM moved into another device or no longer at its install point: tamper case", 0.0
    if not sg["capacity_ok"]:
        return "ESCALATE", (f"{sg['credited_since_source_m3']} + {sg['delta_m3']} m³ credited since the last source visit exceeds "
                            f"the {sg['truck_capacity_m3']} m³ truck: trip inflation"), 0.0
    if not sg["source_visited"] and sg["credited_since_source_m3"] == 0:
        return "ESCALATE", "no contracted-source visit before this delivery: nothing verifiable was loaded", 0.0
    if sg["max_step_cm"] > 25:
        return "ESCALATE", f"sensor feed implausible ({sg['max_step_cm']} cm in one minute): feed integrity case, no credit", 0.0
    if sg["rise_window"] and sg["dwell_window"] and sg["rise_dwell_overlap_min"] == 0:
        return "ESCALATE", (f"measurement not believed: tank rose {sg['rise_window'][0]}-{sg['rise_window'][1]} while the operator "
                            f"puts the truck in the zone {sg['dwell_window'][0]}-{sg['dwell_window'][1]}; not credited to this truck; "
                            "possible unregistered delivery or manipulated trace"), 0.0
    if sg["delta_m3"] >= 0.5 and not sg["truck_entered_tank_zone"]:
        return "ESCALATE", "tank rose with no contracted truck in the zone: unregistered delivery, not credited", 0.0
    if sg["turbidity_ntu"] is not None and sg["turbidity_ntu"] > 5:
        return "ESCALATE", f"turbidity {sg['turbidity_ntu']} NTU > 5: untreated water delivered, contracted load diverted", 0.0
    if sg["dwell_min"] and sg["delta_m3"] > 0 and sg["dwell_min"] < 0.6 * sg["min_minutes_to_pump_delta"]:
        return "ESCALATE", f"{sg['delta_m3']} m³ cannot be discharged in {sg['dwell_min']} min: physically impossible fill", 0.0
    if sg["dwell_min"] >= 15 and sg["delta_m3"] < 0.5:
        return "ESCALATE", f"truck dwelt {sg['dwell_min']} min in the tank zone and the level did not move: no water delivered", 0.0
    if sg["fill_ratio"] is not None and sg["fill_ratio"] < 0.9:
        if sg["tank_room_m3"] is not None and sg["delta_m3"] >= sg["tank_room_m3"] - 0.3:
            return "RELEASE", (f"tank could only take {sg['tank_room_m3']} m³: pay {sg['delta_m3']} m³ verified; "
                               "flag dispatch over-scheduling, not the contractor"), sg["delta_m3"]
        return "HOLD", f"short fill: {sg['delta_m3']} of {sg['claimed_m3']} m³; pay verified litres only, pending contractor response", sg["delta_m3"]
    caveat = ""
    if sg.get("unchecked"):
        caveat = "; not checkable on this deployment profile: " + "; ".join(sg["unchecked"])
    if sg.get("dwell_source") == "polling":
        caveat += (f" (dwell {sg['dwell_window'][0]}-{sg['dwell_window'][1]} is polled at "
                   f"{sg['dwell_uncertainty_min']}-minute cadence, not stamped)") if sg.get("dwell_window") else ""
    return "RELEASE", (f"pay {sg['delta_m3']} m³ verified (claim {sg['claimed_m3']} m³): source visit, presence, dwell, "
                       "sensor integrity and payee all clean" + caveat), min(sg["delta_m3"], sg["claimed_m3"])
