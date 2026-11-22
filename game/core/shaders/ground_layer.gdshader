shader_type spatial;
render_mode cull_back, diffuse_burley, specular_disabled;
// Flat cut-paper ground layers (felt ground, path, ground-cover patches, book page). World-aligned.
// felt_tex: R low-freq mottling, G fibres, B fine grain.

uniform vec4 base_color : source_color = vec4(0.4, 0.5, 0.25, 1.0);
uniform vec4 mottle_color : source_color = vec4(0.32, 0.42, 0.2, 1.0);
uniform sampler2D felt_tex : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform float mottle_scale = 0.09;
uniform float mottle_strength = 0.7;
uniform float fibre_scale = 0.9;
uniform float fibre_strength = 0.13;
uniform float grain_strength = 0.1;
uniform float bump = 0.5;
// LOOKF r1: mid-scale wool clumps (felt nap seen by a macro lens), 0 = off.
uniform float clump_strength = 0.0;
uniform float clump_scale = 0.31;
// Printed speckle (tiny ink flecks) for path / page cards.
uniform float speckle = 0.0;
uniform vec4 speckle_color : source_color = vec4(0.55, 0.42, 0.28, 1.0);
// sunmoon 2026-11-22 (user: "펠트 질감 싫은뎅"): 1 = matte cut / torn PAPER sheets instead of felt: no wool nap or
// clumps, a faint mottle, a fine paper-fibre tooth and almost no bump. 0 (default) = the felt every other tale uses.
uniform float paper = 0.0;
// Darken toward the polygon edge (UV.y = distance to edge in world units, 0 when unused).
uniform float edge_shade = 0.0;
varying vec3 wpos;

void vertex() { wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; }

void fragment() {
	vec2 p = wpos.xz;
	float mott = texture(felt_tex, p * mottle_scale).r - 0.5;
	float mott2 = texture(felt_tex, p * mottle_scale * 2.3 + 0.37).r - 0.5;
	// LOOKF r1: fibre layers at unrelated angles and warped by the mottling, so the nap reads as matted
	// wool, not a woven hatch.
	vec2 pw = p + vec2(mott2, mott) * 0.5;
	vec2 pa = vec2(pw.x * 0.81 - pw.y * 0.59, pw.x * 0.59 + pw.y * 0.81);
	vec2 pb = vec2(pw.x * -0.33 - pw.y * 0.94, pw.x * 0.94 - pw.y * 0.33);
	float fib = (texture(felt_tex, pa * fibre_scale).g + texture(felt_tex, pb * fibre_scale * 0.73 + 0.21).g) * 0.5 - 0.5;
	fib *= 1.25;
	float fine = texture(felt_tex, pb * fibre_scale * 3.1 + 0.11).b - 0.5;
	float ms = mix(mottle_strength, mottle_strength * 0.22, paper);
	float m = clamp(0.5 + (mott * 1.6 + mott2 * 0.8) * ms, 0.0, 1.0);
	vec3 col = mix(base_color.rgb, mottle_color.rgb, m);
	float clump = 0.0;
	float cs = clump_strength * (1.0 - paper);
	if (cs > 0.0) {
		vec3 ct = texture(felt_tex, pa * clump_scale + 0.63).rgb;
		clump = ct.g + ct.b - 1.0;
		col *= 1.0 + clump * cs;
		col = mix(col, col * vec3(1.06, 1.03, 0.9), clamp(clump * 2.0, 0.0, 1.0) * cs);
	}
	float fs = mix(fibre_strength, 0.035, paper);
	float gs = mix(grain_strength, 0.06, paper);
	col *= 1.0 + fib * fs * 2.0 + fine * gs * 2.0;
	if (speckle > 0.0) {
		float s = texture(felt_tex, p * 5.3).b;
		float s2 = texture(felt_tex, p * 2.1 + 0.5).g;
		float fleck = smoothstep(0.80, 0.86, s) * smoothstep(0.55, 0.7, s2);
		col = mix(col, speckle_color.rgb, fleck * speckle);
	}
	ALBEDO = col;
	ROUGHNESS = 0.98;
	SPECULAR = 0.04;
	NORMAL_MAP = normalize(vec3(0.5 + (fib + fine) * 0.4 + clump * cs * 0.5, 0.5 + (fib - fine) * 0.3 - clump * cs * 0.4, 1.0));
	NORMAL_MAP_DEPTH = mix(bump, 0.25, paper);
}
