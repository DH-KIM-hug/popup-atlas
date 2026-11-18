// Shared by the batched card shaders (component F, perf). WindSway's rocking, moved from the CPU to the vertex
// shader for cards drawn through CardBatch. Same formula as core/world/wind_sway.gd:
//   g = (0.5 + 0.5 sin((t * gust_speed - along) * 0.9))^2
//   a = amp * strength * (0.35 + 0.65 g) * (0.6 + 0.4 sin(t * freq * TAU + phase))
//   basis = Basis(axis, a) * rest   (rotation about the card base, axis across the wind)
// INSTANCE_CUSTOM = (k, amp, freq, phase); along = dot(base.xz, wind_dir0) (wind_dir at add time).
uniform vec4 wind = vec4(0.0, 1.0, 1.4, 0.0);  // t, strength, gust_speed, -
uniform vec3 wind_axis = vec3(0.33, 0.0, 0.94);
uniform vec2 wind_dir0 = vec2(0.944, -0.330);

mat3 card_axis_rot(vec3 k, float a) {
	float c = cos(a);
	float s = sin(a);
	float t = 1.0 - c;
	return mat3(
		vec3(c + k.x * k.x * t, k.y * k.x * t + k.z * s, k.z * k.x * t - k.y * s),
		vec3(k.x * k.y * t - k.z * s, c + k.y * k.y * t, k.z * k.y * t + k.x * s),
		vec3(k.x * k.z * t + k.y * s, k.y * k.z * t - k.x * s, c + k.z * k.z * t));
}

// Sway rotation for this instance (identity when amp == 0).
mat3 card_sway(vec4 custom, vec3 origin) {
	float amp = custom.y;
	if (amp <= 0.0) {
		return mat3(1.0);
	}
	float along = dot(origin.xz, wind_dir0);
	float g = 0.5 + 0.5 * sin((wind.x * wind.z - along) * 0.9);
	g = g * g;
	float a = amp * wind.y * (0.35 + 0.65 * g) * (0.6 + 0.4 * sin(wind.x * custom.z * 6.283185307179586 + custom.w));
	return card_axis_rot(wind_axis, a);
}
