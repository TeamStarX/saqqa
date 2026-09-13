"""Drive the dashboard with Playwright and save screenshots for the deck and the HackerEarth "Snapshots" field.

    uvicorn saqqa.server:app --port 8000   (in another terminal)
    python scripts/screenshots.py [scenario ...]      -> docs/screenshots/<scenario>.png
"""
from __future__ import annotations

import os
import sys
import time

from playwright.sync_api import sync_playwright

BASE = os.environ.get("SAQQA_URL", "http://localhost:8000")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "screenshots")


def main(ids: list[str]) -> None:
    os.makedirs(OUT, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page(viewport={"width": 1600, "height": 1750}, device_scale_factor=1.5)
        page.goto(BASE, wait_until="networkidle")
        if not ids:
            # the landing, before any run: what a judge sees when the Demo Link opens
            page.set_viewport_size({"width": 1600, "height": 900})
            time.sleep(0.6)
            page.screenshot(path=os.path.join(OUT, "landing.png"), full_page=False)
            page.set_viewport_size({"width": 1600, "height": 1750})
            print("saved landing")
        cards = page.locator(".scen")
        n = cards.count()
        all_ids = [cards.nth(i).get_attribute("data-id") for i in range(n)]
        todo = ids or all_ids
        for sid in todo:
            page.locator(f".scen[data-id='{sid}']").click()
            # wait until the decision card is filled
            for _ in range(200):
                time.sleep(0.25)
                if page.locator("#decision .big").count():
                    break
            time.sleep(1.2)
            page.screenshot(path=os.path.join(OUT, f"{sid}.png"), full_page=False)
            print("saved", sid)
        b.close()


if __name__ == "__main__":
    main(sys.argv[1:])
