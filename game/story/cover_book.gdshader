shader_type spatial;
// Book-cover materials (game/story/cover_book.gd), one shader with a mode switch so the cover scene compiles few
// pipelines: 0 = printed board (art texture, matte laminate paper), 1 = page block fore-edge (fine page lines),
// 2 = endpaper (tale colour, small printed motif, paper fibre), 3 = wooden table (planks + grain), 4 = plain paper /
// cloth (tint + fibre). All matte: paper, not plastic.
render_mode diffuse_burley, specular_schlick_ggx;

uniform int mode = 0;
uniform sampler2D tex : source_color, filter_linear_mipmap_anisotropic, repeat_disable;
uniform vec4 tint : source_color = vec4(1.0);
uniform vec4 tint2 : source_color = vec4(0.8, 0.7, 0.5, 1.0);
uniform float lines = 220.0;   // page lines across the block thickness
uniform float motif = 9.0;     // endpaper motif repeats across
uniform float roughness_v = 0.88;
uniform vec4 uv_rect = vec4(0.0, 0.0, 1.0, 1.0);  // mode 0: sub-rect of the art (x, y, w, h)

float h21(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float vnoise(vec2 p) {
	vec2 i = floor(p); vec2 f = fract(p); f = f * f * (3.0 - 2.0 * f);
	return mix(mix(h21(i), h21(i + vec2(1, 0)), f.x), mix(h21(i + vec2(0, 1)), h21(i + vec2(1, 1)), f.x), f.y);
}
float fbm(vec2 p) { float a = 0.5; float s = 0.0; for (int i = 0; i < 4; i++) { s += a * vnoise(p); p *= 2.03; a *= 0.5; } return s; }

void fragment() {
	vec3 c = tint.rgb;
	float rough = roughness_v;
	float fib = fbm(UV * vec2(520.0, 360.0)) - 0.5;  // paper fibre tooth
	if (mode == 0) {
		c = texture(tex, uv_rect.xy + UV * uv_rect.zw).rgb * tint.rgb;
		c *= 1.0 + fib * 0.05;
		rough = 0.74;  // printed matte laminate: a whisper of sheen under the raking key
	} else if (mode == 1) {
		float v = UV.y * lines;
		float l = smoothstep(0.35, 0.5, abs(fract(v) - 0.5));
		float n = vnoise(vec2(UV.x * 40.0, floor(v))) * 0.06;
		c = tint.rgb * (0.93 + 0.07 * (1.0 - l) - n);
	} else if (mode == 2) {
		vec2 q = UV * vec2(motif, motif * 0.66);
		vec2 cell = floor(q);
		vec2 f = fract(q) - 0.5;
		f.x += (mod(cell.y, 2.0) - 0.5) * 0.5;
		f = fract(f + 0.5) - 0.5;
		float star = smoothstep(0.17, 0.14, length(f) + 0.06 * sin(atan(f.y, f.x) * 5.0));
		c = mix(tint.rgb, tint2.rgb, star * 0.85);
		c *= 1.0 + fib * 0.08;
	} else if (mode == 3) {
		// planks along x, 0.34 wide; grain = stretched noise, warm walnut / oak
		vec2 p = UV * 13.0;
		float plank = floor(p.y / 0.34);
		float py = fract(p.y / 0.34);
		float off = h21(vec2(plank, 3.0)) * 10.0;
		float g = fbm(vec2((p.x + off) * 0.9, p.y * 22.0 + plank * 7.0));
		float rings = sin((p.y * 30.0 + g * 6.0 + off) ) * 0.5 + 0.5;
		vec3 base = mix(tint.rgb, tint2.rgb, h21(vec2(plank, 9.0)) * 0.5 + g * 0.5);
		c = base * (0.86 + 0.14 * rings);
		float seam = smoothstep(0.0, 0.025, py) * smoothstep(1.0, 0.975, py);
		c *= mix(0.55, 1.0, seam);
		rough = 0.62 + 0.2 * g;
	} else {
		c *= 1.0 + fib * 0.07;
	}
	ALBEDO = c;
	ROUGHNESS = rough;
	SPECULAR = 0.25;
}
