/* Saqqa payer dashboard. Talks to the FastAPI server; streams the agent's steps over SSE. */
const $ = (s) => document.querySelector(s);
let STATUS = null, SCEN = [], current = null, lastRun = null, PROFILE = null;
let map, truckMarker, zoneLayers = {}, routeLine, animTimer = null;

/* One run at a time. `active` is the only source of truth for what may render. */
let active = null;   // { id, es, seq }
let runSeq = 0;

const RECORD = new URLSearchParams(location.search).has("record");
function setCaption(text) {
  let c = document.getElementById("caption");
  if (!c) { c = document.createElement("div"); c.id = "caption"; document.body.appendChild(c); }
  c.textContent = text || ""; c.style.opacity = text ? "1" : "0";
}
window.setCaption = setCaption;

// ---------------------------------------------------------------- boot
async function boot() {
  STATUS = await (await fetch("/api/status")).json();
  if (RECORD) { document.body.classList.add("record"); }
  if (!new URLSearchParams(location.search).has("app")) document.body.classList.add("landing");
  SCEN = await (await fetch("/api/scenarios")).json();
  renderProfiles(); renderScenarios(); initTabs(); initMap(); refreshRuns();
  $("#run").onclick = () => current && runScenario(current.id);
  // on a phone the trip list stacks above the case file, so land on the claim rather than the list
  const go = (id) => {
    select(id, true);
    if (matchMedia("(max-width: 1080px)").matches) document.querySelector("article")?.scrollIntoView({ behavior: "smooth", block: "start" });
    else window.scrollTo({ top: 0, behavior: "smooth" });
  };
  $("#cta_run")?.addEventListener("click", () => go("honest"));
  $("#cta_hero")?.addEventListener("click", () => go("sensor_contradicts_network"));
  // the wordmark is the way back to the landing; a run in progress keeps going underneath
  $("#home")?.addEventListener("click", (e) => {
    e.preventDefault(); document.body.classList.add("landing"); $("#hero")?.classList.remove("done"); window.scrollTo({ top: 0 });
  });
  $("#cta_open")?.addEventListener("click", () => {
    document.body.classList.remove("landing"); $("#hero")?.classList.add("done");
    window.scrollTo({ top: 0 }); if (map) setTimeout(() => map.invalidateSize(), 60);
  });
  $("#f306").onclick = () => lastRun && window.open(`/api/export/f306/${lastRun}`, "_blank");
  select(SCEN[0].id, false);
}

function renderBadges() {
  const el = $("#status"); if (!el) return;
  const live = STATUS.mode === "live";
  const model = STATUS.llm === "stub" ? "no model" : STATUS.llm.replace(/^gemini \((.*)\)$/, "$1");
  const parts = [
    live ? "Live on Nokia Network as Code" : "Fixtures mirroring the Nokia sandbox",
    "LangGraph with " + model,
    STATUS.public_base_url ? "network events by webhook" : "network events by polling",
  ];
  el.className = "status " + STATUS.mode;
  el.innerHTML = "<i></i>";
  el.appendChild(document.createTextNode(parts.join(" · ")));
}

/* Which CAMARA APIs the operator has live. The mentor's point stands: almost nobody has all
   seven. The agent must still decide on the set that is actually deployed, and say what it
   could not check. */
function renderProfiles() {
  const box = $("#profile"); if (!box) return;
  box.innerHTML = "";
  PROFILE = PROFILE || STATUS.profile || "full";
  for (const [k, p] of Object.entries(STATUS.profiles || {})) {
    const b = document.createElement("button");
    b.type = "button";
    b.textContent = `${k} · ${p.apis.length} API${p.apis.length === 1 ? "" : "s"}`;
    b.setAttribute("aria-pressed", String(k === PROFILE));
    b.title = [p.blurb, "", ...p.apis].join("\n");
    b.setAttribute("aria-label", `${p.label}. ${p.blurb}`);
    b.onclick = () => { if (k === PROFILE) return; PROFILE = k; abortRun(); renderProfiles(); resetPanels(); if (current) drawTimelineMarkers(current.network); };
    box.appendChild(b);
  }
  renderApiStrip();
  const p = (STATUS.profiles || {})[PROFILE];
  if (p) $("#cost").textContent = `${p.apis.length} CAMARA APIs · ` +
    (PROFILE === "core" ? "dwell polled at 15-minute cadence, carried with its uncertainty"
                        : "dwell stamped by operator geofence events");
  renderBadges();
}

/* All seven CAMARA APIs, with the ones this profile cannot buy struck through. The switch used
   to be two buttons and a blurb; a judge could not see what changed. Now the loss is on screen. */
function renderApiStrip() {
  const el = $("#apistrip"); if (!el) return;
  const all = ((STATUS.profiles || {}).full || {}).apis || [];
  const have = new Set(((STATUS.profiles || {})[PROFILE] || {}).apis || []);
  el.innerHTML = "";
  for (const name of all) {
    const sp = document.createElement("span");
    sp.className = have.has(name) ? "on" : "off";
    sp.textContent = name;
    sp.title = have.has(name) ? "available on this profile" : "not available on this profile";
    if ((STATUS.live_in_mena || []).includes(name)) {
      const i = document.createElement("i"); i.textContent = "live in MENA";
      i.title = "commercially deployed with at least one MENA operator (GSMA Open Gateway map, dataset 12 Sep 2026)";
      sp.appendChild(i);
    }
    el.appendChild(sp);
  }
}

