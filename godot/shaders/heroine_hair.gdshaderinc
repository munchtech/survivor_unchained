// Her hair's shading, for heroine_hair.gdshader (cut to its strands by hashed
// alpha), heroine_hair_coverage.gdshader (cut by a threshold moved every frame:
// COVERAGE), heroine_hair_soft.gdshader (blended: SOFT), and the two blended
// ways tried under FSR 2 (src/Actors/HairDraw.cs): heroine_hair_blend.gdshader
// (blended over a depth prepass of its solid parts: BLEND), and
// heroine_hair_core.gdshader (its solid parts drawn opaque: CORE) under
// heroine_hair_over.gdshader (the whole drawn again over them, blended: OVER);
// and heroine_hair_erase.gdshader drawn last over any of the blended ones, to
// erase FSR 2's reactive mask under them (ERASE).

uniform sampler2D strands : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform vec3 colour : source_color = vec3(0.56, 0.17, 0.07);
uniform float roots = 0.4;
uniform float variation = 0.35;
uniform vec3 shine_colour : source_color = vec3(1.0, 0.93, 0.86);
// (face 38 r2, the judge: one broken band, two lobes along the strand: a primary tinted 40% by the hair, shifted
// toward the root, tight; a secondary albedo-tinted, toward the tip, broad; each lock's shift jittered +-0.05)
uniform float shine = 0.5;                 // (face 38: 0.1, r1 0.25, r3 0.2; r4 the judge: no band showed)
uniform float shine_width = 110.0;        // (face 38 r2: 140, r3 80, r4 50; r5 the judge: a narrow band)
uniform float shine2 = 0.12;               // (face 38 r2: 0.35, r4 0.3; r5 a weak deep-copper secondary)
uniform float shine2_width = 18.0;        // (face 38 r2: 40)
uniform float shift = -0.05;               // (face 38 r2: 0.06)
uniform float shift2 = 0.08;               // (face 38 r2: -0.1)
uniform float shine_tint = 0.55;           // (face 38 r2: the primary's share of the hair's own hue)
// (face 39 dye: a dark dye's primary highlight (black, dark brown) narrower, dimmer and near-neutral: lit by the
// fire's warm key, tinted toward its own warm hue at full strength, a black head showed large copper-orange patches.
// Real black hair has a soft grey-white sheen band. Weighted by the dye's linear luminance, dark_from (all) to
// dark_to (none): copper #7a4824 (0.088) untouched, brown and chestnut (0.06) about a third, black all.)
uniform float dark_from = 0.03;
uniform float dark_to = 0.08;
uniform float dark_shine = 1.0;            // the shine's share left on a black dye (0.5 and 0.8: no sheen left, a flat blue-black)
uniform float dark_narrow = 1.45;          // its width's exponent times this (r8: 1.8, three grey bands, one per layer, on the pixie's side)
// (face 39 r8, the judge: on a black pixie at turn 40 the narrow dark-dye band lit each shell layer apart, three
// evenly spaced grey-blue stripes. For a dark dye only: its shine broken by a strand-clump mask (dark_clump: the
// least it leaves, 3-6 mm clumps across a card, long along it) and each card's shift jittered by +-dark_card_jitter,
// so the layers' bands don't line up)
uniform float dark_clump = 0.35;
uniform float dark_card_jitter = 0.08;
// (r8: the dark-dye hairline's warm brown wash is not her hair: with the cap and fine hairs dyed other colours
// (--hair-set) it stays, and thinning them (fewer band cards, the cap's fade cut to strands) moved it by 0.1 L*)
uniform float dark_neutral = 0.85;         // how far the light's own colour is greyed in it
uniform float lock_jitter = 0.02;          // (face 38 r2: each lock's shift, by its card number)
uniform float strand_jitter = 0.1;         // (face 38 r2: 0.5, strand to strand, which scattered it into grains)
uniform float through = 0.5;
// Highlights (the owner, 22 Oct: "have a black version, just those are highlights"): a second colour on some of
// her locks, in the albedo (so it holds in every light), mostly her front and crown, stronger toward the tips, in
// streaks along the strands; each lock somewhere from the highlight toward a brown between it and her hair.
uniform float highlights = 0.0;            // on (1) or off (0: her dye one colour)
uniform vec3 highlight : source_color = vec3(0.6, 0.29, 0.125);
uniform float hl_locks = 0.4;              // the share of the locks in its panels that take it
uniform float hl_strength = 1.0;           // (face 40: per swatch, looks.json's hairHighlights' strength: honey 1.5)
uniform float hl_back = 0.0;               // its strength outside its panels, of theirs
uniform float hl_strands = 0.85;           // the share of a lock's strands
uniform float hl_root = 0.75;             // its strength at the root, of the tip's
uniform float hl_brown = 0.5;              // the share of its locks a tan/mid-brown, not the highlight itself
uniform vec3 hl_tan : source_color = vec3(0.54, 0.42, 0.31);   // (that brown's hue; drawn at 0.8 of the highlight's lightness)
uniform vec2 hl_lock_w = vec2(0.35, 1.0);  // (face 40: each lock's strength, from, to)
uniform float hl_dip = 0.7;                // (face 40: how deep the 1-2 dips along a lock's length go: long bands broken)
// (face 40, the judge: in 2-3 soft panels, as the reference lays them, not every other lock: a crown/front panel and
// a temple panel. Each: centre xyz and its radius (metres from her head joint at rest; +z her front, +y up).)
uniform vec4 hl_panel_a = vec4(0.03, 0.2, 0.03, 0.09);      // crown/front (a little to her left)
uniform vec4 hl_panel_b = vec4(-0.08, 0.13, 0.05, 0.08);    // temple (her right)
uniform vec4 hl_panel_c = vec4(0.0, 0.0, 0.0, 0.0);         // (a third, radius 0: none)
// (face 40 r2, the lead: the temple panel bold, a clear patch, as the reference's; the crown subtler: each panel's
// share of the locks (of hl_locks) and gain on its strength)
uniform vec3 hl_share = vec3(1.0, 2.6, 1.0);     // (panels a, b, c)
uniform vec3 hl_gain = vec3(1.1, 3.2, 1.1);
// (face 40 r2: the ash a near-neutral highlight is pushed to, against her warm lights: at the Look's night an ash albedo
// read salmon, #c89680, hue 18)
uniform vec3 hl_ash = vec3(0.55, 0.85, 1.25);
uniform float hl_show = 0.0;             // (a developer's switch, --hair-set hair:hl_show=1: the panels in red, green and blue)
uniform mat3 head_turn = mat3(1.0);        // her head's turn from its rest (HairSway)
// (face 37: the strands' read. fibre_lo/fibre_hi: a strand's shade range in the atlas (was fixed 0.15/0.85);
// lock_share: how much each card's own tone (its vertex green) moves it (was fixed 0.04); wrap: the light
// wrapped round the hair (was fixed 0.45))
uniform float fibre_lo = 0.3;              // (face 38: 0.15, r1 0.08; r2 the judge: grey locks)
uniform float fibre_hi = 0.8;              // (face 38: 0.85, r1 0.92)
uniform float lock_share = 0.04;
uniform float rope_floor = 0.55;          // (face 38 r3: the braid strands' diamond gap floor)
uniform float wrap = 0.25;                 // (face 38: 0.45)
// (a pale near-neutral dye (platinum) held pale and neutral in warm light: ash cools its tone toward ash_tone,
// lift raises it toward its swatch; both fade out with the dye's saturation and darkness: face 34)
uniform float ash = 1.0;
uniform vec3 ash_tone = vec3(0.72, 1.0, 1.0);
uniform float lift = 0.55;
// (20 October, face 32 r2b: the pixie only, People.HerHair. A card is a lock
// of fibres, lit alike from either side; drawn two-sided, Godot turned its
// normal in on its underside, so where a lifted card's underside showed, at
// her crown's outline turned 40 degrees, it took no light: a row of dark
// beads along it. With fibre_back its underside keeps its outward normal.)
// (face 38 r2: on for every style: the braid's lifted cards drew the same dark outline at the Look)
uniform bool fibre_back = true;
// Her scalp under the hair (its cap): fine strands lying the way her hair is
// combed, dark (under the hair), thinning out at her hairline (its vertex
// alpha) to bare skin. A braid's strands are drawn so too.
uniform bool cap = false;
// A leather tie in her hair: dark, no strands.
uniform bool tie = false;
// Her hair's swing (src/Actors/HairSway.cs): how far a mass hung below her
// head has been left behind, and where her head is (both in the mesh's own
// space). Each point is moved by it the more the further it hangs below her
// head and the nearer its tip; and a breath of air through it, always.
uniform vec3 sway = vec3(0.0);
uniform vec3 head = vec3(0.0, 1.6, 0.0);
// A style that hangs on a chain (its second UV: the place along it and how
// much it moves with it): how far each of the chain's points has swung
// from where it hangs at rest, in the mesh's own space.
uniform vec3 chain[8];
// The three as they were last frame, for the motion vectors (motion.gdshaderinc):
// so the temporal smoothing follows the swing, not only her head.
uniform vec3 sway_then = vec3(0.0);
uniform vec3 head_then = vec3(0.0, 1.6, 0.0);
uniform vec3 chain_then[8];
// The chain at rest (where it hangs, carried by its bone) and how far each of its points has turned (a quaternion),
// and last frame's: her hair is turned with it about it, not only moved (moved only, a braid swung sideways went
// edge-on flat, and cards burst where it bent). None set: no turn.
uniform vec3 chain_rest[8];
uniform vec3 chain_rest_then[8];
uniform vec4 chain_turn[8];
uniform vec4 chain_turn_then[8];
// Her forearms (elbow, past the fist; left then right, in the mesh's own space) and their radius: her hair is
// pushed out of them (a lock by her ear as her throwing arm comes past her head). 0: none.
uniform vec3 arms[4];
uniform vec3 arms_then[4];
uniform float arm_r = 0.0;

