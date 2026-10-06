PAIRS = [
('''    bool OnBossGround() => BossGround is { } g && B != null && Fight.Place.In(g, B.Player.X, B.Player.Z, 1.5);''',
'''    /// <summary>On it, and through its gate: on the same side of every gate into it as its start, and clear of
    /// it (a gate's neck belongs to the space it opens, so in the neck she may still be on the near side).</summary>
    bool OnBossGround()
    {
        if (BossGround is not { } g || B == null) return false;
        var p = B.Player;
        if (!Fight.Place.In(g, p.X, p.Z, 1.0)) return false;
        var (sx, sz) = Fight.Place[Fight.BossStart];
        foreach (var gate in Fight.Place.Gates.Where(q => q.Into == g))
        {
            double lx = gate.X1 - gate.X0, lz = gate.Z1 - gate.Z0;
            double her = lx * (p.Z - gate.Z0) - lz * (p.X - gate.X0), start = lx * (sz - gate.Z0) - lz * (sx - gate.X0);
            if (Math.Sign(her) != Math.Sign(start) || SegDist(p.X, p.Z, gate.X0, gate.Z0, gate.X1, gate.Z1) < 2.5) return false;
        }
        return true;
    }'''),
('''        // Clear of the gates, so they shut behind her and not on her (posts dropped on her feet put her
        // back out on the wrong side).
        var p = B.Player;
        if (Fight.Place.Gates.Any(g => g.Into == ground && SegDist(p.X, p.Z, g.X0, g.Z0, g.X1, g.Z1) < 4)) return;
        shutBehind = true;''', '''        shutBehind = true;'''),
]
