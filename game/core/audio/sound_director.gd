class_name SoundDirector
extends Node
## Story sound (shared, one per story scene; spec: artifacts/audio_staging/WIRING.md). Loads the shared catalog
## (res://audio/sound_catalog.json) and plays:
##  - one-shots by sound id (2D or positional), fx / step cues resolved from the tale's `sound` blocks,
##  - music slots with crossfades, ambience beds (looping layers) with random sprinkles (birds, bees, frogs, owl)
##    and gusts, a stream emitter sliding along the water nearest the camera focus, leaf-rustle emitters at trees,
##  - footsteps per drawn-cycle contact frame (CastPuppet.foot_contact → StoryActor → footstep()).
## Buses Voice / Music / Ambience / SFX are created here if the project has none; Music and Ambience duck under the
## voice by a deterministic envelope (duck(true/false) from StoryRunner._say: the spec's fallback, which the preview
## mix also used), Master gets a hard limiter at -1 dB.

const CATALOG := "res://audio/sound_catalog.json"
const DUCK_MUSIC_DB := -7.0
const DUCK_AMB_DB := -3.0

var cat: Dictionary = {}
var tale: Dictionary = {}  ## the script's top-level `sound` block
var beat_sound: Dictionary = {}
var stage: SpreadStage
var log_sound := false
var missing: Array[String] = []
var rng := RandomNumberGenerator.new()
var speaking := false

var _streams := {}
var _last_idx := {}
var _pool3: Array[AudioStreamPlayer3D] = []
var _pool2: Array[AudioStreamPlayer] = []
var _p3 := 0
var _p2 := 0
var _music: Array[AudioStreamPlayer] = []
var _music_slot := ""
var _music_cur := 0
## A "hold" track (the story-start music, catalog `hold: true`) plays out once; music asked for meanwhile waits for it.
var _hold_slot := ""
var _hold_pending: Variant = null
var _hold_has_pending := false
var _loops := {}  ## key -> player
var _bed := ""
var _bed_layers := {}  ## sound id -> player
var _sprinkle_next := 0.0
var _sprinkle_last := {}
var _gust_next := 0.0
var _t := 0.0
var _stream_p: AudioStreamPlayer3D
var _stream_line := PackedVector3Array()
var _trees_p: Array[AudioStreamPlayer3D] = []
var _gust_lift := 0.0
var _env_prev := 0.0
var _duck := 0.0
var _duck_t := 0.0
var _music_extra_db := 0.0
var _music_extra_t := 0.0
var _foot_count := 0
var _cheer_last := -99.0
var _page_take := 0


static var current: SoundDirector


func _exit_tree() -> void:
	if current == self:
		current = null


func _ready() -> void:
	current = self
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(CATALOG))
	cat = parsed if parsed is Dictionary else {}
	_setup_buses()
	for i in 12:
		var p := AudioStreamPlayer3D.new()
		p.attenuation_model = AudioStreamPlayer3D.ATTENUATION_INVERSE_DISTANCE
		p.unit_size = 1.0
		p.panning_strength = 0.5
		p.doppler_tracking = AudioStreamPlayer3D.DOPPLER_TRACKING_DISABLED
		p.bus = "SFX"
		add_child(p)
		_pool3.append(p)
	for i in 6:
		var q := AudioStreamPlayer.new()
		q.bus = "SFX"
		add_child(q)
		_pool2.append(q)
	for i in 2:
		var m := AudioStreamPlayer.new()
		m.bus = "Music"
		m.volume_db = -80.0
		add_child(m)
		_music.append(m)


func _setup_buses() -> void:
	for b in ["Voice", "Music", "Ambience", "SFX"]:
		if AudioServer.get_bus_index(b) < 0:
			AudioServer.add_bus()
			var i := AudioServer.bus_count - 1
			AudioServer.set_bus_name(i, b)
			AudioServer.set_bus_send(i, "Master")
	var m := AudioServer.get_bus_index("Master")
	var has_lim := false
	for e in AudioServer.get_bus_effect_count(m):
		if AudioServer.get_bus_effect(m, e) is AudioEffectHardLimiter:
			has_lim = true
	if not has_lim:
		var lim := AudioEffectHardLimiter.new()
		lim.ceiling_db = -1.0
		AudioServer.add_bus_effect(m, lim)


