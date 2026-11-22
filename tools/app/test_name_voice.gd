extends SceneTree
## Headless check of the name-piece join: every witch_candy seg with `pieces` builds one clip; prints its length next
## to the original whole-line clip and 톡톡's assembled default; writes the joined clips as WAV to OUT (listening /
## waveform check).  godot --headless --path game --script res://../tools/app/test_name_voice.gd -- OUT_DIR
func _init():
	var out := "user://name_test"
	for a in OS.get_cmdline_user_args():
		out = a
	DirAccess.make_dir_recursive_absolute(out)
	var d: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://stories/witch_candy/script.json"))
	var n := 0
	var bad := 0
	for l: Dictionary in d["lines"]:
		var segs: Array = l["segs"]
		for i in segs.size():
			var s: Dictionary = segs[i]
			if not s.has("pieces"):
				continue
			var t0 := Time.get_ticks_usec()
			var st := NameVoice.stream_for("witch_candy", str(l["id"]), i, s, false)
			var ms := (Time.get_ticks_usec() - t0) / 1000.0
			if st == null:
				bad += 1
				print("FAIL ", l["id"])
				continue
			var orig: AudioStream = load(str(s["audio"])) if ResourceLoader.exists(str(s["audio"])) else null
			print("JOIN %s %.2fs (whole-line clip %s) build %.0f ms | %s | as 지우: %s" % [l["id"], st.get_length(), ("%.2fs" % orig.get_length()) if orig else "-", ms, s["text"], NameVoice.seg_text(s, {"A": "지우"})])
			st.save_to_wav(out.path_join(str(l["id"]) + ".wav"))
			n += 1
	print("NAME_VOICE joined=", n, " failed=", bad)
	quit()
