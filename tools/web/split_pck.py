#!/usr/bin/env python3
"""GitHub Pages serves files up to 100 MB. Split build/web/index.pck into index.pck.0, .1, ... (90 MB each) and patch
index.html so the page fetches the parts into one buffer and hands it to the engine as index.pck (same bytes as the
single file, so nothing in the game changes).   python3 tools/web/split_pck.py [build/web]"""
import json, os, re, shutil, sys, time

WEB = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "../../build/web"))
PART = 90 * 1024 * 1024
pck = os.path.join(WEB, "index.pck")
html = os.path.join(WEB, "index.html")
size = os.path.getsize(pck)
parts = []
with open(pck, "rb") as f:
    i = 0
    while True:
        b = f.read(PART)
        if not b:
            break
        name = f"index.pck.{i}"
        with open(os.path.join(WEB, name), "wb") as o:
            o.write(b)
        parts.append(name)
        i += 1
trash = os.path.expanduser(f"~/.Trash/web_pck_{time.strftime('%Y%m%d_%H%M%S')}.pck")
shutil.move(pck, trash)  # the single file must not be deployed (it is over the limit)

LOADER = """
// split_pck.py: the main pack is served in parts (GitHub Pages 100 MB file limit); join them, then start.
const PCK_PARTS = %s;
const PCK_SIZE = %d;
function startSplitGame(override) {
	const onProgress = override['onProgress'];
	const buf = new Uint8Array(PCK_SIZE);
	let got = 0;
	const fetchPart = (i, off) => fetch(PCK_PARTS[i]).then((r) => {
		if (!r.ok) throw new Error('Failed loading ' + PCK_PARTS[i] + ' (' + r.status + ')');
		const rd = r.body.getReader();
		let o = off;
		const pump = () => rd.read().then(({ done, value }) => {
			if (done) return o;
			buf.set(value, o); o += value.length; got += value.length;
			if (onProgress) onProgress(got, PCK_SIZE);
			return pump();
		});
		return pump();
	});
	let chain = Promise.resolve(0);
	PCK_PARTS.forEach((_, i) => { chain = chain.then((off) => fetchPart(i, off)); });
	engine.config.update(override);
	engine.config.args = ['--main-pack', 'index.pck'].concat(engine.config.args);
	return Promise.all([engine.init(engine.config.executable), chain]).then(() => {
		if (got !== PCK_SIZE) throw new Error('pck size mismatch ' + got + ' / ' + PCK_SIZE);
		return engine.preloadFile(buf.buffer, 'index.pck');  // an ArrayBuffer: a typed array would be stringified as a fileSizes key (OOM in Safari)
	}).then(() => engine.start());
}
""" % (json.dumps(parts), size)

s = open(html, encoding="utf-8").read()
assert "engine.startGame({" in s, "index.html: engine.startGame call not found"
s = s.replace("const engine = new Engine(GODOT_CONFIG);", "const engine = new Engine(GODOT_CONFIG);\n" + LOADER, 1)
s = s.replace("engine.startGame({", "startSplitGame({", 1)
open(html, "w", encoding="utf-8").write(s)
print(f"index.pck {size / 1048576:.1f} MB -> {parts}")
