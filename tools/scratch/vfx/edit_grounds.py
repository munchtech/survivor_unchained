"""One-off edit: round, premultiplied ground fills; sparser hostile fills."""
G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a63cd93fc73d5ed79\godot"


def edit(path, reps, crlf=False):
    with open(path, encoding="utf-8", newline="") as f:
        t = f.read()
    for a, b in reps:
        if crlf:
            a, b = a.replace("\n", "\r\n"), b.replace("\n", "\r\n")
        assert a in t, a[:70]
        t = t.replace(a, b)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(t)


edit(G + r"\src\Fx\BattleFx.Skills.cs", [
    ('''            var fillTex = inside switch
            {
                Inside.Runes => Sprites.Runes(1),
                Inside.Embers => Sprites.Burning,
                Inside.Roots => GD.Load<Texture2D>("res://art/fx/marks/roots_emit.png"),
                _ => veinTex,
            };''',
     '''            // Lit by the colour alone (a decal's emission ignores alpha), so each
            // is premultiplied: the importer bleeds colour into the clear pixels,
            // and a turning fill showed as a glowing square.
            var fillTex = inside switch
            {
                Inside.Runes => Premul(Sprites.Runes(0)),
                Inside.Embers => Premul(Sprites.Burning),
                Inside.Roots => Premul(GD.Load<Texture2D>("res://art/fx/marks/roots_emit.png")),
                _ => veinTex,
            };'''),
    ('''        g.Edge.Decal.Modulate = edgeCol with { A = fade * breathe };
        // The pattern inside: a third of the edge's strength at most, turning slowly.
        g.Fill.Decal.Modulate = edgeCol with { A = fade * 0.32f };''',
     '''        g.Edge.Decal.Modulate = edgeCol with { A = fade * breathe * 0.85f };
        // The pattern inside: a third of the edge's strength at most (the runes less:
        // under her for a whole night, they hid her), turning slowly.
        g.Fill.Decal.Modulate = edgeCol with { A = fade * (inside == Inside.Runes ? 0.18f : 0.3f) };'''),
    ('''                float a = Mathf.Exp(-Mathf.Pow((r - 0.93f) / 0.022f, 2)) + 0.25f * Mathf.Exp(-Mathf.Pow((r - 0.9f) / 0.06f, 2));''',
     '''                float a = Mathf.Exp(-Mathf.Pow((r - 0.93f) / 0.014f, 2)) + 0.1f * Mathf.Exp(-Mathf.Pow((r - 0.91f) / 0.04f, 2));'''),
    ('''    /// <summary>A lit edge and nothing inside it: a thin bright band, soft both ways.</summary>''',
     '''    static readonly System.Collections.Generic.Dictionary<Texture2D, Texture2D> premul = new();

    /// <summary>A texture with its colour multiplied by its alpha, for what reads
    /// only its colour (a decal's emission): clear pixels made black.</summary>
    public static Texture2D Premul(Texture2D tex)
    {
        if (premul.TryGetValue(tex, out var done)) return done;
        var img = tex.GetImage();
        if (img.IsCompressed()) img.Decompress();
        img.Convert(Image.Format.Rgba8);
        for (int y = 0; y < img.GetHeight(); y++)
            for (int x = 0; x < img.GetWidth(); x++)
            {
                var c = img.GetPixel(x, y);
                img.SetPixel(x, y, new Color(c.R * c.A, c.G * c.A, c.B * c.A, c.A));
            }
        img.GenerateMipmaps();
        return premul[tex] = ImageTexture.CreateFromImage(img);
    }

    /// <summary>A lit edge and nothing inside it: a thin bright band, soft both ways.</summary>'''),
])

edit(G + r"\src\Fx\BattleFx.cs", [
    ('var tex = !mine ? discTex! : school switch { School.Holy => Sprites.Runes(1), School.Arcane => Sprites.Runes(0), School.Fire => Sprites.Burning, _ => discTex! };',
     'var tex = !mine ? hatchTex! : school switch { School.Holy => Premul(Sprites.Runes(0)), School.Arcane => Premul(Sprites.Runes(0)), School.Fire => Premul(Sprites.Burning), _ => discTex! };'),
    ('                else if (kind == 1) a = r < 0.97f ? 0.35f + 0.65f * Mathf.SmoothStep(0.6f, 0.95f, r) : Mathf.Clamp((1 - r) / 0.03f, 0, 1);',
     '''                // A blow coming, filling as it comes: a bright front at its edge and a sparse hatch behind
                // it, so the crowd still reads through (a solid fill hid the fight).
                else if (kind == 1) a = r < 0.97f ? 0.08f + (Mathf.PosMod((u - v) * 6f, 1f) < 0.22f ? 0.2f : 0) + 0.72f * Mathf.SmoothStep(0.8f, 0.95f, r) : Mathf.Clamp((1 - r) / 0.03f, 0, 1);'''),
    ('''            m.Fill.Modulate = color with { A = 0.55f };
            m.Fill.EmissionEnergy = 2;''',
     '''            m.Fill.Modulate = color with { A = 0.42f };
            m.Fill.EmissionEnergy = 1.4f;'''),
], crlf=True)
print("edited")
