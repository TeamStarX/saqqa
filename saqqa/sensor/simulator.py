"""Tank sensor simulator.

Phase 1 of Saqqa has no hardware: the tank-level / turbidity sensor is modelled here, and the dashboard says so.
The model is a pump-discharge curve, not a straight line, because the agent's plausibility checks look at the
*shape* of the trace (step functions and flat lines during a claimed fill are the tells of a manipulated feed).

  * 1-minute samples from 08:30 to 10:30 (t = 0..120 min).
  * discharge from a 10 m³ tanker ramps 0 -> ~8 L/s over ~2 minutes, holds, tapers (an S-curve in level).
  * 1 cm of level = `litres_per_cm` litres (100 L for the 20 m³ demo tank).
  * ±0.35 cm sensor noise, deterministic (sin/cos) so runs are reproducible.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

T0_HHMM = "08:30"
DURATION_MIN = 120


def hhmm(t_min: float) -> str:
    h, m = 8, 30 + int(round(t_min))
    return f"{h + m // 60:02d}:{m % 60:02d}"


def minutes(hh_mm: str) -> int:
    h, m = hh_mm.split(":")
    return (int(h) - 8) * 60 + int(m) - 30


@dataclass
class SensorSpec:
    level0_cm: float = 38.0        # level at 08:30
    rise_cm: float = 0.0           # total rise from the delivery
    rise_start: str | None = None  # HH:MM when discharge starts
    rise_minutes: int = 22         # duration of the discharge
    turbidity_ntu: float = 1.2
    offline: bool = False          # sensor sends nothing (reachability lost)
    step: bool = False             # manipulated feed: the whole rise arrives in one sample
    noise_cm: float = 0.35
    litres_per_cm: float = 100.0
    height_cm: int = 200


@dataclass
class Trace:
    samples: list[dict] = field(default_factory=list)  # {t, time, level_cm, turb_ntu}
    spec: SensorSpec | None = None

    # ---- derived facts the agent uses ------------------------------------------------------------------
    def level_at(self, hh_mm: str) -> float | None:
        t = minutes(hh_mm)
        for s in self.samples:
            if s["t"] == t:
                return s["level_cm"]
        return None

    def rise_window(self, min_rise_cm_per_3min: float = 2.0) -> tuple[str, str] | None:
        """First and last minute where the level is rising faster than noise (3-minute slope). None if flat."""
        lv = [s["level_cm"] for s in self.samples]
        rising = [i for i in range(1, len(lv) - 2) if lv[i + 2] - lv[i - 1] > min_rise_cm_per_3min]
        if not rising:
            return None
        return hhmm(rising[0]), hhmm(rising[-1] + 2)

    def delta_cm(self, start: str | None = None, end: str | None = None) -> float:
        a = self.level_at(start) if start else self.samples[0]["level_cm"]
        b = self.level_at(end) if end else self.samples[-1]["level_cm"]
        if a is None or b is None:
            return 0.0
        return round(b - a, 1)

    def max_step_cm(self) -> float:
        return round(max((s["level_cm"] - a["level_cm"] for a, s in zip(self.samples, self.samples[1:])), default=0.0), 1)

    def max_turbidity(self) -> float | None:
        vals = [s["turb_ntu"] for s in self.samples if s.get("turb_ntu") is not None]
        return round(max(vals), 1) if vals else None


def simulate(spec: SensorSpec) -> Trace:
    tr = Trace(spec=spec)
    if spec.offline:
        return tr
    start = minutes(spec.rise_start) if spec.rise_start else None
    for t in range(DURATION_MIN + 1):
        level = spec.level0_cm
        if start is not None and t >= start and spec.rise_cm:
            if spec.step:
                level += spec.rise_cm
            else:
                x = min(1.0, (t - start) / max(1, spec.rise_minutes))
                s_curve = (1 - math.cos(math.pi * x)) / 2
                level += spec.rise_cm * s_curve
        level += (math.sin(t * 1.7) + math.cos(t * 0.9)) * spec.noise_cm
        level = max(0.0, min(float(spec.height_cm), level))
        # turbidity rises with the delivered water, so a dirty load shows up as the level rises
        in_rise = start is not None and t >= start
        turb = spec.turbidity_ntu if in_rise else min(spec.turbidity_ntu, 1.3)
        turb += (math.sin(t * 0.7)) * 0.05
        tr.samples.append({"t": t, "time": hhmm(t), "level_cm": round(level, 1), "turb_ntu": round(turb, 2)})
    return tr
