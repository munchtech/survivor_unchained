"""One-off edit: painted bodies for the disc, the coal, the umbral bolt and the moon."""
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
    # The disc: its painted sawblade face turning, instead of a plain torus.
    ('''                rings.Add(new Transform3D(new Godot.Basis(Vector3.Up, spin).Scaled(Vector3.One * s), at), gold);''',
     '''                // Its face: a sawblade of sunlight (painted, tools/comfy/fx_sprites.py), turning.
                Body(at, 1.3f * s, aegis ? "ward_disc" : "sun_disc", gold * 1.25f, spin * 1.3f);'''),
    # The coal: a painted lump of burning coal at its heart.
    ('''                orbs.Add(new Transform3D(Godot.Basis.Identity.Scaled(Vector3.One * s * 1.5f), at), Hdr("#ff5a10", 1.6f) * 0.2f);''',
     '''                orbs.Add(new Transform3D(Godot.Basis.Identity.Scaled(Vector3.One * s * 1.5f), at), Hdr("#ff5a10", 1.6f) * 0.2f);
                Body(at, s * 0.75f, "ember_coal", star ? Hdr("#ffb060", 1.6f) : Hdr("#ff7a28", 1.5f), (float)now * 5 + p.Id);'''),
    # The umbral bolt: a ring of violet flame round its dark heart.
    ('''                orbs.Add(new Transform3D(Godot.Basis.Identity.Scaled(Vector3.One * s * 1.8f), at), rim * 0.2f);''',
     '''                orbs.Add(new Transform3D(Godot.Basis.Identity.Scaled(Vector3.One * s * 1.8f), at), rim * 0.2f);
                if (!lantern) Body(at, s * 1.6f, "umbral", art == "siphon" ? Hdr("#c050ff", 1.2f) : Hdr("#9a50ff", 1.2f), (float)now * 3 + p.Id);'''),
    # The moon: a crescent, not a twirl.
    ('''                Sparks.Spawn(at, Vector3.Zero, 0.06f, s * 1.1f, Moon * 0.35f, null, s * 1.1f, sprite: Sprites.Of("twirl"), spinV: 0);''',
     '''                Body(at, s * 1.2f, "crescent", Moon * 0.5f, (float)now * 2 + p.Id);'''),
    ('''    /// <summary>A dark soft bed under a bright core (drawn first), so it shows over the pale dead.</summary>''',
     '''    /// <summary>A painted body for this frame (a sprite of tools/comfy/fx_sprites.py),
    /// `size` across, turned to `turn` radians.</summary>
    void Body(Vector3 at, float size, string sprite, Color color, float turn) =>
        Sparks.Spawn(new Sparks.P
        {
            At = at, Life = 0.035f, Size = size, SizeEnd = size, Color = color, ColorEnd = color, Alpha = 1,
            Sprite = Sprites.Range(sprite).First + 1, Spin = Mathf.PosMod(turn, Mathf.Tau) + 0.001f, SpinV = 0.001f,
        });

    /// <summary>A dark soft bed under a bright core (drawn first), so it shows over the pale dead.</summary>'''),
])
print("edited")
