shader_type spatial;
render_mode cull_disabled, diffuse_burley;
// Folded (tented) cardstock rock (B_look). Printed grey-green stone with painterly strata strokes,
// a pale scored crease on the ridge and a darker foot where it meets the felt.
// UV.x along the ridge (world units), UV.y up the face (world units, ridge at ridge_h).

uniform vec4 base_color : source_color = vec4(0.56, 0.6, 0.53, 1.0);
uniform vec4 stroke_color : source_color = vec4(0.26, 0.32, 0.25, 1.0);
uniform float value = 0.78;  // printed stock reads darker than the raw tint under the key
uniform vec4 crease_color : source_color = vec4(0.88, 0.88, 0.78, 1.0);
uniform sampler2D felt_tex : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform float ridge_h = 0.3;
uniform float seed = 0.0;

void fragment() {
	vec2 uv = UV;
	float v = clamp(uv.y / max(ridge_h, 0.01), 0.0, 1.0);
	float m = texture(felt_tex, uv * 0.9 + seed).r - 0.5;
	float fib = texture(felt_tex, uv * 3.1 + seed * 0.7).g - 0.5;
	// strata strokes running roughly parallel to the ridge, wobbling
	float s = sin((v * 7.0 + m * 2.2 + uv.x * 0.6 + seed) * 3.14159);
	float stroke = smoothstep(0.55, 0.85, s) * 0.55 + smoothstep(0.75, 0.95, sin((v * 13.0 - uv.x * 1.3 + m * 3.0) * 3.14159)) * 0.3;
	vec3 col = mix(base_color.rgb * (1.0 + m * 0.35), stroke_color.rgb, stroke);
	// the face is printed: a thin cream die-cut border along the ridge crease
	col = mix(col, crease_color.rgb, smoothstep(0.93, 0.985, v) * 0.75);
	col *= mix(0.72, 1.0, smoothstep(0.0, 0.18, v));  // contact darkening at the foot
	ALBEDO = col * value * (1.0 + fib * 0.22);
	ROUGHNESS = 0.95;
	SPECULAR = 0.06;
	NORMAL_MAP = normalize(vec3(0.5 + fib * 0.35, 0.5 + m * 0.2, 1.0));
	NORMAL_MAP_DEPTH = 0.5;
	BACKLIGHT = col * 0.08;
}
