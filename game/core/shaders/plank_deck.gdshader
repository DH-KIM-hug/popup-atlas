shader_type spatial;
render_mode cull_back, diffuse_burley, specular_disabled;
// Plank deck of the paper bridge, as CUT PAPER (2026-11-22, felt -> paper): every board is its own strip of brown
// paper glued across the road, slightly different tone and a little ragged at the ends, a thin dark cut line on its
// far edge with a lit rim on its near edge and a narrow shadow gap between boards; a few printed grain lines and the
// fibre of the paper. No wool noise.
uniform vec4 wood : source_color = vec4(0.66, 0.53, 0.37, 1.0);
uniform vec4 gap : source_color = vec4(0.30, 0.20, 0.12, 1.0);
uniform vec2 along = vec2(0.0, 1.0);  // road direction on the page (boards run across it)
uniform float board = 0.075;
uniform sampler2D felt_tex : hint_default_white, filter_linear_mipmap, repeat_enable;  // noise only
uniform sampler2D fibre_tex : hint_default_white, filter_linear_mipmap, repeat_enable;
varying vec3 wpos;
void vertex() { wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; }
float h1(float x) { return fract(sin(x * 12.9898) * 43758.5453); }
void fragment() {
	vec2 a = normalize(along);
	float u = dot(wpos.xz, vec2(-a.y, a.x));  // across the road
	float s0 = dot(wpos.xz, a) / board;
	// each strip is cut a little crooked: its edges wander with a slow per-board tilt + a fine deckle
	float id = floor(s0);
	float s = s0 + (h1(id) - 0.5) * 0.12 * sin(u * 3.0 + id) + (texture(felt_tex, vec2(u * 0.9, id * 0.37)).r - 0.5) * 0.06;
	id = floor(s);
	float f = fract(s);
	float aa = fwidth(s) * 1.5 + 0.01;
	float body = smoothstep(0.06, 0.06 + aa, f) * smoothstep(0.97, 0.97 - aa, f);
	float rim = (1.0 - smoothstep(0.06, 0.16, f)) * body;        // lit near edge
	float cut = smoothstep(0.86, 0.97, f) * body;               // darker far edge (the cut line)
	float tone = 0.86 + 0.26 * h1(id + 3.1);
	vec3 col = wood.rgb * tone;
	float gl = sin(u * (38.0 + 9.0 * h1(id)) + h1(id + 7.0) * 6.0 + f * 2.0);
	col *= 1.0 - smoothstep(0.93, 0.99, gl) * 0.18;              // a few printed grain lines
	float fib = texture(fibre_tex, vec2(u, s0 * board) * 1.8).g - 0.5;
	col *= 1.0 + fib * 0.14;
	col *= 1.0 + rim * 0.14 - cut * 0.22;
	vec3 g = gap.rgb * (0.9 + 0.2 * h1(id + 1.7));
	ALBEDO = mix(g, col, body);
	ROUGHNESS = 0.95;
	NORMAL_MAP = normalize(vec3(0.5, 0.5 + (rim - cut) * 0.35 + fib * 0.1, 1.0));
	NORMAL_MAP_DEPTH = 0.6;
}
