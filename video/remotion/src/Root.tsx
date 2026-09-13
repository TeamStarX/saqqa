import React from "react";
import { Composition } from "remotion";
import { SaqqaDemo } from "./SaqqaDemo";
import timeline from "./timeline.json";

const total = timeline.scenes.reduce((n, s) => Math.max(n, s.start + s.frames), 0) + timeline.tail;

export const Root: React.FC = () => (
  <Composition
    id="SaqqaDemo"
    component={SaqqaDemo}
    durationInFrames={total}
    fps={timeline.fps}
    width={timeline.width}
    height={timeline.height}
    defaultProps={{ timeline }}
  />
);
