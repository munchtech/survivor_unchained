"""Round 3: her grounds below the enemy's marks (half under a boss), the enemy's ground at the
crowd's 0.28, Dawnpulse's front gold not cream, the herd lit from within, the palm, the shadow's
rent and the moon's brand deeper."""
G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abc6bbe020c7fe287\godot"


def edit(path, pairs):
    p = G + "\\" + path
    s = open(p, encoding="utf-8").read()
    for a, b in pairs:
        assert a in s, (path, a[:70])
        s = s.replace(a, b)
    open(p, "w", encoding="utf-8").write(s)


edit(r"src\Fx\BattleFx.Skills.cs", [
    # A. Her grounds: never louder than a crowd's hostile mark, half that under a boss.
    ('''        // (A thicket's edge is its thorns, a rot's its stain: their lit rings held back.)
        g.Edge.Decal.Modulate = edgeCol with { A = fade * breathe * (inside is Inside.Roots or Inside.Veins ? 0.45f : 0.85f) };
        // The pattern inside: a third of the edge's strength at most (the runes less:
        // under her for a whole night, they hid her), turning slowly.
        g.Fill.Decal.Modulate = edgeCol with { A = fade * (inside == Inside.Runes ? 0.18f : 0.3f) };''',
     '''        // Never louder than a crowd's hostile mark (MECHANICS.md section 2: the enemy's marks are
        // drawn over hers), and half that while a boss is up, so the eye goes to his marks first.
        // (At full strength her thickets' and rots' rims, two or three at once, were the loudest
        // thing at Greymuzzle.) A thicket reads by its thorns, a rot by its stain, not their rims.
        float hush = bossUp ? 0.5f : 1f;
        g.Edge.Decal.Modulate = edgeCol with { A = fade * breathe * (inside is Inside.Roots or Inside.Veins ? 0.22f : 0.34f) * hush };
        // The pattern inside, fainter still (the runes least: under her for a whole night, they
        // hid her), turning slowly.
        g.Fill.Decal.Modulate = edgeCol with { A = fade * (inside == Inside.Runes ? 0.14f : inside == Inside.Veins ? 0.12f : 0.2f) * hush };'''),
    # C. Dawnpulse's front: gold, not a thick cream ring round her.
    ('''                var gold = Hdr("#ffd27a", 1f);
                AddFront(ground, r, 0.4f, 0.42f * g, gold, 3f, Ribbons.Style.Glow, 0.1f);
                for (int k = 1; k < rings; k++) AddFront(ground, r * (1 - 0.18f * k), 0.4f + 0.08f * k, 0.22f, gold, 1.8f, Ribbons.Style.Glow, 0.1f);''',
     '''                // Deep gold and thin: wide and bright, its front bloomed to a thick cream ring that
                // was the strongest mark near her while it lasted.
                var gold = Hdr("#ffb84a", 1f);
                AddFront(ground, r, 0.4f, 0.24f * g, gold, 1.7f, Ribbons.Style.Glow, 0.1f);
                for (int k = 1; k < rings; k++) AddFront(ground, r * (1 - 0.18f * k), 0.4f + 0.08f * k, 0.14f, gold, 1.1f, Ribbons.Style.Glow, 0.1f);'''),
    ('''                Books.Spawn("holy_ring", ground + Vector3.Up * 0.5f, r * 0.7f, 0.5f, new Color(1f, 0.85f, 0.55f, 0.85f), flat: true, sizeEnd: r * 2.3f);''',
     '''                Books.Spawn("holy_ring", ground + Vector3.Up * 0.5f, r * 0.7f, 0.5f, new Color(0.85f, 0.62f, 0.3f, 0.7f), flat: true, sizeEnd: r * 2.3f);'''),
    # D. The herd: lit green from within, whole, larger, its wake shorter.
    ('''                float sc = Mathf.Sqrt(g) * (art == "herd_great" ? 1.12f : 1);''',
     '''                float sc = 1.2f * Mathf.Sqrt(g) * (art == "herd_great" ? 1.12f : 1);'''),
    ('''                var tint = hunt ? new Color(0.75f, 1.45f, 0.5f) : new Color(0.55f, 1.3f, 0.85f);
                float flake = 0.1f + 0.05f * Mathf.Sin((float)now * 13 + p.Id);
                herdCrowd.Push(new Transform3D(basis, feet), "move", now * rate + p.Id * 0.37, 0, flake, 0, 0, tint, hunt ? 1.0f : 0.8f);''',
     '''                // Whole, lit from within (flaking, its edges burned orange and it read as a dark
                // shape in a green streak).
                var tint = hunt ? new Color(0.7f, 1.6f, 0.4f) : new Color(0.45f, 1.5f, 1.0f);
                herdCrowd.Push(new Transform3D(basis, feet), "move", now * rate + p.Id * 0.37, 0, 0, 0, 0, tint, 2.2f);'''),
    ('''                Ribbons.Feed(key, feet + Vector3.Up * 0.55f * sc, 0.5f * sc, 0.22f, new Color(wild.R * 0.5f, wild.G * 0.5f, wild.B * 0.5f), 1.3f, Ribbons.Style.Wisp);''',
     '''                Ribbons.Feed(key, feet + Vector3.Up * 0.5f * sc, 0.3f * sc, 0.14f, new Color(wild.R * 0.4f, wild.G * 0.4f, wild.B * 0.4f), 0.9f, Ribbons.Style.Wisp);'''),
    # E. The palm: a clearer print, less air.
    ('''        var chi = storm ? Hdr("#8ab8ff", 1.35f) : Hdr("#ffb848", 1.35f);''',
     '''        var chi = storm ? Hdr("#8ab8ff", 1.6f) : Hdr("#ffb040", 1.6f);'''),
    ('''        float size = Mathf.Min(2.2f, reach * 0.62f) * Mathf.Sqrt(g);''',
     '''        float size = Mathf.Min(2.4f, reach * 0.7f) * Mathf.Sqrt(g);'''),
    ('''        Waves.Add(at + dir * reach * 0.25f + Vector3.Down * 0.6f, reach * 0.55f, 0.22f, chi, 0.55f);''',
     '''        Waves.Add(at + dir * reach * 0.25f + Vector3.Down * 0.6f, reach * 0.5f, 0.2f, chi, 0.35f);'''),
    # G. The shadow's rent through the rank: deeper violet, quieter.
    ('''                Ribbons.Line(new[] { at - away * 0.7f, at, at + away * 1.0f }, (art == "ruin" ? 0.3f : 0.2f) * g, 0.16f, art == "siphon" ? Hdr("#d060ff", 1f) : Hdr("#9a5aff", 1f), 2.2f, Ribbons.Style.Wisp, new[] { 0f, 1f, 0f });''',
     '''                Ribbons.Line(new[] { at - away * 0.7f, at, at + away * 1.0f }, (art == "ruin" ? 0.26f : 0.17f) * g, 0.16f, art == "siphon" ? Hdr("#b040ff", 1f) : Hdr("#7a3cff", 1f), 1.5f, Ribbons.Style.Wisp, new[] { 0f, 1f, 0f });'''),
    # H. The moon's brand: violet, not a pale blob.
    ('''            "moon" or "moon_brand" => ("moon_burst", new Color(0.3f, 0.25f, 1.0f, 0.6f)),''',
     '''            "moon" or "moon_brand" => ("moon_burst", new Color(0.22f, 0.17f, 0.8f, 0.5f)),'''),
    ('''                Sparks.Spawn(at + Vector3.Up * 0.25f, Vector3.Up * 0.35f, 0.55f, 0.55f * g, MoonSilver, new Color(fire.R * 0.3f, fire.G * 0.3f, fire.B * 0.3f), 0.95f * g, sprite: Sprites.Range("crescent").First + 1, spinV: 0.6f);''',
     '''                Sparks.Spawn(at + Vector3.Up * 0.25f, Vector3.Up * 0.35f, 0.5f, 0.55f * g, Hdr("#9a8cff", 1.1f), new Color(fire.R * 0.3f, fire.G * 0.3f, fire.B * 0.3f), 0.95f * g, sprite: Sprites.Range("crescent").First + 1, spinV: 0.6f);'''),
])

edit(r"src\Fx\BattleFx.cs", [
    # B. The enemy's lasting ground at the crowd's strength, like every hostile mark.
    ('''            var col = z.Owner == Sim.Side.Enemy ? Palette.TeleGround * 0.4f : Palette.Of(school).Glow * 0.5f;''',
     '''            var col = z.Owner == Sim.Side.Enemy ? Palette.TeleGround * 0.28f : Palette.Of(school).Glow * 0.5f;'''),
    # Whether a boss is up this frame (her grounds hush under one).
    ('''        Zones(b, now);
        ArtTrails(b, fdt);''',
     '''        bossUp = false;
        foreach (var e in b.Enemies.Living()) if (e.Boss) { bossUp = true; break; }
        Zones(b, now);
        ArtTrails(b, fdt);'''),
    ('''    float artT;
''',
     '''    float artT;
    /// <summary>A boss is up: her own grounds are drawn at half (the eye goes to his marks).</summary>
    bool bossUp;
'''),
])
print("ok")
