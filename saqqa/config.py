"""Saqqa configuration: environment, run mode, sites and cost table.

Everything the agent knows about the world that is not a network call or a sensor reading lives here.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

NAC_API_KEY = os.environ.get("NAC_API_KEY", "").strip()
NAC_HOST = "network-as-code.nokia.rapidapi.com"
# live    -> every tool call goes to the Nokia sandbox (fails loudly if no key)
# fixture -> every tool call answers from fixtures that mirror the sandbox's scripted outcomes
# auto    -> live when a key is present, fixture otherwise
NAC_MODE = os.environ.get("NAC_MODE", "auto").lower()
LIVE = NAC_MODE == "live" or (NAC_MODE == "auto" and bool(NAC_API_KEY))

PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "").rstrip("/")
WEBHOOK_SINK = (PUBLIC_BASE_URL + "/webhooks/camara") if PUBLIC_BASE_URL else "https://example.invalid/webhooks/camara"

LLM_PROVIDER = (
    "gemini" if os.environ.get("GOOGLE_API_KEY") else ("groq" if os.environ.get("GROQ_API_KEY") else "stub")
)
# 2.5 Flash is retired for new accounts. Flash-Lite answers these small JSON prompts in ~1.5 s; Flash takes ~8 s.
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
GEMINI_FALLBACK_MODEL = os.environ.get("GEMINI_FALLBACK_MODEL", "gemini-3.5-flash")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

DB_PATH = os.environ.get("SAQQA_DB", os.path.join(os.path.dirname(os.path.dirname(__file__)), "saqqa.sqlite3"))

PUMP_RATE_L_PER_S = 8.0          # typical tanker discharge; used for "could this dwell have moved that volume"
IQD_PER_M3 = 3200                # contract rate used by the ledger (3.2 IQD per litre)


@dataclass(frozen=True)
class Zone:
    id: str
    name: str
    kind: str            # "source" | "tank" | "other"
    lat: float
    lon: float
    radius_m: int = 2000  # Nokia NaC geofencing minimum


# Al-Zubair district, Basra governorate, Iraq. Coordinates are illustrative site positions.
ZONES: dict[str, Zone] = {
    "S1": Zone("S1", "Licensed well S1 (Al-Zubair filling station)", "source", 30.4620, 47.7530),
    "K1": Zone("K1", "Camp Al-Zubair, Tank 7", "tank", 30.3890, 47.7080),
    "F1": Zone("F1", "Unregistered farm (no contract)", "other", 30.4010, 47.8020),
}


@dataclass(frozen=True)
class Tank:
    id: str
    zone_id: str
    sim: str
    height_cm: int
    litres_per_cm: float
    install_lat: float
    install_lon: float


TANKS: dict[str, Tank] = {
    "K7": Tank("K7", "K1", "+99999991001", 200, 100.0, 30.3890, 47.7080),  # 20 m³ tank, 1 cm = 100 L
}

# Indicative cost per CAMARA call in USD cents, used by the planner to justify which checks to buy.
API_COST_CENTS = {
    "geofence_subscribe": 2.0,
    "location_verify": 1.0,
    "location_retrieve": 1.5,
    "reachability_status": 0.5,
    "roaming_status": 0.5,
    "sim_swap_check": 1.0,
    "sim_swap_date": 1.0,
    "device_swap_check": 1.0,
}

# ---------------------------------------------------------------- source fingerprint
# Every artefact we ship - screenshots, deck images, the demo video - is captured through the
# RUNNING server, which imported this package once at startup. Editing agent code and then
# recording without a restart films the old behaviour while the working tree looks correct.
# That happened on 3 Sep: a planner fix was verified in a fresh process, committed, and the
# next take still showed the bug. The recorder now compares this against the tree and refuses.
def _source_sha() -> str:
    import hashlib, pathlib
    h = hashlib.sha256()
    root = pathlib.Path(__file__).parent
    for f in sorted(root.rglob("*.py")):
        h.update(f.relative_to(root).as_posix().encode())
        h.update(f.read_bytes())
    return h.hexdigest()[:12]


SOURCE_SHA = _source_sha()


# ---------------------------------------------------------------- deployment profiles
# Mentor review, 3 Sep 2026 (Turk Telekom): almost no operator has all seven of these live,
# and location APIs carry the heaviest regulatory load. A design that only works once every
# operator ships everything is a design that never deploys. So the agent declares which APIs
# it is allowed to use, and must still reach a defensible verdict on the smallest set.
#
#   core  - the widely-deployed set: Device Location Verification, Device Reachability
#           Status, SIM Swap. No geofencing, so dwell is polled, not stamped, and the
#           agent says so instead of pretending to a precision it does not have.
#   full  - everything Nokia Network as Code exposes. The roadmap, not the floor.
POLL_MINUTES = 15                # location poll cadence when geofencing is unavailable

PROFILES = {
    "core": {
        "label": "core · deployable today",
        "tools": {"location_verify", "reachability_status", "sim_swap_check", "sim_swap_date"},
        "dwell": "polling",
        "blurb": "3 CAMARA APIs: the smallest set Saqqa can work on. Dwell is polled at "
                 f"{POLL_MINUTES}-minute cadence, so it carries an explicit uncertainty band.",
    },
    "full": {
        "label": "full · Nokia NaC sandbox",
        "tools": {"geofence_subscribe", "location_verify", "location_retrieve", "reachability_status",
                  "roaming_status", "sim_swap_check", "sim_swap_date", "device_swap_check"},
        "dwell": "geofence",
        "blurb": "7 CAMARA APIs across both organiser categories. Dwell comes from operator "
                 "geofence events, so it is stamped by the network rather than inferred.",
    },
}
# Commercial CAMARA deployments in MENA, from GSMA's Open Gateway map (dataset 2026-09-12, fetched
# 13 Sep; TeamStarX/starx shared/evidence/gsma_open_gateway_mena_2026-09-12.md, verified against the
# 640-row JSON beside it). Of the seven APIs Saqqa uses, only two are live with any MENA operator:
#   SIM Swap            8 operator rows (Asiacell Iraq certified)
#   Device Status       2 rows, both apiOperationName "Device roaming status" (e& UAE certified, e& Egypt)
# Geofencing, Location Verification, Location Retrieval, Reachability and Device Swap: none in the region.
# So "core" is the smallest set Saqqa can work on, not "the three operators already sell".
LIVE_IN_MENA = {"sim_swap_check", "roaming_status"}

PROFILE = os.environ.get("SAQQA_PROFILE", "core").lower()   # core first: the version that ships
if PROFILE not in PROFILES:
    PROFILE = "full"


def profile(name: str | None = None) -> dict:
    return PROFILES.get((name or PROFILE).lower(), PROFILES["full"])


# The seven CAMARA APIs Saqqa uses, in the categories the organisers print.
API_CATALOGUE = {
    "geofence_subscribe": ("Geofencing Subscriptions", "Device intelligence"),
    "location_retrieve": ("Location Retrieval", "Device intelligence"),
    "reachability_status": ("Device Reachability Status", "Device intelligence"),
    "roaming_status": ("Device Roaming Status", "Device intelligence"),
    "location_verify": ("Location Verification", "Digital identity & anti-fraud"),
    "device_swap_check": ("Device Swap", "Digital identity & anti-fraud"),
    "sim_swap_check": ("SIM Swap", "Digital identity & anti-fraud"),
    "sim_swap_date": ("SIM Swap (retrieve date)", "Digital identity & anti-fraud"),
}