# ------------------------------------------------------------------ catalog

func _sound(id: String) -> Dictionary:
	var s: Dictionary = (cat.get("sounds", {}) as Dictionary).get(id, {})
	if s.is_empty() and not missing.has(id):
		missing.append(id)
		print("SOUND_MISSING ", id)
	return s


func _load(path: String, loop: bool) -> AudioStream:
	var key := path + ("#loop" if loop else "")
	if not _streams.has(key):
		var st := load(path) as AudioStream
		if st == null:
			return null
		if loop and st is AudioStreamOggVorbis:
			st = st.duplicate()
			(st as AudioStreamOggVorbis).loop = true
		_streams[key] = st
	return _streams[key]


func _pick(id: String, s: Dictionary) -> String:
	var files: Array = s.get("files", [])
	if files.is_empty():
		return ""
	var i := rng.randi() % files.size()
	if bool(s.get("no_repeat", false)) and files.size() > 1 and i == int(_last_idx.get(id, -1)):
		i = (i + 1) % files.size()
	_last_idx[id] = i
	return str(files[i])


# ------------------------------------------------------------------ one-shots

## One-shot; at = Vector3 for positional, null for 2D. pitch_mul for scales (counter).
func play(id: String, at: Variant = null, gain_db := 0.0, delay := 0.0, pitch_mul := 1.0) -> void:
	if delay > 0.0:
		get_tree().create_timer(delay).timeout.connect(play.bind(id, at, gain_db, 0.0, pitch_mul))
		return
	var s := _sound(id)
	if s.is_empty():
		return
	var f := _pick(id, s)
	var st := _load(f, false)
	if st == null:
		return
	var vol := float(s.get("gain_db", 0.0)) + gain_db + rng.randf_range(-0.5, 0.5) * float(s.get("vol_rand_db", 0.0))
	var pitch := (1.0 + rng.randf_range(-1.0, 1.0) * float(s.get("pitch_rand", 0.0))) * pitch_mul
	var bus := str(s.get("bus", "SFX"))
	if at is Vector3 and bool(s.get("positional", true)):
		var p := _pool3[_p3]
		_p3 = (_p3 + 1) % _pool3.size()
		p.stream = st
		p.bus = bus
		p.volume_db = vol
		p.pitch_scale = pitch
		p.global_position = at
		p.play()
	else:
		var q := _pool2[_p2]
		_p2 = (_p2 + 1) % _pool2.size()
		q.stream = st
		q.bus = bus
		q.volume_db = vol
		q.pitch_scale = pitch
		q.play()
	if log_sound:
		print("SFX ", snappedf(_t, 0.01), " ", id, " ", f.get_file())
	if s.has("duck_music_db"):
		_music_extra_db = float(s["duck_music_db"])
		_music_extra_t = 3.5


func loop_start(id: String, key: String, fade := 0.5, gain_db := 0.0) -> void:
	var s := _sound(id)
	if s.is_empty():
		return
	var st := _load(_pick(id, s), true)
	if st == null:
		return
	var old: AudioStreamPlayer = _loops.get(key)
	if old:
		_fade(old, -80.0, fade, true)
	var p := AudioStreamPlayer.new()
	p.bus = str(s.get("bus", "SFX"))
	p.stream = st
	p.volume_db = -60.0
	add_child(p)
	p.play()
	_fade(p, float(s.get("gain_db", 0.0)) + gain_db, fade, false)
	_loops[key] = p
	if log_sound:
		print("SFX ", snappedf(_t, 0.01), " loop ", id)


