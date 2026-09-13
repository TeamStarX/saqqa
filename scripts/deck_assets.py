"""Capture the deck's dashboard assets from the live page, so they cannot drift from the product.

    uvicorn saqqa.server:app --port 8000
    python scripts/deck_assets.py            -> deck/assets/demo_hero_top.png, demo_hero_trace.png, profile_core.png

Until 13 Sep these were hand crops made on 3 Sep. The dashboard was rebuilt twice after that and the
deck kept embedding the old design while its text slides were rebuilt - a mismatch nobody would
notice from the build log. Every asset is now a clip of the running dashboard, same aspect ratio
the slides were laid out for (about 2.03:1 at w=1440 on a 1920x1080 slide).
"""
from __future__ import annotations

import os
import sys
import time

from playwright.sync_api import sync_playwright

BASE = os.environ.get("SAQQA_URL", "http://localhost:8000")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "deck", "assets")
W, CLIP_H = 1600, 788          # 1600x788 css at 1.5x -> 2400x1182, the shape the slides expect


def wait_decision(page, timeout_s: float = 90) -> None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if page.locator("#decision .big").count():
            return
        time.sleep(0.25)
    raise SystemExit("no verdict arrived in time; is the server live?")


def settle(page, ms: int = 900) -> None:
    page.evaluate("window.getSelection().removeAllRanges()")
    page.wait_for_timeout(ms)


def clip_top(page, path: str) -> None:
    page.evaluate("window.scrollTo(0, 0)")
    settle(page)
    page.screenshot(path=path, clip={"x": 0, "y": 0, "width": W, "height": CLIP_H})


def clip_element(page, selector: str, path: str, height: int = CLIP_H, pad_top: int = 56) -> None:
    """Clip a viewport-sized window with `selector` at the top: the tabs strip plus the panel."""
    page.evaluate(
        "([s, p]) => { const e = document.querySelector(s); const y = e.getBoundingClientRect().top + window.scrollY - p;"
        " window.scrollTo({top: y, behavior: 'instant'}); }", [selector, pad_top])
    settle(page)
    stop = page.evaluate("() => { const t = document.querySelector('.takes'); return t ? t.getBoundingClientRect().top : 1e9; }")
    height = int(min(height, max(400, stop - 28)))   # never slice through the 'what it takes' strip
    page.screenshot(path=path, clip={"x": 0, "y": 0, "width": W, "height": height})


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page(viewport={"width": W, "height": 1000}, device_scale_factor=1.5)
        page.goto(BASE, wait_until="networkidle")
        page.wait_for_timeout(600)

        # 1. the hero trip on the full profile: claim + verdict (slide 13)
        page.locator("#profile button").filter(has_text="full").click()
        page.locator(".scen[data-id='sensor_contradicts_network']").click()
        wait_decision(page)
        page.wait_for_timeout(1500)
        clip_top(page, os.path.join(OUT, "demo_hero_top.png"))
        print("saved demo_hero_top.png")

        # 2. the same run's reasoning: tabs strip + trace, contradiction and investigate rounds (slide 13b)
        page.evaluate("window.showTab('agent')")
        clip_element(page, ".tabs", os.path.join(OUT, "demo_hero_trace.png"))
        print("saved demo_hero_trace.png")

        # 3. deployable today: core profile, payee SIM-swap, BLOCK on three APIs (slide 09b)
        page.locator("#profile button").filter(has_text="core").click()
        page.wait_for_timeout(300)
        page.evaluate("select('payee_swapped', false)")
        page.wait_for_timeout(300)
        page.locator("#run").click()
        wait_decision(page)
        page.wait_for_timeout(1500)
        clip_top(page, os.path.join(OUT, "profile_core.png"))
        print("saved profile_core.png")
        b.close()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
