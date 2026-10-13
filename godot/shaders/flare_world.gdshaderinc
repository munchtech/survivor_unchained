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

// The ferns' spines at a point (0..1): one layer of the plate drawn large (ferns a stride long, so their spines and
// barbs come out a pixel or two wide from the camera), turned and moved by the Flare's seed, and only where the
// crystal is brighter than its own neighbourhood (a few mips down), so they stay thin lines. (At a hand long, or
// thresholded on its own, the plate's dense haze of fine lines read as static, or lit up as a pale field.)
// Fragment only (mip bias).
float flare_spine(vec2 w) {
	float s = flare_web.w;
	float a = s * 2.399;
	vec2 u = mat2(vec2(cos(a), sin(a)), vec2(-sin(a), cos(a))) * w * 0.032 + vec2(fract(s * 0.618), fract(s * 0.382));
	float c = texture(flare_plate, u).r;
	float cb = texture(flare_plate, u, 2.5).r;
	float big = smoothstep(0.05, 0.18, c - cb) * smoothstep(0.28, 0.48, c);
	// A second, finer growth between the big ferns (t6: the field between them read as bare dark glass).
	vec2 u2 = mat2(vec2(cos(a + 1.9), sin(a + 1.9)), vec2(-sin(a + 1.9), cos(a + 1.9))) * w * 0.085 + vec2(0.31, 0.77);
	float f = texture(flare_plate, u2).r;
	float fb = texture(flare_plate, u2, 2.5).r;
	float fine = smoothstep(0.07, 0.2, f - fb) * smoothstep(0.3, 0.5, f);
	return max(big, fine * 0.25);
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
		// The crater: a black pit with a glowing lip, read from the arena's height.
		ch = max(ch, 1.0 - smoothstep(R * 0.34, R * 0.46, dl + (n - 0.5) * 0.3));
		float lip = clamp(1.0 - abs(dl - R * 0.44 + (n - 0.5) * 0.25) / (R * 0.1), 0.0, 1.0);
		float heat = heart * exp(-age * 2.4) + ch * exp(-age * 3.6) * smoothstep(0.55, 0.75, n) * 0.6 + lip * exp(-age * 1.6) * (0.55 + 0.45 * n);
		o.x = max(o.x, melt);
		o.y = max(o.y, ch);
		o.z = max(o.z, heat);
		o.w = max(o.w, melt);
	}
	return o;
}

// The BOOM's ring (the marks' last texel: where it struck, how far it runs, seconds since): its radius, racing out
// fast and easing as it reaches the reach's edge in 0.7 s (after the last word's hitstop). FlareFx.RingAt is the
// same curve: each statue bursts as the line crosses it.
float flare_ring(float s, float rmax) {
	float x = clamp((s - 0.01) / 0.7, 0.0, 1.0);
	return rmax * (1.0 - pow(1.0 - x, 2.5));
}

