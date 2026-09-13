"""Record the demo video: drive the live dashboard with Playwright, captions timed to what the agent actually does.

    uvicorn saqqa.server:app --port 8000      (live: NAC_API_KEY, GOOGLE_API_KEY, PUBLIC_BASE_URL set)
    python scripts/record_demo.py             -> docs/video/saqqa_demo.webm  (under 3 min, 1600x900)

The captions are the narration lines from docs/DEMO_SCRIPT.md. Lay a voice over the file in Clipchamp, or upload as is.
"""
from __future__ import annotations

import os
import shutil
import sys
import time

from playwright.sync_api import sync_playwright

BASE = os.environ.get("SAQQA_URL", "http://localhost:8000")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "docs", "video")
TMP = os.path.join(OUT_DIR, "_raw")
W, H = 1600, 900


def check_server_is_current() -> None:
    """Refuse to film a server running code older than the working tree."""
    import json as _json
    import urllib.request
    sys.path.insert(0, ROOT)
    from saqqa import config                      # imports the tree as it is right now
    with urllib.request.urlopen(BASE + "/api/status", timeout=10) as r:
        running = _json.load(r).get("source_sha")
    if running != config.SOURCE_SHA:
        raise SystemExit(
            "\n".join([
                f"REFUSING TO RECORD: the server is running source {running}, "
                f"the working tree is {config.SOURCE_SHA}.",
                "Restart it before recording:",
                "    uvicorn saqqa.server:app --port 8000",
            ]))


