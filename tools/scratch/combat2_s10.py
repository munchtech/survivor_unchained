W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/godot/"
FILES = {
    W + "balance/Harness/Pilot.cs": [
        ("""            if (e.Def.Ranged == null || e.Elite || e.Disposition != Disposition.Hostile || e.State == EnemyState.Dying) continue;""",
         """            if (e.Def.Ranged == null || e.Elite || e.Disposition != Disposition.Hostile || e.State == EnemyState.Dying || e.Wake > 0 && !e.Roused) continue;"""),
    ],
    W + "balance/Harness/MapSim.cs": [
        ("""            var (mx, mz) = Pilot.Steer(b, spec.Deft, zone.BossScript, onward);""",
         """            var (mx, mz) = Pilot.Steer(b, spec.Deft, zone.BossScript, onward);
            // Held on one spot with nothing roused (a pickup out of reach, a corner): walk on.
            if ((int)(t / 4) != (int)((t + Dt) / 4))
            {
                stuck = Dist(p.X, p.Z, lastX, lastZ) < 1.5 && !b.Enemies.Living().Any(e => e.Disposition == Disposition.Hostile && (e.Wake == 0 || e.Roused) && Dist(e.X, e.Z, p.X, p.Z) < 16) ? 5 : stuck;
                (lastX, lastZ) = (p.X, p.Z);
            }
            if (stuck > 0)
            {
                stuck -= Dt;
                (mx, mz) = (onward.X - p.X, onward.Z - p.Z);
                if (b.Collision.Blocked(p.X + mx * 0.05, p.Z + mz * 0.05, p.Radius)) (mx, mz) = (-mz, mx);
                double ml = Math.Max(1e-6, Math.Sqrt(mx * mx + mz * mz));
                (mx, mz) = (mx / ml, mz / ml);
            }"""),
        ("""        double t = 0, lastKill = 0, lastPack = 0;""", """        double t = 0, lastKill = 0, lastPack = 0, stuck = 0, lastX = p.X, lastZ = p.Z;"""),
    ],
}