// The BOOM's ring over the ground: a thin line of fire racing over the whole reach (so the room-clear reads at
// every camera, t5), black char behind it. A thin line and dark char, never a wash (§1.6: t9's 4 m cream band).
// Returns x: the line's white-yellow core, y: its orange-to-red body, z: the char behind it, w: how fresh the
// char is (its cracks still glowing); at: where it struck.
vec4 flare_boom(vec2 w, out vec2 at) {
	vec4 bm = texelFetch(flare_marks, ivec2(31, 0), 0);
	at = bm.xy;
	if (bm.z <= 0.0) return vec4(0.0);
	vec2 d = w - bm.xy;
	float dl = length(d);
	float a = atan(d.y, d.x);
	// A little ragged by angle and place, never far off the mean the bursts keep.
	float fing = texture(flare_noise, vec2(a * 0.47746, 0.63)).g;
	float n = texture(flare_noise, w * 0.35).r;
	float ahead = flare_ring(bm.w, bm.z) * (0.97 + 0.06 * fing) + (n - 0.5) * 0.45 - dl;
	// Over the whole reach, wherever it struck; the line burns out as it reaches the edge.
	float fade = 1.0 - smoothstep(flare_at.w - 1.0, flare_at.w + 1.5, length(w - flare_at.xz));
	float lit = fade * (1.0 - smoothstep(0.62, 0.85, bm.w));
	// Across the line: a faint red breath ahead, the white-yellow core (a third of a metre), then orange
	// cooling to red over half a metre behind it.
	float core = exp(-pow((ahead - 0.1) / 0.13, 2.0));
	float body = smoothstep(-0.25, 0.05, ahead) * exp(-max(ahead - 0.05, 0.0) / 0.38);
	// Behind it the ground is burnt: char, its cracks glowing a moment, cooling with distance behind the line;
	// gone back to wet ground through the Return.
	float ch = smoothstep(0.1, 0.7, ahead) * fade * (1.0 - smoothstep(2.2, 4.6, bm.w));
	// (Glowing 1.6 m back, the whole inside of the ring read as orange-brown, not char: s2b.)
	float fresh = exp(-max(ahead, 0.0) / 0.55) * (1.0 - smoothstep(0.5, 1.4, bm.w));
	return vec4(core * lit, body * lit, ch, fresh * ch);
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
		// The BOOM's ring melts what it crosses to wet char.
		vec2 bat;
		vec4 bo = flare_boom(w, bat);
		// The impacts take the frost and leave wet ground.
		float ice = cover * (1.0 - mk.w) * (1.0 - smoothstep(0.0, 0.6, bo.z));
		float wet = max(max(mk.x, 0.0) * (1.0 - smoothstep(4.0, 6.5, flare_frost.w)), bo.z * 0.8);
		// Melted frost from the edge leaves the ground wet behind it, drying by the scars' end.
		float melted = (1.0 - cover) * step(0.01, flare_frost.y) * smoothstep(flare_frost.x, flare_frost.x - 1.0, arr) * smoothstep(0.0, 0.5, flare_frost.z);
		wet = max(wet, melted * (1.0 - smoothstep(3.5, 6.0, flare_frost.w)));
		vec3 nw = (inv_view * vec4(nrm_view, 0.0)).xyz;
		bool black = kind > 1.5;
		float day = 1.0 - flare_hue.a;
		// Dark wet glass: the ground seen through it darker and colder than bare, never paler (a pale glaze,
		// or the plate's fine haze of lines lit as a field, read as grey snow over the screen). Only the
		// ferns' spines are bright: thin crystal edges catching the light.
		float spine = flare_spine(w);
		float gl = dot(alb, FL_LUM);
		vec3 under = mix(vec3(gl), alb, 0.45) * vec3(0.46, 0.66, 1.0) * 0.85;
		vec3 glass = mix(under, black ? vec3(0.004, 0.005, 0.008) : vec3(0.006, 0.013, 0.03), black ? 0.8 : 0.3);
		vec3 edge = black ? vec3(0.03, 0.04, 0.055) : mix(vec3(0.26, 0.42, 0.62), vec3(0.4, 0.55, 0.72), day);
		alb = mix(alb, mix(glass, edge, spine * (black ? 0.5 : 1.0)), ice);
		// The fine frost shows in the sheen, not the colour: clear glass mirror-smooth, the feathered rougher.
		rough = mix(rough, black ? 0.05 : max(mix(0.06, 0.22, cr.x), 0.32 * spine), ice);
		// By day the glass reflects little of the sky: its sheen over the whole field was the grey.
		spec = mix(spec, black ? 0.5 : mix(0.42, 0.1, day), ice);
		// The spines stand up from the glass: their ridges catch the light (only theirs: on the field
		// between, the tilt was a speckle).
		float gx = dFdx(cr.x), gy = dFdy(cr.x);
		vec3 tilt = (inv_view * vec4(gx, gy, 0.0, 0.0)).xyz;
		nw = normalize(nw - vec3(tilt.x, 0.0, tilt.z) * 2.2 * ice * spine * (black ? 0.3 : 1.0));
		// At night the spines hold a little cold light of their own, so the ferns read on the dark glass.
		emi += vec3(0.2, 0.46, 1.0) * spine * ice * 0.16 * flare_hue.a * (black ? 0.3 : 1.0);
		// Wet ground: darker, glossy, with meltwater glints.
		alb *= 1.0 - 0.38 * wet;
		rough = mix(rough, 0.1, wet);
		spec = mix(spec, 0.6, wet);
		// Char: black and dry where the ember splashed, its heart glowing as it cools.
		alb = mix(alb, vec3(0.022, 0.018, 0.016), mk.y * 0.92);
		rough = mix(rough, 0.95, mk.y * 0.85);
		float crack = 1.0 - smoothstep(0.0, 0.08, texture(flare_noise, w * 0.9).a);
		emi += vec3(1.0, 0.32, 0.06) * mk.z * (0.25 + 1.6 * crack) * 1.4;
		// The BOOM's ring: char behind it, mottled (wet black ground between the burnt patches), its cracks
		// glowing a moment; the line itself white-yellow at its core (under the knee), orange to red behind.
		float mot = texture(flare_noise, w * 0.23 + 0.5).g;
		alb = mix(alb, vec3(0.016, 0.013, 0.011), bo.z * (0.6 + 0.4 * smoothstep(0.3, 0.7, mot)));
		rough = mix(rough, 0.7, bo.z * smoothstep(0.35, 0.65, mot));
		emi += vec3(1.0, 0.3, 0.05) * bo.w * crack * 1.1;
		emi += mix(vec3(0.75, 0.1, 0.012), vec3(1.0, 0.45, 0.08), smoothstep(0.1, 0.8, bo.y)) * bo.y * 1.25 + vec3(1.0, 0.84, 0.52) * bo.x * 0.9;
		// The front: the frost crystallising as it comes, cold points in a narrow fingered band.
		float band = smoothstep(-0.2, 0.25, flare_frost.x - arr) * (1.0 - smoothstep(0.25, 1.4, flare_frost.x - arr));
		float twinkle = step(0.55, fract(sin(dot(floor(w * 22.0), vec2(12.9898, 78.233)) + floor(TIME * 12.0)) * 43758.5453));
		// (The spines only: the whole line field lit made the front a pale ring.)
		emi += vec3(0.3, 0.6, 1.0) * (cr.y * 0.6 + spine * 0.45) * band * cover * (black ? 0.35 : 1.0);
		// Held frost: a few fine points of cold light, and the meltwater's glints.
		emi += vec3(0.4, 0.68, 1.0) * cr.y * ice * twinkle * 0.05 * flare_hue.a;
		nrm_view = normalize((view * vec4(nw, 0.0)).xyz);
		// The web shows faint under the ice.
		web *= 1.0 - 0.45 * ice;
	}
	emi += web;
}

