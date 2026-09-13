/* The Saqqa demo film. Same type system as the dashboard: one family, paper ground, one accent.
   Cards carry the argument; footage carries the proof; the narration carries both. */
import React from "react";
import {
  AbsoluteFill,
  Audio,
  OffthreadVideo,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { loadFont } from "@remotion/google-fonts/LibreFranklin";

const { fontFamily } = loadFont("normal", { weights: ["400", "500", "600", "700"], subsets: ["latin"] });

const PAPER = "#FBFAF7";
const PAPER2 = "#F4F2ED";
const INK = "#1A1A17";
const MUTED = "#5C5C55";
const RULE = "#DCD9D0";
const ACCENT = "#A8401F";
const RELEASE = "#2E6B3A";
const SANS = `${fontFamily}, "Segoe UI", system-ui, sans-serif`;

type Scene = {
  id: string;
  kind: "card" | "footage";
  clip?: string;
  segments?: number[][];
  narration: string;
  on_screen: string;
  start: number;
  frames: number;
  vo?: string;
  layout?: string;
  stats?: { big: string; cap: string }[];
  steps?: string[];
};
type Timeline = { fps: number; width: number; height: number; tail: number; scenes: Scene[] };

/* ------------------------------------------------------------------ helpers */
const useIn = (delay = 0, damp = 200) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return spring({ frame: frame - delay, fps, config: { damping: damp, stiffness: 120, mass: 0.9 } });
};

