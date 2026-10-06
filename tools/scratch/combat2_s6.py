W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/godot/"
FILES = {
    W + "balance/Harness/Pilot.cs": [
        ("""    public static (double X, double Z) Steer(Battle b, bool deft = false, ArenaBoss? boss = null)
    {""", """    /// <param name="onward">On a map: where the way goes on. Resting packs are left to rest, what
    /// lies about is picked up, and with nothing roused near, the hands walk on.</param>
    public static (double X, double Z) Steer(Battle b, bool deft = false, ArenaBoss? boss = null, (double X, double Z)? onward = null)
    {"""),
        ("""            if (!e.Alive || e.Disposition != Disposition.Hostile || e.State == EnemyState.Dying) continue;
            double d = (e.X - p.X) * (e.X - p.X) + (e.Z - p.Z) * (e.Z - p.Z);
            if (d < nd) { nd = d; nearest = e; }""", """            if (!e.Alive || e.Disposition != Disposition.Hostile || e.State == EnemyState.Dying) continue;
            if (onward != null && e.Wake > 0 && !e.Roused) continue;
            double d = (e.X - p.X) * (e.X - p.X) + (e.Z - p.Z) * (e.Z - p.Z);
            if (d < nd) { nd = d; nearest = e; }"""),
        ("""            if (!k.Alive || k.Kind != PickupKind.Ember) continue;""", """            if (!k.Alive || !(k.Kind == PickupKind.Ember || onward != null && k.Kind is PickupKind.Item or PickupKind.Material or PickupKind.Gold or PickupKind.Chest)) continue;"""),
        ("""        double near = nearest == null ? double.MaxValue : Math.Sqrt(nd);""", """        double near = nearest == null ? double.MaxValue : Math.Sqrt(nd);
        // On a map, one that has wandered far off is not followed into the trees.
        if (onward != null && near > 22) { nearest = null; near = double.MaxValue; }"""),
        ("""        else { mx = -p.X; mz = -p.Z; }
        double far = Math.Sqrt(p.X * p.X + p.Z * p.Z);
        if (far > 60) { mx = mx * 0.3 - p.X / far; mz = mz * 0.3 - p.Z / far; }""", """        else if (onward is var (ox, oz)) { mx = ox - p.X; mz = oz - p.Z; }
        else { mx = -p.X; mz = -p.Z; }
        double far = Math.Sqrt(p.X * p.X + p.Z * p.Z);
        if (far > 60 && onward == null) { mx = mx * 0.3 - p.X / far; mz = mz * 0.3 - p.Z / far; }"""),
    ],
}
