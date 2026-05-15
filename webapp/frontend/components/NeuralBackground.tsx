"use client";

import { useEffect, useRef } from "react";

/**
 * Refined neural-network backdrop.  Premium, calm, scientific.
 *
 *   • Canvas-based, fixed positioned, behind everything.
 *   • ~46 slowly-drifting nodes with content-aware dimming — nodes
 *     near the horizontal centre column (where the report sits) fade
 *     out so they never compete with the text.  Edges stay lit.
 *   • Mostly teal/mint, sparse violet, single ice-blue highlight.
 *   • Thin low-opacity links that breathe slowly.
 *   • A few subtle particles travel along a handful of edges to give
 *     the field a sense of *flow* without flashing.
 *   • Honors `prefers-reduced-motion` — single static frame, no rAF.
 *   • Pointer events disabled.
 *
 * No props, no state.  Mount once at the app root.
 */
export function NeuralBackground() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctxOrNull = canvas.getContext("2d", { alpha: true });
    if (!ctxOrNull) return;
    const c: HTMLCanvasElement = canvas;
    const ctx: CanvasRenderingContext2D = ctxOrNull;

    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const NODE_COUNT = 46;             // calmer field than before
    const LINK_DIST = 165;             // px — connect nodes within this radius
    const PARTICLE_COUNT = 6;          // tiny travellers along random edges

    // Mostly teal/mint with a tasteful violet appearance and a single
    // ice-blue highlight slot.  No green (reserved for safety/supported).
    const PALETTE = [
      { r:  45, g: 212, b: 191 },      // brand-400  teal           (primary)
      { r:  94, g: 234, b: 212 },      // brand-300  mint           (secondary)
      { r: 153, g: 246, b: 228 },      // brand-200  soft mint
      { r:  45, g: 212, b: 191 },      // weight teal extra
      { r:  94, g: 234, b: 212 },      // weight mint extra
      { r: 167, g: 139, b: 250 },      // accent-violet              (atmosphere)
      { r:  56, g: 189, b: 248 },      // accent-cyan / ice blue     (highlight)
    ];

    // Slow drifting glow blobs — very low opacity, just atmosphere.
    type Blob = { x: number; y: number; r: number; color: string; phase: number };
    let blobs: Blob[] = [];

    type Node = {
      x: number;
      y: number;
      vx: number;
      vy: number;
      r: number;          // base radius
      phase: number;      // pulse phase offset
      color: { r: number; g: number; b: number };
    };

    /**
     * Particles ride along a node-pair edge.  Each particle is keyed by
     * two indices into `nodes`; we resample those indices occasionally
     * so the flow visits different parts of the field.
     */
    type Particle = {
      a: number;          // node index a
      b: number;          // node index b
      t: number;          // progress 0..1
      speed: number;      // delta-t per second
      color: { r: number; g: number; b: number };
    };

    let width = 0;
    let height = 0;
    let dpr = 1;
    let nodes: Node[] = [];
    let particles: Particle[] = [];
    let raf = 0;
    const t0 = performance.now();

    function rand(min: number, max: number) {
      return Math.random() * (max - min) + min;
    }

    function seedNodes() {
      nodes = Array.from({ length: NODE_COUNT }, () => ({
        x: rand(0, width),
        y: rand(0, height),
        // Slower drift than before — calm motion only.
        vx: rand(-0.06, 0.06),
        vy: rand(-0.06, 0.06),
        r: rand(1.1, 2.3),
        phase: rand(0, Math.PI * 2),
        color: PALETTE[Math.floor(Math.random() * PALETTE.length)],
      }));
    }

    function pickEdgePair(): [number, number] {
      // Choose two nodes within link distance so the particle has a
      // meaningful edge to travel.  Fall back to a random pair after a
      // few tries.
      for (let attempt = 0; attempt < 10; attempt++) {
        const a = Math.floor(Math.random() * nodes.length);
        const b = Math.floor(Math.random() * nodes.length);
        if (a === b) continue;
        const dx = nodes[a].x - nodes[b].x;
        const dy = nodes[a].y - nodes[b].y;
        if (dx * dx + dy * dy < LINK_DIST * LINK_DIST) return [a, b];
      }
      const a = Math.floor(Math.random() * nodes.length);
      const b = (a + 1) % nodes.length;
      return [a, b];
    }

    function seedParticles() {
      particles = Array.from({ length: PARTICLE_COUNT }, () => {
        const [a, b] = pickEdgePair();
        return {
          a,
          b,
          t: Math.random(),
          speed: rand(0.18, 0.34),          // ~3–5s to traverse an edge
          color: PALETTE[Math.floor(Math.random() * PALETTE.length)],
        };
      });
    }

    function seedBlobs() {
      // Very low alpha — atmosphere, not focal point.
      blobs = [
        { x: width * 0.16, y: height * 0.22, r: Math.max(width, 600) * 0.30, color: "rgba( 45,212,191,0.08)", phase: 0   },  // teal top-left
        { x: width * 0.84, y: height * 0.18, r: Math.max(width, 600) * 0.26, color: "rgba(167,139,250,0.06)", phase: 1.3 },  // violet top-right
        { x: width * 0.50, y: height * 0.95, r: Math.max(width, 600) * 0.34, color: "rgba( 56,189,248,0.05)", phase: 2.6 },  // ice blue bottom
      ];
    }

    function resize() {
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = window.innerWidth;
      height = window.innerHeight;
      c.width = Math.floor(width * dpr);
      c.height = Math.floor(height * dpr);
      c.style.width = `${width}px`;
      c.style.height = `${height}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      seedNodes();
      seedParticles();
      seedBlobs();
    }

    /**
     * Content-aware dimming factor for a point.
     *
     * Returns ~1.0 near the page edges and ~0.30 near the horizontal centre
     * column (where the report sits), so nodes/links visible behind the
     * card are softened and don't compete with the text.  Mathematically:
     * a smooth quintic falloff over a 560-px-wide central band.
     */
    function edgeFactor(x: number): number {
      const halfBand = 280;
      const cx = width / 2;
      const d = Math.min(1, Math.abs(x - cx) / halfBand);
      // smoothstep^2 → very gentle ramp
      const s = d * d * (3 - 2 * d);
      return 0.30 + 0.70 * s;
    }

    function draw(now: number) {
      const t = (now - t0) / 1000;
      ctx.clearRect(0, 0, width, height);

      // 0. Soft drifting glow blobs (deepest layer, very low opacity).
      for (const blob of blobs) {
        const pulse = 0.9 + 0.1 * Math.sin(t * 0.35 + blob.phase);
        const dy = Math.sin(t * 0.14 + blob.phase) * 18;
        const grad = ctx.createRadialGradient(
          blob.x, blob.y + dy, 0,
          blob.x, blob.y + dy, blob.r * pulse,
        );
        grad.addColorStop(0, blob.color);
        grad.addColorStop(1, "rgba(0,0,0,0)");
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, width, height);
      }

      // 1. Update node positions — slow wrap-around.
      for (const n of nodes) {
        n.x += n.vx;
        n.y += n.vy;
        if (n.x < -20) n.x = width + 20;
        if (n.x > width + 20) n.x = -20;
        if (n.y < -20) n.y = height + 20;
        if (n.y > height + 20) n.y = -20;
      }

      // 2. Lines — drawn before nodes so dots sit on top.
      ctx.lineWidth = 0.55;
      for (let i = 0; i < nodes.length; i++) {
        const a = nodes[i];
        for (let j = i + 1; j < nodes.length; j++) {
          const b = nodes[j];
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          const d2 = dx * dx + dy * dy;
          const lim2 = LINK_DIST * LINK_DIST;
          if (d2 > lim2) continue;
          const t01 = 1 - Math.sqrt(d2) / LINK_DIST;          // 1 close, 0 far
          // Slow flow modulation, less amplitude than before.
          const flow = 0.85 + 0.15 * Math.sin(t * 0.4 + (a.phase + b.phase) * 0.5);
          // Content-aware dimming: average both endpoints' edge factor.
          const dim = (edgeFactor(a.x) + edgeFactor(b.x)) * 0.5;
          const alpha = t01 * t01 * 0.22 * flow * dim;        // dimmer than before
          if (alpha < 0.012) continue;                        // skip nearly-invisible edges
          const cr = Math.round((a.color.r + b.color.r) / 2);
          const cg = Math.round((a.color.g + b.color.g) / 2);
          const cb = Math.round((a.color.b + b.color.b) / 2);
          ctx.strokeStyle = `rgba(${cr},${cg},${cb},${alpha})`;
          ctx.beginPath();
          ctx.moveTo(a.x, a.y);
          ctx.lineTo(b.x, b.y);
          ctx.stroke();
        }
      }

      // 3. Particles — tiny bright dots travelling along a few edges.
      // dt is approximated as a fixed 16ms since we throttle naturally to vsync.
      const dt = 1 / 60;
      for (const p of particles) {
        const a = nodes[p.a];
        const b = nodes[p.b];
        p.t += p.speed * dt;
        if (p.t >= 1) {
          // Resample the edge so the flow visits different parts of the field.
          const [na, nb] = pickEdgePair();
          p.a = na;
          p.b = nb;
          p.t = 0;
          p.speed = rand(0.18, 0.34);
          continue;
        }
        const px = a.x + (b.x - a.x) * p.t;
        const py = a.y + (b.y - a.y) * p.t;
        const dim = edgeFactor(px);
        // Soft tear-drop: a tiny halo + bright core, both dimmed by content distance.
        ctx.fillStyle = `rgba(${p.color.r},${p.color.g},${p.color.b},${0.18 * dim})`;
        ctx.beginPath();
        ctx.arc(px, py, 3.2, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = `rgba(${p.color.r},${p.color.g},${p.color.b},${0.75 * dim})`;
        ctx.beginPath();
        ctx.arc(px, py, 1.1, 0, Math.PI * 2);
        ctx.fill();
      }

      // 4. Nodes — soft halo + bright core, dimmed near content column.
      for (const n of nodes) {
        const pulse = 0.5 + 0.5 * Math.sin(t * 0.9 + n.phase);   // calm pulse 0..1
        const dim = edgeFactor(n.x);
        const { r, g, b } = n.color;

        // Outer halo (very soft)
        ctx.fillStyle = `rgba(${r},${g},${b},${0.08 * pulse * dim})`;
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.r * 5.5, 0, Math.PI * 2);
        ctx.fill();

        // Inner glow ring
        ctx.fillStyle = `rgba(${r},${g},${b},${(0.20 * pulse + 0.10) * dim})`;
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.r * 2.2, 0, Math.PI * 2);
        ctx.fill();

        // Core — slightly cooler near content, brighter near edges
        const coreAlpha = (0.55 + 0.20 * pulse) * dim;
        ctx.fillStyle = `rgba(${r},${g},${b},${coreAlpha})`;
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
        ctx.fill();
      }

      if (!reduceMotion) raf = requestAnimationFrame(draw);
    }

    resize();
    if (reduceMotion) {
      draw(performance.now());        // single static frame
    } else {
      raf = requestAnimationFrame(draw);
    }

    const onResize = () => resize();
    window.addEventListener("resize", onResize);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", onResize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden
      // Lower opacity than before and no mix-blend-screen — keeps the
      // network *behind* the cards rather than washing over them.
      className="pointer-events-none fixed inset-0 z-0 h-full w-full opacity-70"
    />
  );
}

