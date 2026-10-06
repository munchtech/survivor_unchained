import os
G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a26767f7f9955cb56\godot"
def rep(path, pairs):
    p = os.path.join(G, path)
    s = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert a in s, (path, a[:70])
        s = s.replace(a, b)
    open(p, 'w', encoding='utf-8').write(s)

rep('logic/Maps/Arenas/HollowNight.cs', [
('''        // Grass where the canopy opens: a little along the clough and round the pool.''',
'''        // This autumn's leaves, loose over the litter: blown into drifts against the banks and
        // thin where it is trodden, wet or mossed.
        double blown = MathX.Smoothstep(0.3, 0.7, Noise.Noise(x * 0.07 - 23, z * 0.07 + 41) * 0.7 + n2 * 0.3 + MathX.Smoothstep(6, 1, inn) * 0.35);
        p.Leaves = (0.35 + 0.65 * blown) * (1 - p.L3) * (1 - p.L4) * (1 - p.Moss * 0.85);
        // Grass where the canopy opens: a little along the clough and round the pool.'''),
])
rep('logic/Maps/Arenas/Hollow.cs', [
('''        // Grass only where the canopy opens, in clearings of the litter.''',
'''        // This autumn's leaves, loose over the litter, in drifts; thin on the runs, the banks, the moss.
        double blown = MathX.Smoothstep(0.3, 0.7, Noise.Noise(x * 0.07 - 23, z * 0.07 + 41) * 0.7 + n2 * 0.3 + MathX.Smoothstep(10, 2, inn) * 0.3);
        p.Leaves = (0.35 + 0.65 * blown) * (1 - p.L3) * (1 - p.L4) * (1 - p.Moss * 0.85);
        // Grass only where the canopy opens, in clearings of the litter.'''),
])
print('ok')
