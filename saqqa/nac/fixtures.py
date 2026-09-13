"""Fixtures that mirror the Nokia NaC sandbox's scripted simulator outcomes.

The sandbox routes any number starting +9999 to simulators whose answers depend on the number's suffix.
Verified by calling the sandbox with scripts/probe_live.py (2 Sep 2026, 28 calls, 0 errors):
  ...1001  the clean persona: Location Verification TRUE, not SIM/device swapped, not roaming, reachable (DATA)
  ...1000  the compromised persona: Location Verification FALSE, swapped, roaming (HU), reachable (SMS only)
  ...1002  Location Verification UNKNOWN, swapped, roaming, reachable (SMS+DATA)
  ...1003  Location Verification PARTIAL, swapped, roaming, unreachable
  Location Retrieval returns the same fixed position for every simulator (47.486, 19.079, r=1000): simulators do not move.
  SIM Swap retrieve-date returns a timestamp about ten minutes old for every number, including the clean one.
`scripts/probe_live.py` prints the real mapping so this file can be corrected against the sandbox at any time.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _sfx(n: str) -> str:
    return (n or "")[-4:]


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def location_verify(phone_number: str, **_: Any) -> dict:
    s = _sfx(phone_number)
    return {"last_location_time": _now(),
            "verification_result": {"1000": "FALSE", "1001": "TRUE", "1002": "UNKNOWN", "1003": "PARTIAL"}.get(s, "UNKNOWN")}


def location_retrieve(phone_number: str, **kw: Any) -> dict:
    # The sandbox reports one fixed position for every simulator (Budapest). Mirrored exactly; the agent labels it.
    return {"last_location_time": _now(), "area": {"area_type": "CIRCLE", "center": {"latitude": 47.48627616952785, "longitude": 19.07915612501993}, "radius": 1000}}


def geofence_subscribe(phone_number: str, **kw: Any) -> dict:
    et = kw.get("event_type", "org.camaraproject.geofencing-subscriptions.v0.area-entered")
    return {"id": f"fixture-{_sfx(phone_number)}-{kw.get('zone_id', '')}-{et.split('.')[-1]}",
            "status": "ACTIVE", "starts_at": _now(), "protocol": "HTTP", "sink": kw.get("sink", ""), "types": [et]}


def reachability_status(phone_number: str, **_: Any) -> dict:
    s = _sfx(phone_number)
    table = {"1000": {"reachable": True, "connectivity": ["SMS"]},
             "1001": {"reachable": True, "connectivity": ["DATA"]},
             "1002": {"reachable": True, "connectivity": ["DATA", "SMS"]},
             "1003": {"reachable": False}}
    return {"device": {"phone_number": phone_number}, "last_status_time": _now(), **table.get(s, {"reachable": False})}


def roaming_status(phone_number: str, **_: Any) -> dict:
    s = _sfx(phone_number)
    if s == "1001":
        return {"device": {"phone_number": phone_number}, "last_status_time": _now(), "roaming": False}
    return {"device": {"phone_number": phone_number}, "last_status_time": _now(), "roaming": True, "country_code": 36, "country_name": ["HU"]}


def sim_swap_check(phone_number: str, **_: Any) -> dict:
    return {"swapped": _sfx(phone_number) != "1001"}


def sim_swap_date(phone_number: str, **_: Any) -> dict:
    from datetime import timedelta
    return {"latest_sim_change": (datetime.now(timezone.utc) - timedelta(minutes=10)).replace(microsecond=0).isoformat().replace("+00:00", "Z")}


def device_swap_check(phone_number: str, **_: Any) -> dict:
    return {"swapped": _sfx(phone_number) != "1001"}


FIXTURES = {
    "location_verify": location_verify,
    "location_retrieve": location_retrieve,
    "geofence_subscribe": geofence_subscribe,
    "reachability_status": reachability_status,
    "roaming_status": roaming_status,
    "sim_swap_check": sim_swap_check,
    "sim_swap_date": sim_swap_date,
    "device_swap_check": device_swap_check,
}
