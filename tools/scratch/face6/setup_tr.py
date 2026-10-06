import os, shutil
S4 = r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face4'
S5 = S4[:-1] + '5'
for i in ['heroine', 'highborn', 'vixen', 'doe', 'sunborn', 'moonlit', 'saffron', 'wildling', 'hardwon', 'fey']:
    d = os.path.join(S5, 'tr_' + i)
    if os.path.exists(d):
        continue
    os.makedirs(d)
    for f in os.listdir(os.path.join(S4, 'tr_' + i)):
        p = os.path.join(S4, 'tr_' + i, f)
        if os.path.isfile(p) and f.endswith('.glb'):
            shutil.copy2(p, d)
    print(i, sorted(os.listdir(d)))
