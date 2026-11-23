// Browser check of the web build: load, screenshot the shelf, tap a book, screenshot the tale.
//   node tools/web/web_check.mjs <url> <outdir> [desktop|ipad] [chromium|webkit] [tapX,tapY (0..1)] [tag]
// Prints load time, console WEB_PERF lines (Godot GPU memory) and Chrome JS heap.
import { chromium, webkit } from "playwright";
import fs from "fs";
const [url, out, mode = "desktop", engine = "chromium", tap = "0.32,0.22", tag = ""] = process.argv.slice(2);
fs.mkdirSync(out, { recursive: true });
const ipad = mode === "ipad";
const ctxOpt = ipad
  ? { viewport: { width: 1180, height: 820 }, deviceScaleFactor: 2, isMobile: engine === "webkit", hasTouch: true,
      userAgent: "Mozilla/5.0 (iPad; CPU OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1" }
  : { viewport: { width: 1366, height: 1024 }, deviceScaleFactor: 1 };
const b = await (engine === "webkit" ? webkit : chromium).launch(
  engine === "webkit" ? {} : { channel: "chrome", args: ["--enable-gpu", "--ignore-gpu-blocklist", "--use-angle=metal"] });
const ctx = await b.newContext(ctxOpt);
const page = await ctx.newPage();
const logs = [];
page.on("console", (m) => { const t = m.text(); logs.push(t); if (/WEB_PERF|ERROR|rror|WebGL|OpenGL|PERF/.test(t)) console.log("console:", t.slice(0, 300)); });
page.on("pageerror", (e) => console.log("pageerror:", e.message));
const t0 = Date.now();
await page.goto(url, { waitUntil: "load", timeout: 120000 });
// Godot hides the status overlay once the engine starts
await page.waitForFunction(() => { const s = document.getElementById("status"); return !s || s.style.display === "none" || s.style.visibility === "hidden" || getComputedStyle(s).display === "none"; }, null, { timeout: 300000 });
const tBoot = (Date.now() - t0) / 1000;
console.log(`boot ${tBoot.toFixed(1)} s`);
const heap = async (label) => {
  if (engine !== "chromium") return;
  const cdp = await ctx.newCDPSession(page);
  await cdp.send("Performance.enable");
  const m = (await cdp.send("Performance.getMetrics")).metrics;
  const g = (n) => (m.find((x) => x.name === n)?.value || 0) / 1048576;
  console.log(`${label}: JSHeapUsed=${g("JSHeapUsedSize").toFixed(0)} MB JSHeapTotal=${g("JSHeapTotalSize").toFixed(0)} MB`);
};
await page.waitForTimeout(12000);
await page.screenshot({ path: `${out}/${tag}${mode}_${engine}_1_shelf.png` });
await heap("shelf");
const [fx, fy] = tap.split(",").map(Number);
const vw = ctxOpt.viewport.width, vh = ctxOpt.viewport.height;
if (ipad) await page.touchscreen.tap(fx * vw, fy * vh); else await page.mouse.click(fx * vw, fy * vh);
for (const [s, n] of [[6, "2_open"], [14, "3_page"], [14, "4_page_later"]]) {
  await page.waitForTimeout(s * 1000);
  await page.screenshot({ path: `${out}/${tag}${mode}_${engine}_${n}.png` });
}
await heap("tale");
// a tap in the middle (taps drive the story)
if (ipad) await page.touchscreen.tap(vw * 0.5, vh * 0.55); else await page.mouse.click(vw * 0.5, vh * 0.55);
await page.waitForTimeout(8000);
await page.screenshot({ path: `${out}/${tag}${mode}_${engine}_5_after_tap.png` });
await heap("end");
fs.writeFileSync(`${out}/${tag}${mode}_${engine}_console.txt`, logs.join("\n"));
await b.close();
