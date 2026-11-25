// Quick look: node tools/threejs/shot.mjs <url> <outdir> t1,t2,... [chromium|webkit] [WxH]
// Opens the url (add ?tale=..), waits for the tale, seeks to each record time (holds there) and screenshots.
import { chromium, webkit } from 'playwright';
import fs from 'fs';
const [url, out, ts = '5', engine = 'chromium', size = '1366x1024'] = process.argv.slice(2);
const [W, H] = size.split('x').map(Number);
fs.mkdirSync(out, { recursive: true });
const b = await (engine === 'webkit' ? webkit : chromium).launch(engine === 'webkit' ? { headless: false } : { channel: 'chrome', headless: false, args: ['--use-angle=metal', '--ignore-gpu-blocklist'] });
const page = await (await b.newContext({ viewport: { width: W, height: H } })).newPage();
page.on('console', (m) => { if (m.type() === 'error' || m.type() === 'warning') console.log('console:', m.text().slice(0, 400)); });
page.on('response', (r) => { if (r.status() >= 400) console.log('http', r.status(), r.url()); });
page.on('pageerror', (e) => console.log('pageerror:', e.message));
await page.goto(url);
await page.waitForFunction(() => window.__pilot && (window.__pilot.ready || window.__pilot.errors.length), null, { timeout: 120000 });
console.log(JSON.stringify(await page.evaluate(() => ({ e: window.__pilot.errors, load: window.__pilot.loadMs, first: window.__pilot.firstFrameMs, waits: window.__pilot.waitList() }))));
for (const t of ts.split(',').map(Number)) {
  const r = await page.evaluate((tt) => window.__pilot.seek(tt), t);
  await page.waitForTimeout(900);
  await page.screenshot({ path: `${out}/three_t${t.toFixed(1).padStart(5, '0')}.png` });
  console.log(t, JSON.stringify(r));
}
console.log(JSON.stringify(await page.evaluate(() => ({ info: window.__pilot.info, gpu: window.__pilot.gpuMB, u: window.__pilot.unknownShaders(), e: window.__pilot.errors }))));
await b.close();
