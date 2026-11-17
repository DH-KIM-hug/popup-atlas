shader_type spatial;
render_mode cull_back, diffuse_burley, specular_schlick_ggx;
// Printed face of a cut-paper card (B_look owns). Uniform names used by PaperCard stay stable:
// albedo_tex, fibre_tex, card_size, plain, plain_color, translucency.

uniform sampler2D albedo_tex : source_color, filter_linear_mipmap_anisotropic;
uniform sampler2D fibre_tex : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform vec2 card_size = vec2(0.4);
uniform float fibre_density = 7.0;   // repeats per world unit
uniform float fibre_strength = 0.16;
uniform bool plain = false;
uniform vec4 plain_color : source_color = vec4(0.93, 0.89, 0.8, 1.0);
uniform float translucency = 0.32;   // light through thin paper from behind
// Die-cut cream rim just inside the cut line (world units).
uniform float rim_width = 0.003;  // PE r3: 0.0024 -> 0.003 (INT r1 0.006 read as a sticker halo; critics still ask for the cut-edge band)
uniform float rim_mix = 0.48;  // PE r3: 0.35 -> 0.48, the die-cut core shows as a light band (INT r3 had cut it to 0.35)
uniform vec4 rim_color : source_color = vec4(0.97, 0.92, 0.80, 1.0);
// Baked contact darkening near the hinge (world units of card height).
uniform float foot_ao_height = 0.06;
uniform float foot_ao_strength = 0.42;
// Ink: a little extra saturation/contrast so prints read like offset printing, not photos.
uniform float ink_saturation = 1.12;
uniform float ink_contrast = 1.06;

float alpha_at(vec2 uv) { return textureLod(albedo_tex, uv, 0.0).a; }

void fragment() {
	vec4 c = plain ? plain_color : texture(albedo_tex, UV);
	if (!plain && c.a < 0.5) discard;
	vec3 col = c.rgb;
	if (!plain) {
		float l = dot(col, vec3(0.299, 0.587, 0.114));
		col = mix(vec3(l), col, ink_saturation);
		col = clamp((col - 0.5) * ink_contrast + 0.5, 0.0, 1.0);
		// Rim: any transparent texel within rim_width means we are on the cut border.
		// Small cards get a thinner rim so thin leaves/grass are not swallowed (A0 note).
		float rw = rim_width * clamp(card_size.y / 0.35, 0.45, 1.0);
		vec2 r = vec2(rw) / max(card_size, vec2(0.01));
		float m = 1.0;
		m = min(m, alpha_at(UV + vec2(r.x, 0.0)));
		m = min(m, alpha_at(UV - vec2(r.x, 0.0)));
		m = min(m, alpha_at(UV + vec2(0.0, r.y)));
		m = min(m, alpha_at(UV - vec2(0.0, r.y)));
		m = min(m, alpha_at(UV + r * 0.7071));
		m = min(m, alpha_at(UV - r * 0.7071));
		m = min(m, alpha_at(UV + vec2(r.x, -r.y) * 0.7071));
		m = min(m, alpha_at(UV + vec2(-r.x, r.y) * 0.7071));
		// Do not draw the rim along the hinge (bottom) edge.
		float not_bottom = step(UV.y, 0.985);
		col = mix(col, rim_color.rgb, (1.0 - smoothstep(0.25, 0.6, m)) * not_bottom * rim_mix);
	}
	vec2 fuv = UV * card_size * fibre_density;
	float f = texture(fibre_tex, fuv).r;
	float f2 = texture(fibre_tex, fuv * 2.7 + 0.31).r;
	float fibre = mix(f, f2, 0.4) - 0.5;
	float h = (1.0 - UV.y) * card_size.y;
	float ao = mix(1.0 - foot_ao_strength, 1.0, smoothstep(0.0, foot_ao_height, h));
	ALBEDO = col * (1.0 + fibre * fibre_strength * 2.0) * ao;
	// weak satin sheen of printed cardstock (matte ink, slightly glossy coating)
	ROUGHNESS = 0.74 - fibre * 0.2;
	SPECULAR = 0.22;
	NORMAL_MAP = normalize(vec3(0.5 + fibre * 0.35, 0.5 - fibre * 0.25, 1.0));
	NORMAL_MAP_DEPTH = 0.6;
	BACKLIGHT = col * translucency;
}
