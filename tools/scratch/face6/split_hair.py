"""heroine_hair.gdshader split: its body to heroine_hair.gdshaderinc, and two shaders over it (cut by hashed alpha;
blended, for her scalp's cap and her hairline's fine hairs)."""
D = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2f7b0f1283f6144a\godot\shaders'
s = open(D + r'\heroine_hair.gdshader', encoding='utf-8').read()
head, body = s.split('render_mode cull_disabled, depth_draw_opaque;\n', 1)
assert 'ALPHA_HASH_SCALE = 1.0;' in body
body = body.replace('\tALPHA_HASH_SCALE = 1.0;\n', '#ifndef SOFT\n\tALPHA_HASH_SCALE = 1.0;\n#endif\n')
inc = ('// Her hair\'s shading, for heroine_hair.gdshader (cut to its strands by hashed\n'
       '// alpha) and heroine_hair_soft.gdshader (blended: SOFT).\n' + body)
open(D + r'\heroine_hair.gdshaderinc', 'w', encoding='utf-8', newline='\n').write(inc)
hard = head + 'render_mode cull_disabled, depth_draw_opaque;\n\n#include "res://shaders/heroine_hair.gdshaderinc"\n'
open(D + r'\heroine_hair.gdshader', 'w', encoding='utf-8', newline='\n').write(hard)
soft = ('// Her hair where it thins to nothing (heroine_hair.gdshaderinc): the cap on her\n'
        '// scalp as it fades out over her hairline, and the fine short hairs and baby\n'
        '// hairs there, blended over her skin as they are faint, not cut by hashed\n'
        '// alpha: a faint hair cut so is a scatter of dots, and her hairline read as\n'
        '// a speckled band with a hard edge (the dots do not move, so the TAA keeps them).\n'
        'shader_type spatial;\n'
        'render_mode blend_mix, cull_disabled, depth_draw_never;\n\n'
        '#define SOFT\n'
        '#include "res://shaders/heroine_hair.gdshaderinc"\n')
open(D + r'\heroine_hair_soft.gdshader', 'w', encoding='utf-8', newline='\n').write(soft)
print('split')
