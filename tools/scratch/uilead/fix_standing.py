p = 'godot/src/Ui/Book.cs'
s = open(p, encoding='utf-8', newline='').read()
nl = '\r\n' if '\r\n' in s else '\n'
s = s.replace('\r\n', '\n')

old_start = s.index('    /// <summary>The standing; with an attribute named, what a point in it would change.</summary>')
old_end = s.index('    /// <summary>What a point would change, as the change itself')
new = '''    /// <summary>Each standing line's change label, by its key: filled when an attribute is previewed.</summary>
    readonly Dictionary<string, Label> changes = new();

    /// <summary>
    /// The standing; with an attribute named, what a point in it would change.
    /// Built once per page and changed in place: rebuilt on every preview, the
    /// lines a pad had in its focus order were freed under it (focusing a +
    /// left the standing unreachable).
    /// </summary>
    void ShowStanding(string? attr)
    {
        if (!IsInstanceValid(standing)) return;
        var ch = G.Journey.Ch;
        var kit = Character.Kit(ch).Stats;
        StatBlock? then = null;
        if (attr != null)
        {
            var clone = Core.Json.Clone(ch);
            switch (attr) { case "might": clone.Attributes.Might++; break; case "finesse": clone.Attributes.Finesse++; break; case "wits": clone.Attributes.Wits++; break; default: clone.Attributes.Resolve++; break; }
            then = Character.Kit(clone).Stats;
        }
        if (standing.GetChildCount() == 0)
        {
            changes.Clear();
            foreach (var (group, lines) in Standing)
            {
                // Each group on a plate of its own.
                var plate = Style.Panel(Style.Slab(12));
                plate.MouseFilter = MouseFilterEnum.Ignore;
                var col = Style.V(4, Style.Label(group.ToUpperInvariant(), Style.UiHeavy, Style.Caption, Style.Gold));
                plate.AddChild(col);
                standing.AddChild(plate);
                foreach (var (key, name, fmt) in lines)
                {
                    var label = Style.Label(name, Style.Ui, Style.Body, Style.InkDim);
                    label.CustomMinimumSize = new Vector2(150, 0);
                    var change = Style.Label("", Style.UiBold, Style.Body, Style.Good);
                    changes[key] = change;
                    var line = Style.H(10, label, Style.Label(fmt(kit.Get(key)), Style.UiBold, Style.Body, Style.Ink), change);
                    // Each line says where it comes from, hovered or focused.
                    var holder = Style.Panel(new StyleBoxEmpty(), line);
                    holder.MouseFilter = MouseFilterEnum.Stop;
                    var k = key;
                    holder.MouseEntered += () => Tip(Breakdown(k, name, fmt), holder);
                    holder.MouseExited += () => Tip(null, null);
                    Nav.Mark(holder, $"stat:{key}", null, focus: () => Tip(Breakdown(k, name, fmt), holder), blur: () => Tip(null, null));
                    col.AddChild(holder);
                }
            }
        }
        foreach (var (key, change) in changes)
        {
            double now = kit.Get(key);
            bool moves = then != null && Math.Abs(then.Get(key) - now) > 1e-6;
            change.Text = moves ? Change(key, now, then!.Get(key)) : "";
            change.Visible = moves;
        }
    }

'''
s = s[:old_start] + new + s[old_end:]
open(p, 'w', encoding='utf-8', newline='').write(s.replace('\n', nl))
print('ok')
