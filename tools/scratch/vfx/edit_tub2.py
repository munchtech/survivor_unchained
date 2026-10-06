p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a191ed81e2df462cf\godot\src\Fx\MineTub.cs"
s = open(p, encoding="utf-8").read()
start = s.index("        // Heaped with spoil, a few lumps of ember-stone among it still warm.")
end = s.index("        return root;\n    }\n\n    static void Materials()")
s = s[:start] + '''        // Heaped with spoil above its lip, a few small lumps of ember-stone in it still warm.
        for (int i = 0; i < 18; i++)
        {
            float x = (float)(r.NextDouble() * 2 - 1) * (TopX - 0.14f), z = (float)(r.NextDouble() * 2 - 1) * (TopZ - 0.16f);
            float rr = Mathf.Min(1, Mathf.Sqrt(x * x / (TopX * TopX) + z * z / (TopZ * TopZ)));
            float s = 0.12f + (float)r.NextDouble() * 0.12f;
            root.AddChild(new MeshInstance3D
            {
                Mesh = new SphereMesh { Radius = s, Height = s * 1.5f, RadialSegments = 5, Rings = 3 },
                MaterialOverride = spoil,
                Position = new Vector3(x, Lip - 0.1f + 0.2f * (1 - rr * rr) + (float)r.NextDouble() * 0.04f, z),
                Rotation = new Vector3((float)r.NextDouble() * 3, (float)r.NextDouble() * 3, (float)r.NextDouble() * 3),
            });
        }
        for (int i = 0; i < 3; i++)
        {
            float x = (float)(r.NextDouble() * 2 - 1) * (TopX - 0.25f), z = (float)(r.NextDouble() * 2 - 1) * (TopZ - 0.3f);
            root.AddChild(new MeshInstance3D
            {
                Mesh = new SphereMesh { Radius = 0.07f, Height = 0.1f, RadialSegments = 5, Rings = 3 },
                MaterialOverride = ember, Position = new Vector3(x, Lip + 0.05f, z),
                Rotation = new Vector3((float)r.NextDouble() * 3, (float)r.NextDouble() * 3, 0),
            });
        }
        // The tub's lamp on its post at the front, hooded: the Dig's tubs run lit, so the rails' dark
        // shows one coming (and it is a lamp, in a hole full of lamps).
        var post = new MeshInstance3D { Mesh = new BoxMesh { Size = new Vector3(0.04f, 0.5f, 0.04f) }, MaterialOverride = iron, Position = new Vector3(TopX - 0.06f, Lip + 0.22f, TopZ + 0.02f) };
        root.AddChild(post);
        root.AddChild(new MeshInstance3D { Mesh = new BoxMesh { Size = new Vector3(0.16f, 0.04f, 0.16f) }, MaterialOverride = iron, Position = new Vector3(TopX - 0.06f, Lip + 0.6f, TopZ + 0.02f) });
        root.AddChild(new MeshInstance3D
        {
            Mesh = new BoxMesh { Size = new Vector3(0.11f, 0.15f, 0.11f) }, MaterialOverride = glass,
            Position = new Vector3(TopX - 0.06f, Lip + 0.5f, TopZ + 0.02f),
        });
        root.AddChild(new OmniLight3D
        {
            Position = new Vector3(TopX - 0.06f, Lip + 0.5f, TopZ + 0.1f), LightColor = new Color(1.0f, 0.62f, 0.3f),
            LightEnergy = 1.4f, OmniRange = 4.5f, OmniAttenuation = 1.6f, ShadowEnabled = false,
        });
''' + s[end:]
reps = [
    ("    static Material? rust, iron, spoil, ember;", "    static Material? rust, iron, spoil, ember, glass;"),
    ("""        ember = new StandardMaterial3D
        {
            AlbedoColor = new Color(0.25f, 0.08f, 0.03f), Roughness = 0.8f,
            EmissionEnabled = true, Emission = new Color(1.0f, 0.32f, 0.06f), EmissionEnergyMultiplier = 1.1f,
        };""",
     """        ember = new StandardMaterial3D
        {
            AlbedoColor = new Color(0.25f, 0.08f, 0.03f), Roughness = 0.8f,
            EmissionEnabled = true, Emission = new Color(1.0f, 0.28f, 0.05f), EmissionEnergyMultiplier = 0.9f,
        };
        glass = new StandardMaterial3D
        {
            AlbedoColor = new Color(0.4f, 0.25f, 0.1f), Roughness = 0.4f,
            EmissionEnabled = true, Emission = new Color(1.0f, 0.6f, 0.25f), EmissionEnergyMultiplier = 1.2f,
        };"""),
    ("spoil = new StandardMaterial3D { AlbedoColor = new Color(0.12f, 0.1f, 0.085f), Roughness = 0.95f };",
     "spoil = new StandardMaterial3D { AlbedoColor = new Color(0.2f, 0.16f, 0.12f), Roughness = 0.95f };"),
]
for a, b in reps:
    assert a in s, a[:60]
    s = s.replace(a, b)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
