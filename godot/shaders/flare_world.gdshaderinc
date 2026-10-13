// The Flare on the world (docs/design/FLARE_LOOK.md §1.5, §4): what every world material does while a Flare
// plays, read from global uniforms the view sets each frame (Fx/Flare/FlareFx.cs), so nothing needs a mask.
// The drain and the repaint: the world (ground, crowd, props) loses its colour at the press and gets it back
// from her outward at the Spend; she, the Flare's own light and every danger mark never read these, so they
// keep theirs. The web: a hairline of ember under the ground in the reach (the Draw), glowing again as the
// light sinks (the Return). Burns Twice's frost: a growth-time map (distance, low noise, fingers that race
// ahead), its crystal two multiplied layers of our own frost plate so it never visibly repeats; impacts melt
// it to wet ground and char. Everything here costs one uniform branch while no Flare plays.

global uniform vec4 flare_at;     // xyz: where she stood at the press; w: the reach (m)
global uniform vec4 flare_look;   // x: drain 0..1; y: repaint radius (m); z: the repaint's cold 0..1; w: kind (0 none, 1 Burns Twice, 2 its Black Ice)
global uniform vec4 flare_web;    // x: web light 0..1; y: heat (1 the calling's hue .. 0 dark); z: how far it has lit (m); w: seed
global uniform vec4 flare_frost;  // x: the front (m); y: frost alive 0..1; z: melted in from the edge (m); w: seconds since the frost
global uniform vec4 flare_hue;    // rgb: the web's hot colour (the calling's); a: night 0..1
global uniform sampler2D flare_plate : filter_linear_mipmap_anisotropic, repeat_enable;
global uniform sampler2D flare_noise : filter_linear_mipmap, repeat_enable;
global uniform sampler2D flare_marks : filter_nearest, repeat_disable; // 32x1: an impact's x, z, radius, age (s); radius 0: none

const vec3 FL_LUM = vec3(0.2126, 0.7152, 0.0722);

bool flare_live() {
	return flare_look.x > 0.0 || flare_look.w > 0.5 || flare_web.x > 0.0;
}

// The drain and the repaint, on a world colour.
void flare_drain(vec3 wp, inout vec3 alb, inout vec3 emi) {
	float dr = flare_look.x;
	if (dr <= 0.0) return;
	float r = length(wp.xz - flare_at.xz);
	// Restored inside the repaint's radius, across a soft 6 m band with no line and no light.
	float back = 1.0 - smoothstep(flare_look.y - 6.0, flare_look.y, r);
	float k = dr * (1.0 - back);
	float l = dot(alb, FL_LUM);
	alb = mix(alb, vec3(l), 0.7 * k) * (1.0 - 0.25 * k);
	// Burns Twice paints the world back cold first; the warmth comes with the embers.
	// (Only on the ford's frost, the reach and a little past it: by the story's camera the whole wood went blue.)
	float cold = flare_look.z * back * dr * (1.0 - smoothstep(flare_at.w, flare_at.w + 5.0, r));
	alb = mix(alb, vec3(l) * vec3(0.74, 0.9, 1.14), cold * 0.55);
	emi = mix(emi, vec3(dot(emi, FL_LUM)), 0.7 * k) * (1.0 - 0.25 * k);
}

// When the frost's front passes a point: its distance, warped by a low cloud, with fingers racing ahead.
float flare_arrive(vec2 w) {
	vec2 d = w - flare_at.xz;
	float r = length(d);
	float a = atan(d.y, d.x);
	float s = flare_web.w;
	// (0.477 turns of the noise a radian: three whole tiles round the circle, so it meets itself.)
	float f = texture(flare_noise, vec2(a * 0.47746 + s, r * 0.004 + s * 0.37)).r;
	float fing = pow(smoothstep(0.42, 0.86, f), 1.6);
	float n = texture(flare_noise, w * 0.045 + s * 1.7).g;
	return r * (1.0 - 0.32 * fing * smoothstep(1.5, 7.0, r)) + (n - 0.5) * 3.2;
}

// The crystal at a point: two layers of the plate, turned and scaled apart, multiplied (no visible repeat).
vec3 flare_crystal(vec2 w) {
	// (Ferns a hand long from the arena's height: smaller, the plate read as salt and static.)
	vec2 u1 = w * 0.11;
	vec2 u2 = mat2(vec2(0.62, -0.78), vec2(0.78, 0.62)) * w * 0.067 + 0.37;
	vec4 p1 = texture(flare_plate, u1);
	vec4 p2 = texture(flare_plate, u2);
	float c = clamp(p1.r * (0.45 + 0.9 * p2.r) * 1.25, 0.0, 1.0);
	float fine = max(p1.g * smoothstep(0.2, 0.6, p2.b), p2.g * 0.6 * smoothstep(0.3, 0.7, p1.b));
	return vec3(c, fine, p1.b * 0.6 + p2.b * 0.4);
}

