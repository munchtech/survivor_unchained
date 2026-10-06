p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src\Ui\Book.cs'
s = open(p, encoding='utf-8').read()
a = s.index("    Control People()")
b = s.index("    Control Deeds()")
new = r'''    string? person;

    /// <summary>People as the quests are: a list of those met (how each feels, in a word), and
    /// the one chosen on the page beside it, drawn as they look, with how they feel about you
    /// on four measures, what is on their mind, and what they know you did.</summary>
    Control People()
    {
        var w = G.Journey.World;
        var ctx = G.Journey.Ctx;
        var met = Lore.Npcs.Values.Where(d => w.Npcs.TryGetValue(d.Id, out var s) && s.Flags.TryGetValue("met", out var m) && m.Truthy).ToList();
        if (met.Count == 0) return Style.V(0, P("You have not met anyone yet. Those you speak with are written here, and how they feel about you.", Style.Body, Style.TextItalic, InkSoft));
        if (person == null || met.All(d => d.Id != person)) person = met[0].Id;
        var side = Style.V(2);
        side.CustomMinimumSize = new Vector2(300, 0);
        foreach (var d in met)
        {
            var st = w.Npcs[d.Id];
            var id = d.Id;
            var bt = Style.Button("", () => { person = id; Refresh(); }, false, true);
            foreach (var state in new[] { "normal", "hover", "pressed" })
                bt.AddThemeStyleboxOverride(state, Style.Box(id == person || state == "hover" ? new Color(0.35f, 0.24f, 0.08f, id == person ? 0.16f : 0.08f) : new Color(0, 0, 0, 0), new Color(0, 0, 0, 0), 0, 4, 0));
            var line = Style.V(0, Style.Label(d.Name, Style.TextBold, Style.Body, id == person ? Red : Ink, false, HorizontalAlignment.Left, false),
                Style.Label($"{d.Role}  ·  {(st.Alive ? Rules.Attitude(st) : "dead")}", Style.TextItalic, Style.Caption, InkSoft, false, HorizontalAlignment.Left, false));
            line.Position = new Vector2(8, 3);
            line.MouseFilter = MouseFilterEnum.Ignore;
            bt.AddChild(line);
            bt.CustomMinimumSize = new Vector2(290, 50);
            // Focus on a name shows them (a pad reads the page as it moves down the list).
            Nav.Mark(bt, $"person:{id}", () => { person = id; Refresh(); }, focus: () => { if (person != id) { person = id; Refresh(); } });
            side.AddChild(bt);
        }
        var d0 = met.First(d => d.Id == person);
        var s0 = w.Npcs[d0.Id];
        var page = Style.V(Style.Gap2);
        var head = Style.H(Style.Gap4);
        var frame = Style.Panel(Style.Box(new Color(0.16f, 0.12f, 0.08f, 0.9f), new Color("#5a3e24"), 2, 4, 0));
        frame.CustomMinimumSize = new Vector2(190, 230);
        if (d0.Person != null) frame.AddChild(new Portrait(new Vector2I(190, 230), Portrait.Framing.Bust).Of(d0.Person, d0.Arms, d0.Scale ?? 1));
        head.AddChild(frame);
        var who = Style.V(4, H2(d0.Name), P(d0.Role + (d0.Title != "" && d0.Title != d0.Role ? $"  ·  {d0.Title}" : ""), Style.Small, Style.TextItalic, InkSoft),
            P(s0.Alive ? Style.Cap1(Rules.Attitude(s0)) : "Dead.", Style.Body, Style.TextBold, Red));
        who.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        if (s0.Alive && Lore.ConcernOf(d0.Id, ctx) is string mind) { who.AddChild(Style.Gap(4)); who.AddChild(P(mind, Style.Body, Style.TextItalic)); }
        head.AddChild(who);
        page.AddChild(head);
        page.AddChild(Style.Rule());
        // Four measures, each a bar from against you to for you, with a word.
        var axes = new GridContainer { Columns = 3, MouseFilter = MouseFilterEnum.Ignore };
        axes.AddThemeConstantOverride("h_separation", 14);
        axes.AddThemeConstantOverride("v_separation", 6);
        foreach (var (label, val, lo, hi) in new[] { ("Trust", s0.Trust, "doubts you", "trusts you"), ("Warmth", s0.Affection, "cold to you", "fond of you"), ("Respect", s0.Respect, "thinks little of you", "respects you"), ("Fear", s0.Fear, "unafraid", "afraid of you") })
        {
            axes.AddChild(P(label, Style.Small, Style.UiBold, Ink));
            axes.AddChild(Feel(val, 260));
            axes.AddChild(P(Math.Abs(val) < 12 ? "neither way" : $"{(Math.Abs(val) > 55 ? "much " : "")}{(val < 0 ? lo : hi)}".Replace("much unafraid", "quite unafraid"), Style.Caption, Style.TextItalic, InkSoft));
        }
        page.AddChild(axes);
        var heard = s0.Memories.Select(m => w.History.FirstOrDefault(h => h.Id == m)).Where(h => h != null).Select(h => h!.Text).ToList();
        page.AddChild(Style.Gap(4));
        page.AddChild(P(heard.Count > 0 ? $"Knows that you {string.Join("; ", heard)}." : "Has heard nothing of what you have done.", Style.Small, Style.Text, InkSoft));
        var h = Style.H(30);
        var list = Style.Scroll(side);
        list.CustomMinimumSize = new Vector2(310, 0);
        list.SizeFlagsHorizontal = SizeFlags.Fill;
        h.AddChild(list);
        this.page = Style.Scroll(page);
        h.AddChild(this.page);
        return h;
    }

'''
s = s[:a] + new + s[b:]
# Feel with a width
old = '''    static Control Feel(double v)
    {
        var p = new Control { CustomMinimumSize = new Vector2(120, 12), MouseFilter = MouseFilterEnum.Ignore };
        p.AddChild(new ColorRect { Color = new Color(0.35f, 0.25f, 0.12f, 0.35f), Position = new Vector2(0, 5), Size = new Vector2(120, 2) });
        p.AddChild(new ColorRect { Color = new Color(0.35f, 0.25f, 0.12f, 0.6f), Position = new Vector2(59, 2), Size = new Vector2(2, 8) });
        p.AddChild(new ColorRect { Color = v >= 0 ? new Color("#3a6a2a") : new Color("#8a2a1a"), Position = new Vector2((float)((v + 100) / 200 * 116), 1), Size = new Vector2(6, 10) });
        return p;
    }'''
