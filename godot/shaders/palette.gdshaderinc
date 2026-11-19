// (lane J art-color, 19 Nov) The world's colour per time of day (logic/Look/Palettes.cs; rigs.json "palettes"): each class a
// ramp of three colours (dark, mid, lit; linear) laid over the albedo's own value, the square root of its linear luminance
// from lo to hi, taken by amount (0: the albedo as built). Set by Atmosphere.SetPalette from the air the clock blends.
// pal_<class>0 = (dark rgb, amount), pal_<class>1 = (mid rgb, lo), pal_<class>2 = (lit rgb, hi).
// Only world classes call it: never her skin, hair, eyes or gear.
#ifndef PALETTE_INC
#define PALETTE_INC
global uniform vec4 pal_leaf0;
global uniform vec4 pal_leaf1;
global uniform vec4 pal_leaf2;
global uniform vec4 pal_grass0;
global uniform vec4 pal_grass1;
global uniform vec4 pal_grass2;
global uniform vec4 pal_ground0;
global uniform vec4 pal_ground1;
global uniform vec4 pal_ground2;
global uniform vec4 pal_path0;
global uniform vec4 pal_path1;
global uniform vec4 pal_path2;
global uniform vec4 pal_stone0;
global uniform vec4 pal_stone1;
global uniform vec4 pal_stone2;
global uniform vec4 pal_bark0;
global uniform vec4 pal_bark1;
global uniform vec4 pal_bark2;
// (ember keep) pal_ember = (near m, far m, keep, value): within near m of her light (cel_ember, cel.gdshaderinc: xyz its point, w its
// reach, 0 none) the palette is taken back by keep, eased back in to none at far m: her pool keeps its own ground at night.
global uniform vec4 pal_ember;
// (lead 2) each class its own value keep: pal_vk0 = (leaf, grass, ground, path), pal_vk1 = (stone, bark, -, -)
global uniform vec4 pal_vk0;
global uniform vec4 pal_vk1;
// (lead 3, judge r1 fix 1) the leaf class's two more crown ramps (a: crimson, b: gold by day; .w unused, the leaf ramp's amount and
// range hold), pal_leafm = (share of crowns on a, share on b, per-tree shift, tip shift), pal_leafn = (darken by the lens, from m, to m, -)
global uniform vec4 pal_leafa0;
global uniform vec4 pal_leafa1;
global uniform vec4 pal_leafa2;
global uniform vec4 pal_leafb0;
global uniform vec4 pal_leafb1;
global uniform vec4 pal_leafb2;
global uniform vec4 pal_leafm;
global uniform vec4 pal_leafn;
// (lead 3, judge r1 fix 4) pal_embera = (rgb linear, on): the ground her pool falls on, in place of the albedo as built that
// pal_ember's keep brought back (its brown under her amber read as mud)
global uniform vec4 pal_embera;
// (lead 4, judge r2 fix 8) pal_stonem = (moss rgb linear, share): laid on the stones' tops after the ramp (kit.gdshader)
global uniform vec4 pal_stonem;
// (lane J lead 5: the world's ink, the form's own contour) pal_inkw = (leaf, stone, bark weights, n.v where the line starts),
// pal_inkc = (ink rgb linear, n.v where it is full): a form's edge, where its surface turns away from the camera, inked in a
// hard band (the reference's bold line round every rock, root and crown); the screen pass (InkPass) adds the drops and creases.
global uniform vec4 pal_inkw;
global uniform vec4 pal_inkc;
vec3 pal_ink(vec3 a, vec3 n_view, vec3 vtx, float w) {
	if (w <= 0.0) return a;
	float nv = abs(dot(normalize(n_view), normalize(-vtx)));
	float k = w * (1.0 - smoothstep(pal_inkc.w, pal_inkw.w, nv));
	return mix(a, a * pal_inkc.rgb, k);
}

