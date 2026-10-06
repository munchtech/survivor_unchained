from fontTools.ttLib import TTFont
import glob, os
src = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aab47bfdab5955dac\godot\art\fonts'
for f in glob.glob(os.path.join(src, '*.woff2')):
    t = TTFont(f); t.flavor = None
    out = os.path.join(r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid5\gb\fonts', os.path.basename(f).replace('.woff2', '.ttf'))
    t.save(out); print(os.path.basename(out))
