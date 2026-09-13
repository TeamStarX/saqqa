#!/usr/bin/env python3
"""Saqqa pitch deck, Prototype Phase edition.

Same design system as the Round-1 deck (one idea per slide, one typeface, flat ink, real assets carry the
visual slides). Slides are authored as SVG, rendered to 1920x1080 PNG with Playwright's Chromium, assembled into a
PDF (Pillow) and a PPTX (python-pptx, full-bleed images). No rsvg / ImageMagick needed.

    python deck/build_deck.py          -> deck/out/Saqqa_Prototype_Deck.pdf + .pptx, deck/png/*.png
"""
import base64
import pathlib
import struct
import textwrap

HERE = pathlib.Path(__file__).parent
SVG = HERE / "svg"; PNG = HERE / "png"; OUT = HERE / "out"; ASSETS = HERE / "assets"
for d in (SVG, PNG, OUT):
    d.mkdir(exist_ok=True)

W, H = 1920, 1080
M = 130

PAPER = "#F5F3EF"; INK = "#14171C"; DARK = "#111418"; BLUE = "#0E6BA8"; MUTE = "#7C838C"
RULE = "#D8D4CC"; ALERT = "#B4462A"; GREEN = "#2F6B4F"
OFFWHITE = "#F2F0EC"; GREYDARK = "#9AA1AA"; PANEL = "#EDEAE4"; PANELDARK = "#1A1F26"; RULEDARK = "#2A2F36"

F = "Helvetica Neue, Inter, Segoe UI, Arial, sans-serif"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def wrap(text, size, maxw, cpl_factor=0.50):
    cpl = max(8, int(maxw / (size * cpl_factor)))
    return textwrap.wrap(text, cpl) or [""]


def T(x, y, s, size=34, weight="400", fill=INK, family=F, anchor="start", spacing=0, opacity=1.0):
    ls = f' letter-spacing="{spacing}"' if spacing else ""
    op = f' opacity="{opacity}"' if opacity != 1.0 else ""
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}"{ls}{op}>{esc(s)}</text>')


def block(x, y, text, size=34, weight="400", fill=INK, maxw=1000, lh=1.42, anchor="start", opacity=1.0):
    return "\n".join(T(x, y + i * size * lh, line, size, weight, fill, anchor=anchor, opacity=opacity)
                     for i, line in enumerate(wrap(text, size, maxw)))


def png_size(path):
    b = pathlib.Path(path).read_bytes()[16:24]
    return struct.unpack(">II", b)


def img(path, x, y, w=None, h=None):
    iw, ih = png_size(path)
    if w and not h:
        h = round(w * ih / iw)
    elif h and not w:
        w = round(h * iw / ih)
    data = base64.b64encode(pathlib.Path(path).read_bytes()).decode()
    return (f'<image x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid meet" '
            f'xlink:href="data:image/png;base64,{data}"/>')


def rect(x, y, w, h, fill, rx=0, op=1.0):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" rx="{rx}" opacity="{op}"/>'


def line(x1, y1, x2, y2, stroke=RULE, sw=2):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{sw}"/>'


def arrow(x1, y1, x2, y2, stroke=MUTE, sw=2):
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{sw}" '
            f'marker-end="url(#ah)"/>')


def chrome(label, dark=False):
    c = "#5A6068" if dark else MUTE
    return (T(M, H - 62, label.upper(), 19, "500", c, spacing=2.4) +
            T(W - M, H - 62, "__PAGENO__", 19, "500", c, anchor="end", spacing=2.4))


DEFS = ('<defs><marker id="ah" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto">'
        '<path d="M0,0 L10,5 L0,10 z" fill="#7C838C"/></marker></defs>')


def svg(body, bg=PAPER):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{W}" height="{H}" viewBox="0 0 {W} {H}">{DEFS}{rect(0, 0, W, H, bg)}{body}</svg>')


SLIDES = []


def slide(name, body, bg=PAPER):
    SLIDES.append((name, svg(body, bg)))


def stat(x, y, big, unit, cap, w=380, big_size=92):
    return "".join([T(x, y, big, big_size, "200", INK),
                    T(x + len(big) * 50, y, unit, 30, "400", MUTE) if unit else "",
                    block(x, y + 58, cap, 24, "400", MUTE, maxw=w, lh=1.36)])


def approw(rows, y0, x=M, lh=64, kw=560, ks=26, vs=26, dark=False):
    kc = OFFWHITE if dark else INK; vc = GREYDARK if dark else MUTE; rc = RULEDARK if dark else RULE
    out = []
    for i, (k, v) in enumerate(rows):
        y = y0 + i * lh
        out.append(line(x, y - 30, W - M, y - 30, rc))
        out.append(block(x, y, k, ks, "500", kc, maxw=kw - 60, lh=1.3))
        out.append(block(x + kw, y, v, vs, "300", vc, maxw=W - M - x - kw, lh=1.3))
    return "".join(out)


def steps(items, y0, x=M, lh=118, numw=86, ts=30, dark=False):
    kc = OFFWHITE if dark else INK; vc = GREYDARK if dark else MUTE
    out = []
    for i, (head, body) in enumerate(items):
        y = y0 + i * lh
        out.append(T(x, y, f"{i + 1:02d}", 26, "500", BLUE))
        out.append(T(x + numw, y, head, ts, "500", kc))
        out.append(block(x + numw, y + 40, body, 24, "300", vc, maxw=W - M - x - numw, lh=1.34))
    return "".join(out)


def box(x, y, w, h, title, body, dark=False, fill=None, tsize=21, bsize=23):
    f = fill or (PANELDARK if dark else PANEL)
    tc = BLUE; bc = OFFWHITE if dark else INK
    return "".join([rect(x, y, w, h, f), T(x + 26, y + 44, title.upper(), tsize, "500", tc, spacing=1.8),
                    block(x + 26, y + 84, body, bsize, "300" if dark else "400", bc, maxw=w - 52, lh=1.32)])


