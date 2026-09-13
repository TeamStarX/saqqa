# Business impact and commercial value

## Who pays today, for what

Somebody already pays for every trucked delivery against a piece of paper. That is what makes Saqqa a business rather
than a demo: the spend exists, the verification does not.

* **Jordan's tanker market turns over about US$176 million a year**, more than every public water supplier combined,
  and about 91 percent of what it sells comes from illegal sources (Klassert et al., *Nature Sustainability* 6:1406,
  2023). Three quarters of sales serve businesses who buy by the cubic metre.
* **Humanitarian water trucking** is paid on UNHCR form F-306: hand-written GPS, a pen signature, "used as part of the
  payment justification process to the contractor" in the agency's own words. Aid agencies funded at a fraction of need
  must show donors where every dollar went.
* A delivery costs **$30 to $70** today and is paid against a signature. Four frauds survive because the only record is
  created by the party being paid: short-filling, diversion, ghost trips, and a bought signature.

## What Saqqa changes, per delivery

| | Today | With Saqqa |
|---|---|---|
| Evidence of volume | driver's number on a form | litres measured at the tank, corroborated by the operator's timestamps |
| Evidence of presence | hand-written GPS | operator-attested entry, exit and dwell in a 2 km zone; unforgeable by either party |
| Payment trigger | a signature | a deterministic gate over network + sensor evidence, with the reasoning stored |
| Honest hauler | weekly paper cycle, no proof when a tank is short | same-day settlement and a record the operator stands behind |
| Unverified trip | paid anyway | falls back to the existing paper process; never a penalty |
| Audit | re-read forms | F-306-compatible export with every CAMARA call cited |

## Revenue lines

1. **Per verified delivery**: cents against a $30–70 trip, priced with value delivered rather than seats. Ten CAMARA
   calls per trip cost the payer about 12–15 cents in the prototype's cost table.
2. **Platform fee per instrumented tank**: flat monthly, on the payer's own site; one sensor covers every contractor
   delivering to that tank.
3. **Operator revenue share**: the operator bills the CAMARA calls and keeps a share, which is what makes Saqqa worth
   onboarding rather than merely tolerating. Every trip is about ten monetisable API calls (10.4 measured) on organisation SIMs
   with a two-legged consent model the operator already sells to banks.

## Scalability

* Zero personal data: organisation SIMs only, no household phone, no app, no consent flow. This is what lets it run in
  a camp, a hotel and a municipality with the same code.
* The agent is stateless per trip; the store is a flat schema; the dashboard is static. One container per payer or one
  multi-tenant deployment, either way.
* The same engine verifies fuel, LPG, food aid and cold-chain medicine deliveries: anything paid per unit that a sensor
  at the receiving end can measure and a fleet SIM can be attested against.

## Route to market

Iraq first (Asiacell is CAMARA-certified since October 2025 on SIM Swap; Ooredoo group rolling out), then Jordan
(Orange), then the Gulf, where labour accommodation, farms and construction run on tankers. Lebanon, Syria and Yemen as
operators join, and Saqqa gives them a reason to.

## What we do not claim

Attribution is at zone scale, never a single house; inside one zone we rely on assigned routes and capacity accounting.
The best attack found against us is substituting dirty water inside the zone; the answer is a $10 turbidity probe,
which F-306 already logs by hand. An illegal well within 2 km of the licensed one is not caught. A sensor offline makes
a trip unverified, never a penalty. Prior art: CHECKPOINT (GSMA Open Gateway Hackathon, MWC 2025) verifies handover at
the door; Saqqa decides what is paid for.
