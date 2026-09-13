"""Persistence: SQLite by default, so the prototype runs with one command.

Tables: runs (one per trip verification, full state as JSON), api_calls (every CAMARA exchange), events (raw
webhooks from the operator), ledger (what was paid and why). The Round-1 plan named Supabase Postgres; the schema
is deliberately flat so it moves there unchanged (see docs/ARCHITECTURE.md).
"""
from __future__ import annotations

import json
import sqlite3
import threading
from typing import Any

from .. import config

_lock = threading.Lock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
  id TEXT PRIMARY KEY, scenario_id TEXT, title TEXT, started TEXT, finished TEXT,
  decision TEXT, reason TEXT, pay_m3 REAL, amount_iqd INTEGER, mode TEXT, llm TEXT, expect TEXT, state_json TEXT
);
CREATE TABLE IF NOT EXISTS api_calls (
  run_id TEXT, seq INTEGER, ts TEXT, api TEXT, camara TEXT, category TEXT, mode TEXT,
  request_json TEXT, response_json TEXT, error TEXT, latency_ms INTEGER, cost_cents REAL
);
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, type TEXT, device TEXT, raw_json TEXT
);
CREATE TABLE IF NOT EXISTS ledger (
  run_id TEXT PRIMARY KEY, ts TEXT, trip_id TEXT, contractor TEXT, tank_id TEXT, truck_id TEXT,
  claimed_m3 REAL, verified_m3 REAL, paid_m3 REAL, amount_iqd INTEGER, status TEXT, evidence_refs TEXT
);
"""


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(config.DB_PATH, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c


def init() -> None:
    with _lock, _conn() as c:
        c.executescript(SCHEMA)


def _jsonable(o: Any) -> Any:
    try:
        json.dumps(o)
        return o
    except TypeError:
        return json.loads(json.dumps(o, default=str))


def save_run(run_id: str, state: dict, started: str, finished: str) -> None:
    st = _jsonable({k: v for k, v in state.items()})
    calls = st.get("calls", [])
    with _lock, _conn() as c:
        c.execute("INSERT OR REPLACE INTO runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                  (run_id, st.get("scenario_id"), st.get("title"), started, finished, st.get("decision"), st.get("reason"),
                   st.get("pay_m3"), st.get("amount_iqd"), "live" if calls and calls[0]["mode"] == "live" else "fixture",
                   st.get("llm_provider"), st.get("expect"), json.dumps(st)))
        c.execute("DELETE FROM api_calls WHERE run_id=?", (run_id,))
        c.executemany("INSERT INTO api_calls VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                      [(run_id, r["seq"], r["ts"], r["api"], r["camara"], r["category"], r["mode"], json.dumps(r["request"]),
                        json.dumps(r["response"]), r["error"], r["latency_ms"], r["cost_cents"]) for r in calls])
        lg = st.get("ledger")
        if lg:
            c.execute("INSERT OR REPLACE INTO ledger VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                      (run_id, lg["ts"], lg["trip_id"], lg["contractor"], lg["tank_id"], lg["truck_id"], lg["claimed_m3"],
                       lg["verified_m3"], lg["paid_m3"], lg["amount_iqd"], lg["status"], json.dumps(lg["evidence_refs"])))


def list_runs(limit: int = 50) -> list[dict]:
    with _lock, _conn() as c:
        rows = c.execute("SELECT id, scenario_id, title, started, finished, decision, reason, pay_m3, amount_iqd, mode, llm, expect "
                         "FROM runs ORDER BY started DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]


def get_run(run_id: str) -> dict | None:
    with _lock, _conn() as c:
        row = c.execute("SELECT state_json FROM runs WHERE id=?", (run_id,)).fetchone()
    return json.loads(row["state_json"]) if row else None


def add_event(ts: str, typ: str, device: str, raw: dict) -> int:
    with _lock, _conn() as c:
        cur = c.execute("INSERT INTO events (ts, type, device, raw_json) VALUES (?,?,?,?)", (ts, typ, device, json.dumps(raw)))
        return int(cur.lastrowid or 0)


def list_events(limit: int = 100) -> list[dict]:
    with _lock, _conn() as c:
        rows = c.execute("SELECT id, ts, type, device, raw_json FROM events ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [{**dict(r), "raw": json.loads(r["raw_json"])} for r in rows]


def ledger(limit: int = 100) -> list[dict]:
    with _lock, _conn() as c:
        rows = c.execute("SELECT * FROM ledger ORDER BY ts DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]


def api_stats() -> dict:
    with _lock, _conn() as c:
        rows = c.execute("SELECT camara, category, mode, COUNT(*) n, AVG(latency_ms) ms, SUM(cost_cents) cents, "
                         "SUM(CASE WHEN error IS NULL THEN 0 ELSE 1 END) errors FROM api_calls GROUP BY camara, category, mode").fetchall()
    return {"by_api": [dict(r) for r in rows]}
