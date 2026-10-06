"""Count shipped third-party files by source, from the tracked file list."""
import re, sys
files = [l.strip() for l in open(sys.argv[1], encoding='utf-8') if l.strip() and not l.strip().endswith(('.import', '.uid'))]
groups = {
    'Quaternius': r'^public/assets/(people|env/(village|props|nature))/|^godot/art/srgb/|^godot/art/people/her_Hair',
    'KayKit': r'^public/assets/(characters|props|anim)/|LICENSE-KayKit',
    'Kenney': r'^godot/art/fx/(sprites|embers|puff|runes)|^godot/art/sound/(impact|footstep|click|select|switch|toggle|tick|back|close|open|confirmation|error|drop|cloth|belt|book|creak|door|drawKnife|knifeSlice|handle|scroll)',
    'Poly Haven': r'^godot/art/(world|ground|arena|materials|studio)/|^public/assets/ground/|^godot/art/(outfit|people/outfit_tex)/(brown_leather|curly|fabric_leather|faux_fur|leather_red|metal_plate|rough_linen|rusty_metal|velour)',
    'ambientCG': r'^godot/art/(outfit|people/outfit_tex)/(Leather|Metal)',
    'OpenGameArt': r'^godot/art/sound/(bed_|anvil)',
    'Sketchfab': r'^public/assets/weapons/|^godot/art/beasts/|anime_female',
    'Fonts': r'^godot/art/fonts/',
    'MakeHuman': r'^godot/art/people/head_tex/(green_eye|eyelashes03|teeth|tongue01)',
}
tot = 0
for k, p in groups.items():
    n = sum(1 for f in files if re.search(p, f))
    tot += n
    print(k, n)
print('total', tot)
