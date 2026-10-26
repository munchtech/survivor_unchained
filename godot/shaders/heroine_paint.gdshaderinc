// The body of heroine_paint.gdshader and heroine_paint_mul.gdshader (face 40 r2).
uniform sampler2D paint : source_color, filter_linear_mipmap_anisotropic;
uniform float rough = 0.7;
uniform float metal = 0.0;
uniform float strength = 1.0;
// Her brows (paint/brows.png, Own's, and brows_ID.png, each other face's: their shape, in its alpha): each hair found in
// her skin's own paint at its full size (darker than the skin round it, and
// redder: they are painted copper) and drawn in its new colour's hue
// (People.HerPaint: a shade darker than her hair, as brows are), the skin
// between them left be. Each hair keeps its own darkness against the skin as
// painted, eased `soften` of the way to the skin: drawn in the dye's own
// darkness, her brows read twice as dark and dense as her portrait's
// (beside it at 1:1 a painted-on tell); as painted, a tenth too dark.
uniform bool dyed = false;
uniform vec3 dye : source_color = vec3(0.35, 0.2, 0.1);
uniform sampler2D skin_paint : source_color, filter_linear_mipmap_anisotropic;
// Her skin's tone (the skin shader's `tone`), so a hair stands to the skin
// round it as painted; how far each hair is eased toward that skin; how much
// of the dye's colour it takes (the rest its own grey).
uniform vec3 skin_tone : source_color = vec3(1.0);
uniform float soften = 0.07;
uniform float dye_sat = 0.85;  // (People.HerBrows: 0.7 since face 32, red hair's brows read crimson)
// (face 32, 21 October: how far each hair's lightness moves from its paint's to the dye's, scaled by how dark the
// hair is against the skin (the brow's core: the dye's own lightness, the skin between hairs: the skin's), so a
// blonde's brows are a darker blonde and a black-haired woman's near black, every hair kept; 0: as painted, only
// the hue moved (Own's brows before). The brow's core darkness against the skin is in the mask's red
// (tools/assets/heroine_browdye.py: per face, Fey's faint brows 0.11, Own's 0.46).)
uniform float dye_light = 1.0;
uniform float dye_gamma = 0.5;
// (the dye's lightness held to this share of her skin's at most, so a platinum blonde's brows on deep skin are a
// darker blonde, never a pale patch)
uniform float dye_room = 0.75;
// (how much a hair as grey as can be counts, against a dark one: 1 the same)
uniform float grey_hair = 0.8;
// (face 33: how much darker than the dye the darkest hairs go, past the brow's core)
uniform float dye_deep = 0.5;
// (face 33: the darkest a dye is drawn (linear luma), and how far a floored one is warmed)
uniform float dye_floor = 0.028;
uniform float dye_floor_warm = 0.45;
// (face 33: the least of its colour a dye held darker for her skin takes; over 1, more than its own)
uniform float dye_sat_held = 1.6;
// (face 33: the skin lightness (linear) a dye starts turning warmer on, and where it is wholly turned; how far)
uniform vec2 dye_deep_skin = vec2(0.35, 0.15);
uniform float dye_deep_warm = 0.8;
// (face 33 round 3: the warm a chromatic dye held darker for her skin turns toward (linear; Oklab hue 42: the old
// `warm`, hue 60, read olive under the night grade on deep skin), and how much darker a fair dye goes on deep skin
// (a blonde's brows on Sunborn read as a mustard tint at the skin's own lightness, not as hair))
uniform vec3 dye_held_warm = vec3(0.26, 0.075, 0.035);
uniform float dye_deep_dark = 0.8;
uniform vec2 dye_dark_skin = vec2(0.35, 0.15);
// (face 33 round 4: a fair (blonde) dye on tan and deeper skin: how much of its held colour it keeps, and how
// much of the deep-skin warm shift it takes (whole, it read brassy amber, near ginger, under butter-blonde hair))
uniform float dye_fair_sat = 0.85;
// (round 4: the honey brown a blonde dye turns on tan and deeper skin (linear, Oklab hue 55: about 48 on screen; beside her orange skin 61 and over read olive))
uniform vec3 dye_honey = vec3(0.24, 0.1, 0.04);
uniform float dye_fair_warm = 0.0;
// (j3: skin lightness (linear, times tone) from which a fair dye takes the platinum's ash-brown, not honey: Sunborn deep 0.056, tan 0.24)
uniform vec2 dye_ash_skin = vec2(0.14, 0.08);
// (face 39: how dark against the skin a texel must be to show as hair, from none to whole: the faint texels between
// her brow's strokes, shown, filled them into one felt block)
uniform float hair_lo = 0.08;
// (face 40 r2: on deep skin (heroine_paint_mul.gdshader) the hue her brows take her skin toward (People.HerPaint, per hair:
// a dark warm brown, a near-neutral for black, a paler ash-brown for a blonde))
uniform vec3 deep_tint = vec3(0.3, 0.2, 0.14);
uniform float hair_hi = 0.6;
// (face 40 b3, the judge: at night the darkest strokes went navy and blue-violet (#010002, hue 266): toward a tint of its
// own the multiply made her lit skin there the night's light times that tint, a near-neutral dark the grade's toe takes
// blue. Now one darken (that factor's luminance) times a fixed warm tint, so the stroke keeps the hue of her own lit
// skin under it, warmed (mul_scalar 1; 0 the per-channel factor as r2, held to mul_warm's order if mul_order is 1))
uniform vec3 mul_warm = vec3(1.0, 0.88, 0.78);
uniform float mul_scalar = 1.0;
uniform float mul_order = 0.0;
// (and each brow's own share of the darkening, over 1 lighter: her paint's two brows are not alike, and under the
// darken one sat at 0.38 of the skin beside it, the other at 0.49 (black, Look lk0, screen value). Her head's UV has
// them side by side across UV.x mul_split: mul_side_a under it (her right brow, screen-right at the Look), mul_side_b
// over; 1.15 and 1.55 bring both to about 0.53)
uniform float mul_side_a = 1.15;
uniform float mul_side_b = 1.55;
uniform float mul_split = 0.512;
// (face 41, judge j2: one darken times one warm tint gave every hair one faint red-brown, black's auburn. Now each hair
// its own brow: a target colour per hair (People.HerPaint's BrowTarget: hue 0-1, saturation, and value as a share of
// the skin's own sRGB value round it), and the multiply is that target over her painted skin's albedo per channel,
// at most 1 (a darken only; the target's own hue keeps B <= G <= R), so a stroke's core is the target whatever the
// skin's cast. Ordered as the multiply itself (never bluer than her skin) every target took her skin's red, black's auburn)
uniform float target_mode = 0.0;
uniform vec3 brow_target = vec3(0.06, 0.32, 0.375);
// (the least a target's channel may be, sRGB: under it the night grade's toe took a near-black stroke to navy)
uniform float target_floor = 0.04;
// (how far a channel may rise past her skin's: her deep skin has so little blue that, held to 1, a black hair's target
// kept the skin's red at S 0.7; the target's value under the skin's keeps it a darken)
uniform float target_cap = 3.0;
uniform float target_border = 1.0;
// (each brow's value over the target's, as mul_side_a/b: her shadowed brow under the night's fill read darker and violet)
uniform vec3 target_side = vec3(1.15, 1.0, 0.0);