func loop_stop(key: String, fade := 0.8) -> void:
	var p: AudioStreamPlayer = _loops.get(key)
	if p:
		_fade(p, -80.0, fade, true)
		_loops.erase(key)


func _fade(p: Node, to_db: float, sec: float, free_after: bool) -> void:
	var tw := create_tween()
	tw.tween_property(p, "volume_db", to_db, maxf(sec, 0.01))
	if free_after:
		tw.tween_callback(p.queue_free)


# ------------------------------------------------------------------ music

func set_music(slot: Variant, fade_in := 1.5, fade_out := 2.0) -> void:
	var name := "" if slot == null else str(slot)
	if _hold_slot != "" and name != _hold_slot:
		_hold_pending = slot  # the beat's music starts when the story-start music has played out
		_hold_has_pending = true
		return
	if name == _music_slot:
		return
	_music_slot = name
	var cur := _music[_music_cur]
	if cur.playing:
		_fade(cur, -80.0, fade_out, false)
		get_tree().create_timer(fade_out).timeout.connect(func(): if _music.find(cur) != _music_cur: cur.stop())
	if name == "":
		return
	var m: Dictionary = (cat.get("music", {}) as Dictionary).get(name, {})
	if m.is_empty():
		if not missing.has("music." + name):
			missing.append("music." + name)
			print("SOUND_MISSING music.", name)
		return
	_music_cur = 1 - _music_cur
	var nxt := _music[_music_cur]
	nxt.stream = _load(str(m["file"]), bool(m.get("loop", false)))
	nxt.volume_db = -60.0
	nxt.play()
	_fade(nxt, float(m.get("gain_db", 0.0)), fade_in, false)
	if bool(m.get("hold", false)):
		_hold_slot = name
		_hold_has_pending = false
	if log_sound:
		print("SFX ", snappedf(_t, 0.01), " music ", name)


# ------------------------------------------------------------------ beds, sprinkles, emitters, gusts

func set_bed(bed: Variant, fade := 2.5) -> void:
	var name := "" if bed == null else str(bed)
	if name == "@light":
		var lb: Dictionary = tale.get("light_beds", {})
		name = str(lb.get(stage.light if stage else "", lb.get("", "day")))
	if name == _bed:
		return
	_bed = name
	var bd: Dictionary = (cat.get("beds", {}) as Dictionary).get(name, {})
	var want := {}
	for l: Array in bd.get("layers", []):
		want[str(l[0])] = float(l[1])
	for id in _bed_layers.keys():
		if not want.has(id):
			_fade(_bed_layers[id], -80.0, fade, true)
			_bed_layers.erase(id)
	for id in want:
		var s := _sound(str(id))
		if s.is_empty():
			continue
		if _bed_layers.has(id):
			_fade(_bed_layers[id], float(s.get("gain_db", 0.0)) + float(want[id]), fade, false)
			continue
		var st := _load(_pick(str(id), s), true)
		if st == null:
			continue
		var p := AudioStreamPlayer.new()
		p.bus = "Ambience"
		p.stream = st
		p.volume_db = -60.0
		add_child(p)
		p.play(rng.randf() * maxf(st.get_length() - 1.0, 0.0))  # a random start point
		_fade(p, float(s.get("gain_db", 0.0)) + float(want[id]), fade, false)
		_bed_layers[id] = p
	var off := bool(bd.get("emitters_off", false))
	if _stream_p:
		_fade(_stream_p, -80.0 if off else float(_sound("amb.stream").get("gain_db", 0.0)), fade, false)
	for tp in _trees_p:
		_fade(tp, -80.0 if off else -6.0, fade, false)
	_sprinkle_next = _t + rng.randf_range(1.0, 3.0)
	if log_sound:
		print("SFX ", snappedf(_t, 0.01), " bed ", name)