# ═══════════════════════════════════════════════════════ 01  title
slide("01_title", "".join([
    rect(0, 0, 18, H, BLUE),
    T(M, 320, "SAQQA", 150, "200", INK, spacing=14),
    T(M + 830, 320, "سقّا", 76, "300", MUTE),
    line(M, 420, W - M, 420),
    block(M, 520, "Network-attested delivery and payment for trucked water.",
          52, "300", INK, maxw=1400, lh=1.34),
    block(M, 742, "Trucked water is the utility for millions across MENA, still billed on a paper form. This working prototype "
                  "is an AI agent that uses the mobile network to check a delivery really happened, then releases payment "
                  "for the litres it can prove. Live on Nokia Network as Code.",
          32, "400", BLUE, maxw=1560, lh=1.34),
    T(M, H - 130, "MENA IGNITE HACKATHON   ·   PROTOTYPE PHASE   ·   THEME 6, CLIMATE RESILIENCE   ·   TEAM STARX",
      19, "500", MUTE, spacing=2.6),
]))

# ═══════════════════════════════════════════════════════ 02  the problem
slide("02_problem", "".join([
    rect(0, 0, W, H, DARK), rect(0, 0, 18, H, BLUE),
    T(M, 148, "THE PROBLEM", 19, "500", "#5A6068", spacing=2.6),
    block(M, 280, "A water delivery is paid for on the word of the person being paid.", 70, "300", OFFWHITE, maxw=1560, lh=1.26),
    line(M, 470, M + 210, 470, "#3A4048", 3),
    block(M, 556, "A tanker arrives at a camp, a clinic or a hotel. Someone signs a paper form to say it delivered ten "
                  "cubic metres. That signature is what releases the money.", 31, "300", GREYDARK, maxw=1560, lh=1.4),
    block(M, 700, "Nobody measured the water. There is no meter on the truck and no meter on the tank. The number on "
                  "the form is the number the driver said.", 31, "300", GREYDARK, maxw=1560, lh=1.4),
    rect(M, 830, W - 2 * M, 108, PANELDARK),
    block(M + 44, 878, "Amal is a WASH officer with 97 sites and one pickup truck. Every Thursday she signs for water "
                       "she did not see arrive, because that is the process.", 28, "400", OFFWHITE, maxw=1520, lh=1.34),
    chrome("the problem", dark=True),
]), bg=DARK)

# ═══════════════════════════════════════════════════════ 03  the incumbent
slide("03_form", "".join([
    T(M, 148, "HOW IT IS DONE TODAY", 19, "500", MUTE, spacing=2.6),
    block(M, 232, "This is the state of the art. It is a pen.", 64, "300", INK, maxw=1100),
    rect(M, 336, 942, 620, "#FFFFFF"),
    img(ASSETS / "f306-1.png", M + 26, 372, h=548),
    line(1200, 336, 1200, 956, RULE),
    T(1268, 392, "UNHCR FORM F-306", 24, "500", BLUE, spacing=1.6),
    block(1268, 456, "GPS coordinates written by hand. A pen signature from a delivery-point representative. "
                     "Copies posted once a week.", 27, "400", INK, maxw=460),
    block(1268, 646, "“Will be used as part of the payment justification process to the contractor.”", 26, "400", ALERT, maxw=460),
    T(1268, 866, "UNHCR's own words, printed on the form.", 21, "400", MUTE),
    chrome("the incumbent"),
]))

# ═══════════════════════════════════════════════════════ 04  why it fails
slide("04_causes", "".join([
    T(M, 148, "WHY IT FAILS", 19, "500", MUTE, spacing=2.6),
    block(M, 236, "One cause, four consequences.", 58, "300", INK, maxw=1400),
    rect(M, 320, W - 2 * M, 96, PANEL),
    block(M + 44, 368, "The only record of a delivery is created by the party being paid for it.", 34, "500", INK, maxw=1560),
    T(M, 494, "WHAT GOES WRONG", 19, "500", MUTE, spacing=2.2),
    T(M + 700, 494, "WHY NOBODY CATCHES IT", 19, "500", MUTE, spacing=2.2),
    approw([
        ("Short-filling", "the tanker arrives two thirds full and is paid for a full load. Nobody at the tank has a meter, so there is nothing to disagree with."),
        ("Diversion", "the load is sold somewhere that pays better and the delivery is logged anyway. Nobody records where the truck actually went."),
        ("Ghost trips", "trips are billed that never happened at all. The log book is the only record that the trip existed."),
        ("A bought signature", "the delivery-point representative signs for a few dinars. The signature is the payment trigger, so buying it is the whole attack."),
    ], 548, lh=100, kw=700, ks=30, vs=25),
    rect(M, 896, W - 2 * M, 86, PANEL),
    block(M + 44, 934, "A truck that never turns up is reported within the hour by a thirsty household. These four are the "
                       "frauds that survive, because nobody who could report them has a reason to.", 24, "400", BLUE, maxw=1560, lh=1.34),
    chrome("why it fails"),
]))

# ═══════════════════════════════════════════════════════ 05  scale
slide("05_scale", "".join([
    T(M, 148, "HOW BIG THIS IS", 19, "500", MUTE, spacing=2.6),
    block(M, 240, "Drought made the tanker the utility.", 64, "300", INK, maxw=1300),
    line(M, 330, W - M, 330),
    stat(M, 468, "$176M", "", "a year in Jordan's tanker market, more than every public supplier combined"),
    stat(M + 430, 468, "91%", "", "of that water drawn from illegal sources"),
    stat(M + 860, 468, "$40k", "", "a day for one UNICEF trucking operation in Gaza"),
    stat(M + 1272, 468, "4.8–10.7×", "", "the piped price, paid by the people with the least", w=360, big_size=74),
    line(M, 800, W - M, 800),
    block(M, 862, "Iraq has just had its driest year since 1933 and Basra's 4.5 million people are on daily deliveries.", 26, "400", MUTE, maxw=1620),
    T(M, 924, "Klassert et al., Nature Sustainability 6:1406 (2023)  ·  UNICEF  ·  independently verified", 22, "400", MUTE),
    chrome("scale"),
]))

