W = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a427a874da78cba8b\godot\logic\Play\Bosses"
def sub(path, old, new, count=1):
    t = open(path, encoding="utf-8").read()
    n = t.count(old)
    assert n == count, (path, old[:60], n)
    t = t.replace(old, new)
    open(path, "w", encoding="utf-8", newline="").write(t)

g = W + r"\GrimtunnelStory.cs"
sub(g, """            if (dazeT <= 0) { e.TakenMul = 1; e.State = EnemyState.Active; }
            return true;""", """            if (dazeT <= 0) { e.TakenMul = 1; e.State = EnemyState.Active; ClimbOut(e); }
            return true;""")
sub(g, """        else Daze(daze, bx, bz);
        if (PhaseIx >= 1) Pit(bx, bz);
    }""", """        else Daze(daze, bx, bz);
        if (PhaseIx >= 1) holeOwed = (bx, bz);
    }

    /// <summary>The hole he came up through, opening when he climbs out of it (from the Collapse on).</summary>
    (double X, double Z)? holeOwed;

    /// <summary>Out of the hole he came up through, onto the ground nearest the lip's middle, and the hole opens
    /// behind him. (It opened under him while he stood dazed in it: he could not walk out of his own sinkhole, a
    /// blade could not reach him across it, and at the lip's edge, behind Snib's heap, he stood in it for minutes
    /// while the night ran on.)</summary>
    void ClimbOut(Enemy e)
    {
        if (holeOwed is not var (hx, hz)) return;
        holeOwed = null;
        double r = 2.3 + e.Radius + 0.4;
        (double X, double Z)? best = null;
        double bd = double.MaxValue;
        for (int k = 0; k < 16; k++)
        {
            double a = k * Math.PI / 8, x = hx + Math.Cos(a) * r, z = hz + Math.Sin(a) * r;
            if (B.Collision.Blocked(x, z, e.Radius) || !S.Place.Inside(x, z, e.Radius + 0.4) || !Inside(x, z, 1.2)) continue;
            double d = Dist(x, z, C.X, C.Z);
            if (d < bd) { bd = d; best = (x, z); }
        }
        best ??= Footing(caving ? caveR - 1.2 : GroundR);
        if (best is var (fx, fz)) DashTo(fx, fz, 0.5);
        Pit(hx, hz);
    }""")

s = W + r"\BossSense.cs"
sub(s, """            case GrimtunnelStory { Flaring: >= 0, Under: false } gl when gl.E.Alive:
                goal = (gl.E.X, gl.E.Z, Math.Max(2.2, Math.Min(reach * 0.7, 6)));
                break;""", """            case GrimtunnelStory { Flaring: >= 0, Under: false } gl when gl.E.Alive:
                goal = (gl.E.X, gl.E.Z, Math.Max(2.2, Math.Min(reach * 0.7, 6)));
                break;
            // Dazed where he came up (the ground marks it safe): in on him while it lasts, as a player is.
            case GrimtunnelStory { Dazed: true, Under: false } gd when gd.E.Alive:
                goal = (gd.E.X, gd.E.Z, Math.Max(2.2, Math.Min(reach * 0.7, 6)));
                break;""")
print("ok")
