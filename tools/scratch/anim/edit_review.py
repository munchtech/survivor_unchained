from pathlib import Path
p = Path(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa4f5fc266b043035\godot\tools_scenes\anim_review.gd')
s = p.read_text(encoding='utf-8')
rep = [
    ('#   OUTFIT=warden|arcanist|reaver|ranger   her outfit; HAIR=style; WEAPON=sword|staff|bow|axe|axes|daggers|wand\n',
     '#   OUTFIT=warden|arcanist|reaver|ranger   her outfit; HAIR=style; WEAPON=sword|staff|bow|axe|axes|daggers|wand\n'
     '#   MODEL=female|male                      a townsfolk body (the kit\'s) instead of hers, in PARTS (kit\n'
     '#                                          outfit parts, comma-separated); clips "folk/<name>"\n'),
    ('\ther = load("res://art/people/heroine.glb").instantiate()\n',
     '\tvar model = env("MODEL", "")\n'
     '\tif model != "":\n'
     '\t\ther = load("res://assets/people/Superhero_%s_FullBody.gltf" % model.capitalize()).instantiate()\n'
     '\telse:\n'
     '\t\ther = load("res://art/people/heroine.glb").instantiate()\n'),
    ('\tdress(her)\n', '\tif model != "": kit(her, env("PARTS", ""))\n\telse: dress(her)\n'),
    ('\t\tap.add_animation_library("her", load("res://art/anim/heroine.res"))\n',
     '\t\tap.add_animation_library("her", load("res://art/anim/heroine.res"))\n'
     '\tif ResourceLoader.exists("res://art/anim/folk.res"):\n'
     '\t\tap.add_animation_library("folk", load("res://art/anim/folk.res"))\n'),
    ('func dress(h):\n',
     '# A townsfolk body in the kit\'s clothes, as People.Build puts one together.\n'
     'func kit(h, parts):\n'
     '\tvar skel: Skeleton3D = h.find_children("*", "Skeleton3D", true, false)[0]\n'
     '\tfor part in parts.split(",", false):\n'
     '\t\tvar sc = load("res://assets/people/%s.gltf" % part).instantiate()\n'
     '\t\tvar from = sc.find_children("*", "Skeleton3D", true, false)[0]\n'
     '\t\tfor mi in from.get_children():\n'
     '\t\t\tif mi is MeshInstance3D:\n'
     '\t\t\t\tfrom.remove_child(mi)\n'
     '\t\t\t\tmi.owner = null\n'
     '\t\t\t\tskel.add_child(mi)\n'
     '\t\t\t\tmi.skeleton = NodePath("..")\n'
     '\t\tsc.free()\n\n'
     'func dress(h):\n'),
]
for a, b in rep:
    assert a in s, a[:50]
    s = s.replace(a, b, 1)
p.write_text(s, encoding='utf-8')
print('ok')
