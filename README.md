# Saqqa · السقّا

**Network-attested delivery and payment for trucked water.**
GSMA MENA Ignite Hackathon 2026 · Prototype Phase · Theme 6, Climate Resilience & Environmental Monitoring · Team StarX.

A water delivery is paid for on the word of the person being paid. A tanker arrives at a camp, a clinic or a hotel;
someone signs a paper form (UNHCR's F-306, hand-written GPS and a pen signature) saying ten cubic metres were delivered,
and the signature releases the money. Nobody measured the water. Saqqa puts a level-and-turbidity sensor on the payer's
tank, a SIM in the tanker's cab, and asks the operator's network, not the driver, what happened. An AI agent then works
out what should be paid for, and writes down why. Saqqa makes the operator's network the witness, and pays
for the litres it can account for.

> The tank sensor is the meter. The network is the meter-reader nobody can bribe. The agent is the billing engine.

## What the prototype does

* **Seven CAMARA APIs on Nokia Network as Code**, called live from the agent: Geofencing Subscriptions, Location
  Verification, Location Retrieval, Device Reachability Status, Device Roaming Status, Device Swap, SIM Swap (check and
  retrieve-date). Two of the organisers' categories: *Device intelligence* and *Digital identity & anti-fraud*.
* **A LangGraph agent** (`saqqa/agent/graph.py`) with real decisions in it: which checks to buy for a trip, what to ask
  next when the evidence does not fit, when to stop asking, and how to explain the outcome. Money decisions are a
  deterministic gate (`saqqa/agent/gate.py`) so an auditor can re-run them without a model.
* **Twelve seeded trips** (`saqqa/scenarios.py`): the honest delivery, short fill, over-scheduled tank, closed valve,
  ghost trip, substitution with dirty water, sensor offline, sensor tamper, trip inflation, SIM-swapped payee, the trace
  that contradicts the network, and a manipulated feed. All twelve decide as expected (`scripts/run_scenarios.py`).
* **A payer dashboard** (`dashboard/`): the operator's geofences on a map, the tank trace with the operator's dwell
  window drawn over it, the agent's reasoning streamed as it runs, every CAMARA request and response verbatim, the
  decision, the ledger entry and an F-306-compatible export.
* **A CloudEvents webhook receiver** (`POST /webhooks/camara`) for Geofencing / Reachability / Roaming subscriptions.
  Real operator events arrive from the sandbox within seconds of a subscription; the polling fallback (Location
  Verification) stays in the plan and the trace says which was used.

## Run it

```bash
pip install -r requirements.txt
cp .env.example .env            # add NAC_API_KEY (networkascode.nokia.io) and GOOGLE_API_KEY or GROQ_API_KEY
python scripts/run_scenarios.py # every seeded trip, traces printed; exit code 0 when all decide as expected
uvicorn saqqa.server:app --port 8000
# open http://localhost:8000
```

Without any key the prototype still runs end to end: the network tools answer from fixtures that mirror the sandbox's
scripted personas, the planner / investigator / explainer use deterministic stubs, and the dashboard status line says so.
With `NAC_API_KEY` every tool call goes to Nokia's sandbox and the raw exchange is on screen. With `GOOGLE_API_KEY`
(Gemini Flash-Lite, `gemini-3.5-flash-lite` by default, `gemini-3.5-flash` as in-family fallback; Groq Llama 3.3 70B as the
cross-vendor fallback) the planner, investigator and explainer are real.

Deploy anywhere that runs a container: `Dockerfile` and `render.yaml` are included (Render free tier, health check on
`/api/status`). To receive operator webhooks, set `PUBLIC_BASE_URL` to the public HTTPS address of this server (a tunnel in development,
the deployment URL in production); the agent then registers `PUBLIC_BASE_URL/webhooks/camara` as the sink.


## Deployable today: three APIs, sharper on seven

Almost no operator has all seven of these APIs live, so the agent declares a **deployment profile** and must reach a
defensible verdict inside it. Switch it on the dashboard next to *Run verification*.

| Profile | APIs | Dwell |
|---|---|---|
| `core` | **3** — Location Verification, Device Reachability, SIM Swap | polled every 15 min, carried with its uncertainty |
| `full` | **7** — adds Geofencing Subscriptions, Location Retrieval, Device Roaming Status, Device Swap | stamped by operator geofence events |

`core` reproduces the `full` verdict on **all twelve trips** (`python scripts/compare_profiles.py`), and every `core`
verdict names the checks it could not run. `core` is the smallest set Saqqa can work on, not "what operators already
sell": of the seven, only **SIM Swap** (8 operator rows, Asiacell Iraq certified) and **Device Roaming Status** are
commercially live with a MENA operator today (GSMA Open Gateway map, dataset 12 Sep 2026, in the team repository
under `shared/evidence/`). SIM Swap is the one that stops money. Location Verification is the one that has to land.

## What it takes to deploy

- **On the truck: nothing.** The SIM already in the cab is the tracker; no hardware to buy, fit or maintain.
- **On the tank: one sensor.** A fixed level sensor with its own SIM on the buyer's site, bought once, covering every contractor who delivers there.
- **In software: one agent, three APIs.** Runs on Nokia Network as Code today; every verdict is reached on the core profile. A pilot is one buyer, one hauler and one operator API key.
- **In paperwork: nothing changes.** The F-306 delivery form stays the legal record; Saqqa fills it from the evidence.
- **In money: 13.6 cents a trip**, measured, against a $30 delivery.

Four students built the working version in three weeks on the public sandbox. A pilot is a procurement decision, not an engineering programme.

## Money

The buyer pays per verified delivery with a per-truck monthly floor; the operator is paid per call. Measured, not
estimated: **10.4 CAMARA calls and 13.6 cents per trip** live (8.2 calls, 7.6 cents on `core`), against a Jordanian
truckload worth about **$30** — 0.45% of trip value. Stopping 2% of overbilling returns **4.5x** the verification spend;
Jordan alone is 48–61 million calls a year, about **$1.2M/yr** to the operator at 2 cents a call. Every figure and its
source is in `docs/BUSINESS_MODEL.md`.

Roadmap, one line: any trucked commodity paid on a delivery note. Water is the wedge because the paper form is public.

## How a trip is verified

```
dispatch says: T-14, 10 m³, well S1 → Tank 7, 08:40
        │
        ▼
intake ─► plan ─► verify ─► sense ─► score ─┬─► investigate ─► verify (≤3 rounds)
                                             └─► decide ─► explain ─► act
```

| Step | What happens | Who decides |
|---|---|---|
| plan | Mandatory checks (four geofence subscriptions on the cab SIM, presence polling, sensor reachability / location / device-swap, payee SIM-swap) plus optional ones the planner buys given site type, contractor history and cost per call | LLM, constrained to the tool set |
| verify | Each check is one CAMARA call through `NaCClient`; request, response, latency, mode recorded | code |
| sense | The tank trace for the window: level before/after, the minutes it rose, turbidity, step artefacts | code |
| score | Signals and **contradictions**: tank rose but no truck in the zone; rose before the truck arrived; dwell too short for the litres; turbidity during the fill; litres exceed the truck; claim vs measurement | code |
| investigate | Given the contradictions, choose the next network question, or stop. Prefers checks that could exonerate an honest contractor | LLM, constrained |
| decide | RELEASE / HOLD / ESCALATE / BLOCK with the litres to pay | deterministic gate |
| explain | Two-sentence audit note, English and Arabic | LLM with template fallback |
| act | Payment webhook (stub), ledger row, F-306-compatible export, supervisor case, contractor notice. Never a household | code |

The run to watch is **"The agent doubts its own sensor"**: the tank rises 9.8 m³ between 09:05 and 09:27, the operator's
timestamps put the truck in the zone from 09:35. The agent re-queries the sensor's reachability and asks the network
where the truck was, then refuses to credit the delivery: *measurement not believed*. Order of evidence is the network
first, our sensor second, always.

## Sandbox honesty

* Nokia's sandbox routes `+9999…` numbers to simulators with scripted outcomes, verified from our account with
  `scripts/probe_live.py` (2 Sep 2026, 28 calls, 0 errors): `…1001` is the clean subscriber (Location Verification TRUE,
  not swapped, not roaming, reachable on DATA); `…1000` is compromised (FALSE, swapped, roaming in HU, SMS only);
  `…1002` returns UNKNOWN; `…1003` returns PARTIAL and is unreachable. The scenarios use those personas, so the same
  trip behaves identically in fixture and live mode, and the probe prints the table again from any account.
* Simulator devices have one fixed position (Location Retrieval returns the same 1 km circle for every number), so the truck's timeline (when it entered and left each zone) is ours; the
  calls that attest to it are real. **Webhook delivery is verified**: every Geofencing subscription the agent creates
  (with `initial_event=true`) produces a CloudEvent at our sink within seconds, with the subscription id in `data`; the
  sandbox fires the subscribed event type on creation for every persona, so it proves the plumbing, not the movement.
  The agent lists the events it received against its own subscription ids and keeps the polling fallback regardless.
* The tank trace is a pump model (`saqqa/sensor/simulator.py`) with its parameters on screen. Hardware is Phase 3.
* No person is located, messaged or asked to consent. Every SIM here belongs to an organisation: the payer issues the
  cab SIM and the sensor SIM as a condition of the contract. The payee check (SIM Swap) is on the contractor's
  business number, agreed at onboarding.

## Repository

```
saqqa/
  config.py           sites (2 km zones), tanks, cost per call, run mode
  nac/client.py       the seven CAMARA APIs through the Nokia SDK; live or fixture; every exchange recorded
  config.py           PROFILES (core / full) and LIVE_IN_MENA, with the GSMA citation
  nac/fixtures.py     sandbox-mirroring fixtures
  sensor/simulator.py tank level / turbidity model
  agent/graph.py      the LangGraph agent
  agent/gate.py       signals, contradictions, the deterministic payment gate
  agent/llm.py        Gemini Flash-Lite → Gemini Flash → Groq → stub
  store/db.py         SQLite: runs, api_calls, events, ledger (flat schema; moves to Supabase unchanged)
  scenarios.py        the twelve seeded trips
  server.py           FastAPI: REST, SSE stream, webhook receiver, dashboard
dashboard/            the payer dashboard (Leaflet map, tank chart, live trace, calls, ledger)
scripts/              run_scenarios.py · probe_live.py
docs/                 ARCHITECTURE.md · API_USAGE.md · BUSINESS_IMPACT.md · DEMO_SCRIPT.md
```

Tools used for the agent layer, all from the hackathon's Resource & Tooling Guide: LangGraph, Gemini Flash, Groq,
Nokia NaC Python SDK. FastAPI serves the API; Leaflet draws the map.

## Team StarX

James Joshua Koshy · Kirti Roshankumar Thakar · Divyam Thakur · Evan Johan Tobias
Indian Institute of Technology Delhi, Abu Dhabi.

MIT licence.
