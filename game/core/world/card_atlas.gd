class_name CardAtlas
extends RefCounted
## Card print atlas for the batched cards (component F, perf, 2026-11-18).
## Every meadow card print is copied texel-for-texel into 4096² pages of one Texture2DArray (no mipmaps, like the
## lossless, mip-less print textures), wrap-padded by PAD texels so linear/anisotropic sampling at the borders is the
## same as the originals' repeat sampler. A quarter-res L8 array holds each print's contour bitmap (shadow quads).
## A small RGBAF params texture holds per print: row 0 atlas rect (u0, v0, du, dv), row 1 (layer, card_w, card_h,
## half thickness) at the print's catalog height, row 2 cut-wall colour (linear), row 3 the shadow quad rect.
## One shared instance: prints are registered by (path, h0) and keep their index for the app's lifetime, so the
## single-surface meshes (UV2.y = index) stay valid when the atlas grows. Build cost is paid once (first spread).

const PAGE := 4096
const PAD := 4
const MASK_DIV := 2
const EDGE := Color(0.96, 0.92, 0.82)  ## PaperCard default edge_color

static var shared: CardAtlas

var keys := {}  ## "path|h0" -> index
var entries: Array[Dictionary] = []  ## per index: path, h0, thick, mesh, size, hz, quad, edge (+ layer, rect once packed)
var color: Texture2DArray
var mask: Texture2DArray
var params: ImageTexture
var built_count := 0  ## entries packed into the current textures
var pages := 0

var _pending: Array[int] = []
var _shelves: Array = []  ## per page: [[y, height, x_used], ...]
var _page_y: Array[int] = []
var _color_imgs: Array[Image] = []
var _mask_imgs: Array[Image] = []


static func get_shared() -> CardAtlas:
	if shared == null:
		shared = CardAtlas.new()
	return shared


static func thickness_for(h: float) -> float:
	return clampf(h * 0.04, 0.011, 0.04)


## Index of a print at catalog height h0 (registered on first use; built on the next ensure()).
func index_of(path: String, h0: float) -> int:
	var key := "%s|%.4f" % [path, h0]
	if keys.has(key):
		return keys[key]
	var i := entries.size()
	keys[key] = i
	entries.append({"path": path, "h0": h0, "thick": thickness_for(h0), "ok": false})
	_pending.append(i)
	return i


func entry(i: int) -> Dictionary:
	return entries[i]


func has_pending() -> bool:
	return not _pending.is_empty()


## Build meshes for the pending prints and (re)upload the atlas textures. `budget_usec` > 0: stop after that much time
## (call again next frame; returns true when everything is built).
func ensure(budget_usec := 0) -> bool:
	var t0 := Time.get_ticks_usec()
	while not _pending.is_empty():
		var i: int = _pending.pop_front()
		_build_entry(i)
		if budget_usec > 0 and Time.get_ticks_usec() - t0 > budget_usec and not _pending.is_empty():
			return false
	if built_count < entries.size() or color == null:
		_upload()
	return true


## Same as ensure(), one print per slicer tick (spread prebuild).
func build_sliced(sl: BuildSlicer) -> void:
	while not _pending.is_empty():
		_build_entry(_pending.pop_front())
		await sl.tick()
	if built_count < entries.size() or color == null:
		_upload()


func _build_entry(i: int) -> void:
	var e := entries[i]
	var tex: Texture2D = load(e["path"])
	if tex == null:
		return
	var b := PaperCard._build(tex, e["h0"], e["thick"], 1.6, i)
	if b.is_empty() or b.get("mesh") == null:
		return
	var img: Image = b["image"]
	var avg: Color = b["avg"]
	e["mesh"] = b["mesh"]
	e["size"] = b["size"]
	e["hz"] = b["hz"]
	e["quad"] = b["quad"]
	e["aabb"] = (b["mesh"] as ArrayMesh).get_aabb()
	# PaperCard._materials: side.edge_color = edge.lerp(avg, 0.42).darkened(0.1) (a source_color uniform -> linear).
	e["edge"] = EDGE.lerp(avg, 0.42).darkened(0.1).srgb_to_linear()
	_pack(e, img, b["polys"])
	e["ok"] = true


func _pack(e: Dictionary, img: Image, polys: Array) -> void:
	_restore_cpu()
	var w := img.get_width()
	var h := img.get_height()
	var sw := _ceil4(w + PAD * 2)
	var sh := _ceil4(h + PAD * 2)
	var slot := _alloc(sw, sh)
	var layer: int = slot[0]
	var ox: int = slot[1]
	var oy: int = slot[2]
	var page := _color_imgs[layer]
	# Centre + wrapped borders (the original sampler repeats).
	var p := PAD
	for dy in [-1, 0, 1]:
		for dx in [-1, 0, 1]:
			var sx := 0 if dx == 0 else (w - p if dx < 0 else 0)
			var sy := 0 if dy == 0 else (h - p if dy < 0 else 0)
			var rw := w if dx == 0 else p
			var rh := h if dy == 0 else p
			var tx := ox + p + (0 if dx == 0 else (-p if dx < 0 else w))
			var ty := oy + p + (0 if dy == 0 else (-p if dy < 0 else h))
			page.blit_rect(img, Rect2i(sx, sy, rw, rh), Vector2i(tx, ty))
	# Contour polygons (the card's cut faces) filled at half res, same normalized rect.
	_fill_polys(_mask_imgs[layer], polys, Vector2(ox + p, oy + p) / MASK_DIV, 1.0 / MASK_DIV)
	e["layer"] = layer
	e["rect"] = Vector4(float(ox + p) / PAGE, float(oy + p) / PAGE, float(w) / PAGE, float(h) / PAGE)