// How much frost lies at a point (0..1): grown past the front, held inside the reach, melted in from the edge.
float flare_cover(vec2 w, float arr, float crystal) {
	if (flare_look.w < 0.5 || flare_frost.y <= 0.0) return 0.0;
	float grow = flare_frost.x - arr;
	float c = smoothstep(-0.2, 0.6, grow + (crystal - 0.5) * 0.9);
	float r = length(w - flare_at.xz);
	float edge = texture(flare_noise, w * 0.09).b;
	// Honest edge: where the reach stops, the frost stops (irregular, never a ring).
	c *= 1.0 - smoothstep(flare_at.w - 2.2, flare_at.w + 0.3, r + (edge - 0.5) * 2.4);
	// The melt comes in from the edge.
	float keep = flare_at.w - flare_frost.z;
	c *= smoothstep(0.0, 1.4, keep - arr + (crystal - 0.5) * 1.6);
	return c * flare_frost.y;
}

// The web (the Draw and the Return): hairline cracks of the calling's light under the ground.
vec3 flare_web_light(vec2 w) {
	if (flare_web.x <= 0.0) return vec3(0.0);
	float r = length(w - flare_at.xz);
	float reach = flare_at.w;
	vec2 s = vec2(flare_web.w * 3.1, flare_web.w * 1.3);
	float e1 = texture(flare_noise, w * 0.071 + s).a;
	float e2 = texture(flare_noise, w * 0.19 + s.yx + 0.5).a;
	// Hairlines (about a pixel from the arena's height), broken into lengths like embers under ash.
	float l1 = 1.0 - smoothstep(0.0, 0.012 + fwidth(e1), e1);
	float l2 = 1.0 - smoothstep(0.0, 0.01 + fwidth(e2), e2);
	float seg = smoothstep(0.3, 0.72, texture(flare_noise, w * 0.11 + s * 0.7).g);
	float line = max(l1 * (0.3 + 0.7 * seg), l2 * 0.35 * seg);
	// Lit from her outward as the Draw begins, fading softly toward the reach's edge (the reach shown with no ring).
	float lit = 1.0 - smoothstep(flare_web.z - 3.0, flare_web.z, r);
	float inside = 1.0 - smoothstep(reach * 0.55, reach * 1.02, r + (texture(flare_noise, w * 0.05).r - 0.5) * 4.0);
	// The light runs inward along the cracks, drawn up into her.
	float run = 0.62 + 0.38 * sin(r * 0.9 + TIME * 11.0 + e1 * 3.0);
	float heat = clamp(flare_web.y, 0.0, 1.0);
	vec3 hot = mix(vec3(0.32, 0.03, 0.01), flare_hue.rgb, smoothstep(0.25, 1.0, heat)) * smoothstep(0.0, 0.25, heat);
	// A breath of glow along the line's sides keeps a hairline alive from thirty metres up.
	float halo = (1.0 - smoothstep(0.0, 0.05, e1)) * 0.07 * seg;
	// Brightest near her, where the light is drawn in; faint toward the reach.
	float near = mix(1.5, 0.4, smoothstep(2.0, reach, r));
	return hot * (line + halo) * lit * inside * run * near * flare_web.x * 0.9;
}

