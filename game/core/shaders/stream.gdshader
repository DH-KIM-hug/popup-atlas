shader_type spatial;
render_mode cull_back, diffuse_burley;
// Layered cut-PAPER stream (2026-11-22, user: "다 종이로 변경"): no felt nap. The channel is three sheets of
// teal / blue paper stacked from the banks inward (shallow on top, deep at the bottom), each with a softly torn
// (deckled) edge: a thin lit rim on the cut and a narrow contact shadow on the sheet below. Cream ripple SLIVERS are
// small cut paper lenses glued on the water with their own little shadow; they drift slowly. Fine paper-fibre grain,
// a gentle broad sheen (a varnished paper, not wet glass).
// UV.x along flow (world units), UV.y across 0..1.

uniform vec4 deep_color : source_color = vec4(0.10, 0.42, 0.44, 1.0);
uniform vec4 shallow_color : source_color = vec4(0.30, 0.66, 0.62, 1.0);
uniform vec4 ripple_color : source_color = vec4(0.86, 0.93, 0.86, 1.0);
uniform sampler2D felt_tex : hint_default_white, filter_linear_mipmap, repeat_enable;  // noise only (R/G/B)
uniform sampler2D fibre_tex : hint_default_white, filter_linear_mipmap, repeat_enable;  // paper fibre photo
uniform float flow_speed = 0.04;
uniform float ripple_amount = 1.0;
uniform float width_world = 0.78;  // channel width in world units (UV.y 0..1)

float hash1(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }

float nz(float x, float row) { return texture(felt_tex, vec2(x, row)).r - 0.5; }

// torn sheet boundary (in "edge" units 0 centre .. 1 bank): slow wander + a fine deckle
float torn(float x, float base, float row) {
	return base + nz(x * 0.045, row) * 0.16 + nz(x * 0.42, row + 0.31) * 0.035;
}

void fragment() {
	float across = UV.y;
	float x = UV.x;
	float side = across < 0.5 ? 0.0 : 0.5;  // each bank tears its own way
	float e = abs(across - 0.5) * 2.0;
	float b_mid = torn(x, 0.36, 0.13 + side);
	float b_sh = torn(x, 0.70, 0.57 + side);
	vec3 mid_col = mix(deep_color.rgb, shallow_color.rgb, 0.5);
	vec3 col;
	float rim = 0.0;
	float shade = 1.0;
	float aa = fwidth(e) * 1.2 + 0.002;
	if (e > b_sh) {
		col = shallow_color.rgb;
		rim = 1.0 - smoothstep(0.0, 0.016, e - b_sh);
	} else if (e > b_mid) {
		col = mid_col;
		rim = 1.0 - smoothstep(0.0, 0.014, e - b_mid);
		shade = mix(0.78, 1.0, smoothstep(0.0, 0.07, b_sh - e));  // shadow of the shallow sheet above
	} else {
		col = deep_color.rgb;
		shade = mix(0.8, 1.0, smoothstep(0.0, 0.07, b_mid - e));
	}
	// antialias the sheet steps a little (no hard aliasing stair)
	col = mix(col, col * 0.86, (1.0 - smoothstep(0.0, aa, abs(e - b_sh))) * 0.5);
	col = mix(col, col * 0.86, (1.0 - smoothstep(0.0, aa, abs(e - b_mid))) * 0.5);
	col *= shade;
	col *= 1.0 + rim * 0.16;

	// cut cream ripple slivers: lenses in three lanes, drifting with the flow, each with a little shadow below
	float t = TIME * flow_speed;
	float rip = 0.0;
	float rip_sh = 0.0;
	float daa = fwidth(across) * 1.2 + 0.001;
	for (int i = 0; i < 3; i++) {
		float fi = float(i);
		float lane = 0.5 + (fi - 1.0) * 0.21;
		float len = 0.55 + fi * 0.12;
		float u = (x - t * (1.0 + fi * 0.25)) / len + fi * 0.37;
		float cell = floor(u);
		float r = hash1(vec2(cell, fi));
		if (r < 0.55) {
			float fx = fract(u);
			float k = 0.18 + 0.5 * hash1(vec2(cell, fi + 7.0));  // sliver length within its cell
			float s0 = 0.1 + (0.8 - k) * hash1(vec2(cell, fi + 3.0));
			float q = (fx - s0) / k;
			if (q > 0.0 && q < 1.0) {
				float hw = 0.022 * sin(3.14159 * q) * (0.7 + 0.6 * r) / width_world * 0.78;
				float wv = sin(x * 2.3 + fi * 1.9) * 0.03 + (hash1(vec2(cell, fi + 11.0)) - 0.5) * 0.08;
				float d = across - lane - wv;
				rip = max(rip, 1.0 - smoothstep(hw - daa, hw + daa, abs(d)));
				rip_sh = max(rip_sh, 1.0 - smoothstep(hw - daa, hw + daa * 3.0, abs(d - 0.018)));
			}
		}
	}
	col *= 1.0 - rip_sh * (1.0 - rip) * 0.22 * ripple_amount;
	col = mix(col, ripple_color.rgb, rip * ripple_amount);

	// paper fibre grain (fibre photo, world-scaled) + a faint mottle
	vec2 fp = vec2(x, across * width_world);
	float fib = texture(fibre_tex, fp * 1.7).g - 0.5;
	float fine = texture(felt_tex, fp * 4.0 + 0.2).b - 0.5;
	float mott = nz(x * 0.08, 0.77) * 0.5 + (texture(felt_tex, fp * 0.35).r - 0.5) * 0.5;
	col *= 1.0 + fib * 0.16 + fine * 0.05 + mott * 0.08;
	ALBEDO = col;
	ROUGHNESS = mix(0.5, 0.95, rip);
	SPECULAR = mix(0.28, 0.05, rip);
	NORMAL_MAP = normalize(vec3(0.5 + fib * 0.18, 0.5 + fine * 0.1, 1.0));
	NORMAL_MAP_DEPTH = 0.35;
}
