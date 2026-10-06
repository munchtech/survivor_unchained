PAIRS = [
("""        var plate = Style.Panel(Kit.PanelBox(18, 6, Kit.Ground with { A = 0.9f }), Prompts());
        plate.MouseFilter = MouseFilterEnum.Ignore;
        var foot = new CenterContainer { Position = new Vector2(0, 996), Size = new Vector2(1920, 48), MouseFilter = MouseFilterEnum.Ignore };
        foot.AddChild(plate);
        AddChild(foot);""",
"""        PromptsOnWorld(Prompts());"""),
("""                over => Hover(it, over), glyph, name, $"worn:{i++}");""",
"""                over => Hover(it, over), glyph, name, $"worn:{i++}", engraved: true);"""),
("""            : $"{Inventory.RarityName(it)} {def.Kind.ToString().ToLowerInvariant()}";""",
"""            : ItemViews.KindLine(it);"""),
("""        var kind = Style.H(Style.Gap2, Style.Label(what, Style.Ui, 15, Kit.Ink2), Style.Gems(it.Rarity, 7));""",
"""        var kind = Style.H(Style.Gap2, Style.Label(what, Style.Ui, 15, Kit.Ink2));"""),
]
