// Quick look: node tools/threejs_pilot/shot.mjs <url> <outdir> t1,t2,... [chromium|webkit]  (1366x1024, seek + screenshot)
import { chromium, webkit } from 'playwright';
import fs from 'fs';
const [url, out, ts = '5', engine = 'chromium'] = process.argv.slice(2);
fs.mkdirSync(out, { recursive: true });
const b = await (engine === 'webkit' ? webkit : chromium).launch(engine === 'webkit' ? { headless: false } : { channel: 'chrome', headless: false, args: ['--use-angle=metal', '--ignore-gpu-blocklist'] });
const page = await (await b.newContext({ viewport: { width: 1366, height: 1024 } })).newPage();
page.on('console', (m) => { if (m.type() === 'error' || m.type() === 'warning') console.log('console:', m.text().slice(0, 400)); });
page.on('response', (r) => { if (r.status() >= 400) console.log('http', r.status(), r.url()); });
page.on('pageerror', (e) => console.log('pageerror:', e.message));
await page.goto(url + (url.includes('?') ? '&' : '?') + 'auto');
await page.waitForFunction(() => window.__pilot && (window.__pilot.ready || window.__pilot.errors.length), null, { timeout: 120000 });
console.log(JSON.stringify(await page.evaluate(() => ({ e: window.__pilot.errors, u: window.__pilot.unknownShaders, load: window.__pilot.loadMs, tl: window.__pilot.timeline }))));
for (const t of ts.split(',').map(Number)) {
  await page.evaluate((tt) => window.__pilot.seek(tt), t);
  await page.waitForTimeout(800);
  await page.screenshot({ path: `${out}/three_t${t.toFixed(1).padStart(5, '0')}.png` });
}
console.log(JSON.stringify(await page.evaluate(() => ({ info: window.__pilot.info, gpu: window.__pilot.gpuMB }))));
await b.close();