// The impacts: melted rings of wet ground round each, char flung out, and a hot heart that cools.
// Returns x: wet (0..1), y: char (0..1), z: heat (0..1); w: melted (frost taken).
vec4 flare_marks_at(vec2 w) {
	vec4 o = vec4(0.0);
	for (int i = 0; i < 24; i++) {
		vec4 m = texelFetch(flare_marks, ivec2(i, 0), 0);
		if (m.z <= 0.0) continue;
		vec2 d = w - m.xy;
		float dl = length(d);
		float R = m.z;
		if (dl > R * 2.2) continue;
		float age = m.w;
		float a = atan(d.y, d.x);
		float spl = texture(flare_noise, vec2(a * 0.47746 + float(i) * 0.137, 0.21 + float(i) * 0.05)).g;
		float n = texture(flare_noise, w * 0.6 + float(i) * 0.31).b;
		// The melt opens fast, then wider as the heat spreads.
		float meltR = R * (0.7 + 0.55 * smoothstep(0.0, 1.6, age)) * (0.85 + 0.3 * spl);
		float melt = 1.0 - smoothstep(meltR * 0.75, meltR * 1.05, dl + (n - 0.5) * 0.5);
		// Char: a heart, and splashes flung out along a few angles.
		float fling = pow(smoothstep(0.55, 0.95, spl), 1.4);
		float charR = R * (0.38 + 0.6 * fling);
		float ch = 1.0 - smoothstep(charR * 0.55, charR, dl + (n - 0.5) * 0.35);
		float heart = 1.0 - smoothstep(0.0, R * 0.32, dl);
		float heat = heart * exp(-age * 2.4) + ch * exp(-age * 3.6) * smoothstep(0.55, 0.75, n) * 0.6;
		o.x = max(o.x, melt);
		o.y = max(o.y, ch);
		o.z = max(o.z, heat);
		o.w = max(o.w, melt);
	}
	return o;
}

// The ground: drained, then the web, the frost and the impacts over it (the Flare's own, never drained).
void flare_ground(vec3 wp, inout vec3 alb, inout float rough, inout float spec, inout vec3 nrm_view, inout vec3 emi, mat4 view, mat4 inv_view) {
	if (!flare_live()) return;
	flare_drain(wp, alb, emi);
	vec2 w = wp.xz;
	vec3 web = flare_web_light(w);
	float kind = flare_look.w;
	if (kind > 0.5 && length(w - flare_at.xz) < flare_at.w + 3.0) {
		vec3 cr = flare_crystal(w);
		float arr = flare_arrive(w);
		float cover = flare_cover(w, arr, cr.x);
		vec4 mk = flare_marks_at(w);
		// The impacts take the frost and leave wet ground.
		float ice = cover * (1.0 - mk.w);
		float wet = max(mk.x, 0.0) * (1.0 - smoothstep(4.0, 6.5, flare_frost.w)) + (cover - ice) * 0.0;
		// Melted frost from the edge leaves the ground wet behind it, drying by the scars' end.
		float melted = (1.0 - cover) * step(0.01, flare_frost.y) * smoothstep(flare_frost.x, flare_frost.x - 1.0, arr) * smoothstep(0.0, 0.5, flare_frost.z);
		wet = max(wet, melted * (1.0 - smoothstep(3.5, 6.0, flare_frost.w)));
		vec3 nw = (inv_view * vec4(nrm_view, 0.0)).xyz;
		bool black = kind > 1.5;
		// Under the glaze the ground goes dark, as if wet.
		alb *= 1.0 - 0.32 * ice;
		vec3 glaze = black ? vec3(0.018, 0.024, 0.034) * (0.6 + 0.8 * cr.x) : vec3(0.13, 0.2, 0.28) * (0.42 + 0.95 * cr.x); // a mid-value glaze: by day the paler one read as snow
		float feather = black ? 0.75 : 0.3 + 0.7 * clamp(cr.x * 1.35, 0.0, 1.0);
		alb = mix(alb, glaze, ice * feather);
		rough = mix(rough, black ? 0.06 : mix(0.16, 0.42, cr.x), ice);
		spec = mix(spec, 0.5, ice);
		// The feathers stand up from the glass: their ridges catch the light.
		float gx = dFdx(cr.x), gy = dFdy(cr.x);
		vec3 tilt = (inv_view * vec4(gx, gy, 0.0, 0.0)).xyz;
		nw = normalize(nw - vec3(tilt.x, 0.0, tilt.z) * 3.5 * ice * (black ? 0.3 : 1.0));
		// Wet ground: darker, glossy, with meltwater glints.
		alb *= 1.0 - 0.38 * wet;
		rough = mix(rough, 0.1, wet);
		spec = mix(spec, 0.6, wet);
		// Char: black and dry where the ember splashed, its heart glowing as it cools.
		alb = mix(alb, vec3(0.022, 0.018, 0.016), mk.y * 0.92);
		rough = mix(rough, 0.95, mk.y * 0.85);
		float crack = 1.0 - smoothstep(0.0, 0.08, texture(flare_noise, w * 0.9).a);
		emi += vec3(1.0, 0.32, 0.06) * mk.z * (0.25 + 1.6 * crack) * 1.4;
		// The front: the frost crystallising as it comes, cold points in a narrow fingered band.
		float band = smoothstep(-0.2, 0.25, flare_frost.x - arr) * (1.0 - smoothstep(0.25, 1.4, flare_frost.x - arr));
		float twinkle = step(0.55, fract(sin(dot(floor(w * 22.0), vec2(12.9898, 78.233)) + floor(TIME * 12.0)) * 43758.5453));
		emi += vec3(0.32, 0.62, 1.0) * (cr.y * 0.6 + cr.x * 0.22) * band * cover * (black ? 0.35 : 1.0);
		// Held frost: a few fine points of cold light, and the meltwater's glints.
		emi += vec3(0.4, 0.68, 1.0) * cr.y * ice * twinkle * 0.05 * flare_hue.a;
		nrm_view = normalize((view * vec4(nw, 0.0)).xyz);
		// The web shows faint under the ice.
		web *= 1.0 - 0.45 * ice;
	}
	emi += web;
}