#include "res://shaders/motion.gdshaderinc"
#ifdef COVERAGE
#include "res://shaders/coverage.gdshaderinc"
#endif
#ifdef CORE
// (the share of a pixel a strand must cover to be drawn solid, its depth and
// motion written: near 1, so the blended pass over it shows no edge)
uniform float core_cut = 0.9;
#ifdef CORE_A2C
// (under MSAA, at the Look: its own cut, near 1, so the core's samples and the blended
// pass over them don't both cover the edge, which drew it darker and wider)
uniform float a2c_cut = 0.9;
#endif
#endif
#ifdef ERASE
// (how much of the blended alpha under it is kept: heroine_hair_erase.gdshader;
// erased fully only where the strands cover at least erase_from: with "two", the core's
// cut, so only what wrote her hair's own motion is accumulated, and the thin
// fringe stays reactive)
uniform float keep = 0.0;
uniform float erase_from = 0.0;
#endif
// (a bias on the strands' mip level: 0.5 cancels the smoothing's -0.5 on strands
// thinner than a pixel; --hair-bias, HairDraw)
uniform float strand_bias = 0.0;

varying vec3 strand;
varying float sparkle;
varying float fibre;
varying float lock_n;
varying vec3 hl_at;
varying float hl_ashen;                    // (face 40 r2: how much of it an ash highlight: its secondary shine untinted)

