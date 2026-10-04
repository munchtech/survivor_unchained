using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Ui;

/// <summary>
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
        var page = Page(ch.Name, $"Level {ch.Level} {Callings.Background(ch.Background).Name} {Callings.Archetype(ch.Archetype).Name}");

        // Who they are: the figure, the way to the next level, the art in hand, what they know.
        var who = Pane(page, new Rect2(0, 0, 536, 920));
        var fig = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
        fig.AddChild(InventoryScreen.Figure(ch, 400, 430));
        who.AddChild(fig);
        double need = Character.XpForLevel(ch.Level);
        var lvl = new Medallion(76, $"{ch.Level}") { Arc = (float)(ch.Xp / need), ArcColor = Style.Day, Core = new Color("#1c2a3a"), Ink = Style.DayHi };
        var lw = Style.V(4, Style.Label("Level", Style.Display, 22, Style.GoldHi), Bar(ch.Xp / need, $"{Math.Floor(ch.Xp)} / {need} to level {ch.Level + 1}", Style.Day, 380));
        lw.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        who.AddChild(Style.H(Style.Gap3, lvl, lw));
        var ab = Abilities.ById(ch.Ability);
        var arts = Style.Button("", () => G.Open("arts"), false, true);
        var artRow = Style.H(8, Glyphs.Icon(ab.Icon, 20), Style.Label($"In hand: {ab.Name}  ·  rank {ArtBook.Rank(ch, ch.Ability)}", Style.UiBold, Style.Small, Style.GoldHi), Style.Key(G.Key(Act.Arts)));
        artRow.Position = new Vector2(10, 7);
        artRow.MouseFilter = MouseFilterEnum.Ignore;
        arts.AddChild(artRow);
        arts.CustomMinimumSize = new Vector2(0, 38);
        arts.TooltipText = "Your arts: the one in hand, its rank and facets";
        who.AddChild(Nav.Id(arts, "arts"));
        // The calling: how they fight and where they came from, in the game's own words.
        var arch = Callings.Archetype(ch.Archetype);
        var back = Callings.Background(ch.Background);
        who.AddChild(new Section("Calling"));
        var calling = Style.Panel(Style.Slab(14));
        calling.MouseFilter = MouseFilterEnum.Ignore;
        var cv = Style.V(Style.Gap2,
            Style.V(0, Style.Label(arch.Name, Style.UiBold, Style.Body, Style.GoldHi), Style.Label(arch.Tagline, Style.TextItalic, Style.Caption, Style.InkDim, true)),
            Style.V(0, Style.Label(back.Name, Style.UiBold, Style.Body, Style.GoldHi), Style.Label(back.Summary, Style.TextItalic, Style.Caption, Style.InkDim, true)));
        calling.AddChild(cv);
        who.AddChild(calling);
        var knows = ch.Knowledge.Where(Know.ContainsKey).Select(k => Know[k]).ToList();
        who.AddChild(Style.Label(knows.Count == 0 ? "You know little yet that others do not." : $"You know {string.Join(", ", knows)}: it opens words and ways others miss.", Style.TextItalic, Style.Small, Style.Ink, true));
        foreach (var c in ch.Conditions)
        {
            bool good = c.Id is ConditionId.Blessed or ConditionId.Rested or ConditionId.Warmed;
            who.AddChild(Style.H(6, Glyphs.Icon(good ? "sun" : "skull", 16, good ? Style.Good : Style.Bad), Style.Label($"{Cond.GetValueOrDefault(c.Id, c.Id.ToString())}  ·  {c.Days} day{(c.Days == 1 ? "" : "s")}", Style.UiBold, Style.Caption, good ? Style.Good : Style.Bad, true)));
        }

        // The four attributes as pillars, the number the hero; traits under them as cards.
        var mid = Pane(page, new Rect2(560, 0, 840, 920));
        mid.AddChild(new Section("Attributes", ch.Points > 0 ? $"{ch.Points} to spend: a + shows what it would change" : "more with each level"));
        var pillars = Style.H(16);
        mid.AddChild(pillars);
        for (int i = 0; i < Attrs.Length; i++)
        {
            var (id, nm, text) = Attrs[i];
            var box = OrnateBox.Make(OrnateBox.Kind.Card, 14, ch.Points > 0 ? Style.Ember : Style.Gold);
            box.Crest = 90;
            var pillar = Style.Panel(UiArt.Frame("pillar", box));
            pillar.CustomMinimumSize = new Vector2(188, 340);
            pillar.MouseFilter = MouseFilterEnum.Ignore;
            pillars.AddChild(pillar);
            var v = Style.V(Style.Gap2);
            pillar.AddChild(v);
            var med = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
            med.AddChild(new Medallion(120, $"{Attr(ch, id)}"));
            v.AddChild(med);
            v.AddChild(Style.Label(nm.ToUpperInvariant(), Style.Display, 22, Style.GoldHi, false, HorizontalAlignment.Center));
            var words = Style.Label(text, Style.Ui, Style.Caption, Style.Ink, true, HorizontalAlignment.Center);
            words.SizeFlagsVertical = SizeFlags.ExpandFill;
            v.AddChild(words);
            if (ch.Points > 0)
            {
                var attr = id;
                var plus = Style.Button("+  Spend", () => G.Gear((j, b) => j.SpendPoint(attr, b)), true, false);
                plus.MouseEntered += () => ShowStanding(attr);
                plus.MouseExited += () => ShowStanding(null);
                Nav.Mark(plus, $"attr:{attr}", () => G.Gear((j, b) => j.SpendPoint(attr, b)), focus: () => ShowStanding(attr), blur: () => ShowStanding(null));
                v.AddChild(plus);
            }
        }

        mid.AddChild(Style.Gap(Style.Gap2));
        mid.AddChild(new Section("Traits", ch.TraitPicks > 0 ? $"choose {ch.TraitPicks}: each is for good" : "chosen at levels, or given for what you do"));
        var traits = new GridContainer { Columns = 3, MouseFilter = MouseFilterEnum.Ignore };
        traits.AddThemeConstantOverride("h_separation", 12);
        traits.AddThemeConstantOverride("v_separation", 12);
        mid.AddChild(traits);
        Control TraitCard(string name, string text, bool earned, Action? take, string? navId)
        {
            var box = OrnateBox.Make(OrnateBox.Kind.Slab, 14, take != null ? Style.Ember : earned ? Style.EmberHi : Style.Gold);
            var inner = Style.V(4, Style.Label(name, Style.UiBold, Style.Body, take != null || earned ? Style.EmberHi : Style.GoldHi), Style.Label(text, Style.Ui, Style.Caption, Style.Ink, true));
            inner.MouseFilter = MouseFilterEnum.Ignore;
            if (take == null)
            {
                var p = Style.Panel(box, inner);
                p.CustomMinimumSize = new Vector2(258, 118);
                return p;
            }
            var bt = Style.Button("", take);
            foreach (var st in new[] { "normal", "hover", "pressed" }) bt.AddThemeStyleboxOverride(st, box);
            inner.Position = new Vector2(14, 12);
            inner.Size = new Vector2(230, 94);
            bt.AddChild(inner);
            bt.CustomMinimumSize = new Vector2(258, 118);
            if (navId != null) Nav.Id(bt, navId);
            return bt;
        }
        foreach (var t in ch.Traits)
        {
            var def = Callings.Trait(t);
            traits.AddChild(TraitCard((def?.Name ?? t) + (def?.Source == TraitSource.World ? "  ·  earned" : ""), def?.Text ?? "", def?.Source == TraitSource.World, null, null));
        }
        if (ch.TraitPicks > 0)
            foreach (var t in Offer(ch))
            {
                var def = Callings.Trait(t)!;
                traits.AddChild(TraitCard(def.Name, def.Text, false, () => G.Gear((j, bt) => j.PickTrait(t, bt)), $"trait:{t}"));
            }
        // The places still to fill, so the page shows where a character is going.
        int cells = traits.GetChildCount();
        int next = ch.Level % 2 == 0 ? ch.Level + 2 : ch.Level + 1;
        do
        {
            var box = OrnateBox.Make(OrnateBox.Kind.Well, 14);
            var inner = Style.V(4, Style.H(6, Glyphs.Icon("lock", 15, Style.InkFaint), Style.Label($"A trait at level {next}", Style.UiBold, Style.Body, Style.InkDim)),
                Style.Label("One of three, chosen when you reach it. Others come for what you do.", Style.TextItalic, Style.Caption, Style.InkFaint, true));
            var p = Style.Panel(box, inner);
            p.CustomMinimumSize = new Vector2(258, 118);
            p.MouseFilter = MouseFilterEnum.Ignore;
            traits.AddChild(p);
            next += 2;
            cells++;
        } while (cells % 3 != 0 || cells < 6);

        // The whole standing, grouped by what it is for.
        var right = Pane(page, new Rect2(1424, 0, 416, 920), null, Style.Gap2);
        right.AddChild(new Section("Standing", "hover: where from"));
        standing = Style.V(Style.Gap2);
        right.AddChild(standing);
        ShowStanding(null);
        if (Controls.Instance.UsingPad)
            PageFooter(Footer((Act.Confirm, ch.Points > 0 ? "Spend a point" : "Choose"), (Act.TabPrev, "Pack"), (Act.TabNext, "Arts"), (Act.Cancel, "Close")));
    }

    /// <summary>Each standing line's change label, by its key: filled when an attribute is previewed.</summary>
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

    /// <summary>What a point would change, as the change itself (a tenth of a percent shows).</summary>
    static string Change(string key, double now, double then) => key switch
    {
        Stat.CritChance or Stat.Dodge => $"{(then - now) * 100:+0.0;-0.0}%",
        Stat.Cooldown => $"{(1 / then - 1 / now) * 100:+0.0;-0.0}% faster",
        Stat.CritDamage => $"{then - now:+0.00;-0.00}×",
        Stat.MaxHealth or Stat.Armor or Stat.MoveSpeed or Stat.Regen or Stat.PickupRadius or Stat.DashCharges => $"{then - now:+0.##;-0.##}",
        _ => $"{(then - now) * 100:+0.#;-0.#}%",
    };

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

