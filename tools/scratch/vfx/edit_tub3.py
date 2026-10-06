p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a191ed81e2df462cf\godot\src\Fx\MineTub.cs"
s = open(p, encoding="utf-8").read()
reps = [
    # Angular chunks, not soft blobs: a smooth-shaded low sphere read as a pillow.
    ("""            float s = 0.12f + (float)r.NextDouble() * 0.12f;
            root.AddChild(new MeshInstance3D
            {
                Mesh = new SphereMesh { Radius = s, Height = s * 1.5f, RadialSegments = 5, Rings = 3 },""",
     """            float s = 0.12f + (float)r.NextDouble() * 0.12f;
            root.AddChild(new MeshInstance3D
            {
                Mesh = new BoxMesh { Size = new Vector3(s * 1.6f, s * (0.8f + (float)r.NextDouble() * 0.6f), s * (1.0f + (float)r.NextDouble() * 0.8f)) },"""),
    ("""                Mesh = new SphereMesh { Radius = 0.07f, Height = 0.1f, RadialSegments = 5, Rings = 3 },
                MaterialOverride = ember, Position = new Vector3(x, Lip + 0.05f, z),""",
     """                Mesh = new BoxMesh { Size = new Vector3(0.11f, 0.08f, 0.09f) },
                MaterialOverride = ember, Position = new Vector3(x, Lip + 0.06f, z),"""),
    # Rust in broad patches over dark iron, not a speckle.
    ("""            Noise = new FastNoiseLite { Seed = 31, Frequency = 0.02f, FractalOctaves = 5 },
            ColorRamp = new Gradient
            {
                Colors = new[] { new Color(0.09f, 0.085f, 0.08f), new Color(0.16f, 0.1f, 0.07f), new Color(0.34f, 0.16f, 0.07f), new Color(0.42f, 0.22f, 0.1f) },
                Offsets = new[] { 0f, 0.42f, 0.66f, 1f },
            },""",
     """            Noise = new FastNoiseLite { Seed = 31, Frequency = 0.009f, FractalOctaves = 4 },
            ColorRamp = new Gradient
            {
                Colors = new[] { new Color(0.08f, 0.075f, 0.07f), new Color(0.13f, 0.1f, 0.08f), new Color(0.26f, 0.13f, 0.065f), new Color(0.34f, 0.17f, 0.08f) },
                Offsets = new[] { 0f, 0.5f, 0.72f, 1f },
            },"""),
]
for a, b in reps:
    assert a in s, a[:60]
    s = s.replace(a, b)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
