import sys
sys.path.insert(0, r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid3')
from edlib import edit

edit('godot/shaders/heroine_paint.gdshader', [
    ('''		ALBEDO = dye * mix(1.0, 0.6, hair);''', '''		// (each hair's own light and dark kept from the painting, so the brow keeps its strokes)
		ALBEDO = dye * mix(0.5, 1.15, clamp(dot(here, lum) / max(skin, 1e-3) * 1.6, 0.0, 1.0));'''),
    ('''	SPECULAR = 0.5;''', '''	SPECULAR = dyed ? 0.25 : 0.5;'''),
])
edit('godot/src/Actors/People.cs', [
    ('''                    m.SetShaderParameter("dye", b.Darkened(0.3f));''', '''                    // (a shade darker than her hair and a little warmer, as brows are)
                    m.SetShaderParameter("dye", b.Darkened(0.3f).Lerp(new Color("#5a3a24"), 0.15f));'''),
])
