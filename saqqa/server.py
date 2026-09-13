"""Saqqa API + dashboard + operator webhook receiver.

    uvicorn saqqa.server:app --reload --port 8000

  GET  /                      dashboard
  GET  /api/status            mode (live / fixture), LLM provider, webhook sink, counters
  GET  /api/scenarios         the seeded trips
  POST /api/run/{scenario}    start a verification run; returns {run_id}
  GET  /api/stream/{run_id}   Server-Sent Events: steps and CAMARA calls as they happen, then "done"
  GET  /api/runs, /api/runs/{run_id}, /api/ledger, /api/events, /api/stats
  GET  /api/export/f306/{run_id}
  POST /webhooks/camara       CloudEvents from Nokia NaC subscriptions (geofencing / reachability / roaming)
"""
from __future__ import annotations

import asyncio
import json
import queue
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from . import config, scenarios
from .agent.graph import SaqqaAgent
from .agent.llm import LLM
from .nac.client import NaCClient, utcnow
from .store import db

ROOT = Path(__file__).resolve().parent.parent
DASH = ROOT / "dashboard"

app = FastAPI(title="Saqqa", version="0.2.0")
db.init()

_llm = LLM()
_runs: dict[str, dict] = {}          # run_id -> {"queue": Queue, "state": dict|None, "started": str}
_live_events: list[dict] = []        # webhook events received in this process


def _run_thread(run_id: str, scenario: dict, profile: str | None = None) -> None:
    q: queue.Queue = _runs[run_id]["queue"]
    started = _runs[run_id]["started"]

    def on_step(rec: dict) -> None:
        q.put({"kind": "step", **rec})

    def on_call(rec: dict) -> None:
        q.put({"kind": "call", **rec})

    try:
        agent = SaqqaAgent(nac=NaCClient(on_call=on_call), llm=_llm, on_step=on_step, live_events=_live_events,
                           profile=profile)
        state = agent.run(scenario)
        state = json.loads(json.dumps(state, default=str))
        _runs[run_id]["state"] = state
        db.save_run(run_id, state, started, utcnow())
        q.put({"kind": "done", "run_id": run_id, "decision": state.get("decision"), "reason": state.get("reason"),
               "pay_m3": state.get("pay_m3"), "amount_iqd": state.get("amount_iqd")})
    except Exception as exc:  # noqa: BLE001
        q.put({"kind": "error", "error": f"{type(exc).__name__}: {exc}"})
    finally:
        q.put(None)


@app.get("/api/status")
def status() -> dict:
    return {"mode": "live" if config.LIVE else "fixture", "nac_key_present": bool(config.NAC_API_KEY),
            "llm": _llm.provider, "llm_errors": _llm.errors[-3:], "webhook_sink": config.WEBHOOK_SINK,
            "public_base_url": config.PUBLIC_BASE_URL, "events_received": len(_live_events),
            "runs": len(db.list_runs(1000)), "zones": {k: v.__dict__ for k, v in config.ZONES.items()},
            "tanks": {k: v.__dict__ for k, v in config.TANKS.items()}, "apis": config.API_CATALOGUE,
            "profile": config.PROFILE, "source_sha": config.SOURCE_SHA,
            "live_in_mena": sorted({config.API_CATALOGUE[t][0].split(" (")[0] for t in config.LIVE_IN_MENA}),
            # check and retrieve-date are two operations of one CAMARA API; counting them
            # separately would inflate "7 APIs" to 8 and the claim has to survive a jury.
            "profiles": {k: {"label": v["label"], "blurb": v["blurb"], "apis": sorted(
                {config.API_CATALOGUE[t][0].split(" (")[0] for t in v["tools"] if t in config.API_CATALOGUE})}
                for k, v in config.PROFILES.items()},
            "server_time": utcnow()}


@app.get("/api/scenarios")
def list_scenarios() -> list[dict]:
    return [{k: s[k] for k in ("id", "label", "title", "story", "expect", "tags", "trip", "network", "sensor")} for s in scenarios.SCENARIOS]


@app.post("/api/run/{scenario_id}")
def start_run(scenario_id: str, profile: str | None = None) -> dict:
    """`profile` picks the deployment profile for this run: core (widely deployed APIs) or full."""
    if scenario_id not in scenarios.BY_ID:
        raise HTTPException(404, "unknown scenario")
    if profile and profile.lower() not in config.PROFILES:
        raise HTTPException(400, f"unknown profile; expected one of {sorted(config.PROFILES)}")
    run_id = uuid.uuid4().hex[:12]
    _runs[run_id] = {"queue": queue.Queue(), "state": None, "started": utcnow(), "scenario_id": scenario_id}
    threading.Thread(target=_run_thread, args=(run_id, scenarios.get(scenario_id), profile), daemon=True).start()
    return {"run_id": run_id}


@app.get("/api/stream/{run_id}")
async def stream(run_id: str) -> StreamingResponse:
    if run_id not in _runs:
        raise HTTPException(404, "unknown run")
    q: queue.Queue = _runs[run_id]["queue"]

    async def gen():
        while True:
            try:
                item = q.get_nowait()
            except queue.Empty:
                await asyncio.sleep(0.05)
                continue
            if item is None:
                break
            yield f"data: {json.dumps(item, default=str)}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.get("/api/runs")
def runs() -> list[dict]:
    return db.list_runs()


@app.get("/api/runs/{run_id}")
def run_detail(run_id: str) -> dict:
    st = (_runs.get(run_id) or {}).get("state") or db.get_run(run_id)
    if not st:
        raise HTTPException(404, "unknown run")
    return st


@app.get("/api/ledger")
def ledger() -> list[dict]:
    return db.ledger()


@app.get("/api/events")
def events() -> list[dict]:
    return db.list_events()


@app.get("/api/stats")
def stats() -> dict:
    return db.api_stats()


@app.get("/api/export/f306/{run_id}")
def export_f306(run_id: str) -> JSONResponse:
    st = (_runs.get(run_id) or {}).get("state") or db.get_run(run_id)
    if not st:
        raise HTTPException(404, "unknown run")
    return JSONResponse(st.get("f306", {}), headers={"Content-Disposition": f'attachment; filename="F306_trip_{st["trip"]["trip_id"]}.json"'})


@app.post("/webhooks/camara")
async def camara_webhook(request: Request) -> dict:
    """CloudEvents receiver for Nokia NaC subscriptions. Accepts JSON or a CloudEvents batch."""
    try:
        body: Any = await request.json()
    except Exception:  # noqa: BLE001
        body = {"raw": (await request.body()).decode("utf-8", "ignore")}
    items = body if isinstance(body, list) else [body]
    ids = []
    for ev in items:
        typ = str(ev.get("type", "")) if isinstance(ev, dict) else ""
        device = ""
        if isinstance(ev, dict):
            data = ev.get("data") or {}
            device = str(((data.get("device") or {}).get("phoneNumber")) or ((data.get("device") or {}).get("phone_number")) or "")
        rec = {"received": utcnow(), "type": typ, "device": device, "headers": {k: v for k, v in request.headers.items() if k.lower() in ("ce-type", "ce-source", "ce-id", "content-type")}, "body": ev}
        _live_events.append(rec)
        ids.append(db.add_event(rec["received"], typ, device, rec))
    return {"ok": True, "stored": ids}


@app.get("/api/live-events")
def live_events() -> list[dict]:
    return _live_events[-100:]


@app.get("/")
def index() -> FileResponse:
    return FileResponse(DASH / "index.html")


app.mount("/static", StaticFiles(directory=str(DASH)), name="static")