## Scanline fill of each polygon (texel centres inside -> 255), polygons in source px, mapped by o + v * k.
static func _fill_polys(dst: Image, polys: Array, o: Vector2, k: float) -> void:
	for poly: PackedVector2Array in polys:
		var rows := {}  ## row -> PackedFloat32Array of x crossings
		var n := poly.size()
		for i in n:
			var a := o + poly[i] * k
			var b := o + poly[(i + 1) % n] * k
			if a.y == b.y:
				continue
			var y0 := minf(a.y, b.y)
			var y1 := maxf(a.y, b.y)
			for y in range(ceili(y0 - 0.5), ceili(y1 - 0.5)):
				var yc := y + 0.5
				if yc < y0 or yc >= y1:
					continue
				var x := a.x + (yc - a.y) / (b.y - a.y) * (b.x - a.x)
				if not rows.has(y):
					rows[y] = PackedFloat32Array()
				var arr: PackedFloat32Array = rows[y]
				arr.append(x)
				rows[y] = arr
		for y: int in rows:
			var xs: PackedFloat32Array = rows[y]
			xs.sort()
			for j in range(0, xs.size() - 1, 2):
				var x0 := ceili(xs[j] - 0.5)
				var x1 := ceili(xs[j + 1] - 0.5)
				if x1 > x0:
					dst.fill_rect(Rect2i(x0, y, x1 - x0, 1), Color(1, 1, 1, 1))


static func _ceil4(v: int) -> int:
	return (v + 3) / 4 * 4


## Shelf packer over PAGE² pages: [layer, x, y].
func _alloc(w: int, h: int) -> Array:
	for li in _shelves.size():
		for sh: Array in _shelves[li]:
			if h <= sh[1] and sh[2] + w <= PAGE and h * 10 >= sh[1] * 7:
				var x: int = sh[2]
				sh[2] += w
				return [li, x, sh[0]]
		if _page_y[li] + h <= PAGE:
			var y := _page_y[li]
			_shelves[li].append([y, h, w])
			_page_y[li] += h
			return [li, 0, y]
	_shelves.append([])
	_page_y.append(0)
	_color_imgs.append(Image.create_empty(PAGE, PAGE, false, Image.FORMAT_RGBA8))
	_mask_imgs.append(Image.create_empty(PAGE / MASK_DIV, PAGE / MASK_DIV, false, Image.FORMAT_L8))
	pages = _color_imgs.size()
	return _alloc(w, h)


func _upload() -> void:
	var n := maxi(1, entries.size())
	var pi := Image.create_empty(n, 4, false, Image.FORMAT_RGBAF)
	for i in entries.size():
		var e := entries[i]
		if not e.get("ok", false):
			continue
		var r: Vector4 = e["rect"]
		var sz: Vector2 = e["size"]
		var q: Vector4 = e["quad"]
		var ec: Color = e["edge"]
		pi.set_pixel(i, 0, Color(r.x, r.y, r.z, r.w))
		pi.set_pixel(i, 1, Color(float(e["layer"]), sz.x, sz.y, float(e["hz"])))
		pi.set_pixel(i, 2, Color(ec.r, ec.g, ec.b, 1.0))
		pi.set_pixel(i, 3, Color(q.x, q.y, q.z, q.w))
	if params == null or params.get_width() != n:
		params = ImageTexture.create_from_image(pi)
	else:
		params.update(pi)
	if color == null or color.get_layers() != _color_imgs.size():
		color = Texture2DArray.new()
		color.create_from_images(_color_imgs)
		mask = Texture2DArray.new()
		mask.create_from_images(_mask_imgs)
	else:
		for li in _color_imgs.size():
			color.update_layer(_color_imgs[li], li)
			mask.update_layer(_mask_imgs[li], li)
	built_count = entries.size()


## Page images are only needed while prints are being added: free the RAM copies (read back if more come later).
func release_cpu_pages() -> void:
	if color != null and built_count == entries.size():
		_color_imgs.clear()
		_mask_imgs.clear()


func _restore_cpu() -> void:
	if _color_imgs.size() == pages or color == null:
		return
	_color_imgs.clear()
	_mask_imgs.clear()
	for li in color.get_layers():
		_color_imgs.append(color.get_layer_data(li))
		_mask_imgs.append(mask.get_layer_data(li))
