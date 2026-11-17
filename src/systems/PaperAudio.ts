/**
 * PaperAudio — procedural paper sounds for Pop-up Atlas (Web Audio, no samples).
 *
 * flap(): one card folding up out of the page (up=true) or folding back flat (up=false).
 *   layers: airy swish (band-passed pink noise, swept filter) + low "thup" body
 *   (sine drop + low-passed noise) + crinkle grains + ending (double settle tick / soft pat).
 * step(): soft paper footstep tap.
 *
 * Every call is randomised (pitch, filter sweep, Q, length, grain count/timing, buffer offsets).
 * Voice limit (MAX_VOICES) steals the quietest voice; a duck stage lowers the bus when many overlap.
 * Master: master gain -> duck -> highpass 35 Hz -> lowpass 9 kHz -> compressor -> out.
 * Every envelope is a value curve that starts and ends at exactly 0 (no clicks).
 *
 * Optional extras for offline rendering/tests (do not change the lead's API):
 *   new PaperAudio({ context, seed })   — render into an OfflineAudioContext, reproducible random
 *   flap({ ..., time })  /  step(foot, speed01, time) — schedule at an absolute context time
 */

export interface FlapOptions {
  pitch: number; // ~0.7..1.4 multiplier
  gain: number; // 0..1
  pan: number; // -1..1
  up: boolean; // true: rising fold, false: folding flat
  time?: number; // optional absolute context time (offline rendering)
}

export interface PaperAudioOptions {
  context?: BaseAudioContext;
  seed?: number;
  maxVoices?: number;
  /** tuning/debug: per-layer level multipliers for flap() (default 1 each) */
  layers?: Partial<LayerLevels>;
}

interface LayerLevels {
  swish: number;
  body: number;
  grain: number;
  end: number;
}

interface Voice {
  start: number;
  end: number;
  level: number;
  out: GainNode;
  sources: AudioScheduledSourceNode[];
  nodes: AudioNode[];
  dead: boolean;
}

const MAX_VOICES_DEFAULT = 10;
const CURVE_POINTS = 48;

function clamp(v: number, lo: number, hi: number): number {
  return v < lo ? lo : v > hi ? hi : v;
}