float hl_hash(vec3 p) { return fract(sin(dot(p, vec3(127.1, 311.7, 74.7))) * 43758.5453); }
float hl_noise(vec3 p) {
	vec3 i = floor(p), f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(mix(hl_hash(i), hl_hash(i + vec3(1, 0, 0)), f.x), mix(hl_hash(i + vec3(0, 1, 0)), hl_hash(i + vec3(1, 1, 0)), f.x), f.y),
		mix(mix(hl_hash(i + vec3(0, 0, 1)), hl_hash(i + vec3(1, 0, 1)), f.x), mix(hl_hash(i + vec3(0, 1, 1)), hl_hash(i + vec3(1, 1, 1)), f.x), f.y), f.z);
}

vec3 turned(vec4 q, vec3 v) {
	return v + 2.0 * cross(q.xyz, cross(q.xyz, v) + q.w * v);
}

void vertex() {
	bool past = last_frame(TIME);
	float hang = clamp(((past ? head_then.y : head.y) - VERTEX.y) / 0.35, 0.0, 1.0);
	float tip = (cap || tie) ? 1.0 : smoothstep(0.0, 1.0, UV.y);
	float moves = (cap && COLOR.b < 0.5) ? 0.0 : 1.0;           // (not the cap on her scalp; a braid's strands, yes)
	hl_at = transpose(head_turn) * (VERTEX - (past ? head_then : head));   // (where it lies on her head at rest)
	vec3 air = vec3(sin(TIME * 1.1 + VERTEX.y * 5.0), 0.0, cos(TIME * 0.9 + VERTEX.x * 7.0)) * 0.0025;
	if (UV2.y > 0.0) {
		float s = clamp(UV2.x, 0.0, 1.0) * 7.0;
		int i = min(int(floor(s)), 6);
		float f = s - float(i);
		vec3 a = past ? chain_then[i] : chain[i];
		vec3 b = past ? chain_then[i + 1] : chain[i + 1];
		vec3 o = VERTEX - mix(past ? chain_rest_then[i] : chain_rest[i], past ? chain_rest_then[i + 1] : chain_rest[i + 1], f);
		vec4 q0 = past ? chain_turn_then[i] : chain_turn[i];
		vec4 q1 = past ? chain_turn_then[i + 1] : chain_turn[i + 1];
		vec4 q = mix(q0, dot(q0, q1) < 0.0 ? -q1 : q1, f);
		float ql = length(q);
		q = ql > 1e-6 ? q / ql : vec4(0.0, 0.0, 0.0, 1.0);
		VERTEX += (mix(a, b, f) + turned(q, o) - o + air * UV2.x) * UV2.y;
		NORMAL = normalize(mix(NORMAL, turned(q, NORMAL), UV2.y));
		TANGENT = normalize(mix(TANGENT, turned(q, TANGENT), UV2.y));
		BINORMAL = normalize(mix(BINORMAL, turned(q, BINORMAL), UV2.y));
	} else {
		VERTEX += ((past ? sway_then : sway) + air) * hang * hang * tip * moves;
	}
	if (arm_r > 0.0 && moves > 0.0) {
		for (int k = 0; k < 2; k++) {
			vec3 a = past ? arms_then[2 * k] : arms[2 * k];
			vec3 ab = (past ? arms_then[2 * k + 1] : arms[2 * k + 1]) - a;
			vec3 c = a + ab * clamp(dot(VERTEX - a, ab) / max(dot(ab, ab), 1e-6), 0.0, 1.0);
			vec3 o = VERTEX - c;
			float d = length(o);
			if (d < arm_r && d > 1e-5) VERTEX = c + o * (arm_r / d);
		}
	}
}

