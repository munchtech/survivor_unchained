// (demo-look r2 her, 16 Nov; judge 1: "nothing casts a shadow, so they float") Her cast shadow in the den: one quad on the
// ground at her feet (Actors/HerShadow.cs; the rig's hero_den row through View/HeroDen.cs). A painted cel shadow, not a hole:
// a contact ellipse under her feet joined to a short tapered trail away from the key, a hard edge (about one pixel, by fwidth
// of the shape's own distance in metres, so it neither blurs nor shimmers) with a slow painted wobble, and a deeper contact
// core under the feet. Its TONE is a deeper tone of what it sits on: the ground multiplied (blend_mul), by a cool multiplier
// that takes the earth's warmth down with its value, so the den grade lands it on warm umber (LOOK_BIBLE "Her shadow").
shader_type spatial;
render_mode unshaded, blend_mul, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

global uniform vec4 hero_cast_shape;   // contact half width, half depth (m), trail length, trail tip half width (m); x 0: off
global uniform vec4 hero_cast_mul;     // the ground's multiplier rgb (linear), w: the contact core's extra multiplier
uniform vec2 dir = vec2(0.77, 0.64);   // the trail's world direction (x, z), HerShadow sets it
varying vec3 wp;

void vertex() {
	wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

float trail(vec2 p, vec2 a, float len, float r0, float r1) {
	float t = clamp(dot(p, a) / max(len, 1e-3), 0.0, 1.0);
	return length(p - a * len * t) - mix(r0, r1, t);
}

void fragment() {
	if (hero_cast_shape.x <= 0.0) discard;
	vec2 p = wp.xz - NODE_POSITION_WORLD.xz;
	vec2 rr = hero_cast_shape.xy;
	float ell = (length(p / rr) - 1.0) * min(rr.x, rr.y);
	float ang = atan(p.y, p.x);
	// (the painted wobble: two slow waves round her, fixed to her, so the edge is a brush's and never a compass's)
	float wob = 0.035 * sin(ang * 5.0 + 1.3) + 0.02 * sin(ang * 9.0 + 0.4);
	float sd = min(ell, trail(p, normalize(dir), hero_cast_shape.z, rr.x * 0.75, hero_cast_shape.w)) + wob;
	float w = fwidth(sd) * 0.75 + 1e-4;
	float cover = 1.0 - smoothstep(-w, w, sd);
	float core = (length(p / (rr * vec2(0.62, 0.6))) - 1.0) * min(rr.x, rr.y) * 0.6 + wob * 0.5;
	float cw = fwidth(core) * 0.75 + 1e-4;
	float cc = 1.0 - smoothstep(-cw, cw, core);
	if (cover <= 0.001) discard;
	ALBEDO = mix(vec3(1.0), hero_cast_mul.rgb, cover) * mix(1.0, hero_cast_mul.w, cc);
}