/// <summary>
/// The journal (the web game's overlays/Journal.tsx): what you are doing,
/// who you know, what you have done and what you have learned. Written like
/// a book because it is one, the survivor's own; every line in it is the
/// world's memory, read back.
/// </summary>
public partial class JournalScreen : Overlay
{
    public override string Kind => "journal";
    public override Act? Toggle => Act.Journal;
    string tab = "quests";
    string? quest;
    static readonly Color Ink = Style.ParchmentInk, InkSoft = new("#5a4a36"), Red = new("#8a2a1a");

    public JournalScreen(Game g) : base(g) { }

    static readonly (string Id, string Name)[] Sections = { ("quests", "Quests"), ("people", "People"), ("deeds", "Deeds"), ("codex", "Codex") };

    public override bool Key(Act a)
    {
        int i = Array.FindIndex(Sections, x => x.Id == tab);
        // Its own pages turn with LT and RT (, and .); LB and RB turn the book's.
        if (a == Act.SubNext) { tab = Sections[(i + 1) % Sections.Length].Id; Refresh(); Sound.Sfx.Page(); return true; }
        if (a == Act.SubPrev) { tab = Sections[(i + Sections.Length - 1) % Sections.Length].Id; Refresh(); Sound.Sfx.Page(); return true; }
        // Pages with nothing to choose on them scroll.
        if (a is Act.Up or Act.Down && tab is "deeds" or "codex" && page is { } sc && IsInstanceValid(sc))
        {
            Nav.KeyMode = true;
            sc.ScrollVertical += a == Act.Down ? 90 : -90;
            return true;
        }
        return false;
    }

