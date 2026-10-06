p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a191ed81e2df462cf\godot\src\Fx\BattleFx.Skills.cs"
s = open(p, encoding="utf-8").read()
reps = [
    ("""        g.Fill.Decal.Rotation = new Vector3(0, (float)(now * turn + z.Id * 1.7), 0);
        // What lives in it, sparse.""",
     """        g.Fill.Decal.Rotation = new Vector3(0, (float)(now * turn + z.Id * 1.7), 0);
        if (inside == Inside.Runes) RuneRing(z.Id, at, r, fade * hush, now);
        // What lives in it, sparse."""),
    ("""    void GroundsGone(System.Collections.Generic.HashSet<int> alive)
    {
        if (grounds.Count == 0) return;""",
     """    readonly System.Collections.Generic.Dictionary<int, (MeshInstance3D Mesh, ShaderMaterial Mat)> runeRings = new();

    /// <summary>A hallowed ground's ring of runes in the air at her waist, at its edge, turning
    /// slowly (shaders/rune_ring.gdshader): seen over a packed crowd as its ground is not.</summary>
    void RuneRing(int id, Vector3 ground, float r, float strength, double now)
    {
        if (!runeRings.TryGetValue(id, out var ring))
        {
            var mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/rune_ring.gdshader") };
            mat.SetShaderParameter("seed", (float)(id % 97));
            var mesh = new MeshInstance3D { Mesh = new PlaneMesh { Size = new Vector2(2, 2) }, MaterialOverride = mat, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off };
            AddChild(mesh);
            runeRings[id] = ring = (mesh, mat);
        }
        ring.Mesh.Visible = true;
        // Runes about half a metre across whatever the reach (an integer, so the band closes).
        ring.Mat.SetShaderParameter("count", Mathf.Max(16, Mathf.Round(Mathf.Tau * r * 0.9f / 0.55f)));
        ring.Mat.SetShaderParameter("lit", strength * 0.5f);
        ring.Mesh.Position = ground + Vector3.Up * 0.95f;
        ring.Mesh.Rotation = new Vector3(0, (float)(-now * 0.18 + id * 0.7), 0);
        ring.Mesh.Scale = new Vector3(r, 1, r);
    }

    void GroundsGone(System.Collections.Generic.HashSet<int> alive)
    {
        foreach (var (id, ring) in runeRings)
            if (!alive.Contains(id)) ring.Mesh.Visible = false;
        if (grounds.Count == 0) return;"""),
]
for a, b in reps:
    assert a in s, a[:60]
    s = s.replace(a, b)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
