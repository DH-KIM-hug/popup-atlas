shader_type spatial;
render_mode cull_disabled, world_vertex_coords;
// Shadow-only stand-in for every batched card (component F, perf): one quad per card in ONE MultiMesh
// (SHADOWS_ONLY), instead of each card's full print+back+wall mesh in every shadow split.
// The quad covers the whole print texture at the light-facing face plane (+hz print face, -hz back) and keeps exactly
// what the original faces kept: print alpha >= 0.5 (mirrored on the back face, like the back's UVs) inside the cut
// contour (mask = the alpha bitmap the contour was traced from). INSTANCE_CUSTOM = (print index, amp, freq, phase).
#include "res://core/world/shaders/card_wind.gdshaderinc"

uniform sampler2DArray atlas : source_color, filter_linear_mipmap_anisotropic, repeat_disable;
uniform sampler2DArray mask_atlas : filter_linear, repeat_disable;
uniform sampler2D params : filter_nearest, repeat_disable;

varying flat vec4 v_rect;
varying flat float v_layer;
varying flat float v_front;

void vertex() {
	int idx = int(INSTANCE_CUSTOM.x + 0.5);
	v_rect = texelFetch(params, ivec2(idx, 0), 0);
	vec4 p1 = texelFetch(params, ivec2(idx, 1), 0);
	vec4 q = texelFetch(params, ivec2(idx, 3), 0);
	v_layer = p1.x;
	vec3 o = MODEL_MATRIX[3].xyz;
	mat3 r = card_sway(INSTANCE_CUSTOM, o);
	vec3 n = r * MODEL_MATRIX[2].xyz;
	// Which face the light camera sees (cull_back on the original faces).
	v_front = dot(n, INV_VIEW_MATRIX[2].xyz) >= 0.0 ? 1.0 : 0.0;
	// One quad at the light-facing face plane (a second quad on the mid / far plane for the cut walls was tried:
	// it shadowed the camera-side face of back-lit cards, worse than leaving the 1-4 mm walls out).
	float plane = v_front > 0.5 ? p1.w : -p1.w;
	vec3 local = vec3(q.x + UV.x * q.z, q.y - UV.y * q.w, plane);
	vec3 wp = (MODEL_MATRIX * vec4(local, 1.0)).xyz;
	VERTEX = o + r * (wp - o);
	NORMAL = normalize(n) * (v_front > 0.5 ? 1.0 : -1.0);
}

void fragment() {
	vec2 dux = dFdx(UV);
	vec2 duy = dFdy(UV);
	vec2 uv = v_front > 0.5 ? UV : vec2(1.0 - UV.x, UV.y);
	vec2 ux = v_front > 0.5 ? dux : vec2(-dux.x, dux.y);
	vec2 uy = v_front > 0.5 ? duy : vec2(-duy.x, duy.y);
	float a = textureGrad(atlas, vec3(v_rect.xy + fract(uv) * v_rect.zw, v_layer), ux * v_rect.zw, uy * v_rect.zw).a;
	float m = texture(mask_atlas, vec3(v_rect.xy + clamp(UV, 0.0, 1.0) * v_rect.zw, v_layer)).r;
	if (a < 0.5 || m < 0.5) discard;
	ALBEDO = vec3(0.0);
}