    ScrollContainer? page;

    /// <summary>Each section's ribbon: its silk, so a glance at the book's top edge finds it.</summary>
    static readonly Dictionary<string, Color> Silk = new()
    {
        ["quests"] = new("#8a2418"), ["people"] = new("#2f5a32"), ["deeds"] = new("#2c3f6a"), ["codex"] = new("#8a6a1e"),
    };

    protected override void Build()
    {
        var content = Page("Journal");
        // The book lies open on the page: the list on the left leaf, what is chosen on the right.
        var book = new OpenBook(new Vector2(1700, 852)) { Position = new Vector2(70, 52) };
        content.AddChild(book);
        page = null;
        var (left, right) = tab switch { "people" => People(), "deeds" => Deeds(), "codex" => Codex(), _ => Quests() };
        Fill(book.Left, left);
        Fill(book.Right, right);
        if (right.GetChildCount() == 0)
        {
            var mark = Glyphs.Icon(tab switch { "people" => "talk", "deeds" => "sigil", "codex" => "book", _ => "quest" }, 220, new Color(0.35f, 0.24f, 0.1f, 0.12f));
            mark.Position = (book.Right.Size - new Vector2(220, 220)) / 2;
            book.Right.AddChild(mark);
        }
        // The leaves' feet: the day on the left, whose book on the right.
        var w = G.Journey.World;
        Foot(book.Left, $"Day {w.Day}");
        Foot(book.Right, $"{G.Journey.Ch.Name}'s journal");

        // The sections as silk ribbons over the top edge, the open one hanging lower; LT and RT turn them.
        bool pad = Controls.Instance.UsingPad;
        var ribbons = Style.H(14);
        ribbons.Position = new Vector2(70 + 120, 52 + 22 - 86);
        ribbons.MouseFilter = MouseFilterEnum.Ignore;
        content.AddChild(ribbons);
        var lt = pad ? Style.PadButton("LT") : Style.Key(G.Key(Act.SubPrev));
        lt.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        ribbons.AddChild(lt);
        foreach (var (id, name) in Sections)
        {
            bool on = tab == id;
            var b = Style.Button(name, () => { tab = id; Refresh(); Sound.Sfx.Page(); }, false, true);
            var rb = new RibbonBox { Silk = Silk[id] };
            var rh = new RibbonBox { Silk = Silk[id], Raised = true };
            b.AddThemeStyleboxOverride("normal", rb);
            b.AddThemeStyleboxOverride("pressed", rb);
            b.AddThemeStyleboxOverride("hover", rh);
            b.AddThemeStyleboxOverride("focus", new StyleBoxEmpty());
            Style.Font(b, Style.UiHeavy, Style.Small, on ? Colors.White : new Color(1, 0.94f, 0.85f, 0.82f), false);
            b.CustomMinimumSize = new Vector2(132, on ? 86 : 66);
            b.SizeFlagsVertical = SizeFlags.ShrinkEnd;
            ribbons.AddChild(Nav.Skip(b));
        }
        var rt = pad ? Style.PadButton("RT") : Style.Key(G.Key(Act.SubNext));
        rt.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        ribbons.AddChild(rt);
        if (pad)
            PageFooter(Footer((Act.SubNext, "Turn to a section"), (Act.Up, "Choose"), (Act.TabPrev, "Arts"), (Act.TabNext, "Map"), (Act.Cancel, "Close")));
    }