void fragment() {
	if (fibre_back && !FRONT_FACING) NORMAL = -NORMAL;
	vec4 t = texture(strands, UV, strand_bias);
	// (its shade kept from going too dark or too light, strand to strand)
	t.r = mix(fibre_lo, fibre_hi, t.r);
	// Strand by strand (the atlas's green) and lock by lock (the card's green),
	// from a deeper auburn to a lighter copper.
	// (the deeper tone's warm shift in step with the dye's own saturation: copper deepens to auburn, but a
	// near-neutral dye keeps its own hue as it darkens; at full shift platinum's deep strands went pink, Oklab
	// hue 25 against its swatch's 85, and the whole head read peach, strawberry blonde: face 34)
	// (face 39 r1: a graded matte mark, 0.45 to 0.5 none to full, full to 0.55; full from 0.495, as 0.5 may come in at 127/255)
	float matte = (!cap && !tie) ? clamp((COLOR.b - 0.45) / 0.045, 0.0, 1.0) * step(COLOR.b, 0.55) : 0.0;
	// Highlights: a lock (its card's number) taken or not, by where it lies (front and crown), streaked strand by strand
	// (the atlas's green), stronger toward its tip; not the cap, the tie or the matte-marked hairs.
	float hl_h = fract(COLOR.g * 91.7 + 0.37);
	float hl_pa = hl_panel_a.w > 0.0 ? 1.0 - smoothstep(0.55, 1.0, length(hl_at - hl_panel_a.xyz) / hl_panel_a.w) : 0.0;
	float hl_pb = hl_panel_b.w > 0.0 ? 1.0 - smoothstep(0.55, 1.0, length(hl_at - hl_panel_b.xyz) / hl_panel_b.w) : 0.0;
	float hl_pc = hl_panel_c.w > 0.0 ? 1.0 - smoothstep(0.55, 1.0, length(hl_at - hl_panel_c.xyz) / hl_panel_c.w) : 0.0;
	float hl_p = max(hl_pa, max(hl_pb, hl_pc));
	// (a lock taken or not by its own number; a taken lock as strong as its own share, and broken by one or two dips
	// along its length)
	vec3 hl_pw = vec3(hl_pa, hl_pb, hl_pc) / max(hl_pa + hl_pb + hl_pc, 1e-3);
	float hl_take = smoothstep(-0.03, 0.03, hl_locks * dot(hl_pw, hl_share) - fract(hl_h * 17.3 + 0.11));
	float hl_d1 = 0.25 + 0.5 * fract(hl_h * 5.9), hl_d2 = 0.15 + 0.7 * fract(hl_h * 11.3);
	float hl_dips = (1.0 - hl_dip * exp(-pow((UV.y - hl_d1) / 0.07, 2.0)))
		* (1.0 - hl_dip * step(0.5, fract(hl_h * 3.1)) * exp(-pow((UV.y - hl_d2) / 0.05, 2.0)));
	float hl_w = highlights * ((cap || tie) ? 0.0 : 1.0) * (1.0 - matte) * hl_take * max(hl_p, hl_back)
		* mix(hl_lock_w.x, hl_lock_w.y, sqrt(fract(hl_h * 13.1))) * hl_dips
		* smoothstep(0.42, 0.58, fract(t.g + hl_h * 3.7) + hl_strands - 0.5)
		* mix(hl_root, 1.0, smoothstep(0.0, 0.7, UV.y));
	hl_w = min(hl_w * hl_strength * dot(hl_pw, hl_gain), 1.0);
	const vec3 hl_lum = vec3(0.2126, 0.7152, 0.0722);
	vec3 hl_t = hl_tan * (0.8 * dot(highlight, hl_lum) / max(dot(hl_tan, hl_lum), 1e-4));
	// (a near-neutral highlight's (platinum's, ash's) brown its own grey: a warm one read pink on blonde)
	float hl_s = (max(highlight.r, max(highlight.g, highlight.b)) - min(highlight.r, min(highlight.g, highlight.b))) / max(max(highlight.r, max(highlight.g, highlight.b)), 1e-3);
	hl_t = mix(vec3(dot(hl_t, hl_lum)), hl_t, smoothstep(0.1, 0.35, hl_s));
	vec3 hl_c = step(hl_brown, fract(hl_h * 7.3)) > 0.5 ? highlight : hl_t;
	vec3 dye = hl_show > 0.5 ? vec3(hl_pa, hl_pb, hl_pc) : mix(colour, hl_c, hl_w);
	float dye_sat = (max(dye.r, max(dye.g, dye.b)) - min(dye.r, min(dye.g, dye.b))) / max(max(dye.r, max(dye.g, dye.b)), 0.001);
	vec3 dark = dye * mix(vec3(0.53), vec3(0.62, 0.5, 0.45), smoothstep(0.2, 0.5, dye_sat));
	vec3 light = min(dye * vec3(1.4, 1.5, 1.55), vec3(1.0));
	// (the card's own share small: at 0.12 each card took a flat tone of its own, a block on her crown)
	vec3 tint = mix(dye, mix(dark, light, clamp(t.g * (1.0 - lock_share) + COLOR.g * lock_share, 0.0, 1.0)), variation);
	// (gray as well as platinum went mauve by the fire, hue 32: the ash reaches the light grays, the lift only the palest)
	float dye_neutral = 1.0 - smoothstep(0.2, 0.5, dye_sat), dye_lum = dot(dye, vec3(0.2126, 0.7152, 0.0722));
	tint = min(tint * (1.0 + lift * dye_neutral * smoothstep(0.3, 0.6, dye_lum)), vec3(1.0));
	float ash_w = ash * dye_neutral * smoothstep(0.1, 0.35, dye_lum);
	// (face 40 r2: a near-neutral highlight (platinum, ash) kept ash on a warm hair: mixed over a blonde, its streaks read pink)
	hl_ashen = hl_w * (1.0 - smoothstep(0.06, 0.2, hl_s));
	tint = mix(tint, vec3(dot(tint, vec3(0.2126, 0.7152, 0.0722))) * hl_ash, hl_ashen);
	float depth = COLOR.r;                                        // 1 outermost, darker within
	strand = normalize(BINORMAL);                                 // along its V: root to tip
	sparkle = t.g;
	lock_n = COLOR.g;
	fibre = t.r * (cap ? 0.35 : 1.0);                            // (the cap's under the hair: little highlight)
	// (face 38 r5: blue 0.45-0.55 on a strand card is the matte mark (braid sideburns, baby hairs, edge wisps): base colour, no shine)
	fibre *= 1.0 - matte;
	float dk_f = 1.0 - smoothstep(dark_from, dark_to, dot(colour, vec3(0.2126, 0.7152, 0.0722)));
	if (dk_f > 0.0 && !cap && !tie) {
		float cl = hl_noise(vec3(UV.x * 30.0 + COLOR.g * 17.0, UV.y * 4.0, COLOR.g * 37.0));
		fibre *= mix(1.0, sqrt(mix(dark_clump, 1.0, smoothstep(0.25, 0.75, cl))), dk_f);
	}
	float cover = 1.0;
	if (tie) {
		ALBEDO = vec3(0.055, 0.035, 0.024);
		fibre = 0.6;
	} else if (cap) {
		// (at her hairline, where its strands are seen, as bright as hair; dark under the cards)
		float fade = COLOR.a;
		// (a rope of hair, a braid's strand (its blue), as bright as hair, deep in it darker)
		// (face 38 r3: blue under 0.5 on the cap is the braid's forehead contact shade, not a rope)
		float rope = step(0.5, COLOR.b);
		float contact = COLOR.b < 0.5 ? COLOR.b : 0.0;
		float tr = mix(t.r, max(t.r, rope_floor), rope);          // (face 38 r3: the braid's diamond gaps no darker than this)
		// (at her hairline as light as her hair, not a darker band over it;
		// and its strands ending each at its own height, by its number (the
		// atlas's green), a ragged line, not a smooth fade along an arc)
		// (darker only well under the cards (fade 0.85 to 1): from 0.4 it drew a dark band just over her
		// hairline, where the cards do not yet cover; and thinned strand by strand over most of its fade, its
		// cover about 0.3 to 0.9 over 7 to 10 mm, not all in its first 3)
		ALBEDO = tint * tr * mix(1.0, 0.75, smoothstep(0.85, 1.0, fade) * (1.0 - rope)) * mix(1.0, mix(0.78, 1.0, depth), rope);   // (face 38 r2: 0.55, a dark net round the braid's diamonds)
		cover = max(fade * fade, t.a * smoothstep(0.0, 0.8, fade + (t.g - 0.5) * 0.35));
		if (contact > 0.001) {                                    // (a dark hair-tinted shade on her skin, not strands)
			ALBEDO = mix(ALBEDO, tint * 0.4, 1.0 - smoothstep(0.0, 0.3, fade));
			cover = max(cover, contact);
		}
	} else {
		float along = UV.y;                                       // 0 at the root, 1 at the tip
		// (layer by layer only a little darker within, and a root dark only
		// where it lies deep: an outer card's root, begun mid-crown, drew a dark
		// band, and an outer card at 1.8 times an inner one's light a block)
		ALBEDO = tint * t.r * mix(1.0 - roots * (1.0 - depth), 1.0, smoothstep(0.0, 0.1, along)) * mix(0.75, 1.0, depth);
		// (the baby hairs at her hairline (their blue): a lighter copper, sunlit fine hair, not grey strokes)
		ALBEDO = mix(ALBEDO, light * mix(0.8, 1.0, t.r), COLOR.b * 0.35 * (1.0 - step(0.45, COLOR.b) * step(COLOR.b, 0.55)));   // (face 38 r2: 0.7, a pale wisp)
		// (its root's blunt end softened; the baby hairs at her hairline faint: its vertex alpha)
		cover = t.a * smoothstep(0.0, 0.012, along) * COLOR.a;
	}
	// (the ash on the lighter strands only: on the dark ones, deep in the hair and lit by the sky, it turned them
	// blue-grey, 0.5% to 6.9% of her crown's pixels bluish: judge j1, face 34)
	ALBEDO *= mix(vec3(1.0), ash_tone, ash_w * smoothstep(0.08, 0.35, dot(ALBEDO, vec3(0.2126, 0.7152, 0.0722)) / max(dye_lum, 0.001)));
#if defined(SOFT) || defined(OVER)
	ALPHA = cover;
#elif defined(BLEND)
	// (its shadow cut at half cover: as much shadow as hashed alpha cast on
	// average, and still; Godot's prepass would cast all over a tenth)
	ALPHA = IN_SHADOW_PASS ? step(0.5, cover) : cover;
#elif defined(CORE)
	ALPHA = cover;
#ifdef CORE_A2C
	// (under MSAA, the cut's edge spread over the samples over a pixel round
	// a2c_cut: alpha to coverage, heroine_hair_core_a2c.gdshader; cut first a
	// quarter below it, as Godot cuts before it spreads. The texture coordinate
	// is the plain UV, whose tiny derivatives turn off Godot's boost of the
	// alpha by a quarter per mip level, which widened the cut)
	float cut0 = max(a2c_cut - 0.25, 0.05);
	ALPHA_SCISSOR_THRESHOLD = IN_SHADOW_PASS ? 0.5 : cut0;
	ALPHA_ANTIALIASING_EDGE = IN_SHADOW_PASS ? 0.0 : a2c_cut - cut0;
	ALPHA_TEXTURE_COORDINATE = UV;
#else
	ALPHA_SCISSOR_THRESHOLD = IN_SHADOW_PASS ? 0.5 : core_cut;
#endif
#elif defined(ERASE)
	// (white, multiplied: the colour kept; the alpha, FSR 2's reactive mask, scaled by keep
	// where the strands cover erase_from or more, eased out over the 0.25 below it)
	ALBEDO = vec3(1.0);
	ALPHA = erase_from > 0.0 ? mix(1.0, keep, smoothstep(erase_from - 0.25, erase_from, cover)) : keep;
#elif defined(COVERAGE)
	// (cut by a threshold moved every frame: coverage.gdshaderinc)
	if (cover < coverage_cut(FRAGCOORD.xy)) discard;
#else
	ALPHA = cover;
	ALPHA_HASH_SCALE = 1.0;
#endif
	ROUGHNESS = 0.7;
	SPECULAR = 0.15;
	AO = mix(0.75, 1.0, depth);
}