## Stream + tree emitters for the spread on screen.
func setup_spread(st: SpreadStage, emitters: Array) -> void:
	stage = st
	if _stream_p:
		_stream_p.queue_free()
		_stream_p = null
	for tp in _trees_p:
		tp.queue_free()
	_trees_p.clear()
	if st == null or st.world == null:
		return
	if emitters.has("stream"):
		_stream_line = st.world.ground.stream_line_3d()
		var s := _sound("amb.stream")
		var e: Dictionary = (cat.get("emitters", {}) as Dictionary).get("stream", {})
		if not s.is_empty() and _stream_line.size() >= 2:
			_stream_p = AudioStreamPlayer3D.new()
			_stream_p.stream = _load(_pick("amb.stream", s), true)
			_stream_p.bus = "Ambience"
			_stream_p.attenuation_model = AudioStreamPlayer3D.ATTENUATION_INVERSE_SQUARE_DISTANCE
			_stream_p.unit_size = float(e.get("unit_size", 0.9))
			_stream_p.max_distance = float(e.get("max_distance", 4.0))
			_stream_p.panning_strength = 0.5
			_stream_p.volume_db = float(s.get("gain_db", 0.0))
			add_child(_stream_p)
			_stream_p.global_position = _stream_line[0]
			_stream_p.play(rng.randf() * 5.0)
	if emitters.has("trees"):
		var pts: Array[Vector3] = st.world.trees.duplicate()
		pts.shuffle()
		var s2 := _sound("amb.breeze")
		for i in mini(3, pts.size()):
			var tp := AudioStreamPlayer3D.new()
			tp.stream = _load(_pick("amb.breeze", s2), true)
			tp.bus = "Ambience"
			tp.unit_size = 1.2
			tp.max_distance = 5.0
			tp.volume_db = -6.0
			add_child(tp)
			tp.global_position = pts[i]
			tp.play(rng.randf() * 10.0)
			_trees_p.append(tp)


var _gust_last := -99.0


func gust(amount: float) -> void:
	_gust_last = _t
	var at: Variant = null
	if stage and stage.world and not stage.world.trees.is_empty():
		at = _nearest_tree(_listener())
	play("amb.gust", at, -8.0 + 8.0 * clampf(amount, 0.0, 1.0))
	_gust_lift = 6.0 * clampf(amount, 0.0, 1.0)


func _listener() -> Vector3:
	if stage and stage.world and stage.world.rig:
		var r := stage.world.rig
		return r._look if "_look" in r else r.camera.global_position
	return Vector3.ZERO


func _nearest_tree(p: Vector3) -> Vector3:
	var best := p
	var bd := INF
	for t: Vector3 in stage.world.trees:
		var d := Vector2(t.x - p.x, t.z - p.z).length()
		if d < bd:
			bd = d
			best = t
	return best


func _sprinkle_point(where: String) -> Variant:
	if stage == null or stage.world == null:
		return null
	var l := _listener()
	if where == "trees" and not stage.world.trees.is_empty():
		var near: Array = []
		for t: Vector3 in stage.world.trees:
			if Vector2(t.x - l.x, t.z - l.z).length() < 4.0:
				near.append(t)
		if not near.is_empty():
			return near[rng.randi() % near.size()]
	if where == "water" and _stream_line.size() > 1:
		return _stream_line[rng.randi() % _stream_line.size()]
	return l + Vector3(rng.randf_range(-2.0, 2.0), 0.3, rng.randf_range(-2.0, 1.0))


