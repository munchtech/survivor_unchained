PAIRS = [
("""    public void Show(IEnumerable<GroundLabel> list)
    {
        labels.Clear();
        labels.AddRange(list);
        QueueRedraw();
    }""",
"""    /// <summary>Where the HUD's words are this frame (a tip, the corner, the notices, a banner): a label
    /// that would fall on one gives way to it, faint, and never runs through its words.</summary>
    public readonly List<Rect2> KeepOut = new();

    public void Show(IEnumerable<GroundLabel> list)
    {
        labels.Clear();
        labels.AddRange(list);
        QueueRedraw();
    }"""),
("""            for (int k = 0; k < 8 && placed.Exists(r => r.Grow(2).Intersects(box)); k++) box.Position -= new Vector2(0, box.Size.Y + 3);
            placed.Add(box);""",
"""            for (int k = 0; k < 8 && placed.Exists(r => r.Grow(2).Intersects(box)); k++) box.Position -= new Vector2(0, box.Size.Y + 3);
            // Still on another after stepping up (a heap): left unsaid rather than written over it.
            if (placed.Exists(r => r.Grow(1).Intersects(box))) continue;
            placed.Add(box);
            // Under the HUD's own words it gives way: faint, and its light not drawn.
            bool under = KeepOut.Exists(r => r.Intersects(box.Grow(4)));
            if (under) { DrawString(font, new Vector2(box.Position.X + (l.Set ? 18 : 0), box.Position.Y + font.GetAscent(size)), text, HorizontalAlignment.Left, -1, size, l.Color with { A = 0.14f }); continue; }"""),
]
