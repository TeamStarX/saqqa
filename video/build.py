"""Assemble the demo film: copy footage and voiceover into the Remotion project, compute the
timeline from the narration lengths, render, and place the result at docs/video/saqqa_demo.mp4.

    python video/build.py            (after video/capture.py and the voiceover in video/vo/)
    python video/build.py --still 90 (one frame, to check the look without a full render)
"""
from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REM = os.path.join(HERE, "remotion")
PUB = os.path.join(REM, "public")
FOOT = os.path.join(HERE, "footage")
VO = os.path.join(HERE, "vo")
PAD_S = 0.7            # breath after each narration
FADE_S = 0.35

CARD_LAYOUTS = {
    "02_problem": ("stats", [{"big": "$176M", "cap": "a year in Jordan alone, settled on paper"},
                              {"big": "1", "cap": "signature releases the money"},
                              {"big": "0", "cap": "meters on the water"}]),
    "03_what": ("steps", ["A level sensor on the buyer's tank", "The SIM already in the tanker's cab", "The mobile operator is the witness"]),
    "08_money": ("stats", [{"big": "$30", "cap": "a truckload of water"},
                            {"big": "13.6¢", "cap": "of network calls to verify it"},
                            {"big": "0", "cap": "things to install on the truck"}]),
    "09_close": ("close", None),
}


def probe(path: str) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True).stdout.strip()
    return float(out or 0)


def main(argv):
    script = json.load(open(os.path.join(HERE, "script.json"), encoding="utf-8"))
    fps = script["fps"]
    os.makedirs(os.path.join(PUB, "footage"), exist_ok=True)
    os.makedirs(os.path.join(PUB, "vo"), exist_ok=True)

    scenes, start = [], 0
    for sc in script["scenes"]:
        s = {k: sc[k] for k in ("id", "kind", "narration", "on_screen")}
        if sc.get("clip"):
            src = os.path.join(FOOT, sc["clip"] + ".mp4")
            if not os.path.exists(src):
                raise SystemExit(f"missing footage {src}: run video/capture.py")
            shutil.copy2(src, os.path.join(PUB, "footage", sc["clip"] + ".mp4"))
            s["clip"] = sc["clip"]
        vo_src = os.path.join(VO, sc["id"] + ".wav")
        if not os.path.exists(vo_src):
            # a raw take from the generator is enough: normalise it here (48 kHz mono, -16 LUFS)
            raws = sorted(f for f in os.listdir(VO) if f.startswith("_" + sc["id"] + "_") and f.endswith("_raw.wav")) if os.path.isdir(VO) else []
            if raws:
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(VO, raws[0]),
                                "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "48000", "-ac", "1", vo_src], check=True)
                print(f"  normalised {raws[0]} -> {os.path.basename(vo_src)}")
        seconds = sc["target_seconds"]
        if os.path.exists(vo_src):
            shutil.copy2(vo_src, os.path.join(PUB, "vo", sc["id"] + ".wav"))
            s["vo"] = "vo/" + sc["id"] + ".wav"
            seconds = probe(vo_src) + PAD_S
        else:
            print(f"  (no voiceover yet for {sc['id']}: using target {seconds}s)")
        if sc.get("clip"):
            clip_len = probe(os.path.join(FOOT, sc["clip"] + ".mp4"))
            marks_path = os.path.join(FOOT, sc["clip"] + ".json")
            m = json.load(open(marks_path)) if os.path.exists(marks_path) else {}
            # marks were taken from page creation; the recording ends at context close, so shift them onto video time
            off = (m.get("end", clip_len) - clip_len) if m else 0.0
            v = {k: max(0.0, m[k] - off) for k in ("paint", "click", "step", "verdict") if k in m}
            start = v.get("paint", 2.6) + 0.3            # skip the white before first paint
            if sc["clip"] == "apis" and "verdict" in v:
                start = v["verdict"] + 0.4                # the calls scene opens on the finished run
            segs = [[start, clip_len]]
            need = seconds
            if "verdict" in v and sc["clip"] != "apis":
                # the verdict must be on screen for 4.5 s; a run longer than the narration allows is cut in the middle
                run_len = v["verdict"] - v["click"]
                budget = seconds - (v["click"] - start) - 4.5
                if run_len > budget + 1.5 and "step" in v:
                    seg1 = [start, v["click"] + 1.5]
                    seg3 = [v["verdict"] - 1.2, clip_len]
                    fill = max(3.5, seconds - (seg1[1] - seg1[0]) - (seg3[1] - seg3[0]))
                    seg2 = [v["step"] - 0.2, min(v["step"] - 0.2 + fill, seg3[0])]
                    segs = [seg1, seg2, seg3]
                    print(f"  {sc['id']}: run {run_len:.0f}s, cut to click -> first steps -> verdict")
                else:
                    need = max(seconds, v["verdict"] - start + 4.5)
            avail = sum(b - a for a, b in segs)
            seconds = max(need, 0)
            if avail < seconds:
                print(f"  WARNING {sc['id']}: footage {avail:.1f}s shorter than scene {seconds:.1f}s; clamping")
                seconds = avail
            s["segments"] = [[round(a, 2), round(b, 2)] for a, b in segs]
        layout = CARD_LAYOUTS.get(sc["id"])
        if layout:
            s["layout"] = layout[0]
            if layout[0] == "stats":
                s["stats"] = layout[1]
            if layout[0] == "steps":
                s["steps"] = layout[1]
        s["start"] = start
        s["frames"] = int(math.ceil(seconds * fps))
        start += s["frames"]
        scenes.append(s)

    timeline = {"fps": fps, "width": script["width"], "height": script["height"], "tail": int(1.0 * fps), "scenes": scenes}
    json.dump(timeline, open(os.path.join(REM, "src", "timeline.json"), "w", encoding="utf-8"), indent=1)
    total = (start + timeline["tail"]) / fps
    print(f"timeline: {len(scenes)} scenes, {total:.1f} s")

    npx = "npx.cmd" if os.name == "nt" else "npx"
    if "--still" in argv:
        frame = argv[argv.index("--still") + 1]
        subprocess.run([npx, "remotion", "still", "src/index.tsx", "SaqqaDemo", "out/frame.png", "--frame", frame], cwd=REM, check=True)
        print("still ->", os.path.join(REM, "out", "frame.png"))
        return
    out = os.path.join(REM, "out", "saqqa_demo.mp4")
    subprocess.run([npx, "remotion", "render", "src/index.tsx", "SaqqaDemo", out, "--codec", "h264", "--crf", "18"], cwd=REM, check=True)
    dst = os.path.join(ROOT, "docs", "video", "saqqa_demo.mp4")
    shutil.copy2(out, dst)
    print(f"film -> {dst}  ({probe(dst):.1f} s, {os.path.getsize(dst) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main(sys.argv[1:])
