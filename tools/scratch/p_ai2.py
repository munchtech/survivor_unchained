PAIRS = [
("""                // Lead the target a little; lobs are slow.
                double lead = tgt.Player ? 0.45 : 0;
                double lx = tx + p.Vx * lead + (b.Rng.Next() - 0.5) * 1.2;
                double lz = tz + p.Vz * lead + (b.Rng.Next() - 0.5) * 1.2;""",
"""                // Lead the target a little; lobs are slow. Several at once fan out across the
                // line to it, so the gaps between them can be stood in.
                double lead = tgt.Player ? 0.45 : 0;
                double ax = tx, az = tz;
                if (n > 1)
                {
                    double a0 = Math.Atan2(tz - e.Z, tx - e.X) + (i - (n - 1) / 2.0) * (r.Spread ?? 0.3), d0 = Dist(tx, tz, e.X, e.Z);
                    ax = e.X + Math.Cos(a0) * d0; az = e.Z + Math.Sin(a0) * d0;
                }
                double lx = ax + p.Vx * lead + (b.Rng.Next() - 0.5) * 1.2;
                double lz = az + p.Vz * lead + (b.Rng.Next() - 0.5) * 1.2;"""),
]
