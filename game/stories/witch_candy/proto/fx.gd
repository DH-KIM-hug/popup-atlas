extends TaleHandler
## witch_candy phase-1 PROTOTYPE handler (2026-11-19): warm light sources for the night street and the shop room, so
## the stills show where phase 2's night dress gets its light (lanterns, lit windows, the hearth). Not the final
## implementation: phase 2 moves this into the night-street dress / RoomBox template.

const WARM := Color(1.0, 0.68, 0.36)


func setup() -> void:
	# a warm omni light at every lamp post / pumpkin lantern / lit window spot named in the proto's `lights` list
	var lights: Array = stage.tale.get("proto_lights", [])
	for l: Array in lights:
		var o := OmniLight3D.new()
		o.light_color = Color(l[3]) if l.size() > 3 else WARM
		o.light_energy = float(l[2])
		o.omni_range = float(l[4]) if l.size() > 4 else 0.9
		o.shadow_enabled = false
		add_child(o)
		var p := stage.spot_point(l[0])
		o.global_position = p + Vector3(0, float(l[1]), 0)
