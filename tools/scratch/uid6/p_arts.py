PAIRS = [
("""            if (rest.Count > 0)
            {
                v.AddChild(Kit.Head("Not yet learned", "manuals teach them"));
                v.AddChild(Marks(ch, rest, false));
            }""",
"""            if (rest.Count > 0)
            {
                // The rest of the calling's arts, small and faint on one line, named on hover: a promise, not a wall.
                v.AddChild(Kit.Head("Not yet learned", $"{rest.Count}, taught by manuals"));
                v.AddChild(Marks(ch, rest, false));
            }"""),
("""            var b = new Button { FocusMode = FocusModeEnum.None, Flat = true, MouseDefaultCursorShape = CursorShape.PointingHand, CustomMinimumSize = new Vector2(112, 104) };""",
"""            var b = new Button { FocusMode = FocusModeEnum.None, Flat = true, MouseDefaultCursorShape = CursorShape.PointingHand, CustomMinimumSize = known ? new Vector2(112, 100) : new Vector2(54, 54) };
            if (!known) b.TooltipText = $"{a.Name}: {Roles[a.Role].Name.ToLowerInvariant()}. A manual teaches it.";"""),
("""            var m = new Medallion(64, "", a.Icon)""", """            var m = new Medallion(known ? 60 : 44, "", a.Icon)"""),
("""            var col = Style.V(2, mc, Style.Label(a.Name, Style.UiBold, 14, known ? (held ? Style.EmberHi : Kit.Ink) : Kit.Faint, false, HorizontalAlignment.Center),
                Style.Label(known ? (held ? "in hand" : $"rank {Numerals[rank - 1]}") + (ArtBook.OpenSlots(ch, a.Id) > 0 ? " · a facet!" : "") : Roles[a.Role].Name,
                    Style.Ui, 13, known ? Roles[a.Role].Color : Kit.Faint, false, HorizontalAlignment.Center));
            col.MouseFilter = MouseFilterEnum.Ignore;
            col.Position = new Vector2(0, 2);
            col.Size = new Vector2(112, 100);""",
"""            var col = Style.V(2, mc);
            if (known)
            {
                col.AddChild(Style.Label(a.Name, Style.UiBold, 14, held ? Style.EmberHi : Kit.Ink, false, HorizontalAlignment.Center));
                col.AddChild(Style.Label((held ? "in hand" : $"rank {Numerals[rank - 1]}") + (ArtBook.OpenSlots(ch, a.Id) > 0 ? " · a facet!" : ""), Style.Ui, 13, Roles[a.Role].Color, false, HorizontalAlignment.Center));
            }
            col.MouseFilter = MouseFilterEnum.Ignore;
            col.Position = new Vector2(0, known ? 2 : 4);
            col.Size = known ? new Vector2(112, 96) : new Vector2(54, 50);"""),
("""        var big = new Medallion(112, "", a.Icon)""", """        var big = new Medallion(88, "", a.Icon)"""),
("""        words.AddChild(Style.Label(a.Name.ToUpperInvariant(), Style.Display, 32, held ? Style.EmberHi : Kit.Ink));""",
"""        var nameRow = Style.H(16, Style.Label(a.Name.ToUpperInvariant(), Style.Display, 30, held ? Style.EmberHi : Kit.Ink));
        words.AddChild(nameRow);"""),
("""        else if (held) words.AddChild(Style.Label("IN HAND", Style.UiHeavy, 15, Style.EmberHi));
        else if (Safe) words.AddChild(Nav.Id(Kit.Word($"Take {a.Name} in hand", () => G.Gear((j, b) => j.HoldArt(a.Id, b)), Style.EmberHi, 17), "hold"));""",
"""        // (in hand, or the way to take it in hand, on the name's line: one line less)
        else if (held) nameRow.AddChild(Style.Label("in hand", Style.TextItalic, 17, Style.EmberHi) is var ih ? ih : null!);
        else if (Safe) nameRow.AddChild(Nav.Id(Kit.Word("Take it in hand", () => G.Gear((j, b) => j.HoldArt(a.Id, b)), Style.EmberHi, 16), "hold"));"""),
]
