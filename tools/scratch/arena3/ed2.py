import os
G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a26767f7f9955cb56\godot"
def rep(path, pairs):
    p = os.path.join(G, path)
    s = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert a in s, (path, a[:70])
        s = s.replace(a, b)
    open(p, 'w', encoding='utf-8').write(s)

rep('logic/Maps/ArenaGen.cs', [
('''    /// <summary>Foxfire: rotting wood and roots glowing a little, cold (the Hollow's own light).</summary>
    public double Fox;''',
'''    /// <summary>Foxfire: rotting wood and roots glowing a little, cold (the Hollow's own light).</summary>
    public double Fox;
    /// <summary>Open to the sky: a clearing in a wood, where the moon comes down whole and the
    /// canopy's dapple stops (0 under the trees).</summary>
    public double Open;'''),
('splat3[o + 2] = MapGen.B(p.Fox * (1 - p.Char));', 'splat3[o + 2] = MapGen.B(p.Fox * (1 - p.Char)); splat3[o + 3] = MapGen.B(p.Open);'),
])
rep('shaders/arena_ground.gdshader', [
('''		albedo *= mix(1.0, mix(0.45, 1.4, smoothstep(0.4, 0.62, leaves)), dapple);''',
'''		// In a clearing (splat3 A) the moon comes down whole: a pool of it, the canopy's
		// shade all round.
		albedo *= mix(mix(1.0, mix(0.45, 1.4, smoothstep(0.4, 0.62, leaves)), dapple), 1.35, s3.a);'''),
('''// R moss, G the slurry's light.''', '''// R moss, G the slurry's light, B foxfire, A open to the sky.'''),
])
rep('logic/Maps/Arenas/HollowNight.cs', [
('''        // Grass where the canopy opens: a little along the clough and round the pool.''',
'''        // Where the canopy opens: the den's floor (the boss's ground, under the moon whole), the
        // pool (it holds the sky), and the clough's middle.
        double cl = Math.Abs(x - cx) + n1 * 2;
        p.Open = Math.Max(Math.Max(1 - MathX.Smoothstep(7, 13, dd + n1 * 3), 1 - MathX.Smoothstep(5, 10, dp + n1 * 2)),
            space == "clough" ? (1 - MathX.Smoothstep(2, 6, cl)) * 0.7 : 0);
        // Grass where the canopy opens: a little along the clough and round the pool.'''),
('int light = B.Glow(x, z, "#ff8a3a", 9, fire: true, height: 1.2, size: 0.85);',
 'int light = B.Glow(x, z, "#ff8a3a", 12, fire: true, height: 1.4, size: 1.15);'),
('Z = z + uz * 2.1, Size = 0.7, Light = light, Ring = false });', 'Z = z + uz * 2.1, Size = 0.95, Light = light, Ring = false });'),
])
rep('logic/Maps/ArenaPlaces.cs', [
('''            HemiSky = "#2a3c48", HemiGround = "#16140e", HemiIntensity = 1.0, EnvIntensity = 0.7,''',
'''            HemiSky = "#2a3c48", HemiGround = "#16140e", HemiIntensity = 1.25, EnvIntensity = 0.75,'''),
])
print('ok')