const Fade: React.FC<{ frames: number; children: React.ReactNode }> = ({ frames, children }) => {
  const frame = useCurrentFrame();
  const o = interpolate(frame, [0, 10, frames - 10, frames], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return <AbsoluteFill style={{ opacity: o }}>{children}</AbsoluteFill>;
};

const Words: React.FC<{ text: string; size: number; weight?: number; color?: string; delay?: number; maxWidth?: number; align?: "center" | "left" }> = ({
  text, size, weight = 600, color = INK, delay = 0, maxWidth = 1500, align = "center",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const words = text.split(" ");
  return (
    <div style={{ fontFamily: SANS, fontSize: size, fontWeight: weight, color, letterSpacing: "-0.035em", lineHeight: 1.05, maxWidth, textAlign: align, textWrap: "balance" as any }}>
      {words.map((w, i) => {
        const s = spring({ frame: frame - delay - i * 2, fps, config: { damping: 200, stiffness: 140 } });
        return (
          <span key={i} style={{ display: "inline-block", marginRight: "0.26em", opacity: s, transform: `translateY(${(1 - s) * 22}px)` }}>
            {w}
          </span>
        );
      })}
    </div>
  );
};

const Eyebrow: React.FC<{ text: string; delay?: number }> = ({ text, delay = 0 }) => {
  const s = useIn(delay);
  return (
    <div style={{ fontFamily: SANS, fontSize: 24, fontWeight: 500, color: MUTED, letterSpacing: "-0.005em", opacity: s, transform: `translateY(${(1 - s) * 10}px)`, marginBottom: 34 }}>
      {text}
    </div>
  );
};

const Mark: React.FC = () => (
  <div style={{ position: "absolute", left: 72, top: 56, display: "flex", alignItems: "baseline", gap: 18, fontFamily: SANS }}>
    <span style={{ fontSize: 34, fontWeight: 700, letterSpacing: "-0.025em", color: INK }}>Saqqa</span>
    <span style={{ fontSize: 22, fontWeight: 400, color: MUTED, borderLeft: `1px solid ${RULE}`, paddingLeft: 18 }}>
      network-attested delivery and payment for trucked water
    </span>
  </div>
);

const Ground: React.FC<{ children: React.ReactNode; glow?: boolean }> = ({ children, glow = true }) => (
  <AbsoluteFill
    style={{
      background: glow
        ? `radial-gradient(60% 55% at 50% 0%, rgba(168,64,31,.07), transparent 70%), ${PAPER}`
        : PAPER,
    }}
  >
    {children}
  </AbsoluteFill>
);

/* ------------------------------------------------------------------ cards */
const HeadlineCard: React.FC<{ scene: Scene; eyebrow?: string }> = ({ scene, eyebrow }) => (
  <Ground>
    <Mark />
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", padding: "0 160px" }}>
      {eyebrow ? <Eyebrow text={eyebrow} delay={4} /> : null}
      <Words text={scene.on_screen} size={108} delay={10} maxWidth={1420} />
    </AbsoluteFill>
  </Ground>
);

const StatsCard: React.FC<{ scene: Scene }> = ({ scene }) => {
  const stats = scene.stats || [];
  return (
    <Ground glow={false}>
      <Mark />
      <AbsoluteFill style={{ justifyContent: "center", padding: "0 160px" }}>
        <div style={{ marginBottom: 70 }}>
          <Words text={scene.on_screen} size={64} weight={600} delay={6} maxWidth={1500} align="left" />
        </div>
        <div style={{ display: "flex", gap: 0, borderTop: `1px solid ${RULE}` }}>
          {stats.map((st, i) => {
            const s = useIn(22 + i * 9);
            return (
              <div key={i} style={{ flex: 1, padding: "44px 48px 0 0", marginRight: 48, borderTop: `2px solid ${i === 0 ? ACCENT : "transparent"}`, marginTop: -1, opacity: s, transform: `translateY(${(1 - s) * 18}px)` }}>
                <div style={{ fontFamily: SANS, fontSize: 132, fontWeight: 700, letterSpacing: "-0.045em", lineHeight: 0.95, color: INK }}>{st.big}</div>
                <div style={{ fontFamily: SANS, fontSize: 28, fontWeight: 400, color: MUTED, marginTop: 22, lineHeight: 1.35, maxWidth: 420 }}>{st.cap}</div>
              </div>
            );
          })}
        </div>
      </AbsoluteFill>
    </Ground>
  );
};

const StepsCard: React.FC<{ scene: Scene }> = ({ scene }) => {
  const steps = scene.steps || [];
  return (
    <Ground>
      <Mark />
      <AbsoluteFill style={{ justifyContent: "center", padding: "0 160px" }}>
        <div style={{ marginBottom: 74 }}>
          <Words text={scene.on_screen} size={76} weight={600} delay={6} maxWidth={1500} align="left" />
        </div>
        <div style={{ display: "flex", gap: 40 }}>
          {steps.map((t, i) => {
            const s = useIn(26 + i * 12);
            return (
              <div key={i} style={{ flex: 1, background: PAPER2, borderRadius: 14, padding: "38px 40px", opacity: s, transform: `translateY(${(1 - s) * 22}px)` }}>
                <div style={{ fontFamily: SANS, fontSize: 22, fontWeight: 600, color: ACCENT, marginBottom: 16 }}>{String(i + 1).padStart(2, "0")}</div>
                <div style={{ fontFamily: SANS, fontSize: 34, fontWeight: 500, color: INK, letterSpacing: "-0.02em", lineHeight: 1.25 }}>{t}</div>
              </div>
            );
          })}
        </div>
      </AbsoluteFill>
    </Ground>
  );
};

const CloseCard: React.FC<{ scene: Scene }> = ({ scene }) => {
  const s1 = useIn(6);
  const s2 = useIn(26);
  const s3 = useIn(44);
  return (
    <Ground>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <div style={{ fontFamily: SANS, fontSize: 150, fontWeight: 700, letterSpacing: "-0.05em", color: INK, opacity: s1, transform: `translateY(${(1 - s1) * 24}px)` }}>Saqqa</div>
        <div style={{ fontFamily: SANS, fontSize: 40, fontWeight: 500, color: INK, letterSpacing: "-0.02em", marginTop: 8, opacity: s2, transform: `translateY(${(1 - s2) * 16}px)` }}>
          Pay only for the water that arrived. The mobile network is the witness.
        </div>
        <div style={{ fontFamily: SANS, fontSize: 26, fontWeight: 400, color: MUTED, marginTop: 44, opacity: s3 }}>
          Team StarX · GSMA MENA Ignite Hackathon 2026 · Built on CAMARA Open Gateway APIs
        </div>
      </AbsoluteFill>
    </Ground>
  );
};

/* ------------------------------------------------------------------ footage */
const FW = 1696, FH = 954, FTOP = 34;   // the inset browser frame; the caption lives in the band under it

const Footage: React.FC<{ scene: Scene }> = ({ scene }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const scale = interpolate(frame, [0, scene.frames], [1.0, 1.025], { extrapolateRight: "clamp" });
  const lift = spring({ frame, fps, config: { damping: 200, stiffness: 90 } });
  const cap = spring({ frame: frame - 18, fps, config: { damping: 200, stiffness: 120 } });
  const src = staticFile(`footage/${scene.clip}.mp4`);
  const segs = scene.segments && scene.segments.length ? scene.segments : [[0, 1e9]];
  let at = 0;
  const parts = segs.map(([a, b], i) => {
    const from = Math.round(a * fps);
    const len = i === segs.length - 1 ? Math.max(1, scene.frames - at) : Math.max(1, Math.round((b - a) * fps));
    const el = (
      <Sequence key={i} from={at} durationInFrames={len} layout="none">
        <OffthreadVideo src={src} startFrom={from} style={{ width: FW, height: FH, objectFit: "cover" }} muted />
      </Sequence>
    );
    at += len;
    return el;
  });
  return (
    <Ground glow={false}>
      <div
        style={{
          position: "absolute", left: (1920 - FW) / 2, top: FTOP, width: FW, height: FH, borderRadius: 14, overflow: "hidden",
          boxShadow: "0 26px 70px rgba(26,26,23,.16), 0 1px 0 rgba(26,26,23,.06)",
          border: `1px solid ${RULE}`, background: PAPER, transformOrigin: "50% 40%",
          transform: `translateY(${(1 - lift) * 26}px) scale(${scale})`, opacity: lift,
        }}
      >
        {parts}
      </div>
      {/* the caption band under the frame: the sentence the footage is proving, never over the page */}
      <div
        style={{
          position: "absolute", left: (1920 - FW) / 2, top: FTOP + FH + 16, height: 1080 - FTOP - FH - 16,
          display: "flex", alignItems: "center", gap: 14,
          fontFamily: SANS, fontSize: 26, fontWeight: 500, letterSpacing: "-0.015em", color: INK,
          opacity: cap, transform: `translateY(${(1 - cap) * 10}px)`,
        }}
      >
        <span style={{ width: 9, height: 9, borderRadius: 5, background: RELEASE, display: "inline-block" }} />
        {scene.on_screen}
      </div>
    </Ground>
  );
};

/* ------------------------------------------------------------------ the film */
const SceneView: React.FC<{ scene: Scene }> = ({ scene }) => {
  if (scene.kind === "footage") return <Footage scene={scene} />;
  if (scene.layout === "stats") return <StatsCard scene={scene} />;
  if (scene.layout === "steps") return <StepsCard scene={scene} />;
  if (scene.layout === "close") return <CloseCard scene={scene} />;
  return <HeadlineCard scene={scene} eyebrow={scene.id === "01_open" ? "Trucked water, across the Middle East" : undefined} />;
};

export const SaqqaDemo: React.FC<{ timeline: Timeline }> = ({ timeline }) => (
  <AbsoluteFill style={{ background: PAPER }}>
    {timeline.scenes.map((scene) => (
      <Sequence key={scene.id} from={scene.start} durationInFrames={scene.frames} name={scene.id}>
        <Fade frames={scene.frames}>
          <SceneView scene={scene} />
        </Fade>
        {scene.vo ? <Audio src={staticFile(scene.vo)} /> : null}
      </Sequence>
    ))}
  </AbsoluteFill>
);
