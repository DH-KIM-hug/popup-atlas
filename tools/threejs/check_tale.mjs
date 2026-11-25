// Plays a whole tale in autoplay and checks it (docs/THREEJS.md):
//   node tools/threejs/check_tale.mjs <base url> <tale> <outdir> [webkit|chromium] [ipad|desktop]
// Opens <base>?tale=<tale>&auto=1 (taps simulated 1 s into each wait, holds held, like Godot autoplay), waits for the
// end, writes <outdir>/<tale>_<engine>.json: bytes on the wire, first frame / ready time, fps median + p5 over the
// playing part (waits excluded), GPU memory estimate, draw calls, the line check (every line Godot said, in order,
// with its voice clip decoded and started), the audio meter (output RMS: loud time), stalls (playhead waiting for
// a chunk), errors. Exit code 1 when the tale did not reach its end or a line is missing.
import { chromium, webkit } from 'playwright';
import fs from 'fs';

const [base, tale, out, engine = 'webkit', mode = 'ipad'] = process.argv.slice(2);
fs.mkdirSync(out, { recursive: true });
const ipad = mode === 'ipad';
const ctxOpt = ipad
  ? { viewport: { width: 1180, height: 820 }, deviceScaleFactor: 2, isMobile: engine === 'webkit', hasTouch: true }
  : { viewport: { width: 1366, height: 1024 }, deviceScaleFactor: 1 };
const b = await (engine === 'webkit' ? webkit : chromium).launch(engine === 'webkit'
  ? { headless: false }
  : { channel: 'chrome', headless: false, args: ['--enable-gpu', '--ignore-gpu-blocklist', '--use-angle=metal', '--autoplay-policy=no-user-gesture-required'] });
const ctx = await b.newContext(ctxOpt);
const page = await ctx.newPage();
const errors = [];
let wire = 0, nReq = 0;
page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text().slice(0, 300)); });
page.on('pageerror', (e) => errors.push('pageerror: ' + e.message));
page.on('requestfinished', async (rq) => {
  try { const s = await rq.sizes(); wire += s.responseBodySize + s.responseHeadersSize; nReq++; } catch (e) { /* gone */ }
});
const sep = base.includes('?') ? '&' : '?';
const t0 = Date.now();
await page.goto(`${base}${sep}tale=${tale}&auto=1`, { waitUntil: 'load', timeout: 120000 });
await page.waitForFunction(() => window.__pilot && (window.__pilot.ready || window.__pilot.errors.length), null, { timeout: 120000 });
const readyS = (Date.now() - t0) / 1000;
// a tap on the page = the user gesture that unlocks audio (autoplay keeps playing; the tap lands before the first wait)
await page.mouse.click(5, 400);
const meter = { loudMs: 0, peak: 0, samples: 0 };
const iv = setInterval(async () => {
  try {
    const l = await page.evaluate(() => (window.__audioLevel ? window.__audioLevel() : 0));
    meter.samples++; meter.peak = Math.max(meter.peak, l); if (l > 0.003) meter.loudMs += 500;
  } catch (e) { /* page busy */ }
}, 500);
const len = await page.evaluate(() => window.__pilot.timeline.tEnd);
let ok = true;
try {
  await page.waitForFunction(() => window.__pilot.state === 'done' || window.__pilot.errors.length > 3, null, { timeout: (len * 1.6 + 120) * 1000, polling: 1000 });
} catch (e) { ok = false; errors.push('timeout: ' + e.message.slice(0, 120)); }
clearInterval(iv);
const r = await page.evaluate(() => {
  const p = window.__pilot;
  const f = p.frames.slice(60).filter((x) => x > 0).sort((a, b) => a - b);
  const q = (k) => f[Math.min(f.length - 1, Math.floor(f.length * k))];
  const log = p.audioLog();
  return { state: p.state, t: p.t, doneAt: p.doneAt, firstFrameMs: p.firstFrameMs, loadMs: p.loadMs, bytes: p.bytes, gpuMB: p.gpuMB, texMB: p.texMB, geoMB: p.geoMB,
    info: p.info, fpsMedian: 1000 / q(0.5), fpsP5: 1000 / q(0.95), worstMs: f[f.length - 1], frames: f.length, stalls: p.stalls, stallMs: Math.round(p.stallMs),
    lineCheck: p.lineCheck, tapped: p.tapped, waits: p.waitList().length, audio: p.audio, clipsStarted: log.length, clipsNoBuffer: log.filter((x) => !x[1]).map((x) => x[0]).slice(0, 20),
    errors: p.errors, unknownShaders: p.unknownShaders() };
});
Object.assign(r, { tale, engine, mode, readyS, wireMB: +(wire / 1048576).toFixed(2), requests: nReq, meter, consoleErrors: errors.slice(0, 20), reachedEnd: ok && r.state === 'done' });
fs.writeFileSync(`${out}/${tale}_${engine}.json`, JSON.stringify(r, null, 1));
const lc = r.lineCheck || {};
console.log(JSON.stringify({ tale, engine, end: r.reachedEnd, wireMB: r.wireMB, readyS, firstFrameMs: r.firstFrameMs, fps: r.fpsMedian?.toFixed(1), p5: r.fpsP5?.toFixed(1),
  gpuMB: r.gpuMB, calls: r.info?.calls, lines: `${lc.webLines}/${lc.voicedLines} inOrder=${lc.inOrder}`, missing: lc.missing, noBuffer: lc.noBuffer, waits: r.waits,
  taps: r.tapped.length, loudS: meter.loudMs / 1000, stalls: r.stalls, errors: r.errors.concat(errors).slice(0, 5) }));
await b.close();
process.exit(r.reachedEnd && lc.inOrder ? 0 : 1);
