// fps probe: node tools/threejs/fps_probe.mjs <url> [webkit|chromium] [seconds]  (iPad viewport @2x, autoplay)
import { chromium, webkit } from 'playwright';
const [url, engine = 'webkit', secs = '20'] = process.argv.slice(2);
const b = await (engine === 'webkit' ? webkit : chromium).launch(engine === 'webkit' ? { headless: false } : { channel: 'chrome', headless: false, args: ['--use-angle=metal', '--ignore-gpu-blocklist'] });
const page = await (await b.newContext({ viewport: { width: 1180, height: 820 }, deviceScaleFactor: 2 })).newPage();
await page.goto(url);
await page.waitForFunction(() => window.__pilot && window.__pilot.ready, null, { timeout: 120000 });
await page.waitForTimeout(3000);
await page.evaluate(() => { window.__pilot.frames.length = 0; });
await page.waitForTimeout(Number(secs) * 1000);
console.log(JSON.stringify(await page.evaluate(() => { const f = window.__pilot.frames.filter((x) => x > 0).sort((a, b) => a - b); const q = (k) => f[Math.floor(f.length * k)];
  return { n: f.length, fps: +(1000 / q(0.5)).toFixed(1), p5: +(1000 / q(0.95)).toFixed(1), info: window.__pilot.info, gpu: window.__pilot.gpuMB, t: window.__pilot.t }; })));
await b.close();