// How glazed a body is at this point (0..1): the spell's own rime gives way to the Flare's.
float flare_glazed(vec3 wp) {
	if (flare_look.w < 0.5 || flare_frost.y <= 0.0) return 0.0;
	float cr = texture(flare_plate, wp.xz * 0.9 + wp.y * 0.6).r;
	return flare_cover(wp.xz, flare_arrive(wp.xz), cr);
}

// A body in the crowd: drained, then glazed where the frost has reached it, its own shading kept.
void flare_body(vec3 wp, vec3 nrm_view, mat4 inv_view, float rim, inout vec3 alb, inout float rough, inout vec3 emi) {
	if (!flare_live()) return;
	flare_drain(wp, alb, emi);
	float g = flare_glazed(wp);
	if (g <= 0.0) return;
	vec3 nw = (inv_view * vec4(nrm_view, 0.0)).xyz;
	vec4 p = texture(flare_plate, wp.xz * 1.3 + vec2(wp.y * 0.9, wp.y * -0.4));
	float l = dot(alb, FL_LUM);
	bool black = flare_look.w > 1.5;
	vec3 ice = black ? vec3(0.02, 0.026, 0.036) : vec3(0.12, 0.19, 0.27) * (0.7 + 0.8 * clamp(l * 2.0, 0.0, 1.0));
	// Glazed in a coat that runs thicker on what faces up; the body under it still reads through.
	float coat = g * clamp(0.5 + 0.4 * nw.y + (p.r - 0.4) * 0.8, 0.0, 1.0);
	alb = mix(alb, mix(alb * 0.55, ice, 0.7), coat);
	rough = mix(rough, black ? 0.05 : 0.12, g);
	emi += vec3(0.22, 0.5, 0.95) * pow(rim, 3.0) * g * (black ? 0.12 : 0.32) + vec3(0.45, 0.7, 1.0) * p.g * coat * 0.1;
}

// A blade of grass: drained, and frost on its tip.
void flare_blade(vec3 wp, float tip, inout vec3 alb, inout float rough, inout vec3 emi) {
	if (!flare_live()) return;
	flare_drain(wp, alb, emi);
	if (flare_look.w < 0.5) return;
	float cr = texture(flare_plate, wp.xz * 0.5).r;
	float g = flare_cover(wp.xz, flare_arrive(wp.xz), cr);
	bool black = flare_look.w > 1.5;
	vec3 ice = black ? vec3(0.03, 0.04, 0.05) : vec3(0.11, 0.17, 0.24);
	// (Leaf litter lies flat: it takes the glaze too, or it reads as orange confetti on the ice.)
	alb = mix(alb, ice * (0.75 + 0.45 * tip), g * (0.6 + 0.3 * tip));
	rough = mix(rough, 0.2, g);
}

// A prop (stones, posts, walls): drained, and rimed on what faces up.
void flare_prop(vec3 wp, vec3 nrm_view, mat4 inv_view, inout vec3 alb, inout float rough, inout vec3 emi) {
	if (!flare_live()) return;
	flare_drain(wp, alb, emi);
	if (flare_look.w < 0.5) return;
	vec3 nw = (inv_view * vec4(nrm_view, 0.0)).xyz;
	vec3 p = flare_crystal(wp.xz + wp.y * 0.7);
	float g = flare_cover(wp.xz, flare_arrive(wp.xz), p.x) * smoothstep(-0.2, 0.7, nw.y);
	bool black = flare_look.w > 1.5;
	vec3 ice = black ? vec3(0.02, 0.026, 0.036) : vec3(0.15, 0.22, 0.3) * (0.5 + 0.8 * p.x);
	alb = mix(alb, ice, g * (0.4 + 0.5 * p.x));
	rough = mix(rough, 0.15, g);
}
