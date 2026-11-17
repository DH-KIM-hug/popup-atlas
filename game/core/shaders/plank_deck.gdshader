shader_type spatial;
render_mode cull_back, diffuse_burley, specular_disabled;
// Printed plank deck of the paper bridge (integrator r1): warm boards across the road, dark gaps, grain.
uniform vec4 wood : source_color = vec4(0.66, 0.53, 0.37, 1.0);
uniform vec4 gap : source_color = vec4(0.30, 0.20, 0.12, 1.0);
uniform vec2 along = vec2(0.0, 1.0);  // road direction on the page (boards run across it)
uniform float board = 0.075;
uniform sampler2D felt_tex : hint_default_white, filter_linear_mipmap, repeat_enable;
varying vec3 wpos;
void vertex() { wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; }
void fragment() {
	float s = dot(wpos.xz, normalize(along)) / board;
	float id = floor(s);
	float f = fract(s);
	float g = smoothstep(0.0, 0.08, f) * smoothstep(1.0, 0.92, f);
	float tone = 0.88 + 0.24 * fract(sin(id * 12.9898) * 43758.5453);
	float grain = texture(felt_tex, vec2(dot(wpos.xz, vec2(-along.y, along.x)) * 0.6, s * 0.21)).g - 0.5;
	ALBEDO = mix(gap.rgb, wood.rgb * tone * (1.0 + grain * 0.35), g);
	ROUGHNESS = 0.95;
}
