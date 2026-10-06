PAIRS = [
("""    float? height;
    int measuring;
    readonly List<Control> measured = new();""", """    float? height;
    int measuring, tries;
    readonly List<Control> measured = new();
    readonly List<ScrollContainer> leaves = new();
    bool settling = true;"""),
("""        measured.Clear();
        AddChild(new Backdrop(null, 0.94f));""", """        measured.Clear();
        leaves.Clear();
        AddChild(new Backdrop(null, 0.94f));"""),
("""            leaf.AddChild(sc);
            measured.Add(words);
        }
        if (height == null) { page.Modulate = Colors.Transparent; measuring = 4; }""", """            leaf.AddChild(sc);
            measured.Add(words);
            leaves.Add(sc);
        }
        if (settling) { page.Modulate = Colors.Transparent; measuring = 4; }"""),
("""        // Laid out: the book takes its writing's height (the taller leaf's), then shows.
        if (measuring > 0 && --measuring == 0)
        {
            float need = measured.Where(IsInstanceValid).Select(c => c.GetCombinedMinimumSize().Y).DefaultIfEmpty(0).Max();
            // (the Journal's chrome less the foot line its leaves carry, which this book has not)
            height = Math.Clamp(need + OpenBook.Chrome - 14, MinH, MaxH);
            if (Args.Has("shot")) GD.Print($"chapter: words {need:0}, book {height:0}");
            Refresh();
        }""", """        // Laid out: the book takes its writing's height (the taller leaf's), measured again at it
        // until it holds (wrapped words settle their lines a frame or two after the width they wrap
        // to; a scroll bar, once shown, narrows them onto more), as the Journal's book does; then shows.
        if (measuring > 0 && --measuring == 0 && settling)
        {
            float need = measured.Where(IsInstanceValid).Select(c => c.GetCombinedMinimumSize().Y)
                .Concat(leaves.Where(IsInstanceValid).Select(s => (float)s.GetVScrollBar().MaxValue)).DefaultIfEmpty(0).Max();
            float had = height ?? MaxH;
            // (the Journal's chrome less the foot line its leaves carry, which this book has not)
            float now = Math.Clamp(need + OpenBook.Chrome - 14, MinH, MaxH);
            if (tries > 0) now = Math.Max(now, had);
            height = now;
            if (Math.Abs(now - had) <= 2 || ++tries >= 4) settling = false;
            if (Args.Has("shot")) GD.Print($"chapter: words {need:0}, book {now:0}{(settling ? "" : ", held")}");
            Refresh();
        }"""),
]
