shader_type canvas_item;
// Screen-space finishing for the look rig (B_look): tilt-shift band blur, warm grade, vignette.
// Runs as a full-rect ColorRect on a CanvasLayer above the 3D view.

uniform sampler2D screen_tex : hint_screen_texture, filter_linear_mipmap;
uniform float focus_y = 0.55;        // screen y (0 top) of the sharp band centre
uniform float band_half = 0.17;      // half height of the sharp band
uniform float band_soft = 0.32;      // transition height
uniform float max_lod = 3.2;         // blur strength at the frame edges (mip level)
uniform float base_lod = 0.0;       // global lens softness (photo, not CG-crisp)
uniform float top_bias = 1.0;       // top (far) blurs more than bottom (near)
uniform float vignette = 0.38;
uniform vec4 shadow_tint : source_color = vec4(0.15, 0.165, 0.12, 1.0);  // sage-warm shadows
uniform vec4 highlight_tint : source_color = vec4(1.0, 0.95, 0.84, 1.0);
uniform float grade = 1.0;
uniform float saturation = 1.0;
uniform float contrast = 1.0;
uniform float lift = 0.012;
uniform float grain = 0.0;          // LOOKF r1: sensor grain (photo, not vector-clean)
uniform float toe = 0.0;            // LOOKF r1: crush the darkest stops a little (real shadow depth)
uniform float pre_gamma = 1.0;      // web only (LookRig.web_look): the Compatibility renderer's lifted tone curve, undone

vec3 sample_blur(vec2 uv, float lod, vec2 px) {
	if (lod < 0.02) return textureLod(screen_tex, uv, 0.0).rgb;
	vec2 o = px * exp2(lod) * 0.6;
	vec3 c = textureLod(screen_tex, uv, lod).rgb * 0.36;
	c += textureLod(screen_tex, uv + vec2(o.x, o.y), lod).rgb * 0.16;
	c += textureLod(screen_tex, uv + vec2(-o.x, o.y), lod).rgb * 0.16;
	c += textureLod(screen_tex, uv + vec2(o.x, -o.y), lod).rgb * 0.16;
	c += textureLod(screen_tex, uv + vec2(-o.x, -o.y), lod).rgb * 0.16;
	return c;
}

void fragment() {
	vec2 uv = SCREEN_UV;
	float dy = uv.y - focus_y;
	float d = max(abs(dy) - band_half, 0.0) / band_soft;
	float lod = base_lod + clamp(d, 0.0, 1.0) * max_lod * (dy < 0.0 ? top_bias : 1.0);
	vec3 c = sample_blur(uv, lod, SCREEN_PIXEL_SIZE);
	if (pre_gamma != 1.0) c = pow(max(c, vec3(0.0)), vec3(pre_gamma));
	// Grade: split-tone shadows warm-brown, highlights cream; saturation, contrast, lift.
	float l = dot(c, vec3(0.2126, 0.7152, 0.0722));
	vec3 g = c * mix(shadow_tint.rgb * 2.0 + 0.68, highlight_tint.rgb, smoothstep(0.05, 0.75, l));
	g = mix(vec3(l), g, saturation);
	g = (g - 0.45) * contrast + 0.45 + lift;
	g = mix(g, g * smoothstep(0.0, 0.35, l + 0.08), toe);
	c = mix(c, g, grade);
	if (grain > 0.0) {
		vec2 gp = floor(FRAGCOORD.xy * 0.75);
		float n = fract(sin(dot(gp, vec2(12.9898, 78.233)) + TIME * 7.0) * 43758.5453) - 0.5;
		c += n * grain * (0.6 + 0.8 * (1.0 - l));
	}
	vec2 v = uv - 0.5;
	float vig = 1.0 - vignette * smoothstep(0.25, 0.85, dot(v * vec2(1.1, 1.0), v * vec2(1.1, 1.0)) * 2.2);
	COLOR = vec4(max(c * vig, 0.0), 1.0);
}
