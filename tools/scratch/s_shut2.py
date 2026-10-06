PAIRS = [
('''        var ground = BossGround;
        if (ground == null || !OnBossGround()) return;
        shutBehind = true;''',
'''        var ground = BossGround;
        if (ground == null || !OnBossGround()) return;
        // Clear of the gates, so they shut behind her and not on her (posts dropped on her feet put her
        // back out on the wrong side).
        var p = B.Player;
        if (Fight.Place.Gates.Any(g => g.Into == ground && SegDist(p.X, p.Z, g.X0, g.Z0, g.X1, g.Z1) < 4)) return;
        shutBehind = true;'''),
('''    bool shutBehind;''', '''    bool shutBehind;

    static double SegDist(double x, double z, double x0, double z0, double x1, double z1)
    {
        double lx = x1 - x0, lz = z1 - z0, len2 = lx * lx + lz * lz;
        double t = len2 > 0 ? Math.Clamp(((x - x0) * lx + (z - z0) * lz) / len2, -0.3, 1.3) : 0;
        return Dist(x, z, x0 + lx * t, z0 + lz * t);
    }'''),
]
