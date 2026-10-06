"""One-off edit: the new filmed atlases put to use."""
G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a63cd93fc73d5ed79\godot"


def edit(path, reps):
    with open(path, encoding="utf-8", newline="") as f:
        t = f.read()
    for a, b in reps:
        assert a in t, a[:60]
        t = t.replace(a, b)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(t)


edit(G + r"\src\Fx\BattleFx.Skills.cs", [
    # Umbral bolts break in wisps of shadow (filmed) rather than the school's generic burst.
    ('''            "umbral" or "ruin" or "siphon" or "tether" or "tether2" or "tether_mark" => ("shadow_burst", new Color(1.3f, 1.2f, 1.4f, 0.9f)),''',
     '''            "umbral" or "ruin" or "siphon" or "tether" or "tether2" or "tether_mark" => ("shadow_wisps", new Color(1.2f, 1.1f, 1.4f, 0.9f)),'''),
    # A disc's critical: the sun flares, a star of rays (filmed).
    ('''            case "disc" or "disc_aegis" or "disc_reckon":
''',
     '''            case "disc" or "disc_aegis" or "disc_reckon":
                if (e.Crit) Books.Spawn("gold_flare", at + Vector3.Up * 0.3f, 0.6f * g, 0.3f, new Color(1f, 0.85f, 0.55f, 0.85f), sizeEnd: 1.4f * g);
'''),
    # Thorns breaking the ground carry the filmed brambles with them.
    ('''                    Erupt(x, zz, 0, 0.45f, 3, SpikeKind.Thorn, 0.9f, 1.6f, Hdr("#4ec85a", 1f));''',
     '''                    Erupt(x, zz, 0, 0.45f, 3, SpikeKind.Thorn, 0.9f, 1.6f, Hdr("#4ec85a", 1f));
                    Books.Spawn("bramble_burst", foot + Vector3.Up * 0.1f, 1.2f, 1.4f, new Color(0.9f, 1.2f, 0.9f, 0.8f), flat: true, sizeEnd: 1.6f);'''),
    # Dawn breaks at its heart: a star of rays over the ring.
    ('''                Flash(ground + Vector3.Up * 1.5f, h.Light, 7, 0.4f, r * 2.5f);''',
     '''                Flash(ground + Vector3.Up * 1.5f, h.Light, 7, 0.4f, r * 2.5f);
                Books.Spawn("gold_flare", ground + Vector3.Up * 1.4f, r * 0.35f, 0.35f, new Color(1f, 0.85f, 0.55f, 0.8f), sizeEnd: r * 0.9f);'''),
    # The green gathers at the hand before the lance is loosed.
    ('''        Sparks.Spawn(a, Vector3.Zero, life * 0.6f, 0.9f * g, pal.Core * 0.7f, pal.Glow * 0.2f, 0.4f, sprite: Sprites.Of("flare"));''',
     '''        if (sun) Sparks.Spawn(a, Vector3.Zero, life * 0.6f, 0.9f * g, pal.Core * 0.7f, pal.Glow * 0.2f, 0.4f, sprite: Sprites.Of("flare"));
        else Books.Spawn("leaf_burst", a, 1.6f * g, 0.45f, new Color(0.8f, 1.2f, 0.8f, 0.85f), sizeEnd: 0.6f * g);'''),
])
print("edited")