/* Evidence lives behind tabs. Everything is still one click away, but the page opens on the
   answer instead of on four sections of proof shouting at once. */
function initTabs() {
  const tabs = [...document.querySelectorAll(".tabs [role=tab]")];
  if (!tabs.length) return;
  tabs.forEach((t) => (t.onclick = () => showTab(t.dataset.tab)));
  showTab("network");   // the map is in plain sight; the agent's log is one click away
}

function showTab(name) {
  document.querySelectorAll(".tabs [role=tab]").forEach((t) =>
    t.setAttribute("aria-selected", String(t.dataset.tab === name)));
  document.querySelectorAll(".tabpanel").forEach((p) => (p.hidden = p.dataset.panel !== name));
  // Leaflet measures its container on creation; a map built inside a hidden panel has no size
  // until the panel is shown, so it has to be told to re-measure.
  if (name === "network" && map) setTimeout(() => map.invalidateSize(), 60);
}
window.showTab = showTab;

/* A judge should not have to guess where to begin. Three trips carry a signpost; the rest are
   there to be explored. After each signposted run, the verdict suggests the next one. */
const TOUR = {
  honest: "start here",
  sensor_contradicts_network: "the one that matters",
  payee_swapped: "the one that stops money",
};
const NEXT = {
  honest: { id: "sensor_contradicts_network", text: "Now the run that matters: the tank rises before the truck arrives, and the agent refuses to believe its own sensor. Switch to full · 7 APIs first to see the operator's geofence stamp the exact minute." },
  sensor_contradicts_network: { id: "payee_swapped", text: "Now the one that stops money: a perfect delivery, but the payee's number changed SIM. The verdict is the same on three APIs or seven." },
  payee_swapped: { id: "sensor_offline", text: "Then try a sensor that is simply unreachable: unverified is never treated as fraud." },
};

function renderScenarios() {
  const box = $("#scenarios"); box.innerHTML = "";
  for (const s of SCEN) {
    const d = document.createElement("button");
    d.type = "button"; d.className = "scen"; d.dataset.id = s.id;
    d.setAttribute("aria-current", "false");
    const tour = TOUR[s.id];
    d.innerHTML = `<span class="t">${s.label || s.title}</span><span class="tag ${s.expect}">${s.expect}</span>` +
                  (tour ? `<span class="tour">${tour}</span>` : "");
    d.setAttribute("aria-label", `${s.title}. Expected decision ${s.expect}. Run this verification.`);
    d.onclick = () => select(s.id, true);
    box.appendChild(d);
  }
}

function select(id, autorun) {
  abortRun();
  current = SCEN.find((s) => s.id === id);
  document.querySelectorAll(".scen").forEach((e) => e.setAttribute("aria-current", String(e.dataset.id === id)));
  const t = current.trip;
  $("#storytext").innerHTML = `<b>${current.title}</b> ${current.story}<span class="meta">trip #${t.trip_id} · ${t.truck_id} · claims ${t.claimed_m3} m³ into tank ${t.tank_id} · ${t.contractor} · ${t.site_type} site</span>`;
  $("#run").disabled = false;
  resetPanels();
  drawTimelineMarkers(current.network);
  if (autorun) runScenario(id);
}

function resetPanels() {
  $("#trace").innerHTML = ""; $("#calls").innerHTML = ""; $("#callcount").textContent = "";
  document.querySelectorAll("#graph span").forEach((n) => n.classList.remove("active", "done"));
  $("#decision").className = "card";
  $("#decision").innerHTML = `<h2>Verdict</h2><div class="waiting">Awaiting verification</div><div class="amount">press Run verification: about ten network calls, then a decision on what to pay</div>`;
  $("#ledger").textContent = "The ledger entry and the audit note appear here after a run.";
  $("#auditnote").innerHTML = "";
  $("#f306").disabled = true; $("#clock").textContent = ""; $("#webhooks").innerHTML = "";
  ["k_claim", "k_meas", "k_dwell", "k_turb"].forEach((k) => ($("#" + k).textContent = "—"));
  $("#kpi_meas").className = "kpi"; $("#kpi_meas .flag")?.remove();
  drawChart(null, current ? current.network : null, null);
  if (truckMarker) { truckMarker.setLatLng(ROUTE[0]); truckMarker.getElement()?.querySelector(".truck")?.classList.remove("moving"); }
  clearInterval(animTimer);
}

