// Does sound play in the web build? (docs/WEB_BUILD.md, "Sound")
//   node tools/web/web_audio_check.mjs <url> [chromium|webkit] [desktop|ipad] [tapX,tapY 0..1] [seconds after the tap]
// Instruments Web Audio before the page loads: AudioContext states, AudioBufferSourceNode.start() calls (Godot's
// "Sample" playback), <audio> plays; taps a book on the shelf like a reader (the user gesture that unlocks audio)
// and prints the counts plus the console's VOICE / LINE lines. Exit code 1 when no source started after the tap.
import { chromium, webkit } from "playwright";
const [url, engine = "chromium", mode = "desktop", tap = "0.32,0.22", secs = "25"] = process.argv.slice(2);
const ipad = mode === "ipad";
const ctxOpt = ipad
  ? { viewport: { width: 1180, height: 820 }, deviceScaleFactor: 2, isMobile: engine === "webkit", hasTouch: true }
  : { viewport: { width: 1366, height: 1024 }, deviceScaleFactor: 1 };
const b = await (engine === "webkit" ? webkit : chromium).launch(
  engine === "webkit" ? {} : { channel: "chrome", args: ["--enable-gpu", "--ignore-gpu-blocklist", "--use-angle=metal"] });
const ctx = await b.newContext(ctxOpt);
const page = await ctx.newPage();
await page.addInitScript(() => {
  const A = { ctx: [], starts: 0, startsAfterTap: 0, media: 0, peak: 0, tapped: false, worklet: 0, loudMs: 0, rawPeak: 0, bufs: [], err: '' };
  window.__audio = A;
  const Orig = window.AudioContext || window.webkitAudioContext;
  if (Orig) {
    const Wrapped = function (...a) {
      const c = new Orig(...a);
      A.ctx.push(c);
      return c;
    };
    Wrapped.prototype = Orig.prototype;
    window.AudioContext = Wrapped;
    window.webkitAudioContext = Wrapped;
    // output meter: whatever feeds a destination also feeds an analyser; peak RMS over the run
    const conn = AudioNode.prototype.connect;
    // graph record (for --graph): node ids, edges, so a silent run can show where the signal stops
    let nid = 0;
    const id = (n) => (n.__id ??= ++nid);
    A.edges = new Map();
    A.nodes = new Map();
    const disc = AudioNode.prototype.disconnect;
    AudioNode.prototype.disconnect = function (...a) {
      const s = A.edges.get(id(this));
      if (s) { if (a.length && a[0] instanceof AudioNode) s.delete(id(a[0])); else if (!a.length || typeof a[0] === "number") s.clear(); }
      return disc.apply(this, a);
    };
    A.trace = () => {
      // from the most recent buffer source, walk every path; print node type (+ gain) per hop
      const out = [];
      const walk = (n, path, depth) => {
        const node = A.nodes.get(n);
        const lab = node.constructor.name.replace("Node", "") + (node.gain ? `(${node.gain.value.toFixed(3)})` : "") + `#${n}`;
        const p = path.concat(lab);
        const nx = [...(A.edges.get(n) || [])].filter((k) => !A.nodes.get(k).__meter);
        if (node instanceof AudioDestinationNode || !nx.length || depth > 14) { out.push(p.join(" > ")); return; }
        for (const k of nx) walk(k, p, depth + 1);
      };
      if (A.lastSrc) walk(A.lastSrc, [], 0);
      return out.slice(0, 8);
    };
    AudioNode.prototype.connect = function (dst, ...a) {
      if (!this.__meter) {
        A.nodes.set(id(this), this);
        if (dst instanceof AudioNode) { A.nodes.set(id(dst), dst); if (!A.edges.has(id(this))) A.edges.set(id(this), new Set()); A.edges.get(id(this)).add(id(dst)); }
      }
      if (dst instanceof AudioDestinationNode) {
        const c = this.context;
        if (!c.__an) {
          c.__an = c.createAnalyser(); c.__an.__meter = true;
          c.__an.fftSize = 2048;
          const z = c.createGain(); z.__meter = true;  // keep the analyser pulled by the graph, silently
          z.gain.value = 0;
          conn.call(c.__an, z);
          conn.call(z, c.destination);
          const buf = new Float32Array(2048);
          setInterval(() => {
            c.__an.getFloatTimeDomainData(buf);
            let e = 0;
            for (const v of buf) e += v * v;
            const r = Math.sqrt(e / buf.length);
            if (A.tapped && r > A.peak) A.peak = r;
            if (A.tapped && r > 0.003) A.loudMs += 100;
          }, 100);
        }
        conn.call(this, c.__an);
      }
      return conn.call(this, dst, ...a);
    };
    const st = AudioBufferSourceNode.prototype.start;
    AudioBufferSourceNode.prototype.start = function (...a) {
      A.starts++;
      A.lastSrc = this.__id;
      // raw source level (before Godot's bus gains): tells a silent buffer from a muted bus
      try {
        const c = this.context;
        if (!c.__raw) {
          c.__raw = c.createAnalyser(); c.__raw.__meter = true; c.__raw.fftSize = 2048;
          const z = c.createGain(); z.__meter = true; z.gain.value = 0; conn.call(c.__raw, z); conn.call(z, c.destination);
          const buf = new Float32Array(2048);
          setInterval(() => { c.__raw.getFloatTimeDomainData(buf); let e = 0; for (const v of buf) e += v * v;
            const r = Math.sqrt(e / buf.length); if (A.tapped && r > A.rawPeak) A.rawPeak = r; }, 100);
        }
        conn.call(this, c.__raw);
        A.bufs.push(this.buffer ? `${this.buffer.duration.toFixed(2)}s/${this.buffer.numberOfChannels}ch` : "none");
      } catch (e) { A.err = String(e); }
      if (A.tapped) A.startsAfterTap++;
      return st.apply(this, a);
    };
  }
  const pl = HTMLMediaElement.prototype.play;
  HTMLMediaElement.prototype.play = function () { A.media++; return pl.apply(this); };
});
const voice = [];
page.on("console", (m) => { const t = m.text(); if (/^(LINE|SOUND|VOICE|AUDIO|WEB_AUDIO)/.test(t)) voice.push(t.slice(0, 120)); });
page.on("pageerror", (e) => console.log("pageerror:", e.message));
await page.goto(url, { waitUntil: "load", timeout: 120000 });
await page.waitForFunction(() => { const s = document.getElementById("status"); return !s || getComputedStyle(s).display === "none" || s.style.visibility === "hidden"; }, null, { timeout: 300000 });
await page.waitForTimeout(10000);
const state = () => page.evaluate(() => ({ ctx: window.__audio.ctx.map((c) => c.state + "@" + c.sampleRate), starts: window.__audio.starts,
  after: window.__audio.startsAfterTap, media: window.__audio.media, meters: window.__audio.ctx.map((c) => !!c.__an), peakRms: +window.__audio.peak.toFixed(4), rawPeak: +window.__audio.rawPeak.toFixed(4), bufs: window.__audio.bufs.slice(0, 12).join(' '), voiceLen: window.__audio.bufs.filter((b) => { const d = parseFloat(b); return d >= 1 && d <= 10; }).length, err: window.__audio.err, loudMs: window.__audio.loudMs }));
console.log("before tap:", JSON.stringify(await state()));
await page.evaluate(() => { window.__audio.tapped = true; });
const [fx, fy] = tap.split(",").map(Number);
const vw = ctxOpt.viewport.width, vh = ctxOpt.viewport.height;
if (ipad) await page.touchscreen.tap(fx * vw, fy * vh); else await page.mouse.click(fx * vw, fy * vh);
await page.waitForTimeout(Number(secs) * 1000);
const s = await state();
console.log("after tap:", JSON.stringify(s));
if (process.env.GRAPH) console.log("paths from the last source:\n  " + (await page.evaluate(() => window.__audio.trace())).join("\n  "));
console.log(`console lines (${voice.length}):\n  ` + voice.slice(0, 12).join("\n  "));
await b.close();
process.exit(s.after > 0 && s.peakRms > 0.003 && s.ctx.some((c) => c.startsWith("running")) ? 0 : 1);
