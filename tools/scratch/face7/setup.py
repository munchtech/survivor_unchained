import os, shutil
S4 = r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face4'
S5 = S4[:-1] + '5'
for f in ['shot.ps1', 'rebuild.ps1', 'rebuild_head.ps1', 'repaint_all.ps1', 'build_v7.ps1', 'shots_v7.ps1', 'sheet.py', 'stray.py',
          'hair_views.py', 'mask_view.py', 'measure.py', 'overlay.py', 'presets_wrap.ps1', 'portrait.ps1', 'tendril_check.py', 'hair_dbg.py']:
    s = open(os.path.join(S4, f), encoding='utf-8').read()
    s = s.replace('agent-a833b7942e978d994', 'agent-a7905c3e498df9528')
    open(os.path.join(S5, f), 'w', encoding='utf-8').write(s)
for d in ['paint_doe', 'paint_fey', 'paint_hardwon', 'paint_highborn', 'paint_moonlit', 'paint_saffron', 'paint_sunborn', 'paint_vixen',
          'paint_wildling', 'paintL']:
    if not os.path.exists(os.path.join(S5, d)):
        shutil.copytree(os.path.join(S4, d), os.path.join(S5, d))
print(sorted(os.listdir(S5)))
