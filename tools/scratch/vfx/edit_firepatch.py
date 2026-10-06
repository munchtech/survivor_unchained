p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a191ed81e2df462cf\godot\src\Fx\BattleFx.Skills.cs"
s = open(p, encoding="utf-8").read()
reps = [
    ("""        if (inside == Inside.Runes) RuneRing(z.Id, at, r, fade * hush, now);""",
     """        if (inside == Inside.Runes) RuneRing(z.Id, at, r, fade * hush, now);
        else if (inside == Inside.Embers) FirePatch(z.Id, at, r, fade);"""),
    ("""    void GroundsGone(System.Collections.Generic.HashSet<int> alive)
    {""",
     """    readonly System.Collections.Generic.Dictionary<int, (MeshInstance3D Mesh, ShaderMaterial Mat)> firePatches = new();

    /// <summary>Ground left burning: low tongues of flame standing round its edge and lapping in
    /// (the rise's wall in small, shaders/fire_wall.gdshader), so it burns over a packed crowd's
    /// feet where its embers on the ground are hidden. (A firepot's burst alone was a soft orange
    /// blob.)</summary>
    void FirePatch(int id, Vector3 ground, float r, float strength)
    {
        if (!firePatches.TryGetValue(id, out var patch))
        {
            var mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/fire_wall.gdshader") };
            mat.SetShaderParameter("seed", R() * 100);
            mat.SetShaderParameter("segs", 48f);
            mat.SetShaderParameter("cells", Mathf.Max(6, Mathf.Round(Mathf.Tau * r * 0.8f / 0.42f)));
            var mesh = new MeshInstance3D
            {
                Mesh = Kept("firecards48", () => FireCards(48)), MaterialOverride = mat, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
                CustomAabb = new Aabb(new Vector3(-1.5f, -0.5f, -1.5f), new Vector3(3, 2, 3)),
            };
            AddChild(mesh);
            firePatches[id] = patch = (mesh, mat);
        }
        patch.Mesh.Position = ground - Vector3.Up * 0.05f;
        patch.Mesh.Scale = new Vector3(r * 0.8f, 0.75f + 0.1f * r, r * 0.8f);
        patch.Mat.SetShaderParameter("burn", strength);
    }

    void GroundsGone(System.Collections.Generic.HashSet<int> alive)
    {
        if (firePatches.Count > 0)
        {
            var out1 = new System.Collections.Generic.List<int>();
            foreach (var (id, patch) in firePatches)
                if (!alive.Contains(id)) { patch.Mesh.QueueFree(); out1.Add(id); }
            foreach (var id in out1) firePatches.Remove(id);
        }"""),
]
for a, b in reps:
    assert a in s, a[:60]
    s = s.replace(a, b)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
