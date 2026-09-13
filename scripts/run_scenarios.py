"""Run every seeded scenario through the agent and print the traces.

    python scripts/run_scenarios.py            # all scenarios, fixture or live depending on NAC_API_KEY
    python scripts/run_scenarios.py honest     # one scenario
    python scripts/run_scenarios.py --json     # also write runs/<scenario>.json

Exit code is non-zero if any scenario's decision differs from its expected decision.
"""
from __future__ import annotations

import json
import os
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to cp1252

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from saqqa import config, scenarios  # noqa: E402
from saqqa.agent.graph import SaqqaAgent  # noqa: E402
from saqqa.agent.llm import LLM  # noqa: E402
from saqqa.nac.client import NaCClient  # noqa: E402


def main(argv: list[str]) -> int:
    want_json = "--json" in argv
    ids = [a for a in argv if not a.startswith("--")]
    todo = [scenarios.get(i) for i in ids] if ids else [dict(s) for s in scenarios.SCENARIOS]
    llm = LLM()
    print(f"mode: {'LIVE Nokia NaC sandbox' if config.LIVE else 'FIXTURES mirroring the sandbox'} · LLM: {llm.provider}"
          + (f" · sink {config.WEBHOOK_SINK}" if config.LIVE else ""))
    failures = 0
    for sc in todo:
        nac = NaCClient()
        agent = SaqqaAgent(nac=nac, llm=llm)
        t0 = time.perf_counter()
        out = agent.run(sc)
        ok = out["decision"] == sc["expect"]
        failures += 0 if ok else 1
        print("\n" + "=" * 100)
        print(f"{sc['id']:<28} {sc['title']}")
        print(f"{'':<28} expected {sc['expect']} · got {out['decision']} {'✓' if ok else '✗'} · {len(out['calls'])} calls · "
              f"{round((time.perf_counter() - t0) * 1000)} ms")
        print("-" * 100)
        for st in out["steps"]:
            print(f"{st['node'].upper():<12} {st['text']}")
        if want_json:
            os.makedirs("runs", exist_ok=True)
            with open(os.path.join("runs", f"{sc['id']}.json"), "w", encoding="utf-8") as f:
                json.dump({k: v for k, v in out.items()}, f, indent=1, default=str)
    print("\n" + ("all scenarios decided as expected" if not failures else f"{failures} scenario(s) differ from expectation"))
    if llm.errors:
        print("LLM errors:", *llm.errors, sep="\n  ")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
