## 4 · The agent

The hackathon's mandatory requirement is an AI agent layer that treats CAMARA APIs as trusted real-time data sources rather than user-triggered actions. This chapter is where the agent actually decides, where it deliberately does not, and how to show the difference in a room.

### The graph

One LangGraph graph per trip (`saqqa/agent/graph.py`):

```
intake → plan → verify → sense → score ─┬─► investigate → verify (loop, at most 3 rounds)
                                        └─► decide → explain → act → END
```

| Node | What happens | Who decides |
|---|---|---|
| intake | Loads the trip as the payer's dispatch sent it; loads the sensor trace for the window; states the order of evidence (network, then sensor, then payee). | code |
| plan | Fixes the mandatory checks and asks the model which optional ones to buy for this trip. | **model**, constrained |
| verify | Executes each check as one CAMARA call through the Nokia SDK. Request, response, latency and mode are recorded. Waits up to 12 s for the operator's webhooks against this run's own subscription ids. | code |
| sense | Summarises the trace: level at 08:30, the minutes it rose, litres, turbidity, step artefacts. | code |
| score | Derives the signals (chapter 3's checks) and lists the contradictions between them. | code |
| investigate | Given the contradictions, asks the model which network question to ask next, or whether to stop. | **model**, constrained |
| decide | Applies the gate (chapter 5). | deterministic |
| explain | Asks the model for a two-sentence audit note in English and Arabic, with the decision and reason given to it verbatim. | **model**, template fallback |
| act | Payment webhook (stub), ledger row, F-306-compatible export, supervisor case or contractor notice. Never a household. | code |

Tools are the CAMARA calls (`saqqa/nac/client.py`) and the sensor store. A failed call comes back as evidence (`{"error": …}`) and the agent reasons about it; nothing raises into the graph.

### Where the model decides

**Planning.** The mandatory set is fixed: four geofence subscriptions on the cab SIM (well in and out, tank in and out), the presence poll, reachability, location and device-swap on the sensor SIM, and SIM Swap on the payee. The optional set is Location Retrieval (where the truck went) and Device Roaming (is the fleet SIM abroad). The model sees the trip (site type, contractor history, claimed volume) and the cost per call, and returns which optional checks to add and one sentence of reasoning. In the last run the planner said, for the honest camp delivery:

> {{runs.honest.planner_note}}

and for the ghost trip:

> {{runs.ghost_trip.planner_note}}

Every network call costs money and no payer runs every check on every load. The plan is where that judgement lives.

**Investigation.** When `score` finds contradictions, the model is shown them, the signals, what has already been called, and a menu: re-ask reachability, re-verify the sensor's location, check device swap, retrieve the truck's location, check roaming, retrieve the SIM-swap date. It picks up to three, or none, and says why. It may ask Location Verification and Reachability twice, before rejecting a sensor, and everything else once. Three rounds at most. This is the run to watch, as the model reasoned it in the last live run:

{{runs.sensor_contradicts_network.investigation_log}}

Note the instruction the investigator carries: prefer checks that could exonerate an honest contractor over checks that only confirm suspicion. That is a design choice, not a courtesy; a system that only ever looked for guilt would be gamed by whoever controlled the accusations.

**Explanation.** The audit note is written for a supervisor who has thirty seconds. The model is given the decision and its reason as written and is told not to invent another. In the last run:

> {{runs.sensor_contradicts_network.audit_note}}

> {{runs.sensor_contradicts_network.audit_note_ar}}

### Where the model does not decide

Money. RELEASE, HOLD, ESCALATE and BLOCK, and the litres to pay, come from the gate in `saqqa/agent/gate.py`: ordered rules over the signals, pure functions of state, re-runnable by an auditor without a model. Two reasons, both worth saying aloud:

1. A payer's finance desk must be able to reproduce every decision from the ledger. "The model thought so" is not an audit trail.
2. A model can be talked into things. A contractor who learned that the audit note influenced payment would start writing for the model. The note describes the decision; it never makes it.

This is also the answer to the judge's Round-1 objection that "the LLM is a narrator, not a decision-maker". It is both, in the places where each is right: it decides what to ask, it never decides what to pay.

### The model, and what happens when it fails

Gemini 3.5 Flash-Lite is primary (about 1.5 s per call on these small JSON prompts), Gemini 3.5 Flash is the in-family fallback (about 8 s), Groq Llama 3.3 70B the cross-vendor fallback, and a deterministic stub last. Gemini 2.5 Flash, which the Round-1 plan named, is no longer offered to new accounts. All three are on the hackathon's Resource and Tooling Guide, as is LangGraph.

The chain is per call. Early on, one Gemini timeout demoted the shared model to the stub for every later run, silently; the dashboard's "audit note by template" label is what caught it. Now a failed call falls down the chain for that call only, the primary is tried again on the next call, and every run records which provider wrote each note. In the last full run every audit note was written by a Gemini model; the runs show which.

Prompts are JSON-constrained and short. The model's reasoning tokens are turned down (they added latency and nothing else on prompts this size). Responses are parsed tolerantly (fenced or bare JSON, list-shaped content), because the first live run failed on exactly that and looked like a model failure when it was a parsing one.

### A second design, on Evan's branch

Evan's own prototype (`phase2/prototype`, pushed 3 September) answers the same question with a different mechanism: the agent holds eight competing explanations of a trip as beliefs, knows roughly how each paid question would move them, and buys evidence while the money it expects to protect beats what the answer costs, about five credits' worth on an average trip against eight for a checklist. It has 31 tests and a written fallback policy that gets twelve of twelve without a model. It ran against synthetic answers because no key was on that machine; the mechanism is sound and the arithmetic is real. The canonical build (this book's) uses a constrained model for the planning and investigation choices and ran live. The two are complementary, not rivals: the value-of-information framing is the better answer to "is the AI doing anything", and folding its cost-benefit accounting into the live planner is the first merge on the list.

### What to show in the room

If there is one screen to show, it is the trace of "the agent doubts its own sensor": the contradiction found by code, the two questions chosen by the model with its reasons, the decision made by the gate, the note written by the model. The sequence is the argument: judgement where judgement helps, rules where money moves.
