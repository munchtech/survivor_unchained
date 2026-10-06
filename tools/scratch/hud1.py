p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src\Ui\GameHud.cs'
s = open(p, encoding='utf-8').read()

old_prompt = s[s.index("    public void Prompt(PromptView? p)"):s.index("    public void Say(string text")]
new_prompt = '''    public void Prompt(PromptView? p)
    {
        promptView = p;
        promptBox.Visible = p != null;
        if (p == null) return;
        foreach (var c in promptBox.GetChildren()) { promptBox.RemoveChild(c); c.QueueFree(); }
        // The key as the device in hand has it: a keycap, or the pad's button.
        var key = Controls.Instance.UsingPad ? Style.PadButton(Controls.Instance.PadLabels(Act.Interact).FirstOrDefault() ?? "B")
            : Style.Panel(Style.Box(Hex("#0d0c10"), Style.GoldDim, 1, 17, 0), Style.Label(p.Key, Style.UiBold, 16, Style.GoldHi, false, HorizontalAlignment.Center));
        key.CustomMinimumSize = new Vector2(34, 34);
        bool locked = p.Locked != null;
        var row = Style.H(11, key, Style.Label(p.Verb, Style.UiHeavy, 18, locked ? Colors.White with { A = 0.55f } : Colors.White),
            Style.Label(p.Target, Style.Display, 18, locked ? Style.GoldHi with { A = 0.55f } : Style.GoldHi));
        if (locked) row.AddChild(Style.H(4, Glyphs.Icon("lock", 15, Hex("#ff9a80")), Style.Label(p.Locked!, Style.UiBold, Style.Small, Hex("#ff9a80"))));
        else if (p.Hint != null) row.AddChild(Style.Label(p.Hint, Style.TextItalic, Style.Small, Style.InkDim));
        promptBox.AddChild(row);
        promptBox.ResetSize();
        var size = promptBox.GetCombinedMinimumSize();
        promptBox.Position = new Vector2((1920 - size.X) / 2, 1080 - 180 - size.Y);
    }

'''
s = s.replace(old_prompt, new_prompt, 1)

old_toast = s[s.index("    public void Toast(Toast t)"):s.index("    public void Announce(Announcement a)")]
new_toast = '''    public void Toast(Toast t)
    {
        // Discoveries and loot in a burst gather into one toast that grows, not a column of them.
        double now = Time.GetTicksMsec() / 1000.0;
        if (lastToast is { } lt && lt.Kind == t.Kind && t.Kind is ToastKind.Lore or ToastKind.Loot && t.Rarity == null && t.Icon == null
            && now - lt.At < 2.5 && IsInstanceValid(lt.Box) && lt.Names.Count < 5)
        {
            lt.Names.Add(t.Text);
            if (lt.Box.FindChild("Title", true, false) is Label title) title.Text = string.Join(", ", lt.Names);
            lt.Box.SetMeta("t", 0.06);
            lastToast = lt with { At = now };
            return;
        }
        var (glyph, color) = ToastLook.GetValueOrDefault(t.Kind, ("arcane", Style.Gold));
        if (t.Rarity is int r) color = Style.RarityOf(r);
        var box = new PanelContainer { MouseFilter = Control.MouseFilterEnum.Ignore, CustomMinimumSize = new Vector2(408, 0) };
        var s = Style.Box(new Color(0.047f, 0.04f, 0.055f, 0.82f), color, 0, 4, 8);
        s.BorderWidthLeft = 3;
        box.AddThemeStyleboxOverride("panel", Skin.Frame("toast", s));
        var row = Style.H(10, t.Icon != null ? ItemPhotos.Icon(t.Icon, 40, color) : Glyphs.Icon(glyph, 22, color));
        var head = Style.Label(t.Text, t.Kind == ToastKind.Quest ? Style.Display : Style.UiBold, 17, t.Kind == ToastKind.Quest ? Style.GoldHi : t.Rarity != null ? color : Hex("#f0e6d2"), true);
        head.Name = "Title";
        var words = Style.V(0, head);
        if (!string.IsNullOrEmpty(t.Sub)) words.AddChild(Style.Label(t.Sub, Style.TextItalic, Style.Caption, Hex("#b8ab96"), true));
        words.SizeFlagsHorizontal = Control.SizeFlags.ExpandFill;
        row.AddChild(words);
        box.AddChild(row);
        box.SetMeta("t", 0.0);
        box.SetMeta("life", t.Life ?? 5.0);
        toasts.AddChild(box);
        lastToast = (box, t.Kind, new List<string> { t.Text }, now);
        while (toasts.GetChildCount() > 6) toasts.GetChild(0).Free();
    }

'''
s = s.replace(old_toast, new_toast, 1)

