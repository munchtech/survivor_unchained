PAIRS = [
("""    List<string>? report;
    TextureRect? warmth;
    double t;""", """    List<string>? report;
    TextureRect? warmth;
    Control? warmHead;
    double t;"""),
("""            warmth = WorldType.Light(new Vector2(520, 190), Style.Ember with { A = 0 });
            warmth.ShowBehindParent = true;
            b.AddChild(warmth);
            b.MoveChild(warmth, 0);
            b.Ready += () => { if (warmth != null) warmth.Position = new Vector2(b.Size.X / 2, head.Position.Y + head.Size.Y / 2) - warmth.Size / 2; };""", """            warmth = WorldType.Light(new Vector2(520, 190), Style.Ember with { A = 0 });
            warmth.ShowBehindParent = true;
            b.AddChild(warmth);
            b.MoveChild(warmth, 0);
            warmHead = head;"""),
("""        if (warmth != null && IsInstanceValid(warmth)) warmth.Modulate = Style.Ember with { A = 0.2f + 0.07f * Mathf.Sin((float)t * 2.1f) };""", """        if (warmth != null && IsInstanceValid(warmth) && warmHead != null && IsInstanceValid(warmHead))
        {
            // (centred on the name, wherever the column has laid it)
            warmth.Position = warmHead.GetParent<Control>().Position + warmHead.Position + warmHead.Size / 2 - warmth.Size / 2;
            warmth.Modulate = Style.Ember with { A = 0.2f + 0.07f * Mathf.Sin((float)t * 2.1f) };
        }"""),
("""        if (height == null) { book.Modulate = Colors.Transparent; head.Modulate = Colors.Transparent; measuring = 4; }
""", """        if (height == null) { page.Modulate = Colors.Transparent; measuring = 4; }
"""),
("""        if (height == null) { acts.Modulate = Colors.Transparent; }
""", ""),
]
