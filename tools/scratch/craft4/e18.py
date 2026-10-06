from ed import sub

sub("src/Ui/Forge.cs", [
# The slurry's steep as type: its name the held act, the odds under it, no card.
("""        var slab = Style.V(Style.Gap3);
        var top = Style.H(10, Style.Label("Steep it in slurry", Style.TextBold, 19, ItemViews.SlurryGreen, false, HorizontalAlignment.Left, false));
        if (Crafting.Line(crafter, "jar") is { } said) top.AddChild(Style.Label($"“{said}”", Style.TextItalic, 15, Kit.Dim, true));
        ((Control)top.GetChild(top.GetChildCount() - 1)).SizeFlagsHorizontal = SizeFlags.ExpandFill;
        slab.AddChild(top);
        slab.AddChild(SlurryOdds(it, LeftW - 2 * Pad - 32));""",
"""        var slab = Style.V(Style.Gap2);
        var top = Style.H(14, Deed("Steep it in slurry", q, () => Work(q, Sound.Sfx.Pour), "steep", true, ItemViews.SlurryGreen));
        if (Crafting.Line(crafter, "jar") is { } said) top.AddChild(Style.Label($"“{said}”", Style.TextItalic, 15, Kit.Dim, true));
        ((Control)top.GetChild(top.GetChildCount() - 1)).SizeFlagsHorizontal = SizeFlags.ExpandFill;
        slab.AddChild(top);
        slab.AddChild(SlurryOdds(it, LeftW - 2 * Pad));"""),
("""        if (!q.Ok && q.Blocked != closed)
            words.AddChild(Style.Label(noJar && Crafting.Does(crafter, Verb.Buy) ? $"No jar yet: {He} sells them, above the anvil." : q.Blocked!, Style.TextItalic, 15, Style.Bad, true));
        foot.AddChild(words);
        var b = Hold("Steep", q, () => Work(q, Sound.Sfx.Pour), "steep");
        b.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        foot.AddChild(b);
        slab.AddChild(foot);
        o.Wide = Style.Panel(Kit.PanelBox(16, 14, new Color("#151d12")), slab);""",
"""        if (!q.Ok && q.Blocked != closed)
            words.AddChild(Style.Label(noJar && Crafting.Does(crafter, Verb.Buy) ? $"No jar yet: {He} sells them, above the anvil." : q.Blocked!, Style.TextItalic, 15, Style.Bad, true));
        else if (q.Ok) words.AddChild(Style.Label("held: it cannot be undone", Style.Ui, 14, Kit.Ink2, true));
        foot.AddChild(words);
        slab.AddChild(foot);
        o.Wide = slab;"""),
# Snib's jar as type.
("""        words.AddChild(Style.Label("A jar of slurry", Style.TextBold, 19, new Color("#a8e08a")));
        words.AddChild(Style.Label(q.Ok ? $"{q.Gold} gold  ·  {left} left today  ·  you carry {carry}" : q.Blocked!, Style.TextItalic, 15, q.Ok ? Kit.Dim : Style.Bad, true));
        h.AddChild(words);
        var b = Style.Button("Buy", null, q.Ok, true);
        b.Disabled = !q.Ok;
        b.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        b.Pressed += () => { if (!q.Ok) { Sound.Sfx.Deny(); return; } Sound.Sfx.Loot(false); if (G.Journey.Make(q)) Refresh(); };
        Nav.Mark(b, "jar", () => b.EmitSignal(BaseButton.SignalName.Pressed));
        h.AddChild(b);
        return Style.Panel(Kit.PanelBox(14, 10, new Color("#151d12")), h);""",
"""        words.AddChild(Deed("Buy a jar of slurry", q, () => { Sound.Sfx.Loot(false); if (G.Journey.Make(q)) Refresh(); }, "jar", false, new Color("#a8e08a")));
        words.AddChild(Style.Label(q.Ok ? $"{q.Gold} gold  ·  {left} left today  ·  you carry {carry}" : q.Blocked!, Style.Ui, 14, q.Ok ? Kit.Ink2 : Style.Bad, true));
        h.AddChild(words);
        return h;"""),
# What the jar did, as type with its colour's mark at the left.
("""        ((Control)row.GetChild(1)).SizeFlagsHorizontal = SizeFlags.ExpandFill;
        return Style.Panel(Kit.PanelBox(14, 10, new Color("#18200f")), row);""",
"""        ((Control)row.GetChild(1)).SizeFlagsHorizontal = SizeFlags.ExpandFill;
        return Style.H(12, new ColorRect { Color = col, CustomMinimumSize = new Vector2(2, 0), MouseFilter = MouseFilterEnum.Ignore }, row);"""),
])