old_hint = s[s.index("    public void Hint(Hint? h)"):s.index("    /// <summary>Fade to black (1)")]
new_hint = '''    public void Hint(Hint? h)
    {
        hintView = h;
        hintBox.Visible = h != null;
        foreach (var c in hintBox.GetChildren()) { hintBox.RemoveChild(c); c.QueueFree(); }
        if (h == null) return;
        var ink = Style.ParchmentInk;
        var v = Style.V(5, Style.H(6, Glyphs.Icon("scroll", 17, Hex("#6a3a14")), Style.Label(h.Title.ToUpperInvariant(), Style.Display, 15, Hex("#6a3a14"), false, HorizontalAlignment.Left, false)),
            Style.Label(h.Text, Style.Text, 19, ink, true, HorizontalAlignment.Left, false));
        // A known width, so the words wrap before the box is measured.
        v.GetChild<Control>(1).CustomMinimumSize = new Vector2(396 - 28, 0);
        if (h.Keys.Count > 0) v.AddChild(Style.H(6, HintKeys(h.Keys).ToArray()));
        hintBox.AddChild(v);
        hintBox.OffsetTop = hintBox.OffsetBottom;
    }

    static readonly string[] PadNames = ["A", "B", "X", "Y", "LB", "RB", "LT", "RT", "View", "Menu"];

    /// <summary>A hint's keys as the device in hand has them: W A S D become the stick on a pad.</summary>
    static IEnumerable<Control> HintKeys(List<string> keys)
    {
        bool pad = Controls.Instance.UsingPad;
        bool wasd = keys.Count == 4 && string.Concat(keys) == "WASD";
        if (pad && wasd) { yield return Style.PadButton("Left stick"); yield break; }
        foreach (var k in keys) yield return pad && !wasd && PadNames.Contains(k) ? Style.PadButton(k) : Style.Key(k);
    }

    /// <summary>The device in hand changed: every key shown redraws as its keys or buttons.</summary>
    public void DeviceChanged()
    {
        foreach (var (act, row) in handKeys)
        {
            var old = row.GetChild(0);
            row.RemoveChild(old);
            old.QueueFree();
            var k = Style.Prompt(act);
            row.AddChild(k);
            row.MoveChild(k, 0);
        }
        Prompt(promptView);
        Hint(hintView);
        draft?.Prompts();
        talk?.Prompts();
    }

    /// <summary>Where the survivor stands on screen, each frame (null: not on it).</summary>
    public void Follow(Vector2? at)
    {
        if (at is { } p) under.Position = p + new Vector2(-38, 22);
        underWanted &= at != null;
    }

    /// <summary>The corner map, a few times a second; null hides it (an arena, the title).</summary>
    public void MapFrame(MinimapView? m)
    {
        bool on = m != null;
        if (minimap.Visible != on)
        {
            minimap.Visible = on;
            corner.Position = corner.Position with { Y = on ? 28 + Minimap.Diameter + 16 : 22 };
        }
        if (m == null) return;
        minimap.Zone(m.Zone, m.Drawing, m.Extent);
        minimap.Show(m.Seen, m.N, m.Marks, m.X, m.Z, m.Facing, m.Night);
    }

'''
s = s.replace(old_hint, new_hint, 1)

old = """        // The trail behind health catches up after a moment."""
new = """        // The health under the survivor eases in and out with the night's fight.
        underAlpha = Mathf.MoveToward(underAlpha, underWanted ? 1 : 0, dt * 4);
        under.Modulate = Colors.White with { A = underAlpha };
        underFill.Size = new Vector2(74 * underK, 7);
        underFill.Color = underK < 0.35f ? Hex("#ff5a4a").Lerp(Colors.White, 0.25f * Mathf.Max(0, Mathf.Sin(Time.GetTicksMsec() / 1000f * 7))) : Hex("#e8383a");
        underShield.Size = new Vector2(74 * underShieldK, 3);
        // The trail behind health catches up after a moment."""
assert old in s
s = s.replace(old, new, 1)

old = """/// <summary>What is near and can be used, as the prompt shows it.</summary>"""
new = """/// <summary>What the corner map shows: the zone's drawing, the fog, the marks, the survivor.</summary>
public sealed record MinimapView(string Zone, Texture2D Drawing, float Extent, string Seen, int N, List<MiniMark> Marks, double X, double Z, double Facing, bool Night);

/// <summary>What is near and can be used, as the prompt shows it.</summary>"""
assert old in s
s = s.replace(old, new, 1)
open(p, 'w', encoding='utf-8', newline='').write(s)
print("done")