/** mulberry32 — tiny seeded PRNG so offline renders are reproducible. */
function makeRng(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export class PaperAudio {
  private ctx: BaseAudioContext | null = null;
  private ownsContext = false;
  private readonly rng: () => number;
  private readonly maxVoices: number;
  private readonly layers: LayerLevels;

  private master: GainNode | null = null;
  private duck: GainNode | null = null;
  private busNodes: AudioNode[] = [];

  private white: AudioBuffer[] = [];
  private pink: AudioBuffer[] = [];
  private crackle: AudioBuffer | null = null;

  private voices: Voice[] = [];
  private masterVolume = 0.8;
  private lastBufferIndex = -1;

  constructor(opts: PaperAudioOptions = {}) {
    this.rng = makeRng(opts.seed ?? (Date.now() ^ 0x5eed) >>> 0);
    this.maxVoices = opts.maxVoices ?? MAX_VOICES_DEFAULT;
    this.layers = { swish: 1, body: 1, grain: 1, end: 1, ...opts.layers };
    if (opts.context) {
      this.ctx = opts.context;
      this.ownsContext = false;
      this.build();
    }
  }

  // ---------------------------------------------------------------- public API

  /** Call from the first user gesture. Creates (once) and resumes the AudioContext. */
  unlock(): void {
    if (!this.ctx) {
      const Ctor =
        typeof window !== 'undefined'
          ? window.AudioContext ||
            (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext
          : undefined;
      if (!Ctor) return;
      this.ctx = new Ctor({ latencyHint: 'interactive' });
      this.ownsContext = true;
      this.build();
    }
    const c = this.ctx;
    if (typeof AudioContext !== 'undefined' && c instanceof AudioContext && c.state !== 'running') {
      void c.resume().catch(() => undefined);
    }
  }

  flap(opts: FlapOptions): void {
    const ctx = this.ready();
    if (!ctx || !this.master) return;
    const r = this.rng;
    const gain = clamp(opts.gain, 0, 1);
    if (gain <= 0.001) return;
    const t0 = opts.time ?? ctx.currentTime + 0.006;
    const pitch = clamp(opts.pitch, 0.5, 2) * (0.94 + r() * 0.12);
    const up = opts.up;
    const L = this.layers;

    // Bigger / lower cards move a little slower.
    const lenScale = (1 / Math.sqrt(pitch)) * (0.85 + r() * 0.3);
    const swishLen = (up ? 0.15 : 0.13) * lenScale; // 0.10 .. 0.21 s
    const attack = 0.005 + r() * 0.01; // 5..15 ms
    const landAt = t0 + swishLen * (0.55 + r() * 0.2);
    const tail = up ? 0.26 : 0.16;
    const end = t0 + swishLen + tail;

    const level = 0.55 * gain;
    const voice = this.allocVoice(t0, end, level, clamp(opts.pan, -1, 1));
    const out = voice.out;

    // 1) airy swish ---------------------------------------------------------
    {
      const src = this.noiseSource(this.pickPink(), voice);
      const bp = ctx.createBiquadFilter();
      bp.type = 'bandpass';
      bp.Q.value = 0.7 + r() * 0.9;
      const fLo = (650 + r() * 350) * pitch;
      const fHi = (2100 + r() * 1300) * pitch;
      const f = bp.frequency;
      // rising card: air moves up then the edge stops; flat: sweep down
      const fa = up ? fLo : fHi;
      const fb = up ? fHi : fLo * 0.85;
      f.setValueAtTime(fa, t0);
      f.exponentialRampToValueAtTime(fb, t0 + swishLen * (0.6 + r() * 0.25));
      f.exponentialRampToValueAtTime(fb * (up ? 0.7 : 0.9), t0 + swishLen);
      const hp = ctx.createBiquadFilter();
      hp.type = 'highpass';
      hp.frequency.value = 280 + r() * 120;
      const g = this.envGain(t0, attack, swishLen, L.swish * 1.1 * (0.85 + r() * 0.3), 3.2 + r() * 1.5);
      src.connect(bp).connect(hp).connect(g).connect(out);
      voice.nodes.push(bp, hp, g);
      this.startSource(src, t0, swishLen + 0.02);
    }

    // 2) low "thup" body as the card stands / lands -------------------------
    {
      const bodyF = (up ? 135 : 110) * pitch * (0.85 + r() * 0.3); // ~90..180 Hz
      const osc = ctx.createOscillator();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(bodyF * 1.35, landAt);
      osc.frequency.exponentialRampToValueAtTime(bodyF, landAt + 0.035);
      const bodyLen = 0.05 + r() * 0.03;
      const g = this.envGain(landAt, 0.004, bodyLen, L.body * (up ? 0.09 : 0.08) * (0.8 + r() * 0.4), 4);
      osc.connect(g).connect(out);
      voice.nodes.push(g);
      voice.sources.push(osc);
      osc.start(landAt);
      osc.stop(landAt + bodyLen + 0.02);

      const n = this.noiseSource(this.pickWhite(), voice);
      const lp = ctx.createBiquadFilter();
      lp.type = 'lowpass';
      lp.frequency.value = (260 + r() * 160) * pitch;
      lp.Q.value = 0.9;
      const ng = this.envGain(landAt, 0.003, 0.04 + r() * 0.025, L.body * 0.16, 5);
      n.connect(lp).connect(ng).connect(out);
      voice.nodes.push(lp, ng);
      this.startSource(n, landAt, 0.08);
    }

    // 3) crinkle grains ------------------------------------------------------
    {
      const count = 2 + Math.floor(r() * 4); // 2..5
      const hp = ctx.createBiquadFilter();
      hp.type = 'bandpass';
      hp.frequency.value = (3200 + r() * 2600) * Math.sqrt(pitch);
      hp.Q.value = 0.8 + r() * 0.8;
      hp.connect(out);
      voice.nodes.push(hp);
      for (let i = 0; i < count; i++) {
        const at = t0 + swishLen * (0.08 + r() * 0.85);
        const len = 0.004 + r() * 0.009;
        const src = this.noiseSource(this.crackle!, voice);
        const g = this.envGain(at, 0.0015, len, L.grain * (0.3 + r() * 0.35), 3);
        src.connect(g).connect(hp);
        voice.nodes.push(g);
        this.startSource(src, at, len + 0.004);
      }
    }

    // 4) ending: double settle tick (up) / soft pat (flat) ------------------
    if (up) {
      const tickF = (2000 + r() * 900) * pitch;
      const t1 = landAt + 0.055 + r() * 0.03;
      const t2 = t1 + 0.06 + r() * 0.035;
      this.tick(voice, t1, tickF, L.end * (0.6 + r() * 0.2));
      this.tick(voice, t2, tickF * (0.9 + r() * 0.15), L.end * (0.3 + r() * 0.15));
    } else {
      const at = t0 + swishLen + 0.005 + r() * 0.02;
      const n = this.noiseSource(this.pickPink(), voice);
      const lp = ctx.createBiquadFilter();
      lp.type = 'lowpass';
      lp.frequency.value = (700 + r() * 500) * pitch;
      const len = 0.035 + r() * 0.02;
      const g = this.envGain(at, 0.004, len, L.end * (0.3 + r() * 0.1), 4);
      n.connect(lp).connect(g).connect(out);
      voice.nodes.push(lp, g);
      this.startSource(n, at, len + 0.01);
    }

    this.updateDuck(t0);
  }

  step(foot: 0 | 1, speed01: number, time?: number): void {
    const ctx = this.ready();
    if (!ctx || !this.master) return;
    const r = this.rng;
    const s = clamp(speed01, 0, 1);
    const t0 = time ?? ctx.currentTime + 0.004;
    const footPitch = foot === 0 ? 1 : 0.93;
    const pitch = footPitch * (0.94 + r() * 0.12);
    const len = 0.03 + r() * 0.018 + (1 - s) * 0.008;
    const level = (0.22 + 0.16 * s) * (0.85 + r() * 0.3);
    const pan = (foot === 0 ? -0.08 : 0.08) + (r() - 0.5) * 0.04;
    const voice = this.allocVoice(t0, t0 + len + 0.03, level, pan);
    const out = voice.out;

    // papery tap: band-passed noise
    const n = this.noiseSource(this.pickPink(), voice);
    const bp = ctx.createBiquadFilter();
    bp.type = 'bandpass';
    bp.frequency.setValueAtTime((900 + 500 * s + r() * 300) * pitch, t0);
    bp.frequency.exponentialRampToValueAtTime((520 + r() * 150) * pitch, t0 + len);
    bp.Q.value = 0.9 + r() * 0.5;
    const g = this.envGain(t0, 0.003 + r() * 0.002, len, 1.0, 4.5);
    n.connect(bp).connect(g).connect(out);
    voice.nodes.push(bp, g);
    this.startSource(n, t0, len + 0.01);

    // tiny soft body
    const osc = ctx.createOscillator();
    osc.type = 'sine';
    const bf = (145 + r() * 30) * pitch;
    osc.frequency.setValueAtTime(bf * 1.25, t0);
    osc.frequency.exponentialRampToValueAtTime(bf, t0 + 0.02);
    const og = this.envGain(t0, 0.003, 0.028, 0.14, 4);
    osc.connect(og).connect(out);
    voice.nodes.push(og);
    voice.sources.push(osc);
    osc.start(t0);
    osc.stop(t0 + 0.05);

    // occasional single crinkle grain
    if (r() < 0.45) {
      const at = t0 + 0.004 + r() * 0.012;
      const src = this.noiseSource(this.crackle!, voice);
      const hp = ctx.createBiquadFilter();
      hp.type = 'highpass';
      hp.frequency.value = 3000 + r() * 2000;
      const cg = this.envGain(at, 0.001, 0.006, 0.12 + r() * 0.1, 3);
      src.connect(hp).connect(cg).connect(out);
      voice.nodes.push(hp, cg);
      this.startSource(src, at, 0.012);
    }

    this.updateDuck(t0);
  }

  setMasterVolume(v: number): void {
    this.masterVolume = clamp(v, 0, 1);
    if (this.ctx && this.master) {
      const t = this.ctx.currentTime;
      this.master.gain.cancelScheduledValues(t);
      this.master.gain.setTargetAtTime(this.masterVolume, t, 0.04);
    }
  }

  dispose(): void {
    for (const v of this.voices) this.killVoice(v, true);
    this.voices = [];
    for (const n of this.busNodes) n.disconnect();
    this.busNodes = [];
    this.master = null;
    this.duck = null;
    if (this.ownsContext && this.ctx && typeof AudioContext !== 'undefined' && this.ctx instanceof AudioContext) {
      void this.ctx.close().catch(() => undefined);
    }
    this.ctx = null;
    this.white = [];
    this.pink = [];
    this.crackle = null;
  }

  /** Number of voices still sounding (for tests / debug overlays). */
  get activeVoices(): number {
    return this.voices.length;
  }

  // ---------------------------------------------------------------- internals

  private ready(): BaseAudioContext | null {
    const c = this.ctx;
    if (!c) return null;
    // A suspended realtime context would queue sounds and blurt them out on resume: skip.
    if (typeof AudioContext !== 'undefined' && c instanceof AudioContext && c.state !== 'running') return null;
    return c;
  }

  private build(): void {
    const ctx = this.ctx!;
    this.master = ctx.createGain();
    this.master.gain.value = this.masterVolume;
    this.duck = ctx.createGain();
    this.duck.gain.value = 1;
    const hp = ctx.createBiquadFilter();
    hp.type = 'highpass';
    hp.frequency.value = 35;
    hp.Q.value = 0.6;
    const lp = ctx.createBiquadFilter();
    lp.type = 'lowpass';
    lp.frequency.value = 9000;
    lp.Q.value = 0.5;
    const comp = ctx.createDynamicsCompressor();
    comp.threshold.value = -22;
    comp.knee.value = 12;
    comp.ratio.value = 3;
    comp.attack.value = 0.004;
    comp.release.value = 0.18;
    const out = ctx.createGain();
    out.gain.value = 0.7; // quiet overall: calm toy
    this.master.connect(this.duck).connect(hp).connect(lp).connect(comp).connect(out).connect(ctx.destination);
    this.busNodes = [this.master, this.duck, hp, lp, comp, out];
    this.makeBuffers();
  }

  private makeBuffers(): void {
    const ctx = this.ctx!;
    const sr = ctx.sampleRate;
    const len = Math.floor(sr * 1.0);
    const r = makeRng(0xc0ffee); // buffers are fixed; variation comes from offsets

    const removeDc = (d: Float32Array) => {
      let m = 0;
      for (let i = 0; i < d.length; i++) m += d[i];
      m /= d.length;
      for (let i = 0; i < d.length; i++) d[i] -= m;
    };

    this.white = [];
    this.pink = [];
    for (let b = 0; b < 3; b++) {
      const buf = ctx.createBuffer(1, len, sr);
      const d = buf.getChannelData(0);
      for (let i = 0; i < len; i++) d[i] = (r() * 2 - 1) * 0.5;
      removeDc(d);
      this.white.push(buf);
    }
    for (let b = 0; b < 3; b++) {
      // Paul Kellet pink noise (economy), slightly brighter than pure pink — paper air
      const buf = ctx.createBuffer(1, len, sr);
      const d = buf.getChannelData(0);
      let b0 = 0, b1 = 0, b2 = 0;
      for (let i = 0; i < len; i++) {
        const w = r() * 2 - 1;
        b0 = 0.99765 * b0 + w * 0.099046;
        b1 = 0.963 * b1 + w * 0.2965164;
        b2 = 0.57 * b2 + w * 1.0526913;
        d[i] = (b0 + b1 + b2 + w * 0.1848) * 0.16;
      }
      removeDc(d);
      this.pink.push(buf);
    }
    // crackle: sparse random spikes with tiny decays (paper fibres snapping)
    {
      const buf = ctx.createBuffer(1, len, sr);
      const d = buf.getChannelData(0);
      let env = 0;
      let sign = 1;
      for (let i = 0; i < len; i++) {
        if (r() < 0.012) {
          env = 0.4 + r() * 0.6;
          sign = r() < 0.5 ? -1 : 1;
        }
        env *= 0.86;
        d[i] = sign * env * (r() * 2 - 1);
      }
      removeDc(d);
      this.crackle = buf;
    }
  }

  private pickPink(): AudioBuffer {
    let i = Math.floor(this.rng() * this.pink.length);
    if (i === this.lastBufferIndex) i = (i + 1) % this.pink.length;
    this.lastBufferIndex = i;
    return this.pink[i];
  }

  private pickWhite(): AudioBuffer {
    return this.white[Math.floor(this.rng() * this.white.length)];
  }

  private noiseSource(buf: AudioBuffer, voice: Voice): AudioBufferSourceNode {
    const src = this.ctx!.createBufferSource();
    src.buffer = buf;
    src.playbackRate.value = 0.92 + this.rng() * 0.16;
    voice.sources.push(src);
    return src;
  }

  private startSource(src: AudioBufferSourceNode, at: number, dur: number): void {
    const buf = src.buffer!;
    const maxOff = Math.max(0, buf.duration - dur - 0.05);
    src.start(at, this.rng() * maxOff, dur + 0.01);
  }

  /**
   * Gain node with a click-free envelope curve: 0 -> peak (attack, sine-shaped) -> decays to exactly 0.
   * `shape` controls how fast the decay falls (higher = shorter body, longer faint tail).
   */
  private envGain(at: number, attack: number, total: number, peak: number, shape: number): GainNode {
    const g = this.ctx!.createGain();
    g.gain.value = 0;
    const curve = new Float32Array(CURVE_POINTS);
    const atkFrac = clamp(attack / total, 0.02, 0.5);
    const floor = Math.exp(-shape);
    for (let i = 0; i < CURVE_POINTS; i++) {
      const x = i / (CURVE_POINTS - 1);
      let v: number;
      if (x <= atkFrac) {
        v = Math.sin((x / atkFrac) * Math.PI * 0.5);
      } else {
        const y = (x - atkFrac) / (1 - atkFrac);
        // exponential decay minus a linear term so it lands on exactly 0 at the end (monotone)
        v = Math.max(0, Math.exp(-shape * y) - floor * y);
      }
      curve[i] = v * peak;
    }
    curve[0] = 0;
    curve[CURVE_POINTS - 1] = 0;
    g.gain.setValueCurveAtTime(curve, at, total);
    return g;
  }

  private tick(voice: Voice, at: number, freq: number, peak: number): void {
    const ctx = this.ctx!;
    const src = this.noiseSource(this.pickWhite(), voice);
    const bp = ctx.createBiquadFilter();
    bp.type = 'bandpass';
    bp.frequency.value = freq;
    bp.Q.value = 1.6 + this.rng() * 1.2;
    const len = 0.007 + this.rng() * 0.005;
    const g = this.envGain(at, 0.0012, len, peak, 3);
    src.connect(bp).connect(g).connect(voice.out);
    voice.nodes.push(bp, g);
    this.startSource(src, at, len + 0.004);
  }

  private allocVoice(start: number, end: number, level: number, pan: number): Voice {
    const ctx = this.ctx!;
    this.reap(start);
    while (this.voices.length >= this.maxVoices) {
      // drop the quietest: level weighted by how much of it is still to come
      let qi = 0;
      let qs = Infinity;
      for (let i = 0; i < this.voices.length; i++) {
        const v = this.voices[i];
        const remain = clamp((v.end - start) / (v.end - v.start), 0, 1);
        const score = v.level * remain * remain;
        if (score < qs) {
          qs = score;
          qi = i;
        }
      }
      const victim = this.voices.splice(qi, 1)[0];
      this.fadeOutVoice(victim, start);
    }
    const out = ctx.createGain();
    out.gain.value = level;
    const panner = ctx.createStereoPanner();
    panner.pan.value = pan;
    out.connect(panner).connect(this.master!);
    const voice: Voice = { start, end, level, out, sources: [], nodes: [panner], dead: false };
    this.voices.push(voice);
    // clean up node graph after it finishes (realtime only; offline graph is thrown away)
    if (typeof AudioContext !== 'undefined' && ctx instanceof AudioContext) {
      const cleanupDelayMs = Math.max(0, (end - ctx.currentTime) * 1000 + 120);
      setTimeout(() => this.killVoice(voice, false), cleanupDelayMs);
    }
    return voice;
  }

  private reap(now: number): void {
    if (!this.voices.length) return;
    this.voices = this.voices.filter((v) => v.end > now && !v.dead);
  }

  /** Steal: 15 ms ramp to 0 then stop the sources. */
  private fadeOutVoice(v: Voice, at: number): void {
    const g = v.out.gain;
    g.cancelScheduledValues(at);
    g.setValueAtTime(v.level, at);
    g.linearRampToValueAtTime(0, at + 0.015);
    for (const s of v.sources) {
      try {
        s.stop(at + 0.02);
      } catch {
        /* already stopped */
      }
    }
    v.end = Math.min(v.end, at + 0.02);
  }

  private killVoice(v: Voice, immediate: boolean): void {
    if (v.dead) return;
    v.dead = true;
    if (immediate && this.ctx) {
      const t = this.ctx.currentTime;
      try {
        v.out.gain.cancelScheduledValues(t);
        v.out.gain.setValueAtTime(v.out.gain.value, t);
        v.out.gain.linearRampToValueAtTime(0, t + 0.01);
      } catch {
        /* context closed */
      }
    }
    const disconnectAll = () => {
      for (const s of v.sources) s.disconnect();
      for (const n of v.nodes) n.disconnect();
      v.out.disconnect();
    };
    if (immediate) setTimeout(disconnectAll, 30);
    else disconnectAll();
    const i = this.voices.indexOf(v);
    if (i >= 0) this.voices.splice(i, 1);
  }

  /** Lower the bus when many voices overlap; recover once they end. */
  private updateDuck(at: number): void {
    if (!this.duck) return;
    let sum = 0;
    let lastEnd = at;
    for (const v of this.voices) {
      const remain = clamp((v.end - at) / (v.end - v.start), 0, 1);
      sum += v.level * remain;
      if (v.end > lastEnd) lastEnd = v.end;
    }
    // energy-ish loudness of the overlap relative to one full flap at gain 1 (0.55)
    const load = sum / 0.55;
    const target = load <= 1.2 ? 1 : clamp(1 / Math.sqrt(load / 1.2), 0.4, 1);
    const g = this.duck.gain;
    g.cancelScheduledValues(at);
    g.setTargetAtTime(target, at, 0.012);
    g.setTargetAtTime(1, Math.max(at + 0.05, lastEnd - 0.1), 0.18);
  }
}
