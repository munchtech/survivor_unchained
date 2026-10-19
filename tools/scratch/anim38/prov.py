p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a6b5a13d0be70144d\docs\legal\ASSET_PROVENANCE.md"
s = open(p, encoding="utf-8").read()
a = 'https://sketchfab.com/3d-models/viking-sword-game-model-a05d0bd73e9e4508b873ffd7b6a6238d |'
b = ('https://sketchfab.com/3d-models/viking-sword-game-model-a05d0bd73e9e4508b873ffd7b6a6238d; MODIFIED 18 Oct 2026 '
     '(animation, `tools/assets/grip_conform.py conform viking_sword --seat --round`): only the grip band\'s vertices drawn '
     'to 13.7 mm round (was a flat 36.9 x 18.9 mm oval), the Blade1H grip standard (docs/anim/GRIP_STANDARD.md), and an '
     'anchor_grip node added at the type\'s grip point (38.6 mm toward the pommel from the plain mount); guard, pommel, '
     'blade, UVs and texture as they came. The change is ours, derived from the source piece |')
assert s.count(a) == 1
s = s.replace(a, b)
a = 'https://sketchfab.com/3d-models/silver-bladed-weapons-fantasy-weapon-set-d5189211a1d348b0a9d7ddc052a22989 |'
b = ('https://sketchfab.com/3d-models/silver-bladed-weapons-fantasy-weapon-set-d5189211a1d348b0a9d7ddc052a22989; MODIFIED '
     '18 Oct 2026 (animation, `tools/assets/grip_conform.py conform dagger_b --no-anchor`): the second dagger\'s '
     '(Cube_004_01) grip band scaled to the Dagger grip standard, 29.2 x 15.2 mm (was 24.9 x 11.9; '
     'docs/anim/GRIP_STANDARD.md), 72 vertices, nothing else touched (Cube_004, guards, blades, UVs and texture byte for '
     'byte). The change is ours, derived from the source piece |')
assert s.count(a) == 1
s = s.replace(a, b)
open(p, "w", encoding="utf-8", newline="").write(s)
print("ok")
