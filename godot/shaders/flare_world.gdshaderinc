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
global uniform vec4 flare_fire;   // xyz: the BOOM's fireball (world); w: its light on the frozen statues' rims (0 none)
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

// The char's cracks (the Return's web): distance to the nearest seam between cells about 0.55 m across (F2-F1
// of a jittered grid, m), so the burnt ground glows along a joined crust of cracks, never in loose straight lengths
// (judge 3: the hairline web held under the char read as orange straw and sticks).
float fl_seam(vec2 w) {
	vec2 g = w / 0.8;
	vec2 gi = floor(g);
	float d1 = 9.0, d2 = 9.0;
	for (int y = -1; y <= 1; y++)
	for (int x = -1; x <= 1; x++) {
		vec2 c = gi + vec2(float(x), float(y));
		vec2 h = fract(sin(vec2(dot(c, vec2(127.1, 311.7)), dot(c, vec2(269.5, 183.3)))) * 43758.5453);
		float d = length(g - c - 0.1 - 0.8 * h);
		if (d < d1) { d2 = d1; d1 = d; } else if (d < d2) d2 = d;
	}
	return (d2 - d1) * 0.8 * 0.5;
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
	// Never a neon hoop (judge 2, s4): it wobbles about 0.4 m either side of the mean the bursts keep
	// (FlareFx.RingAt), ragged by place too.
	float u = a * 0.15915;
	float wob = (texture(flare_noise, vec2(u * 2.0, 0.63 + bm.w * 0.5)).g - 0.5) * 1.3 + (texture(flare_noise, vec2(u * 9.0, 0.29)).r - 0.5) * 0.3;
	float n = texture(flare_noise, w * 0.35).r;
	float ahead = flare_ring(bm.w, bm.z) + wob + (n - 0.5) * 0.3 - dl;
	// Over the whole reach, wherever it struck; the line burns out as it reaches the edge.
	float fade = 1.0 - smoothstep(flare_at.w - 1.0, flare_at.w + 1.5, length(w - flare_at.xz));
	// Its fire uneven along its length: 30% either way, drifting.
	float br = 0.7 + 0.6 * clamp(0.5 + (texture(flare_noise, vec2(u * 3.0, 0.41 + bm.w * 1.3)).g - 0.5) * 2.4, 0.0, 1.0);
	float lit = fade * (1.0 - smoothstep(0.62, 0.85, bm.w)) * br;
	// Across the line, thin: the white-yellow core (12 cm), orange cooling to red over 40 cm behind it, and ahead
	// of it a fading red edge. (A third of a metre of core and half a metre of orange, under the glow, read as a
	// thick soft cream band: s2e.)
	float core = exp(-pow((ahead - 0.05) / 0.07, 2.0));
	float body = pow(smoothstep(-0.16, 0.03, ahead), 2.0) * exp(-max(ahead - 0.03, 0.0) / 0.16);
	// (Judge 3: a red edge two or three pixels outside the line, not a soft orange fade.)
	body = max(body, 0.42 * exp(-pow((ahead + 0.075) / 0.032, 2.0)));
	// Tongues of flame licking out ahead of it, 1-1.5 m, on a few angles (about eight round it: the noise's
	// blue holds ~17 px features), each flickering every three or four frames; orange at the root, red to
	// their tips, torn.
	float tg = smoothstep(0.6, 0.78, texture(flare_noise, vec2(u * 2.0, 0.83)).b);
	float fl = texture(flare_noise, vec2(u * 2.0 + 0.5, 0.17 + floor(TIME * 16.0) * 0.0731)).b;
	float tl = tg * 1.45 * (0.5 + 0.5 * smoothstep(0.3, 0.7, fl));
	float out_ = -ahead;
	float tear = texture(flare_noise, w * 1.7 + vec2(0.0, -TIME * 2.5)).g;
	float tongue = step(0.0, out_) * (1.0 - smoothstep(tl * 0.35, tl, out_ + (tear - 0.5) * 0.35)) * step(0.05, tl);
	body = max(body, tongue * (0.85 - 0.6 * clamp(out_ / max(tl, 0.01), 0.0, 1.0)) * (0.6 + 0.6 * tear));
	// Behind it the ground is burnt black at once; gone back to wet ground through the Return.
	float ch = smoothstep(0.12, 0.42, ahead) * fade * (1.0 - smoothstep(2.2, 4.6, bm.w));
	// Its cracks glow a breath behind the line, no further. (Glowing 1.6 m back, the whole inside of the ring
	// read as orange-brown, not char: s2b.)
	float fresh = exp(-max(ahead, 0.0) / 0.3) * (1.0 - smoothstep(0.4, 1.0, bm.w));
	return vec4(core * lit, body * lit, ch, fresh * ch);
}