// ---------------------------------------------------------------- map
const ROUTE = [[30.4620, 47.7530], [30.4520, 47.7450], [30.4330, 47.7300], [30.4120, 47.7180], [30.3890, 47.7080]];
const FARM = [30.4010, 47.8020];
function initMap() {
  map = L.map("map", { zoomControl: false, attributionControl: false, keyboard: false }).setView([30.425, 47.745], 12);
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 18, className: "light-tiles" }).addTo(map);
  const colors = { S1: "#2A5580", K1: "#2C6A4E", F1: "#A8401F" };
  for (const [id, z] of Object.entries(STATUS.zones)) {
    zoneLayers[id] = L.circle([z.lat, z.lon], { radius: z.radius_m, color: colors[id], weight: 1, fillOpacity: 0.06, interactive: false }).addTo(map);
    // offset the label from the zone centre so the fleet-SIM marker never covers it
    L.marker([z.lat, z.lon], { interactive: false, keyboard: false, icon: L.divIcon({ className: "", html: `<div style="color:${colors[id]};font:700 11px 'Libre Franklin',sans-serif;letter-spacing:.04em;text-shadow:0 0 5px #FBFAF8">${id}</div>`, iconSize: [22, 13], iconAnchor: [-10, 20] }) }).addTo(map);
  }
  routeLine = L.polyline(ROUTE, { color: "#93938A", weight: 1.2, dashArray: "2 5", interactive: false }).addTo(map);
  truckMarker = L.marker(ROUTE[0], { interactive: false, keyboard: false, icon: L.divIcon({ className: "", html: `<div class="truck"></div>`, iconSize: [12, 12], iconAnchor: [6, 6] }) }).addTo(map);
}

function animateTruck(network, farm) {
  // 08:30 → 10:30 in ~9 s; S1 dwell, drive, K1 dwell (or park at the farm inside K1 for the substitution case)
  clearInterval(animTimer);
  const el = truckMarker.getElement()?.querySelector(".truck");
  el?.classList.add("moving");
  const s1 = network.S1, k1 = network.K1;
  const tIn = s1 ? minutes(s1.entered) : 5, tOut = s1 ? minutes(s1.left) : 20, kIn = k1 ? minutes(k1.entered) : 999;
  let t = 0;
  animTimer = setInterval(() => {
    t += 0.7;
    if (t > 120) { clearInterval(animTimer); el?.classList.remove("moving"); return; }
    $("#clock").textContent = "trip " + hhmm(t) + (k1 && t >= kIn && t <= minutes(k1.left) ? " · in K1" : s1 && t >= tIn && t <= tOut ? " · at S1" : "");
    let p;
    if (!k1) { p = t < tOut ? 0 : Math.min(0.55, (t - tOut) / 60); }       // never reaches the tank zone
    else if (t < tOut) p = 0; else if (t < kIn) p = (t - tOut) / (kIn - tOut); else p = 1;
    const pos = farm && k1 && t >= kIn + 4 ? FARM : pointAlong(p);
    truckMarker.setLatLng(pos);
  }, 55);
}
function pointAlong(p) {
  const segs = ROUTE.length - 1, x = Math.max(0, Math.min(1, p)) * segs, i = Math.min(segs - 1, Math.floor(x)), f = x - i;
  return [ROUTE[i][0] + (ROUTE[i + 1][0] - ROUTE[i][0]) * f, ROUTE[i][1] + (ROUTE[i + 1][1] - ROUTE[i][1]) * f];
}
const minutes = (s) => { const [h, m] = s.split(":").map(Number); return (h - 8) * 60 + m - 30; };
const hhmm = (t) => { const m = 30 + Math.floor(t); return `${String(8 + Math.floor(m / 60)).padStart(2, "0")}:${String(m % 60).padStart(2, "0")}`; };

// ---------------------------------------------------------------- chart
const MONO = "Libre Franklin, sans-serif";
/* The two clocks. This is the product: the operator says when the truck was there, the tank says
   when it filled, and those two windows have to overlap. Everything else on the page is support.
   Drawn as two stacked lanes on one shared time axis so the comparison is the shape, not a legend. */
const C = { net: "#2A5580", tank: "#8A6A1E", accent: "#A8401F", ink: "#15150F",
            muted: "#67675D", faint: "#6E6E66", rule: "#DEDBD3", wash: "#F4F2ED" };
const W = 1000, H = 252, PAD = 6;
const x = (t) => PAD + (t / 120) * (W - PAD * 2);
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;");

function band(a, b, y, h, fill, op) {
  return `<rect x="${x(a)}" y="${y}" width="${Math.max(2, x(b) - x(a))}" height="${h}" fill="${fill}" opacity="${op}"/>`;
}
function tx(xx, yy, t, o = {}) {
  const a = o.anchor || "start", f = o.size || 12, w = o.weight || 400, fam = o.mono === false ? "Libre Franklin, sans-serif" : MONO;
  return `<text x="${xx}" y="${yy}" fill="${o.fill || C.muted}" font-size="${f}" font-weight="${w}" font-family="${fam}" text-anchor="${a}">${esc(t)}</text>`;
}

function drawTimelineMarkers(network) { drawChart(null, network, null); }

const POLL_MIN = 15;
function observedWindow(w) {
  if (!w) return null;
  const a = minutes(w.entered), b = minutes(w.left);
  const lo = Math.floor(a / POLL_MIN) * POLL_MIN, hi0 = Math.ceil(b / POLL_MIN) * POLL_MIN;
  const hi = hi0 - lo < POLL_MIN ? lo + POLL_MIN : hi0;
  return { entered: hhmm(lo), left: hhmm(hi), lo, hi };
}

