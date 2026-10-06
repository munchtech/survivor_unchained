import os
G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a3058a45eee41d695\godot"


def edit(rel, pairs):
    p = os.path.join(G, rel)
    s = open(p, encoding="utf-8").read()
    for old, new in pairs:
        assert s.count(old) == 1, (rel, s.count(old), old[:70])
        s = s.replace(old, new, 1)
    open(p, "w", encoding="utf-8", newline="").write(s)


edit(r"logic\Play\Zones\Prologue.cs", [
('''        grim.State = EnemyState.Surfacing; grim.StateT = 0.55;''',
'''        grim.State = EnemyState.Surfacing; grim.StateT = 0.55;
        grimByCine = true;'''),
('''    void GrimDown()
    {''',
'''    bool grimByCine;

    /// <summary>Gone down the hole: nothing of him left above the mud.</summary>
    void GrimGone()
    {
        GrimDown();
        if (grim != null) { if (grim.Alive) B?.Enemies.Release(grim); grim = null; }
    }

    void GrimDown()
    {'''),
('''        wardenInCine = false;
        GrimDown();
        if (grim != null) { if (grim.Alive) B?.Enemies.Release(grim); grim = null; }
        shown.Add("grimGone");''',
'''        wardenInCine = false;
        GrimGone();
        shown.Add("grimGone");'''),
('''            case "grim_down": GrimDown(); break;''',
'''            case "grim_down": GrimDown(); break;
            case "grim_gone": GrimGone(); break;'''),
('''        if (victoryByCine && grim is { Alive: true, State: EnemyState.Surfacing } gs)''',
'''        if (grimByCine && grim is { Alive: true, State: EnemyState.Surfacing } gs)'''),
])

edit(r"src\Actors\BossViews.cs", [
('''        AddChild(ball);
        light = new OmniLight3D { LightColor = new Color(color), OmniRange = 14, OmniAttenuation = 1.3f };''',
'''        AddChild(ball);
        // A soft halo about it, as a bright thing has in mist.
        AddChild(new MeshInstance3D
        {
            Mesh = new QuadMesh { Size = Vector2.One * (float)size * 7 },
            CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
            MaterialOverride = new StandardMaterial3D
            {
                ShadingMode = BaseMaterial3D.ShadingModeEnum.Unshaded, Transparency = BaseMaterial3D.TransparencyEnum.Alpha,
                BlendMode = BaseMaterial3D.BlendModeEnum.Add, BillboardMode = BaseMaterial3D.BillboardModeEnum.Enabled,
                AlbedoTexture = new GradientTexture2D
                {
                    Gradient = new Gradient { Colors = [new Color(1, 1, 1, 1), new Color(1, 1, 1, 0.2f), new Color(1, 1, 1, 0)], Offsets = [0, 0.2f, 1] },
                    Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.5f, 0.5f), FillTo = new Vector2(1, 0.5f), Width = 64, Height = 64,
                },
                AlbedoColor = new Color(new Color(color), 0.5f),
            },
        });
        light = new OmniLight3D { LightColor = new Color(color), OmniRange = 14, OmniAttenuation = 1.3f };'''),
])
print("ok")
