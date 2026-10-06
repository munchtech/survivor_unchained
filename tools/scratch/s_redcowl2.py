PAIRS = [
('''        double nx = e.X + vx / vl * sp * dt, nz = e.Z + vz / vl * sp * dt;
        if (!S.Place.Inside(nx, nz, 1.5) || B.Collision.Blocked(nx, nz, e.Radius)) { side = -side; sideT = 2; nx = e.X; nz = e.Z; }''',
'''        double nx = e.X + vx / vl * sp * dt, nz = e.Z + vz / vl * sp * dt;
        if (!S.Place.Inside(nx, nz, 1.5) || B.Collision.Blocked(nx, nz, e.Radius))
        {
            // Into a corner: he turns, and steps back toward the middle of his yard.
            side = -side; sideT = 2;
            double cx = C.X - e.X, cz = C.Z - e.Z, cl = Math.Max(0.01, Math.Sqrt(cx * cx + cz * cz));
            nx = e.X + cx / cl * sp * dt; nz = e.Z + cz / cl * sp * dt;
            if (B.Collision.Blocked(nx, nz, e.Radius)) { nx = e.X; nz = e.Z; }
        }'''),
('''    protected override void OnHard()
    {
        levyT = 0;
    }''',
'''    /// <summary>All Forty-One: the whole camp turns out. His watchers come in as his lot, the levy forms
    /// again and again, and he hits the harder the longer it goes: it is the end of it, one way or the other.</summary>
    protected override void OnHard()
    {
        levyT = 0;
        foreach (var w in watchers.Where(Here).ToList())
        {
            w.E.Scripted = false;
            w.E.Disposition = Disposition.Hostile;
            w.E.Target = -1;
            lot.Add((w.E, w.Seed));
        }
        watchers.Clear();
    }

    public override void Step(double dt)
    {
        if (Hard && E != null && !Ending) E.Damage *= 1 + 0.015 * dt;
        StepGround(dt);
    }'''),
('''    public override void Step(double dt)
    {
        if (E == null) return;
        watchers.RemoveAll(w => !Here(w));''',
'''    void StepGround(double dt)
    {
        if (E == null) return;
        watchers.RemoveAll(w => !Here(w));'''),
]
