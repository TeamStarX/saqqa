"""One thin wrapper around the Nokia Network as Code SDK.

Every CAMARA call the agent makes goes through `NaCClient.call`, which
  * runs live against the sandbox when a key is present (or fixtures otherwise),
  * records the exact request, the exact response, latency and mode, so the dashboard can show the
    raw exchange and the ledger can cite it,
  * never raises into the agent: a failed call comes back as {"error": ...} and the agent reasons about it.

Method names below are the ones in network_as_code 10.0.0 (verified by introspection, 2 Sep 2026):
  location.verify_v1 / location.retrieve / geofencing.create_subscription /
  device_status.retrieve_reachability_status / device_status.retrieve_roaming_status /
  sim_swap.check / sim_swap.retrieve_date / device_swap.check
"""
from __future__ import annotations

import re
import time
from datetime import datetime, timezone
from typing import Any, Callable

from .. import config
from .fixtures import FIXTURES

EVENT_ENTERED = "org.camaraproject.geofencing-subscriptions.v0.area-entered"
EVENT_LEFT = "org.camaraproject.geofencing-subscriptions.v0.area-left"


def _circle(zone_id: str, radius: int | None = None) -> dict:
    z = config.ZONES[zone_id]
    return {"area_type": "CIRCLE", "center": {"latitude": z.lat, "longitude": z.lon}, "radius": radius or z.radius_m}


def _snake(k: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", k).lower()


def _normalise(o: Any) -> Any:
    """The SDK returns camelCase keys (verificationResult, lastStatusTime); the agent reads snake_case everywhere."""
    if isinstance(o, dict):
        return {_snake(k): _normalise(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_normalise(v) for v in o]
    return o


def _dump(r: Any) -> dict:
    if hasattr(r, "model_dump"):
        return _normalise(r.model_dump(mode="json"))
    if isinstance(r, dict):
        return _normalise(r)
    return {"raw": str(r)}


def utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class NaCClient:
    def __init__(self, live: bool | None = None, sink: str | None = None, on_call: Callable[[dict], None] | None = None):
        self.live = config.LIVE if live is None else live
        self.sink = sink or config.WEBHOOK_SINK
        self.on_call = on_call
        self.calls: list[dict] = []
        self._sdk = None
        if self.live:
            if not config.NAC_API_KEY:
                raise RuntimeError("NAC_MODE=live but NAC_API_KEY is not set")
            from network_as_code import NetworkAsCodeApi  # type: ignore

            self._sdk = NetworkAsCodeApi(rapidapi_host=config.NAC_HOST, api_key=config.NAC_API_KEY)

    # ------------------------------------------------------------------ request builders (what we send)
    def _request(self, api: str, **kw: Any) -> dict:
        n = kw.get("phone_number")
        if api == "location_verify":
            return {"device": {"phone_number": n}, "area": _circle(kw["zone_id"], kw.get("radius")), "max_age": kw.get("max_age", 3600)}
        if api == "location_retrieve":
            return {"device": {"phone_number": n}, "max_age": kw.get("max_age", 120)}
        if api == "geofence_subscribe":
            return {"protocol": "HTTP", "sink": self.sink, "types": [kw.get("event_type", EVENT_ENTERED)],
                    "config": {"subscription_detail": {"device": {"phone_number": n}, "area": _circle(kw["zone_id"])},
                               "initial_event": kw.get("initial_event", True), "subscription_max_events": kw.get("max_events", 1)}}
        if api in ("reachability_status", "roaming_status"):
            return {"device": {"phone_number": n}}
        if api in ("sim_swap_check", "device_swap_check"):
            return {"phone_number": n, "max_age": kw.get("max_age", 72 if api == "sim_swap_check" else 720)}
        if api == "sim_swap_date":
            return {"phone_number": n}
        raise ValueError(f"unknown api {api}")

    # ------------------------------------------------------------------ live dispatch (what the SDK sends)
    def _live(self, api: str, req: dict) -> dict:
        c = self._sdk
        assert c is not None
        if api == "location_verify":
            return _dump(c.location.verify_v1(device=req["device"], area=req["area"], max_age=req["max_age"]))
        if api == "location_retrieve":
            return _dump(c.location.retrieve(device=req["device"], max_age=req["max_age"]))
        if api == "geofence_subscribe":
            return _dump(c.geofencing.create_subscription(protocol=req["protocol"], sink=req["sink"], types=req["types"], config=req["config"]))
        if api == "reachability_status":
            return _dump(c.device_status.retrieve_reachability_status(device=req["device"]))
        if api == "roaming_status":
            return _dump(c.device_status.retrieve_roaming_status(device=req["device"]))
        if api == "sim_swap_check":
            return _dump(c.sim_swap.check(phone_number=req["phone_number"], max_age=req["max_age"]))
        if api == "sim_swap_date":
            return _dump(c.sim_swap.retrieve_date(phone_number=req["phone_number"]))
        if api == "device_swap_check":
            return _dump(c.device_swap.check(phone_number=req["phone_number"], max_age=req["max_age"]))
        raise ValueError(api)

    # ------------------------------------------------------------------ public
    def call(self, api: str, **kw: Any) -> dict:
        req = self._request(api, **kw)
        t0 = time.perf_counter()
        mode = "live" if self.live else "fixture"
        try:
            resp = self._live(api, req) if self.live else FIXTURES[api](**{**kw, "sink": self.sink})
            error = None
        except Exception as exc:  # noqa: BLE001 - the agent must see failures as evidence, not crash
            resp, error = {}, f"{type(exc).__name__}: {str(exc)[:300]}"
        rec = {
            "seq": len(self.calls) + 1,
            "ts": utcnow(),
            "api": api,
            "camara": config.API_CATALOGUE.get(api, (api, ""))[0],
            "category": config.API_CATALOGUE.get(api, (api, ""))[1],
            "mode": mode,
            "request": req,
            "response": resp,
            "error": error,
            "latency_ms": round((time.perf_counter() - t0) * 1000),
            "cost_cents": config.API_COST_CENTS.get(api, 0.0),
        }
        self.calls.append(rec)
        if self.on_call:
            self.on_call(rec)
        return {"error": error} if error else resp
