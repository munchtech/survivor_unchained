"""Mipmaps on for the face's textures the game loads from code (Godot's detect-3D never sees them, so they kept the 2D
defaults: no mipmaps, and at the Look a pixel point-sampled a few texels of paint: the faces' brows came out sparse and
pale, and the freckles and grain sparkled at a distance)."""
import os, re
D = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aed215ba3ca60cc29\godot\art\people\head_tex'
names = ['heroine_head_%s.jpg' % i for i in ('doe', 'fey', 'hardwon', 'highborn', 'moonlit', 'saffron', 'sunborn', 'vixen', 'wildling')]
names += ['heroine_freckles.png', 'heroine_freckles_graft.png', 'heroine_grain.png', 'heroine_ao.png', 'heroine_shadow.png', 'hero_shadow.png']
for n in names:
    p = os.path.join(D, n + '.import')
    s = open(p, encoding='utf-8').read()
    t = s.replace('mipmaps/generate=false', 'mipmaps/generate=true')
    if t != s:
        open(p, 'w', encoding='utf-8', newline='\n').write(t)
        print('mipmaps on:', n)
    else:
        print('unchanged:', n, re.search(r'mipmaps/generate=\w+', s).group(0))
