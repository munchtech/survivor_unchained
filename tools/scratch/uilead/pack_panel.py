p = 'godot/src/Ui/Pack.cs'
s = open(p, encoding='utf-8', newline='').read()
nl = '\r\n' if '\r\n' in s else '\n'
s = s.replace('\r\n', '\n')

def rep(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:80])
    s = s.replace(old, new)

a = s.index('    protected override void Build()\n    {\n        var ch = Ch;\n        if (!seeded)')
b = s.index('    static IEnumerable<ItemInstance> Carried(CharacterData ch)')
new_build = '''    /// <summary>The pack is a panel at the right; the survivor stands in view between it and the
    /// thing read closely at the left.</summary>
    public override float CameraShift => -188;
    const float PanelW = 880;

    protected override void Build()
    {
        var ch = Ch;
        if (!seeded) { seeded = true; foreach (var it in Carried(ch)) seen.Add(it.Uid); }
        // A panel at the right (docs/UI_DESIGN.md 6, "Page or panel"): the pack is what is tweaked
        // mid-play, so the world stays in view, as in Diablo IV, PoE and Last Epoch.
        var area = SidePanel("Pack", $"{ch.Name}  ·  Level {ch.Level} {Callings.Background(ch.Background).Name} {Callings.Archetype(ch.Archetype).Name}", true, PanelW);
        var v = Style.V(Style.Gap2);
        v.Size = area.Size;
        area.AddChild(v);

        // What they wear, round them.
        var doll = Style.H(Style.Gap3, Column(Left, ch), Figure(ch, 300, 404), Column(Right, ch));
        doll.Alignment = BoxContainer.AlignmentMode.Center;
        v.AddChild(doll);
        var standWell = Style.Panel(Style.Well(10));
        stats = Style.V(2);
        standWell.AddChild(stats);
        v.AddChild(standWell);
        ShowStats(null);

        // What they carry.
        v.AddChild(FilterRow());
        var well = Style.Panel(Style.Well(10));
        var centre = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
        centre.AddChild(ItemViews.Grid(ch.Pack, 8, 84, it => it.Uid == sel, null, it => Select(it.Uid), Primary, Hover, "pack", Leave, SetupCell));
        well.AddChild(centre);
        v.AddChild(well);
        v.AddChild(Style.H(18,
            Style.H(4, Glyphs.Icon("coin", 18, Style.GoldHi), Style.Label($"{Math.Floor(ch.Gold)} gold", Style.UiBold, Style.Body, Style.GoldHi)),
            Style.Label($"{ch.Pack.Count(p => p != null)} of {ch.Pack.Count} carried", Style.Ui, Style.Small, Style.InkDim)));

        // The thing chosen, read closely, at the left over the world: beside the survivor, not under the panel.
        inspect = Style.V(Style.Gap2);
        inspect.Position = new Vector2(40, 120);
        inspect.Size = new Vector2(480, 900);
        AddChild(inspect);
        ShowInspect(sel != null ? Inventory.Find(ch, sel)?.Item : null);
        foot = new Control { CustomMinimumSize = new Vector2(PanelW - 40, 30), MouseFilter = MouseFilterEnum.Ignore };
        SideFooter(foot);
        Footer();
    }

'''
s = s[:a] + new_build + s[b:]

# The doll's slots, smaller in the panel.
rep('var view = ItemViews.Slot(it, 104, it != null && it.Uid == sel,', 'var view = ItemViews.Slot(it, 76, it != null && it.Uid == sel,')
rep('''    Control Column(EquipSlot[] slots, CharacterData ch)
    {
        var v = Style.V(Style.Gap3);''', '''    Control Column(EquipSlot[] slots, CharacterData ch)
    {
        var v = Style.V(Style.Gap1);''')

# The read-closely column: nothing when nothing is chosen (the world shows), the pair stacked.
rep('''        if (it == null)
        {
            inspect.AddChild(Style.Gap(Style.Gap4));
            inspect.AddChild(Style.Label(Controls.Instance.UsingPad ? "Move over a thing to read it." : "Choose a thing to read it closely; drag it onto yourself to wear it.", Style.Text, Style.Body, Style.Ink, true, HorizontalAlignment.Center));
            inspect.AddChild(Style.Label("Gear stays with you. Ember fades when you rest; what you carry, and what you wear, does not.", Style.TextItalic, Style.Caption, Style.InkDim, true, HorizontalAlignment.Center));
            return;
        }''', '''        if (it == null) return;''')
rep('''            var pair = Style.H(Style.Gap3, ItemViews.Card(it, Ch, true, acts, 580));
            var worn = ItemViews.Against(it, Ch);
            var side = Style.V(4, Style.Label("WORN NOW", Style.UiHeavy, Style.Badge, Style.InkDim));
            if (worn != null) side.AddChild(ItemViews.Card(worn, Ch, false, null, 380, true));
            else
            {
                var empty = Style.Panel(Style.Slab(16), Style.Label("Nothing in that place: wearing it is all gain.", Style.TextItalic, Style.Small, Style.InkDim, true));
                empty.CustomMinimumSize = new Vector2(380, 0);
                side.AddChild(empty);
            }
            pair.AddChild(side);
            inspect.AddChild(Style.Scroll(pair));
            return;
        }
        var card = ItemViews.Card(it, Ch, loc.InPack, acts, 980);
        inspect.AddChild(Style.Scroll(card));''', '''            inspect.AddChild(ItemViews.Card(it, Ch, true, acts, 480));
            var worn = ItemViews.Against(it, Ch);
            inspect.AddChild(Style.Label("WORN NOW", Style.UiHeavy, Style.Badge, Style.InkDim));
            if (worn != null) inspect.AddChild(ItemViews.Card(worn, Ch, false, null, 480, true));
            else
            {
                var empty = Style.Panel(Style.Slab(16), Style.Label("Nothing in that place: wearing it is all gain.", Style.TextItalic, Style.Small, Style.InkDim, true));
                empty.CustomMinimumSize = new Vector2(480, 0);
                inspect.AddChild(empty);
            }
            return;
        }
        inspect.AddChild(ItemViews.Card(it, Ch, loc.InPack, acts, 480));''')
rep('''        f.Size = new Vector2(1840, 30);
        foot.AddChild(f);''', '''        f.Size = foot.CustomMinimumSize;
        foot.AddChild(f);''')
# The footer's lines, short enough for the panel.
rep('''            f = Overlay.Footer((Act.Confirm, "Wear, use or take off"), (Act.Alt, "Leave behind"), (Act.Alt2, "Sort"), (Act.SubNext, "Filter"), (Act.TabNext, "Next page"), (Act.Cancel, "Close"));
        else f = MouseFooter("Right-click or double-click to wear or use", "drag onto yourself to wear, off to take off", "hover to compare");''',
'''            f = Overlay.Footer((Act.Confirm, "Wear or use"), (Act.Alt, "Leave"), (Act.Alt2, "Sort"), (Act.SubNext, "Filter"), (Act.Cancel, "Close"));
        else f = MouseFooter("Right-click to wear or use", "drag to wear or take off", "hover to compare");''')
open(p, 'w', encoding='utf-8', newline='').write(s.replace('\n', nl))
print('ok')
