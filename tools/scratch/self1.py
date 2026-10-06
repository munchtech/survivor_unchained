p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src\Ui\Book.cs'
s = open(p, encoding='utf-8').read()
a = s.index("/// <summary>\n/// Who the survivor has become")
b = s.index("/// <summary>\n/// The journal (the web game's overlays/Journal.tsx)")
new = r'''/// <summary>
/// Who the survivor has become (docs/UI_DESIGN.md, "Self"), answering "what
/// am I becoming, and where do my numbers come from?". On the left who they
/// are: the figure, the level and the way to the next, the art in hand,
/// what they know, what ails or blesses them. In the middle the four
/// attributes, each saying what a point gives; with points to spend, the +
/// shows (hovered or focused) what that point would change in the standing.
/// On the right the whole standing, grouped by what it is for; every line,
/// hovered or focused, says where it comes from (the calling, the
/// attributes, each thing worn, traits, conditions). Traits under the
/// attributes, to choose and held.
/// </summary>
public partial class SheetScreen : Overlay
{
    public override string Kind => "character";
    public override Act? Toggle => Act.Character;

    static readonly (string Id, string Name, string Text)[] Attrs =
    {
        ("might", "Might", "+2.5% damage and +4 health per point"),
        ("finesse", "Finesse", "+0.6% critical chance and +1% speed per point"),
        ("wits", "Wits", "+1% weapon speed, +2% area and ember per point"),
        ("resolve", "Resolve", "+3 health, +0.5 armour, +0.08 regeneration per point"),
    };
    public static readonly Dictionary<string, string> Know = new() { ["beastlore"] = "Beastlore", ["arcana"] = "Arcana", ["underworld"] = "The Underworld", ["faith"] = "The Faith" };
    static readonly Dictionary<ConditionId, string> Cond = new()
    {
        [ConditionId.Wounded] = "Wounded: 20% less health until it heals", [ConditionId.Blightsick] = "Blight-sick: your wounds close slowly", [ConditionId.Poisoned] = "Poisoned",
        [ConditionId.Blessed] = "Blessed: +15% holy damage", [ConditionId.Rested] = "Rested: +5% health", [ConditionId.Warmed] = "Warmed: +8% damage, +5% speed",
        [ConditionId.Wolfscent] = "Wolf-scented", [ConditionId.Hunted] = "Hunted",
    };

    /// <summary>The standing, grouped by what it is for; each line's key, name and how it is written.</summary>
    static readonly (string Group, (string Key, string Name, Func<double, string> Fmt)[] Lines)[] Standing =
    {
        ("Staying alive", new (string, string, Func<double, string>)[]
        {
            (Stat.MaxHealth, "Health", v => $"{Math.Round(v)}"),
            (Stat.Armor, "Armour", v => $"{Math.Round(v)}  ·  {Math.Round(StatBlock.ArmorReduction(v) * 100)}% less from blows"),
            (Stat.Regen, "Regeneration", v => $"{v:0.0} a second"),
            (Stat.Healing, "Healing", Pct),
            (Stat.Dodge, "Dodge", v => $"{Math.Round(v * 100)}%"),
        }),
        ("Dealing death", new (string, string, Func<double, string>)[]
        {
            (Stat.Damage, "Damage", Pct),
            (Stat.CritChance, "Critical chance", v => $"{Math.Round(v * 100)}%"),
            (Stat.CritDamage, "Critical damage", v => $"×{v:0.##}"),
            (Stat.Cooldown, "Weapon speed", v => v <= 0 ? "-" : $"{(1 / v - 1) * 100:+0;-0;0}% faster"),
            (Stat.Area, "Area", Pct),
        }),
        ("Moving", new (string, string, Func<double, string>)[]
        {
            (Stat.MoveSpeed, "Speed", v => $"{v:0.0}"),
            (Stat.DashCharges, "Dashes", v => $"{Math.Round(v)}"),
            (Stat.PickupRadius, "Reach for what falls", v => $"{v:0.0} m"),
        }),
        ("Fortune", new (string, string, Func<double, string>)[]
        {
            (Stat.XpGain, "Experience", Pct),
            (Stat.GoldGain, "Gold found", Pct),
        }),
    };

    static string Pct(double v) => $"{(v - 1) * 100:+0;-0;0}%";

    VBoxContainer standing = null!;

    public SheetScreen(Game g) : base(g) { Nav.Prefer = "attr:might"; }

    static int Attr(CharacterData ch, string id) => id switch { "might" => ch.Attributes.Might, "finesse" => ch.Attributes.Finesse, "wits" => ch.Attributes.Wits, _ => ch.Attributes.Resolve };

    protected override void Build()
    {
        var ch = G.Journey.Ch;
        var body = Frame(ch.Name, new Vector2(1500, 790), G.Key(Act.Character), $"Level {ch.Level} {Callings.Background(ch.Background).Name} {Callings.Archetype(ch.Archetype).Name}");
        var row = Style.H(30);
        row.SizeFlagsVertical = SizeFlags.ExpandFill;
        body.AddChild(row);

        // Who they are.
        var left = Style.V(Style.Gap2);
        left.CustomMinimumSize = new Vector2(290, 0);
        left.AddChild(new Portrait(new Vector2I(270, 330)).Of(Loadouts.Of(ch)));
        double need = Character.XpForLevel(ch.Level);
        left.AddChild(Style.H(8, Style.Label($"Level {ch.Level}", Style.Display, 20, Style.GoldHi), Style.Label("experience", Style.Ui, Style.Caption, Style.Day)));
        // Experience in the day's cool colour, as the HUD's bar has it by day.
        left.AddChild(Bar(ch.Xp / need, $"{Math.Floor(ch.Xp)} / {need} to level {ch.Level + 1}", Style.Day, 280));
        var ab = Abilities.ById(ch.Ability);
        var arts = Style.Button("", () => G.Open("arts"), false, true);
        var artRow = Style.H(6, Glyphs.Icon(ab.Icon, 18), Style.Label($"{ab.Name}  ·  rank {ArtBook.Rank(ch, ch.Ability)}", Style.UiBold, Style.Small, Style.GoldHi), Style.Key(G.Key(Act.Arts)));
        artRow.Position = new Vector2(8, 6);
        artRow.MouseFilter = MouseFilterEnum.Ignore;
        arts.AddChild(artRow);
        arts.CustomMinimumSize = new Vector2(280, 36);
        arts.TooltipText = "Your arts: the one in hand, its rank and facets";
        left.AddChild(Nav.Id(arts, "arts"));
        var knows = ch.Knowledge.Where(Know.ContainsKey).Select(k => Know[k]).ToList();
        left.AddChild(Style.Label(knows.Count == 0 ? "You know little yet that others do not." : $"You know {string.Join(", ", knows)}: it opens words and ways others miss.", Style.TextItalic, Style.Caption, Style.InkDim, true));
        foreach (var c in ch.Conditions)
        {
            bool good = c.Id is ConditionId.Blessed or ConditionId.Rested or ConditionId.Warmed;
            left.AddChild(Style.H(6, Glyphs.Icon(good ? "sun" : "skull", 15, good ? Style.Good : Style.Bad), Style.Label($"{Cond.GetValueOrDefault(c.Id, c.Id.ToString())}  ·  {c.Days} day{(c.Days == 1 ? "" : "s")}", Style.UiBold, Style.Caption, good ? Style.Good : Style.Bad, true)));
        }
        row.AddChild(left);

        // The attributes, and the traits.
        var mid = Style.V(Style.Gap2);
        mid.CustomMinimumSize = new Vector2(470, 0);
        mid.AddChild(Style.H(8, Style.SubLabel("Attributes"), ch.Points > 0 ? Style.Label($"{ch.Points} to spend: each + shows what it would change", Style.UiBold, Style.Caption, Style.EmberHi) : Style.Label("more with each level", Style.TextItalic, Style.Caption, Style.InkFaint)));
        foreach (var (id, name, text) in Attrs)
        {
            var r = Style.H(12);
            var val = Style.Label($"{Attr(ch, id)}", Style.Display, 28, Style.GoldHi);
            val.CustomMinimumSize = new Vector2(36, 0);
            r.AddChild(val);
            var words = Style.V(0, Style.Label(name, Style.UiBold, Style.Body, Style.Ink), Style.Label(text, Style.Ui, Style.Caption, Style.InkDim, true));
            words.SizeFlagsHorizontal = SizeFlags.ExpandFill;
            r.AddChild(words);
            if (ch.Points > 0)
            {
                var attr = id;
                var plus = Style.Button("+", () => G.Gear((j, b) => j.SpendPoint(attr, b)), true, true);
                plus.CustomMinimumSize = new Vector2(40, 36);
                plus.MouseEntered += () => ShowStanding(attr);
                plus.MouseExited += () => ShowStanding(null);
                Nav.Mark(plus, $"attr:{attr}", () => G.Gear((j, b) => j.SpendPoint(attr, b)), focus: () => ShowStanding(attr), blur: () => ShowStanding(null));
                r.AddChild(plus);
            }
            mid.AddChild(r);
        }
        mid.AddChild(Style.Rule());
        mid.AddChild(Style.H(8, Style.SubLabel("Traits"), ch.TraitPicks > 0 ? Style.Label($"choose {ch.TraitPicks}", Style.UiBold, Style.Caption, Style.EmberHi) : new Control()));
        if (ch.Traits.Count == 0 && ch.TraitPicks == 0) mid.AddChild(Style.Label("None yet. Traits come with levels, and with what you do.", Style.TextItalic, Style.Caption, Style.InkDim, true));
        foreach (var t in ch.Traits)
        {
            var def = Callings.Trait(t);
            mid.AddChild(Style.V(0, Style.Label((def?.Name ?? t) + (def?.Source == TraitSource.World ? "  ·  earned" : ""), Style.UiBold, Style.Small, def?.Source == TraitSource.World ? Style.EmberHi : Style.GoldHi),
                Style.Label(def?.Text ?? "", Style.Ui, Style.Caption, Style.InkDim, true)));
        }
        if (ch.TraitPicks > 0)
            foreach (var t in Offer(ch))
            {
                var def = Callings.Trait(t)!;
                var b = Style.Button("", () => G.Gear((j, bt) => j.PickTrait(t, bt)));
                var inner = Style.V(0, Style.Label(def.Name, Style.UiBold, Style.Small, Style.GoldHi), Style.Label(def.Text, Style.Ui, Style.Caption, Style.Ink, true));
                inner.Position = new Vector2(12, 6);
                inner.Size = new Vector2(440, 52);
                inner.MouseFilter = MouseFilterEnum.Ignore;
                b.CustomMinimumSize = new Vector2(460, 66);
                Nav.Id(b, $"trait:{t}");
                mid.AddChild(b);
            }
        row.AddChild(mid);

        // The whole standing.
        var right = Style.V(Style.Gap2);
        right.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        right.AddChild(Style.H(8, Style.SubLabel("Standing"), Style.Label("hover or focus a line: where it comes from", Style.TextItalic, Style.Caption, Style.InkFaint)));
        standing = Style.V(2);
        right.AddChild(standing);
        row.AddChild(right);
        ShowStanding(null);
        if (Controls.Instance.UsingPad)
            body.AddChild(Footer((Act.Confirm, ch.Points > 0 ? "Spend a point" : "Choose"), (Act.TabPrev, "Pack"), (Act.TabNext, "Arts"), (Act.Cancel, "Close")));
    }

    /// <summary>The standing; with an attribute named, what a point in it would change.</summary>
    void ShowStanding(string? attr)
    {
        if (!IsInstanceValid(standing)) return;
        foreach (var c in standing.GetChildren()) { standing.RemoveChild(c); c.QueueFree(); }
        var ch = G.Journey.Ch;
        var kit = Character.Kit(ch).Stats;
        StatBlock? then = null;
        if (attr != null)
        {
            var clone = Core.Json.Clone(ch);
            switch (attr) { case "might": clone.Attributes.Might++; break; case "finesse": clone.Attributes.Finesse++; break; case "wits": clone.Attributes.Wits++; break; default: clone.Attributes.Resolve++; break; }
            then = Character.Kit(clone).Stats;
        }
        foreach (var (group, lines) in Standing)
        {
            standing.AddChild(Style.Gap(Style.Gap1));
            standing.AddChild(Style.Label(group.ToUpperInvariant(), Style.UiHeavy, Style.Badge, Style.Gold));
            foreach (var (key, name, fmt) in lines)
            {
                double now = kit.Get(key);
                var label = Style.Label(name, Style.Ui, Style.Small, Style.InkDim);
                label.CustomMinimumSize = new Vector2(190, 0);
                var line = Style.H(10, label, Style.Label(fmt(now), Style.UiBold, Style.Small, Style.Ink));
                if (then != null && Math.Abs(then.Get(key) - now) > 1e-6)
                    line.AddChild(Style.Label($"to {fmt(then.Get(key))}", Style.UiBold, Style.Small, Style.Good));
                // Each line says where it comes from, hovered or focused.
                var holder = Style.Panel(new StyleBoxEmpty(), line);
                holder.MouseFilter = MouseFilterEnum.Stop;
                var k = key;
                holder.MouseEntered += () => Tip(Breakdown(k, name, fmt), holder);
                holder.MouseExited += () => Tip(null, null);
                Nav.Mark(holder, $"stat:{key}", null, focus: () => Tip(Breakdown(k, name, fmt), holder), blur: () => Tip(null, null));
                standing.AddChild(holder);
            }
        }
    }

    /// <summary>Where a number comes from: the calling's base, then each thing that moves it.</summary>
    Control Breakdown(string key, string name, Func<double, string> fmt)
    {
        var ch = G.Journey.Ch;
        var kit = Character.Kit(ch).Stats;
        var card = Style.Panel(UiArt.Frame("tooltip", Style.Box(new Color(0.07f, 0.062f, 0.08f, 0.98f), Style.Line, 1, 5, 14)));
        card.CustomMinimumSize = new Vector2(380, 0);
        var v = Style.V(4);
        card.AddChild(v);
        v.AddChild(Style.H(10, Style.Label(name, Style.TextBold, 19, Style.GoldHi), Style.Label(fmt(kit.Get(key)), Style.UiBold, Style.Body, Style.Ink)));
        v.AddChild(Style.Rule());
        var bases = kit.GetBase();
        if (bases.TryGetValue(key, out var b0)) v.AddChild(Line("Your calling", key == Stat.MaxHealth && ch.Level > 1 ? $"{b0:0.##}  (with {ch.Level - 1} levels)" : $"{b0:0.##}"));
        int n = 0;
        foreach (var m in kit.List().Where(m => m.Stat == key))
        {
            n++;
            string what = m.Kind switch
            {
                ModKind.Flat => $"{m.Value:+0.##;-0.##}",
                ModKind.Inc => $"{m.Value * 100:+0.#;-0.#}%",
                _ => $"×{1 + m.Value:0.##}",
            };
            v.AddChild(Line(Source(m.Source, ch), what));
        }
        if (n == 0 && !bases.ContainsKey(key)) v.AddChild(Style.Label("Nothing changes it yet.", Style.TextItalic, Style.Caption, Style.InkDim));
        return card;

        static Control Line(string from, string what)
        {
            var l = Style.Label(from, Style.Ui, Style.Small, Style.InkDim);
            l.SizeFlagsHorizontal = SizeFlags.ExpandFill;
            return Style.H(10, l, Style.Label(what, Style.UiBold, Style.Small, Style.Ink));
        }
    }

    /// <summary>A modifier's source, in words.</summary>
    static string Source(string src, CharacterData ch)
    {
        if (src == "attributes") return "Your attributes";
        if (src.StartsWith("item:") && Inventory.Find(ch, src[5..]) is { } w) return Inventory.Name(w.Item);
        if (src.StartsWith("trait:")) return Callings.Trait(src[6..])?.Name ?? "A trait";
        if (src.StartsWith("cond:") && Enum.TryParse<ConditionId>(src[5..], true, out var c)) return Cond.GetValueOrDefault(c, c.ToString()).Split(':')[0];
        return Style.Cap1(src);
    }

    /// <summary>Three traits to choose from, the same three until one is taken.</summary>
    static List<string> Offer(CharacterData ch)
    {
        var pool = Callings.LevelupTraits.Where(t => !ch.Traits.Contains(t)).ToList();
        int seed = ch.Level * 7 + ch.Traits.Count * 13;
        return pool.OrderBy(a => a.Length * seed % 17).Take(3).ToList();
    }

    public static Control Bar(double k, string text, Color color, float width = 260)
    {
        var p = new Panel { CustomMinimumSize = new Vector2(width, 20), MouseFilter = MouseFilterEnum.Ignore };
        p.AddThemeStyleboxOverride("panel", UiArt.Frame("bar_track", Style.Box(new Color(0.04f, 0.035f, 0.05f), Style.GoldDim, 1, 3, 0)));
        p.AddChild(new ColorRect { Color = color with { A = 0.85f }, Position = new Vector2(2, 2), Size = new Vector2((width - 4) * (float)Math.Clamp(k, 0, 1), 16), MouseFilter = MouseFilterEnum.Ignore });
        var l = Style.Label(text, Style.UiBold, Style.Badge, Style.Ink, false, HorizontalAlignment.Center);
        l.Size = new Vector2(width, 20);
        l.VerticalAlignment = VerticalAlignment.Center;
        p.AddChild(l);
        return p;
    }
}

'''
s = s[:a] + new + s[b:]
open(p, 'w', encoding='utf-8', newline='').write(s)
print('done')
