PAIRS = [
("""        if (InBook) BookTabs(new Vector2(40, 30));
        var plaque = new Plaque(title, 34, 120);""",
"""        // The book's tabs ride the same chain on a full page as on the panel, so turning from the
        // Pack to the Journal keeps one object under the hand.
        if (InBook)
        {
            int on = Array.FindIndex(Book, b => b.Kind == Kind);
            var tabs = new ChainTabs(Book.Select(b => (b.Name, Controls.Instance?.KeyLabel(b.Key) ?? "")).ToArray(), on, k => { Sound.Sfx.Page(); G.Open(Book[k].Kind); })
                { Position = new Vector2(40, 16) };
            AddChild(tabs);
        }
        var plaque = new Plaque(title, 34, 120);"""),
]