function drawChart(samples, network, signals, cursor) {
  const svg = $("#chart");
  if (cursor != null && samples) samples = samples.filter((p) => p.t <= cursor);
  const NET_Y = 30, NET_H = 26, TANK_TOP = 94, TANK_BOT = 196, AXIS = 216, VERDICT = 243;
  const yL = (cm) => TANK_BOT - Math.max(0, Math.min(200, cm)) / 200 * (TANK_BOT - TANK_TOP);
  const polled = PROFILE === "core";
  const k1raw = network && network.K1, s1raw = network && network.S1;
  const k1 = polled ? observedWindow(k1raw) : k1raw, s1 = polled ? observedWindow(s1raw) : s1raw;
  let s = polled ? `<defs><pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
      <line x1="0" y1="0" x2="0" y2="6" stroke="${C.net}" stroke-width="1.2" opacity=".55"/></pattern></defs>` : "";

  // shared time axis
  for (let i = 0; i <= 8; i++) {
    const t = i * 15;
    s += `<line x1="${x(t)}" y1="${NET_Y - 12}" x2="${x(t)}" y2="${AXIS - 12}" stroke="#C6C2B7" stroke-width="1"/>`;
    if (i % 2 === 0) s += tx(x(t), AXIS, hhmm(t), { anchor: i === 0 ? "start" : i === 8 ? "end" : "middle", size: 11, fill: C.faint });
  }

  // ---- lane 1: what the operator's network says
  s += tx(PAD, NET_Y - 20, "Truck at the tank — from the operator's network", { size: 13, weight: 600, fill: C.net });
  s += `<line x1="${PAD}" y1="${NET_Y + NET_H}" x2="${W - PAD}" y2="${NET_Y + NET_H}" stroke="#C6C2B7"/>`;
  if (s1) {
    s += band(minutes(s1.entered), minutes(s1.left), NET_Y, NET_H, C.net, 0.16);
    s += tx(x(minutes(s1.entered)) + 7, NET_Y + 19, `at the well  ${s1.entered}–${s1.left}${polled ? "  (polled)" : ""}`, { size: 11.5, fill: C.net, weight: 500 });
  } else {
    s += tx(PAD + 4, NET_Y + 19, "no visit to the contracted source", { size: 11.5, fill: C.accent, weight: 500 });
  }
  if (k1 && polled) {
    // the poll grid, hatched: the truck was inside somewhere within these edges, not at them
    const a = minutes(k1raw.entered), b = minutes(k1raw.left);
    s += band(k1.lo, a, NET_Y, NET_H, "url(#hatch)", 1);
    s += band(a, b, NET_Y, NET_H, C.net, 0.34);
    s += band(b, k1.hi, NET_Y, NET_H, "url(#hatch)", 1);
    s += tx(x(k1.lo) + 7, NET_Y + 18, `at the tank  ${k1.entered}–${k1.left}  (polled, ±${POLL_MIN} min)`, { size: 12.5, fill: C.net, weight: 700 });
  } else if (k1) {
    s += band(minutes(k1.entered), minutes(k1.left), NET_Y, NET_H, C.net, 0.34);
    s += tx(x(minutes(k1.entered)) + 7, NET_Y + 18, `at the tank  ${k1.entered}–${k1.left}`, { size: 12.5, fill: C.net, weight: 700 });
  } else {
    s += `<rect x="${x(70)}" y="${NET_Y}" width="${x(105) - x(70)}" height="${NET_H}" fill="none" stroke="${C.accent}" stroke-width="1.5" stroke-dasharray="4 4"/>`;
    s += tx(x(70) + 8, NET_Y + 18, "never at the tank", { size: 12.5, fill: C.accent, weight: 700 });
  }

  // ---- lane 2: what the buyer's tank says
  s += tx(PAD, TANK_TOP - 16, "Tank filled — from the tank's own level sensor", { size: 13, weight: 600, fill: C.tank });
  s += `<line x1="${PAD}" y1="${TANK_BOT}" x2="${W - PAD}" y2="${TANK_BOT}" stroke="#C6C2B7"/>`;
  const rw = signals && signals.rise_window;

  if (samples && samples.length) {
    const pts = samples.map((p) => `${x(p.t)},${yL(p.level_cm)}`).join(" ");
    s += `<polygon fill="${C.tank}" opacity=".10" points="${x(samples[0].t)},${TANK_BOT} ${pts} ${x(samples[samples.length - 1].t)},${TANK_BOT}"/>`;
    s += `<polyline class="draw" fill="none" stroke="${C.tank}" stroke-width="2.5" stroke-linejoin="round" points="${pts}"/>`;
    if (rw) {
      const mid = (TANK_TOP + TANK_BOT) / 2;
      s += band(minutes(rw[0]), minutes(rw[1]), mid - 14, 28, C.tank, 0.92);
      const wide = x(minutes(rw[1])) - x(minutes(rw[0])) > 250;   // label inside a wide bar, beside a narrow one
      s += tx(x(minutes(wide ? rw[0] : rw[1])) + 8, mid + 5, `tank filled  ${rw[0]}–${rw[1]}  +${signals.delta_m3} m³`,
              { size: 12.5, fill: wide ? "#FBFAF7" : C.tank, weight: 700 });
    } else if (signals) {
      s += tx(PAD + 4, (TANK_TOP + TANK_BOT) / 2 + 4, "the level never moved", { size: 12.5, fill: C.accent, weight: 700 });
    }
  } else if (cursor != null) {
    // the clock has not reached the first sample yet
  } else if (samples) {
    s += tx(W / 2, (TANK_TOP + TANK_BOT) / 2, "no samples · the tank sensor was unreachable", { anchor: "middle", size: 13, fill: C.accent, weight: 500 });
  } else {
    s += tx(PAD + 2, (TANK_TOP + TANK_BOT) / 2 + 4, "the tank's fill bar appears here after a run, to compare with the truck's bar above", { size: 12.5, fill: C.faint });
  }
  if (cursor != null) {
    s += `<line x1="${x(cursor)}" y1="${NET_Y - 12}" x2="${x(cursor)}" y2="${AXIS - 12}" stroke="${C.accent}" stroke-width="1.5"/>`;
    s += tx(x(cursor) + 6, NET_Y - 14, hhmm(cursor), { size: 11, fill: C.accent, weight: 600 });
  }

  // ---- the comparison, stated in words: this is the sentence the whole product exists to say
  if (signals && rw && k1) {
    const ov = signals.rise_dwell_overlap_min;
    const kIn = polled ? k1.lo : minutes(k1.entered), kOut = polled ? k1.hi : minutes(k1.left);
    const a = Math.max(minutes(rw[0]), kIn), b = Math.min(minutes(rw[1]), kOut);
    if (ov > 0) {
      s += band(a, b, NET_Y, TANK_BOT - NET_Y, C.tank, 0.07);
      s += `<line x1="${x(a)}" y1="${NET_Y}" x2="${x(a)}" y2="${TANK_BOT}" stroke="${C.tank}" stroke-width="1.5"/>`;
      s += `<line x1="${x(b)}" y1="${NET_Y}" x2="${x(b)}" y2="${TANK_BOT}" stroke="${C.tank}" stroke-width="1.5"/>`;
      s += tx(PAD, VERDICT, `The tank filled while the truck was there: the two bars overlap for ${ov} minutes.`,
              { size: 15.5, fill: C.ink, weight: 700, mono: false });
    } else {
      const gapA = Math.min(minutes(rw[1]), kIn), gapB = Math.max(minutes(rw[1]), kIn);
      s += band(gapA, gapB, NET_Y, TANK_BOT - NET_Y, C.accent, 0.1);
      s += `<line x1="${x(gapA)}" y1="${NET_Y}" x2="${x(gapA)}" y2="${TANK_BOT}" stroke="${C.accent}" stroke-width="1.5" stroke-dasharray="3 3"/>`;
      s += `<line x1="${x(gapB)}" y1="${NET_Y}" x2="${x(gapB)}" y2="${TANK_BOT}" stroke="${C.accent}" stroke-width="1.5" stroke-dasharray="3 3"/>`;
      s += tx(PAD, VERDICT, "The tank filled before the truck arrived: the two bars do not overlap at all.",
              { size: 15.5, fill: C.accent, weight: 700, mono: false });
    }
  } else if (signals && !rw && k1) {
    s += tx(PAD, VERDICT, "The truck was in the zone and the level never moved.", { size: 14.5, fill: C.accent, weight: 600, mono: false });
  } else if (signals && rw && !k1) {
    s += tx(PAD, VERDICT, "The tank rose with no contracted truck in the zone.", { size: 14.5, fill: C.accent, weight: 600, mono: false });
  } else {
    s += tx(PAD, VERDICT, "The two bars have to overlap. That is the whole test.", { size: 15, fill: C.faint, weight: 500, mono: false });
  }

  svg.innerHTML = s;
  svg.setAttribute("aria-label", chartLabel(network, signals, samples));
  if (cursor != null) return;
  svg.querySelectorAll("polyline.draw").forEach((pl) => {
    const len = pl.getTotalLength();
    pl.animate([{ strokeDasharray: len, strokeDashoffset: len }, { strokeDasharray: len, strokeDashoffset: 0 }],
               { duration: 950, easing: "cubic-bezier(.23,1,.32,1)", fill: "forwards" });
  });
}

