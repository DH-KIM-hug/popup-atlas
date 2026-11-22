class_name NameVoice
extends RefCounted
## Creative-tale name lines as name piece + fixed pieces, joined on the device into ONE clip (톡톡 동화극장's method,
## its engine/names.js assemble(), 2026-11-22). A seg with `pieces` (script.json, from tools/app/name_pieces.py):
##   [{k: "S"|"N", tpl, gap, audio}]  k S = fixed piece (app bundle), N = the name piece ("다현이랑", "다현이가" ...).
## Join: trim silence (-45 dB, 20 ms window, keep 15 / 30 ms) -> the name piece's level matched to the fixed pieces'
## mean RMS (+-6 dB) -> 6 ms fade in / 12 ms fade out -> `gap` s of silence after each piece -> seg.name_gain_db (the
## line's loudness to -16 LUFS) -> soft limiter at 0.8 -> AudioStreamWAV 16-bit mono.
##
## The default name piece is in the bundle (톡톡's recording). A custom name's pieces come from the name server
## (docs/APP_UI_PLAN.md "이름 녹음") as WAV files under user://app/names/<tale>/<hash>/<line id>.wav; until every line
## of a tale has arrived the tale plays and shows the default name (no TTS on the device).
## Pieces are WAV with importer "keep": read as bytes, parsed by AudioStreamWAV.load_from_buffer.

const SR := 24000
static var _cache: Dictionary = {}  ## "<tale>/<line>/<seg>/<name>" -> AudioStreamWAV
static var _pcm: Dictionary = {}  ## path -> PackedFloat32Array


# ------------------------------------------------------------------ names + text

static func has_batchim(name: String) -> bool:
	if name == "":
		return false
	var c := name.unicode_at(name.length() - 1)
	return c >= 0xAC00 and c <= 0xD7A3 and (c - 0xAC00) % 28 != 0


## "{A:이랑/랑}" + 다현 -> 다현이랑, + 지우 -> 지우랑 (the form after a final consonant / after a vowel).
static func fill(tpl: String, names: Dictionary) -> String:
	var re := RegEx.create_from_string("\\{([A-D]):([^/}]*)/([^}]*)\\}")
	var out := tpl
	for m in re.search_all(tpl):
		var n := str(names.get(m.get_string(1), ""))
		out = out.replace(m.get_string(0), n + (m.get_string(2) if has_batchim(n) else m.get_string(3)))
	return out


static func seg_text(seg: Dictionary, names: Dictionary) -> String:
	var parts := PackedStringArray()
	for p: Dictionary in seg.get("pieces", []):
		parts.append(fill(str(p["tpl"]), names))
	return " ".join(parts)


## A name a parent may type: 1-4 Hangul syllables (톡톡 server rule) (the recordings are Korean; English names are a later step).
static func valid_name(n: String) -> bool:
	n = n.strip_edges()
	if n.length() < 1 or n.length() > 4:
		return false
	for i in n.length():
		var c := n.unicode_at(i)
		if c < 0xAC00 or c > 0xD7A3:
			return false
	return true


## The name the tale should speak and show: the parent's name when it is on and all its pieces arrived, else the
## default. Command-line story runs always use the default (AppState returns nothing there).
static func active_names(tale: String, defaults: Dictionary) -> Dictionary:
	var cfg := AppState.tale_names(tale)
	if cfg.is_empty() or not bool(cfg.get("on", false)) or not bool(cfg.get("done", false)):
		return defaults
	var out := defaults.duplicate()
	for s in defaults:
		if cfg.has(s) and valid_name(str(cfg[s])):
			out[s] = str(cfg[s])
	return out


static func custom_piece(tale: String, line_id: String) -> String:
	var cfg := AppState.tale_names(tale)
	var got: Dictionary = cfg.get("got", {})
	return str(got.get(line_id, ""))


# ------------------------------------------------------------------ audio

static func pieces_exist(seg: Dictionary) -> bool:
	for p: Dictionary in seg.get("pieces", []):
		if not FileAccess.file_exists(str(p.get("audio", ""))):
			return false
	return true


## The joined clip for one seg (cached). `custom` = the parent's name is active: its N piece comes from user://.
static func stream_for(tale: String, line_id: String, seg_i: int, seg: Dictionary, custom: bool) -> AudioStreamWAV:
	var key := "%s/%s/%d/%s" % [tale, line_id, seg_i, custom_piece(tale, line_id) if custom else ""]
	if _cache.has(key):
		return _cache[key]
	var parts: Array = []  # [kind, samples, gap]
	for p: Dictionary in seg.get("pieces", []):
		var path := str(p["audio"])
		if custom and str(p["k"]) == "N":
			path = custom_piece(tale, line_id)
		var d := _load_pcm(path)
		if d.is_empty():
			return null
		parts.append([str(p["k"]), d, float(p.get("gap", 0.0))])
	var st := join(parts, float(seg.get("name_gain_db", 0.0)))
	_cache[key] = st
	return st


