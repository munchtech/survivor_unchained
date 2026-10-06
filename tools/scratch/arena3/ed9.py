import os
G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a26767f7f9955cb56\godot"
def rep(path, pairs):
    p = os.path.join(G, path)
    s = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert a in s, (path, a[:70])
        s = s.replace(a, b)
    open(p, 'w', encoding='utf-8').write(s)

rep('logic/Maps/Arenas/Dig.cs', [
# heaps: taller tips
('''            double x = Math.Cos(a) * rr, z = Math.Sin(a) * rr, r = Rng.Range(7, 11);''',
 '''            double x = Math.Cos(a) * rr, z = Math.Sin(a) * rr, r = Rng.Range(6, 9.5);'''),
('''            heaps.Add((x, z, r, Rng.Range(1.6, 2.6)));''',
 '''            heaps.Add((x, z, r, Rng.Range(2.4, 3.6)));'''),
('''            if (d < hp.R) h += hp.H * (1 - MathX.Smoothstep(0, hp.R, d)) * (1 + 0.15 * Noise.Noise(x * 0.4, z * 0.4));''',
 '''            // A tip: a cone at the rock's angle of rest, its top rounded where the last tub
            // was emptied, its flanks lumpy with what rolled down them.
            if (d >= hp.R) continue;
            double k = 1 - d / hp.R;
            h += hp.H * Math.Pow(k, 1.1) * MathX.Smoothstep(0, 0.2, k) * (1 - 0.25 * MathX.Smoothstep(0.75, 1, k))
                * (1 + 0.12 * Noise.Noise(x * 0.4, z * 0.4) + 0.08 * Noise.Noise(x * 1.3 + 5, z * 1.3));'''),
# rust as a mottle
('''        p.L4 = MathX.Smoothstep(0.25, 0.6, Noise.Noise(x * 0.03 - 17, z * 0.03 + 5) + n1 * 0.3 + n2 * 0.25) * 0.6;
        foreach (var bk in bakes)
        {
            double d = MathX.Dist(x, z, bk.X, bk.Z);
            if (d < bk.R + 2) p.L4 = Math.Max(p.L4, (1 - MathX.Smoothstep(bk.R * 0.4, bk.R, d + n1 * 2.5)) * 0.9);
        }''',
 '''        // A mottle, never a blob: small stains a metre or two across, gathered where the broad
        // drifts and the planned patches are, frayed by the clay's own grain.
        double n3 = Noise.Noise(x * 0.42 - 3, z * 0.42 + 8), n4 = Noise.Noise(x * 0.13 + 9, z * 0.13 - 4);
        double drift = MathX.Smoothstep(0.2, 0.6, Noise.Noise(x * 0.03 - 17, z * 0.03 + 5) + n1 * 0.3);
        foreach (var bk in bakes)
        {
            double d = MathX.Dist(x, z, bk.X, bk.Z);
            if (d < bk.R + 2) drift = Math.Max(drift, 1 - MathX.Smoothstep(bk.R * 0.3, bk.R, d + n1 * 2.5));
        }
        p.L4 = MathX.Smoothstep(0.42, 0.62, n4 * 0.6 + n3 * 0.4 + drift * 0.45 - 0.2) * (0.35 + 0.6 * drift);'''),
# grass where nobody walks
('''        if (Drowned) p.Wet = Math.Max(p.Wet, MathX.Smoothstep(0.35, 0.7, Noise.Noise(x * 0.05 - 9, z * 0.05)) * 0.7);
    }''',
 '''        if (Drowned) p.Wet = Math.Max(p.Wet, MathX.Smoothstep(0.35, 0.7, Noise.Noise(x * 0.05 - 9, z * 0.05)) * 0.7);
        // Dry grass where nobody walks: along the working's edge, round the tips' feet, between
        // the stones; never on the rails' bed, in the slurry or the char.
        double feet = 0;
        foreach (var hp in heaps)
        {
            double d = MathX.Dist(x, z, hp.X, hp.Z);
            feet = Math.Max(feet, (1 - MathX.Smoothstep(1.5, 4, Math.Abs(d - hp.R - 1.2))));
        }
        double wild = Math.Max(MathX.Smoothstep(16, 5, inn), feet * 0.9);
        p.Grass = wild * MathX.Smoothstep(0.35, 0.7, Noise.Noise(x * 0.09 + 31, z * 0.09 - 7) * 0.7 + n2 * 0.3 + 0.15)
            * (1 - p.L2 * 0.9) * (1 - p.L3) * (1 - p.Trod) * (1 - p.L5);
    }'''),
])
print('ok')
