import sys
sys.path.insert(0, r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid3')
from edlib import edit

edit('tools/assets/heroine_paint.py', [
    ('''def brows_layer(shape, f):
    """Her painted brows, found: grey how dark each hair is, alpha how much brow."""
    a = np.clip(f['brows'] * 1.6, 0, 1)
    L = layer(shape)
    L[..., 0] = L[..., 1] = L[..., 2] = np.clip(a * 1.2, 0, 1)
    L[..., 3] = blur(a, 1.0)
    return L''', '''def brows_layer(shape, f):
    """Her painted brows, found, hair by hair: grey how dark each hair is (the
    game shades the dye by it, so the brow keeps its strokes in any colour),
    alpha how much brow there is (the gaps between hairs thin, so the skin
    shows between them)."""
    dark = f['brows']
    L = layer(shape)
    L[..., 0] = L[..., 1] = L[..., 2] = np.clip(dark * 1.8, 0, 1)
    L[..., 3] = blur(np.clip(dark * 2.6, 0, 1), 0.6)
    return L'''),
])
edit('godot/shaders/heroine_paint.gdshader', [
    ('''// Her brows (paint/brows.png, how much brow there is in its alpha): drawn in
// her hair's colour, a shade darker as brows are, covering the copper brows
// painted into her skin where they are thick.''', '''// Her brows (paint/brows.png: how dark each hair is in its grey, how much brow
// there is in its alpha): drawn in their colour (People.HerPaint: a shade
// darker than her hair, as brows are), each hair darker by its grey, covering
// the copper brows painted into her skin.'''),
    ('''	ALBEDO = dyed ? dye * 0.55 : p.rgb;
	ALPHA = (dyed ? smoothstep(0.04, 0.55, p.a) : p.a) * strength;''', '''	ALBEDO = dyed ? dye * mix(1.0, 0.5, p.r) : p.rgb;
	ALPHA = (dyed ? smoothstep(0.03, 0.5, p.a) : p.a) * strength;'''),
])
edit('godot/src/Actors/People.cs', [
    ('''                    m.SetShaderParameter("dye", b);''', '''                    m.SetShaderParameter("dye", b.Darkened(0.3f));'''),
])
