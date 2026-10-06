R = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src\Ui'
p = R + r'\Pack.cs'
s = open(p, encoding='utf-8').read()

def cut(a, b, new):
    global s
    i = s.index(a)
    j = s.index(b, i)
    s = s[:i] + new + s[j:]

def rep(old, new):
    global s
    assert old in s, old[:90]
    s = s.replace(old, new, 1)

cut("""    protected override void Build()
    {
        var ch = G.Journey.Ch;
        var w = G.Journey.World;
        var def = Lore.Shops[shop];""", """    void Buy(ItemInstance it) => Buy(it.Uid);""", '''    protected override void Build()
    {
        var ch = G.Journey.Ch;
        var w = G.Journey.World;
        var def = Lore.Shops[shop];
        var who = Lore.Person(shop);
        var page = Page(def.Name, who != null ? $"{who.Name}, {who.Role.ToLowerInvariant()}" : null, null, "Esc");

        // The merchant, as large as the wares: who you are dealing with, and how they deal with you.
        var them = Pane(page, new Rect2(0, 0, 440, 920));
        if (who?.Person != null)
        {
            var frame = Style.Panel(Style.Well(0));
            frame.CustomMinimumSize = new Vector2(400, 470);
            frame.AddChild(new Portrait(new Vector2I(400, 470), Portrait.Framing.Bust).Of(who.Person, who.Arms, who.Scale ?? 1));
            them.AddChild(frame);
        }
        if (who != null)
        {
            var plaque = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
            plaque.AddChild(new Plaque(who.Name, 26, 40));
            them.AddChild(plaque);
            var st = w.Npc(shop);
            double mod = G.Journey.PriceMod(shop);
            int pct = (int)Math.Round((mod - 1) * 100);
            them.AddChild(Style.Label(Style.Cap1(Rules.Attitude(st)), Style.TextItalic, Style.Body, Style.InkDim, false, HorizontalAlignment.Center));
            them.AddChild(Style.Label(pct == 0 ? "Their usual prices" : pct < 0 ? $"Prices {-pct}% under their usual" : $"Prices {pct}% over their usual",
                Style.UiBold, Style.Small, pct < 0 ? Style.Good : pct > 0 ? Style.Bad : Style.Ink, false, HorizontalAlignment.Center));
        }
        them.AddChild(Style.Label(def.BuysAll ? "They will buy anything." : $"They buy {string.Join(", ", def.Buys.Select(b => b.Replace('_', ' ')))}, at {def.Pays * 100:0}% of its worth.",
            Style.TextItalic, Style.Small, Style.InkDim, true, HorizontalAlignment.Center));

        // The counter: their wares in a well of large slots, the chosen thing read closely beneath.
        var counter = Pane(page, new Rect2(470, 0, 880, 920));
        var stock = w.Shops.GetValueOrDefault(shop)?.Stock ?? new();
        var shelf = stock.Cast<ItemInstance?>().ToList();
        while (shelf.Count < 21 || shelf.Count % 7 != 0) shelf.Add(null);
        counter.AddChild(new Section("Their wares", "a price in red is more than you have"));
        var well = Style.Panel(Style.Well(12));
        var centre = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
        centre.AddChild(ItemViews.Grid(shelf, 7, 104, it => sel is { Buy: true } s && s.Uid == it.Uid, it => G.Journey.PriceOf(shop, it.Uid, true),
            it => Choose(it.Uid, true), Buy, (it, over) => Hover(it, over, true), "shelf", null, (i, it, v) =>
            {
                if (it != null) v.Drag = $"shelf:{it.Uid}";
                v.CanTake = d => d.StartsWith("mine:");
                v.Take = d => Sell(d[5..]);
            }, dear: it => G.Journey.PriceOf(shop, it.Uid, true) is int p && p > ch.Gold));
        well.AddChild(centre);
        counter.AddChild(well);
        counter.AddChild(new Section("Read closely"));
        inspect = Style.V(Style.Gap2);
        inspect.SizeFlagsVertical = SizeFlags.ExpandFill;
        counter.AddChild(inspect);

        // What you carry, and what you have to spend.
        var mine = Pane(page, new Rect2(1380, 0, 460, 920));
        mine.AddChild(new Section("Your pack", $"{ch.Pack.Count(p => p != null)} of {ch.Pack.Count}"));
        var mwell = Style.Panel(Style.Well(10));
        var mc = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
        mc.AddChild(ItemViews.Grid(ch.Pack, 5, 78, it => sel is { Buy: false } s && s.Uid == it.Uid, it => G.Journey.PriceOf(shop, it.Uid, false),
            it => Choose(it.Uid, false), it => Sell(it.Uid), (it, over) => Hover(it, over, false), "mine", null, (i, it, v) =>
            {
                if (it != null) v.Drag = $"mine:{it.Uid}";
                v.CanTake = d => d.StartsWith("shelf:");
                v.Take = d => Buy(d[6..]);
            }));
        mwell.AddChild(mc);
        mine.AddChild(mwell);
        var purse = Style.H(Style.Gap2, Glyphs.Icon("coin", 34, Style.GoldHi), Style.Label($"{Math.Floor(ch.Gold)}", Style.Display, 40, Style.GoldHi), Style.Label("gold", Style.TextItalic, Style.Body, Style.InkDim));
        purse.Alignment = BoxContainer.AlignmentMode.Center;
        mine.AddChild(purse);
        mine.AddChild(Style.Label("What they will not buy is dimmed.", Style.TextItalic, Style.Caption, Style.InkDim, true, HorizontalAlignment.Center));
        ShowInspect();
        PageFooter(Controls.Instance.UsingPad
            ? Footer((Act.Confirm, "Buy or sell"), (Act.Cancel, "Close"))
            : MouseFooter("Right-click or double-click to buy or sell", "or drag it across", "hover to compare"));
    }

''')
rep("""        if (chosen == null || sel is not var (_, buying))
        {
            inspect.AddChild(Style.Gap(60));""", """        if (chosen == null || sel is not var (_, buying))
        {
            inspect.AddChild(Style.Gap(Style.Gap4));""")
