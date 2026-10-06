import sys
sys.path.insert(0, r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid3')
from edlib import edit

edit('godot/shaders/heroine_paint.gdshader', [
    ('''		ALBEDO = dye * mix(0.5, 1.15, clamp(dot(here, lum) / max(skin, 1e-3) * 1.6, 0.0, 1.0));''',
     '''		ALBEDO = dye * mix(0.78, 1.15, clamp(dot(here, lum) / max(skin, 1e-3) * 1.6, 0.0, 1.0));'''),
])
edit('godot/src/Actors/People.cs', [
    ('''b.Darkened(0.3f + 0.25f * b.Luminance).Lerp(new Color("#5a3a24"), 0.25f)''', '''b.Darkened(0.25f + 0.15f * b.Luminance).Lerp(new Color("#6a4a30"), 0.2f)'''),
])
