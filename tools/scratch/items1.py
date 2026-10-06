p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src\Ui\ItemViews.cs'
s = open(p, encoding='utf-8').read()
pairs = [
("""    /// <summary>One slot of a grid: empty, or an item rimmed in its rarity.</summary>
    public static Control Slot(ItemInstance? it, int size, bool selected = false, int? price = null, bool refused = false,
        Action? onClick = null, Action? onDouble = null, Action<Control?>? onHover = null, string? emptyGlyph = null, string? caption = null)
    {
        var box = new Panel { CustomMinimumSize = new Vector2(size, size), MouseFilter = Control.MouseFilterEnum.Stop };
        var rim = it != null ? Style.RarityOf(it.Rarity) with { A = selected ? 1 : 0.55f } : Style.Line with { A = 0.18f };
        var bg = it != null ? new Color(0.08f, 0.07f, 0.09f, 0.95f).Lerp(Style.RarityOf(it.Rarity), 0.08f) : new Color(0.05f, 0.045f, 0.06f, 0.8f);
        box.AddThemeStyleboxOverride("panel", Style.Box(bg, rim, selected ? 2 : 1, 4, 0));""",
"""    /// <summary>One slot of a grid: empty, or an item rimmed in its rarity. A
    /// click chooses it, a double click or a right click does its first thing
    /// (wear, use, buy); with a name it can take focus, where A does that first
    /// thing, X its second (onAlt), and its card shows beside it.</summary>
    public static Control Slot(ItemInstance? it, int size, bool selected = false, int? price = null, bool refused = false,
        Action? onClick = null, Action? onDouble = null, Action<Control?>? onHover = null, string? emptyGlyph = null, string? caption = null,
        string? navId = null, Action? onAlt = null)
    {
        var box = new Panel { CustomMinimumSize = new Vector2(size, size), MouseFilter = Control.MouseFilterEnum.Stop };
        var rim = it != null ? Style.RarityOf(it.Rarity) with { A = selected ? 1 : 0.55f } : Style.Line with { A = 0.18f };
        var bg = it != null ? new Color(0.08f, 0.07f, 0.09f, 0.95f).Lerp(Style.RarityOf(it.Rarity), 0.08f) : new Color(0.05f, 0.045f, 0.06f, 0.8f);
        var flat = Style.Box(bg, rim, selected ? 2 : 1, 4, 0);
        box.AddThemeStyleboxOverride("panel", UiArt.Frame(it != null ? $"slot_{Math.Clamp(it.Rarity, 0, 5)}" : "slot", flat));"""),
("""            if (it.Qty > 1)
            {
                var q = Style.Label(it.Qty.ToString(), Style.UiBold, 13, Style.Ink);
                q.Position = new Vector2(size - 20, size - 20);
                box.AddChild(q);
            }""",
"""            if (it.Qty > 1)
            {
                // How many, as a count (x3), never to be mistaken for a price.
                var q = Style.Label($"×{it.Qty}", Style.UiHeavy, Style.Badge, Style.Ink);
                q.HorizontalAlignment = HorizontalAlignment.Right;
                q.Size = new Vector2(size - 6, 16);
                q.Position = new Vector2(0, size - 18);
                box.AddChild(q);
            }"""),
("""            if (price is int p)
            {
                var pl = Style.Label($"{p}", Style.UiBold, 12, Style.GoldHi);
                pl.Position = new Vector2(4, size - 19);
                box.AddChild(pl);
            }""",
"""            if (price is int p)
            {
                // The price on a dark tag at the top, with its coin.
                var tag = Style.Panel(Style.Box(new Color(0.03f, 0.025f, 0.04f, 0.85f), Style.GoldDim, 1, 3, 3), Style.H(2, Glyphs.Icon("coin", 11, Style.GoldHi), Style.Label($"{p}", Style.UiHeavy, Style.Badge, Style.GoldHi)));
                tag.MouseFilter = Control.MouseFilterEnum.Ignore;
                tag.Position = new Vector2(2, 2);
                box.AddChild(tag);
            }"""),
("""        box.GuiInput += e =>
        {
            if (e is not InputEventMouseButton { Pressed: true, ButtonIndex: MouseButton.Left } mb || it == null) return;
            if (mb.DoubleClick) onDouble?.Invoke(); else onClick?.Invoke();
        };
        if (onHover != null)
        {
            box.MouseEntered += () => onHover(it != null ? box : null);
            box.MouseExited += () => onHover(null);
        }
        return box;
    }""",
"""        box.GuiInput += e =>
        {
            if (e is not InputEventMouseButton { Pressed: true } mb || it == null) return;
            if (mb.ButtonIndex == MouseButton.Right) onDouble?.Invoke();
            else if (mb.ButtonIndex == MouseButton.Left) { if (mb.DoubleClick) onDouble?.Invoke(); else onClick?.Invoke(); }
        };
        if (onHover != null)
        {
            box.MouseEntered += () => onHover(it != null ? box : null);
            box.MouseExited += () => onHover(null);
        }
        if (navId != null)
            Nav.Mark(box, navId, it != null ? onDouble ?? onClick ?? (() => { }) : () => { }, it != null ? onAlt : null, null,
                () => onHover?.Invoke(it != null ? box : null), () => onHover?.Invoke(null));
        return box;
    }"""),
("""    /// <summary>A grid of slots (the pack, a shelf, the storeroom).</summary>
    public static GridContainer Grid(IEnumerable<ItemInstance?> items, int cols, int size, Func<ItemInstance, bool>? selected = null, Func<ItemInstance, int?>? price = null,
        Action<ItemInstance>? onClick = null, Action<ItemInstance>? onDouble = null, Action<ItemInstance?, Control?>? onHover = null)
    {
        var g = new GridContainer { Columns = cols, MouseFilter = Control.MouseFilterEnum.Ignore };
        g.AddThemeConstantOverride("h_separation", 5);
        g.AddThemeConstantOverride("v_separation", 5);
        foreach (var it in items)
        {
            int? p = it != null && price != null ? price(it) : null;
            g.AddChild(Slot(it, size, it != null && selected?.Invoke(it) == true, p, it != null && price != null && p == null,
                it != null && onClick != null ? () => onClick(it) : null, it != null && onDouble != null ? () => onDouble(it) : null,
                onHover != null ? c => onHover(it, c) : null));
        }
        return g;
    }""",
"""    /// <summary>A grid of slots (the pack, a shelf, the storeroom); with a name, each slot can take focus.</summary>
    public static GridContainer Grid(IEnumerable<ItemInstance?> items, int cols, int size, Func<ItemInstance, bool>? selected = null, Func<ItemInstance, int?>? price = null,
        Action<ItemInstance>? onClick = null, Action<ItemInstance>? onDouble = null, Action<ItemInstance?, Control?>? onHover = null,
        string? nav = null, Action<ItemInstance>? onAlt = null)
    {
        var g = new GridContainer { Columns = cols, MouseFilter = Control.MouseFilterEnum.Ignore };
        g.AddThemeConstantOverride("h_separation", 5);
        g.AddThemeConstantOverride("v_separation", 5);
        int i = 0;
        foreach (var it in items)
        {
            int? p = it != null && price != null ? price(it) : null;
            g.AddChild(Slot(it, size, it != null && selected?.Invoke(it) == true, p, it != null && price != null && p == null,
                it != null && onClick != null ? () => onClick(it) : null, it != null && onDouble != null ? () => onDouble(it) : null,
                onHover != null ? c => onHover(it, c) : null, null, null, nav != null ? $"{nav}:{i}" : null, it != null && onAlt != null ? () => onAlt(it) : null));
            i++;
        }
        return g;
    }

    /// <summary>The worn thing an item would replace, if any (the second ring's place when the first is taken).</summary>
    public static ItemInstance? Against(ItemInstance it, CharacterData ch)
    {
        var def = Items.Get(it.Def);
        if (Items.SlotFor(def) is not EquipSlot slot) return null;
        if (Enum.GetValues<EquipSlot>().Any(s => ch.Equipment[s]?.Uid == it.Uid)) return null;
        var target = slot == EquipSlot.Ring1 && ch.Equipment.Ring1 != null && ch.Equipment.Ring2 == null ? EquipSlot.Ring2 : slot;
        return ch.Equipment[target];
    }

    /// <summary>A hovered thing's card, with the worn one it would replace beside it
    /// (the ARPGs' side-by-side comparison: docs/UI_RESEARCH.md 7.1).</summary>
    public static Control Compare(ItemInstance it, CharacterData ch, bool compare)
    {
        var card = Card(it, ch, compare);
        if (!compare || Against(it, ch) is not { } worn) return card;
        var h = Style.H(Style.Gap2, card);
        var w = Style.V(4, Style.Label("WORN NOW", Style.UiHeavy, Style.Badge, Style.InkDim), Card(worn, ch, false, null, 300, true));
        h.AddChild(w);
        return h;
    }"""),
("""    /// <summary>Everything an item is, on one card.</summary>
    public static PanelContainer Card(ItemInstance it, CharacterData? ch, bool compare, Control? actions = null, int width = 340)
    {
        var def = Items.Get(it.Def);
        var col = Style.RarityOf(it.Rarity);
        var card = Style.Panel(Style.Box(new Color(0.07f, 0.062f, 0.08f, 0.98f), col with { A = 0.6f }, 1, 5, 14));""",
"""    /// <summary>Everything an item is, on one card (worn: the quieter card beside a comparison).</summary>
    public static PanelContainer Card(ItemInstance it, CharacterData? ch, bool compare, Control? actions = null, int width = 340, bool worn = false)
    {
        var def = Items.Get(it.Def);
        var col = Style.RarityOf(it.Rarity);
        var card = Style.Panel(UiArt.Frame(worn ? "tooltip_worn" : "tooltip", Style.Box(new Color(0.07f, 0.062f, 0.08f, worn ? 0.94f : 0.98f), col with { A = worn ? 0.35f : 0.6f }, 1, 5, 14)));"""),
("""        names.AddChild(Style.Label($"{Inventory.RarityName(it)} {KindNames.GetValueOrDefault(def.Kind, def.Kind.ToString())}{(def.Unique ? " · Unique" : "")}", Style.Ui, 13, Style.InkDim));""",
"""        var kind = Style.H(Style.Gap2, Style.Label($"{Inventory.RarityName(it)} {KindNames.GetValueOrDefault(def.Kind, def.Kind.ToString())}{(def.Unique ? " · Unique" : "")}", Style.Ui, Style.Caption, Style.InkDim), Style.Gems(it.Rarity, 5));
        kind.Alignment = BoxContainer.AlignmentMode.Begin;
        names.AddChild(kind);"""),
("""        v.AddChild(Style.Label(def.Description, Style.Text, 15, Style.Ink, true));
        var lines = Inventory.Lines(it).Where(l => l != "").ToList();
        if (lines.Count > 0) v.AddChild(Style.V(1, lines.Select(l => (Control)Style.Label(l, Style.UiBold, 14, new Color("#9ad8ff"), true)).ToArray()));
        if (def.Downside != null) v.AddChild(Style.Label(def.Downside, Style.UiBold, 14, Style.Bad, true));
        foreach (var t in def.Tags ?? new())
            if (TagLines.TryGetValue(t, out var tl)) v.AddChild(Style.H(6, Glyphs.Icon("eye", 13, Style.Gold), Style.Label(tl, Style.TextItalic, 14, Style.GoldHi, true)));
        if (def.Lore != null) v.AddChild(Style.Label(def.Lore, Style.TextItalic, 14, Style.InkDim, true));
        if (it.History is { Count: > 0 } h) v.AddChild(Style.V(1, h.Select(x => (Control)Style.Label(x, Style.TextItalic, 13, Style.InkFaint, true)).ToArray()));""",
"""        v.AddChild(Style.Label(def.Description, Style.Text, Style.Small, Style.Ink, true));
        var lines = Inventory.Lines(it).Where(l => l != "").ToList();
        if (lines.Count > 0) v.AddChild(Style.V(1, lines.Select(l => (Control)Style.Label(l, Style.UiBold, Style.Caption, new Color("#9ad8ff"), true)).ToArray()));
        if (def.Downside != null) v.AddChild(Style.Label(def.Downside, Style.UiBold, Style.Caption, Style.Bad, true));
        foreach (var t in def.Tags ?? new())
            if (TagLines.TryGetValue(t, out var tl)) v.AddChild(Style.H(6, Glyphs.Icon("eye", 14, Style.Gold), Style.Label(tl, Style.TextItalic, Style.Caption, Style.GoldHi, true)));
        if (def.Lore != null) v.AddChild(Style.Label(def.Lore, Style.TextItalic, Style.Caption, Style.InkDim, true));
        if (it.History is { Count: > 0 } h) v.AddChild(Style.V(1, h.Select(x => (Control)Style.Label(x, Style.TextItalic, Style.Caption, Style.InkFaint, true)).ToArray()));"""),
("""                    v.AddChild(Style.Label($"Instead of {(against != null ? Inventory.Name(against) : "nothing")}", Style.UiBold, 13, Style.InkDim));
                    foreach (var (key, before, after) in diffs)
                    {
                        var (text, good) = Delta(key, before, after);
                        v.AddChild(Style.Label(text, Style.UiBold, 14, good ? Style.Good : Style.Bad));
                    }""",
"""                    v.AddChild(Style.Label($"Instead of {(against != null ? Inventory.Name(against) : "nothing")}", Style.UiBold, Style.Caption, Style.InkDim));
                    foreach (var (key, before, after) in diffs)
                    {
                        // Better or worse said three ways: colour, the sign, and a word.
                        var (text, good) = Delta(key, before, after);
                        v.AddChild(Style.H(6, Style.Label(good ? "better" : "worse", Style.UiHeavy, Style.Badge, good ? Style.Good : Style.Bad), Style.Label(text, Style.UiBold, Style.Small, good ? Style.Good : Style.Bad)));
                    }"""),
("""        if (it.Qty > 1) foot.AddChild(Style.Label($"×{it.Qty}", Style.UiBold, 13, Style.InkDim));
        foot.AddChild(Style.H(4, Glyphs.Icon("coin", 13, Style.GoldHi), Style.Label($"{def.Value * Math.Max(1, it.Qty)}", Style.UiBold, 13, Style.GoldHi)));""",
"""        if (it.Qty > 1) foot.AddChild(Style.Label($"×{it.Qty}", Style.UiBold, Style.Caption, Style.InkDim));
        foot.AddChild(Style.H(4, Glyphs.Icon("coin", 14, Style.GoldHi), Style.Label($"{def.Value * Math.Max(1, it.Qty)}", Style.UiBold, Style.Caption, Style.GoldHi)));"""),
]
for old, new in pairs:
    assert old in s, old[:70]
    s = s.replace(old, new, 1)
open(p, 'w', encoding='utf-8', newline='').write(s)
print('done')
