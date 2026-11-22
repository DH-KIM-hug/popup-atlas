shader_type spatial;
render_mode cull_disabled, diffuse_burley;
// Folded (tented) cardstock rock, CUT PAPER look (2026-11-22, felt -> paper): each face is layered torn grey-green
// paper bands (a few tones stacked up the face, torn edges with a thin dark cut line and a lit rim), a pale scored
// crease on the ridge, a darker foot where it meets the ground sheet, paper fibre. No wool / painterly fuzz.
// UV.x along the ridge (world units), UV.y up the face (world units, ridge at ridge_h).

uniform vec4 base_color : source_color = vec4(0.56, 0.6, 0.53, 1.0);
uniform vec4 stroke_color : source_color = vec4(0.26, 0.32, 0.25, 1.0);
uniform float value = 0.78;  // printed stock reads darker than the raw tint under the key
uniform vec4 crease_color : source_color = vec4(0.88, 0.88, 0.78, 1.0);
uniform sampler2D felt_tex : hint_default_white, filter_linear_mipmap, repeat_enable;  // noise only
uniform sampler2D fibre_tex : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform float ridge_h = 0.3;
uniform float seed = 0.0;

void fragment() {
	vec2 uv = UV;
	float v = clamp(uv.y / max(ridge_h, 0.01), 0.0, 1.0);
	// torn band boundaries running roughly along the ridge
	float wob = (texture(felt_tex, vec2(uv.x * 0.55 + seed, 0.21)).r - 0.5) * 0.5
		+ (texture(felt_tex, vec2(uv.x * 3.7 + seed, 0.63)).r - 0.5) * 0.12;
	float q = v * 3.2 + wob + seed * 0.13;
	float band = floor(q);
	float f = fract(q);
	float aa = fwidth(q) * 1.5 + 0.01;
	float t = fract(sin((band + floor(seed * 3.0)) * 7.31) * 413.7);
	vec3 col = mix(base_color.rgb, mix(base_color.rgb, stroke_color.rgb, 0.45), t * 0.8);
	col *= mix(0.84, 1.0, smoothstep(0.0, 0.12, f));                 // shade just above the sheet below
	col *= 1.0 + (1.0 - smoothstep(0.9, 0.9 + aa * 2.0, 1.0 - f)) * 0.0;
	col = mix(col, col * 0.62, 1.0 - smoothstep(0.0, aa * 1.5, abs(f - 0.0)));  // thin dark cut line at the tear
	col *= 1.0 + (smoothstep(0.88, 0.97, f)) * 0.12;                 // lit rim on the upper torn edge
	// a few small cut flecks (moss / darker stone) as paper bits
	float fl = texture(felt_tex, uv * 1.7 + seed).b;
	col = mix(col, stroke_color.rgb * 1.1, smoothstep(0.86, 0.88, fl) * 0.6);
	// the face is printed: a thin cream scored crease along the ridge
	col = mix(col, crease_color.rgb, smoothstep(0.95, 0.99, v) * 0.6);
	col *= mix(0.72, 1.0, smoothstep(0.0, 0.18, v));  // contact darkening at the foot
	float fib = texture(fibre_tex, uv * 1.4 + seed).g - 0.5;
	ALBEDO = col * value * (1.0 + fib * 0.14);
	ROUGHNESS = 0.96;
	SPECULAR = 0.05;
	NORMAL_MAP = normalize(vec3(0.5 + fib * 0.15, 0.5 + (smoothstep(0.88, 0.97, f) - (1.0 - smoothstep(0.0, 0.1, f))) * 0.25, 1.0));
	NORMAL_MAP_DEPTH = 0.4;
	BACKLIGHT = col * 0.06;
}