function revealChart(samples, network, signals, seq) {
  if (!samples || !samples.length) { drawChart(samples, network, signals); return; }
  const t0 = performance.now(), D = RECORD ? 2600 : 3200;
  const step = () => {
    if (seq !== runSeq) return;
    const f = Math.min(1, (performance.now() - t0) / D);
    const e = 1 - Math.pow(1 - f, 3);
    if (f < 1) { drawChart(samples, network, null, e * 120); requestAnimationFrame(step); }
    else drawChart(samples, network, signals);
  };
  requestAnimationFrame(step);
}

function chartLabel(network, sg, samples) {
  const dwell = network && network.K1
    ? `The operator places the truck in the tank zone from ${network.K1.entered} to ${network.K1.left}.`
    : "The operator never places the truck in the tank zone.";
  if (!sg) return `Two clocks compared: the operator's dwell window and the tank's level rise. ${dwell}`;
  if (samples && !samples.length) return `No sensor samples: the tank sensor was unreachable. ${dwell}`;
  const rise = sg.rise_window ? `The level rises ${sg.delta_m3} cubic metres between ${sg.rise_window[0]} and ${sg.rise_window[1]}.` : "The level does not rise.";
  const agree = sg.rise_dwell_overlap_min > 0
    ? `They overlap for ${sg.rise_dwell_overlap_min} minutes.` : "They do not overlap.";
  return `${rise} ${dwell} ${agree} Peak turbidity ${sg.turbidity_ntu ?? "unknown"} NTU.`;
}