// (lane J lead 6, judge r4 cel fix 3: the reference draws 2-4 lines inside a stone, 2-3 down a trunk) pal_line = (stone
// frequency /m, bark frequency /m, line px, strength): isolines of a world-space value noise at a fixed screen width, broken in
// places (a second noise), in the ink colour (pal_inkc), faded where the noise runs finer than the pixels.
global uniform vec4 pal_line;
float pal_h3(vec3 p) { p = fract(p * 0.3183099 + 0.1); p *= 17.0; return fract(p.x * p.y * p.z * (p.x + p.y + p.z)); }
float pal_vn3(vec3 x) {
	vec3 i = floor(x), f = fract(x);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(mix(pal_h3(i), pal_h3(i + vec3(1, 0, 0)), f.x), mix(pal_h3(i + vec3(0, 1, 0)), pal_h3(i + vec3(1, 1, 0)), f.x), f.y),
		mix(mix(pal_h3(i + vec3(0, 0, 1)), pal_h3(i + vec3(1, 0, 1)), f.x), mix(pal_h3(i + vec3(0, 1, 1)), pal_h3(i + vec3(1, 1, 1)), f.x), f.y), f.z);
}
// p: world position already scaled (and stretched) to the line frequency
vec3 pal_lines(vec3 a, vec3 p) {
	if (pal_line.w <= 0.0) return a;
	float n = pal_vn3(p);
	float fw = max(fwidth(n), 1e-5);
	float cov = 1.0 - smoothstep(pal_line.z * 0.5 - 0.5, pal_line.z * 0.5 + 0.5, abs(n - 0.5) / fw);
	cov *= smoothstep(0.42, 0.52, pal_vn3(p * 1.3 + vec3(13.1, 7.7, 3.3)));   // (a brush line lifts off: breaks)
	cov *= 1.0 - smoothstep(0.08, 0.2, length(fwidth(p)));   // (fine as the pixels: none)
	return mix(a, a * pal_inkc.rgb, cov * pal_line.w);
}
// (lane J r6 fix 1, judge r5: inner lines fade out within 8 px of the silhouette (they read as a second contour); nv_px is the
// pixel distance to the silhouette, nv / fwidth(nv))
vec3 pal_lines_in(vec3 a, vec3 p, float nv_px) {
	vec3 b = pal_lines(a, p);
	return mix(a, b, smoothstep(8.0, 14.0, nv_px));
}
// (lane J r6 fix 1) planar facets: a flat lit face and a flat shade face, the terminator a 1-2 px edge. Cells of about 1.1 m,
// each its own plane (the normal leaned by a hash), lit by a fixed upper-left key; n the world normal
vec3 pal_facets(vec3 a, vec3 p, vec3 n, float k) {
	vec3 c = floor(p / 1.1);
	vec3 h = vec3(pal_h3(c + 3.1), pal_h3(c + 7.7), pal_h3(c + 11.3)) * 2.0 - 1.0;
	vec3 fn = normalize(n + 0.9 * h);
	float d = dot(fn, normalize(vec3(-0.45, 0.75, 0.35))) - 0.28;
	float w = max(fwidth(d), 1e-4);
	float lit = smoothstep(-w, w, d);
	return mix(a, a * mix(0.68, 1.1, lit), k);
}
// (lead 5: the reference's flat colour fields with hard edges) pal_band0 = bands for (leaf, grass, ground, path), pal_band1 =
// (stone, bark, the band edge's half width, 0): the albedo's value on the ramp taken in that many flat steps (0/1: smooth, as before)
global uniform vec4 pal_band0;
global uniform vec4 pal_band1;
float pal_bands(float u, float nb) {
	if (nb < 1.5) return u;
	float x = u * (nb - 1.0), e = max(pal_band1.z, 0.01);
	return (floor(x) + smoothstep(0.5 - e, 0.5 + e, fract(x))) / (nb - 1.0);
}
// (lane J lead 7, judge r5 (a): the crowns' camouflage) the FORM's bands (pal_ramp2's fs > 0) hard to the pixel: the step
// one pixel wide (fwidth of the band coordinate), not a share of the value: a crown's facing turns slowly across a dome,
// so band_edge's 0.05 of a band drew 10-20 px soft steps there
float pal_bands_px(float u, float nb) {
	if (nb < 1.5) return u;
	float x = u * (nb - 1.0), e = 0.5 * max(fwidth(x), 1e-4);
	return (floor(x) + smoothstep(0.5 - e, 0.5 + e, fract(x))) / (nb - 1.0);
}
// (lane J lead 6, judge r4 cel fix 4: the crowns read camouflage, the ramp's bands cut across the albedo's own speckle)
// uf, fs: the ramp's place taken this share (fs) from the form (uf: the card's facing) instead of the albedo's value
// (lead 7: uf the facing over the upper half only, 0 level to 1 up: the play camera sees a crown from above, so a cluster's
// dome, tip 0.5-1, spans two or three bands (cap, flank, rim); over -1..1 it sat in one band, one flat colour per crown)
vec3 pal_ramp2(vec3 albedo, vec4 d, vec4 m, vec4 l, float k, float shift, float vk, float nb, float uf, float fs) {
	if (d.w <= 0.0 || k <= 0.0) return albedo;
	float v = sqrt(max(dot(albedo, vec3(0.2126, 0.7152, 0.0722)), 0.0));
	if (fs < 0.0) v = mix(0.5 * (m.w + l.w), v, 0.55);   // (the albedo's texture speckle held to the middle band; the macro and dabs make the steps)
	float u0 = mix(clamp((v - m.w) / max(l.w - m.w, 1e-3), 0.0, 1.0), uf, max(fs, 0.0));
	// (lane J lead 7: fs < 0, the one-pixel band step on the albedo's own value: the painted ground and path)
	float u = fs != 0.0 ? pal_bands_px(u0, nb) : pal_bands(u0, nb);
	if (nb >= 1.5) v = m.w + u * (l.w - m.w);   // (the value kept is the band's)
	float t = clamp(u + shift, 0.0, 1.0);
	vec3 r = t < 0.5 ? mix(d.rgb, m.rgb, t * 2.0) : mix(m.rgb, l.rgb, t * 2.0 - 1.0);
	// (pal_ember.w, the palette's "value": how far the albedo's own luminance is kept, the ramp giving hue and chroma only)
	float lr = dot(r, vec3(0.2126, 0.7152, 0.0722));
	r = mix(r, r * (v * v / max(lr, 1e-4)), vk);
	// (lead 2: never brighter than 1.15 x the ramp's lit stop: a bright-albedo rock by the camera kept its value and blew out
	// to salmon in full sun, k13 (254,168,133) where the ramp's warm grey was meant; the lit stop is each class's ceiling)
	float lc = 1.15 * dot(l.rgb, vec3(0.2126, 0.7152, 0.0722));
	r *= min(1.0, lc / max(dot(r, vec3(0.2126, 0.7152, 0.0722)), 1e-4));
	if (pal_embera.w <= 0.0) return mix(albedo, r, d.w * k);
	// (lead 3: within her pool the keep takes the pool's own ground, its value turned by the albedo's)
	return mix(mix(albedo, r, d.w), pal_embera.rgb * clamp(v / 0.45, 0.6, 1.3), (1.0 - k) * d.w);
}
vec3 pal_ramp(vec3 albedo, vec4 d, vec4 m, vec4 l, float k, float shift, float vk, float nb) {
	return pal_ramp2(albedo, d, m, l, k, shift, vk, nb, 0.0, 0.0);
}
float pal_keep(vec3 wp) {
	if (pal_ember.z <= 0.0 || cel_ember.w <= 0.0) return 1.0;
	return 1.0 - pal_ember.z * (1.0 - smoothstep(pal_ember.x, max(pal_ember.y, pal_ember.x + 1e-3), distance(wp.xz, cel_ember.xz)));
}
vec3 pal_leaf(vec3 a) { return pal_ramp(a, pal_leaf0, pal_leaf1, pal_leaf2, 1.0, 0.0, pal_vk0.x, pal_band0.x); }
// (a tree its own place on the ramp: s -1..1, a per-copy hash, moves t by up to 0.3: one tree crimson, the next orange or gold)
vec3 pal_leaf(vec3 a, vec3 wp, float s) { return pal_ramp(a, pal_leaf0, pal_leaf1, pal_leaf2, pal_keep(wp), 0.3 * s, pal_vk0.x, pal_band0.x); }
// (lead 3) a crown's own ramp by its hash h (0..1): the first pal_leafm.x of them on ramp a, the last pal_leafm.y on ramp b,
// the rest on the leaf ramp; h2 (0..1) its place on it (shift pal_leafm.z), tip the spray's sky-facing (-1..1, shift pal_leafm.w)
// dist: the frame radius (0 the frame's centre, about 1 its corners; m5: by metres from the lens nothing darkened, the play
// camera stands far off): toward the frame's edges (pal_leafn: darken, from, to) the crown slides down its ramp and darkens
// (m6: by the frame radius alone the crown nearest the lens, low in the frame, was missed: also by metres, none past pal_leafn.w m, whole inside 0.55 of it)
float pal_near_w(float edge, float dist) {
	if (pal_leafn.x <= 0.0) return 0.0;
	float e = smoothstep(pal_leafn.y, max(pal_leafn.z, pal_leafn.y + 1e-3), edge);
	return pal_leafn.w > 0.0 ? max(e, 1.0 - smoothstep(0.55 * pal_leafn.w, pal_leafn.w, dist)) : e;
}
vec3 pal_leaf3(vec3 a, vec3 wp, float h, float h2, float tip, float edge, float dist) {
	float nw = pal_near_w(edge, dist);
	float sh = pal_leafm.z * (h2 * 2.0 - 1.0) + pal_leafm.w * tip - 0.2 * nw;
	vec4 d = pal_leaf0, m = pal_leaf1, l = pal_leaf2;
	if (h < pal_leafm.x) { d = vec4(pal_leafa0.rgb, pal_leaf0.w); m = vec4(pal_leafa1.rgb, pal_leaf1.w); l = vec4(pal_leafa2.rgb, pal_leaf2.w); }
	else if (h > 1.0 - pal_leafm.y) { d = vec4(pal_leafb0.rgb, pal_leaf0.w); m = vec4(pal_leafb1.rgb, pal_leaf1.w); l = vec4(pal_leafb2.rgb, pal_leaf2.w); }
	// (by the lens toward ramp a's hue: crimson by day, violet by night; lead 4, judge r2 fix 6: a gold crown toward the leaf
	// ramp's mid instead, amber, on its own dark stop: toward crimson it went khaki)
	if (nw > 0.0 && h > 1.0 - pal_leafm.y) m = vec4(mix(m.rgb, pal_leaf1.rgb, nw), pal_leaf1.w);
	else if (nw > 0.0 && h >= pal_leafm.x) { d = vec4(pal_leafa0.rgb, pal_leaf0.w); m = vec4(mix(m.rgb, pal_leafa1.rgb, nw), pal_leaf1.w); }
	return pal_ramp2(a, d, m, l, pal_keep(wp), sh - pal_band1.w * pal_leafm.w * tip, pal_vk0.x, pal_band0.x, clamp(tip, 0.0, 1.0), pal_band1.w) * (1.0 - pal_leafn.x * nw);
}
vec3 pal_leaf(vec3 a, vec3 wp) { return pal_ramp(a, pal_leaf0, pal_leaf1, pal_leaf2, pal_keep(wp), 0.0, pal_vk0.x, pal_band0.x); }
vec3 pal_grass(vec3 a) { return pal_ramp(a, pal_grass0, pal_grass1, pal_grass2, 1.0, 0.0, pal_vk0.y, pal_band0.y); }
vec3 pal_grass(vec3 a, vec3 wp) { return pal_ramp(a, pal_grass0, pal_grass1, pal_grass2, pal_keep(wp), 0.0, pal_vk0.y, pal_band0.y); }
vec3 pal_ground(vec3 a) { return pal_ramp(a, pal_ground0, pal_ground1, pal_ground2, 1.0, 0.0, pal_vk0.z, pal_band0.z); }
vec3 pal_ground(vec3 a, vec3 wp) { return pal_ramp(a, pal_ground0, pal_ground1, pal_ground2, pal_keep(wp), 0.0, pal_vk0.z, pal_band0.z); }
vec3 pal_path(vec3 a) { return pal_ramp(a, pal_path0, pal_path1, pal_path2, 1.0, 0.0, pal_vk0.w, pal_band0.w); }
vec3 pal_path(vec3 a, vec3 wp) { return pal_ramp(a, pal_path0, pal_path1, pal_path2, pal_keep(wp), 0.0, pal_vk0.w, pal_band0.w); }
vec3 pal_ground_px(vec3 a, vec3 wp) { return pal_ramp2(a, pal_ground0, pal_ground1, pal_ground2, pal_keep(wp), 0.0, pal_vk0.z, pal_band0.z, 0.0, -1.0); }
vec3 pal_path_px(vec3 a, vec3 wp) { return pal_ramp2(a, pal_path0, pal_path1, pal_path2, pal_keep(wp), 0.0, pal_vk0.w, pal_band0.w, 0.0, -1.0); }
vec3 pal_stone(vec3 a) { return pal_ramp(a, pal_stone0, pal_stone1, pal_stone2, 1.0, 0.0, pal_vk1.x, pal_band1.x); }
vec3 pal_stone(vec3 a, vec3 wp) { return pal_ramp(a, pal_stone0, pal_stone1, pal_stone2, pal_keep(wp), 0.0, pal_vk1.x, pal_band1.x); }
vec3 pal_bark(vec3 a) { return pal_ramp(a, pal_bark0, pal_bark1, pal_bark2, 1.0, 0.0, pal_vk1.y, pal_band1.y); }
vec3 pal_bark(vec3 a, vec3 wp) { return pal_ramp(a, pal_bark0, pal_bark1, pal_bark2, pal_keep(wp), 0.0, pal_vk1.y, pal_band1.y); }
#endif