vec3 hsv_rgb(vec3 c) {
	vec3 q = clamp(abs(mod(c.x * 6.0 + vec3(0.0, 4.0, 2.0), 6.0) - 3.0) - 1.0, 0.0, 1.0);
	return c.z * mix(vec3(1.0), q, c.y);
}
vec3 lin_srgb(vec3 c) { return mix(c * 12.92, 1.055 * pow(max(c, vec3(0.0)), vec3(1.0 / 2.4)) - 0.055, step(vec3(0.0031308), c)); }
vec3 srgb_lin(vec3 c) { return mix(c / 12.92, pow((max(c, vec3(0.0)) + 0.055) / 1.055, vec3(2.4)), step(vec3(0.04045), c)); }

void vertex() {
	// (a tenth of a millimetre out, so it never fights the skin under it)
	VERTEX += NORMAL * 0.0001;
}

void fragment() {
	vec4 p = texture(paint, UV);
	if (dyed) {
		vec3 here = texture(skin_paint, UV).rgb;
		// (her skin round it, its hairs left out: the mask's green, tools/assets/heroine_browdye.py; the brightest
		// of a ring of samples a brow's breadth out caught her lid's and eye's highlights where a face's brows hug
		// the lid, and counted the skin between hairs as hair)
		const vec3 lum = vec3(0.3, 0.59, 0.11);
		float skin = max(p.g, 0.02);
		// (how much darker than that skin, as a share of the brow's core darkness there: 1 a whole hair)
		float core = max(p.r, 0.05);
		float raw = (skin - dot(here, lum)) / max(skin * core, 1e-3);
		// (or how much greyer than the skin round it: Highborn's, Fey's and Moonlit's portraits paint many of
		// their brows' hairs ash-grey at the skin's own lightness, which no darkness finds)
		vec3 near_skin = textureLod(skin_paint, UV, 5.0).rgb;
		float s_here = (max(here.r, max(here.g, here.b)) - min(here.r, min(here.g, here.b))) / max(max(here.r, max(here.g, here.b)), 1e-3);
		float s_skin = (max(near_skin.r, max(near_skin.g, near_skin.b)) - min(near_skin.r, min(near_skin.g, near_skin.b))) / max(max(near_skin.r, max(near_skin.g, near_skin.b)), 1e-3);
		raw = max(raw, clamp(1.0 - s_here / max(s_skin, 1e-3), 0.0, 1.0) * grey_hair);
		float hair = clamp(raw, 0.0, 1.0);
		// (each hair's own light and dark kept from the painting, so the brow keeps its strokes: each texel is her
		// skin's colour and the dye's mixed as dark as its hair is (`dye_gamma` under 1: a half-dark hair counts
		// for more, so sparse painted strokes read as a brow, not a grey haze), past the dye where it is darker
		// than the brow's core; the skin's colour is her paint's round it (a coarse mip) at the skin's lightness, so a
		// faint texel stays skin, not a rim of the dye's hue, and a grey stroke takes no grey)
		float tl = dot(skin_tone, lum);
		float sk = skin * tl;
		float hl = max(dot(here, lum), 1e-3);
		vec3 skin_col = near_skin * skin_tone * (skin / max(dot(near_skin, lum), 1e-3));
		// (face 33: a near-black dye floored at `dye_floor`'s lightness, warmed: at its own near-zero light every
		// game grade's blue toe took her brows to a blue-black; a dark warm brown reads near black after it)
		float dl0 = max(dot(dye, lum), 1e-4);
		// (face 33: deep skin: its floor lower, so a black-haired woman's brows on it stay near black, not brown)
		float deep_skin = smoothstep(dye_deep_skin.x, dye_deep_skin.y, sk);
		float floor_l = dye_floor * mix(1.0, 0.7, deep_skin);
		const vec3 warm = vec3(0.195, 0.088, 0.034);
		vec3 dye_n = mix(dye / dl0, warm / dot(warm, lum), dye_floor_warm * clamp(1.0 - dl0 / floor_l, 0.0, 1.0));
		vec3 dyev = dye_n * max(dl0, floor_l);
		float fair = smoothstep(dye_dark_skin.x, dye_dark_skin.y, sk) * smoothstep(0.07, 0.11, dl0);
		dyev *= mix(1.0, dye_deep_dark, fair);
		float dl = max(dot(dyev, lum), 1e-3);
		// (round 4: a fair dye on tan and deeper skin a honey brown, a pale grey's most of the way: a grey-brown, not tan
		// nor mauve)
		float dmx = max(dyev.r, max(dyev.g, dyev.b));
		float s_dye = smoothstep(0.5, 0.75, (dmx - min(dyev.r, min(dyev.g, dyev.b))) / max(dmx, 1e-4));
		vec3 honey_n = dye_honey / dot(dye_honey, lum);
		// (j3: on deep skin a blonde's brows the platinum's neutral dark ash-brown: a honey darker than red-brown skin
		// read olive-khaki beside it; honey stays for tan skin)
		float deeper = smoothstep(dye_ash_skin.x, dye_ash_skin.y, sk);
		dyev = mix(dyev, mix(mix(vec3(1.0), honey_n, 0.75), honey_n, s_dye * (1.0 - deeper)) * dl, fair);
		// (held darker than her skin, a fair dye is warmed as it is darkened: a blonde's brows on deep skin a golden
		// brown; the dye's yellow only darkened read olive-grey)
		float room = min(1.0, sk * dye_room / dl);
		// (face 33: on deep skin a fair dye turns a warmer, oranger brown at its own lightness: a blonde's brows on
		// Sunborn's skin read khaki beside it, a golden brown there; a red's, already warmer, kept)
		const vec3 deep_warm = vec3(0.254, 0.08, 0.021);
		float deep = deep_skin * smoothstep(0.35, 0.5, dyev.g / max(dyev.r, 1e-3))
			* smoothstep(0.05, 0.09, dl0);
		dyev = mix(dyev, deep_warm * (dl / dot(deep_warm, lum)), dye_deep_warm * deep * mix(1.0, dye_fair_warm, fair)) * (1.0 + 0.1 * deep);
		// (round 4: a fair dye held keeps its own hue, a honey brown, not the copper warm: a blonde on deep skin read
		// as the default's auburn)
		vec3 held_to = mix(mix(warm, dye_held_warm, smoothstep(0.025, 0.04, dl0)), dyev / dl, fair);
		vec3 dye_held = mix(held_to * (dl / dot(held_to, lum)), dyev, pow(room, 2.5));
		// (face 33: held, it keeps its whole colour, so a blonde's or redhead's brows on deep skin stay golden-brown
		// or auburn, never grey-green)
		vec3 dye_col = max(mix(vec3(dl), dye_held, mix(max(dye_sat, dye_sat_held), dye_sat, max(room, fair))), vec3(0.0)) * room;
		dye_col = mix(vec3(dot(dye_col, lum)), dye_col, mix(1.0, dye_fair_sat, fair));
		// (face 33: never mixed past the dye, which pushed a dark dye away from the skin's warmth into blue-black
		// and clipped its red to nothing; a hair darker than the brow's core is the dye darkened, its hue kept)
		float r = pow(clamp(raw, 0.0, 1.0), dye_gamma);
		// (face 33: mixed in ratio, not in sum: a half-dark hair keeps the warmth of the skin and the dye between
		// them, where a sum's grey middle went blue-grey under a grade's toe)
		vec3 sc = max(skin_col, vec3(1e-3));
		vec3 dyed_col = sc * pow(max(dye_col, vec3(1e-3)) / sc, vec3(r)) * (1.0 - dye_deep * clamp(raw - 1.0, 0.0, 0.4) / 0.4);
		// (dye_light 0: as painted, its hue the dye's: Own's brows before face 32)
		vec3 painted = mix(vec3(1.0), dyev / dl, dye_sat) * mix(hl, skin, soften) * tl;
#ifdef MUL
		// (face 40 r2: on deep skin her brows darken the skin's own lit colour (blend_mul, unshaded): drawn as a lit
		// surface of their own they took none of her skin's warm subsurface light, only the night's blue, and every
		// stroke's core read blue-black whatever the dye (#0e0e17). Each hair takes her skin toward the dye's tint at
		// dye_room of its lightness.)
		vec3 dt = deep_tint / max(dot(deep_tint, lum), 1e-4) * dot(sc, lum) * dye_room;
		float a = p.a * smoothstep(hair_lo, hair_hi, hair) * strength * min(r, 1.0);
		// (against the texel's own paint, her skin's painted brow in it: against the skin round it, that brow, already dark
		// and red under a deep tone, went near black (#040308) in the cores and orange-red at the edges; above 1 where the
		// dye has more of a channel than that paint)
		vec3 f = clamp(dt / max(here * skin_tone, vec3(2e-3)), 0.0, 8.0);
		float fl = dot(f, lum);
		vec3 fo = vec3(f.r, min(f.g, f.r * mul_warm.g / max(mul_warm.r, 1e-3)), 0.0);
		fo.b = min(f.b, fo.g * mul_warm.b / max(mul_warm.g, 1e-3));
		f = mix(f, fo * (fl / max(dot(fo, lum), 1e-4)), mul_order);
		// (the darken: the tint's luminance over her painted skin's there, so the stroke is as light as the tint made it)
		float k = clamp(dot(dt, lum) / max(dot(here * skin_tone, lum), 2e-3), 0.0, 8.0);
		f = mix(f, mul_warm * (k / max(dot(mul_warm, lum), 1e-3)), mul_scalar);
		f *= UV.x < mul_split ? mul_side_a : mul_side_b;
		if (target_mode > 0.5) {
			vec3 s_srgb = lin_srgb(sc);
			float sv = max(s_srgb.r, max(s_srgb.g, s_srgb.b));
			vec3 tg = srgb_lin(max(hsv_rgb(vec3(brow_target.xy, brow_target.z * sv * (UV.x < mul_split ? target_side.x : target_side.y))), vec3(target_floor)));
			vec3 ft = clamp(tg / max(here * skin_tone, vec3(2e-3)), 0.0, target_cap);
			// (blue never lifted past green: lifted, the stroke took the night fill on her shadowed brow as violet, h 250-300)
			ft.b = mix(ft.b, min(ft.b, ft.g), target_border);
			f = ft;
		}
		ALBEDO = mix(vec3(1.0), f, a);
		ALPHA = 1.0;
#else
		ALBEDO = clamp(mix(painted, dyed_col, dye_light), 0.0, 1.0);
		ALPHA = p.a * smoothstep(hair_lo, hair_hi, hair) * strength;
#endif
	} else {
		ALBEDO = p.rgb;
		ALPHA = p.a * strength;
	}
	ROUGHNESS = rough;
	METALLIC = metal;
	SPECULAR = dyed ? 0.0 : 0.5;
}
