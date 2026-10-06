from ed import sub
sub('src/Ui/Pack.cs', [
("""        breaking = null;
        if (sel == it.Uid) sel = null;
        Sound.Sfx.Shatter();
        G.Gear((j, b) => j.Work(it.Uid, q, b));
    }""",
"""        breaking = null;
        if (sel == it.Uid) sel = null;
        Sound.Sfx.Shatter();
        // The HUD's toasts are hidden under the pack: what it came to is said where it was read.
        broke = (Inventory.Name(it), string.Join(" and ", q.Gives.Select(kv => Items.Several(kv.Key, kv.Value))), q.Gives.Keys.First());
        G.Gear((j, b) => j.Work(it.Uid, q, b));
    }

    /// <summary>What was just broken down, and what it came to (said in the reading place).</summary>
    (string Name, string Gives, string Icon)? broke;"""),
("""        foreach (var c in inspect.GetChildren()) { inspect.RemoveChild(c); c.QueueFree(); }
        if (it == null) return;""",
"""        foreach (var c in inspect.GetChildren()) { inspect.RemoveChild(c); c.QueueFree(); }
        if (it == null && broke is { } b)
        {
            broke = null;
            var row = Style.H(Style.Gap3, ItemPhotos.Icon(Items.Get(b.Icon).Icon, 48, Style.InkDim),
                Style.V(1, Style.Label($"Broken down: {b.Name}", Style.UiBold, Style.Body, Style.Ink, true),
                    Style.Label($"{Style.Cap1(b.Gives)}, into the pouch for the forge.", Style.TextItalic, Style.Small, Style.InkDim, true)));
            var note = Style.Panel(Style.Slab(14), row);
            note.CustomMinimumSize = new Vector2(480, 0);
            inspect.AddChild(note);
            note.CreateTween().TweenProperty(note, "modulate:a", 0f, 0.8).SetDelay(3.0);
            return;
        }
        if (it == null) return;"""),
("""                acts.AddChild(Style.Button(breaking == it.Uid ? "Break it down for good" : $"Break down for {bq.Gives[Crafting.Iron]} old iron", () => BreakDown(it), false, true));""",
"""            {
                var bb = Style.Button(breaking == it.Uid ? "Break it down for good" : $"Break down for {Items.Several(Crafting.Iron, bq.Gives[Crafting.Iron])}", () => BreakDown(it), false, true);
                // Asked again, in the colour of what cannot be undone.
                if (breaking == it.Uid) bb.AddThemeColorOverride("font_color", Style.Bad);
                acts.AddChild(bb);
            }"""),
])