# ═══════════════════════════════════════════════════════ 06  the solution
slide("06_what", "".join([
    rect(0, 0, W, H, DARK),
    T(M, 148, "THE SOLUTION", 19, "500", "#5A6068", spacing=2.6),
    block(M, 250, "Measure the water at the tank. Verify the trip with the mobile network.", 58, "300", OFFWHITE, maxw=1620, lh=1.3),
    block(M, 400, "The payer, an aid agency, a municipality, a hotel, puts two SIM cards into the contract. Neither of "
                  "them goes on the contractor's vehicle body, and nothing is asked of any household.", 29, "300", GREYDARK, maxw=1620, lh=1.4),
    box(M, 520, 760, 300, "SIM one, in the truck cab",
        "Lets the operator's network say which truck this was, which well it loaded at, and how long it stood at the tank.", dark=True, bsize=26),
    box(M + 810, 520, 850, 300, "SIM two, in a sensor on the payer's tank",
        "A level and turbidity probe. The level rising while the truck is there is the volume delivered, in litres.", dark=True, bsize=26),
    block(M, 900, "An AI agent watches both, decides what it is willing to believe, and releases payment for the litres it "
                  "can account for. Every decision is written down with its reasons.", 29, "400", OFFWHITE, maxw=1620, lh=1.38),
    chrome("the solution", dark=True),
]), bg=DARK)

# ═══════════════════════════════════════════════════════ 07  one delivery, as built
slide("07_walkthrough", "".join([
    T(M, 118, "ONE DELIVERY, START TO FINISH · AS BUILT", 19, "500", MUTE, spacing=2.6),
    block(M, 196, "What the prototype does on a single trip.", 50, "300", INK, maxw=1400),
    steps([
        ("The agent plans the checks and registers four geofences on the cab SIM",
         "Well in, well out, tank in, tank out. Each subscription names our webhook as the sink; the operator delivers a CloudEvent to it within seconds. A Location Verification poll stays in the plan regardless."),
        ("The tank level rises while the truck is standing there",
         "The rise, in litres, is the delivered volume. The minutes it rose must sit inside the operator's dwell window, and the dwell must be long enough to have pumped that much."),
        ("The agent asks whether the sensor can be believed at all",
         "Device Reachability says it is online. Location Verification says it is still at its install point. Device Swap says its SIM is still inside it."),
        ("The agent asks who is about to be paid",
         "SIM Swap on the payee's number, with the date of the last change if there was one."),
        ("If the evidence contradicts itself, the agent investigates",
         "It chooses the next network question from a menu (retrieve the truck's location, roaming, re-ask reachability) and decides when to stop. Up to three rounds."),
        ("A deterministic gate decides, the model explains, the ledger records",
         "RELEASE, HOLD, ESCALATE or BLOCK with the litres to pay, an audit note in English and Arabic, and an F-306-compatible export citing every operator call."),
    ], 330, lh=116),
    chrome("walkthrough"),
]))

# ═══════════════════════════════════════════════════════ 08  division of labour
slide("08_split", "".join([
    T(M, 148, "WHAT EACH HALF PROVES", 19, "500", MUTE, spacing=2.6),
    block(M, 236, "The network does not measure water, and we do not say it does.", 52, "300", INK, maxw=1500),
    rect(M, 340, 760, 380, PANEL),
    T(M + 50, 420, "HOW MUCH ARRIVED", 22, "500", MUTE, spacing=2.0),
    block(M + 50, 486, "is a sensor question.", 46, "300", INK, maxw=640),
    block(M + 50, 566, "The tank level answers it, in litres. That is a physical measurement and it needs a physical device.", 25, "400", MUTE, maxw=640),
    rect(M + 810, 340, 850, 380, DARK),
    T(M + 860, 420, "WHOSE TRUCK, FROM WHICH WELL, AND IS THE SENSOR HONEST", 22, "500", "#6E757E", spacing=2.0),
    block(M + 860, 486, "are network questions.", 46, "300", OFFWHITE, maxw=730),
    block(M + 860, 566, "Nothing mounted on the truck can answer them honestly, because the truck belongs to the party being audited.", 25, "400", GREYDARK, maxw=730),
    block(M, 810, "The tank sensor is the meter. The network is the meter-reader nobody can bribe. The agent is the billing engine.",
          28, "400", BLUE, maxw=1600),
    chrome("the split"),
]))

# ═══════════════════════════════════════════════════════ 09  the APIs, verified live
API_ROWS = [
    ("Location Verification", "core · Anti-fraud", "presence poll at the tank zone; the sensor is still standing where we installed it"),
    ("Device Reachability", "core · Device intelligence", "separates a sensor that is offline from one that has been removed; re-asked before a trace is rejected"),
    ("SIM Swap", "core · Anti-fraud", "the payee's number has not been hijacked before the money moves; retrieve-date puts the change on the ticket"),
    ("Geofencing Subscriptions", "full · Device intelligence", "entry and exit of the well zone and the tank zone, with dwell. Four per trip; CloudEvents delivered to our webhook"),
    ("Device Swap", "full · Anti-fraud", "the sensor's SIM is still inside the sensor, not in someone's handset"),
    ("Location Retrieval", "full · Device intelligence", "where the truck was when the tank rose without it. Chosen by the investigation, not run on every trip"),
    ("Device Roaming Status", "full · Device intelligence", "a fleet SIM that has left the country entirely"),
]
_rows = []
for i, (api, cat, verb) in enumerate(API_ROWS):
    y = 400 + i * 74
    _rows.append(line(M, y - 32, W - M, y - 32))
    _rows.append(T(M, y, api, 28, "500", INK))
    _rows.append(T(M + 480, y, cat, 20, "400", BLUE))
    _rows.append(block(M + 760, y, verb, 23, "300", MUTE, maxw=W - M - M - 760, lh=1.28))
