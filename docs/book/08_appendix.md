## Appendix · The evidence, verbatim

One real request and response per API, exactly as logged in the last full live run ({{stats.generated}}, commit {{stats.commit}}). Keys are normalised to snake_case by the client; the SDK returns camelCase. Timestamps in responses are the sandbox's.

### Geofencing Subscriptions ({{calls.geofence_subscribe.latency_ms}} ms, trip "{{calls.geofence_subscribe.scenario}}")

{{calls.geofence_subscribe.request}}

{{calls.geofence_subscribe.response}}

### Location Verification ({{calls.location_verify.latency_ms}} ms, trip "{{calls.location_verify.scenario}}")

{{calls.location_verify.request}}

{{calls.location_verify.response}}

### Device Reachability Status ({{calls.reachability_status.latency_ms}} ms, trip "{{calls.reachability_status.scenario}}")

{{calls.reachability_status.request}}

{{calls.reachability_status.response}}

### Device Swap ({{calls.device_swap_check.latency_ms}} ms, trip "{{calls.device_swap_check.scenario}}")

{{calls.device_swap_check.request}}

{{calls.device_swap_check.response}}

### SIM Swap ({{calls.sim_swap_check.latency_ms}} ms, trip "{{calls.sim_swap_check.scenario}}")

{{calls.sim_swap_check.request}}

{{calls.sim_swap_check.response}}

### Location Retrieval ({{calls.location_retrieve.latency_ms}} ms, trip "{{calls.location_retrieve.scenario}}")

{{calls.location_retrieve.request}}

{{calls.location_retrieve.response}}

The circle is near Budapest for every simulator; see chapter 2.

### Device Roaming Status ({{calls.roaming_status.latency_ms}} ms, trip "{{calls.roaming_status.scenario}}")

{{calls.roaming_status.request}}

{{calls.roaming_status.response}}

### Reproduce it

```
pip install -r requirements.txt
cp .env.example .env                      # NAC_API_KEY, GOOGLE_API_KEY, PUBLIC_BASE_URL
python scripts/probe_live.py              # the persona table, from your own account
python scripts/run_scenarios.py --json    # twelve trips, live; writes runs/*.json
python docs/book/extract_evidence.py      # rebuilds the evidence pack from the logs
python docs/book/build_book.py            # rebuilds this book with the new numbers
uvicorn saqqa.server:app --port 8000      # the dashboard; set PUBLIC_BASE_URL to receive webhooks
```

Every number in this book is substituted from the evidence pack at build time. If the runs change, the book changes.

### Glossary

| Term | Meaning here |
|---|---|
| CAMARA | The open API standard for network capabilities, governed under the Linux Foundation with GSMA Open Gateway; the seven APIs Saqqa uses are CAMARA APIs. |
| Nokia Network as Code (NaC) | Nokia's platform exposing CAMARA APIs, with a sandbox of scripted simulator numbers; the hackathon's mandated platform. |
| Persona | One of the sandbox's simulator numbers (`…1000`, `…1001`, `…1002`, `…1003`), each with fixed answers to every API. |
| CloudEvent | The JSON envelope in which the operator platform delivers a subscription event to our webhook (`type`, `source`, `time`, `data`). |
| Dwell | Minutes between the operator's area-entered and area-left stamps for a zone. |
| Rise window | The minutes in which the tank level rose faster than sensor noise. |
| Gate | The ordered, deterministic rules that turn signals into RELEASE / HOLD / ESCALATE / BLOCK and litres to pay. |
| F-306 | UNHCR's water-trucking log book: the paper form Saqqa replaces in the payment path and exports to for continuity. |
| Unverified | A trip the system cannot attest (usually a sensor offline). It goes back to paper. It is never fraud. |
| Zone | A circle of at least 2,000 m radius, the smallest geofence Nokia's platform accepts. |
