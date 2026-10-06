from ed import sub
sub('src/Ui/Forge.cs', [
# A real flare over the row, additive; bigger sparks.
("""            row.Modulate = new Color(1.9f, 1.45f, 1.05f);
            row.CreateTween().TweenProperty(row, "modulate", Colors.White, 0.7).SetTrans(Tween.TransitionType.Quad).SetEase(Tween.EaseType.Out);
            Sparks(row, badge.Position + badge.Size / 2, now.Verb == Verb.Cage);""",
"""            // The row flares as the iron does under the hammer, and cools.
            var flare = new Panel { MouseFilter = MouseFilterEnum.Ignore, Material = new CanvasItemMaterial { BlendMode = CanvasItemMaterial.BlendModeEnum.Add } };
            flare.AddThemeStyleboxOverride("panel", Style.Box(new Color(1f, 0.55f, 0.18f, 0.5f), new Color(1f, 0.85f, 0.5f, 0.9f), 2, 5, 0));
            row.AddChild(flare);
            flare.CreateTween().TweenProperty(flare, "modulate:a", 0f, 0.9).SetTrans(Tween.TransitionType.Quad).SetEase(Tween.EaseType.Out);
            flare.GetTree().CreateTimer(1.0).Timeout += () => { if (IsInstanceValid(flare)) flare.QueueFree(); };
            Sparks(row, badge.Position + badge.Size / 2, now.Verb == Verb.Cage);"""),
("""        var p = new CpuParticles2D
        {
            Amount = ember ? 46 : 38, Lifetime = 0.75, OneShot = true, Explosiveness = 0.92f, Emitting = false,
            Direction = new Vector2(0.3f, -1), Spread = 70, Gravity = new Vector2(0, ember ? 160 : 620),
            InitialVelocityMin = 140, InitialVelocityMax = 420, DampingMin = 20, DampingMax = 60,
            ScaleAmountMin = 1.6f, ScaleAmountMax = 3.6f, ColorRamp = ramp, Position = local, ZIndex = 30,
        };""",
"""        var p = new CpuParticles2D
        {
            Amount = ember ? 70 : 64, Lifetime = 0.95, OneShot = true, Explosiveness = 0.95f, Emitting = false,
            Direction = new Vector2(0.35f, -1), Spread = 75, Gravity = new Vector2(0, ember ? 140 : 700),
            InitialVelocityMin = 200, InitialVelocityMax = 560, DampingMin = 30, DampingMax = 80,
            ScaleAmountMin = 2.6f, ScaleAmountMax = 5.6f, ColorRamp = ramp, Position = local, ZIndex = 30,
            Material = new CanvasItemMaterial { BlendMode = CanvasItemMaterial.BlendModeEnum.Add },
        };"""),
# The gauge: a preview waits until the burn has played.
("""    public void Preview(int lo, int hi, bool grows = false)
    {
        if (lo == 0 && hi == 0) { Clear(); return; }""",
"""    public void Preview(int lo, int hi, bool grows = false)
    {
        if (lo == 0 && hi == 0) { Clear(); return; }
        // The heat a craft just took is seen go first; what the next would take, after.
        if (burnFrom >= 0) { pending = (lo, hi, grows); return; }"""),
("""    public void Clear()
    {
        if (!preview) return;""",
"""    public void Clear()
    {
        pending = null;
        if (!preview) return;"""),
("""    int burnFrom = -1;
    double burnT;""",
"""    int burnFrom = -1;
    double burnT;
    (int Lo, int Hi, bool Grows)? pending;"""),
("""        if (burnFrom >= 0)
        {
            burnT += delta;
            if (burnT > 1.1) burnFrom = -1;
            cells.QueueRedraw();
        }""",
"""        if (burnFrom >= 0)
        {
            burnT += delta;
            if (burnT > 1.1)
            {
                burnFrom = -1;
                if (pending is { } p) { pending = null; Preview(p.Lo, p.Hi, p.Grows); }
            }
            cells.QueueRedraw();
        }"""),
("""    public void Burn(int before)
    {
        if (before == heat) return;
        burnFrom = before;""",
"""    public void Burn(int before)
    {
        if (before == heat) return;
        // A preview already up (the focus stayed on the press) waits its turn.
        if (preview) { pending = (lo, hi, grows); preview = false; Say(); }
        burnFrom = before;"""),
])
