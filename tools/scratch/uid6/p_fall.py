PAIRS = [
("""        light = WorldType.Light(new Vector2(520, 200), Style.Ember with { A = 0 });
        light.Position = new Vector2(960 - 420 - 260 + 140, 600 - 100);
        AddChild(light);
""", """        light = WorldType.Light(new Vector2(520, 200), Style.Ember with { A = 0 });
"""),
("""        row.Position = new Vector2(0, 560);
        row.Size = new Vector2(1920, 0);
        AddChild(row);""",
"""        row.Position = new Vector2(0, 560);
        row.Size = new Vector2(1920, 0);
        AddChild(row);
        // (the light sits behind "Get up" itself, wherever the row puts it)
        var first = (Control)row.GetChild(0);
        light.Position = first.CustomMinimumSize / 2 - light.Size / 2;
        light.ShowBehindParent = true;
        first.AddChild(light);"""),
]