def main() -> None:
    check_server_is_current()
    os.makedirs(OUT_DIR, exist_ok=True)
    shutil.rmtree(TMP, ignore_errors=True)
    t_start = time.time()
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": W, "height": H}, record_video_dir=TMP,
                            record_video_size={"width": W, "height": H}, device_scale_factor=1)
        page = ctx.new_page()
        page.goto(BASE + "/?record=1", wait_until="networkidle")
        page.wait_for_timeout(600)

        def cap(text: str, hold: float) -> None:
            page.evaluate("t => window.setCaption(t)", text)
            page.wait_for_timeout(int(hold * 1000))

        def scroll(y: int) -> None:
            page.evaluate(f"window.scrollTo({{top: {y}, behavior: 'smooth'}})")
            page.wait_for_timeout(700)

        def see(selector: str, block: str = "center") -> None:
            """Bring a section into frame by identity, not by pixel offset."""
            page.evaluate(
                "([s, b]) => { const e = document.querySelector(s);"
                " if (e) e.scrollIntoView({behavior: 'smooth', block: b}); }",
                [selector, block])
            page.wait_for_timeout(750)

        def wait_trace(substr: str, timeout_s: float = 60) -> bool:
            deadline = time.time() + timeout_s
            while time.time() < deadline:
                if page.evaluate(f"document.getElementById('trace').innerText.includes({substr!r})"):
                    return True
                page.wait_for_timeout(200)
            return False

        def wait_decision(timeout_s: float = 55) -> None:
            deadline = time.time() + timeout_s
            while time.time() < deadline:
                if page.locator("#decision .big").count():
                    return
                page.wait_for_timeout(200)

        def run(scenario: str) -> None:
            page.locator(f".scen[data-id='{scenario}']").click()

        t_film = time.time()

        def elapsed() -> float:
            return time.time() - t_film

        # ---------------------------------------------------------------- 0:00 intro
        cap("A water delivery is paid for on the word of the person being paid.", 2.8)
        cap("Saqqa: a sensor on the buyer's tank, a SIM in the tanker's cab, and the operator's network as the witness. "
            "Every SIM here belongs to an organisation. No household is involved.", 4.0)

        # ---------------------------------------------------------------- honest delivery
        run("honest")
        cap("The agent plans which checks to buy, then makes them live on Nokia Network as Code. Every request and response is on screen.", 3.7)
        if wait_trace("operator webhook delivered", 40):
            cap("Four geofence subscriptions on the cab SIM. The operator delivers a CloudEvent to our webhook within seconds of each one.", 3.7)
        see(".clocks, #chart")
        cap("Entry and exit stamps from the operator give dwell. The tank rising inside that dwell gives litres. The two have to agree.", 3.7)
        wait_decision()
        see("#decision", "start")
        cap("RELEASE: 9.7 cubic metres verified against a claim of 10, paid the same day, reasoning stored. The gate is deterministic. The model never touches money.", 4.7)
        cap("", 2.2)

        # ---------------------------------------------------------------- the agent doubts its own sensor
        scroll(0)
        run("sensor_contradicts_network")
        cap("Now the run that matters. Tank 7 rises 9.7 cubic metres between 09:05 and 09:27. The operator's timestamps put the truck in the zone from 09:35.", 4.3)
        see("#trace")
        wait_trace("does not fit", 37.2)
        see("#chart")
        cap("The evidence contradicts itself, so the agent does not decide. It asks the sensor again whether it can be believed, and asks the network where the truck actually was.", 4.7)
        wait_decision()
        see("#decision", "start")
        cap("The measurement is not believed. Our own sensor loses to the operator's timestamps, because the sensor is ours and the timestamps are nobody's. Not credited, case opened, nobody accused.", 5.0)
        cap("", 2.2)

        # ------------------------------------------- payee fraud AND deployment realism, in one run
        # SIM Swap is in the core profile, so the BLOCK can be demonstrated on three APIs. That
        # answers the mentor's "no operator has all seven" without spending a fourth run on it.
        scroll(0)
        if elapsed() < 108:
          cap("Twelve trips run this way. Two release, two hold, seven escalate, one blocks.", 3.2)
          page.locator("#profile button").filter(has_text="core").click()
          page.wait_for_timeout(500)
          cap("And almost no operator has all seven of these APIs live today. So: three APIs. The ones that are.", 3.8)
          # set the trap before springing it: on the core profile this run finishes inside the
          # caption, so captioning after the click showed the verdict before the setup line.
          # select without running, so the brief on screen matches the caption; clicking a trip
          # auto-runs it, which is why this goes through select(id, false) rather than run().
          page.evaluate("select('payee_swapped', false)")
          page.wait_for_timeout(450)
          cap("A perfect delivery, and the number the money would go to changed SIM inside the last 72 hours.", 2.9)
          page.locator("#run").click()
          wait_decision()
          see("#decision", "start")
          cap("Blocked, on three APIs, before a dinar moves. The agent names every check the smaller profile could not run, instead of pretending it ran them.", 4.8)
          cap("", 2.2)
        else:
          cap("Twelve trips run this way. Two release, two hold, seven escalate, one blocks: a payee whose number changed SIM inside 72 hours, stopped before a dinar moves. It reaches all twelve verdicts on the three-API core profile.", 5.4)

        # ---------------------------------------------------------------- close
        scroll(0)
        cap("Seven CAMARA APIs across two categories — and every verdict still reached on the three it can work on. SIM Swap, the one that stops money, is live in MENA today.", 4.6)
        cap("The tank sensor is the meter. The network is the meter-reader nobody can bribe. The agent is the billing engine.", 3.7)

        # ---------------------------------------------------------------- money (scored: commercial viability)
        cap("A truckload is worth about thirty dollars. Verifying it costs thirteen cents, under half a percent. Stop two percent of overbilling and the buyer earns that back four and a half times.", 5.6)
        cap("The buyer pays per verified delivery with a per-truck monthly floor. The operator is paid per call: about a million dollars a year from Jordan alone, at two cents a call.", 5.0)
        cap("Water is the wedge because the paper form is public. The same gate can pay for any trucked commodity settled on a delivery note.", 4.0)
        # ---------------------------------------------------------------- what it takes (scored: feasibility)
        cap("Nothing to fit on the truck: the SIM already in the cab is the tracker. One level sensor on the buyer's tank, bought once. The F-306 form stays; Saqqa fills it. A pilot is one buyer, one hauler and one operator key.", 5.6)
        cap("Saqqa  ·  Team StarX  ·  GSMA MENA Ignite Hackathon 2026", 2.5)
        cap("", 2.2)

        video = page.video
        ctx.close()
        b.close()
        src = video.path()
    dst = os.path.join(OUT_DIR, "saqqa_demo.webm")
    shutil.move(src, dst)
    shutil.rmtree(TMP, ignore_errors=True)
    print(f"saved {dst} · {os.path.getsize(dst) / 1e6:.1f} MB · wall time {time.time() - t_start:.0f} s")
    if time.time() - t_start > 180:
        print("WARNING: the recording ran past three minutes; the submission cap is 3:00")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
