"""One-off edit: restraint when many die or flash at once."""
G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a63cd93fc73d5ed79\godot"


def edit(path, reps):
    with open(path, encoding="utf-8", newline="") as f:
        t = f.read()
    for a, b in reps:
        assert a in t, a[:80]
        t = t.replace(a, b)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(t)


edit(G + r"\src\Fx\BattleFx.cs", [
    ("        hitBudget = 28;",
     "        hitBudget = 28;\n        killBudget = 6;"),
    ('''                    Burst(at, e.School, e.Elite ? 40 : 10, e.Elite ? 7 : 4, 3, life: 0.6f);
                    for (int i = 0; i < (e.Elite ? 14 : 4); i++)
                        Sparks.Spawn(V(e.X + (R() - 0.5) * 0.6, gy + 0.5, e.Z + (R() - 0.5) * 0.6), new Vector3(0, 1.4f + R() * 1.5f, 0), 1 + R() * 0.6f, 0.07f,
                            new Color(2.4f, 1.1f, 0.3f), new Color(1.6f, 0.3f, 0.05f), 0.02f, 0, 0.8f);''',
     '''                    // A crowd cut down at once is told by its first few deaths in a frame; the
                    // rest fall with their gore alone (every death's burst of light together
                    // read as one cream blob over the crowd). What steel kills throws bone
                    // and grit, not light.
                    bool told = e.Elite || e.Boss || killBudget-- > 0;
                    if (told)
                    {
                        if (e.School == School.Physical)
                            for (int i = 0; i < (e.Elite ? 18 : 6); i++)
                                Smoke.Spawn(at, new Vector3((R() - 0.5f) * 5, 2 + R() * 3, (R() - 0.5f) * 5), 0.6f + R() * 0.3f, 0.06f + R() * 0.05f,
                                    new Color("#bfb6a2"), gravity: 12, sprite: Sprites.Of("dirt"), spinV: 6);
                        else Burst(at, e.School, e.Elite ? 30 : 7, e.Elite ? 7 : 4, 3, life: 0.5f);
                        for (int i = 0; i < (e.Elite ? 12 : 3); i++)
                            Sparks.Spawn(V(e.X + (R() - 0.5) * 0.6, gy + 0.5, e.Z + (R() - 0.5) * 0.6), new Vector3(0, 1.4f + R() * 1.5f, 0), 0.8f + R() * 0.5f, 0.06f,
                                new Color(2.2f, 0.9f, 0.25f), new Color(1.4f, 0.25f, 0.05f), 0.02f, 0, 0.8f);
                    }'''),
    ('''    public void Flash(Vector3 at, Color color, float peak, float life, float range = 9)
    {
        int best = 0;''',
     '''    public void Flash(Vector3 at, Color color, float peak, float life, float range = 9)
    {
        // Lights share: each one already lit dims the next, so a crowd's worth of
        // blows lights the pale dead no brighter than a few (they washed to cream).
        int lit = 0;
        foreach (var f in flashes) if (f.T < 0.5f) lit++;
        peak /= 1 + 0.6f * lit;
        int best = 0;'''),
])

edit(G + r"\src\Fx\BattleFx.Skills.cs", [
    ("    int hitBudget;",
     "    int hitBudget, killBudget;"),
])
print("edited")
