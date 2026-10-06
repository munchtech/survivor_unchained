p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a191ed81e2df462cf\godot\src\Fx\BattleFx.Rise.cs"
s = open(p, encoding="utf-8").read()
reps = [
    ("""            wallMesh = new MeshInstance3D
            {
                Mesh = new CylinderMesh { TopRadius = 1, BottomRadius = 1, Height = 1, RadialSegments = 160, Rings = 1, CapTop = false, CapBottom = false },
                MaterialOverride = wallMat, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
            };""",
     """            wallMesh = new MeshInstance3D
            {
                Mesh = FireCards(WallCards),
                MaterialOverride = wallMat, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
                CustomAabb = new Aabb(new Vector3(-1.5f, -0.5f, -1.5f), new Vector3(3, 2, 3)),
            };
            wallMat.SetShaderParameter("segs", (float)WallCards);"""),
    ("""            wallMesh.Position = at + Vector3.Up * (high / 2 - 0.05f);
            wallMesh.Scale = new Vector3(reach, high, reach);""",
     """            wallMesh.Position = at - Vector3.Up * 0.05f;
            wallMesh.Scale = new Vector3(reach, high, reach);"""),
    ("""    /// <summary>The wall of flame at its tallest, and how far apart its tongues stand (about).</summary>
    const float WallHigh = 2.8f, WallTongue = 0.85f;""",
     """    /// <summary>The wall of flame at its tallest, and how far apart its tongues stand (about).</summary>
    const float WallHigh = 2.8f, WallTongue = 0.85f;
    /// <summary>The cards the wall is drawn on, round the ring (fire_wall.gdshader).</summary>
    const int WallCards = 160;

    /// <summary>The wall's ring of cards: each a quad standing on the unit ring at its place round it,
    /// turned to the camera in the shader (UV: across -1..1 and up 0..1; UV2.x: its place, 0..1).</summary>
    static ArrayMesh FireCards(int n)
    {
        var verts = new Vector3[n * 4];
        var uv = new Vector2[n * 4];
        var uv2 = new Vector2[n * 4];
        var idx = new int[n * 6];
        for (int i = 0; i < n; i++)
        {
            float a = i * Mathf.Tau / n;
            var at = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
            for (int k = 0; k < 4; k++)
            {
                float x = k is 0 or 3 ? -1 : 1, y = k >= 2 ? 1 : 0;
                verts[i * 4 + k] = at + Vector3.Up * y;
                uv[i * 4 + k] = new Vector2(x, y);
                uv2[i * 4 + k] = new Vector2(i / (float)n, 0);
            }
            int b = i * 4;
            idx[i * 6] = b; idx[i * 6 + 1] = b + 1; idx[i * 6 + 2] = b + 2;
            idx[i * 6 + 3] = b; idx[i * 6 + 4] = b + 2; idx[i * 6 + 5] = b + 3;
        }
        var arrays = new Godot.Collections.Array();
        arrays.Resize((int)Mesh.ArrayType.Max);
        arrays[(int)Mesh.ArrayType.Vertex] = verts;
        arrays[(int)Mesh.ArrayType.TexUV] = uv;
        arrays[(int)Mesh.ArrayType.TexUV2] = uv2;
        arrays[(int)Mesh.ArrayType.Index] = idx;
        var mesh = new ArrayMesh();
        mesh.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arrays);
        return mesh;
    }"""),
]
for a, b in reps:
    assert a in s, a[:70]
    s = s.replace(a, b)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