// How far behind the BOOM's line this point lies (m; negative: not reached yet, or no ring).
float flare_boom_behind(vec2 w) {
	vec4 bm = texelFetch(flare_marks, ivec2(31, 0), 0);
	if (bm.z <= 0.0) return -1e3;
	return flare_ring(bm.w, bm.z) - length(w - bm.xy);
}

// The BOOM's line on a surface (its white-yellow core under the knee, orange to red behind it).
vec3 flare_boom_light(vec4 bo) {
	return mix(vec3(0.5, 0.05, 0.008), vec3(1.0, 0.36, 0.05), smoothstep(0.15, 0.85, bo.y)) * bo.y * 1.05 + vec3(1.0, 0.72, 0.36) * bo.x * 0.55;
}

// The last word's ground flash (judge 2, s4): its first frames, a torn disc about 3 m across round the crater, a
// yellow heart under the knee going orange to its ragged edge (Flare time: the hitstop holds it ~4 frames).
vec3 flare_boom_flash(vec2 w) {
	vec4 bm = texelFetch(flare_marks, ivec2(31, 0), 0);
	if (bm.z <= 0.0 || bm.w > 0.03) return vec3(0.0);
	vec2 d = w - bm.xy;
	float dl = length(d);
	float u = atan(d.y, d.x) * 0.15915;
	float torn = texture(flare_noise, vec2(u * 7.0, 0.11)).r + (texture(flare_noise, vec2(u * 19.0, 0.53)).g - 0.5) * 0.6;
	float R = 1.55 * (0.65 + 0.6 * torn);
	float k = 1.0 - smoothstep(0.004, 0.014, bm.w);
	float disc = 1.0 - smoothstep(R * 0.7, R, dl + (texture(flare_noise, w * 2.3).b - 0.5) * 0.35);
	float heart = 1.0 - smoothstep(0.0, R * 0.55, dl);
	return (vec3(1.0, 0.42, 0.08) * disc * 0.9 + vec3(0.6, 0.45, 0.2) * heart * 0.5) * k;
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
		// The ground as it was (drained, not yet glazed, wet or burnt): the char is a step under this.
		vec3 fl_alb0 = alb;
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
		// The BOOM's ring: black char behind it, mottled dry and wet (both black: mottled back to the lit ground,
		// the inside read orange-brown under the last word's light, s2e), its cracks glowing a breath behind
		// the line; the line itself white-yellow at its core (under the knee), orange to red behind.
		// Char a dark warm brown, a step under the unburnt ground (judge 2, s4: near-black read as a dead frame),
		// blacker while fresh; mottled dry and wet.
		float mot = texture(flare_noise, w * 0.23 + 0.5).g;
		vec4 bmk = texelFetch(flare_marks, ivec2(31, 0), 0);
		float aged = smoothstep(0.25, 1.4, bmk.w);
		// A step under the ground it burnt, whatever ground (a fixed near-black read as a dead frame at night and a
		// hole by day): its own colour, warmed, at about 0.45 of it, blacker while fresh. (The s5 salmon was a
		// name clash, never this.)
		// (Judge 3: at 0.45 of the wet ground, about 0.3 of the dry, it was the dead frame of the Return: the char
		// now sits at about 0.7 of the ground it burnt, mottled, a breath darker while fresh.)
		vec3 charc = mix(vec3(dot(fl_alb0, FL_LUM)), fl_alb0, 0.5) * vec3(1.2, 0.85, 0.55) * 0.8
			* mix(1.15, 0.82, smoothstep(0.3, 0.7, mot)) * mix(0.85, 1.0, aged);
		alb = mix(alb, charc, bo.z * 0.97);
		// A warm scorched rim where the char gives out (judge 3, by day: a clear disc with a warm edge).
		float fl_rim = bo.z * (1.0 - bo.z) * 4.0;
		alb = mix(alb, fl_alb0 * vec3(1.05, 0.72, 0.42), fl_rim * 0.55);
		rough = mix(rough, mix(0.3, 0.85, smoothstep(0.35, 0.65, mot)), bo.z);
		spec = mix(spec, 0.25, bo.z);
		emi *= 1.0 - 0.5 * bo.z;
		emi += vec3(1.0, 0.3, 0.05) * bo.w * crack * 0.9;
		emi += flare_boom_light(bo);
		// Live embers scattered in the char, breathing, dying through the Return (FLARE_LOOK §4.1).
		// A point in one 31 cm cell in ten, clumped, of varied heat (a jittered grid of even dots read as polka, s5). (NEVER name a local in this file after a uniform of a shader that
		// includes it: arena_ground's 'uniform vec3 ember' won over a local 'ember' and lit the whole inside of
		// the ring salmon at 4x ready, s5. Locals here take an fl_ prefix when in doubt.)
		// (Judge 3: still a polka grid. Now one a metre cell, anywhere in it (+-0.5 m), sized 0.5-2x, a third of
		// them out by 1-2 s and the rest by 2.5-5 s.)
		vec2 eci = floor(w);
		float en = fract(sin(dot(eci, vec2(127.1, 311.7))) * 43758.5453);
		float en2 = fract(sin(dot(eci, vec2(269.5, 183.3))) * 43758.5453);
		float en3 = fract(sin(dot(eci, vec2(419.2, 371.9))) * 43758.5453);
		float er = length(w - eci - vec2(en, en2));
		float erad = 0.012 * (0.5 + 1.5 * en3 * en3);
		float epx = max(fwidth(w.x), 0.002);
		float fl_emb = step(0.15, en3 + en * 0.2) * (1.0 - smoothstep(erad, erad + epx * 1.2, er)) * (0.35 + 0.65 * en2 * en2) * smoothstep(0.45, 0.75, textureLod(flare_noise, w * 0.4 + 0.7, 0.0).r);
		float eend = en3 < 0.33 ? 1.0 + 3.0 * en3 : 2.5 + 2.5 * en3;
		float breath = 0.65 + 0.35 * sin(TIME * (3.0 + 4.0 * en2) + en2 * 40.0);
		emi += vec3(1.0, 0.33, 0.06) * fl_emb * breath * bo.z * smoothstep(0.08, 0.3, bmk.w) * (1.0 - smoothstep(eend - 0.6, eend, bmk.w)) * 1.3;
		// The last word's ground flash.
		emi += flare_boom_flash(w);
		// The front: the frost crystallising as it comes, cold points in a narrow fingered band.
		float band = smoothstep(-0.2, 0.25, flare_frost.x - arr) * (1.0 - smoothstep(0.25, 1.4, flare_frost.x - arr));
		float twinkle = step(0.55, fract(sin(dot(floor(w * 22.0), vec2(12.9898, 78.233)) + floor(TIME * 12.0)) * 43758.5453));
		// (The spines only: the whole line field lit made the front a pale ring.)
		emi += vec3(0.3, 0.6, 1.0) * (cr.y * 0.6 + spine * 0.45) * band * cover * (black ? 0.35 : 1.0);
		// Held frost: a few fine points of cold light, and the meltwater's glints.
		emi += vec3(0.4, 0.68, 1.0) * cr.y * ice * twinkle * 0.05 * flare_hue.a;
		// Meltwater glints (judge 3): about one a square metre, sharp (a pixel or two), each twinkling on its own
		// clock, thickest at the frost's receding edge and scattered thin on the wet ground behind it.
		{
			vec2 gci = floor(w);
			float gh = fract(sin(dot(gci, vec2(41.3, 289.1))) * 43758.5453);
			float gh2 = fract(sin(dot(gci, vec2(157.7, 113.9))) * 43758.5453);
			vec2 gp = gci + 0.15 + 0.7 * vec2(gh, gh2);
			float gpx = max(fwidth(w.x), 0.004);
			float gd = 1.0 - smoothstep(gpx * 0.5, gpx * 1.6, length(w - gp));
			float gtw = step(0.45, fract(sin(gh * 91.7 + floor(TIME * (9.0 + 8.0 * gh2) + gh * 13.0)) * 43758.5453));
			float keep = flare_at.w - flare_frost.z;
			float gedge = step(0.01, flare_frost.z) * smoothstep(-0.4, 0.3, keep - arr) * (1.0 - smoothstep(0.5, 1.9, keep - arr));
			float gwet = max(gedge, 0.3 * wet) * (1.0 - ice * 0.7) * (1.0 - smoothstep(4.5, 6.0, flare_frost.w));
			emi += vec3(0.75, 0.9, 1.0) * gd * gtw * gwet * mix(0.9, 2.2, flare_hue.a);
		}
		nrm_view = normalize((view * vec4(nw, 0.0)).xyz);
		// The web shows faint under the ice, and is burnt out under the char (its glow over the inside of the
		// ring read as orange lines on the black: s2e).
		// Through the char it glows amber (judge 2, s4), a breath warmer than the web on open ground.
		// (Judge 3: held at full over the whole char it read as orange straw. Half, and sunk dark by 2 s.)
		// (Judge 3's Return: amber to 2 s, dark by 4 s; the Burns timeline sinks flare_web itself.)
		web *= (1.0 - 0.45 * ice) * (1.0 - bo.z);
		// Under the char the web is the crust's own cracks: amber to 2 s, dark red and gone by 4 s (FlareFx.Burns
		// sinks flare_web), a few joined runs of them alight, not the whole net.
		if (bo.z > 0.01 && flare_web.x > 0.0) {
			float fl_sd = fl_seam(w);
			float fl_px = max(fwidth(w.x), 0.004);
			// (f6b: the whole net lit, 3 px wide, read as a giraffe's hide at 1.6x the frame. One pixel; a sixth of it.)
			float fl_sl = 1.0 - smoothstep(fl_px * 0.2, fl_px * 0.8, fl_sd);
			// (f6d: lit in loose bits it read as scattered straw. Patches a few metres across where the whole crust
			// glows, joined, cooling to dark at their edges.)
			float fl_on = smoothstep(0.58, 0.72, texture(flare_noise, w * 0.11 + 0.3).g);
			float fl_ht = clamp(flare_web.y, 0.0, 1.0);
			// (f6h at 100%: at (1, 0.42, 0.08) over the char they read as tan twigs. Deep ember orange, cooling to red.)
			vec3 fl_hot = mix(vec3(0.35, 0.025, 0.005), vec3(1.0, 0.27, 0.035), smoothstep(0.3, 1.0, fl_ht)) * smoothstep(0.0, 0.3, fl_ht);
			web += fl_hot * fl_sl * fl_on * bo.z * flare_web.x * 0.8 * mix(0.3, 1.0, flare_hue.a);
		}
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
	// Behind the BOOM's ring the frost is gone: the living who walk in after it are not statues (s2e: two glazed
	// figures by her at c2 and c3). Every statue breaks as the line crosses it, before this.
	return flare_cover(wp.xz, flare_arrive(wp.xz), cr) * (1.0 - smoothstep(1.2, 3.0, flare_boom_behind(wp.xz)));
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
		// A drift of hue across the field (teal to blue, about 5%) and a quarter of each body's own paint through the
		// coat, so 250 bodies are not one blue gummy carpet (judge 2).
		float vj = texture(flare_plate, wp.xz * 0.13 + vec2(0.37, 0.71)).g - 0.5;
		vec3 tint = vec3(0.5, 0.74, 1.0) + vec3(-0.05, 0.04, -0.02) * vj * 2.0;
		// About one and a half to two times the ground glass, darker at night (judge 2: the Verge night's glaze was
		// the brightest thing in the frame, several steps over the ground).
		vec3 ice = mix(vec3(l), alb, 0.28) * tint * mix(0.5, 0.24, night) + vec3(0.014, 0.034, 0.062) * (0.6 + 0.8 * p.r);
		// Rime: white frost caught on what faces up (heads, shoulders, a brim), in patches, mid-value, never white.
		float rime = smoothstep(0.62, 0.9, max(nw.y, 0.0) * 0.75 + p.g * 0.55) * (black ? 0.0 : 1.0);
		ice = mix(ice, vec3(0.3, 0.34, 0.38) * mix(0.8, 0.42, night), rime * 0.4);
		if (black) ice = mix(vec3(l), alb, 0.2) * vec3(0.12, 0.14, 0.18) + vec3(0.005, 0.007, 0.01);
		alb = mix(alb, ice, g);
		rough = mix(rough, black ? 0.05 : mix(0.12, 0.55, rime), g);
		// Its own warm lights (a lantern, an eye, a struck flare) go dim under the ice (t10: warm beads on
		// the glazed field).
		emi *= 1.0 - 0.96 * g;
		// The rim is the brightest of it: ice-blue, cyan where the body is thin (its edges, an arm, a hand, a brim).
		// (Wide, at 2.2, the rim covered most of a small body and the pack read pale: s4f.)
		float fres = pow(rim, 3.4);
		vec3 rimc = mix(vec3(0.22, 0.56, 1.0), vec3(0.28, 1.0, 0.9), smoothstep(0.6, 0.92, rim));
		emi += rimc * fres * g * (black ? 0.06 : mix(0.2, 0.32, night));
		// The light held in the ice itself, so a statue reads from above (a hat or a crown faces the camera and has no
		// rim): its facets uneven (s1b: the far pack went black). (At 0.05-0.22 the glazed pack lifted the night frame
		// to 1.7x its ready mean for a second: s2c, §1.6.)
		emi += vec3(0.013, 0.03, 0.056) * g * (black ? 0.15 : mix(0.45, 1.0, night)) * (0.55 + 0.9 * p.r) * (0.6 + 0.4 * max(nw.y, 0.0));
		// Glints: a point of light 2-4 px across at the arena camera, a few to a body at their own spots, each
		// flashing for 4-8 frames on its own beat (judge 2: 8 cm squares in the same place read as paper chips).
		vec3 sc = wp * 12.0;
		vec3 cell = floor(sc);
		float h = fract(sin(dot(cell, vec3(12.9898, 78.233, 37.719))) * 43758.5453);
		float beat = fract(h * 13.7 + TIME * (0.35 + 0.4 * h));
		float tw = smoothstep(0.0, 0.015, beat) * (1.0 - smoothstep(0.03, 0.06, beat));
		float dotp = 1.0 - smoothstep(0.08, 0.3, length(fract(sc) - 0.5));
		float glint = step(0.95, h) * tw * dotp;
		emi += vec3(0.7, 0.9, 1.0) * glint * g * (black ? 0.4 : mix(1.2, 1.8, night)) * (0.4 + 0.6 * max(nw.y, 0.0));
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
	vec2 bat;
	vec4 bo = flare_boom(wp.xz, bat);
	g *= 1.0 - smoothstep(0.0, 0.6, bo.z);
	float l = dot(alb, FL_LUM);
	vec3 glass = mix(vec3(l), alb, 0.3) * vec3(0.4, 0.62, 1.0);
	glass *= black ? 0.25 : mix(0.4, 0.85, smoothstep(0.6, 1.0, tip));
	alb = mix(alb, glass, g);
	rough = mix(rough, black ? 0.08 : 0.16, g);
	// The BOOM's ring: the litter in its line burns with it and is char behind it. (Lying over the ground's
	// line unlit, every leaf in it was a black fleck: s2e.)
	alb = mix(alb, vec3(0.012, 0.01, 0.009), bo.z * 0.97);
	emi *= 1.0 - 0.7 * bo.z;
	emi += flare_boom_light(bo);
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
	vec2 bat;
	vec4 bo = flare_boom(wp.xz, bat);
	g *= 1.0 - smoothstep(0.0, 0.6, bo.z);
	alb = mix(alb, mix(glass, edge, spine * (black ? 0.5 : 0.85)), g);
	// Not mirror-smooth: a rock face tilted to the moon threw a still white hotspot (t10, s1b: the triangle at the
	// Verge's top centre).
	rough = mix(rough, mix(0.26, 0.38, spine), g);
	// The BOOM's ring: what it crosses is lit from the blast's side, and what faces up is charred behind it.
	if (bo.x + bo.y > 0.001) {
		float face = 0.3 + 0.7 * max(0.0, dot(nw, normalize(vec3(bat.x - wp.x, 0.4, bat.y - wp.z))));
		emi += vec3(1.0, 0.42, 0.1) * (bo.x * 0.5 + bo.y * 0.25) * face;
	}
	// (Char a dark warm brown, as on the ground.)
	alb = mix(alb, mix(vec3(dot(alb, FL_LUM)), alb, 0.5) * vec3(1.2, 0.85, 0.55) * 0.45, bo.z * 0.85 * smoothstep(0.2, 0.8, nw.y));
}

// The BOOM's line reaching a statue (judge 2, s4: statues just behind the line stood whole): it cracks, the fire
// showing orange through its glaze along hairline cracks, for the frame or three before it bursts
// (FlareFx.CrackHold). Read by vat.gdshaderinc after the glaze; 0 off the line's reach.
float flare_crack(vec3 wp) {
	if (flare_look.w < 0.5 || flare_frost.y <= 0.0) return 0.0;
	float bh = flare_boom_behind(wp.xz);
	if (bh < -0.6 || bh > 3.0) return 0.0;
	float g = flare_glazed(wp);
	float lines = 1.0 - smoothstep(0.0, 0.07, texture(flare_noise, wp.xz * 1.1 + wp.y * vec2(0.83, 1.37)).a);
	// Lines, not the whole body (a 0.3 floor lit every cracked statue a flat beige, s5).
	return smoothstep(-0.6, -0.1, bh) * g * (0.05 + 1.8 * lines);
}