static func _load_pcm(path: String) -> PackedFloat32Array:
	if _pcm.has(path):
		return _pcm[path]
	var out := PackedFloat32Array()
	if path == "" or not FileAccess.file_exists(path):
		return out
	var w := AudioStreamWAV.load_from_buffer(FileAccess.get_file_as_bytes(path))
	if w == null or w.format != AudioStreamWAV.FORMAT_16_BITS:
		push_warning("NameVoice: not a 16-bit WAV: " + path)
		return out
	var b := w.data
	var ch := 2 if w.stereo else 1
	var n := b.size() / (2 * ch)
	out.resize(n)
	for i in n:
		out[i] = b.decode_s16(i * 2 * ch) / 32768.0
	if w.mix_rate != SR:
		out = _resample(out, float(w.mix_rate))
	_pcm[path] = out
	return out


static func _resample(d: PackedFloat32Array, rate: float) -> PackedFloat32Array:
	var n := int(d.size() * SR / rate)
	var o := PackedFloat32Array()
	o.resize(n)
	for i in n:
		var x := i * rate / SR
		var j := int(x)
		var f := x - j
		o[i] = d[mini(j, d.size() - 1)] * (1.0 - f) + d[mini(j + 1, d.size() - 1)] * f
	return o


static func _trim_range(d: PackedFloat32Array) -> Vector2i:
	var W := int(SR * 0.02)
	var step := W / 4
	var thr := pow(10.0, -45.0 / 20.0)
	var a := 0
	while a < d.size() and not _loud(d, a, W, thr):
		a += step
	var b := d.size()
	while b > a and not _loud(d, maxi(0, b - W), W, thr):
		b -= step
	return Vector2i(maxi(0, a - int(SR * 0.015)), mini(d.size(), b + int(SR * 0.03)))


static func _loud(d: PackedFloat32Array, i: int, W: int, thr: float) -> bool:
	var s := 0.0
	var n := 0
	for j in range(i, mini(d.size(), i + W)):
		s += d[j] * d[j]
		n += 1
	return n > 0 and sqrt(s / n) > thr


static func _rms_db(d: PackedFloat32Array, r: Vector2i) -> float:
	var s := 0.0
	for i in range(r.x, r.y):
		s += d[i] * d[i]
	return 20.0 * log(sqrt(s / maxf(1.0, r.y - r.x)) + 1e-9) / log(10.0)


static func join(parts: Array, gain_db: float) -> AudioStreamWAV:
	var ranges: Array[Vector2i] = []
	var s_db: Array[float] = []
	for p in parts:
		var r := _trim_range(p[1])
		ranges.append(r)
		if p[0] == "S":
			s_db.append(_rms_db(p[1], r))
	var ref := 0.0
	for v in s_db:
		ref += v
	var has_ref := s_db.size() > 0
	if has_ref:
		ref /= s_db.size()
	var total := 0
	for i in parts.size():
		total += ranges[i].y - ranges[i].x
		if i < parts.size() - 1:
			total += int(round(SR * float(parts[i][2])))
	var bytes := PackedByteArray()
	bytes.resize(total * 2)
	var post := pow(10.0, gain_db / 20.0)
	var at := 0
	var fi := int(SR * 0.006)
	var fo := int(SR * 0.012)
	for i in parts.size():
		var d: PackedFloat32Array = parts[i][1]
		var r := ranges[i]
		var g := post
		if parts[i][0] == "N" and has_ref:
			g *= pow(10.0, clampf(ref - _rms_db(d, r), -6.0, 6.0) / 20.0)
		var L := r.y - r.x
		for j in L:
			var v: float = d[r.x + j] * g
			if j < fi:
				v *= float(j) / fi
			if j > L - fo:
				v *= maxf(0.0, float(L - j) / fo)
			var a := absf(v)
			if a > 0.65:  # soft limiter: reaches 0.8 smoothly (names.js)
				v = signf(v) * (0.65 + 0.15 * tanh((a - 0.65) / 0.15))
			bytes.encode_s16((at + j) * 2, int(clampf(v, -1.0, 1.0) * 32767.0))
		at += L
		if i < parts.size() - 1:
			at += int(round(SR * float(parts[i][2])))  # zeros already
	var w := AudioStreamWAV.new()
	w.format = AudioStreamWAV.FORMAT_16_BITS
	w.mix_rate = SR
	w.stereo = false
	w.data = bytes
	return w