# ═══════════════════════════════════════════════════════ 09  ships first (core)
slide("09b_deployable", "".join([
    T(M, 148, "API USAGE SYNOPSIS · WHAT SHIPS FIRST", 19, "500", MUTE, spacing=2.6),
    block(M, 246, "Our mentor put it plainly: no operator in the region has all the network APIs live. So Saqqa is built to decide on three, and to say what it could not check.",
          46, "300", INK, maxw=1660),
    stat(M, 500, "3", "APIs",
         "Location Verification, Device Reachability, SIM Swap: the smallest set Saqqa can work on. No geofencing, so "
         "dwell is polled every 15 minutes and carried with that uncertainty, never rounded away.", w=400),
    stat(M + 470, 500, "12", "of 12",
         "trips reach the same verdict as the seven-API build. Every verdict on this profile names the "
         "checks it could not run. scripts/compare_profiles.py fails if that ever stops being true.", w=400),
    img(ASSETS / "profile_core.png", 1000, 372, w=790),
    line(M, 900, W - M, 900),
    block(M, 926, "SIM Swap, the one that stops money, is the most deployed CAMARA API in MENA today (GSMA map, 12 Sep). "
                  "Location Verification is the one that has to land. Four more APIs sharpen the answer: next slide.",
          25, "400", BLUE, maxw=1640, lh=1.3),
    chrome("deployable today"),
]))

slide("09_apis", "".join([
    T(M, 148, "API USAGE SYNOPSIS · THE FULL PROFILE, AND WHAT EACH API ANSWERS", 19, "500", MUTE, spacing=2.6),
    block(M, 246, "The full profile adds four APIs to the core, each answering a question the core cannot.", 46, "300", INK, maxw=1660),
    *_rows,
    line(M, 400 + 7 * 74 - 32, W - M, 400 + 7 * 74 - 32),
    block(M, 926, "All seven through the official Python SDK, every request and response recorded and shown verbatim. "
                  "Two of the four CAMARA categories. Both profiles switch with one control on the dashboard.",
          25, "400", BLUE, maxw=1640, lh=1.3),
    chrome("the apis"),
]))

# ═══════════════════════════════════════════════════════ 10  where the agent thinks
slide("10_agent", "".join([
    T(M, 148, "WHERE THE AI AGENT THINKS", 19, "500", MUTE, spacing=2.6),
    block(M, 236, "The payment gate is a fixed rule. The investigation is the agent.", 52, "300", INK, maxw=1560),
    rect(M, 348, 760, 400, PANEL),
    T(M + 46, 412, "A PARTIAL DELIVERY", 21, "500", MUTE, spacing=2.0),
    block(M + 46, 474, "Driver claimed 10 m³. The tank rose 6. The truck stood there 17 minutes. The contractor has never given us trouble.",
          27, "400", INK, maxw=670, lh=1.34),
    block(M + 46, 618, "Pay for 6, hold the rest, ask the contractor. Do not call it fraud.", 26, "500", GREEN, maxw=670, lh=1.34),
    rect(M + 810, 348, 850, 400, DARK),
    T(M + 856, 412, "AN OPEN CASE", 21, "500", "#6E757E", spacing=2.0),
    block(M + 856, 474, "Tank 7 rose 9.7 m³ between 09:05 and 09:27. The operator's stamps put the truck in the zone from 09:35.",
          27, "400", OFFWHITE, maxw=760, lh=1.34),
    block(M + 856, 570, "Another contractor? A broken sensor? A manipulated trace? A truck nobody registered?", 24, "400", GREYDARK, maxw=760, lh=1.32),
    block(M + 856, 676, "The agent picks which network call to make next, and decides when it has heard enough to stop.",
          25, "500", BLUE, maxw=760, lh=1.32),
    block(M, 840, "A lookup table cannot pick the next question, and it cannot know when to stop asking. "
                  "That is the difference between an agent and an if-statement with a model attached.", 27, "400", INK, maxw=1620, lh=1.36),
    chrome("the agent"),
]))

# ═══════════════════════════════════════════════════════ 11  agent design, as built
slide("11_agentdesign", "".join([
    T(M, 118, "AGENT DESIGN · AS BUILT", 19, "500", MUTE, spacing=2.6),
    block(M, 196, "One graph. The model plans, investigates and explains. Code decides the money.", 46, "300", INK, maxw=1660),
    rect(M, 268, W - 2 * M, 76, PANEL),
    T(M + 40, 316, "intake → plan → verify → sense → score ⇄ investigate → decide → explain → act", 28, "500", INK),
    approw([
        ("plan  ·  model", "which optional checks to buy for this trip, given site type, contractor history and the cost per call. The mandatory set is fixed."),
        ("verify  ·  code", "one CAMARA call per tool through the Nokia SDK; request, response, latency and mode recorded; failures returned as evidence, never raised."),
        ("score  ·  code", "litres, dwell, fill ratio, overlap of the rise with the dwell, pump-time plausibility, capacity accounting, and the contradictions between them."),
        ("investigate  ·  model", "given the contradictions, the next network question or none; prefers checks that could exonerate an honest contractor. Three rounds at most."),
        ("decide  ·  deterministic gate", "RELEASE, HOLD, ESCALATE or BLOCK with the litres to pay, in a fixed order of severity an auditor can re-run without a model."),
        ("explain and act  ·  model, then code", "a two-sentence audit note in English and Arabic; payment webhook, ledger row, F-306-compatible export, supervisor case."),
    ], 424, lh=86, kw=520, ks=26, vs=23),
    chrome("agent design"),
]))

