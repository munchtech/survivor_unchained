import pickle, numpy as np
F = pickle.load(open(r'C:/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/746784c6-95b9-4ef2-95bf-f24b9874f4bb/scratchpad/anim45/staff/frames_arcanist.pkl','rb'))
H = np.concatenate([d['hat'] for d in F]); print(len(F), 'hat y range', H[:,1].min().round(3), H[:,1].max().round(3))
c = np.array([0.03, 0, 0.03])
for ang in range(150, 271, 15):  # 180 = straight behind (-z), 270 = her right (-x)
    a = np.radians(ang); d = np.array([np.sin(a), 0, np.cos(a)])
    r = (H - c) @ d
    lat = np.linalg.norm((H - c) - np.outer(r, d) - np.outer(H[:,1], [0,1,0]), axis=1)
    m = lat < 0.05
    print(ang, 'reach', r[m].max().round(3), 'y at reach', H[m][r[m].argmax(), 1].round(3), 'min y of brim within', H[m & (r > r[m].max() - 0.08)][:,1].min().round(3))
B = np.concatenate([d['body'] for d in F[:1]])
for y in (1.5, 1.6, 1.7):
    m = np.abs(B[:,1]-y) < 0.02; print('body y', y, 'x', B[m][:,0].min().round(3), B[m][:,0].max().round(3), 'zmin', B[m][:,2].min().round(3))
print('legs envelope (min z per height band, and its x) over frames; frames are in world, check pelvis drift')
for d in F:
    pass
Lg = [(d['name'], d['legs']) for d in F]
for y in np.arange(0.2, 0.95, 0.1):
    worst = (9, None, None)
    for n, P in Lg:
        m = (P[:,1] >= y) & (P[:,1] < y + 0.1)
        if m.any():
            j = P[m][:,2].argmin()
            if P[m][j,2] < worst[0]: worst = (P[m][j,2].round(3), P[m][j,0].round(3), n)
    print(round(y,1), worst)
print('spine origin z per frame range', np.round([d['sp'][2,3] for d in F][::8],3))
