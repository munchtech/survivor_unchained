"""One-off edit: small marks for mote and shard hits, no filmed bursts; the hoarfrost wash gone; sprite bodies."""
G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a63cd93fc73d5ed79\godot"


def edit(path, reps):
    with open(path, encoding="utf-8", newline="") as f:
        t = f.read()
    for a, b in reps:
        assert a in t, a[:80]
        t = t.replace(a, b)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(t)


edit(G + r"\src\Fx\BattleFx.Skills.cs", [
    ('''                Sparks.Spawn(at, Vector3.Zero, 0.2f, 0.9f * g, Hdr("#bfe8ff", 2.4f), null, 0.3f, sprite: Sprites.Range("star").First + 1, spinV: 1);''',
     '''                // A star of frost where it strikes, blue, gone in a breath.
                Sparks.Spawn(at, Vector3.Zero, 0.22f, 0.45f * g, Hdr("#a8dcff", 1.7f), Hdr("#3d8cff", 0.8f), 0.75f * g, sprite: Sprites.Of("frost_star"), spinV: 1.5f);'''),
    ('''        // The skill's own burst at the body, small: a mote breaks in violet, a disc in gold, a shard in rime.
        var (book, tint) = art switch
        {
            "mote" or "mote_cascade" or "mote_star" or "moon" or "moon_brand" => ("arcane_burst", new Color(1.2f, 1.1f, 1.3f, 0.9f)),
            "disc" or "disc_aegis" or "disc_reckon" => ("holy_burst", new Color(1.2f, 1.1f, 0.85f, 0.9f)),
            "shard" or "shard_deep" or "spear_ice" => ("frost_burst", new Color(0.55f, 0.8f, 1.3f, 0.9f)),''',
     '''        // The skill's own burst at the body, small: a moon breaks in violet, a disc in gold.
        // (Motes and shards hit too often for a filmed burst each: a crowd of them read as
        // one white haze. Their marks above are enough.)
        var (book, tint) = art switch
        {
            "moon" or "moon_brand" => ("arcane_burst", new Color(1.2f, 1.1f, 1.3f, 0.9f)),
            "disc" or "disc_aegis" or "disc_reckon" => ("holy_burst", new Color(1.1f, 0.95f, 0.6f, 0.7f)),'''),
    ('''                // The burst is a breath of cold, not a white-out: blue, thin, gone in half a second.
                Books.Spawn("frost_burst", ground + Vector3.Up * 0.4f, r * 0.8f, 0.45f, new Color(0.35f, 0.65f, 1.25f, 0.5f), flat: true, sizeEnd: r * 1.8f);
''',
     '''                // No filmed burst: the front, the ice and the cold it rolls out are the blow
                // (the burst, however faint, washed the whole crowd blue-white).
'''),
    ('''                Scars.Add("frost", ground, r * 0.8f, 1.6f, 0);''',
     '''                Scars.Add("frost", ground, r * 0.7f, 1.2f, 0);'''),
])
print("edited")