# ═══════════════════════════════════════════════════════ 12  architecture, drawn
def _node(x, y, w, h, title, sub, fill=PANEL, tc=INK, sc=MUTE):
    return "".join([rect(x, y, w, h, fill), T(x + w / 2, y + 44, title, 24, "500", tc, anchor="middle"),
                    block(x + 22, y + 84, sub, 19, "400", sc, maxw=w - 44, lh=1.3, anchor="start")])


slide("12_arch", "".join([
    T(M, 118, "ARCHITECTURE · AS BUILT", 19, "500", MUTE, spacing=2.6),
    T(W - M, 118, "DETERMINISTIC WHERE MONEY MOVES, OPEN EVERYWHERE ELSE", 19, "500", MUTE, anchor="end", spacing=2.6),
    _node(M, 220, 400, 170, "Payer dispatch / ERP", "posts the trip: truck, source, tank, claimed m³. Receives the payment webhook, holds and cases."),
    _node(M + 560, 220, 800, 170, "Saqqa API  ·  FastAPI", "POST /api/run · SSE stream of the agent's steps · POST /webhooks/camara (CloudEvents from the operator) · dashboard"),
    _node(M + 560, 470, 800, 200, "LangGraph agent", "intake → plan → verify → sense → score ⇄ investigate → decide → explain → act.  Gemini Flash-Lite for plan / investigate / explain; the gate is code.", fill=DARK, tc=OFFWHITE, sc=GREYDARK),
    _node(M + 1420, 470, 340, 200, "Store", "SQLite now, Supabase Postgres unchanged: runs, api_calls, events, ledger."),
    _node(M + 250, 750, 560, 170, "Nokia NaC client", "seven CAMARA APIs through the official SDK; live or fixture; every exchange recorded."),
    _node(M + 1100, 750, 560, 170, "Tank sensor store", "level and turbidity, 1-minute samples. Simulated in Phase 1; an LTE-M probe in Phase 3."),
    arrow(M + 400, 305, M + 560, 305), arrow(M + 560, 330, M + 400, 330),
    arrow(M + 960, 390, M + 960, 470), arrow(M + 1360, 570, M + 1420, 570),
    arrow(M + 760, 670, M + 560, 750), arrow(M + 1160, 670, M + 1360, 750),
    T(M + 530, 985, "Nokia Network as Code sandbox  →  operator network: cab SIM, sensor SIM, payee number", 22, "400", BLUE, anchor="middle"),
    T(M + 1380, 985, "no household is ever queried", 22, "400", MUTE, anchor="middle"),
    chrome("architecture"),
]))

# ═══════════════════════════════════════════════════════ 13  the demo, live
slide("13_demo", "".join([
    rect(0, 0, W, H, DARK),
    T(M, 92, "DEMO DESCRIPTION · LIVE ON NOKIA NETWORK AS CODE", 19, "500", "#5A6068", spacing=2.6),
    T(M, 148, "The run that matters: the agent refuses to believe its own sensor.", 44, "300", OFFWHITE),
    T(M, 202, "Tank 7 rose 9.7 m³ between 09:05 and 09:27. The operator's stamps put the truck in the zone from 09:35. The network wins.",
      21, "400", GREYDARK),
    T(M, 232, "Status line top right: Nokia NaC live, Gemini, webhooks on. Four operator webhooks received for this run's own subscriptions.",
      21, "400", "#7C848D"),
    img(ASSETS / "demo_hero_top.png", 240, 268, w=1440),
    chrome("the demo", dark=True),
]), bg=DARK)

# ═══════════════════════════════════════════════════════ 13b  what the agent did
slide("13b_trace", "".join([
    rect(0, 0, W, H, DARK),
    T(M, 92, "WHAT THE AGENT DID WITH IT", 19, "500", "#5A6068", spacing=2.6),
    T(M, 148, "Contradiction found, two questions asked, measurement rejected, nobody accused.", 40, "300", OFFWHITE),
    T(M, 200, "score: “does not fit: tank rose 09:05–09:27 but the truck was in the zone 09:35–10:03”  ·  investigate: reachability re-asked, truck location retrieved  ·  decide: ESCALATE, 0 m³ released",
      20, "400", GREYDARK),
    img(ASSETS / "demo_hero_trace.png", 240, 240, w=1440),
    chrome("the demo", dark=True),
]), bg=DARK)

# ═══════════════════════════════════════════════════════ 13c  twelve trips
TRIPS = [
    ("Honest delivery", "RELEASE", "9.7 m³ verified, 31,040 IQD, same day"),
    ("Short fill, 6 of 10", "HOLD", "pay 6 m³ now, contractor asked"),
    ("Tank was nearly full", "RELEASE", "5.8 m³ was all it could take; flag dispatch, not the contractor"),
    ("Showed up, never opened the valve", "ESCALATE", "22 min dwell, level flat"),
    ("Ghost trip", "ESCALATE", "fleet SIM never in the zone; roaming abroad"),
    ("Substitution, dirty water", "ESCALATE", "level rose, turbidity 41 NTU"),
    ("Sensor offline", "HOLD", "unverified, not fraud; back to paper"),
    ("Sensor SIM moved", "ESCALATE", "device swapped, not at install point"),
    ("Trip inflation", "ESCALATE", "9.8 + 8 m³ off one 10 m³ load"),
    ("Payee SIM-swapped", "BLOCK", "no money to a hijacked number"),
    ("Trace contradicts the network", "ESCALATE", "measurement not believed"),
    ("Manipulated feed", "ESCALATE", "98 cm in one minute"),
]
_t = []
for i, (name, dec, why) in enumerate(TRIPS):
    col, row = i // 6, i % 6
    x = M + col * 830; y = 356 + row * 92
    c = {"RELEASE": GREEN, "HOLD": "#8A6A1F", "ESCALATE": ALERT, "BLOCK": "#7A2E6B"}[dec]
    _t.append(line(x, y - 34, x + 800, y - 34))
    _t.append(T(x, y, name, 26, "500", INK))
    _t.append(T(x + 430, y, dec, 20, "500", c, spacing=1.6))
    _t.append(block(x, y + 34, why, 20, "300", MUTE, maxw=780, lh=1.25))