// ---------------------------------------------------------------- run
function abortRun() {
  if (!active) return;
  try { active.es.close(); } catch (e) { /* already closed */ }
  active = null;
  clearInterval(animTimer);
  truckMarker?.getElement()?.querySelector(".truck")?.classList.remove("moving");
  runDone();
}

function runDone() {
  const b = $("#run"); b.disabled = false; b.classList.remove("running"); b.textContent = "Run verification";
  $("#mode").textContent = "";
  const cur = $("#trace .cursor"); if (cur) cur.remove();
}

async function runScenario(id) {
  if (active) abortRun();
  resetPanels();
  $("#hero")?.classList.add("done");   // the landing gives way to the tool the moment a run starts
  document.body.classList.remove("landing");
  const seq = ++runSeq;
  const b = $("#run"); b.disabled = true; b.classList.add("running"); b.textContent = "Verifying";
  // the verdict block shows that something is happening, and what
  $("#decision").innerHTML = `<h2>Verdict</h2><div class="waiting running">Verifying</div><div class="amount" id="progress">asking the operator's network…</div>`;
  let progCalls = 0, progNode = "intake";
  const progress = () => { const el = $("#progress"); if (el) el.textContent = `${progCalls} network call${progCalls === 1 ? "" : "s"} so far · agent at ${progNode}`; };
  $("#mode").textContent = STATUS.mode === "live" ? "calling Nokia NaC" : "fixtures";

  let run_id;
  try {
    const r = await fetch(`/api/run/${id}?profile=${encodeURIComponent(PROFILE || "")}`, { method: "POST" });
    if (!r.ok) throw new Error(`the server answered ${r.status}`);
    ({ run_id } = await r.json());
  } catch (err) {
    if (seq === runSeq) { showFailure("The run could not be started.", err.message); runDone(); }
    return;
  }
  if (seq !== runSeq) return;            // a different trip was picked while we waited
  lastRun = run_id;

  const queue = []; let done = false, calls = 0;
  const es = new EventSource(`/api/stream/${run_id}`);
  active = { id: run_id, es, seq };
  es.onmessage = (ev) => {
    const it = JSON.parse(ev.data);
    if (it.kind === "done" || it.kind === "error") { done = true; es.close(); }
    queue.push(it);
  };
  es.onerror = () => {
    es.close();
    if (!done && active && active.seq === seq) { showFailure("The connection to the run was lost.", "the event stream closed before the agent finished"); abortRun(); }
    done = true;
  };
  animateTruck(current.network, id === "substitution");

  // paced playback so a human can follow the reasoning
  const tick = async () => {
    if (!active || active.seq !== seq) return;      // superseded by another run
    while (queue.length) {
      const it = queue.shift();
      if (it.kind === "step") { addStep(it); progNode = it.node; progress(); }
      else if (it.kind === "call") { addCall(it); calls++; $("#callcount").textContent = `${calls} calls`; progCalls = calls; progress(); }
      else if (it.kind === "done") { await finish(run_id, seq); active = null; runDone(); return; }
      else if (it.kind === "error") { showFailure("The agent stopped before deciding.", it.error); active = null; runDone(); return; }
      await sleep(it.kind === "call" ? (RECORD ? 60 : 120) : (RECORD ? 190 : 380));
      if (!active || active.seq !== seq) return;
    }
    if (!done || queue.length) setTimeout(tick, 60); else { active = null; runDone(); }
  };
  tick();
}
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function showFailure(headline, detail) {
  const d = $("#decision");
  d.className = "card failed";
  d.innerHTML = `<h2>Verdict</h2><div class="big ESCALATE">Not run</div><div class="reason">${headline}</div>
    <div class="next"><span>What happened</span><br>${detail}. No operator calls were charged beyond those already listed, and no payment was released.</div>
    <div class="amount">press Run verification to try again</div>`;
}

function setNode(name) {
  const g = $("#graph"); if (!g) return;
  g.querySelectorAll("span.active").forEach((n) => { n.classList.remove("active"); n.classList.add("done"); });
  const n = g.querySelector(`[data-node="${name}"]`);
  if (n) { n.classList.remove("done"); n.classList.add("active"); }
}

function addStep(st) {
  setNode(st.node);
  const d = document.createElement("div");
  d.className = `ln ${st.node}` + (st.text.startsWith("does not fit") ? " contra" : "");
  d.innerHTML = `<span class="n ${st.node}">${st.node.toUpperCase()}</span><span class="x"></span>`;
  if (!renderFacts(d.querySelector(".x"), st.text)) d.querySelector(".x").textContent = st.text;
  const cur = $("#trace .cursor"); if (cur) cur.remove();
  $("#trace").appendChild(d);
  if (active) { const c = document.createElement("span"); c.className = "cursor"; d.querySelector(".x").appendChild(c); }
  $("#trace").scrollTop = $("#trace").scrollHeight;
}
/* The score step is a JSON object. Dumping it raw is developer output: correct, unreadable,
   and the single densest thing on the page. Same values, laid out as facts. */
