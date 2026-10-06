PAIRS = [
("""    protected void Foot(Control row)
    {
        // Under the panels they lie on the world, which can be bright: a soft oval of shade behind
        // them, darkest at their middle and gone well before its edge, so no shape is seen.
        float w = row.GetCombinedMinimumSize().X + 260;
        var wash = new TextureRect
        {
            Texture = new GradientTexture2D
            {
                Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.5f, 0.5f), FillTo = new Vector2(1, 0.5f), Width = 128, Height = 128,
                Gradient = new Gradient { Colors = new[] { new Color(0.02f, 0.015f, 0.02f, 0.78f), new Color(0.02f, 0.015f, 0.02f, 0.6f), new Color(0.02f, 0.015f, 0.02f, 0) }, Offsets = new[] { 0f, 0.5f, 1f } },
            },
            ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale, MouseFilter = MouseFilterEnum.Ignore,
            Position = new Vector2(960 - w / 2, 1016 - 50), Size = new Vector2(w, 100),
        };
        AddChild(wash);
        var centre = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore, Position = new Vector2(0, 1000), Size = new Vector2(1920, 32) };
        centre.AddChild(row);
        AddChild(centre);
    }""",
"""    protected void Foot(Control row) => PromptsOnWorld(row);"""),
]
