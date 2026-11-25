// Real-input check: open <url> (no ?auto), tap the start card, wait for the seed ring, tap it, check the story goes
// on and audio runs.   node tools/threejs_pilot/verify_tap.mjs <url> <outdir> [webkit|chromium]
import { chromium, webkit } from 'playwright';
import fs from 'fs';
const [url, out, engine = 'webkit'] = process.argv.slice(2);
fs.mkdirSync(out, { recursive: true });
const b = await (engine === 'webkit' ? webkit : chromium).launch(engine === 'webkit' ? { headless: false } : { channel: 'chrome', headless: false });
const ctx = await b.newContext({ viewport: { width: 1180, height: 820 }, deviceScaleFactor: 2, hasTouch: true, isMobile: engine === 'webkit' });
const page = await ctx.newPage();
page.on('pageerror', (e) => console.log('pageerror', e.message));
await page.goto(url);
await page.waitForFunction(() => window.__pilot && window.__pilot.ready, null, { timeout: 120000 });
await page.waitForTimeout(500);
await page.screenshot({ path: `${out}/${engine}_0_start.png` });
await page.touchscreen.tap(590, 410); // the start card
await page.waitForFunction(() => window.__pilot.holding, null, { timeout: 60000 });
await page.waitForTimeout(1500);
const ring = await page.evaluate(() => { const r = document.getElementById('ring'); return { x: +r.dataset.x, y: +r.dataset.y, r: +r.dataset.r, a: window.__pilot.audio }; });
await page.screenshot({ path: `${out}/${engine}_1_ring.png` });
await page.touchscreen.tap(ring.x, ring.y);
await page.waitForTimeout(1200);
const after = await page.evaluate(() => ({ t: window.__pilot.t, holding: window.__pilot.holding, tapAt: window.__pilot.tapAt, auto: window.__pilot.tapAuto, a: window.__pilot.audio }));
await page.waitForFunction(() => window.__pilot.state === 'done', null, { timeout: 30000 });
await page.screenshot({ path: `${out}/${engine}_2_done.png` });
console.log(JSON.stringify({ engine, ringAt: ring, after, done: true }));
await b.close();