    /// <summary>A leaf's words, scrolled if they run long; the left leaf's scroll is the one the keys move.</summary>
    void Fill(Control leaf, Control words)
    {
        var sc = words as ScrollContainer ?? Style.Scroll(words);
        sc.Position = Vector2.Zero;
        sc.Size = leaf.Size - new Vector2(0, 30);
        leaf.AddChild(sc);
        page ??= sc;
    }

    static void Foot(Control leaf, string text)
    {
        var l = Style.Label($"~  {text}  ~", Style.TextItalic, Style.Caption, InkSoft, false, HorizontalAlignment.Center);
        l.Position = new Vector2(0, leaf.Size.Y - 18);
        l.Size = new Vector2(leaf.Size.X, 20);
        leaf.AddChild(l);
    }

    // Reading text on paper: body size, the ink of a hand that wrote it.
    static Label P(string text, int size = Style.Body, Font? font = null, Color? color = null) => Style.Label(text, font ?? Style.Text, size, color ?? Ink, true, HorizontalAlignment.Left, false);
    static Label H2(string text) => Style.Label(text, Style.Display, Style.Title, new Color("#3a2414"), true, HorizontalAlignment.Left, false);

    (Control, Control) Quests()
    {
        var w = G.Journey.World;
        // The troubles first, then the mysteries (the lamps open on the Low
        // Ford road, before anyone in town has asked the survivor for anything).
        var list = w.Quests.Values.Where(q => q.Status != QuestStatus.Unknown && Lore.Quests.ContainsKey(q.Id)).OrderBy(q => Lore.Quests[q.Id].Mystery).ToList();
        quest ??= list.FirstOrDefault(q => q.Status == QuestStatus.Active)?.Id ?? list.FirstOrDefault()?.Id;
        var side = Style.V(4);
        foreach (var (st, label) in new[] { (QuestStatus.Active, "Under way"), (QuestStatus.Resolved, "Done"), (QuestStatus.Failed, "Lost") })
        {
            var qs = list.Where(x => st == QuestStatus.Failed ? x.Status is QuestStatus.Failed or QuestStatus.Abandoned : x.Status == st).ToList();
            if (qs.Count == 0) continue;
            if (side.GetChildCount() > 0) side.AddChild(Style.Gap(Style.Gap2));
            side.AddChild(H2(label));
            foreach (var q in qs)
            {
                var def = Lore.Quests[q.Id];
                var id = q.Id;
                var b = new Button { Text = (def.Mystery ? "? " : "• ") + def.Name, Alignment = HorizontalAlignment.Left, FocusMode = FocusModeEnum.None, Flat = true };
                Nav.Id(b, $"quest:{id}");
                Style.Font(b, quest == id ? Style.TextBold : Style.Text, Style.Body, quest == id ? Red : Ink, false);
                b.AddThemeColorOverride("font_hover_color", Red);
                b.Pressed += () => { quest = id; Refresh(); };
                side.AddChild(b);
            }
        }
        if (list.Count == 0) side.AddChild(P("Nothing written yet. What people ask of you is written here as you hear it.", Style.Small, Style.TextItalic, InkSoft));
        var page = Style.V(8);
        if (quest != null && w.Quests.TryGetValue(quest, out var qst) && Lore.Quests.TryGetValue(quest, out var qd))
        {
            page.AddChild(H2(qd.Name));
            page.AddChild(P(qd.Summary, Style.Body, Style.TextItalic, InkSoft));
            page.AddChild(Style.Rule());
            foreach (var e in qst.Entries) page.AddChild(P(qd.Entries.GetValueOrDefault(e, e)));
            if (qst.Outcome != null && qd.Outcomes?.GetValueOrDefault(qst.Outcome) is string o) page.AddChild(P(o, Style.Body, Style.TextBold, Red));
            if (qst.StartedDay is int d) page.AddChild(P($"Begun on day {d}", Style.Caption, Style.TextItalic, InkSoft));
        }
        else if (list.Count > 0) page.AddChild(P("Choose an entry.", Style.Body, Style.TextItalic, InkSoft));
        return (side, page);
    }

