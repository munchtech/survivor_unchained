import sys
sys.path.insert(0, r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid3')
from edlib import edit

edit('tools/assets/heroine_paint.py', [
    ('''def brows_layer(shape, f):
    """Her painted brows, found, hair by hair: grey how dark each hair is (the
    game shades the dye by it, so the brow keeps its strokes in any colour),
    alpha how much brow there is (the gaps between hairs thin, so the skin
    shows between them)."""
    dark = f['brows']
    L = layer(shape)
    L[..., 0] = L[..., 1] = L[..., 2] = np.clip(dark * 1.8, 0, 1)
    L[..., 3] = blur(np.clip(dark * 2.6, 0, 1), 0.6)
    return L''', '''def brows_layer(shape, f):
    """Where her painted brows are: alpha the brow's whole shape, a little
    beyond it. The game finds each hair in her skin's own paint (its full
    size, which this layout halves) and dyes it there (heroine_paint.gdshader)."""
    dark = f['brows']
    L = layer(shape)
    band = np.clip(blur(np.clip(dark * 3.0, 0, 1), 5) * 2.0, 0, 1)
    L[..., 0] = L[..., 1] = L[..., 2] = 1.0
    L[..., 3] = band
    return L'''),
    ('''paint), and godot/art/people/paint/brows.png: her painted brows found in her
head's paint, so the game can dye them the colour of her hair (grey: how dark
each hair is, alpha: how much brow there is).''', '''paint), and godot/art/people/paint/brows.png: where her painted brows are in
her head's paint, so the game can dye them the colour of her hair (alpha: the
brows' shape; the game finds each hair in her skin's paint).'''),
])
edit('godot/shaders/heroine_paint.gdshader', [
    ('''// Her brows (paint/brows.png: how dark each hair is in its grey, how much brow
// there is in its alpha): drawn in their colour (People.HerPaint: a shade
// darker than her hair, as brows are), each hair darker by its grey, covering
// the copper brows painted into her skin.
uniform bool dyed = false;
uniform vec3 dye : source_color = vec3(0.35, 0.2, 0.1);''', '''// Her brows (paint/brows.png: their shape, in its alpha): each hair found in
// her skin's own paint at its full size (darker than the skin round it, and
// redder: they are painted copper) and drawn in its new colour (People.HerPaint:
// a shade darker than her hair, as brows are), the skin between them left be.
uniform bool dyed = false;
uniform vec3 dye : source_color = vec3(0.35, 0.2, 0.1);
uniform sampler2D skin_paint : source_color, filter_linear_mipmap_anisotropic;'''),
    ('''	vec4 p = texture(paint, UV);
	ALBEDO = dyed ? dye * mix(1.0, 0.5, p.r) : p.rgb;
	ALPHA = (dyed ? smoothstep(0.03, 0.5, p.a) : p.a) * strength;''', '''	vec4 p = texture(paint, UV);
	if (dyed) {
		vec3 here = texture(skin_paint, UV).rgb;
		vec3 round_it = textureLod(skin_paint, UV, 4.5).rgb;
		const vec3 lum = vec3(0.3, 0.59, 0.11);
		float hair = clamp((dot(round_it, lum) - dot(here, lum)) / 0.1 + 0.15, 0.0, 1.0) * clamp((here.r - here.b - 0.02) / 0.12, 0.0, 1.0);
		ALBEDO = dye * mix(1.0, 0.6, hair);
		ALPHA = p.a * smoothstep(0.08, 0.6, hair) * strength;
	} else {
		ALBEDO = p.rgb;
		ALPHA = p.a * strength;
	}'''),
])
edit('godot/src/Actors/People.cs', [
    ('''                    m.SetShaderParameter("dye", b.Darkened(0.3f));''', '''                    m.SetShaderParameter("dye", b.Darkened(0.3f));
                    m.SetShaderParameter("skin_paint", skin.GetShaderParameter("paint"));'''),
])
