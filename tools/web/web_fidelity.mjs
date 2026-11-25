// Web side of the web-vs-native comparison (docs/WEB_BUILD.md, "Fidelity check").
//   node tools/web/web_fidelity.mjs <base url> <outdir> [chromium|webkit] [desktop|ipad] [tale filter]
// For every moment in tools/web/fidelity_moments.json it opens <base>?tale=..&beat=..&autoplay=1&mute=1 (the loader turns
// the query into the desktop story-run args), waits for the beat's first "LINE" console line and screenshots t seconds
// after it.
// Files: <outdir>/<tale>_<beat>_<t>.png (same names as tools/web/fidelity_native.sh writes).
import { chromium, webkit } from "playwright";
import fs from "fs";
import path from "path";
const [base, out, engine = "chromium", mode = "desktop", only = ""] = process.argv.slice(2);
fs.mkdirSync(out, { recursive: true });
const moments = JSON.parse(fs.readFileSync(new URL("./fidelity_moments.json", import.meta.url))).moments
  .filter((m) => !only || only.split(",").includes(m.tale));
const ipad = mode === "ipad";
const ctxOpt = ipad
  ? { viewport: { width: 1180, height: 820 }, deviceScaleFactor: 2, isMobile: engine === "webkit", hasTouch: true }
  : { viewport: { width: 1366, height: 1024 }, deviceScaleFactor: 1 };
const b = await (engine === "webkit" ? webkit : chromium).launch(
  engine === "webkit" ? {} : { channel: "chrome", args: ["--enable-gpu", "--ignore-gpu-blocklist", "--use-angle=metal"] });
const ctx = await b.newContext(ctxOpt);
const sep = base.includes("?") ? "&" : "?";
for (const m of moments) {
  const page = await ctx.newPage();
  const logs = [];
  let beatSeen = false;
  let beatAt = 0;  // wall time of the beat's first spoken LINE (the build before it runs slower on the web)
  page.on("console", (msg) => {
    const t = msg.text();
    logs.push(t);
    if (t.startsWith(`BEAT ${m.beat} `)) beatSeen = true;
    if (beatSeen && !beatAt && t.startsWith("LINE ")) beatAt = Date.now();
    if (/ERROR|rror/.test(t)) console.log(`  ${m.tale}: ${t.slice(0, 200)}`);
  });
  page.on("pageerror", (e) => console.log("pageerror:", e.message));
  const t0 = Date.now();
  await page.goto(`${base}${sep}tale=${m.tale}&beat=${m.beat}&autoplay=1&mute=1`, { waitUntil: "load", timeout: 120000 });
  while (!beatAt && Date.now() - t0 < 240000) await page.waitForTimeout(100);
  if (!beatAt) { console.log(`${m.tale}/${m.beat}: no LINE after the BEAT line`); await page.close(); continue; }
  for (const t of m.t) {
    const wait = beatAt + t * 1000 - Date.now();
    if (wait > 0) await page.waitForTimeout(wait);
    await page.screenshot({ path: path.join(out, `${m.tale}_${m.beat}_${t}.png`) });
  }
  console.log(`${m.tale}/${m.beat}: boot ${((beatAt - t0) / 1000).toFixed(1)} s, shots ${m.t.join(",")}`);
  fs.writeFileSync(path.join(out, `${m.tale}_${m.beat}_console.txt`), logs.join("\n"));
  await page.close();
}
await b.close();
