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
// Her brows (paint/brows.png: their shape, in its alpha): each hair found in
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
uniform float dye_sat = 0.85;

void vertex() {
	// (a tenth of a millimetre out, so it never fights the skin under it)
	VERTEX += NORMAL * 0.0001;
}

void fragment() {
	vec4 p = texture(paint, UV);
	if (dyed) {
		vec3 here = texture(skin_paint, UV).rgb;
		// (the skin round it: the brightest of a ring of samples a brow's breadth out,
		// which is past the brow on one side or the other however thick it is)
		const vec3 lum = vec3(0.3, 0.59, 0.11);
		vec2 px = 1.0 / vec2(textureSize(skin_paint, 0));
		float skin = 0.0;
		for (int i = 0; i < 16; i++) {
			float a = float(i) * 0.3927;
			skin = max(skin, dot(texture(skin_paint, UV + vec2(cos(a), sin(a)) * px * 44.0).rgb, lum));
		}
		// (how much darker than that skin, as a share of it: a hair is half as bright or less)
		float hair = clamp((skin - dot(here, lum)) / max(skin * 0.45, 1e-3), 0.0, 1.0);
		// (each hair's own light and dark kept from the painting, so the brow keeps its strokes;
		// its colour the dye's, at its own lightness)
		float l = mix(dot(here, lum), skin, soften) * dot(skin_tone, lum);
		vec3 hue = mix(vec3(1.0), dye / max(dot(dye, lum), 1e-3), dye_sat);
		ALBEDO = clamp(hue * l, 0.0, 1.0);
		ALPHA = p.a * smoothstep(0.08, 0.6, hair) * strength;
	} else {
		ALBEDO = p.rgb;
		ALPHA = p.a * strength;
	}
	ROUGHNESS = rough;
	METALLIC = metal;
	SPECULAR = dyed ? 0.25 : 0.5;
}
