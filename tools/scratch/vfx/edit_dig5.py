p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a191ed81e2df462cf\godot\src\Fx\BattleFx.Dig.cs"
s = open(p, encoding="utf-8").read()
reps = [
    ("""        var mat = new StandardMaterial3D
        {
            AlbedoTexture = GD.Load<Texture2D>("res://art/arena/dig/albedo.jpg"), AlbedoColor = new Color(0.82f, 0.78f, 0.74f),
            NormalEnabled = true, NormalTexture = GD.Load<Texture2D>("res://art/arena/dig/normal.jpg"), NormalScale = 1.4f,
            Uv1Triplanar = true, Uv1WorldTriplanar = true, Uv1Scale = new Vector3(0.45f, 0.45f, 0.45f), Roughness = 0.95f,
        };""",
     """        var mat = new StandardMaterial3D
        {
            AlbedoTexture = DigLayer("albedo", 0), AlbedoColor = new Color(0.82f, 0.78f, 0.74f),
            NormalEnabled = DigLayer("normal", 0) != null, NormalTexture = DigLayer("normal", 0), NormalScale = 1.4f,
            // (the clay layer is laid four metres to a tile, as the ground lays it: layers.json)
            Uv1Triplanar = true, Uv1WorldTriplanar = true, Uv1Scale = new Vector3(0.25f, 0.25f, 0.25f), Roughness = 0.95f,
        };"""),
    ("""    MeshInstance3D? mound;
""",
     """    MeshInstance3D? mound;
    static readonly Dictionary<string, Texture2D?> digLayers = new();

    /// <summary>One layer of the Dig's ground (arena art's texture arrays: 0 clay, 1 spoil, ...), as a
    /// plain texture for a thing made of the same earth.</summary>
    static Texture2D? DigLayer(string map, int layer)
    {
        string key = map + layer;
        if (digLayers.TryGetValue(key, out var t)) return t;
        var arr = GD.Load<Resource>($"res://art/arena/dig/{map}.jpg") as TextureLayered;
        var img = arr != null && layer < arr.GetLayers() ? arr.GetLayerData(layer) : null;
        return digLayers[key] = img != null ? ImageTexture.CreateFromImage(img) : null;
    }
"""),
]
for a, b in reps:
    assert a in s, a[:60]
    s = s.replace(a, b)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
