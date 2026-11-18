extends "res://addons/agentkit/agent_job.gd"
## Static-card analysis: instance distances to the view camera, contour vertex counts per eps, texture sizes.

func run() -> Dictionary:
	var w = (load("res://scenes/world/meadow.tscn") as PackedScene).instantiate()
	w.view = int(arg("view", 0))
	w.walk = false
	w.pop_on_load = true
	root.add_child(w)
	await wait_frames(2)
	var cam: Camera3D = w.rig.camera
	var cp := cam.global_position
	var hist := {}
	var prints_by_band := {}
	var tex_sizes := {}
	var eps_counts := {"1.6": 0, "3": 0, "6": 0, "12": 0}
	var n := 0
	var hp := {}
	for h in w.hinges:
		var c = h.get_child(0)
		hp[c.texture.resource_path] = 1
	for path in w.statics._groups:
		for xf in w.statics._groups[path]["xforms"]:
			var mmi_name: String = path
			var o: Vector3 = xf.origin
			var d := o.distance_to(cp)
			var b := int(d / 2.0) * 2
			hist[b] = hist.get(b, 0) + 1
			if not prints_by_band.has(b):
				prints_by_band[b] = {}
			prints_by_band[b][mmi_name] = 1
			n += 1
	for b in prints_by_band:
		prints_by_band[b] = prints_by_band[b].size()
	# contour counts for a sample of prints
	var paths: Array = w.statics._groups.keys()
	var tot := {}
	for k in eps_counts:
		tot[k] = 0
	var sample := 0
	var area := 0.0
	for p in paths:
		var tex: Texture2D = load(p)
		var sz := tex.get_size()
		area += sz.x * sz.y
		var key := "%d" % maxi(int(sz.x), int(sz.y))
		tex_sizes[key] = tex_sizes.get(key, 0) + 1
		if sample < 60:
			sample += 1
			var img := PaperCard._source_image(tex)
			var full := Vector2(img.get_width(), img.get_height())
			var cimg := img.duplicate() as Image
			var sc := minf(1.0, 320.0 / maxf(full.x, full.y))
			if sc < 1.0:
				cimg.resize(int(full.x * sc), int(full.y * sc), Image.INTERPOLATE_BILINEAR)
			var bm := BitMap.new()
			bm.create_from_image_alpha(cimg, 0.35)
			for k in eps_counts:
				var polys := bm.opaque_to_polygons(Rect2i(Vector2i.ZERO, bm.get_size()), float(k))
				for pp in polys:
					tot[k] += pp.size()
	for k in tot:
		tot[k] = snappedf(tot[k] / float(sample), 0.1)
	var hinged_h := []
	return {"statics": n, "dist_hist_2u": hist, "prints_by_band": prints_by_band, "cam": cp, "tex_long_side": tex_sizes, "avg_contour_verts": tot, "prints": paths.size(), "tex_area_mpx": area / 1e6, "hinged": w.hinges.size(), "hinged_prints": hp.size()}
