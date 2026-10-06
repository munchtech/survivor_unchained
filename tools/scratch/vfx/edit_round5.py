"""One-off edit: round 5 fixes from the arena runs."""
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


edit(G + r"\src\Fx\BattleFx.Skills.cs", [
    # The survivor's own marks: a thin ring, never the filling disc a threat has.
    ('''            if (art != "slash_quake") Ring(e.X, e.Z, r, pal.Glow * 0.35f, (float)e.Delay, true);''',
     '''            if (art != "slash_quake") Ring(e.X, e.Z, r, pal.Glow * 0.3f, (float)e.Delay, false);'''),
    # Gale Chakram: a short curl of wind, not a white beam.
    ('''                Ribbons.Feed(key, at, 0.55f * s, 0.25f, art == "chakram_hail" ? Hdr("#bfe6ff", 1f) : Hdr("#e8f8f0", 1f), art == "chakram_razor" ? 1.6f : 1.1f,''',
     '''                Ribbons.Feed(key, at, 0.45f * s, 0.13f, art == "chakram_hail" ? Hdr("#8fd0ff", 1f) : Hdr("#a8f0d0", 1f), art == "chakram_razor" ? 1.4f : 1f,'''),
    # Umbral bolt: a short wisp (long, it read as a violet beam).
    ('''                Ribbons.Feed(key, at, 0.62f * s, ruin ? 0.55f : 0.42f, new Color(rim.R / 3, rim.G / 3, rim.B / 3), 1.6f, Ribbons.Style.Wisp);''',
     '''                Ribbons.Feed(key, at, 0.5f * s, ruin ? 0.28f : 0.18f, new Color(rim.R / 3, rim.G / 3, rim.B / 3), 1.6f, Ribbons.Style.Wisp);'''),
    # The moon's stardust violet, not cream.
    ('''            "moon" or "moon_brand" => ("moon_burst", new Color(0.9f, 0.85f, 1.1f, 0.85f)),''',
     '''            "moon" or "moon_brand" => ("moon_burst", new Color(0.55f, 0.45f, 1.05f, 0.75f)),'''),
    ('''                Books.Spawn("moon_burst", ground + Vector3.Up * 0.6f, r * 0.8f, 0.7f, new Color(0.95f, 0.9f, 1.15f, 0.9f), flat: true, sizeEnd: r * 2.6f);''',
     '''                Books.Spawn("moon_burst", ground + Vector3.Up * 0.6f, r * 0.8f, 0.7f, new Color(0.6f, 0.5f, 1.1f, 0.85f), flat: true, sizeEnd: r * 2.6f);'''),
    # Reaving Arc: a shallower smear, so the crowd inside reads.
    ('''                Blades.Add(at, facing, r, Mathf.Tau * 1.02f, false, 0.16f, 0.24f, hue, 0.4f * Mathf.Min(g, 1.3f));''',
     '''                Blades.Add(at, facing, r, Mathf.Tau * 1.02f, false, 0.16f, 0.24f, hue, 0.3f * Mathf.Min(g, 1.3f));'''),
])

edit(G + r"\src\Fx\BattleFx.cs", [
    # Fire's filmed burst pulled toward orange: its white-yellow heart read as cream over the crowd.
    ('''        var tint = school == School.Frost ? new Color(glow * 0.8f, glow * 0.92f, glow * 1.15f, 1) : new Color(glow, glow, glow, 1);''',
     '''        var tint = school == School.Frost ? new Color(glow * 0.8f, glow * 0.92f, glow * 1.15f, 1)
            : school == School.Fire ? new Color(glow * 1.05f, glow * 0.72f, glow * 0.45f, 1) : new Color(glow, glow, glow, 1);'''),
    # A lane coming: its edges and a sparse hatch between them (filled, it hid what stood in it).
    ('''                else if (kind == 2) { float e = Mathf.Abs(u); a = (Mathf.Clamp(1 - Mathf.Abs(e - 0.88f) / 0.1f, 0, 1) + 0.22f) * Mathf.Clamp((1 - Mathf.Abs(v)) / 0.05f, 0, 1); }''',
     '''                else if (kind == 2) { float e = Mathf.Abs(u); a = (Mathf.Clamp(1 - Mathf.Abs(e - 0.88f) / 0.08f, 0, 1) + (e < 0.86f ? (Mathf.PosMod((u + v * 4) * 5f, 1f) < 0.25f ? 0.28f : 0.06f) : 0)) * Mathf.Clamp((1 - Mathf.Abs(v)) / 0.05f, 0, 1); }'''),
    # Blocked blows said once a beat, not once a blow (a wall of shields wrote a wall of words).
    ('''                    if (e.Blocked) { Hits.Text(at, "blocked", new Color(0.7f, 0.75f, 0.8f), 44); Burst(at, School.Physical, 5, 3, 2, 0.06f); break; }''',
     '''                    if (e.Blocked)
                    {
                        if (time - lastBlocked > 0.35) { lastBlocked = time; Hits.Text(at, "blocked", new Color(0.7f, 0.75f, 0.8f), 44); }
                        Burst(at, School.Physical, 5, 3, 2, 0.06f);
                        break;
                    }'''),
])

edit(G + r"\src\Fx\BattleFx.Skills.cs", [
    ("    double lastFall = -1;", "    double lastFall = -1, lastBlocked = -1;"),
])
print("edited")
