import os
G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a26767f7f9955cb56\godot"
def rep(path, pairs):
    p = os.path.join(G, path)
    s = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert a in s, (path, a[:70])
        s = s.replace(a, b)
    open(p, 'w', encoding='utf-8').write(s)

rep('src/World/Grass.cs', [
('                float x = centre.X - radius + (k + 0.5f) * step, zz = centre.Y - radius + (j + 0.5f) * step;\n                mm.SetInstanceTransform(i++, new Transform3D(new Basis(Vector3.Up, rng.Randf() * Mathf.Tau), new Vector3(x, 0, zz)));',
 '                float x = centre.X - radius + (k + rng.Randf()) * step, zz = centre.Y - radius + (j + rng.Randf()) * step;\n                mm.SetInstanceTransform(i++, new Transform3D(new Basis(Vector3.Up, rng.Randf() * Mathf.Tau), new Vector3(x, 0, zz)));'),
])
rep('logic/Maps/ArenaGen.cs', [
('''    public double Open;
}''', '''    public double Open;
    /// <summary>Fallen leaves lying loose over the ground (geometry: World/Grass.cs, Leaves).</summary>
    public double Leaves;
}'''),
('        readonly byte[] grass = new byte[SplatRes * SplatRes];', '        readonly byte[] grass = new byte[SplatRes * SplatRes];\n        readonly byte[] leaves = new byte[SplatRes * SplatRes];'),
('                    grass[j * SplatRes + i] = MapGen.B(p.Grass * (1 - p.Char) * (1 - p.Wet * 0.9) * (1 - p.Trod * 0.7));',
 '                    grass[j * SplatRes + i] = MapGen.B(p.Grass * (1 - p.Char) * (1 - p.Wet * 0.9) * (1 - p.Trod * 0.7));\n                    // Nor do leaves lie on char, in water or on trodden ground; they blow into the hollows.\n                    leaves[j * SplatRes + i] = MapGen.B(p.Leaves * (1 - p.Char) * (1 - p.Wet) * (1 - p.Trod * 0.8));'),
('Splat3 = splat3, Grass = grass,', 'Splat3 = splat3, Grass = grass, Leaves = leaves,'),
])
rep('logic/Maps/MapGen.cs', [
('''    public byte[]? Grass;''', '''    public byte[]? Grass;
    /// <summary>An arena's fallen leaves, one byte a texel as Grass: how thick they lie.</summary>
    public byte[]? Leaves;'''),
])
rep('src/World/ZoneData.cs', [
('            for (int i = 0; i < m.Grass.Length; i++) g[i * 4 + 1] = (byte)(255 - m.Grass[i]);',
 '            for (int i = 0; i < m.Grass.Length; i++) g[i * 4 + 1] = (byte)(255 - m.Grass[i]);\n            // R: the fallen leaves (Grass.Leaves).\n            if (m.Leaves != null) for (int i = 0; i < m.Leaves.Length; i++) g[i * 4] = m.Leaves[i];'),
])
rep('src/World/ArenaGround.cs', [
('''    public static GrassLook GrassOf(string place) => Grasses[place];''',
'''    public static GrassLook GrassOf(string place) => Grasses[place];

    /// <summary>A place's fallen leaves: how thick where its paint lays them, leaves to a
    /// cell of sixty centimetres, and how large (1: about eleven centimetres).</summary>
    public sealed record LeafLook(float Density, int PerCell, float Size);

    static readonly Dictionary<string, LeafLook> LeafLooks = new()
    {
        // The Hollow's: this autumn's, over the litter of years.
        ["hollow"] = new(1f, 14, 1.35f),
    };

    public static LeafLook? LeavesOf(string place) => LeafLooks.GetValueOrDefault(place);'''),
('''    public static bool GrowsGrass(string place) => Grasses[place].Density > 0;''',
 '''    public static bool GrowsGrass(string place) => Grasses[place].Density > 0 || LeafLooks.ContainsKey(place);'''),
])
rep('src/World/ZoneView.cs', [
('''        grass?.QueueFree();
        grass = Grass.Build(Data, at, radius, grassCell);
        grassAt = at;
        grassRadius = radius;
        AddChild(grass);''',
'''        grass?.QueueFree();
        leaves?.QueueFree();
        grass = Grass.Build(Data, at, radius, grassCell);
        grassAt = at;
        grassRadius = radius;
        AddChild(grass);
        // An arena's fallen leaves, following her as its grass does.
        leaves = Grass.Leaves(Data, at, radius, grassCell);
        if (leaves != null) AddChild(leaves);'''),
('    MultiMeshInstance3D? grass;', '    MultiMeshInstance3D? grass, leaves;'),
('''    public void FollowGrass(Vector2 at) => grass?.Multimesh.Mesh.SurfaceGetMaterial(0)?.Set("shader_parameter/centre", at);''',
 '''    public void FollowGrass(Vector2 at)
    {
        grass?.Multimesh.Mesh.SurfaceGetMaterial(0)?.Set("shader_parameter/centre", at);
        leaves?.Multimesh.Mesh.SurfaceGetMaterial(0)?.Set("shader_parameter/centre", at);
    }'''),
])
print('ok')