rep("""        inspect.AddChild(ItemViews.Card(chosen, ch, true, act, 420));
    }""", """        // Bought gear reads beside what it would replace, as in the pack.
        var card = ItemViews.Card(chosen, ch, true, act, buying && ItemViews.Against(chosen, ch) != null ? 480 : 820);
        if (buying && ItemViews.Against(chosen, ch) is { } worn)
            inspect.AddChild(Style.H(Style.Gap3, card, Style.V(4, Style.Label("WORN NOW", Style.UiHeavy, Style.Badge, Style.InkDim), ItemViews.Card(worn, ch, false, null, 320, true))));
        else inspect.AddChild(card);
    }""")

cut("""        var body = Frame("Rook's Storeroom", new Vector2(1240, 560), "Esc", "Kept safe, whatever becomes of you.", fit: true);""",
    """    }
}""", """        var page = Page("Rook's Storeroom", "Kept safe, whatever becomes of you", null, "Esc");
        // The store is the larger: it keeps what a life on the road cannot carry.
        var store = Pane(page, new Rect2(0, 0, 1140, 920));
        store.AddChild(new Section("Stored", $"{w.Stash.Count(x => x != null)} of {w.Stash.Count}"));
        var well = Style.Panel(Style.Well(12));
        var sc = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
        sc.AddChild(ItemViews.Grid(w.Stash, 10, 98, null, null, it => G.Journey.FromStash(it.Uid), it => G.Journey.FromStash(it.Uid), (it, over) => Tip(it != null ? ItemViews.Card(it, ch, false) : null, over), "store", null,
            (i, it, v) => { if (it != null) v.Drag = $"store:{it.Uid}"; v.CanTake = d => d.StartsWith("mine:"); v.Take = d => G.Journey.ToStash(d[5..]); }));
        well.AddChild(sc);
        store.AddChild(well);
        store.AddChild(Style.Label("Whatever happens to you on the road, what is here stays here: Rook keeps the key.", Style.TextItalic, Style.Small, Style.InkDim, true));
        var mine = Pane(page, new Rect2(1170, 0, 670, 920));
        mine.AddChild(new Section("Your pack", $"{ch.Pack.Count(p => p != null)} of {ch.Pack.Count}"));
        var mwell = Style.Panel(Style.Well(12));
        var mc = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
        mc.AddChild(ItemViews.Grid(ch.Pack, 6, 98, null, null, it => G.Journey.ToStash(it.Uid), it => G.Journey.ToStash(it.Uid), (it, over) => Tip(it != null ? ItemViews.Card(it, ch, false) : null, over), "mine", null,
            (i, it, v) => { if (it != null) v.Drag = $"mine:{it.Uid}"; v.CanTake = d => d.StartsWith("store:"); v.Take = d => G.Journey.FromStash(d[6..]); }));
        mwell.AddChild(mc);
        mine.AddChild(mwell);
        PageFooter(Controls.Instance.UsingPad ? Footer((Act.Confirm, "Move between pack and store"), (Act.Cancel, "Close")) : MouseFooter("Click, or drag, to move between pack and store"));
""")
open(p, 'w', encoding='utf-8', newline='').write(s)
print('ok')