slide("13c_trips", "".join([
    T(M, 148, "TWELVE SEEDED TRIPS, ALL RUN LIVE", 19, "500", MUTE, spacing=2.6),
    block(M, 246, "Every decision as expected, 115 real CAMARA calls, zero errors.", 48, "300", INK, maxw=1600),
    *_t,
    block(M, 940, "Unverified is never fraud: an offline sensor sends the trip back to the paper process it came from. "
                  "The honest hauler is paid the same day; only the ones stealing are bitten.", 24, "400", BLUE, maxw=1640, lh=1.3),
    chrome("twelve trips"),
]))

# ═══════════════════════════════════════════════════════ 13d  what we verified, what we do not claim
slide("13d_honesty", "".join([
    T(M, 118, "WHAT IS REAL IN THE DEMO", 19, "500", MUTE, spacing=2.6),
    block(M, 196, "The sandbox delivers real webhooks. It does not move trucks.", 48, "300", INK, maxw=1600),
    rect(M, 270, 780, 400, DARK),
    T(M + 40, 330, "VERIFIED, 2 SEPTEMBER", 21, "500", BLUE, spacing=1.8),
    block(M + 40, 386, "Every Geofencing subscription the agent creates produced a CloudEvent at our webhook within eight seconds: "
                       "type area-entered or area-left, the subscription id in the payload, posted from Nokia's platform. "
                       "Four personas: clean, compromised, UNKNOWN, PARTIAL and unreachable.",
          23, "300", OFFWHITE, maxw=700, lh=1.36),
    rect(M + 830, 270, 830, 400, PANEL),
    T(M + 870, 330, "SAID ON SCREEN, EVERY RUN", 21, "500", ALERT, spacing=1.8),
    block(M + 870, 386, "Simulators have fixed positions and fire the subscribed event on creation, so the trip clock is ours and the "
                        "calls that attest to it are real. The tank trace is a pump model with its parameters on screen; hardware is Phase 3. "
                        "The location APIs are not yet commercially live with a MENA operator, so Phase 1 runs on the sandbox and says so.",
          23, "400", INK, maxw=750, lh=1.36),
    chrome("what is real"),
]))

# ═══════════════════════════════════════════════════════ 14  why not GPS
slide("14_gps", "".join([
    T(M, 148, "THE OBVIOUS OBJECTION", 19, "500", MUTE, spacing=2.6),
    block(M, 236, "“Why not just bolt a GPS tracker on the truck?”", 58, "300", INK, maxw=1500),
    line(M, 330, W - M, 330),
    T(M, 424, "BECAUSE RESOLUTION IS THE WRONG AXIS.", 26, "500", ALERT, spacing=1.6),
    block(M, 500, "A tracker reports its own position. Anything that reports its own position can be made to lie, and a "
                  "tamper-evident seal stops a screwdriver, not a spoofed signal.", 34, "300", INK, maxw=1520, lh=1.44),
    rect(M, 660, W - 2 * M, 140, DARK),
    block(M + 50, 726, "2,000 metres you cannot forge beats 5 metres you report yourself, when you are the party being audited.",
          32, "400", OFFWHITE, maxw=1500),
    block(M, 880, "Cell-level location is coarse, roughly two kilometres. It is computed by infrastructure the contractor does not own "
                  "and cannot reach. And the hardware sits on the payer's tank, so the truck carries nothing to disable, swap or drive around with.",
          26, "400", MUTE, maxw=1620, lh=1.36),
    chrome("forgeability"),
]))

# ═══════════════════════════════════════════════════════ 15  alternatives
COMP = [
    ("", "PROVES LITRES", "PROVES WHOSE TRUCK", "CONTRACTOR CAN FAKE IT", "COST PER SITE"),
    ("Paper log (F-306)", "claimed only", "signature", "yes, trivially", "near zero"),
    ("Fleet GPS tracker", "no", "yes, to metres", "yes: the device reports its own position", "per truck, ongoing"),
    ("Biometric / RFID gate", "no", "at a fixed gate only", "no, but tanks are not gated", "per gate"),
    ("Saqqa", "yes, measured", "yes, at zone scale", "no: the operator computes it", "one sensor, payer-owned"),
]
_c = []
for r, cells in enumerate(COMP):
    y = 356 + r * 108
    if r == 0:
        for c, cell in enumerate(cells):
            _c.append(T(M + [0, 470, 780, 1140, 1520][c], y, cell, 17, "500", MUTE, spacing=1.6))
    else:
        _c.append(line(M, y - 44, W - M, y - 44))
        strong = (r == len(COMP) - 1)
        for c, cell in enumerate(cells):
            _c.append(block(M + [0, 470, 780, 1140, 1520][c], y, cell, 23, "500" if (strong or c == 0) else "300",
                            INK if strong else (INK if c == 0 else MUTE), maxw=[440, 290, 340, 360, 260][c], lh=1.28))