new2 = '''    /// <summary>A measure from -100 to 100 as a line with a mark: green for you, red against, the middle marked.</summary>
    static Control Feel(double v, float w = 120)
    {
        var p = new Control { CustomMinimumSize = new Vector2(w, 14), MouseFilter = MouseFilterEnum.Ignore };
        p.AddChild(new ColorRect { Color = new Color(0.35f, 0.25f, 0.12f, 0.35f), Position = new Vector2(0, 6), Size = new Vector2(w, 2), MouseFilter = MouseFilterEnum.Ignore });
        p.AddChild(new ColorRect { Color = new Color(0.35f, 0.25f, 0.12f, 0.6f), Position = new Vector2(w / 2 - 1, 2), Size = new Vector2(2, 10), MouseFilter = MouseFilterEnum.Ignore });
        float x = (float)((Math.Clamp(v, -100, 100) + 100) / 200 * (w - 8));
        var col = v >= 0 ? new Color("#3a6a2a") : new Color("#8a2a1a");
        // The stretch from the middle to the mark, then the mark.
        p.AddChild(new ColorRect { Color = col with { A = 0.35f }, Position = new Vector2(Math.Min(x + 4, w / 2), 5), Size = new Vector2(Math.Abs(x + 4 - w / 2), 4), MouseFilter = MouseFilterEnum.Ignore });
        p.AddChild(new ColorRect { Color = col, Position = new Vector2(x, 1), Size = new Vector2(8, 12), MouseFilter = MouseFilterEnum.Ignore });
        return p;
    }'''
assert old in s
s = s.replace(old, new2, 1)
open(p, 'w', encoding='utf-8', newline='').write(s)
print('done')