// Whether Burns Twice's frost holds this point's reach (its glaze, not a spell's rime, says what is frozen there).
bool flare_frosting(vec3 wp) {
	return flare_look.w > 0.5 && flare_frost.y > 0.0 && length(wp.xz - flare_at.xz) < flare_at.w + 3.0;
}

// How glazed a body is at this point (0..1): only once the frost's front has reached it.
float flare_glazed(vec3 wp) {
	if (flare_look.w < 0.5 || flare_frost.y <= 0.0) return 0.0;
	float cr = texture(flare_plate, wp.xz * 0.9 + wp.y * 0.6).r;
	return flare_cover(wp.xz, flare_arrive(wp.xz), cr);
}

// A body in the crowd: drained, then glazed where the frost has reached it, its own shading kept.
void flare_body(vec3 wp, vec3 nrm_view, mat4 inv_view, float rim, inout vec3 alb, inout float rough, inout vec3 emi) {
	if (!flare_live()) return;
	flare_drain(wp, alb, emi);
	vec3 nw = (inv_view * vec4(nrm_view, 0.0)).xyz;
	float g = flare_glazed(wp);
	bool black = flare_look.w > 1.5;
	float night = flare_hue.a;
	if (g > 0.0) {
		// A statue of ice, a step brighter than the ground's dark glass so the frozen pack still reads on it:
		// the body's own light and shade through a cold clear coat (its warmth drawn out, never paler than
		// the body was: a pale glaze read as grey haze over the crowd), the light living in the ice: an
		// ice-blue fresnel rim, cyan where it is thin (its edges, a hand, a brim), and a few glints.
		vec4 p = texture(flare_plate, wp.xz * 1.3 + vec2(wp.y * 0.9, wp.y * -0.4));
		float l = dot(alb, FL_LUM);
		vec3 ice = mix(vec3(l), alb, 0.2) * vec3(0.5, 0.74, 1.0) * mix(0.75, 0.6, night) + vec3(0.02, 0.05, 0.09) * (0.6 + 0.8 * p.r);
		if (black) ice = mix(vec3(l), alb, 0.2) * vec3(0.12, 0.14, 0.18) + vec3(0.005, 0.007, 0.01);
		alb = mix(alb, ice, g);
		rough = mix(rough, black ? 0.05 : 0.12, g);
		// Its own warm lights (a lantern, an eye, a struck flare) go dim under the ice (t10: warm beads on
		// the glazed field).
		emi *= 1.0 - 0.8 * g;
		float fres = pow(rim, 2.4);
		vec3 rimc = mix(vec3(0.22, 0.56, 1.0), vec3(0.32, 1.0, 0.92), smoothstep(0.82, 0.98, rim));
		emi += rimc * fres * g * (black ? 0.06 : mix(0.2, 0.42, night));
		// The light held in the ice itself, so a statue reads from above (a hat or a crown faces the camera and has no
		// rim): a cold mid-value body over the ground's dark glass, its facets uneven (s1b: the far pack went black).
		emi += vec3(0.05, 0.12, 0.22) * g * (black ? 0.15 : mix(0.45, 1.0, night)) * (0.55 + 0.9 * p.r) * (0.6 + 0.4 * max(nw.y, 0.0));
		// A few in a hundred of its facets catch the light at once, each on its own beat (the statues stand
		// still, so the world's cells stay on them).
		vec3 cell = floor(wp * 8.0);
		float h = fract(sin(dot(cell, vec3(12.9898, 78.233, 37.719))) * 43758.5453);
		float beat = fract(h * 13.7 + TIME * (0.7 + 0.9 * h));
		float glint = step(0.955, h) * smoothstep(0.0, 0.08, beat) * (1.0 - smoothstep(0.2, 0.45, beat));
		emi += vec3(0.62, 0.86, 1.0) * glint * g * (black ? 0.25 : mix(0.55, 0.95, night)) * (0.4 + 0.6 * max(nw.y, 0.0));
	}
	// The BOOM's ring lights each body from the blast's side as it passes.
	if (flare_look.w > 0.5) {
		vec2 bat;
		vec4 bo = flare_boom(wp.xz, bat);
		if (bo.x + bo.y > 0.001) {
			float face = 0.35 + 0.65 * max(0.0, dot(nw, normalize(vec3(bat.x - wp.x, 0.5, bat.y - wp.z))));
			emi += vec3(1.0, 0.46, 0.13) * (bo.x * 0.55 + bo.y * 0.08) * face;
		}
	}
}