function renderFacts(el, text) {
  if (!text || text[0] !== "{") return false;
  let o;
  try { o = JSON.parse(text); } catch (e) { return false; }
  if (!o || typeof o !== "object" || Array.isArray(o)) return false;
  el.className = "x facts";
  el.textContent = "";
  for (const [k, v] of Object.entries(o)) {
    if (v === null) continue;
    const f = document.createElement("span");
    f.className = "fact";
    const b = document.createElement("b"), i = document.createElement("i");
    b.textContent = k.replace(/_/g, " ");
    i.textContent = Array.isArray(v) ? v.join(" – ") : String(v);
    if (v === false) i.className = "no";
    f.append(b, i);
    el.appendChild(f);
  }
  return true;
}

function countUp(el, target, unit, decimals) {
  const t0 = performance.now(), dur = 700;
  const step = (now) => { const p = Math.min(1, (now - t0) / dur), e = 1 - Math.pow(1 - p, 3); el.textContent = (target * e).toFixed(decimals) + unit; if (p < 1) requestAnimationFrame(step); };
  requestAnimationFrame(step);
}
function addCall(c) {
  const tb = $("#calls"); const tr = document.createElement("tr");
  tr.className = "call"; tr.tabIndex = 0; tr.setAttribute("role", "button"); tr.setAttribute("aria-expanded", "false");
  const res = c.error ? "ERROR " + c.error : summarize(c.response);
  tr.innerHTML = `<td>${c.seq}</td><td><b>${c.camara}</b><br><span class="muted">${c.api}</span></td><td class="muted">${c.category}</td><td>${targetOf(c.request)}${c.request.area ? `<br><span class="muted">r=${c.request.area.radius} m</span>` : ""}${c.request.config ? `<br><span class="muted">${c.request.types[0].split(".").pop()}</span>` : ""}</td><td><span class="pill ${c.mode}">${c.mode}</span></td><td>${c.latency_ms}</td><td>${res}</td>`;
  tr.setAttribute("aria-label", `Call ${c.seq}, ${c.camara}. Show the raw request and response.`);
  const raw = document.createElement("tr"); raw.className = "raw"; raw.hidden = true;
  raw.innerHTML = `<td colspan="7">REQUEST  ${JSON.stringify(c.request, null, 1)}\n\nRESPONSE ${JSON.stringify(c.response, null, 1)}</td>`;
  const toggle = () => { raw.hidden = !raw.hidden; tr.setAttribute("aria-expanded", String(!raw.hidden)); };
  tr.onclick = toggle;
  tr.onkeydown = (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggle(); } };
  tb.appendChild(tr); tb.appendChild(raw);
}
function targetOf(req) {
  if (req.device) return req.device.phone_number;
  if (req.phone_number) return req.phone_number;
  if (req.config && req.config.subscription_detail) return req.config.subscription_detail.device.phone_number + " · " + zoneName(req.config.subscription_detail.area);
  return "—";
}
function zoneName(area) {
  for (const [id, z] of Object.entries(STATUS.zones)) if (Math.abs(z.lat - area.center.latitude) < 1e-4 && Math.abs(z.lon - area.center.longitude) < 1e-4) return id;
  return "";
}
function summarize(r) {
  if (!r) return "—";
  if (r.verification_result) return `verification_result: <b>${r.verification_result}</b>${r.match_rate ? ` (match ${r.match_rate}%)` : ""}`;
  if ("swapped" in r) return `swapped: <b>${r.swapped}</b>`;
  if ("reachable" in r) return `reachable: <b>${r.reachable}</b>${r.connectivity ? ` · ${r.connectivity.join("+")}` : ""}`;
  if ("roaming" in r) return `roaming: <b>${r.roaming}</b>${r.country_name ? ` · ${r.country_name[0]}` : ""}`;
  if (r.area) return `area ${r.area.area_type} (${r.area.center.latitude.toFixed(3)}, ${r.area.center.longitude.toFixed(3)}) r=${r.area.radius}`;
  if (r.id && r.types) return `subscription created · ${String(r.id).slice(0, 8)}${r.status ? " · " + r.status : ""}${r.starts_at ? " · " + String(r.starts_at).slice(11, 19) + "Z" : ""}`;
  if (r.latest_sim_change) return `latest change ${r.latest_sim_change}`;
  return JSON.stringify(r).slice(0, 80);
}

