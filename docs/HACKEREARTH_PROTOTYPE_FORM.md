# HackerEarth · Prototype Phase form · paste-ready text

Form fields (dashboard → Prototype Phase → New Submission): Title · Description (rich text) · Parent Submission
(Saqqa, id 85013) · Theme (6) · Snapshots (PNG ≤3 MB each) · Video URL · Presentation (pdf/pptx, required) ·
Demo Link · Repository URL · Source Code zip (required) · Instructions to Run. Save as Draft exists; resubmit until
13 Sep 22:29 Dubai; the last submission counts.

---

## Title

Saqqa: network-attested delivery and payment for trucked water

## Description

# Saqqa — the network is the witness

**A water delivery is paid for on the word of the person being paid.** A tanker arrives, someone signs UNHCR form F-306, and the signature releases the money. Nobody measured the water. Jordan's tanker market alone moves US$176 million a year this way (Klassert et al., Nature Sustainability, 2023). Across Iraq, Jordan, Yemen and the Gulf, trucked water is the utility for millions of people, and it is the only utility with no meter.

**Saqqa pays for the litres it can account for, and makes the mobile operator the witness nobody can bribe.**

## What we built

A working, live prototype. Two organisation SIMs: one in the tanker's cab, one inside a level-and-turbidity sensor on the buyer's own tank. No household is located, messaged or asked to consent.

An AI agent runs every delivery through the operator's network:

- **Plans** which network checks to buy for this trip, from site type, contractor history and cost per call.
- **Verifies** the trip through the operator's network on Nokia Network as Code, every answer on screen.
- **Senses** the tank: litres from the level rise, fill time, turbidity.
- **Scores** evidence against evidence: did the tank rise while the operator says the truck was there?
- **Investigates** when the facts disagree, choosing the next network question itself, up to three rounds.
- **Decides** RELEASE, HOLD, ESCALATE or BLOCK, with the litres to pay and a bilingual audit note, through a deterministic gate the model never touches.
- **Acts**: payment webhook, ledger, F-306-compatible export, supervisor case.

**Twelve delivery scenarios, from the honest trip to the ghost trip to the hijacked payee. Twelve correct verdicts.**

## The run that wins the argument

Tank 7 rises 9.7 m³ between 09:05 and 09:27. The operator's timestamps put the truck in the zone from 09:35. The agent does not trust its own sensor. It re-asks whether the sensor can be believed, asks the network where the truck actually was, and refuses to credit the delivery. **Our sensor loses to the operator's timestamps, because the sensor is ours and the timestamps are nobody's.**

## Why the network, not a GPS tracker

A tracker reports its own position. The operator observes yours. Disable a tracker and the trip is simply unlogged, and invoiced anyway. Disable Saqqa's cab SIM and the gate cannot release payment. **Saqqa is fail-secure. Tampering costs the contractor money instead of hiding fraud.**

## Seven APIs, one agent, two categories

| API | Whose SIM | What it proves |
|---|---|---|
| Geofencing Subscriptions | cab | operator-stamped entry, exit and dwell at the well and the tank, delivered as CloudEvents to our webhook |
| Location Verification | cab + sensor | presence at the tank; the sensor is still where we installed it |
| Device Reachability Status | sensor | whether the sensor can be believed at all |
| Device Swap | sensor | the SIM is still inside the sensor, not in a handset |
| SIM Swap | payee | no payment to a number hijacked since the contract was signed |
| Location Retrieval | cab | where the truck went when the tank rose without it |
| Device Roaming Status | cab | a fleet SIM that left the country |

Device intelligence and Digital identity & anti-fraud, orchestrated by one LangGraph graph whose tools are the CAMARA calls.

## Deployable today, sharper tomorrow

