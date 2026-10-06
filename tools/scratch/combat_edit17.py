W = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09c5a65f5a84319e\godot'

def edit(path, pairs):
    p = W + '\\' + path
    s = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert s.count(a) == 1, (path, s.count(a), a[:80])
        s = s.replace(a, b, 1)
    open(p, 'w', encoding='utf-8').write(s)

edit(r'logic\Sim\Events.cs', [
('''        /// <summary>A boss's: drawn above the survivor's own effects, and named over the boss.</summary>
        public bool Boss; public string? Label;''',
'''        /// <summary>A boss's: drawn above the survivor's own effects, and named over the boss.</summary>
        public bool Boss; public string? Label;
        /// <summary>Who marked it, where it stood (its name is said over it, not over the survivor).</summary>
        public double? ByX, ByZ;'''),
])

edit(r'logic\Sim\Battle.cs', [
('''            Width = b.Width, Angle = b.Angle, Arc = b.Arc, Duration = b.Delay, Hostile = true, Boss = b.From?.Boss == true, Label = b.Label,
        });''',
'''            Width = b.Width, Angle = b.Angle, Arc = b.Arc, Duration = b.Delay, Hostile = true, Boss = b.From?.Boss == true, Label = b.Label,
            ByX = b.From?.X, ByZ = b.From?.Z,
        });'''),
])

edit(r'src\Fx\BattleFx.cs', [
('''                    // A boss's move, named over its mark for as long as the mark stands (a lane or a
                    // cone from the boss is named over the boss, where the eye already is).
                    if (e.Label is { Length: > 0 } label)
                        Hits.Word(V(e.X, Y(e.X, e.Z) + 3.4, e.Z), label.ToUpperInvariant(), WordColour(col), 46, (float)Math.Min(2.5, e.Duration + 0.3));''',
'''                    // A boss's move, named over the boss for as long as its mark stands: who is doing
                    // it, where the eye already is (over the mark, it sat on the survivor's head).
                    if (e.Label is { Length: > 0 } label)
                    {
                        double lx = e.ByX ?? e.X, lz = e.ByZ ?? e.Z;
                        Hits.Word(V(lx, Y(lx, lz) + 4.4, lz), label.ToUpperInvariant(), WordColour(col), 70, (float)Math.Min(2.5, e.Duration + 0.3));
                    }'''),
])
print("ok")