slide("15_versus", "".join([
    T(M, 148, "AGAINST THE ALTERNATIVES", 19, "500", MUTE, spacing=2.6),
    block(M, 246, "Nothing else answers both halves at once.", 52, "300", INK, maxw=1500),
    *_c,
    line(M, 852, W - M, 852),
    block(M, 906, "Only the last row answers both questions at once, and it is the only row where the party being paid does not produce the evidence.",
          27, "400", BLUE, maxw=1620, lh=1.32),
    chrome("alternatives"),
]))

# ═══════════════════════════════════════════════════════ 16  tooling, as built
slide("16_tooling", "".join([
    T(M, 148, "BUILT FROM THE RESOURCE AND TOOLING GUIDE", 19, "500", MUTE, spacing=2.6),
    block(M, 246, "Every component of the prototype, and what it does.", 52, "300", INK, maxw=1500),
    approw([
        ("LangGraph", "the agent: one stateful graph, conditional edges for the investigate loop, the CAMARA calls as its tools"),
        ("Gemini 3.5 Flash-Lite · Flash · Groq Llama 3.3 70B", "planning, investigation choice, audit notes. In that fallback order, per call; Gemini 2.5 Flash is no longer offered to new accounts"),
        ("Nokia NaC Python SDK 10.0", "the seven CAMARA APIs, live against the sandbox; responses normalised and recorded verbatim"),
        ("FastAPI · SQLite → Supabase", "REST, Server-Sent Events for the live trace, the CloudEvents webhook receiver; runs, calls, events and the ledger"),
        ("Leaflet · the dashboard", "operator geofences on a map, the tank trace with the dwell window, the reasoning as it streams, every call, the decision, F-306 export"),
        ("Docker · Render · cloudflared", "one-command run, one-click deploy, a public sink for the operator's webhooks during development"),
    ], 400, lh=90, kw=760, ks=27, vs=24),
    chrome("tooling"),
]))

# ═══════════════════════════════════════════════════════ 17  business model
slide("17_money", "".join([
    T(M, 118, "BUSINESS IMPACT · MODEL AND MONETIZATION", 19, "500", MUTE, spacing=2.6),
    block(M, 196, "The payer already exists, and already pays against paper.", 50, "300", INK, maxw=1500),
    line(M, 268, W - M, 268),
    T(M, 322, "WHO THE BUYER IS", 19, "500", MUTE, spacing=2.2),
    stat(M, 420, "75%", "", "of Jordan's tanker sales serve businesses: hotels, factories, sites. They pay per cubic metre and get short-filled.", w=360, big_size=74),
    stat(M + 440, 420, "21%", "", "funded: the humanitarian buyer whose donors demand third-party proof of every dollar.", w=360, big_size=74),
    stat(M + 880, 420, "$30–70", "", "a delivery today, paid against a signature.", w=360, big_size=74),
    stat(M + 1320, 420, "New", "", "API revenue for operators. UN agencies and utilities are a customer they do not have today.", w=360, big_size=74),
    line(M, 640, W - M, 640),
    T(M, 694, "HOW WE CHARGE", 19, "500", MUTE, spacing=2.2),
    approw([
        ("Per verified delivery", "cents against a $30–70 trip; verification costs about 13 cents. The price scales with value delivered rather than with seats."),
        ("Platform fee per instrumented tank", "a flat monthly fee per tank on the payer's own site, which is where the sensor lives. One sensor covers every contractor who delivers to it."),
        ("Operator revenue share", "the operator bills the CAMARA calls and keeps a share. That is what makes us worth onboarding rather than merely tolerating."),
    ], 756, lh=72, kw=560, ks=27, vs=24),
    chrome("business model"),
]))

# ═══════════════════════════════════════════════════════ 18  how it scales
slide("18_scale", "".join([
    rect(0, 0, W, H, DARK),
    T(M, 118, "BUSINESS IMPACT · HOW IT SCALES", 19, "500", "#5A6068", spacing=2.6),
    block(M, 210, "One sensor per tank, not per contractor and not per delivery.", 50, "300", OFFWHITE, maxw=1620),
    line(M, 288, W - M, 288, RULEDARK),
    T(M, 342, "WHY THE UNIT ECONOMICS IMPROVE WITH VOLUME", 19, "500", "#6E757E", spacing=2.2),
    block(M, 400, "The sensor is fixed to the payer's tank, so it is bought once and then covers every contractor who ever delivers "
                  "to that tank. Cost per verified delivery falls as the tank gets busier. A camp taking two loads a day amortises "
                  "the same hardware twenty times faster than one taking two a week.", 27, "300", GREYDARK, maxw=1620, lh=1.36),
    T(M, 566, "WHY IT SPREADS INSTEAD OF STALLING", 19, "500", "#6E757E", spacing=2.2),
    approw([
        ("Nothing to install on the fleet", "the contractor's only obligation is a SIM in the cab. No hardware to buy, fit, maintain or argue about, which is what kills tracker rollouts at procurement."),
        ("The operator is the channel", "once one operator exposes these APIs in a market, every payer in that market is reachable with no new integration from us. We sell through the operator, not around it."),
        ("Same engine, other cargo", "trucked diesel and LPG ask the same question with a bigger number: a 20,000-litre load is worth about $15,000, generator tanks already carry level sensors, and the same 13 cents of calls verifies it. Food aid and cold chain follow."),
    ], 632, lh=108, kw=560, ks=27, vs=24, dark=True),
    line(M, 940, W - M, 940, RULEDARK),
    block(M, 984, "Sequenced on GSMA's deployment database, not on our roadmap: Iraq first, then Jordan as the commercial market, then the Gulf.",
          24, "400", BLUE, maxw=1620),
    chrome("how it scales", dark=True),
]), bg=DARK)