The agent declares a **deployment profile** and must reach a defensible verdict inside it. On the **core profile**, three APIs (Location Verification, Device Reachability, SIM Swap), it reproduces the full verdict on all twelve trips and names what it could not check. SIM Swap, the API that stops money, is the most deployed CAMARA API in MENA today (GSMA Open Gateway map, 12 Sep 2026). Switch profiles live on the dashboard. The other four make every answer sharper.

Every SIM belongs to an organisation, so consent is a fleet-telematics contract signed once at onboarding, not a consumer location lookup.

## Business model

Somebody already pays for every trucked delivery against a piece of paper. Saqqa attaches verification to a payment that already exists.

- **Buyer** pays per verified delivery with a per-truck monthly floor. Verification costs **about 14 cents on a $30 truckload, under half a percent**. Stopping 2% of overbilling returns **4.5x** the verification spend.
- **Operator** is paid per call. Jordan alone is **48 to 61 million calls a year, about $1.2M/yr at 2 cents a call**, on organisation SIMs with the two-legged consent model operators already sell to banks.
- **Honest haulers** are paid same day and hold a record the operator stands behind. An unverified trip falls back to the paper process, never to a penalty.

Route to market: Iraq (Asiacell, CAMARA-certified), Jordan, the Gulf. Every figure sourced or derived in docs/BUSINESS_MODEL.md.

**Roadmap in one line: any trucked commodity paid on a delivery note.** Water is the wedge because the paper form is public.

## Stack

LangGraph · Gemini 3.5 Flash-Lite (Groq Llama 3.3 70B fallback) · Nokia NaC Python SDK 10.0.0 · FastAPI · SQLite, flat schema ready for Supabase. Agent layer built only from the Resource & Tooling Guide. Network calls run against Nokia's sandbox; the tank sensor is a pump-discharge model with its parameters on screen in this phase, hardware in the next.

## What it takes to deploy

Nothing on the truck: the SIM already in the cab is the tracker, so there is no hardware to buy, fit or maintain at procurement. One fixed level sensor with its own SIM on the buyer's tank, bought once, covers every contractor who delivers there. One agent and three CAMARA APIs, running on Nokia Network as Code today, reach every verdict; a pilot needs one buyer, one hauler and one operator API key. The F-306 delivery form stays the legal record; Saqqa fills it from the evidence. Verification costs 13.6 cents of network calls against a $30 trip. Four students built the working version in three weeks on the public sandbox: a pilot is a procurement decision, not an engineering programme.

## Team StarX

James Joshua Koshy (network integration, agent) · Evan Johan Tobias (agent, backend) · Divyam Thakur (research, sourcing) · Kirti Roshankumar Thakar (design, pitch). Indian Institute of Technology Delhi, Abu Dhabi.

## Instructions to Run

1. `pip install -r requirements.txt` (Python 3.11+).
2. `cp .env.example .env` and add `NAC_API_KEY` from networkascode.nokia.io (Console → application → API key). Optional:
   `GOOGLE_API_KEY` for the real planner/investigator/explainer (Gemini), `PUBLIC_BASE_URL` (a public HTTPS address of
   this server) to receive operator webhooks. Without keys the prototype runs on sandbox-mirroring fixtures and says so.
3. `python scripts/run_scenarios.py` runs all twelve trips in the terminal (exit code 0 when all decide as expected).
4. `uvicorn saqqa.server:app --port 8000` and open http://localhost:8000. Pick a trip, click Run verification.
5. On the dashboard, switch **core · 3 APIs** / **full · 7 APIs** next to Run verification to see the same trip decided on the widely deployed API set. `python scripts/compare_profiles.py` prints the twelve-trip comparison.
6. `python scripts/probe_live.py` prints what the sandbox returns for every persona on your account.

## Snapshots (upload)

docs/screenshots/landing.png · sensor_contradicts_network.png · honest.png · payee_swapped.png · ghost_trip.png · sensor_offline.png · deck/assets/profile_core.png

## Links

Video URL: (≤3 min, script in docs/DEMO_SCRIPT.md) · Demo Link: (deployment URL) · Repository URL: (public repo)
