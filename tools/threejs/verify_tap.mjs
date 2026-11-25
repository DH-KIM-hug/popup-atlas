// Real input on the three.js player (docs/THREEJS.md):
//   node tools/threejs/verify_tap.mjs <base url> <outdir> [webkit|chromium] [taps=3]
// Opens the shelf like a reader, taps the turnip book (the gesture that unlocks audio), waits at the cover and taps
// the book open, then at each tap step waits for the ring, screenshots it, taps a point OUTSIDE the ring (the story
// must keep waiting), then the ring itself (the story must go on). Reports audio context state + clips started.
import { chromium, webkit } from 'playwright';
import fs from 'fs';
const [base, out, engine = 'webkit', nTaps = '3'] = process.argv.slice(2);
fs.mkdirSync(out, { recursive: true });
const b = await (engine === 'webkit' ? webkit : chromium).launch(engine === 'webkit' ? { headless: false } : { channel: 'chrome', headless: false, args: ['--use-angle=metal'] });
const ctx = await b.newContext({ viewport: { width: 1180, height: 820 }, deviceScaleFactor: 2, hasTouch: true, isMobile: engine === 'webkit' });
const page = await ctx.newPage();
const errs = [];
page.on('pageerror', (e) => errs.push(e.message));
await page.goto(base);
await page.waitForFunction(() => window.__app && window.__app.shelf, null, { timeout: 60000 });
await page.waitForTimeout(800);
await page.screenshot({ path: `${out}/${engine}_0_shelf.png` });
const box = await page.locator('.book[data-tale="turnip"] .board').boundingBox();
await page.touchscreen.tap(box.x + box.width / 2, box.y + box.height / 2);
await page.waitForFunction(() => window.__pilot && window.__pilot.ready && window.__pilot.holding() === 'cover', null, { timeout: 120000 });
await page.waitForTimeout(600);
await page.screenshot({ path: `${out}/${engine}_1_cover.png` });
const res = { engine, cover: null, taps: [], errs };
const a0 = await page.evaluate(() => window.__pilot.audio);
await page.touchscreen.tap(590, 410);
await page.waitForTimeout(500);
res.cover = { audioBefore: a0, holdingAfter: await page.evaluate(() => window.__pilot.holding()) };
for (let k = 0; k < Number(nTaps); k++) {
  await page.waitForFunction(() => window.__pilot.holding() === 'tap', null, { timeout: 120000 });
  await page.waitForTimeout(700);
  const ring = await page.evaluate(() => window.__pilot.ringAt());
  await page.screenshot({ path: `${out}/${engine}_${2 + k}_ring.png` });
  const t0 = await page.evaluate(() => window.__pilot.t);
  // outside the ring: nothing happens
  const ox = ring.x > 590 ? ring.x - ring.r * 3 : ring.x + ring.r * 3;
  await page.touchscreen.tap(Math.max(5, Math.min(1175, ox)), ring.y);
  await page.waitForTimeout(500);
  const stillWaiting = await page.evaluate(() => window.__pilot.holding() === 'tap');
  await page.touchscreen.tap(ring.x, ring.y);
  await page.waitForTimeout(1200);
  const after = await page.evaluate(() => ({ t: window.__pilot.t, holding: window.__pilot.holding(), audio: window.__pilot.audio }));
  res.taps.push({ target: ring.target, ring: [Math.round(ring.x), Math.round(ring.y), Math.round(ring.r)], heldAt: +t0.toFixed(2), outsideTapIgnored: stillWaiting,
    wentOn: after.t > t0 + 0.5, tAfter: +after.t.toFixed(2), audio: after.audio });
}
fs.writeFileSync(`${out}/${engine}_verify_tap.json`, JSON.stringify(res, null, 1));
console.log(JSON.stringify(res));
await b.close();