    /// <summary>A measure from -100 to 100 as a line with a mark: green for you, red against, the middle marked.</summary>
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
    }

    string? person;

    /// <summary>People as the quests are: a list of those met (how each feels, in a word), and
    /// the one chosen on the page beside it, drawn as they look, with how they feel about you
    /// on four measures, what is on their mind, and what they know you did.</summary>
    (Control, Control) People()
    {
        var w = G.Journey.World;
        var ctx = G.Journey.Ctx;
        var met = Lore.Npcs.Values.Where(d => w.Npcs.TryGetValue(d.Id, out var s) && s.Flags.TryGetValue("met", out var m) && m.Truthy).ToList();
        if (met.Count == 0) return (Style.V(0, H2("People"), P("You have not met anyone yet. Those you speak with are written here, and how they feel about you.", Style.Body, Style.TextItalic, InkSoft)), Style.V(0));
        if (person == null || met.All(d => d.Id != person)) person = met[0].Id;
        var side = Style.V(2, H2("Those you have met"));
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
            bt.CustomMinimumSize = new Vector2(0, 50);
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
            var name = Style.Label(label, Style.UiBold, Style.Small, Ink, false, HorizontalAlignment.Left, false);
            name.CustomMinimumSize = new Vector2(90, 0);
            axes.AddChild(name);
            axes.AddChild(Feel(val, 260));
            axes.AddChild(Style.Label(Math.Abs(val) < 12 ? "neither way" : $"{(Math.Abs(val) > 55 ? "much " : "")}{(val < 0 ? lo : hi)}".Replace("much unafraid", "quite unafraid"), Style.TextItalic, Style.Caption, InkSoft, false, HorizontalAlignment.Left, false));
        }
        page.AddChild(axes);
        var heard = s0.Memories.Select(m => w.History.FirstOrDefault(h => h.Id == m)).Where(h => h != null).Select(h => h!.Text).ToList();
        page.AddChild(Style.Gap(4));
        page.AddChild(P(heard.Count > 0 ? $"Knows that you {string.Join("; ", heard)}." : "Has heard nothing of what you have done.", Style.Small, Style.Text, InkSoft));
        return (side, page);
    }

    (Control, Control) Deeds()
    {
        var w = G.Journey.World;
        var ch = G.Journey.Ch;
        var left = Style.V(8, H2("What the world remembers"));
        if (w.History.Count == 0) left.AddChild(P("Nothing, yet. Give it time.", 16, Style.TextItalic, InkSoft));
        foreach (var h in Enumerable.Reverse(w.History))
        {
            var knowers = w.Npcs.Values.Where(n => n.Memories.Contains(h.Id)).Select(n => Lore.Person(n.Id)?.Name).Where(n => n != null).ToList();
            left.AddChild(Style.V(1, P($"Day {h.Day}", Style.Badge, Style.UiHeavy, InkSoft), P($"You {h.Text}."),
                P(knowers.Count > 0 ? $"Known to {string.Join(", ", knowers)}" : h.Spread > 0 ? "Word has not got round yet." : "Nobody saw.", Style.Caption, Style.TextItalic, InkSoft)));
        }
        var right = Style.V(8, H2("Where you stand"));
        var stand = Standings.Of(G.Journey.Ctx);
        if (stand.Count == 0) right.AddChild(P("Nobody out here knows you yet.", 16, Style.TextItalic, InkSoft));
        foreach (var st in stand)
        {
            var tone = st.Tone switch { StandingTone.Ally or StandingTone.Friend => new Color("#3a6a2a"), StandingTone.Hostile => Red, StandingTone.Wary => new Color("#8a5a1a"), _ => InkSoft };
            right.AddChild(Style.V(1, Style.H(10, P(st.Name, Style.Body, Style.TextBold), P(st.Word, Style.Small, Style.TextItalic, tone)), P(st.Why, Style.Caption, Style.Text, InkSoft)));
        }
        right.AddChild(Style.Rule());
        right.AddChild(P($"Days on the road: {w.Day}    Creatures slain: {ch.Stats.Kills}    Falls: {ch.Stats.Deaths}    Gold earned: {Math.Floor(ch.Stats.GoldEarned)}", Style.Caption, Style.UiBold, InkSoft));
        return (left, right);
    }

    (Control, Control) Codex()
    {
        var w = G.Journey.World;
        var left = Style.V(8, H2("Bestiary"));
        var seen = w.Bestiary.Where(kv => Content.Enemies.All.ContainsKey(kv.Key)).ToList();
        if (seen.Count == 0) left.AddChild(P("Nothing put down yet.", 16, Style.TextItalic, InkSoft));
        foreach (var (id, n) in seen)
        {
            var e = Content.Enemies.Get(id);
            left.AddChild(Style.V(1, P($"{e.Name}  × {n}", Style.Body, Style.TextBold), P(e.Note, Style.Caption, Style.Text, InkSoft)));
        }
        // What the ember has made: evolutions and unions, named once made; until
        // then the recipe stands as the hint.
        var right = Style.V(8);
        var evos = Weapons.All.Values.Where(x => x.Findable).SelectMany(x => x.Evolutions.Select(e => (W: x, E: e))).ToList();
        int known = evos.Count(x => w.Codex.Contains($"evo:{x.E.Id}")) + Unions.All.Count(u => w.Codex.Contains($"union:{u.Id}"));
        right.AddChild(H2($"What the ember makes  ({known} of {evos.Count + Unions.All.Length})"));
        foreach (var (wd, e) in evos)
        {
            bool found = w.Codex.Contains($"evo:{e.Id}");
            string recipe = $"{wd.Name} at rank 8, with {string.Join(" or ", e.Catalysts.Select(c => Boons.Find(c)?.Name ?? c))}";
            right.AddChild(Style.V(1, P(found ? e.Name : "???", 16, Style.TextBold, found ? Ink : InkSoft), P(found ? $"{recipe}. {e.Description}" : recipe, 14, Style.TextItalic, InkSoft)));
        }
        foreach (var u in Unions.All)
        {
            bool found = w.Codex.Contains($"union:{u.Id}");
            string recipe = $"{Weapons.All[u.A].Name} and {Weapons.All[u.B].Name}, both evolved";
            right.AddChild(Style.V(1, P(found ? u.Name : "??? (a union)", 16, Style.TextBold, found ? Ink : InkSoft), P(found ? $"{recipe}. {u.Description}" : recipe, 14, Style.TextItalic, InkSoft)));
        }
        right.AddChild(Style.Gap(10));
        right.AddChild(H2("Discoveries"));
        foreach (var d in Discoveries.All)
        {
            bool found = w.Codex.Contains(d.Id);
            right.AddChild(Style.V(1, P(found ? d.Name : "Not yet found", Style.Body, Style.TextBold, found ? Ink : InkSoft), P(found ? d.Description : d.Hint, Style.Caption, Style.TextItalic, InkSoft)));
        }
        return (left, right);
    }
}
