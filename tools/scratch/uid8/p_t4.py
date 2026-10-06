PAIRS = [
("""        if (!Settings.Current.Mature) { Mature(); return; }""", """        if (!Settings.Current.Mature) { Mature(); return; }
        // (a panel open takes the name's place: the picture keeps its fire, the panel its room)"""),
("""        AddChild(brand);

        var slots = G.Saves.Slots();""", """        if (panel == "") AddChild(brand);

        var slots = G.Saves.Slots();"""),
("""            var v = Fitted(new Vector2(540, 16), panel == "controls" ? 880 : panel == "settings" ? 780 : 640);""", """            var v = Fitted(new Vector2(540, 16), panel == "controls" ? 600 : panel == "settings" ? 780 : 640);"""),
]
