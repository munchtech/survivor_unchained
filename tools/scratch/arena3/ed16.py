import os
G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a26767f7f9955cb56\godot"
def rep(path, pairs):
    p = os.path.join(G, path)
    s = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert a in s, (path, a[:70])
        s = s.replace(a, b)
    open(p, 'w', encoding='utf-8').write(s)
rep('logic/Maps/Arenas/Ruts.cs', [
('("village/Prop_Wagon", -1.0, -9.0, 1.8), ("props/Cauldron", 1.5, 1.0, 0.8), ("props/Bucket_Wooden_1", 2.6, 1.6, 0.0) })',
 '("village/Prop_Wagon", -1.0, -9.0, 1.8), ("props/Bucket_Wooden_1", 2.6, 1.6, 0.0) })'),
('''        // Their colours: red rags on poles, at the camp's edge.''',
'''        // The pot, over its own fire in the middle of the camp: the camp's heart, the
        // brightest warm thing at the edge of the fight.
        {
            double px = campX + ux * 1.5 + fx * 1.0, pz = campZ + uz * 1.5 + fz * 1.0;
            B.Piece("arena/cookpot", px, pz, face);
            B.Block(px, pz, 1.2);
            B.Glow(px, pz, "#ff8a3a", 11, fire: true, height: 0.5, size: 0.75);
        }
        // Their colours: red rags on poles, at the camp's edge.'''),
])
print('ok')
