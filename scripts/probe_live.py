"""Probe the Nokia NaC sandbox with the exact calls the agent makes, and print what each persona returns.

    set NAC_API_KEY=...            (PowerShell: $env:NAC_API_KEY="...")
    python scripts/probe_live.py                 # all eight APIs x four personas
    python scripts/probe_live.py --webhook URL   # also create one geofence subscription with a real sink and wait 60 s

Purpose: (1) prove every API the agent uses works on our account; (2) capture the real per-suffix outcomes so
saqqa/nac/fixtures.py mirrors the sandbox exactly; (3) find out whether the sandbox delivers webhook events at all,
which decides whether the demo shows real events or the polling fallback (README, "Sandbox honesty").
"""
from __future__ import annotations

import json
import os
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from saqqa import config  # noqa: E402
from saqqa.nac.client import EVENT_ENTERED, NaCClient  # noqa: E402

PERSONAS = ["+99999991000", "+99999991001", "+99999991002", "+99999991003"]
CALLS = [
    ("location_verify", {"zone_id": "K1"}),
    ("location_retrieve", {"max_age": 120}),
    ("reachability_status", {}),
    ("roaming_status", {}),
    ("sim_swap_check", {"max_age": 72}),
    ("sim_swap_date", {}),
    ("device_swap_check", {"max_age": 720}),
]


def main(argv: list[str]) -> int:
    if not config.NAC_API_KEY:
        print("NAC_API_KEY is not set; nothing to probe. See .env.example.")
        return 2
    sink = None
    if "--webhook" in argv:
        sink = argv[argv.index("--webhook") + 1]
    c = NaCClient(live=True, sink=sink or config.WEBHOOK_SINK)
    table: dict[str, dict[str, str]] = {}
    for api, kw in CALLS:
        table[api] = {}
        for n in PERSONAS:
            r = c.call(api, phone_number=n, **kw)
            table[api][n[-4:]] = json.dumps({k: v for k, v in r.items() if k not in ("last_location_time", "last_status_time")})
            time.sleep(0.2)
    print(f"\nsandbox outcomes by suffix (account {config.NAC_API_KEY[:6]}…):\n")
    for api, row in table.items():
        print(f"{api:<22}")
        for sfx, v in row.items():
            print(f"    …{sfx}: {v}")
    print(f"\n{len(c.calls)} calls · mean latency {sum(x['latency_ms'] for x in c.calls) / len(c.calls):.0f} ms · "
          f"errors {sum(1 for x in c.calls if x['error'])}")
    for x in c.calls:
        if x["error"]:
            print("  ERROR", x["api"], x["request"], x["error"])
    if sink:
        print(f"\ncreating one geofence subscription for …1001 on K1 with sink {sink} (initial_event=True) …")
        r = c.call("geofence_subscribe", phone_number="+99999991001", zone_id="K1", event_type=EVENT_ENTERED, initial_event=True, max_events=2)
        print(json.dumps(r, indent=1, default=str))
        print("waiting 60 s for the operator to POST to the sink; check the server log / GET /api/live-events")
        time.sleep(60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
