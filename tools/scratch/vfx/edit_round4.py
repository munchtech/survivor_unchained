G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abc6bbe020c7fe287\godot"


def edit(path, pairs):
    p = G + "\\" + path
    s = open(p, encoding="utf-8").read()
    for a, b in pairs:
        assert a in s, (path, a[:70])
        s = s.replace(a, b)
    open(p, "w", encoding="utf-8").write(s)


edit(r"src\Fx\BattleFx.Skills.cs", [
    ('''        g.Edge.Decal.Modulate = edgeCol with { A = fade * breathe * (inside is Inside.Roots or Inside.Veins ? 0.22f : 0.34f) * hush };''',
     '''        // (Scaled in its colour: a decal's emission ignores its alpha, so an alpha of a fifth left
        // the rims at full strength.)
        g.Edge.Decal.Modulate = Dim(edgeCol, fade * breathe * (inside is Inside.Roots or Inside.Veins ? 0.22f : 0.34f) * hush);'''),
    ('''        g.Fill.Decal.Modulate = edgeCol with { A = fade * (inside == Inside.Runes ? 0.14f : inside == Inside.Veins ? 0.12f : 0.2f) * hush };''',
     '''        g.Fill.Decal.Modulate = Dim(edgeCol, fade * (inside == Inside.Runes ? 0.14f : inside == Inside.Veins ? 0.12f : 0.2f) * hush);'''),
    ('''    void GroundsGone(System.Collections.Generic.HashSet<int> alive)''',
     '''    /// <summary>A decal's colour at a strength: its light scaled in the colour itself (a decal's
    /// emission ignores alpha) and its alpha the same, for what it lays as paint.</summary>
    static Color Dim(Color c, float k) => new(c.R * k, c.G * k, c.B * k, k);

    void GroundsGone(System.Collections.Generic.HashSet<int> alive)'''),
    # Dawnpulse: no disc of light over the crowd.
    ('''                Books.Spawn("holy_ring", ground + Vector3.Up * 0.5f, r * 0.7f, 0.5f, new Color(0.85f, 0.62f, 0.3f, 0.7f), flat: true, sizeEnd: r * 2.3f);''',
     '''                Books.Spawn("holy_ring", ground + Vector3.Up * 0.5f, r * 0.7f, 0.45f, new Color(0.6f, 0.38f, 0.12f, 0.5f), flat: true, sizeEnd: r * 2.3f);'''),
    ('''                Scars.Add("sigil", ground, r * 0.7f, art == "nova_sun" ? 3 : 1.4f, 0.6f);''',
     '''                // The sigil it leaves, small at her feet (seventy percent of its reach, it was a lit
                // disc of rings over the whole crowd).
                Scars.Add("sigil", ground, Mathf.Min(1.6f, r * 0.35f), art == "nova_sun" ? 3 : 1.2f, 0.6f);'''),
])
print("ok")
