p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src\Ui\ItemViews.cs'
s = open(p, encoding='utf-8').read()
pairs = [
("""    public static Control Slot(ItemInstance? it, int size, bool selected = false, int? price = null, bool refused = false,
        Action? onClick = null, Action? onDouble = null, Action<Control?>? onHover = null, string? emptyGlyph = null, string? caption = null,
        string? navId = null, Action? onAlt = null)
    {
        var box = new Panel { CustomMinimumSize = new Vector2(size, size), MouseFilter = Control.MouseFilterEnum.Stop };""",
"""    public static SlotView Slot(ItemInstance? it, int size, bool selected = false, int? price = null, bool refused = false,
        Action? onClick = null, Action? onDouble = null, Action<Control?>? onHover = null, string? emptyGlyph = null, string? caption = null,
        string? navId = null, Action? onAlt = null, bool fresh = false, bool dim = false, bool dear = false)
    {
        var box = new SlotView { CustomMinimumSize = new Vector2(size, size), MouseFilter = Control.MouseFilterEnum.Stop, Item = it };"""),
("""            if (price is int p)
            {
                // The price on a dark tag at the top, with its coin.
                var tag = Style.Panel(Style.Box(new Color(0.03f, 0.025f, 0.04f, 0.85f), Style.GoldDim, 1, 3, 3), Style.H(2, Glyphs.Icon("coin", 11, Style.GoldHi), Style.Label($"{p}", Style.UiHeavy, Style.Badge, Style.GoldHi)));
                tag.MouseFilter = Control.MouseFilterEnum.Ignore;
                tag.Position = new Vector2(2, 2);
                box.AddChild(tag);
            }
            if (refused) box.Modulate = new Color(1, 1, 1, 0.4f);""",
"""            if (price is int p)
            {
                // The price on a dark tag at the top, with its coin; red when it is more than you have.
                var pc = dear ? Style.Bad : Style.GoldHi;
                var tag = Style.Panel(Style.Box(new Color(0.03f, 0.025f, 0.04f, 0.85f), dear ? Style.Bad with { A = 0.6f } : Style.GoldDim, 1, 3, 3), Style.H(2, Glyphs.Icon("coin", 11, pc), Style.Label($"{p}", Style.UiHeavy, Style.Badge, pc)));
                tag.MouseFilter = Control.MouseFilterEnum.Ignore;
                tag.Position = new Vector2(2, 2);
                box.AddChild(tag);
            }
            // New since the pack was last looked at: an ember mark until it is.
            if (fresh)
            {
                var mark = Style.Panel(Style.Box(Style.Ember, Style.EmberHi, 1, 6, 3), Style.Label("NEW", Style.UiHeavy, 10, new Color("#2a1206"), false, HorizontalAlignment.Center, false));
                mark.MouseFilter = Control.MouseFilterEnum.Ignore;
                mark.Position = new Vector2(2, 2);
                box.AddChild(mark);
            }
            if (refused || dim) box.Modulate = new Color(1, 1, 1, dim ? 0.25f : 0.4f);"""),
("""    /// <summary>A grid of slots (the pack, a shelf, the storeroom); with a name, each slot can take focus.</summary>
    public static GridContainer Grid(IEnumerable<ItemInstance?> items, int cols, int size, Func<ItemInstance, bool>? selected = null, Func<ItemInstance, int?>? price = null,
        Action<ItemInstance>? onClick = null, Action<ItemInstance>? onDouble = null, Action<ItemInstance?, Control?>? onHover = null,
        string? nav = null, Action<ItemInstance>? onAlt = null)
    {""",
"""    /// <summary>A grid of slots (the pack, a shelf, the storeroom); with a name, each slot can take focus;
    /// setup readies each cell for dragging and dropping (its index, its item, the slot).</summary>
    public static GridContainer Grid(IEnumerable<ItemInstance?> items, int cols, int size, Func<ItemInstance, bool>? selected = null, Func<ItemInstance, int?>? price = null,
        Action<ItemInstance>? onClick = null, Action<ItemInstance>? onDouble = null, Action<ItemInstance?, Control?>? onHover = null,
        string? nav = null, Action<ItemInstance>? onAlt = null, Action<int, ItemInstance?, SlotView>? setup = null)
    {"""),
("""            g.AddChild(Slot(it, size, it != null && selected?.Invoke(it) == true, p, it != null && price != null && p == null,
                it != null && onClick != null ? () => onClick(it) : null, it != null && onDouble != null ? () => onDouble(it) : null,
                onHover != null ? c => onHover(it, c) : null, null, null, nav != null ? $"{nav}:{i}" : null, it != null && onAlt != null ? () => onAlt(it) : null));
            i++;""",
"""            var slot = Slot(it, size, it != null && selected?.Invoke(it) == true, p, it != null && price != null && p == null,
                it != null && onClick != null ? () => onClick(it) : null, it != null && onDouble != null ? () => onDouble(it) : null,
                onHover != null ? c => onHover(it, c) : null, null, null, nav != null ? $"{nav}:{i}" : null, it != null && onAlt != null ? () => onAlt(it) : null);
            setup?.Invoke(i, it, slot);
            g.AddChild(slot);
            i++;"""),
]
for old, new in pairs:
    assert old in s, old[:80]
    s = s.replace(old, new, 1)
open(p, 'w', encoding='utf-8', newline='').write(s)
print('done')
