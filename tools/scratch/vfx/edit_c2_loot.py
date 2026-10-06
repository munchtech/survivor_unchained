from ed import edit
edit(r"src\Fx\BattleFx.Loot.cs", [
    ("enum Lit { Rare = 1, Epic = 2, Set = 3, Pillar = 4, Strike = 5, Glow = 6, Shaft = 7 }",
     "enum Lit { Rare = 1, Epic = 2, Set = 3, Pillar = 4, Strike = 5, Glow = 6, Shaft = 7, Band = 8, Room = 9 }"),
    ("""    // A moment's columns of light (Pillar): where, how tall and wide, in what colour, since when, how long.
    readonly List<(Vector3 At, float Height, float Width, Color Colour, double Born, float Life)> shafts = new();
""", """    // A moment's columns of light (Pillar): where, how tall and wide, in what colour, since when, how
    // long, and how thick the motes riding up it.
    readonly List<(Vector3 At, float Height, float Width, Color Colour, double Born, float Life, float Motes)> shafts = new();
"""),
    ("""    /// four times wider.</summary>
    void Pillar(Vector3 at, float height, float radius, Color color, float life)
    {
        // Its hue kept, its brightness held to the knee.
        float top = Mathf.Max(color.R, Mathf.Max(color.G, color.B));
        var c = top > 1.1f ? new Color(color.R / top * 1.1f, color.G / top * 1.1f, color.B / top * 1.1f) : color;
        shafts.Add((at, height, Mathf.Max(0.5f, radius * 4), c, time, Mathf.Max(0.05f, life)));
    }
""", """    /// four times wider. `motes`: light riding up it (0 to 1).</summary>
    void Pillar(Vector3 at, float height, float radius, Color color, float life, float motes = 0)
    {
        // Its hue kept, its brightness held to the knee.
        float top = Mathf.Max(color.R, Mathf.Max(color.G, color.B));
        var c = top > 1.1f ? new Color(color.R / top * 1.1f, color.G / top * 1.1f, color.B / top * 1.1f) : color;
        shafts.Add((at, height, Mathf.Max(0.5f, radius * 4), c, time, Mathf.Max(0.05f, life), motes));
    }
"""),
    ("Light(s.At.X, s.At.Y - 0.04f, s.At.Z, Lit.Shaft, 0, s.Width * (0.8f + 0.2f * grow), s.Height * (0.4f + 0.6f * grow), s.Colour, fade);",
     "Light(s.At.X, s.At.Y - 0.04f, s.At.Z, Lit.Shaft, s.Motes, s.Width * (0.8f + 0.2f * grow), s.Height * (0.4f + 0.6f * grow), s.Colour, fade);"),
])
edit(r"src\Fx\BattleFx.cs", [
    ("""                    var gold = new Color(2.6f, 1.9f, 1.0f);
                    Flash(at + Vector3.Up * 3, new Color("#ffe6b0"), 42, 1.8f, 28);
                    // (One column, gold: its white core read as a cream bar.)
                    Pillar(at, 34, 1.1f, gold, 1.6f);
""", """                    var gold = new Color(2.6f, 1.9f, 1.0f);
                    // Ember-warm, not white-gold: at 42 the whole field went cream round her.
                    Flash(at + Vector3.Up * 3, new Color("#ffb060"), 30, 1.6f, 24);
                    // One column in the ember's own colour with the ember riding up it, leaving what
                    // ruled the night. (Gold and four metres wide, it was a cream haze up the middle
                    // of the screen, behind the words; white-cored, a cream bar.)
                    Pillar(at, 34, 0.75f, new Color(1.1f, 0.6f, 0.2f), 1.8f, motes: 1);
"""),
])
