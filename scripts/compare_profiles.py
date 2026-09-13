"""Run every seeded trip under each deployment profile and print the comparison.

    python scripts/compare_profiles.py            # fixture mode, fast, deterministic
    NAC_MODE=live python scripts/compare_profiles.py

The question this answers is the one the mentor asked on 3 Sep 2026: almost no operator has all
seven CAMARA APIs live, so does the agent still work on the set that is actually deployed?

It is evidence, not decoration. If a future change makes `core` diverge from `full`, this script
says so, and the claim in docs/DEPLOYMENT_REALISM.md has to be rewritten rather than repeated.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("NAC_MODE", "fixture")

from saqqa import config, scenarios                      # noqa: E402
from saqqa.agent.graph import SaqqaAgent                 # noqa: E402

NAMES = ["core", "full"]


def main() -> int:
    rows, disagreements = [], 0
    for sc in scenarios.SCENARIOS:
        out = {}
        for prof in NAMES:
            st = SaqqaAgent(profile=prof).run(scenarios.get(sc["id"]))
            out[prof] = (st["decision"], len(st["calls"]), len({c["api"] for c in st["calls"]}))
        agree = len({v[0] for v in out.values()}) == 1
        disagreements += not agree
        rows.append((sc["id"], sc["expect"], out, agree))

    w = max(len(r[0]) for r in rows)
    head = f"{'trip':<{w}}  {'expected':<9}"
    for n in NAMES:
        head += f"  {n + ' verdict':<16}{'calls':>6}{'apis':>5}"
    print(head + "   agree")
    print("-" * len(head + "   agree"))
    for tid, expect, out, agree in rows:
        line = f"{tid:<{w}}  {expect:<9}"
        for n in NAMES:
            d, calls, apis = out[n]
            line += f"  {d:<16}{calls:>6}{apis:>5}"
        print(line + f"   {'yes' if agree else 'NO'}")

    matched = sum(1 for _, e, o, _ in rows if o["full"][0] == e)
    print()
    print(f"full profile matches the expected verdict on {matched}/{len(rows)} trips")
    print(f"core profile reproduces the full-profile verdict on {len(rows) - disagreements}/{len(rows)} trips")
    print()
    for n in NAMES:
        p = config.profile(n)
        tot = sum(o[n][1] for _, _, o, _ in rows)
        print(f"  {p['label']:<26} {len({config.API_CATALOGUE[t][0].split(' (')[0] for t in p['tools']})} APIs, "
              f"{tot} calls over {len(rows)} trips ({tot / len(rows):.1f}/trip)")
    print()
    print("Reproducing the verdict is not the same as having the same evidence: `core` cannot check")
    print("device swap, roaming or post-delivery trajectory, and its dwell is polled. Those gaps are")
    print("named in every verdict it issues. See docs/DEPLOYMENT_REALISM.md.")
    return 1 if disagreements else 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
