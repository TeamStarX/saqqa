"""Footage for the demo film: one 1920x1080 clip per scene, driven against the live dashboard.

    uvicorn saqqa.server:app --port 8000          (in another terminal)
    python video/capture.py [clip ...]            -> video/footage/<clip>.mp4

Each clip is its own browser context so Playwright writes one webm per clip; ffmpeg then
re-encodes to h264 at 30 fps for the Remotion composition. No cursor is recorded: the
narration says what is happening, the page shows it.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time

from playwright.sync_api import sync_playwright

BASE = os.environ.get("SAQQA_URL", "http://localhost:8000")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "footage")
TMP = os.path.join(OUT, "_raw")
W, H = 1920, 1080


def wait_decision(page, timeout_s=90):
    for _ in range(int(timeout_s / 0.25)):
        if page.locator("#decision .big").count():
            return
        time.sleep(0.25)
    raise SystemExit("no verdict within the wait; is the server live?")


def scroll_to(page, selector, block="center"):
    page.evaluate(
        "([s, b]) => document.querySelector(s)?.scrollIntoView({behavior: 'smooth', block: b})",
        [selector, block],
    )


def hold(s):
    time.sleep(s)


MARKS = {}
T0 = 0.0


def mark(name):
    MARKS[name] = round(time.time() - T0, 2)


def wait_first_step(page, timeout_s=60):
    for _ in range(int(timeout_s / 0.2)):
        if page.locator("#trace .ln").count():
            return
        time.sleep(0.2)


def profile(page, name):
    """Click the deployment-profile segment whose label starts with `name` (core or full)."""
    page.locator("#profile button", has_text=name).first.click()
    time.sleep(0.8)


# --------------------------------------------------------------------------- the clips
def clip_honest(page):
    page.goto(BASE + "/?record=1", wait_until="networkidle")
    mark("paint")
    hold(2.0)                                    # the landing, still
    page.click("#cta_run")                       # hero collapses, run starts
    mark("click")
    wait_first_step(page); mark("step")
    wait_decision(page); mark("verdict")
    hold(3)
    scroll_to(page, "#decision", "start")        # verdict at the top, the two clocks below it
    hold(7)


def clip_doubt(page):
    page.goto(BASE + "/?record=1", wait_until="networkidle")
    mark("paint")
    page.evaluate("select('sensor_contradicts_network', false)")
    hold(0.8)
    profile(page, "full")
    page.click("#run"); mark("click")
    wait_first_step(page); mark("step")
    wait_decision(page); mark("verdict")
    scroll_to(page, "#decision", "start")
    hold(7)
    page.click(".tabs button[data-tab='agent']")
    scroll_to(page, ".tabs", "start")
    hold(6)


def clip_block(page):
    page.goto(BASE + "/?record=1", wait_until="networkidle")
    mark("paint")
    page.evaluate("select('payee_swapped', false)")
    hold(0.8)
    profile(page, "full")
    page.click("#run"); mark("click")
    wait_first_step(page); mark("step")
    wait_decision(page); mark("verdict")
    scroll_to(page, "#decision", "start")
    hold(8)


def clip_apis(page):
    page.goto(BASE + "/?record=1", wait_until="networkidle")
    mark("paint")
    page.evaluate("select('honest', false)")
    hold(0.8)
    profile(page, "full")
    page.click("#run"); mark("click")
    wait_first_step(page); mark("step")
    wait_decision(page); mark("verdict")
    scroll_to(page, "#apistrip", "center")
    hold(4)
    page.click(".tabs button[data-tab='calls']")
    scroll_to(page, ".tabs", "start")
    hold(7)


def clip_landing(page):
    page.goto(BASE + "/?record=1", wait_until="networkidle")
    hold(8)


def clip_takes(page):
    page.goto(BASE + "/?record=1", wait_until="networkidle")
    page.click(".scen[data-id='honest']")
    wait_decision(page)
    scroll_to(page, ".takes", "center")
    hold(7)


CLIPS = {
    "landing": clip_landing,
    "honest": clip_honest,
    "doubt": clip_doubt,
    "block": clip_block,
    "apis": clip_apis,
    "takes": clip_takes,
}


def main(names):
    os.makedirs(OUT, exist_ok=True)
    shutil.rmtree(TMP, ignore_errors=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        for name in names or list(CLIPS):
            raw_dir = os.path.join(TMP, name)
            os.makedirs(raw_dir, exist_ok=True)
            ctx = b.new_context(viewport={"width": W, "height": H}, device_scale_factor=1,
                                record_video_dir=raw_dir, record_video_size={"width": W, "height": H})
            page = ctx.new_page()
            global T0
            T0 = time.time(); MARKS.clear()
            t0 = T0
            CLIPS[name](page)
            mark("end")
            video = page.video
            ctx.close()
            src = video.path()
            dst = os.path.join(OUT, f"{name}.mp4")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-c:v", "libx264", "-preset", "medium",
                            "-crf", "18", "-pix_fmt", "yuv420p", "-r", "30", "-an", "-movflags", "+faststart", dst], check=True)
            dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", dst],
                                 capture_output=True, text=True).stdout.strip()
            import json
            json.dump(dict(MARKS, duration=float(dur)), open(os.path.join(OUT, f"{name}.json"), "w"), indent=1)
            print(f"{name}: {float(dur):.1f} s  marks {MARKS}  -> {dst}")
        b.close()
    shutil.rmtree(TMP, ignore_errors=True)


if __name__ == "__main__":
    main(sys.argv[1:])