func _process(dt: float) -> void:
	_t += dt
	if _hold_slot != "" and not _music[_music_cur].playing:
		_hold_slot = ""
		_music_slot = ""
		if _hold_has_pending:
			_hold_has_pending = false
			set_music(_hold_pending, 2.5)
	# ducking under the voice (deterministic envelope: attack 60 ms, release 450 ms)
	_duck = move_toward(_duck, 1.0 if speaking else 0.0, dt / (0.06 if speaking else 0.45))
	_music_extra_t = maxf(0.0, _music_extra_t - dt)
	var extra := _music_extra_db if _music_extra_t > 0.0 else 0.0
	var mb := AudioServer.get_bus_index("Music")
	var ab := AudioServer.get_bus_index("Ambience")
	if mb >= 0:
		AudioServer.set_bus_volume_db(mb, DUCK_MUSIC_DB * _duck + extra)
	if ab >= 0:
		AudioServer.set_bus_volume_db(ab, DUCK_AMB_DB * _duck)
	# stream emitter: nearest point of the water line to the camera focus, smoothed
	if _stream_p and _stream_line.size() > 1:
		var l := _listener()
		var best := _stream_line[0]
		var bd := INF
		for q in _stream_line:
			var d := Vector2(q.x - l.x, q.z - l.z).length_squared()
			if d < bd:
				bd = d
				best = q
		_stream_p.global_position = _stream_p.global_position.lerp(best, 1.0 - exp(-4.0 * dt))
	# leaf rustle swells with gusts: huffs, random gusts, and the meadow's own sway envelope at the listener
	_gust_lift = maxf(0.0, _gust_lift - dt * 4.0)
	if stage and stage.world and stage.world.sway:
		var sw := stage.world.sway
		var l2 := _listener()
		var g := 0.5 + 0.5 * sin((sw._t * sw.gust_speed - Vector2(l2.x, l2.z).dot(sw.wind_dir.normalized())) * 0.9)
		g = g * g
		if g > 0.85 and _env_prev <= 0.85 and _bed != "room" and _bed != "" and _t - _gust_last > 7.0:
			gust(0.4)
		_env_prev = g
	for tp in _trees_p:
		if _bed != "room":
			tp.volume_db = lerpf(tp.volume_db, -6.0 + _gust_lift, 1.0 - exp(-3.0 * dt))
	var bd2: Dictionary = (cat.get("beds", {}) as Dictionary).get(_bed, {})
	# random gusts on beds that have them
	var gu: Variant = bd2.get("gusts")
	if gu is Dictionary:
		if _gust_next <= 0.0:
			_gust_next = _t + rng.randf_range(float(gu["every"][0]), float(gu["every"][1]))
		elif _t >= _gust_next:
			gust(rng.randf_range(0.2, 0.7))
			_gust_next = _t + rng.randf_range(float(gu["every"][0]), float(gu["every"][1]))
	# sprinkles (birds, cuckoo, dove, bee, frogs, owl)
	var sname: Variant = bd2.get("sprinkles")
	if sname != null and _t >= _sprinkle_next:
		var ss: Dictionary = (cat.get("sprinkle_sets", {}) as Dictionary).get(str(sname), {})
		if not ss.is_empty():
			var pool: Array = []
			var wsum := 0.0
			for it: Array in ss["items"]:
				var gap := float(it[2]) if it.size() > 2 else 0.0
				if _t - float(_sprinkle_last.get(str(it[0]), -999.0)) >= gap:
					pool.append(it)
					wsum += float(it[1])
			if not pool.is_empty():
				var r := rng.randf() * wsum
				var pick: Array = pool[0]
				for it: Array in pool:
					r -= float(it[1])
					if r <= 0.0:
						pick = it
						break
				var gr: Array = ss.get("gain_db", [-8, 0])
				var gain := rng.randf_range(float(gr[0]), float(gr[1])) - (6.0 if speaking else 0.0)
				play(str(pick[0]), _sprinkle_point(str(ss.get("where", "any"))), gain)
				_sprinkle_last[str(pick[0])] = _t
			var iv: Array = ss.get("interval", [4.0, 10.0])
			_sprinkle_next = _t + rng.randf_range(float(iv[0]), float(iv[1]))


# ------------------------------------------------------------------ cues

func duck(on: bool) -> void:
	speaking = on


## The beat's sound block: music, bed, emitters (setup once per spread).
func enter_beat(b: Dictionary, st: SpreadStage, new_spread: bool) -> void:
	beat_sound = b.get("sound", {})
	if beat_sound.has("music"):
		set_music(beat_sound["music"])
	if st and new_spread:
		setup_spread(st, beat_sound.get("emitters", []))
	stage = st
	if beat_sound.has("bed"):
		set_bed(beat_sound["bed"])


