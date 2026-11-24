// The den's painted set's body (den_set.gdshader cuts at alpha 0.5; den_set_soft.gdshader blends: the hole paintings).

uniform sampler2D paint_tex : source_color, filter_linear_mipmap_anisotropic, repeat_disable;
uniform float gain = 1.0;                       // the painting's albedo scale (calibrated on the den's frames)
uniform vec3 tint = vec3(1.0);
uniform float sat = 1.0;
uniform float cold_take = 0.5;                  // how much of a cold light's brightness it takes (never its colour)
uniform float local_turn = 0.5;                 // how much a spot or omni follows the proxy's normal (0 flat)
uniform float key_shadow = 0.0;                 // 1: the key's shadow falls on it (her shadow on a spill); 0: pre-lit only
// (round 10b) The painting's own shade goes cool grey-violet, its lit masses keep their warmth: the targets' darks between
// the roots are blue-grey (90% of their pixels under 20 of 255 have B >= R), their lit root tops warm. By the painting's own
// luminance (linear): under shade_lo all shade_tint, over shade_hi all the painting's colour.
uniform vec3 shade_tint = vec3(0.84, 0.92, 1.2);
uniform float shade_lo = 0.01;
uniform float shade_hi = 0.08;
uniform float shade_k = 1.0;
// (r10c) The darks between the roots never go black: the targets' sit at L 12-20 of 255, cool; the painting's own darks
// lit at least dark_floor (an emission in shade_tint, fading out over the painting's darkest 5%), whatever light reaches them.
uniform float dark_floor = 0.0;
// (r10c) and the painting shows at least amb_floor of its own painted value where little light reaches (the frame's edges
// fell to 1/20 of it: flat black between roots the target paints at L 20-40)
uniform float amb_floor = 0.0;
uniform float glow_k = 0.95;
// (r12 judge: den_room.png's mushrooms light the ground beneath them teal) the painted caps' halo: their cyan in a coarse
// mip, a little below them in the painting (the ground they stand on), as a soft teal emission on the painting round them
uniform float mush_glow = 0.0;
uniform float fungus_sat = 1.0;   // (den r14) the painted caps' saturation (DungeonDress.SetMat: --den-fungus-sat)
uniform float mush_lod = 3.6;
uniform float mush_drop = 0.012;
uniform vec3 mush_col : source_color = vec3(0.55, 0.72, 0.69);   // (den r15 C) was .3,.85,.78: the glow pool under the caps over the band
uniform float fg_dark = 0.65;
uniform float rim_in = 1.15;    // (r11, the hole paintings) the surround shown to this many lip radii, gone by rim_out
uniform float rim_out = 1.45;
// (r12) the lair's holes glow green from below (den_boss.png: lime veins down in the pits' dark): veins by a cell
// noise's edges over the painting's own darks inside the lip; COLOR.a < 0.75 marks a lair hole (PlaceSetHole)
uniform float pit_glow = 0.0;
uniform vec3 pit_col : source_color = vec3(0.5, 0.9, 0.28);
uniform float blood_rust = 0.0;   // (den r15 C) share of the blood pulled to a rust hue (O5 only)
uniform vec3 blood_dir = vec3(1.5, 0.9, 0.45);
uniform float pit_sat = 0.3;   // (den r15 C) pit glow core saturation (judge r14: C90 .18 against .089)
uniform float pit_halo = 0.14;   // (den r15 C) the soft halo (was .07)
uniform float pit_net = 0.6;   // (den r15 P) the thin crack network's strength (0 off)
uniform float pit_floor = 0.3;   // (den r15 P) how far the pit floor takes veins whatever the painting's brightness
uniform float pit_dark = 0.35;   // (den r13 rooms) share of each pit left dark: a slow noise mask on the veins
// (den r16 A, R15f item 1) a lair pit as glowing cracks in a dark pit (den_boss.png's veined pit): inside its broken lip the
// painting gives way to a closed cell network in world metres (each pit its own, never swims): dark rock plates with a thin lit
// top edge, cracks a thin lime core in a soft green halo; an inner shadow under the lip, earth crumbs on it; 2-3 cracks run out
// past the rim (UV2: the point's floor offset from the pit's centre, PlaceSetHole). pit_cells 0: the r15 strokes on the painting
uniform float pit_cells = 0.0;
uniform float pit_cell_m = 1.0;   // metres between the plates' seeds
uniform vec3 pit_cw = vec3(0.03, 0.1, 0.55);   // metres: the core's half width, the halo's fall; share of borders lit
uniform vec3 pit_core_c = vec3(0.2, 0.33, 0.1);   // linear: the cores' and the halo's emission
uniform vec3 pit_halo_c = vec3(0.05, 0.16, 0.02);
uniform vec3 pit_plate_c = vec3(0.05, 0.052, 0.046);   // linear: the plates' albedo
uniform vec3 pit_lipw = vec3(0.14, 0.05, 0.6);   // the inner shadow's width (lip radii), the lip's break, the plates' lit edge
uniform vec3 pit_ray = vec3(1.0, 0.75, 1.35);   // the past-rim cracks on, their length past the lip (metres) min, max
// (den r16 A2, R15f item 1: it read as a raised turtle shell) the pit sunken: x its depth (metres; the view ray carried down,
// so the far wall shows and the floor shifts as the camera moves; 0 flat), y the near lip's shadow reach (x depth), z the
// plates' brightness at the middle (x); pit_wall_c the wall's earth face (linear albedo). COLOR.g: the lip's radius / 8
uniform vec3 pit_deep = vec3(0.0, 1.6, 0.55);
uniform vec3 pit_wall_c = vec3(0.06, 0.042, 0.028);
uniform float pit_cast_min = 0.16;   // (den r17 P, R16 item 1) the near lip's shadow's floor (r16 .16: a .13-.19 band inside the near rim)
// (den r17 P2, R16 item 1: still a dome) pit_bowl 1: the pit a bowl, as den_boss.png's. Its inside (floor and wall) takes no spot
// or omni light (pit_pt, read in light(): the PitGlow and the shafts lit its middle as the floor's), only the key and the ambient,
// so its floor is flat; the far wall an earth band lit at the brink, falling to pit_bw.x of that at its foot; the floor dark at
// the far wall's foot (pit_bw.y within pit_bw.z metres: the far rim's shade), no all-round vignette, no band inside the near rim;
// the lip a smooth noise (no per-chunk steps: the r16 notches), no square crumbs, the past-rim glow's fringe not boosted (the seam).
// 0: as r16 / r17 P
uniform float pit_bowl = 0.0;
uniform vec3 pit_bw = vec3(0.35, 0.55, 0.5);
// (den r18 P4, R17 item 1: tiles, card seams, a terraced wall, wires) pit_v2 1: the floor one continuous surface (no per-plate
// shade, no plate top edges), its veins the cells' borders warped hard (pit_vein.z cells) with a width (x m, half) and light
// varying along them, a finer branch layer (w) and a broad bleed (y m); the far wall one gradient (pit_wg: lip, foot, power),
// no strata, no brink band; the floor shaded under the near lip (pit_near: factor at the lip, reach m); the wall radius taken
// from the drawn lip (no per-vertex steps); the shader's thin root lines off (the painted B6 roots lie over the lips)
uniform float pit_v2 = 0.0;
uniform vec4 pit_vein = vec4(0.06, 0.15, 0.55, 0.35);
uniform vec3 pit_wg = vec3(1.4, 0.45, 0.8);
uniform vec2 pit_near = vec2(0.7, 0.9);
uniform vec2 pit_self = vec2(1.0, 0.0);   // the bowl's albedo share kept under the room's light, and its own light (x albedo)
// (den r18 P5, R17 items 1, 5) pit_paint.x > 0: a painted lair pit (H3, den_boss.png's bowls: the far wall lit, the near lip shaded,
// roots over the lips): its lime pixels (G over max(R, B), from z to w, linear) emit x times their colour, y of their albedo taken
// off; pit_paint_pt the share of a spot's or omni's light kept inside its lip (the painting carries its own light)
uniform vec4 pit_paint = vec4(0.0, 0.5, 0.02, 0.25);
uniform float pit_paint_pt = 0.0;
// (den r18 P5) the veins' glow bled onto the rock: the lime-ness of the painting's mips (lod y and y + 1.5, from 0 to z) emits
// pit_bleed_c x x, inside the lip (den_boss.png's glow runs 10-20 px off each vein; the painting's own about 5)
uniform vec4 pit_bleed = vec4(0.0, 3.5, 0.06, 0.0);
uniform vec3 pit_bleed_c = vec3(0.16, 0.4, 0.06);
// (den r19 V2, R18b item 1) pit_cmax > 0: the painted pit's emissive and bleed colours clamped to this OKLab chroma (same luminance), 0 off
uniform float pit_cmax = 0.0;
// (den r19 V2, R18b item 6) the painted pit's rim: pit_gaps (half-width rad, ell from, ell to; 0 off) 2-3 wedges of its crumb ring cut away by
// angle hash; pit_fall (x: albedo off at the painting's outer edge, y: blur lod of the alpha it reads; x 0 off) a darker earth falloff
uniform vec3 pit_gaps = vec3(0.0, 1.05, 1.3);
uniform vec2 pit_fall = vec2(0.0, 4.0);
// (den r19 S, R19 judge item 1: the pits inverted, the mip bleed lit the plates mid-green and left the cracks dark) pit_lines > 0:
// the painted pit's light from its vein mask (pit_vein_tex, den_set.py veins: R the cores, G a narrow glow, B a wider one, from
// the painting's own lime lines): pit_line_core x R + pit_line_glow x (pit_line_w.x G + pit_line_w.y B), the cores' albedo off
// by pit_line_w.z; no lime emission and no bleed, so the plates keep the painting's dark albedo. 0: the lime and bleed path
uniform float pit_lines = 0.0;
uniform sampler2D pit_vein_tex : hint_default_black, filter_linear_mipmap, repeat_disable;
uniform vec3 pit_line_core = vec3(0.3, 0.55, 0.16);
uniform vec3 pit_line_glow = vec3(0.05, 0.11, 0.03);
uniform vec3 pit_line_w = vec3(1.0, 0.5, 1.0);
vec3 pit_cclamp(vec3 rgb) {
	if (pit_cmax <= 0.0) return rgb;
	vec3 lms = vec3(0.4122214708 * rgb.r + 0.5363325363 * rgb.g + 0.0514459929 * rgb.b,
		0.2119034982 * rgb.r + 0.6806995451 * rgb.g + 0.1073969566 * rgb.b,
		0.0883024619 * rgb.r + 0.2817188376 * rgb.g + 0.6299787005 * rgb.b);
	lms = pow(max(lms, vec3(1e-9)), vec3(1.0 / 3.0));
	float a = 1.9779984951 * lms.x - 2.4285922050 * lms.y + 0.4505937099 * lms.z;
	float b = 0.0259040371 * lms.x + 0.7827717662 * lms.y - 0.8086757660 * lms.z;
	float k = min(1.0, pit_cmax / max(length(vec2(a, b)), 1e-5));
	return mix(vec3(dot(rgb, vec3(0.2126, 0.7152, 0.0722))), rgb, k);
}
// (den r18 lead, R18 judge item 1: the veins neon, glow C50 .150 / C90 .195 against den_boss .073 / .089, cores L99 .85-.88
// against .60-.72) the veins' look: x the saturation kept in their emission and albedo (1: r18 as judged), y the emission's
// luminance cap (linear; 0 off)
uniform vec2 pit_look = vec2(1.0, 0.0);
// (den r18 lead, R18 judge item 5: the pit rims stickers, a pale crumb ring ending hard with a lilac fringe) x the painting
// darkened by this much toward its fade (an earth falloff), y the lilac fringe's saturation taken out near the rim (0 off)
uniform vec2 pit_rim = vec2(0.0, 0.0);
// (den r18 lead, R18 judge item 5: the crumb ring ends hard on the floor) the painting's own edge eroded and feathered: its
// alpha read at this mip (0 off) from x to y
uniform vec3 pit_feather = vec3(0.0, 0.5, 0.95);
varying float pit_pt;
// (r12) the lair's gloom (dungeon_floor.gdshader's boss_gloom, the same rule): its pools of light in the middle, the
// ground and its dressing falling dark and cool toward the walls (den_boss.png: its 12-35 band 13 %, cool 18.8 %)
uniform vec3 boss_c = vec3(0.0);
uniform float boss_gloom = 0.0;
uniform vec4 spur_seg[16];   // (den r16 G2, R15f item 11) the lair's root spurs (x0, z0, x1, z1), spur_r their radii (0: none)
uniform float spur_r[16];
uniform float spur_lift = 0.0;   // the gloom taken off within 1-4 m of a spur (0: off)
uniform float hi_roll = 1.0;   // (den r14 corr) the near banks' highlights' scale (1 off)
uniform float top_k = 1.0;   // (den r16 D, R15f item 4) every bank card's lit tops (the painting's light masses) scaled by this (1 off)
uniform float corr_k = 1.0;   // (den r16 D, R15f item 4) a bank card's albedo x this in the corridors (corr_tex: DenRagged's corridor weight; 1 off)
uniform sampler2D corr_tex : filter_linear, repeat_disable;
uniform vec3 corr_map = vec3(0.0);   // x, z of the texture's corner, 1 / its size in metres
uniform float pt_take = 1.0;   // (den r16 D, R15f item 4) share of a spot's or omni's light a bank card takes (1 off; the key and ambient whole)
uniform float bank_gloom = 0.0;   // (den r13 corr) the corridor banks' depth gloom (--den-set-gloom)
uniform float dbg_mod = 0.0;   // (den r15 E, diagnosis: --den-set-dbgmod) each bank module a false colour (COLOR.a), rows behind striped
// (den r15 E, judge r14 item 4) a bank card's cut (COLOR.g's 0.5 contour) wanders at a fine scale and follows the painting's
// masses: the threshold moved by a world value noise (cut_noise: its share of the ramp) and by the painting's local brightness
// (cut_lum: lit roots kept further out, dark gaps cut first), so a border ends in root shapes, not a ruled line. 0, 0: off
uniform float cut_noise = 0.0;
uniform float cut_lum = 0.0;
uniform float cut_scale = 2.2;   // the noise's cycles per metre (two octaves)
uniform vec2 gloom_m = vec2(2.5, 6.5);   // metres into the bank: from, full
// (den r14 objects, item 3) the lit open-floor boulders (sheet O1r): the painting's facets blurred out (rock_lod), a lit warm top
// (COLOR.b: the card's v, 0 at the top) mottled by cell noise and mossed, as den_room.png's round stones. 0: off (banks, other sheets)
uniform float rock_k = 0.0;
uniform float rock_lod = 2.2;
uniform vec3 rock_lit = vec3(0.23, 0.155, 0.085);
uniform vec3 rock_moss = vec3(0.1, 0.13, 0.04);
uniform float rock_moss_k = 0.6;
varying vec3 wpos;
// (den r15 F, lane A judge: the den's roots drew over her) the occlusion cut-out: a fragment of the set nearer the camera than
// her chest and above her knees, inside a screen-space disc round her, is dithered out to occ_a of itself (soft edge, as
// dungeon_wall's cutaway). occ_k 0 off (--den-occlude). Her chest is the global 'survivor' (WorldScene), w 1 in the world.
global uniform vec4 survivor;
uniform float occ_k = 0.0;
uniform float occ_a = 0.2;        // the share kept in the middle
uniform vec2 occ_r = vec2(0.085, 0.15);   // full cut inside / none outside, in viewport heights from her
float occ_bayer(ivec2 p) {
	int x = p.x & 7;
	int y = p.y & 7;
	int v = 0;
	for (int i = 2; i >= 0; i--) {
		v = (v << 2) | ((((x >> i) & 1) ^ ((y >> i) & 1)) << 1) | ((y >> i) & 1);
	}
	return (float(v) + 0.5) / 64.0;
}
bool occ_cut(mat4 vm, mat4 pm, vec3 vtx, vec3 wp, vec4 frag, vec2 vp) {
	if (occ_k <= 0.0 || survivor.w <= 0.0 || wp.y < survivor.y - 0.2) return false;
	vec3 her_v = (vm * vec4(survivor.xyz, 1.0)).xyz;
	if (-vtx.z >= -her_v.z - 0.4) return false;
	vec4 hp = pm * vec4(her_v, 1.0);
	vec2 ndc = hp.xy / hp.w;
	vec2 her_px = vec2(ndc.x * 0.5 + 0.5, 0.5 - ndc.y * 0.5) * vp;
	float d = length(frag.xy - her_px) / vp.y;
	float hole = (1.0 - occ_a) * occ_k * (1.0 - smoothstep(occ_r.x, occ_r.y, d));
	return occ_bayer(ivec2(frag.xy)) < hole;
}
void vertex() { wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; }
float lair_gloom(vec3 p) {
	if (boss_c.z <= 0.0 || boss_gloom <= 0.0) return 0.0;
	float d = distance(p.xz, boss_c.xy);
	float near = 0.0;
	for (int i = 0; i < 16; i++) {
		if (spur_r[i] <= 0.0) continue;
		vec2 a = spur_seg[i].xy, ab = spur_seg[i].zw - a;
		float t = clamp(dot(p.xz - a, ab) / max(dot(ab, ab), 1e-4), 0.0, 1.0);
		near = max(near, 1.0 - smoothstep(1.0, 4.0, distance(p.xz, a + ab * t) - spur_r[i]));
	}
	return boss_gloom * smoothstep(boss_c.z * 0.3, boss_c.z * 0.75, d) * (1.0 - smoothstep(boss_c.z * 1.2, boss_c.z * 1.5, d)) * (1.0 - spur_lift * near);
}
vec3 gloom_col(vec3 c, float g) { return mix(c, vec3(dot(c, vec3(0.3, 0.55, 0.15))) * vec3(0.8, 0.95, 1.25), 0.7 * g) * (1.0 - 0.55 * g); }
// (tester lane, 23 Nov, coordinator option a) An integer hash (pcg2d, Jarzynski & Olano 2020) in place of fract(sin(dot) * 43758.5):
// sin of arguments near 10^4 and a fused or split multiply-add differ by GPU and driver, so the old pattern was not the same on
// D3D12 and Vulkan (parity round 2: the den floor busier on D3D12), nor (inference) across GPU makers. The input is quantized to
// 1/256 first (integer cells stay exact; a fraction an ulp apart only flips at a 1/256 step), out uniform in [0, 1) as before.
vec2 pg_h2(vec2 p) {
	uvec2 v = uvec2(ivec2(floor(p * 256.0 + 0.5)));
	v = v * 1664525u + 1013904223u;
	v.x += v.y * 1664525u; v.y += v.x * 1664525u;
	v = v ^ (v >> 16u);
	v.x += v.y * 1664525u; v.y += v.x * 1664525u;
	v = v ^ (v >> 16u);
	return vec2(v >> 8u) * (1.0 / 16777216.0);
}
float pg_vn(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(pg_h2(i).x, pg_h2(i + vec2(1.0, 0.0)).x, f.x), mix(pg_h2(i + vec2(0.0, 1.0)).x, pg_h2(i + vec2(1.0, 1.0)).x, f.x), f.y);
}
// (den r14 objects, item 12) branching cracks: the ridge of a domain-warped noise (thin lit line, soft halo), not cell edges
float pg_ridge(vec2 p) {
	vec2 w = vec2(pg_vn(p * 0.7 + 3.1), pg_vn(p * 0.7 - 5.7));
	return 1.0 - abs(2.0 * pg_vn(p + 2.5 * w) - 1.0);
}
float pg_edge(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	float d1 = 8.0, d2 = 8.0;
	for (int y = -1; y <= 1; y++) for (int x = -1; x <= 1; x++) {
		vec2 g = vec2(float(x), float(y)), o = pg_h2(i + g);
		float d = length(g + o - f);
		if (d < d1) { d2 = d1; d1 = d; } else if (d < d2) d2 = d;
	}
	return d2 - d1;
}
// (den r16 A) the pits' closed cell network: IQ's two-pass Voronoi (the distance to the cell's nearest border), each border's
// glow (a core and an e-fold halo, summed over the cell's own borders) lit or dark by its own hash (the same from both sides),
// and the plate's lit top edge (a border whose normal points up the frame, -z). x: border distance, y core, z halo, w top edge
vec2 pc_seed(vec2 c) { return 0.12 + 0.76 * pg_h2(c); }
vec4 pc_net(vec2 x, float cw, float hw, float aa, float share, out float cell_h, out float bot) {
	vec2 n = floor(x), f = fract(x), mg = vec2(0.0), mr = vec2(0.0);
	float md = 8.0;
	for (int j = -1; j <= 1; j++) for (int i = -1; i <= 1; i++) {
		vec2 g = vec2(float(i), float(j)), r = g + pc_seed(n + g) - f;
		float d = dot(r, r);
		if (d < md) { md = d; mr = r; mg = g; }
	}
	vec2 cid = n + mg;
	cell_h = pg_h2(cid + 7.31).y;
	md = 8.0;
	float core = 0.0, halo = 0.0, top = 0.0;
	bot = 0.0;
	for (int j = -2; j <= 2; j++) for (int i = -2; i <= 2; i++) {
		vec2 g = mg + vec2(float(i), float(j)), r = g + pc_seed(n + g) - f, dr = r - mr;
		float l2 = dot(dr, dr);
		if (l2 < 1e-5) continue;
		vec2 nr = dr * inversesqrt(l2);
		float d = dot(0.5 * (mr + r), nr);
		if (d > 0.7) continue;
		md = min(md, d);
		vec2 eh = pg_h2(cid + n + g + 3.7);
		float s = smoothstep(-0.12, 0.12, share - eh.x) * (0.5 + 0.5 * eh.y);   // (den r17 P, R16 item 1) share = the share lit (r16: 1 - share was)
		core += s * (1.0 - smoothstep(cw - aa, cw + aa, d));
		halo += s * exp(-max(d - cw, 0.0) / hw);
		float up = clamp(-nr.y, 0.0, 1.0);
		top = max(top, up * up * (smoothstep(cw + 0.4 * aa, cw + 1.1 * aa, d) - smoothstep(cw + 1.6 * aa, cw + 2.6 * aa, d)));   // (den r16 A2) 1-2 px
		bot = max(bot, clamp(nr.y, 0.0, 1.0) * (1.0 - smoothstep(cw + aa, cw + 7.0 * aa, d)));
	}
	return vec4(md, min(core, 1.3), min(halo, 1.6), top);
}

