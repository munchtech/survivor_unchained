import os
G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a26767f7f9955cb56\godot"
def rep(path, pairs):
    p = os.path.join(G, path)
    s = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert a in s, (path, a[:70])
        s = s.replace(a, b)
    open(p, 'w', encoding='utf-8').write(s)
rep('src/World/ArenaGround.cs', [
('        mat.SetShaderParameter("dapple", (float)place.Air.Dapple);',
 '        // (The canopy\'s pools are real shadow now, ArenaEdge.Canopy: none painted on the ground.)\n        mat.SetShaderParameter("dapple", 0f);'),
])
rep('logic/Maps/ArenaPlaces.cs', [
('KeyColor = "#a8c4d4", KeyIntensity = 4.2, KeyElevation = 38,', 'KeyColor = "#a8c4d4", KeyIntensity = 5.6, KeyElevation = 38,'),
])
rep('logic/Maps/Arenas/HollowNight.cs', [
('''        var (gx0, gz0) = Past(3.2);
        B.Glow(gx0, gz0, "#b8d060", 2.4, height: 0.3, flicker: 0.05);''',
'''        // (In the hole's mouth, under the plate: it lights the roots hanging over it from below.)
        var (gx0, gz0) = Past(0.6);
        B.Glow(gx0, gz0, "#b8d060", 4.5, height: 0.7, flicker: 0.06);'''),
])
rep('src/World/Pieces.Arena.cs', [
('(earth.Mesh(true), Surface("forest_ground_04", 1.6f, "#5a4c40"))', '(earth.Mesh(true), Surface("forest_ground_04", 1.6f, "#8a7a66"))'),
('(roots.Mesh(true), Surface("rough_wood", 0.9f, "#6a5e52"))', '(roots.Mesh(true), Surface("rough_wood", 0.9f, "#9a8a76"))'),
('(fine.Mesh(), Mat("#3e3428", 0, 0.9f))', '(fine.Mesh(), Mat("#6a5a46", 0, 0.9f))'),
])
print('ok')
