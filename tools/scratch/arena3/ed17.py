import os
G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a26767f7f9955cb56\godot"
def rep(path, pairs):
    p = os.path.join(G, path)
    s = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert a in s, (path, a[:70])
        s = s.replace(a, b)
    open(p, 'w', encoding='utf-8').write(s)
rep('src/World/ArenaEdge.cs', [
('        const float H = 14f;', '        // (Low: a canopy far over a low moon throws its pools a long way off, and they slide.)\n        const float H = 9f;'),
('        if (place.Air.Dapple > 0 && z.Splat3 != null) root.AddChild(Canopy(z, (float)place.Air.Dapple));',
 '        // (A story place is a cut under the wood\'s edge: more of its sky is open.)\n        if (place.Air.Dapple > 0 && z.Splat3 != null) root.AddChild(Canopy(z, (float)place.Air.Dapple * (z.Story ? 0.7f : 1f)));'),
])
rep('src/World/ArenaGround.cs', [
# soften the litter's micro-contrast: control detail, keep the big shapes
('new(0.11f, 1.0f, Con: 1.3f, Lift: 0.02f, Size: 1.9f), new(0.06f, 0.9f, Con: 1.35f, Size: 1.5f)',
 'new(0.1f, 1.0f, Con: 0.8f, Lift: 0.02f, Size: 1.9f), new(0.05f, 0.9f, Con: 0.9f, Size: 1.5f)'),
('new(0.1f, 0.9f, Con: 1.35f, Lift: 0.01f, Size: 1.4f), new(0.07f, 0.7f)],', 'new(0.085f, 0.9f, Con: 0.9f, Lift: 0.01f, Size: 1.4f), new(0.07f, 0.7f)],'),
])
rep('logic/Maps/ArenaPlaces.cs', [
# under the crowns the sky still lights the litter a little
('HemiSky = "#2a3c48", HemiGround = "#16140e", HemiIntensity = 1.25, EnvIntensity = 0.75,',
 'HemiSky = "#2a3c48", HemiGround = "#16140e", HemiIntensity = 1.6, EnvIntensity = 0.85,'),
])
print('ok')
