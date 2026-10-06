W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/godot/"
FILES = {
    W + "logic/Sim/Weapons.cs": [
        ("""        for (int i = 0; i < n; i++) Launch(b, w, a0 + (i - (n - 1) / 2.0) * spread, target: t.Id);
        // Arrowfall: the volley also rains on the densest knot of the crowd.""",
         """        for (int i = 0; i < n; i++) Launch(b, w, a0 + (i - (n - 1) / 2.0) * spread, target: t.Id);
        // The Ravine (a Mark): a second volley at the farthest in reach, a part as strong.
        if (w.Id == "volley" && b.Marked(Marks.Ravine, out double ravine) && b.FarthestHostile(p.X, p.Z, RangeOf(w)) is { } far && far != t)
        {
            double af = Math.Atan2(far.Z - p.Z, far.X - p.X), k = Marks.Lerp(0.2, 0.9, ravine);
            for (int i = 0; i < n; i++)
                if (Launch(b, w, af + (i - (n - 1) / 2.0) * spread, target: far.Id) is { } pr) pr.Damage *= k;
        }
        // Arrowfall: the volley also rains on the densest knot of the crowd."""),
        ("""        int n = CountOf(b, w);
        double life = DurationOf(b, w, w.Num(s => s.Duration) ?? 3);
        double radius = AreaOf(b, w, w.Num(s => s.OrbitRadius) ?? 2);""",
         """        int n = CountOf(b, w);
        // The Gyre (a Mark): an axe more for every few close by, to three more.
        if (w.Id == "axe_gyre" && b.Marked(Marks.Gyre, out double gyre))
            n += Math.Min(3, (int)(b.HostilesInRadius(b.Player.X, b.Player.Z, 5).Count / Marks.Lerp(6, 3, gyre)));
        double life = DurationOf(b, w, w.Num(s => s.Duration) ?? 3);
        double radius = AreaOf(b, w, w.Num(s => s.OrbitRadius) ?? 2);"""),
        ("""            pr.GroundOnHit = w.GroundOf;""",
         """            pr.GroundOnHit = w.GroundOf;
            // The Falling Star (a Mark): the cinder's blast leaves the ground burning.
            if (pr.GroundOnHit == null && w.Id == "cinderfall" && b.Marked(Marks.FallingStar, out double star))
                pr.GroundOnHit = new GroundSpec(1.8, Marks.Lerp(1, 4, star), 0.25);"""),
    ],
    W + "logic/Sim/Battle.cs": [
        ("""        var w = new WeaponInst(id, rank, Weapons.Count);
        Weapons.Add(w);""",
         """        var w = new WeaponInst(id, rank, Weapons.Count);
        if (SkillMods.TryGetValue(id, out var sm)) Marks.Fold(w.Mods, sm);
        Weapons.Add(w);"""),
        ("""        Events.Emit(new Ev.Dash { X0 = x0, Z0 = z0, X1 = x0 + p.DashDX * Abilities.Dash.Distance, Z1 = z0 + p.DashDZ * Abilities.Dash.Distance });
        Fire(TriggerEvent.Dash, new ProcCtx { X = p.X, Z = p.Z });""",
         """        Events.Emit(new Ev.Dash { X0 = x0, Z0 = z0, X1 = x0 + p.DashDX * Abilities.Dash.Distance, Z1 = z0 + p.DashDZ * Abilities.Dash.Distance });
        Fire(TriggerEvent.Dash, new ProcCtx { X = p.X, Z = p.Z });
        OpenGate(x0, z0);"""),
    ],
}
