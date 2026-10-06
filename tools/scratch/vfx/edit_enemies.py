"""One-off edit: wire the enemy looks into BattleFx."""
G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a63cd93fc73d5ed79\godot"


def edit(path, reps):
    with open(path, encoding="utf-8", newline="") as f:
        t = f.read()
    for a, b in reps:
        if "\r\n" in t:
            a, b = a.replace("\n", "\r\n"), b.replace("\n", "\r\n")
        assert a in t, a[:70]
        t = t.replace(a, b)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(t)


edit(G + r"\src\Fx\BattleFx.cs", [
    ('''                    var col = e.Hostile ? Palette.Telegraph(e.Kind) : Palette.Of(School.Holy).Glow;
                    if (e.Shape == TelegraphShape.Line)''',
     '''                    var col = e.Hostile ? Palette.Telegraph(e.Kind) : e.Faction is { } pf ? People(pf) : Palette.Of(School.Holy).Glow;
                    if (!e.Hostile && e.Faction is { } rf && e.Shape == TelegraphShape.Ring) Rally(e, col);
                    else if (e.Hostile && e.Faction is { } sf && e.Kind == TelegraphKind.Ground && e.Id == -1 && e.Shape == TelegraphShape.Circle) Summoning(e, People(sf));
                    else if (e.Shape == TelegraphShape.Line)'''),
    ('''                    Cam?.AddTrauma((float)Math.Min(0.3, 0.05 + e.Power * 0.1));
                    if (Blast(e.X, e.Z, e.School, r, 0.8f + r * 0.08f)) break;''',
     '''                    Cam?.AddTrauma((float)Math.Min(0.3, 0.05 + e.Power * 0.1));
                    if (e.School == School.Physical && e.Art == null) Slammed(e.X, e.Z, r);
                    if (Blast(e.X, e.Z, e.School, r, 0.8f + r * 0.08f)) break;'''),
    ('''        shades.Begin(); orbs.Begin(); steel.Begin(); axes.Begin(); daggers.Begin(); shards.Begin(); rings.Begin(); kegs.Begin();
        foreach (var p in b.Projectiles.Living())''',
     '''        shades.Begin(); orbs.Begin(); steel.Begin(); axes.Begin(); daggers.Begin(); shards.Begin(); rings.Begin(); kegs.Begin();
        Buffs(b);
        foreach (var p in b.Projectiles.Living())'''),
    ('''            if (!hostile && Flight(p, at + Vector3.Up * 0.55f, heading, now, dt)) continue;''',
     '''            if (!hostile && Flight(p, at + Vector3.Up * 0.55f, heading, now, dt)) continue;
            if (hostile && HostileFlight(p, at + Vector3.Up * 0.3f, heading, (float)now)) continue;'''),
])
print("edited")
