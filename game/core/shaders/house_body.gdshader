shader_type spatial;
render_mode cull_back, diffuse_burley, specular_schlick_ggx;
// House body faces (2026-11-23, game/core/world/house_body.gd): the side walls, roof, soffits, back and chimney of a
// house card's extruded body, printed with crops of the house's own art. Same ink / fibre / sheen as paper_print so the
// body reads as the same card stock as the front; the print repeats (mirror-tiled crops) instead of clamping.

uniform sampler2D albedo_tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D fibre_tex : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform float fibre_density = 7.0;
uniform float fibre_strength = 0.16;
uniform float shade = 1.0;  // inner faces / soffits darker
uniform float ink_saturation = 1.12;
uniform float ink_contrast = 1.06;
uniform float foot_ao_height = 0.05;
uniform float foot_ao_strength = 0.35;
uniform float translucency = 0.12;
uniform float glow = 0.0;
uniform vec4 glow_color : source_color = vec4(1.0, 0.72, 0.36, 1.0);

varying float h_local;
varying vec3 w_pos;

void vertex() {
	h_local = VERTEX.y;
	w_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec3 col = texture(albedo_tex, UV).rgb;
	float l = dot(col, vec3(0.299, 0.587, 0.114));
	col = mix(vec3(l), col, ink_saturation);
	col = clamp((col - 0.5) * ink_contrast + 0.5, 0.0, 1.0);
	vec2 fuv = vec2(w_pos.x + w_pos.z, w_pos.y) * fibre_density;
	float f = texture(fibre_tex, fuv).r;
	float f2 = texture(fibre_tex, fuv * 2.7 + 0.31).r;
	float fibre = mix(f, f2, 0.4) - 0.5;
	float ao = mix(1.0 - foot_ao_strength, 1.0, smoothstep(0.0, foot_ao_height, h_local));
	ALBEDO = col * (1.0 + fibre * fibre_strength * 2.0) * ao * shade;
	ROUGHNESS = 0.78 - fibre * 0.2;
	SPECULAR = 0.2;
	NORMAL_MAP = normalize(vec3(0.5 + fibre * 0.35, 0.5 - fibre * 0.25, 1.0));
	NORMAL_MAP_DEPTH = 0.5;
	BACKLIGHT = col * translucency * shade;
	if (glow > 0.0) {
		float mx = max(col.r, max(col.g, col.b));
		float mn = min(col.r, min(col.g, col.b));
		float lum = dot(col, vec3(0.299, 0.587, 0.114));
		float warm = smoothstep(0.05, 0.2, col.r - col.b) * smoothstep(0.68, 0.84, lum) * smoothstep(0.25, 0.5, (mx - mn) / max(mx, 0.001));
		EMISSION = mix(col, glow_color.rgb, 0.35) * warm * glow * shade;
	}
}