## Light change on the page (the bed follows it).
func light_changed() -> void:
	if beat_sound.get("bed", "") == "@light" and _bed != "room":
		set_bed("@light")


## fx cue: beat sound.fx, then tale sound.fx. ctx = stage.build_ctx (by_tap).
func fx(name: String, at: Variant = null, ctx: Dictionary = {}) -> void:
	var v: Variant = (beat_sound.get("fx", {}) as Dictionary).get(name, null)
	if v == null:
		v = (tale.get("fx", {}) as Dictionary).get(name, null)
	if v == null:
		return
	if name == "pigs_cheer" and v is Dictionary and _t - _cheer_last < float((v as Dictionary).get("min_gap", 0.0)):
		return
	if name == "pigs_cheer":
		_cheer_last = _t
	cue(v, at, ctx)


func cue(v: Variant, at: Variant = null, ctx: Dictionary = {}) -> void:
	if v is String:
		play(v, at)
	elif v is Array:
		for x in v:
			cue(x, at, ctx)
	elif v is Dictionary:
		var d: Dictionary = v
		if d.has("by_tap"):
			var lst: Array = d["by_tap"]
			var i := clampi(int(ctx.get("tap", 1)) - 1, 0, lst.size() - 1)
			cue(lst[i], at, ctx)
			if d.has("gust"):
				var taps := maxf(float(ctx.get("taps", 1)), 1.0)
				gust(float(ctx.get("tap", 1)) / taps * (0.6 if str(d["gust"]) == "tap_soft" else 1.0))
		elif d.has("sound"):
			play(str(d["sound"]), at, float(d.get("gain_db", 0.0)), float(d.get("delay", 0.0)))
		elif d.has("loop"):
			loop_start(str(d["loop"]), str(d.get("key", d["loop"])), float(d.get("fade", 0.5)), float(d.get("gain_db", 0.0)))
		elif d.has("bed"):
			set_bed(d["bed"], float(d.get("fade", 2.5)))
			for k in d.get("stop_loops", []):
				loop_stop(str(k))
		elif d.has("music"):
			set_music(d["music"], float(d.get("fade", 1.5)))


## Engine step cue (tale sound.steps): page_turn, cover, go_inside door_open/door_shut, end close_book, climb.
func step(name: String, sub := "", at: Variant = null) -> void:
	var v: Variant = (tale.get("steps", {}) as Dictionary).get(name, null)
	if v is Dictionary and sub != "":
		v = (v as Dictionary).get(sub, null)
	if v == null:
		return
	if name == "page_turn":
		_page_take += 1
	cue(v, at)


## Footstep at an actor's feet (one per drawn-cycle contact frame).
func footstep(a: StoryActor, surface_hint := "") -> void:
	var kinds: Dictionary = tale.get("footsteps", {})
	var kind: Variant = kinds.get(a.role, null)
	if kind == null:
		return
	var p := a.global_position
	var l := _listener()
	if Vector2(p.x - l.x, p.z - l.z).length() > 4.0:
		return
	var surface := surface_hint
	var id := ""
	if surface == "ladder":
		id = "foot.ladder_rung"
	elif surface == "roof":
		id = "foot.roof_tile"
	else:
		var g := stage.world.ground if stage and stage.world else null
		surface = "grass"
		if g:
			var q := Vector2(p.x, p.z)
			if g.path_distance(q) < 0.0:
				surface = "bridge" if g.stream_distance(q) < 0.05 else "road"
			elif g.stream_distance(q) < 0.0:
				surface = "bridge"
		id = "foot.%s.%s" % [str(kind), surface]
	var gain := -2.0 + (2.0 if a.walk_pose in ["run", "run_away", "scared"] else 0.0)
	play(id, p, gain)
