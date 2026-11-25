// three.js pilot measurements (docs/THREEJS_PILOT.md).
//   node tools/threejs_pilot/measure.mjs <url> <outdir> [chromium|webkit] [ipad|desktop] [shots=t1,t2,..]
// Loads <url>?auto (start overlay skipped, the seed tap simulated after 1 s like Godot autoplay), waits for the
// whole beat, and writes <outdir>/<engine>_<mode>.json: load time, bytes, fps median / p5 over the playing part,
// JS heap (Chrome: CDP; WebKit: n/a), renderer.info (draw calls, triangles, textures), GPU memory estimate,
// screenshots at the given record times (seek + hold, for the compare sheet).
import { chromium, webkit } from 'playwright';
import fs from 'fs';

const [url, out, engine = 'chromium', mode = 'ipad', shotsArg = ''] = process.argv.slice(2);
fs.mkdirSync(out, { recursive: true });
const ipad = mode === 'ipad';
const ctxOpt = ipad
  ? { viewport: { width: 1180, height: 820 }, deviceScaleFactor: 2, isMobile: engine === 'webkit', hasTouch: true,
      userAgent: 'Mozilla/5.0 (iPad; CPU OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1' }
  : { viewport: { width: 1366, height: 1024 }, deviceScaleFactor: 1 };
const b = await (engine === 'webkit' ? webkit : chromium).launch(engine === 'webkit'
  ? { headless: false }
  : { channel: 'chrome', headless: false, args: ['--enable-gpu', '--ignore-gpu-blocklist', '--use-angle=metal', '--autoplay-policy=no-user-gesture-required'] });
const ctx = await b.newContext(ctxOpt);
const page = await ctx.newPage();
const errors = [];
const bytes = { total: 0, n: 0 };
page.on('console', (m) => { if (m.type() === 'error' || m.type() === 'warning') errors.push(m.text().slice(0, 300)); });
page.on('pageerror', (e) => errors.push('pageerror: ' + e.message));
page.on('response', async (r) => {
  try { const h = await r.allHeaders(); const n = Number(h['content-length'] || 0); bytes.total += n; bytes.n++; } catch (e) { /* ignore */ }
});
const sep = url.includes('?') ? '&' : '?';
const t0 = Date.now();
await page.goto(url + sep + 'auto', { waitUntil: 'load', timeout: 120000 });
await page.waitForFunction(() => window.__pilot && (window.__pilot.ready || window.__pilot.errors.length), null, { timeout: 300000 });
const tReady = (Date.now() - t0) / 1000;
const heap = async () => {
  if (engine !== 'chromium') return null;
  const cdp = await ctx.newCDPSession(page);
  await cdp.send('Performance.enable');
  const m = (await cdp.send('Performance.getMetrics')).metrics;
  return Math.round((m.find((x) => x.name === 'JSHeapUsedSize')?.value || 0) / 1048576);
};
// play the whole beat (tap simulated); frame intervals from the page
await page.evaluate(() => { window.__pilot.frames.length = 0; });
await page.waitForFunction(() => window.__pilot.state === 'done' || window.__pilot.errors.length, null, { timeout: 180000 });
const r = await page.evaluate(() => {
  const p = window.__pilot;
  const f = p.frames.slice(30).filter((x) => x > 0).sort((a, b) => a - b);
  const q = (k) => f[Math.min(f.length - 1, Math.floor(f.length * k))];
  return { loadMs: p.loadMs, bytes: p.bytes, texMB: p.texMB, geoMB: p.geoMB, gpuMB: p.gpuMB, info: p.info, errors: p.errors,
    unknownShaders: p.unknownShaders, frames: f.length, fpsMedian: 1000 / q(0.5), fpsP5: 1000 / q(0.95), worstMs: f[f.length - 1],
    timeline: p.timeline, tapAt: p.tapAt };
});
r.heapMB = await heap();
r.readyS = tReady;
r.netBytes = bytes;
r.engine = engine; r.mode = mode; r.url = url;
r.consoleErrors = errors.slice(0, 20);
// screenshots at record times
for (const t of shotsArg.split(',').filter(Boolean).map(Number)) {
  await page.evaluate((tt) => window.__pilot.seek(tt), t);
  await page.waitForTimeout(700);
  await page.screenshot({ path: `${out}/three_${engine}_${mode}_t${t.toFixed(1).padStart(5, '0')}.png` });
}
fs.writeFileSync(`${out}/${engine}_${mode}.json`, JSON.stringify(r, null, 1));
console.log(JSON.stringify({ engine, mode, readyS: r.readyS, loadMs: r.loadMs, fpsMedian: r.fpsMedian?.toFixed(1), fpsP5: r.fpsP5?.toFixed(1),
  heapMB: r.heapMB, gpuMB: r.gpuMB, texMB: r.texMB, calls: r.info?.calls, tris: r.info?.triangles, net: (bytes.total / 1048576).toFixed(1) + 'MB', errors: r.errors }));
await b.close();
