p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src\Ui\Pack.cs'
s = open(p, encoding='utf-8').read()
pairs = [
# Inventory: the doc comment
("""/// <summary>
/// The pack (the web game's overlays/Inventory.tsx): the survivor as they
/// stand in the middle with what they wear round them, what they carry on
/// the right, and the chosen thing's card with what can be done with it.
/// Hover to read and compare, click to choose, double-click to wear or use.
/// </summary>""",
"""/// <summary>
/// The pack (the web game's overlays/Inventory.tsx): the survivor as they
/// stand in the middle with what they wear round them, what they carry on
/// the right, and the chosen thing's card with what can be done with it.
/// Hover to read and compare (the worn thing beside it), click to choose,
/// double-click or right-click to wear or use. With a pad: move over the
/// slots, the card follows; A wears or uses (or takes off), X leaves it behind.
/// </summary>"""),
("""        var body = Frame("Pack", new Vector2(1320, 700), G.Key(Act.Inventory));""",
"""        var body = Frame("Pack", new Vector2(1320, 660), G.Key(Act.Inventory));"""),
("""        pack.AddChild(ItemViews.Grid(ch.Pack, 6, 64, it => it.Uid == sel, null, it => Select(it.Uid), Primary,
            (it, over) => Tip(it != null && it.Uid != sel ? ItemViews.Card(it, ch, true) : null, over)));
        pack.AddChild(Style.H(18,
            Style.H(4, Glyphs.Icon("coin", 16, Style.GoldHi), Style.Label($"{Math.Floor(ch.Gold)}", Style.UiBold, 16, Style.GoldHi)),
            Style.Label($"{ch.Pack.Count(p => p != null)} / {ch.Pack.Count}", Style.Ui, 15, Style.InkDim),
            Style.Label("Double-click to wear or use", Style.TextItalic, 14, Style.InkFaint)));
        row.AddChild(pack);""",
"""        pack.AddChild(ItemViews.Grid(ch.Pack, 6, 64, it => it.Uid == sel, null, it => Select(it.Uid), Primary,
            (it, over) => Tip(it != null && it.Uid != sel ? ItemViews.Compare(it, ch, true) : null, over), "pack", Drop));
        pack.AddChild(Style.H(18,
            Style.H(4, Glyphs.Icon("coin", 17, Style.GoldHi), Style.Label($"{Math.Floor(ch.Gold)}", Style.UiBold, Style.Small, Style.GoldHi)),
            Style.Label($"{ch.Pack.Count(p => p != null)} / {ch.Pack.Count} carried", Style.Ui, Style.Caption, Style.InkDim)));
        row.AddChild(pack);"""),
("""            detail.AddChild(Style.Label("Choose something to look at it closely.", Style.Text, 16, Style.Ink, true, HorizontalAlignment.Center));
            detail.AddChild(Style.Label("Gear stays with you. Ember fades when you rest; what you carry, and what you wear, does not.", Style.TextItalic, 14, Style.InkDim, true, HorizontalAlignment.Center));
        }
        row.AddChild(detail);
    }

    void Select(string uid) { sel = sel == uid ? null : uid; Refresh(); }""",
"""            detail.AddChild(Style.Label("Choose something to look at it closely.", Style.Text, Style.Body, Style.Ink, true, HorizontalAlignment.Center));
            detail.AddChild(Style.Label("Gear stays with you. Ember fades when you rest; what you carry, and what you wear, does not.", Style.TextItalic, Style.Caption, Style.InkDim, true, HorizontalAlignment.Center));
        }
        row.AddChild(detail);
        body.AddChild(new Control { SizeFlagsVertical = SizeFlags.ExpandFill, MouseFilter = MouseFilterEnum.Ignore });
        body.AddChild(Controls.Instance.UsingPad
            ? Footer((Act.Confirm, "Wear, use or take off"), (Act.Alt, "Leave behind"), (Act.TabNext, "Next page"), (Act.Cancel, "Close"))
            : MouseFooter("Click to choose", "Double-click or right-click to wear or use", "Hover to compare with what you wear"));
    }

    void Select(string uid) { sel = sel == uid ? null : uid; Refresh(); }

    void Drop(ItemInstance it)
    {
        if (Items.Get(it.Def).Kind == ItemKind.Quest) { Sound.Sfx.Deny(); return; }
        if (sel == it.Uid) sel = null;
        G.Journey.Drop(it.Uid);
    }"""),
("""            v.AddChild(ItemViews.Slot(it, 76, it != null && it.Uid == sel, null, false, it != null ? () => Select(it.Uid) : null, null,
                over => Tip(it != null && it.Uid != sel ? ItemViews.Card(it, ch, false) : null, over), glyph, name));""",
"""            var slot = s;
            Action? off = it != null && slot != EquipSlot.Weapon ? () => G.Gear((j, b) => j.Unequip(slot, b)) : null;
            v.AddChild(ItemViews.Slot(it, 76, it != null && it.Uid == sel, null, false, it != null ? () => Select(it.Uid) : null, off,
                over => Tip(it != null && it.Uid != sel ? ItemViews.Card(it, ch, false) : null, over), glyph, name, $"eq:{slot}"));"""),
# Shop
("""        var body = Frame(def.Name, new Vector2(1380, 640), "Esc", who != null ? $"{who.Name}, {who.Role.ToLowerInvariant()}" : null);""",
"""        var body = Frame(def.Name, new Vector2(1380, 640), "Esc", who != null ? $"{who.Name}, {who.Role.ToLowerInvariant()}" : null, fit: true);"""),
("""                it => { sel = (it.Uid, true); Refresh(); }, it => G.Journey.Buy(shop, it.Uid), (it, over) => Tip(it != null && it.Uid != sel?.Uid ? ItemViews.Card(it, ch, true) : null, over)));""",
"""                it => { sel = (it.Uid, true); Refresh(); }, it => G.Journey.Buy(shop, it.Uid), (it, over) => Tip(it != null && it.Uid != sel?.Uid ? ItemViews.Compare(it, ch, true) : null, over), "shelf"));"""),
("""            detail.AddChild(Style.Label("Choose something on the shelf, or in your pack.", Style.Text, 16, Style.Ink, true, HorizontalAlignment.Center));
            detail.AddChild(Style.Label("Prices soften for people who like you.", Style.TextItalic, 14, Style.InkDim, true, HorizontalAlignment.Center));""",
"""            detail.AddChild(Style.Label("Choose something on the shelf, or in your pack.", Style.Text, Style.Body, Style.Ink, true, HorizontalAlignment.Center));
            detail.AddChild(Style.Label("Prices soften for people who like you.", Style.TextItalic, Style.Caption, Style.InkDim, true, HorizontalAlignment.Center));"""),
("""                it => { sel = (it.Uid, false); Refresh(); }, it => G.Journey.Sell(shop, it.Uid), (it, over) => Tip(it != null && it.Uid != sel?.Uid ? ItemViews.Card(it, ch, true) : null, over)),
            Style.H(16, Style.H(4, Glyphs.Icon("coin", 16, Style.GoldHi), Style.Label($"{Math.Floor(ch.Gold)}", Style.UiBold, 16, Style.GoldHi)),
                Style.Label("Double-click to buy or sell", Style.TextItalic, 14, Style.InkFaint)));
        row.AddChild(right);
    }""",
"""                it => { sel = (it.Uid, false); Refresh(); }, it => G.Journey.Sell(shop, it.Uid), (it, over) => Tip(it != null && it.Uid != sel?.Uid ? ItemViews.Card(it, ch, true) : null, over), "mine"),
            Style.H(16, Style.H(4, Glyphs.Icon("coin", 17, Style.GoldHi), Style.Label($"{Math.Floor(ch.Gold)}", Style.UiBold, Style.Small, Style.GoldHi))));
        row.AddChild(right);
        body.AddChild(Controls.Instance.UsingPad
            ? Footer((Act.Confirm, "Buy or sell"), (Act.Cancel, "Close"))
            : MouseFooter("Click to choose", "Double-click or right-click to buy or sell"));
    }"""),
# Stash
("""        var body = Frame("Rook's Storeroom", new Vector2(1120, 560), "Esc", "Kept safe, whatever becomes of you.");""",
"""        var body = Frame("Rook's Storeroom", new Vector2(1120, 560), "Esc", "Kept safe, whatever becomes of you.", fit: true);"""),
("""        row.AddChild(Style.V(8, Style.SubLabel("Stored"),
            ItemViews.Grid(w.Stash, 8, 56, null, null, it => G.Journey.FromStash(it.Uid), null, (it, over) => Tip(it != null ? ItemViews.Card(it, ch, false) : null, over))));
        row.AddChild(Style.V(8, Style.SubLabel("Your pack"),
            ItemViews.Grid(ch.Pack, 6, 56, null, null, it => G.Journey.ToStash(it.Uid), null, (it, over) => Tip(it != null ? ItemViews.Card(it, ch, false) : null, over)),
            Style.Label("Click to move between pack and store", Style.TextItalic, 14, Style.InkFaint)));
    }""",
"""        row.AddChild(Style.V(8, Style.SubLabel($"Stored  ·  {w.Stash.Count(x => x != null)} of {w.Stash.Count}"),
            ItemViews.Grid(w.Stash, 8, 56, null, null, it => G.Journey.FromStash(it.Uid), it => G.Journey.FromStash(it.Uid), (it, over) => Tip(it != null ? ItemViews.Card(it, ch, false) : null, over), "store")));
        row.AddChild(Style.V(8, Style.SubLabel("Your pack"),
            ItemViews.Grid(ch.Pack, 6, 56, null, null, it => G.Journey.ToStash(it.Uid), it => G.Journey.ToStash(it.Uid), (it, over) => Tip(it != null ? ItemViews.Card(it, ch, false) : null, over), "mine")));
        body.AddChild(Controls.Instance.UsingPad ? Footer((Act.Confirm, "Move between pack and store"), (Act.Cancel, "Close")) : MouseFooter("Click to move between pack and store"));
    }"""),
]
for old, new in pairs:
    assert old in s, old[:80]
    s = s.replace(old, new, 1)
open(p, 'w', encoding='utf-8', newline='').write(s)

# Overlay: the mouse's footer
p2 = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src\Ui\Overlay.cs'
s = open(p2, encoding='utf-8').read()
old = """    /* ------------------------------------------------ hovering a thing -- */"""
new = """    /// <summary>The same footer for the mouse: what clicks do, quietly.</summary>
    protected static Control MouseFooter(params string[] lines)
    {
        var l = Style.Label(string.Join("   ·   ", lines), Style.TextItalic, Style.Caption, Style.InkDim, false, HorizontalAlignment.Center);
        return l;
    }

    /* ------------------------------------------------ hovering a thing -- */"""
assert old in s
s = s.replace(old, new, 1)
open(p2, 'w', encoding='utf-8', newline='').write(s)
print('done')
