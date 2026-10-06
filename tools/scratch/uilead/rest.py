p = 'godot/src/Ui/Menus.cs'
s = open(p, encoding='utf-8', newline='').read()
nl = '\r\n' if '\r\n' in s else '\n'
s = s.replace('\r\n', '\n')
a = s.index('        AddChild(Style.Scrim(G.CloseOverlay));\n        int cost = G.Journey.RestCost;')
b = s.index('    public override bool Key(Act a)\n    {\n        if (report != null && a is Act.Confirm')
new = '''        // The choice made in the place itself (docs/UI_DESIGN.md 7.7): three crested cards on a plate,
        // each with its sign, what it does and what it costs; the world stays in view round it.
        AddChild(Style.Scrim(G.CloseOverlay, 0.5f));
        int cost = G.Journey.RestCost;
        bool afford = G.Journey.Ch.Gold >= cost;
        var plate = Style.Panel(Style.Plate(26));
        var centre = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
        Style.Fill(centre);
        centre.AddChild(plate);
        AddChild(centre);
        var col = Style.V(Style.Gap3);
        col.AddChild(new Plaque("The Last Lamp", 30, 120));
        col.AddChild(Style.Label("Mother Rook keeps a bed, a fire and the door. What will you do with the hours?", Style.TextItalic, Style.Body, Style.InkDim, false, HorizontalAlignment.Center));
        var row = Style.H(Style.Gap4);
        row.Alignment = BoxContainer.AlignmentMode.Center;
        row.AddChild(Choice("moon", "Sleep until morning", "A day passes. You wake rested; the ember goes out while you sleep.",
            cost > 0 ? $"{cost} gold" : "On the house", afford ? null : $"You need {cost} gold; you have {Math.Floor(G.Journey.Ch.Gold)}.", () => G.Rest(false), true, "rest:sleep"));
        if (w.Time != TimeOfDay.Night)
            row.AddChild(Choice("hourglass", "Wait until nightfall", "The day goes by at the fire. By dark the arenas burn and the road is not safe.", null, null, () => G.Rest(true), false, "rest:wait"));
        row.AddChild(Choice("next", "Not yet", "Back out into the day. The lamp will be lit when you come back.", null, null, G.CloseOverlay, false, "rest:leave"));
        col.AddChild(row);
        plate.AddChild(col);
    }

    /// <summary>One of the lamp's choices: a crested card with its sign, words, price and, if refused, why.</summary>
    Control Choice(string glyph, string title, string text, string? price, string? refused, Action go, bool primary, string id)
    {
        var box = OrnateBox.Make(OrnateBox.Kind.Card, 18, refused != null ? Style.InkFaint : primary ? Style.Ember : Style.Gold);
        box.Crest = 70;
        var lit = OrnateBox.Make(OrnateBox.Kind.Card, 18, refused != null ? Style.InkFaint : Style.EmberHi);
        lit.Crest = 70;
        lit.Glow = refused != null ? 0 : 1.2f;
        var b = new Button { CustomMinimumSize = new Vector2(300, 330), FocusMode = FocusModeEnum.None, MouseDefaultCursorShape = refused != null ? CursorShape.Forbidden : CursorShape.PointingHand };
        b.AddThemeStyleboxOverride("normal", box);
        b.AddThemeStyleboxOverride("hover", lit);
        b.AddThemeStyleboxOverride("pressed", lit);
        b.AddThemeStyleboxOverride("disabled", box);
        b.AddThemeStyleboxOverride("focus", new StyleBoxEmpty());
        b.Disabled = refused != null;
        b.Pressed += go;
        var v = Style.V(Style.Gap2);
        v.MouseFilter = MouseFilterEnum.Ignore;
        v.Position = new Vector2(20, 18);
        v.Size = new Vector2(260, 294);
        var med = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
        med.AddChild(new Medallion(96, "", glyph) { Lit = primary && refused == null });
        v.AddChild(med);
        v.AddChild(Style.Label(title, Style.Display, 21, refused != null ? Style.InkDim : Style.GoldHi, true, HorizontalAlignment.Center));
        var words = Style.Label(text, Style.Text, Style.Small, Style.Ink, true, HorizontalAlignment.Center);
        words.SizeFlagsVertical = SizeFlags.ExpandFill;
        v.AddChild(words);
        if (price != null)
            v.AddChild(Style.H(4, Glyphs.Icon("coin", 16, Style.GoldHi), Style.Label(price, Style.UiBold, Style.Small, refused != null ? Style.Bad : Style.GoldHi)) is var tag && tag is BoxContainer bc ? Center(bc) : tag);
        if (refused != null) v.AddChild(Style.Label(refused, Style.UiBold, Style.Caption, Style.Bad, true, HorizontalAlignment.Center));
        b.AddChild(v);
        Nav.Id(b, id);
        return b;
    }

    static Control Center(BoxContainer b) { b.Alignment = BoxContainer.AlignmentMode.Center; return b; }

'''
s = s[:a] + new + s[b:]
open(p, 'w', encoding='utf-8', newline='').write(s.replace('\n', nl))
print('ok')
