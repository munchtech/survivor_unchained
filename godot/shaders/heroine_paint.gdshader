// Her brows' dye, over her skin (People.HerPaint). The face paint itself is drawn in her skin since 20 October
// (heroine_skin.gdshader's face_paint); this pass draws it only with --paint-pass, to compare.
// Paint on her face (People.HerPaint; tools/assets/heroine_paint.py lays
// each design out on her head's own paint): drawn over her skin as a pass of
// its own, the same face a hair's breadth out, so it lies on the skin rather
// than in it (no light carried under it) and moves with her face as it is
// shaped, blinks and speaks. Its own sheen: chalky woad and ash, waxy kohl,
// bright gold leaf.
shader_type spatial;
render_mode blend_mix, depth_draw_never, cull_back;

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
uniform float dye_gamma = 0.7;
// (the dye's lightness held to this share of her skin's at most, so a platinum blonde's brows on deep skin are a
// darker blonde, never a pale patch)
uniform float dye_room = 0.6;
// (how much a hair as grey as can be counts, against a dark one: 1 the same)
uniform float grey_hair = 0.8;

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
		float dl = max(dot(dye, lum), 1e-3);
		// (held darker than her skin, a fair dye is warmed as it is darkened: a blonde's brows on deep skin a golden
		// brown; the dye's yellow only darkened read olive-grey)
		float room = min(1.0, sk * dye_room / dl);
		const vec3 warm = vec3(0.195, 0.088, 0.034);
		vec3 dye_held = mix(warm * (dl / dot(warm, lum)), dye, room);
		vec3 dye_col = mix(vec3(dl), dye_held, dye_sat) * room;
		float r = pow(clamp(raw, 0.0, 1.4), dye_gamma);
		vec3 dyed_col = max(mix(skin_col, dye_col, r), vec3(0.0));
		// (dye_light 0: as painted, its hue the dye's: Own's brows before face 32)
		vec3 painted = mix(vec3(1.0), dye / dl, dye_sat) * mix(hl, skin, soften) * tl;
		ALBEDO = clamp(mix(painted, dyed_col, dye_light), 0.0, 1.0);
		ALPHA = p.a * smoothstep(0.08, 0.6, hair) * strength;
	} else {
		ALBEDO = p.rgb;
		ALPHA = p.a * strength;
	}
	ROUGHNESS = rough;
	METALLIC = metal;
	SPECULAR = dyed ? 0.25 : 0.5;
}
