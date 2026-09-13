# Architecture

```
┌──────────────────────┐      ┌─────────────────────────────────────────────────────────────────┐
│ Payer dispatch / ERP │ ───► │ Saqqa API (FastAPI)                                              │
│ trip: truck, source, │      │  POST /api/run  · GET /api/stream (SSE) · GET /api/runs, /ledger │
│ tank, claimed m³     │ ◄─── │  POST /webhooks/camara  (CloudEvents from the operator)          │
└──────────────────────┘      └───────────────┬──────────────────────────────────┬──────────────┘
        payment webhook, hold, case            │                                  │
                                               ▼                                  ▼
                              ┌────────────────────────────┐        ┌───────────────────────────┐
                              │ LangGraph agent            │        │ Store (SQLite → Supabase) │
                              │ intake→plan→verify→sense→  │ ─────► │ runs · api_calls · events │
                              │ score⇄investigate→decide→  │        │ ledger                    │
                              │ explain→act                │        └───────────────────────────┘
                              └───────┬───────────┬────────┘
                       tools          │           │  tools
                                      ▼           ▼
                  ┌───────────────────────┐   ┌─────────────────────────────┐
                  │ Nokia NaC client      │   │ Tank sensor store           │
                  │ 7 CAMARA APIs, live   │   │ level + turbidity, 1-min    │
                  │ or fixture, recorded  │   │ (simulated in Phase 1)      │
                  └──────────┬────────────┘   └─────────────────────────────┘
                             ▼
                  Nokia Network as Code sandbox  ──►  operator network (cab SIM, sensor SIM, payee number)
```

## Components

| Layer | Implementation | Notes |
|---|---|---|
| Input | `POST /api/run/{scenario}` with the trip as the payer's dispatch would send it | Twelve seeded trips in `scenarios.py`; a real integration posts the same shape |
| Network | `nac/client.py` around `network_as_code` 10.0.0 | One method per CAMARA API; request/response/latency/mode recorded; failures returned as evidence, never raised |
| Events | `POST /webhooks/camara` CloudEvents receiver; `events` table; merged into the run when present | Polling fallback via Location Verification is always planned |
| Sensor | `sensor/simulator.py` pump-discharge model, 1-min samples, deterministic noise | Phase 3 replaces it with an LTE-M level/turbidity probe on the payer's tank; interface is the same trace |
| Agent | `agent/graph.py` LangGraph `StateGraph`; nodes intake, plan, verify, sense, score, investigate, decide, explain, act | Conditional edges score→investigate/decide and investigate→verify/decide; recursion limit 40; max 3 investigation rounds |
| Gate | `agent/gate.py` | Signals, contradictions, and the ordered payment gate; pure functions of state, re-runnable by an auditor |
| LLM | `agent/llm.py` Gemini 3.5 Flash-Lite → Gemini 3.5 Flash → Groq Llama 3.3 70B → deterministic stub | Used for planning, investigation choice and the audit note only; JSON-constrained; provider shown in the UI |
| Store | `store/db.py` SQLite | Flat tables: runs, api_calls, events, ledger; the same DDL runs on Supabase Postgres |
| Output | payment webhook (stub), ledger row, F-306-compatible export (`/api/export/f306/{run}`), supervisor case, contractor notice | No message ever goes to a household |
| Dashboard | `dashboard/` Leaflet map of the operator's 2 km zones, tank chart with the operator's dwell window, streamed reasoning, verbatim calls, decision, ledger | Served by the same process; one command to run |

## Sequence for one trip

1. Dispatch posts the trip. `intake` builds the state and loads the tank trace for the window.
2. `plan` registers four geofence subscriptions on the cab SIM (well in/out, tank in/out) with the server's public
   webhook as sink, schedules the presence poll and the three sensor checks, and the payee SIM-swap check; the planner
   may add Location Retrieval / Roaming.
3. `verify` executes the calls. Geofence events (live or timeline) become the operator's timestamps.
4. `sense` summarises the trace: level at 08:30, the minutes it rose, litres, turbidity, step artefacts.
5. `score` derives signals (dwell, litres, fill ratio, overlap of the rise with the dwell, pump-time plausibility,
   capacity accounting) and lists contradictions.
6. If anything contradicts, `investigate` picks the next question from the menu, `verify` runs it, `score` re-derives.
7. `decide` applies the gate. `explain` writes the audit note. `act` writes the ledger and the export, and calls the
   payer's payment webhook for RELEASE.

## Why the network and not GPS

A payer-issued GPS tracker is precise and belongs to the audited party's vehicle; its trace can be forged, replayed or
"lost". The operator's timestamps are coarse (2 km) and belong to nobody in the transaction. Saqqa uses the coarse,
unforgeable record to decide whether to believe the precise, forgeable one (the sensor trace, our own hardware). That
is the whole design: forgeability, not resolution.

## Production path

* Operator: any CAMARA channel (operator-direct, Aduna, Nokia NaC). Two-legged tokens for organisation-owned M2M SIMs
  are the commercial norm for fraud-prevention use of SIM Swap and Device Status.
* Hosting: the FastAPI service on any container host with a public HTTPS URL for the webhook sink; Supabase for the
  store; the dashboard is static.
* Hardware: LTE-M level + turbidity probe per instrumented tank ($15–30 plus a ~$10 probe), on the payer's site.
