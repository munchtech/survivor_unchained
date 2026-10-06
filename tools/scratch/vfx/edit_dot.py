"""One-off edit: damage over time tallied per body in its school's colour."""
G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a63cd93fc73d5ed79\godot"


def edit(path, reps):
    with open(path, encoding="utf-8", newline="") as f:
        t = f.read()
    for a, b in reps:
        if "\r\n" in t:
            a, b = a.replace("\n", "\r\n"), b.replace("\n", "\r\n")
        assert a in t, a[:60]
        t = t.replace(a, b)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(t)


edit(G + r"\src\Fx\Hits.Numbers.cs", [
    ('''        public double Sum, Born;
        public bool Crit, Heavy;
    }''', '''        public double Sum, Born;
        public bool Crit, Heavy;
        /// <summary>Damage over time's own colour (its school's); none for a blow.</summary>
        public Color? Tint;
    }'''),
    ('''        public double Amount, MaxHp;
        public bool Crit;
    }''', '''        public double Amount, MaxHp;
        public bool Crit;
        public Color? Tint;
    }'''),
    ('''    /// <summary>A hit on `target` for this frame's numbers (shown at Flush).</summary>
    public void Tally(int target, Vector3 at, double amount, double maxHp, bool crit)
    {''', '''    /// <summary>A hit on `target` for this frame's numbers (shown at Flush). Damage over
    /// time passes its school's colour as `dot`, and sums into a number of its own.</summary>
    public void Tally(int target, Vector3 at, double amount, double maxHp, bool crit, Color? dot = null)
    {
        if (dot != null) { target = ~target; crit = false; }'''),
    ('''        waiting.Add(new Waiting { Target = target, At = at, Amount = amount, MaxHp = maxHp, Crit = crit });''',
     '''        waiting.Add(new Waiting { Target = target, At = at, Amount = amount, MaxHp = maxHp, Crit = crit, Tint = dot });'''),
    ('''            var t = new Tallied { Target = w.Target, Sum = w.Amount, Born = clock, Crit = w.Crit, Heavy = w.MaxHp > 0 && w.Amount > w.MaxHp * 0.2 };''',
     '''            var t = new Tallied { Target = w.Target, Sum = w.Amount, Born = clock, Crit = w.Crit, Heavy = w.MaxHp > 0 && w.Amount > w.MaxHp * 0.2, Tint = w.Tint };'''),
    ('''        l.Modulate = t.Crit ? new Color(1.6f, 1.15f, 0.4f) : new Color(1, 0.94f, 0.86f);
        l.FontSize = (t.Crit ? 80 : 58) + (t.Heavy ? 18 : 0);''',
     '''        l.Modulate = t.Tint ?? (t.Crit ? new Color(1.6f, 1.15f, 0.4f) : new Color(1, 0.94f, 0.86f));
        // What burns or bleeds a body is told smaller than the blows themselves.
        l.FontSize = t.Tint != null ? 44 : (t.Crit ? 80 : 58) + (t.Heavy ? 18 : 0);'''),
])

edit(G + r"\src\Fx\BattleFx.cs", [
    ('''                        if (R() < 0.35f) Hits.Text(at, ((int)Math.Round(e.Amount)).ToString(), new Color(0.85f, 0.8f, 0.72f, 0.85f), 40);''',
     '''                        // Summed per body per beat like the blows, in the colour of what is doing it.
                        var dc = Palette.Of(e.School).Glow;
                        float dm = Mathf.Max(dc.R, Mathf.Max(dc.G, dc.B));
                        Hits.Tally(e.Target, at, e.Amount, e.MaxHp, false, new Color(dc.R / dm * 1.1f, dc.G / dm * 1.1f, dc.B / dm * 1.1f, 0.9f));'''),
])
print("edited")