// A blade of grass: drained, and frost on its tip.
void flare_blade(vec3 wp, float tip, inout vec3 alb, inout float rough, inout vec3 emi) {
	if (!flare_live()) return;
	flare_drain(wp, alb, emi);
	if (flare_look.w < 0.5) return;
	float cr = texture(flare_plate, wp.xz * 0.5).r;
	float g = flare_cover(wp.xz, flare_arrive(wp.xz), cr);
	bool black = flare_look.w > 1.5;
	// Glazed dark like the ground's glass, a little lighter (never paler than the blade was) where its tip
	// catches the light. (Leaf litter lies flat: it takes the glaze too, or it reads as orange confetti on the ice.)
	float l = dot(alb, FL_LUM);
	vec3 glass = mix(vec3(l), alb, 0.3) * vec3(0.4, 0.62, 1.0);
	glass *= black ? 0.25 : mix(0.4, 0.85, smoothstep(0.6, 1.0, tip));
	alb = mix(alb, glass, g);
	rough = mix(rough, black ? 0.08 : 0.16, g);
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
	// The ground's dark glass on what faces up, its fern spines the only bright in it.
	float spine = flare_spine(wp.xz + wp.y * 0.7);
	float l = dot(alb, FL_LUM);
	vec3 glass = mix(vec3(l), alb, 0.4) * vec3(0.46, 0.66, 1.0) * 0.72;
	glass = mix(glass, black ? vec3(0.004, 0.005, 0.008) : vec3(0.006, 0.013, 0.03), black ? 0.8 : 0.3);
	vec3 edge = black ? vec3(0.03, 0.04, 0.055) : vec3(0.26, 0.42, 0.62) * (1.0 - 0.3 * (1.0 - flare_hue.a));
	alb = mix(alb, mix(glass, edge, spine * (black ? 0.5 : 0.85)), g);
	// Not mirror-smooth: a rock face tilted to the moon threw a still white hotspot (t10, s1b: the triangle at the
	// Verge's top centre).
	rough = mix(rough, mix(0.26, 0.38, spine), g);
}