async function finish(run_id, seq) {
  const st = await (await fetch(`/api/runs/${run_id}`)).json();
  if (seq !== runSeq) return;                      // a different trip was picked while we fetched
  const sg = st.signals || {};
  revealChart(st.trace_samples || [], st.network, sg, seq);

  // the gate can reject the measurement outright; the KPI must not keep asserting it
  const rejected = /not believed|implausible/.test(st.reason || "");
  countUp($("#k_claim"), sg.claimed_m3, " m³", 1);
  countUp($("#k_meas"), sg.delta_m3, " m³", 1);
  $("#kpi_meas").className = "kpi" + (rejected ? " rejected" : "");
  $("#kpi_meas .flag")?.remove();
  if (rejected) {
    const f = document.createElement("span"); f.className = "flag"; f.textContent = "not credited";
    $("#kpi_meas").appendChild(f);
  }
  if (sg.dwell_min) countUp($("#k_dwell"), sg.dwell_min, " min", 0); else $("#k_dwell").textContent = "—";
  if (sg.turbidity_ntu == null) $("#k_turb").textContent = "—"; else countUp($("#k_turb"), sg.turbidity_ntu, " NTU", 1);

  // decision: the verdict and what happens next, nothing else
  const word = st.decision.charAt(0) + st.decision.slice(1).toLowerCase();
  const act = (st.steps || []).find((s) => s.node === "act");
  const d = $("#decision");
  d.className = "card " + st.decision;
  setNode("act");
  setTimeout(() => { const n = $('#graph [data-node="act"]'); if (n) { n.classList.remove("active"); n.classList.add("done"); } }, 800);
  // the gate appends the profile caveat to its reason string; the list below carries it, so the sentence stays short
  const reason = (sg.unchecked && sg.unchecked.length) ? st.reason.split("; not checkable on this deployment profile")[0] : st.reason;
  d.innerHTML = `<h2>Verdict</h2><div class="big ${st.decision}">${word}</div><div class="reason">${reason}</div>
    ${act ? `<div class="next"><span>Next step</span><br>${act.text}</div>` : ""}
    ${(sg.unchecked && sg.unchecked.length) ? `<div class="unchecked"><span>Not checked on this profile</span><ul>${sg.unchecked.map((u) => `<li>${u}</li>`).join("")}</ul></div>` : ""}
    <div class="amount"><b>${st.pay_m3} m³</b> released · <b>${(st.amount_iqd || 0).toLocaleString()} IQD</b> · ${st.evidence.length} operator checks · ${st.investigations} investigation round${st.investigations === 1 ? "" : "s"}</div>`;

  // record: the ledger row and the model's audit note
  const lg = st.ledger;
  $("#ledger").innerHTML = lg
    ? `${lg.contractor} · trip #${lg.trip_id} · tank ${lg.tank_id} · claimed ${lg.claimed_m3} m³ · verified ${lg.verified_m3} m³ · paid <b>${lg.paid_m3} m³ = ${lg.amount_iqd.toLocaleString()} IQD</b> · status <b class="${lg.status}">${lg.status}</b><br><span class="muted">evidence: ${lg.evidence_refs.join(", ")}</span>`
    : "—";
  $("#auditnote").innerHTML = `<div class="note">${st.audit_note}</div>${st.audit_note_ar ? `<div class="ar">${st.audit_note_ar}</div>` : ""}
    <div class="src">Audit note written by ${st.audit_note_source && st.audit_note_source !== "template" ? st.audit_note_source : (STATUS.llm === "stub" ? "a template, no model configured" : "a template, the model was unavailable for this call")}. The decision above came from the deterministic gate.${st.planner_note ? `<br>Planner: ${st.planner_note}` : ""}</div>`;

  const wh = st.webhooks || [];
  $("#webhooks").innerHTML = wh.length
    ? `<b>${wh.length} operator webhook${wh.length > 1 ? "s" : ""} received</b> for this run's subscriptions (CloudEvents to ${STATUS.webhook_sink.replace(/^https?:\/\//, "")})<br>` +
      wh.map((w, i) => `<div style="animation-delay:${i * 90}ms">${(w.time || "").slice(11, 19)}Z · ${(w.type || "").split(".").pop()} · ${w.device} · sub ${(w.subscription || "").slice(0, 8)}</div>`).join("")
    : (STATUS.mode === "live" ? "no operator webhook received for this run (polling fallback used)" : "fixture mode: no operator webhooks (set NAC_API_KEY and PUBLIC_BASE_URL)");

  $("#f306").disabled = false;
  refreshRuns();

  const nx = NEXT[current?.id];
  if (nx && SCEN.some((x) => x.id === nx.id)) {
    const box = document.createElement("div"); box.className = "nextstep";
    box.innerHTML = `<span></span> <a role="button" tabindex="0">Run it →</a>`;
    box.querySelector("span").textContent = nx.text;
    const go = () => select(nx.id, true);
    box.querySelector("a").onclick = go;
    box.querySelector("a").onkeydown = (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); go(); } };
    d.appendChild(box);
  }

  // one column on narrow screens puts the verdict far below the trip list; bring it to the reader
  if (window.innerWidth <= 1100) {
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    d.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "start" });
  }
}

async function refreshRuns() {
  const runs = await (await fetch("/api/runs")).json();
  if (!runs.length) return;
  $("#runs").innerHTML = runs.slice(0, window.innerWidth <= 700 ? 3 : 6).map((r) => `<div><span class="tag ${r.decision}">${r.decision}</span> · ${r.started.replace("T", " ").slice(11, 16)} · ${r.title}</div>`).join("");
}

boot();
