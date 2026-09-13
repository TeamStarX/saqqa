"""Extract the field manual's evidence from the run logs and the events table.

    python scripts/run_scenarios.py --json      # refresh runs/*.json (live when NAC_API_KEY is set)
    python docs/book/extract_evidence.py        # -> docs/book_evidence.json, docs/book_evidence_event.json

The book substitutes {{stats.*}}, {{calls.<api>.*}}, {{runs.<id>.*}} and {{event.*}} from these files at build time,
so a number in the book is always a number from a logged run.
"""
from __future__ import annotations

import datetime as dt
import glob
import json
import os
import sqlite3
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)

SIGNAL_KEYS = ("claimed_m3", "delta_m3", "fill_ratio", "tank_room_m3", "dwell_min", "rise_window", "dwell_window",
               "rise_dwell_overlap_min", "min_minutes_to_pump_delta", "turbidity_ntu", "max_step_cm", "sensor_online",
               "sensor_in_place", "sensor_swapped", "payee_swapped", "capacity_ok", "truck_location_verify",
               "truck_roaming", "truck_roaming_country", "source_visited", "truck_entered_tank_zone")


def main() -> None:
    seen: dict[str, dict] = {}
    rows: list[dict] = []
    lat: list[int] = []
    per_api: dict[str, list[int]] = {}
    tot = live = errs = 0
    for f in sorted(glob.glob("runs/*.json")):
        d = json.load(open(f, encoding="utf-8"))
        for c in d.get("calls", []):
            tot += 1
            live += c["mode"] == "live"
            errs += bool(c["error"])
            lat.append(c["latency_ms"])
            per_api.setdefault(c["api"], []).append(c["latency_ms"])
            if c["api"] not in seen and c["mode"] == "live" and not c["error"]:
                seen[c["api"]] = {"scenario": d["scenario_id"], "request": c["request"], "response": c["response"],
                                  "latency_ms": c["latency_ms"], "ts": c["ts"], "camara": c["camara"], "category": c["category"]}
        rows.append({
            "id": d["scenario_id"], "title": d["title"], "expect": d.get("expect"), "decision": d["decision"], "reason": d["reason"],
            "pay_m3": d["pay_m3"], "amount_iqd": d["amount_iqd"], "calls": len(d["calls"]), "investigations": d["investigations"],
            "llm": d.get("llm_provider"), "planner_note": d.get("planner_note"), "investigation_log": d.get("investigation_log"),
            "audit_note": d.get("audit_note"), "audit_note_ar": d.get("audit_note_ar"), "audit_note_source": d.get("audit_note_source"),
            "contradictions": d.get("contradictions"), "trip": d["trip"], "network": d["network"],
            "signals": {k: d["signals"].get(k) for k in SIGNAL_KEYS},
            "steps": [{"node": s["node"], "text": s["text"]} for s in d["steps"]],
        })
    stats = {
        "runs": len(rows), "runs_as_expected": sum(1 for r in rows if r["decision"] == r["expect"]),
        "calls_total": tot, "calls_live": live, "errors": errs,
        "latency_min": min(lat), "latency_median": int(statistics.median(lat)), "latency_mean": int(statistics.mean(lat)), "latency_max": max(lat),
        "per_api_median": {k: int(statistics.median(v)) for k, v in per_api.items()},
        "per_api_count": {k: len(v) for k, v in per_api.items()},
        "generated": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "commit": os.popen("git rev-parse --short HEAD").read().strip(),
    }
    # events table: real CloudEvents the operator platform posted to our sink
    event_sample = None
    if os.path.exists("saqqa.sqlite3"):
        c = sqlite3.connect("saqqa.sqlite3")
        c.row_factory = sqlite3.Row
        by_type = {r[0].split(".")[-1]: r[1] for r in c.execute("SELECT type, COUNT(*) FROM events WHERE device LIKE '+9999999%' GROUP BY type")}
        stats["events_total"] = sum(by_type.values())
        stats["events_entered"] = by_type.get("area-entered", 0)
        stats["events_left"] = by_type.get("area-left", 0)
        stats["events_ends"] = by_type.get("subscription-ends", 0)
        stats["events_first"] = c.execute("SELECT MIN(ts) FROM events WHERE device LIKE '+9999999%'").fetchone()[0]
        stats["events_last"] = c.execute("SELECT MAX(ts) FROM events WHERE device LIKE '+9999999%'").fetchone()[0]
        ev = c.execute("SELECT raw_json FROM events WHERE type LIKE '%area-entered' AND device='+99999991001' ORDER BY id DESC LIMIT 1").fetchone()
        if ev:
            event_sample = json.loads(ev["raw_json"])
    json.dump({"stats": stats, "calls": seen, "runs": rows}, open("docs/book_evidence.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    if event_sample:
        json.dump(event_sample, open("docs/book_evidence_event.json", "w", encoding="utf-8"), indent=1)
    print(json.dumps({k: v for k, v in stats.items() if not isinstance(v, dict)}, indent=1))
    print("apis with a live sample:", sorted(seen))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
