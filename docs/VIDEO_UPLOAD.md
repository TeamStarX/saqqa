# Video upload: title, description, checklist

For the HackerEarth Prototype form's Video URL field. Upload as an **unlisted** YouTube video
from James's account. The file is `docs/video/saqqa_demo.mp4`; the re-cut primary is producing
replaces it in place, so upload whichever copy is there after the final commit.

## Title

Paste exactly:

```
Saqqa: network-attested delivery and payment for trucked water (GSMA MENA Ignite, Team StarX)
```

## Description

Paste exactly. The repository link is the public TeamStarX repo (already live); leave
the deployment URL out of the description (it stays in the form's Demo Link field only).

```
Saqqa: network-attested delivery and payment for trucked water.
GSMA MENA Ignite Hackathon 2026, Prototype Phase. Theme 6, Climate Resilience & Environmental Monitoring. Team StarX.

A trucked water delivery is paid for on the word of the person being paid: a signed paper form (UNHCR F-306), a hand-written GPS point, and nobody who measured the water. Saqqa puts a level sensor on the payer's tank and a SIM in the tanker's cab, then asks the mobile operator's network, not the driver, what happened. An AI agent decides which network checks are worth buying for each trip, investigates when the evidence conflicts, and explains the outcome in English and Arabic. Money is released by a deterministic gate the agent cannot override.

What the video shows
- An honest delivery released the same day with the operator's timestamps and the tank's litres attached
- A ghost trip, a short fill and a swapped payee caught by the network, not by paperwork
- The hero run: the tank rises before the operator places the truck at the site, and the agent refuses to trust its own sensor
- The same verdict on three CAMARA APIs as on seven, switched live on the dashboard

CAMARA / Open Gateway APIs, called live on Nokia Network as Code: Geofencing Subscriptions, Location Verification, Location Retrieval, Device Reachability Status, Device Roaming Status, Device Swap, SIM Swap. 125 live calls, 0 errors, median 291 ms in the last full run.

Every SIM in Saqqa belongs to an organisation. No household or personal handset is located, messaged or asked for consent.

Numbers: a Jordanian truckload is worth about $30; verification costs 13.6 cents, 0.45% of the trip; stopping 2% of overbilling returns 4.5x the spend; the operator earns about $1.2M a year from Jordan alone at 2 cents a call. Market: US$176M/yr (Klassert et al., Nature Sustainability, 2023).

The tank sensor is the meter. The network is the meter-reader nobody can bribe. The agent is the billing engine.

Repository: https://github.com/TeamStarX/saqqa
Team StarX
```

Suggested tags: `CAMARA`, `Open Gateway`, `GSMA`, `MENA Ignite`, `Nokia Network as Code`, `agentic AI`,
`water trucking`, `Jordan`.

## Checklist for James

1. Upload the final `saqqa_demo.mp4`, set visibility to **Unlisted**, paste the title and description above, and set "not made for kids".
2. Open the link in a private window and confirm it plays start to finish with sound and no copyright claim on the audio.
3. Paste the URL into the Video URL field of the HackerEarth Prototype form and into `docs/SUBMISSION_PACK.md` under "Video URL".
