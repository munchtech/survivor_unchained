p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a191ed81e2df462cf\godot\src\Fx\BattleFx.Dig.cs"
s = open(p, encoding="utf-8").read()
start = s.index("        var dirt = new NoiseTexture2D\n        {\n            Width = 128, Height = 128, Seamless = true,\n            Noise = new FastNoiseLite { Seed = 5")
end = s.index("        var m = new MeshInstance3D { Mesh = new SphereMesh { Radius = 1, Height = 1.2f")
s = s[:start] + '''        // The Dig's own dirt (arena art's), a shade darker: freshly turned earth is damp. (Its own
        // dark noise read as a black disc on the lit ground.)
        var mat = new StandardMaterial3D
        {
            AlbedoTexture = GD.Load<Texture2D>("res://art/arena/dig/albedo.jpg"), AlbedoColor = new Color(0.82f, 0.78f, 0.74f),
            NormalEnabled = true, NormalTexture = GD.Load<Texture2D>("res://art/arena/dig/normal.jpg"), NormalScale = 1.4f,
            Uv1Triplanar = true, Uv1WorldTriplanar = true, Uv1Scale = new Vector3(0.45f, 0.45f, 0.45f), Roughness = 0.95f,
        };
''' + s[end:]
reps = [
    ("Godot.Basis.FromScale(new Vector3(1.5f, 0.8f * heave, 2.1f))", "Godot.Basis.FromScale(new Vector3(1.15f, 0.75f * heave, 1.6f))"),
]
for a, b in reps:
    assert a in s, a[:60]
    s = s.replace(a, b)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