# ═══════════════════════════════════════════════════════ 19  who it protects
slide("19_hauler", "".join([
    rect(0, 0, W, H, DARK),
    T(M, 148, "COMMERCIAL VALUE · WHO THIS IS FOR", 19, "500", "#5A6068", spacing=2.6),
    block(M, 300, "Saqqa is not surveillance of haulers.", 62, "300", "#6E757E", maxw=1600),
    block(M, 420, "It is same-day settlement for the honest ones.", 62, "300", OFFWHITE, maxw=1600),
    line(M, 530, M + 210, 530, "#3A4048", 3),
    block(M, 612, "Today an honest driver is paid on a weekly paper cycle he cannot influence, and when a tank comes up short "
                  "he has no way to prove it was full when he left.", 31, "300", GREYDARK, maxw=1520),
    block(M, 790, "Under Saqqa he is paid the same day, and he holds a record the operator stands behind that says he delivered. "
                  "It only bites the ones who were stealing.", 31, "300", OFFWHITE, maxw=1520),
    chrome("the beneficiary", dark=True),
]), bg=DARK)

# ═══════════════════════════════════════════════════════ 19b  what it takes to deploy
slide("19b_feasible", "".join([
    T(M, 118, "COMMERCIAL VIABILITY · WHAT IT TAKES TO DEPLOY", 19, "500", MUTE, spacing=2.6),
    block(M, 196, "Nothing new on the truck, nothing new in the law.", 50, "300", INK, maxw=1560),
    line(M, 268, W - M, 268),
    approw([
        ("On the truck: nothing", "the SIM already in the cab is the tracker. No hardware to buy, fit, maintain or argue about at procurement."),
        ("On the tank: one sensor", "a fixed level sensor with its own SIM on the buyer's site, bought once, covering every contractor who ever delivers there."),
        ("In software: one agent, three APIs", "runs on Nokia Network as Code today; every verdict is reached on the three-API core profile. A pilot needs one buyer, one hauler and one operator API key."),
        ("In paperwork: nothing changes", "the F-306 delivery form stays the legal record; Saqqa fills it from the evidence instead of from a signature."),
        ("In money: 13.6 cents a trip", "measured, against a $30 delivery: under half a percent, paid per verified trip, with the operator earning per call."),
    ], 350, lh=104, kw=620, ks=27, vs=24),
    line(M, 876, W - M, 876),
    chrome("what it takes"),
]))

# ═══════════════════════════════════════════════════════ 20  team
slide("20_team", "".join([
    T(M, 148, "TEAM STARX", 19, "500", MUTE, spacing=2.6),
    block(M, 246, "Four engineering students, Indian Institute of Technology Delhi, Abu Dhabi.", 48, "300", INK, maxw=1620),
    line(M, 330, W - M, 330),
    *[x for i, (name, role, disc, bio) in enumerate([
        ("James Joshua Koshy", "Network integration and agent", "Computer Science",
         "Works out what the network can actually tell us, wires the CAMARA APIs into the agent, and ran the live verification."),
        ("Evan Johan Tobias", "Agent and backend", "Computer Science",
         "Builds the agent, the rule that decides what gets paid, and the records behind it."),
        ("Divyam Thakur", "Research and sourcing", "Computer Science",
         "Chases down every number in this deck and where it came from, including the ones that argue against us."),
        ("Kirti Roshankumar Thakar", "Design and pitch", "Chemical Engineering",
         "Designs the deck and decides how the pitch gets told."),
    ]) for x in [
        line(M, 400 + i * 156 - 44, W - M, 400 + i * 156 - 44),
        T(M, 400 + i * 156, name, 32, "500", INK),
        T(M, 400 + i * 156 + 42, disc, 21, "400", MUTE),
        T(M + 620, 400 + i * 156, role.upper(), 21, "500", BLUE, spacing=1.8),
        block(M + 620, 400 + i * 156 + 44, bio, 25, "300", MUTE, maxw=W - M - M - 620, lh=1.32),
    ]],
    chrome("team"),
]))


def main():
    from playwright.sync_api import sync_playwright
    from PIL import Image
    from pptx import Presentation
    from pptx.util import Emu

    names = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page(viewport={"width": W, "height": H})
        for i, (name, s) in enumerate(SLIDES):
            s = s.replace("__PAGENO__", f"{i + 1:02d}")
            (SVG / f"{name}.svg").write_text(s, encoding="utf-8")
            page.set_content(f'<html><body style="margin:0;background:#000">{s}</body></html>')
            page.wait_for_timeout(120)
            out = PNG / f"{name}.png"
            page.screenshot(path=str(out), clip={"x": 0, "y": 0, "width": W, "height": H})
            names.append(out)
            print("rendered", name)
        b.close()

    imgs = [Image.open(n).convert("RGB") for n in names]
    pdf = OUT / "Saqqa_Prototype_Deck.pdf"
    try:
        imgs[0].save(pdf, save_all=True, append_images=imgs[1:], resolution=144.0, quality=92)
    except PermissionError:
        pdf = OUT / "Saqqa_Prototype_Deck_v2.pdf"
        imgs[0].save(pdf, save_all=True, append_images=imgs[1:], resolution=144.0, quality=92)
    print("PDF  ->", pdf, f"({pdf.stat().st_size / 1e6:.1f} MB)")

    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(12192000), Emu(6858000)
    blank = prs.slide_layouts[6]
    for n in names:
        sl = prs.slides.add_slide(blank)
        sl.shapes.add_picture(str(n), 0, 0, prs.slide_width, prs.slide_height)
    pptx = OUT / "Saqqa_Prototype_Deck.pptx"
    try:
        prs.save(str(pptx))
    except PermissionError:  # the file is open in PowerPoint
        pptx = OUT / "Saqqa_Prototype_Deck_v2.pptx"
        prs.save(str(pptx))
    print("PPTX ->", pptx, f"({pptx.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