void fragment() {
	if (occ_cut(VIEW_MATRIX, PROJECTION_MATRIX, VERTEX, wpos, FRAGCOORD, VIEWPORT_SIZE)) discard;   // (den r15 F)
	pit_pt = 1.0;
	vec4 c = texture(paint_tex, UV);
	if (rock_k > 0.0) {
		vec4 cb = textureLod(paint_tex, UV, rock_lod);
		float lbm = dot(cb.rgb, vec3(0.299, 0.587, 0.114));
		vec2 q = UV * 70.0;
		float m1 = pg_edge(q), m2 = pg_edge(q * 3.1 + 7.0);
		float mot = clamp(0.55 + 0.9 * (0.6 * pg_vn(q * 0.18 + 1.0) + 0.4 * pg_vn(q * 0.55 + 4.0)), 0.55, 1.4);
		float top = smoothstep(0.8, 0.12, COLOR.b);
		float ab = textureLod(paint_tex, UV, 3.0).a;
		float rim = smoothstep(0.35, 0.95, ab);
		// form: lit across the top, falling to a dark belly and a darker rim; cracks as thin dark cell edges
		float form = mix(0.42, 1.2, top) * mix(0.55, 1.0, rim);
		float crack = 1.0 - 0.12 * pg_ridge(q * 0.3 + 2.0) * pg_ridge(q * 0.3 + 2.0);
		vec3 stone = rock_lit * mot * form * crack * clamp(0.75 + lbm * 3.0, 0.8, 1.3);
		float ms = top * rim * smoothstep(0.45, 0.7, 0.7 * pg_vn(q * 0.2 + 9.0) + 0.3 * pg_vn(q * 0.7) + 0.2 * top) * rock_moss_k;
		stone = mix(stone, rock_moss * mot * (0.6 + 0.6 * form), ms);
		vec3 rb = mix(cb.rgb * 0.9, stone, rock_k);
		c = vec4(rb, c.a);
	}
	float lb = dot(textureLod(paint_tex, UV, 3.0).rgb, vec3(0.299, 0.587, 0.114));
	float s = smoothstep(0.1, 0.4, sqrt(max(lb, 0.0)));
	float show = step(1.0, s + COLOR.r + 0.001);
	vec3 col = c.rgb * tint;
	float l = dot(col, vec3(0.299, 0.587, 0.114));
	col = mix(vec3(l), col, sat);
	col = mix(col, vec3(l) * blood_dir, blood_rust);
	// (den r14 lead, lane E note) the painted fungus' cyan held in its band (C .053-.080 under E's grade, .10-.11 before)
	float cyan = smoothstep(0.05, 0.2, min(c.g, c.b) - c.r);
	col = mix(col, mix(vec3(l), col, fungus_sat), cyan);
	col = mix(col, vec3(l) * shade_tint, shade_k * (1.0 - smoothstep(shade_lo, shade_hi, l)));
	col = gloom_col(col, lair_gloom(wpos));
	// (den r14 corr, item 9) the camera-side banks' lit tops rolled off and warmed (hi_roll 1: off; DungeonDress.SetMat)
	col = mix(col, col * hi_roll * vec3(1.0, 0.93, 0.84), smoothstep(0.05, 0.22, l) * step(hi_roll, 0.999));
	col *= mix(1.0, top_k, smoothstep(0.04, 0.2, l));
	if (corr_k != 1.0 && corr_map.z > 0.0) col *= mix(1.0, corr_k, texture(corr_tex, (wpos.xz - corr_map.xy) * corr_map.z).r);   // (den r16 D)   // (den r16 D) the banks' lit tops down (DungeonDress --den-bank-top)
#ifndef SET_SOFT
	// (den r13 corr) a corridor bank's roots go dark warm umber as they lie deeper in the bank (COLOR.b: metres in / 10,
	// 0 outside the corridors and on objects): the deep rows' borders and the mound behind them meet in the gloom
	float bg = bank_gloom * smoothstep(gloom_m.x, gloom_m.y, COLOR.b * 10.0);
	col = mix(col, vec3(dot(col, vec3(0.299, 0.587, 0.114))) * vec3(1.0, 0.84, 0.7) * 0.3, bg);
#endif
	ALBEDO =col * gain * mix(1.0, fg_dark, smoothstep(0.82, 1.0, SCREEN_UV.y));   // (r11 judge: the nearest banks fall off, as den_room.png's bottom row)
	EMISSION = col * gain * amb_floor + shade_tint * dark_floor * (1.0 - smoothstep(0.0, 0.05, l));
	// (r10d) the painted glow caps (pale cyan: G and B well over R) give their own light, whatever reaches them
	EMISSION += mix(vec3(dot(c.rgb, vec3(0.299, 0.587, 0.114))), c.rgb, fungus_sat) * glow_k * cyan;
	if (mush_glow > 0.0) {
		vec3 hb = textureLod(paint_tex, UV - vec2(0.0, mush_drop), mush_lod).rgb;
		vec3 hc = textureLod(paint_tex, UV - vec2(0.0, mush_drop), mush_lod + 1.0).rgb;
		// cyan AND bright in the mip: the painting's cool dark hollows (B over R, dim) take none
		float hm = max(smoothstep(-0.02, 0.05, min(hb.g, hb.b) - hb.r * 0.9) * smoothstep(0.1, 0.2, dot(hb, vec3(0.299, 0.587, 0.114))),
			0.6 * smoothstep(-0.03, 0.04, min(hc.g, hc.b) - hc.r * 0.9) * smoothstep(0.07, 0.15, dot(hc, vec3(0.299, 0.587, 0.114))));
		EMISSION += mush_col * mush_glow * hm * (1.0 - smoothstep(0.05, 0.2, min(c.g, c.b) - c.r));
	}
	float cut_t = 0.5;
#ifndef SET_SOFT
	if (cut_noise > 0.0 || cut_lum > 0.0) {
		vec2 cq = wpos.xz * cut_scale;
		float fn = 0.62 * pg_vn(cq + 17.3) + 0.38 * pg_vn(cq * 2.7 - 4.1);
		cut_t = clamp(0.5 + cut_noise * (fn - 0.5) * 2.0 + cut_lum * (0.5 - s), 0.03, 0.97);
		// the fades (a run's ends, the image's own cut: COLOR.r) gone before the card's geometric end: at COLOR.r 0 the bright
		// masses still showed, cut by the card's last column (s23 corridor x 1490-1500, a module's end ruled for 260 px)
		show = step(1.0, 0.8 * s + 1.25 * COLOR.r + 0.5 * cut_noise * (fn - 0.5));
	}
#endif
	ALPHA = c.a * show * step(cut_t, COLOR.g);
#ifndef SET_SOFT
	if (dbg_mod > 0.0) {
		vec3 hc = clamp(abs(fract(fract(COLOR.a * 2.0) + vec3(0.0, 2.0 / 3.0, 1.0 / 3.0)) * 6.0 - 3.0) - 1.0, 0.0, 1.0);
		float stripe = COLOR.a >= 0.5 ? step(0.5, fract((FRAGCOORD.x + FRAGCOORD.y) / 14.0)) : 1.0;
		vec3 dc = hc * (0.2 + 0.8 * clamp(dot(c.rgb, vec3(0.299, 0.587, 0.114)) * 2.5, 0.0, 1.0)) * mix(0.3, 1.0, stripe) * mix(0.5, 1.0, step(0.999, COLOR.r));
		ALBEDO = dc * 0.1;
		EMISSION = dc * dbg_mod;
	}
#endif
#ifdef SET_SOFT
	// (r11) a hole painting's own earth surround fades out past its rim (COLOR.b: half the distance in lip radii)
	ALPHA *= 1.0 - smoothstep(rim_in, rim_out, 2.0 * COLOR.b);
	if (pit_paint.x > 0.0 && COLOR.a < 0.75) {   // (den r18 P5) see pit_paint
		float lime = smoothstep(pit_paint.z, pit_paint.w, c.g - max(c.r, c.b));
		if (pit_lines > 0.0) {   // (den r19 S) see pit_lines: the painted lime keeps its albedo cut and grey (below), its emission and bleed off
			vec3 pvm = texture(pit_vein_tex, UV).rgb;
			ALBEDO *= 1.0 - pit_line_w.z * pvm.r;
			EMISSION += pit_cclamp(pit_line_core * pvm.r + pit_line_glow * (pit_line_w.x * pvm.g + pit_line_w.y * pvm.b)) * (0.92 + 0.08 * sin(TIME * 1.3 + wpos.x * 0.7));
		}
		ALBEDO *= 1.0 - pit_paint.y * lime;
		ALBEDO = mix(vec3(dot(ALBEDO, vec3(0.2126, 0.7152, 0.0722))), ALBEDO, mix(1.0, pit_look.x, lime));
		vec3 pem = c.rgb * pit_paint.x * lime * (0.92 + 0.08 * sin(TIME * 1.3 + wpos.x * 0.7));
		float pel = dot(pem, vec3(0.2126, 0.7152, 0.0722));
		pem = mix(vec3(pel), pem, pit_look.x);
		pem = pit_cclamp(pem);
		if (pit_look.y > 0.0) pem *= min(1.0, pit_look.y / max(pel, 1e-4));
		EMISSION += pem * step(pit_lines, 0.0);
		float prb = smoothstep(rim_in - 0.3, rim_out, 2.0 * COLOR.b);
		float plil = smoothstep(0.0, 0.03, min(c.r, c.b) - c.g) * smoothstep(0.75, 1.0, 2.0 * COLOR.b);
		ALBEDO = mix(ALBEDO, vec3(dot(ALBEDO, vec3(0.2126, 0.7152, 0.0722))) * vec3(1.04, 1.0, 0.9), pit_rim.y * plil);
		ALBEDO *= 1.0 - pit_rim.x * prb;
		if (pit_feather.x > 0.0) ALPHA *= smoothstep(pit_feather.y, pit_feather.z, textureLod(paint_tex, UV, pit_feather.x).a);
		if (pit_gaps.x > 0.0) {
			vec2 gsd = pg_h2(floor((wpos.xz - UV2) * 2.0 + 0.5) + 77.0);
			float ga = atan(UV2.y, UV2.x), gm = 0.0;
			for (int gi = 0; gi < 3; gi++) {
				float gc = gsd.x * 6.2832 + float(gi) * 2.0944 + (gi == 0 ? 0.0 : 0.7 * (pg_h2(gsd + float(gi)).x - 0.5));
				float gd = abs(mod(ga - gc + 3.1416, 6.2832) - 3.1416);
				gm = max(gm, (gi < 2 || gsd.y > 0.5 ? 1.0 : 0.0) * (1.0 - smoothstep(pit_gaps.x * 0.6, pit_gaps.x, gd)));
			}
			ALPHA *= 1.0 - gm * (1.0 - smoothstep(pit_gaps.y, pit_gaps.z, textureLod(paint_tex, UV, 5.0).a));   // the wedge's outer band eroded (the blurred alpha under pit_gaps.y .. .z)
		}
		if (pit_fall.x > 0.0) ALBEDO *= 1.0 - pit_fall.x * (1.0 - smoothstep(0.5, 0.95, textureLod(paint_tex, UV, pit_fall.y).a));
		pit_pt = mix(1.0, pit_paint_pt, 1.0 - smoothstep(0.85, 1.05, 2.0 * COLOR.b));
		vec3 cb1 = textureLod(paint_tex, UV, pit_bleed.y).rgb, cb2 = textureLod(paint_tex, UV, pit_bleed.y + 1.5).rgb;
		float lbl = 0.6 * smoothstep(0.0, pit_bleed.z, cb1.g - max(cb1.r, cb1.b)) + 0.4 * smoothstep(0.0, pit_bleed.z, cb2.g - max(cb2.r, cb2.b));
		EMISSION += pit_cclamp(pit_bleed_c * pit_bleed.x) * lbl * (1.0 - lime) * (1.0 - smoothstep(0.9, 1.05, 2.0 * COLOR.b)) * step(pit_lines, 0.0);   // (den r19 S) no bleed under pit_lines
	} else
	if (pit_cells > 0.0 && pit_glow > 0.0 && COLOR.a < 0.75) {   // (den r16 A, R15f item 1) see pit_cells
		// (den r16 A2) sunken (see pit_deep): the view ray carried pit_deep.x metres down. Where it meets the pit's wall before its
		// floor, the wall's dark earth face (the far side, lit at its brink, dark at its foot); else the floor's plates where the ray
		// lands: shadowed by the near lip, dark at the wall's foot and toward the middle, the glow brightest in the deepest seams, in
		// bright and dim zones. The lip broken in chunks and lobes, root ends over it, crumbs of earth
		vec2 xz = wpos.xz, off = UV2;
		float ell = 2.0 * COLOR.b, rr = length(off), R0 = max(8.0 * COLOR.g, 0.3), dep = max(pit_deep.x, 0.0);
		vec2 sd = pg_h2(floor((xz - off) * 2.0 + 0.5) + 41.0);   // the pit's own seed (its centre)
		vec2 kq = xz / 0.22, kn = floor(kq), kf = fract(kq), kid = kn, kr = vec2(0.0);
		float k1 = 8.0;
		for (int j = -1; j <= 1; j++) for (int i = -1; i <= 1; i++) {
			vec2 g = vec2(float(i), float(j)), r = g + pc_seed(kn + g) - kf;
			float d = dot(r, r);
			if (d < k1) { k1 = d; kid = kn + g; kr = r; }
		}
		vec2 kh = pg_h2(kid + 5.1);
		float en = ell + pit_lipw.y * (mix(kh.x - 0.5, 0.8 * (pg_vn(xz * 5.5 + sd * 17.0) - 0.5), pit_bowl) + 0.7 * (pg_vn(xz * 2.3 + sd * 60.0) - 0.5) + 1.1 * (pg_vn(xz * 0.75 + sd * 31.0) - 0.5));
		float ea = max(fwidth(en), 1e-4);
		float inside = 1.0 - smoothstep(1.0 - ea, 1.0 + ea, en), u = max(1.0 - en, 0.0);
		// the view ray: where it meets the wall (tau < 1) or the floor (tau >= 1), the lip a circle of R0 round this bearing
		vec3 vd = normalize(wpos - CAMERA_POSITION_WORLD);
		vec2 sv = vd.xz / max(-vd.y, 0.2) * dep;
		R0 = mix(R0, rr / max(en, 1e-3), pit_v2 * smoothstep(0.3, 0.55, en));   // (den r18 P4) the wall at the drawn lip, not the vertices' radius
		float qa = max(dot(sv, sv), 1e-6), qb = 2.0 * dot(off, sv), qc = dot(off, off) - R0 * R0;
		float tau = qc >= 0.0 ? 0.0 : (-qb + sqrt(max(qb * qb - 4.0 * qa * qc, 0.0))) / (2.0 * qa);
		float wall = 1.0 - smoothstep(1.0 - max(fwidth(tau), 1e-3), 1.0, tau);
		// the floor: plates and cracks where the ray lands (the coordinates warped: the cracks wander, with a fine jag)
		vec2 of = off + sv, pf = xz + sv;
		float ef = length(of) / R0;
		vec2 bk = sv * inversesqrt(qa);
		float ob = dot(of, bk), tb = ob + sqrt(max(ob * ob - dot(of, of) + R0 * R0, 0.0));   // metres back toward the camera to the wall
		float cast = smoothstep(0.55, 1.35, tb / max(dep * pit_deep.y, 1e-3));   // 0: in the near lip's shadow
		float aof = smoothstep(0.0, 0.2, 1.0 - ef), mid = smoothstep(0.9, 0.15, ef);
		vec2 x = pf / pit_cell_m;
		x += 0.32 * (vec2(pg_vn(x * 0.9 + 1.7), pg_vn(x * 0.9 - 6.3)) - 0.5) + 0.07 * (vec2(pg_vn(x * 4.1 + 2.9), pg_vn(x * 4.1 - 8.2)) - 0.5);
		float aa = 0.75 * length(fwidth(x)), ch, bot, cwc = pit_cw.x / pit_cell_m;
		vec4 nt = pc_net(x, cwc, pit_cw.y / pit_cell_m, aa, pit_cw.z, ch, bot);
		float lit2 = 1.0;
		if (pit_v2 > 0.0) {
			// (den r18 P4) the veins: the borders' distance (no plate's own shade or lit edge), warped hard so no border runs straight;
			// each vein fat or thin along its run and lit or dying out (the branches end), warped ridges between, the bleed broad
			vec2 y = pf / pit_cell_m;
			y += pit_vein.z * (vec2(pg_vn(y * 0.6 + 1.7), pg_vn(y * 0.6 - 6.3)) - 0.5) + 0.35 * pit_vein.z * (vec2(pg_vn(y * 2.1 + 2.9), pg_vn(y * 2.1 - 8.2)) - 0.5);
			float h2, b2;
			vec4 n2 = pc_net(y, 0.0, 1.0, 0.0, 1.0, h2, b2);
			float d = n2.x * pit_cell_m;
			float wv = pg_vn(pf * 1.1 + sd * 23.0), lv = pg_vn(pf * 0.45 + sd * 37.0);
			float hw0 = pit_vein.x * mix(0.3, 1.5, wv);
			lit2 = smoothstep(0.18, 0.5, 0.65 * lv + 0.35 * wv);
			float core = (1.0 - smoothstep(0.45 * hw0, hw0 + 0.01, d)) * lit2;
			float halo = exp(-max(d - 0.45 * hw0, 0.0) / pit_vein.y) * mix(0.2, 1.0, lit2);
			float sub = smoothstep(0.93, 0.99, pg_ridge(pf * 1.7 + sd * 11.0)) * pit_vein.w * (1.0 - smoothstep(0.0, 0.5, core)) * smoothstep(0.08, 0.3, d);
			nt = vec4(d / pit_cell_m, min(core + sub, 1.3), min(halo + 0.6 * sub, 1.6), 0.0);
			ch = 0.5 + 0.35 * (pg_vn(pf * 0.8 + 4.0) - 0.5);
		}
		float grain = 1.0 + 0.22 * (pg_vn(pf * 9.0) - 0.5) + 0.12 * (pg_vn(pf * 23.0) - 0.5);
		float fine = 1.0 - mix(0.3, 0.12, pit_v2) * (1.0 - smoothstep(0.0, 0.08, pg_edge(x * 3.3 + 9.1)));   // hairline cracks across a plate
		vec3 alb = pit_plate_c * (0.6 + 0.8 * ch) * grain * fine * (1.0 + 2.0 * pit_lipw.z * nt.w);
		alb *= mix(0.25, 1.0, smoothstep(cwc * 0.4, cwc + aa, nt.x));   // the crack a dark groove where it does not glow
		float ff = mix(0.3, 1.0, aof) * mix(pit_cast_min, 1.0, cast) * mix(0.25, 1.0, smoothstep(0.0, pit_lipw.x, u));
		// (den r17 P2) the bowl's floor: dark at the far wall's foot (tf: metres on to the far wall along the view), a little darker
		// toward the far wall overall; nothing round the near rim
		float tf = max(-ob + sqrt(max(ob * ob - dot(of, of) + R0 * R0, 0.0)), 0.0);
		ff = mix(ff, mix(pit_bw.y, 1.0, smoothstep(0.0, pit_bw.z, tf)) * mix(0.82, 1.0, clamp(tf / (1.6 * R0), 0.0, 1.0)), pit_bowl);
		ff *= mix(1.0, mix(pit_near.x, 1.0, smoothstep(0.0, pit_near.y, tb)), pit_v2);   // (den r18 P4) the near lip's overhang shade
		alb *= mix(1.0, pit_deep.z, mid) * ff;
		float pulse = 0.9 + 0.1 * sin(TIME * 1.3 + pf.x * 0.7);
		float rm = smoothstep(0.15, 0.75, 0.7 * pg_vn(pf * 0.3 + sd * 80.0) + 0.3 * pg_vn(pf * 0.85 + 3.3));
		vec3 em = (pit_core_c * nt.y + pit_halo_c * nt.z) * pit_glow * mix(mix(0.15, 0.45, pit_v2), 1.0, rm) * mix(0.4, 1.0, smoothstep(0.95, 0.3, ef)) * pulse;
		// the wall's earth face: strata and streaks, lit at the brink, dark at its foot, a little green off the floor's glow
		vec2 hw = xz + sv * clamp(tau, 0.0, 1.0);
		float zw = dep * clamp(tau, 0.0, 1.0), zr = zw / max(dep, 1e-3), aw = hw.x + 0.6 * hw.y;
		float wn = 0.5 * pg_vn(vec2(aw * 2.2, zw * 8.0) + sd * 50.0) + 0.3 * pg_vn(vec2(aw * 7.0, zw * 2.5) + 7.7) + 0.2 * pg_vn(vec2(aw * 1.1, zw * 30.0) - 3.1);
		vec3 wcol = pit_wall_c * (0.55 + 0.9 * wn) * mix(1.0, 0.28, smoothstep(0.05, 1.0, zr)) * (1.0 + 1.4 * (1.0 - smoothstep(0.0, 0.035, zw)));
		wcol = mix(wcol, pit_wall_c * (0.7 + 0.6 * wn) * mix(1.0, pit_bw.x, smoothstep(0.0, 1.0, zr)) * (1.0 + 0.5 * (1.0 - smoothstep(0.0, 0.03, zw))), pit_bowl);   // (den r17 P2) lit at the brink
		// (den r18 P4) one gradient from the lip down, streaked down the face (no strata: the stepped rings), no brink band
		float ws = 0.6 * pg_vn(vec2(aw * 2.6, zw * 0.9) + sd * 50.0) + 0.4 * pg_vn(vec2(aw * 8.0, zw * 1.6) + 7.7);
		wcol = mix(wcol, pit_wall_c * (0.82 + 0.36 * ws) * mix(pit_wg.x, pit_wg.y, pow(clamp(zr, 0.0, 1.0), pit_wg.z)), pit_v2);
		vec3 wem = pit_halo_c * pit_glow * 0.45 * smoothstep(0.4, 1.0, zr) * mix(0.15, 1.0, rm);
		alb = mix(alb, wcol, wall);
		em = mix(em, wem, wall);
		// root ends over the lip (tapering to a tip inside, lit on their upper side) and crumbs of earth
		float th = atan(off.y, off.x), rootm = 0.0, rooth = 0.0;
		for (int k = 0; k < 7; k++) {
			if (pit_v2 > 0.0) break;   // (den r18 P4, R17 item 5: the black wires) the painted B6 roots lie over the lips
			vec2 hk = pg_h2(sd * 53.0 + float(k) * 7.9);
			if (hk.y < 0.3) continue;
			float tk = 6.2832 * ((float(k) + 0.25 + 0.5 * hk.x) / 7.0 + sd.y);
			float dth = th - tk;
			dth -= 6.2832 * floor((dth + 3.1416) / 6.2832);
			float tip = mix(0.8, 0.93, hk.x), ta = clamp((1.3 - en) / (1.3 - tip), 0.0, 1.0);
			float wr = mix(0.045, 0.008, ta * ta) * mix(0.65, 1.0, hk.y);
			float lat = dth * rr - 0.05 * sin(en * 10.0 + float(k) * 2.1) * (0.4 + hk.x);
			float onr = step(en, 1.3) * step(tip, en) * (1.0 - smoothstep(wr - 0.005, wr + 0.005, abs(lat)));
			rootm = max(rootm, onr);
			rooth = max(rooth, onr * smoothstep(0.1, 0.6, lat * sign(-cos(th) + 1e-3) / max(wr, 1e-3)));
		}
		float crad = mix(0.2, 0.38, kh.x), crumb = step(0.8 + 0.5 * max(en - 1.0, 0.0), kh.y) * step(0.96, en) * step(en, 1.3) * (1.0 - smoothstep(crad - 0.06, crad + 0.04, sqrt(k1)));
		crumb *= 1.0 - pit_bowl;   // (den r17 P2) the square crumbs off (the rim's notches)
		// 2-3 cracks run out past the rim on the floor: a jagged dark groove, tapering, a glowing core fading along it
		float rc = 0.0, rh = 0.0, rg = 0.0, past = (en - 1.0) * R0, am = max(fwidth(rr), 1e-4);
		if (pit_ray.x > 0.0 && rr > 0.01) {
			for (int k = 0; k < 3; k++) {
				vec2 hk = pg_h2(sd * 97.0 + float(k) * 13.7);
				if (k == 2 && hk.x < 0.45) break;
				float tk = 6.2832 * fract(sd.x + float(k) * 0.37 + 0.12 * hk.x);
				float t = past / mix(pit_ray.y, pit_ray.z, hk.y);
				if (t > 1.0 || past < -0.3) continue;
				float ps = max(past, 0.0) / 0.085, pn = floor(ps);
				float j0 = pg_h2(vec2(pn, float(k) * 3.0 + sd.y * 31.0)).x - 0.5, j1 = pg_h2(vec2(pn + 1.0, float(k) * 3.0 + sd.y * 31.0)).x - 0.5;
				float jag = 0.06 * mix(j0, j1, fract(ps)) * smoothstep(0.0, 0.12, past) + 0.12 * (pg_vn(vec2(past * 1.6, float(k) * 5.3 + sd.y * 40.0)) - 0.5);
				float dth = th - tk;
				dth -= 6.2832 * floor((dth + 3.1416) / 6.2832);
				float lat = abs(dth * rr - jag), tp = 1.0 - clamp(t, 0.0, 1.0), wg = mix(0.007, 0.035, tp * tp);
				rg = max(rg, 1.0 - smoothstep(wg - am, wg + am, lat));
				rc = max(rc, (1.0 - smoothstep(0.45 * wg - am, 0.45 * wg + am, lat)) * smoothstep(0.0, 0.4, tp));
				rh = max(rh, exp(-max(lat - 0.45 * wg, 0.0) / (pit_cw.y * mix(0.45, 1.0, tp))) * tp * tp);
			}
		}
		float out_ = 1.0 - inside, ra = clamp(max(rg, 0.35 * rh), 0.0, 1.0) * out_;
		alb = mix(mix(vec3(0.09, 0.064, 0.042), vec3(0.02, 0.015, 0.01), rg), alb, inside);
		alb = mix(alb, vec3(0.055, 0.036, 0.024) * mix(1.0, 2.4, rooth), rootm);
		alb = mix(alb, vec3(0.16, 0.108, 0.068) * mix(0.5, 1.25, smoothstep(-0.15, 0.15, kr.y)) * mix(0.5, 1.0, out_), crumb);
		alb = gloom_col(alb, lair_gloom(wpos));
		ALBEDO = alb * mix(1.0, fg_dark, smoothstep(0.82, 1.0, SCREEN_UV.y)) * mix(1.0, pit_self.x, inside);
		EMISSION = alb * pit_self.y * inside + (em * inside + (pit_core_c * rc + pit_halo_c * rh) * pit_glow * pulse * out_ * 0.85 / max(ra, mix(0.05, 0.3, pit_bowl)) * step(0.001, ra)) * (1.0 - max(rootm, crumb));
		ALPHA = max(inside, max(ra, max(rootm, crumb)));
		pit_pt = 1.0 - inside * pit_bowl;   // (den r17 P2) no spot or omni light inside the bowl (light())
	} else
	if (pit_glow > 0.0 && COLOR.a < 0.75) {
		vec2 q = UV * 13.0;
		float m = smoothstep(0.25, 0.65, pg_edge(q * 0.33 + 5.3) * 1.6);
		float r1 = pg_ridge(q * 0.9), r2 = pg_ridge(q * 2.1 + 4.0);
		// (den r14 objects, item 12) a hairline core, a soft halo, a second finer set of branches on the slow mask
		float v = 1.0 * smoothstep(0.93, 0.99, r1) + 0.5 * pow(r1, 8.0) + (0.75 * smoothstep(0.945, 0.99, r2) + 0.22 * pow(r2, 8.0)) * (0.4 + 0.6 * m);
		float inner = 1.0 - smoothstep(0.55, 1.1, 2.0 * COLOR.b);
		// (den r13 rooms) clusters: veins only where the slow cell mask clears its threshold (about pit_dark of the area stays dark)
		// (den r15 P) the mask feathered wide (no edge) and a pit's interior never wholly dark of veins; the painting's own
		// brightness no longer switches a whole pit off (s23's lit pit had none): the floor of the pit takes the veins by radius
		float pm = smoothstep(0.0, 0.3, pg_edge(q * 0.16 + 11.3) - pit_dark * 0.55);
		inner *= mix(0.35, 1.0, pm);
		float dark = max(1.0 - smoothstep(0.015, 0.09, l), pit_floor * (1.0 - smoothstep(0.35, 0.85, 2.0 * COLOR.b)));
		// thin crack network (2-4 px) over most of the floor and a few running out past the rim
		float r3 = pg_ridge(q * 1.3 + 9.0), r4 = pg_ridge(q * 0.6 + 21.0);
		float net = smoothstep(0.955, 0.985, r3) + smoothstep(0.965, 0.99, r4);
		float pulse = 0.85 + 0.15 * sin(TIME * 1.3 + q.x * 0.2);
		vec3 pc = mix(vec3(dot(pit_col, vec3(0.299, 0.587, 0.114))), pit_col, pit_sat);
		EMISSION += pc * pit_glow * v * inner * dark * pulse;
		EMISSION += pc * pit_glow * pit_halo * inner * dark * (0.3 + m);
		// the net: lit regardless of the painting's brightness, out to the rim and a little past (feathered)
		EMISSION += pc * pit_glow * pit_net * net * (1.0 - smoothstep(0.9, 1.3, 2.0 * COLOR.b)) * pulse;
	}
#endif
#ifndef SET_SOFT
	ALPHA_SCISSOR_THRESHOLD = 0.5;
#endif
	// the ink tag (cel.gdshaderinc's cel_tag): roughness 1, class 2 (no post ink: the painting carries its own)
	ROUGHNESS = 126.0 / 127.0;
}

void light() {
	float w = LIGHT_IS_DIRECTIONAL ? 1.0 : mix(1.0, max(dot(NORMAL, LIGHT), 0.0), local_turn) * pt_take * pit_pt;   // (den r16 D: pt_take; r17 P2: pit_pt)
	vec3 lc = LIGHT_COLOR;
	float ll = dot(lc, vec3(0.299, 0.587, 0.114));
	lc = LIGHT_IS_DIRECTIONAL || lc.r >= lc.g ? lc : vec3(ll) * cold_take;
	float att = LIGHT_IS_DIRECTIONAL ? mix(1.0, ATTENUATION, key_shadow) : ATTENUATION;
	DIFFUSE_LIGHT += lc * att * w / PI;
}