float along_strand(vec3 t, vec3 h, float width) {
	float th = dot(t, h);
	return smoothstep(-1.0, 0.0, th) * pow(sqrt(max(1.0 - th * th, 0.0)), width);
}

void light() {
	vec3 lc = LIGHT_COLOR * ATTENUATION / PI;
	float nl = dot(NORMAL, LIGHT);
	DIFFUSE_LIGHT += lc * clamp((nl + wrap) / (1.0 + wrap), 0.0, 1.0);
	DIFFUSE_LIGHT += lc * through * pow(clamp(dot(-LIGHT, VIEW), 0.0, 1.0), 3.0);
	vec3 h = normalize(LIGHT + VIEW);
	// (each strand's highlight a little up or down it from the next's: the
	// highlight broken into strands, not one smooth band)
	float jitter = (sparkle - 0.5) * strand_jitter + (lock_n - 0.5) * 2.0 * lock_jitter;
	float dk = 1.0 - smoothstep(dark_from, dark_to, dot(colour, vec3(0.2126, 0.7152, 0.0722)));
	jitter += dk * (fract(lock_n * 7.31 + 0.21) - 0.5) * 2.0 * dark_card_jitter;
	float s1 = along_strand(normalize(strand + NORMAL * (shift + jitter)), h, shine_width * mix(1.0, dark_narrow, dk));
	float s2 = along_strand(normalize(strand + NORMAL * (shift2 + jitter)), h, shine2_width);
	float seen = clamp(nl * 0.6 + 0.4, 0.0, 1.0);
	vec3 lc1 = mix(lc, vec3(dot(lc, vec3(0.2126, 0.7152, 0.0722))), dark_neutral * dk);
	SPECULAR_LIGHT += seen * fibre * fibre * (lc1 * shine_colour * mix(vec3(1.0), ALBEDO / max(max(ALBEDO.r, max(ALBEDO.g, ALBEDO.b)), 0.001), shine_tint * (1.0 - dk)) * shine * mix(1.0, dark_shine, dk) * s1 + lc * ALBEDO * mix(vec3(1.0, 0.55, 0.35), vec3(0.9, 0.95, 1.0), hl_ashen) * shine2 * s2 * (0.4 + 1.2 * sparkle));   // (r5: deep copper)
}
