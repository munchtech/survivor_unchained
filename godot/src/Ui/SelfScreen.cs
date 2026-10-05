using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Ui;

/// <summary>
/// Who the survivor has become (docs/ui_review/self_v2, approved): the day's book's panel at the
/// right, they standing in the live world beside it. It answers "what am I becoming, and where do
/// my numbers come from?". From the top: the four attributes as one strip, a point spent with a
/// preview of everything it changes until it is confirmed (Elden Ring's level up); the traits as a
/// track of levels (taken, next, later) with those given for deeds after it; the standing in four
/// aligned columns, each number saying where it comes from when hovered; then the calling, the
/// origin, what they know and how they are. The owner on the boxes this replaced: "horribly ai and
/// bloated in screen space".
/// </summary>
public partial class SheetScreen : Overlay
{
    public override string Kind => "character";
    public override Act? Toggle => Act.Character;
    public override float CameraShift => -330;
    public override float CameraNear => 0.56f;

    static readonly (string Id, string Name, string Text)[] Attrs =
    {
        ("might", "Might", "+2.5% damage and +4 health a point"),
        ("finesse", "Finesse", "+0.6% critical chance and +1% speed a point"),
        ("wits", "Wits", "+1% weapon speed, +2% area and ember a point"),
        ("resolve", "Resolve", "+3 health, +0.5 armour, +0.08 regeneration a point"),
    };
    public static readonly Dictionary<string, string> Know = new() { ["beastlore"] = "Beastlore", ["arcana"] = "Arcana", ["underworld"] = "The Underworld", ["faith"] = "The Faith" };
    static readonly Dictionary<ConditionId, string> Cond = new()
    {
        [ConditionId.Wounded] = "Wounded: 20% less health until it heals", [ConditionId.Blightsick] = "Blight-sick: your wounds close slowly", [ConditionId.Poisoned] = "Poisoned",
        [ConditionId.Blessed] = "Blessed: +15% holy damage", [ConditionId.Rested] = "Rested: +5% health", [ConditionId.Warmed] = "Warmed: last night is still with you",
        [ConditionId.Wolfscent] = "Wolf-scented", [ConditionId.Hunted] = "Hunted",
    };

    /// <summary>A line of the standing: its key (a stat, or the art in hand's), its name and how it is written.</summary>
    sealed record Line(string Key, string Name, Func<StatBlock, CharacterData, string> Fmt);

    static string Pct(double v) => $"{(v - 1) * 100:+0;-0;0}%";
    static Line S(string key, string name, Func<double, string> fmt) => new(key, name, (k, _) => fmt(k.Get(key)));
    static Line R(School s, string name) => new(Stat.ResistOf(s), name, (k, _) => $"{Math.Round(k.GetRaw(Stat.ResistOf(s)) * 100)}%");

    /// <summary>The standing in four columns, each one or two groups, so none runs long.</summary>
    static readonly (string Group, Line[] Lines)[][] Columns =
    {
        new[] { ("Staying alive", new[]
        {
            S(Stat.MaxHealth, "Health", v => $"{Math.Round(v)}"),
            S(Stat.Armor, "Armour", v => $"{Math.Round(v)} · {Math.Round(StatBlock.ArmorReduction(v) * 100)}%"),
            S(Stat.Regen, "Regeneration", v => $"{v:0.0}/s"),
            S(Stat.Healing, "Healing", Pct),
            S(Stat.Dodge, "Dodge", v => $"{Math.Round(v * 100)}%"),
        }) },
        new[] { ("Dealing death", new[]
        {
            S(Stat.Damage, "Damage", Pct),
            S(Stat.CritChance, "Critical chance", v => $"{Math.Round(v * 100)}%"),
            S(Stat.CritDamage, "Critical damage", v => $"×{v:0.##}"),
            S(Stat.Cooldown, "Weapon speed", v => v <= 0 ? "-" : $"{(1 / v - 1) * 100:+0;-0;0}%"),
            S(Stat.Area, "Area", Pct),
        }) },
        new[]
        {
            ("Warding", new[] { R(School.Fire, "Fire"), R(School.Frost, "Frost"), R(School.Storm, "Storm"), R(School.Nature, "Nature"), R(School.Shadow, "Shadow") }),
            ("Fortune", new[] { S(Stat.XpGain, "Experience", Pct), S(Stat.GoldGain, "Gold found", Pct) }),
        },
        new[]
        {
            ("Moving", new[]
            {
                S(Stat.MoveSpeed, "Speed", v => $"{v:0.0}"),
                S(Stat.DashCharges, "Dashes", v => $"{Math.Round(v)}"),
                S(Stat.PickupRadius, "Reach", v => $"{v:0.0} m"),
            }),
            ("The art in hand", new Line[]
            {
                new("art:rank", "", (_, ch) => $"rank {ArtsScreen.Numerals[Math.Clamp(ArtBook.Rank(ch, ch.Ability), 1, ArtsScreen.Numerals.Length) - 1]}"),
                new("art:power", "Strength", (_, ch) => $"+{(Abilities.RankPower(ArtBook.Rank(ch, ch.Ability)) - 1) * 100:0}%"),
                new("art:wait", "Wait", (_, ch) => $"{Abilities.ById(ch.Ability).Cooldown * Abilities.RankHaste(ArtBook.Rank(ch, ch.Ability)):0.#} s"),
            }),
        },
    };

    /// <summary>Points put in but not yet kept: shown everywhere as they would be, until Confirm or Undo.</summary>
    static readonly Dictionary<string, int> pending = new();
    static string pendingFor = "";
    string? hovered;

    public SheetScreen(Game g) : base(g) { Nav.Prefer = "attr:might"; }

    CharacterData Ch => G.Journey.Ch;
    static int Attr(CharacterData ch, string id) => id switch { "might" => ch.Attributes.Might, "finesse" => ch.Attributes.Finesse, "wits" => ch.Attributes.Wits, _ => ch.Attributes.Resolve };
    int Spent => pending.Values.Sum();

    readonly Dictionary<string, (Label Now, Label Change)> lines = new();

    protected override void Build()
    {
        var ch = Ch;
        // What was put in and not kept belongs to the survivor it was put in for.
        if (pendingFor != ch.Id || Spent > ch.Points) { pending.Clear(); pendingFor = ch.Id; }
        var v = BookPanel(ch.Name);
        var arch = Callings.Archetype(ch.Archetype);
        var back = Callings.Background(ch.Background);
        var knows = ch.Knowledge.Where(Know.ContainsKey).Select(k => Know[k]).ToList();
        var who = Style.Label($"Level {ch.Level}  ·  {arch.Name}  ·  {back.Name}{(knows.Count > 0 ? $", who knows {string.Join(" and ", knows)}" : "")}",
            Style.TextItalic, 16, Kit.Dim, false, HorizontalAlignment.Center);
        v.AddChild(Style.V(4, who, Xp(ch)));

        Attributes(v, ch);
        Traits(v, ch);
        Standing(v);
        Calling(v, ch, arch, back, knows);
        v.AddChild(Prompts());
        ShowStanding();
    }

    /// <summary>The way to the next level: a thin bar in the day's blue, with its numbers.</summary>
    static Control Xp(CharacterData ch)
    {
        double need = Character.XpForLevel(ch.Level);
        float k = ch.Level >= Character.MaxLevel ? 1 : (float)Math.Clamp(ch.Xp / need, 0, 1);
        var bar = new Control { CustomMinimumSize = new Vector2(220, 4), SizeFlagsVertical = SizeFlags.ShrinkCenter, MouseFilter = MouseFilterEnum.Ignore };
        bar.AddChild(new ColorRect { Color = new Color("#0e0d10"), Size = new Vector2(220, 4), MouseFilter = MouseFilterEnum.Ignore });
        bar.AddChild(new ColorRect { Color = Style.Day, Size = new Vector2(220 * k, 4), MouseFilter = MouseFilterEnum.Ignore });
        var h = Style.H(10, bar, Style.Label(ch.Level >= Character.MaxLevel ? "the last level" : $"{Math.Floor(ch.Xp)} / {need}", Style.UiBold, 13, Kit.Dim, false, HorizontalAlignment.Left, false));
        h.Alignment = BoxContainer.AlignmentMode.Center;
        return h;
    }

    /* ------------------------------------------------------- attributes -- */

    /// <summary>
    /// The attributes as a ledger line (approved: "more like a dnd top bit"): four numerals and their
    /// names set on the page on one baseline, fine rules between, no boxes. A point to spend is a
    /// live coal in a small iron dish at the line's end; given to an attribute (a click on it, A on a
    /// pad, or a coal dragged from the dish), the coal lies at the numeral's foot and the numeral is
    /// lit as if from the fire, its new value, until Keep or Undo; a right click (X) takes it back.
    /// </summary>
    void Attributes(VBoxContainer v, CharacterData ch)
    {
        var end = new List<Control>();
        int free = ch.Points - Spent;
        if (Spent > 0)
        {
            end.Add(Style.Label($"{Spent} of {ch.Points} spent", Style.TextItalic, 15, Style.Ember, false, HorizontalAlignment.Left, false));
            end.Add(Nav.Underlined(Nav.Id(Kit.Word("UNDO", Undo, Kit.Dim, 14), "undo")));
            var keep = Nav.Underlined(Nav.Id(Kit.Word("KEEP", Keep, Style.Ember, 14), "keep"));
            // (the mouse's hover marks it the same quiet way the pad's focus does)
            var under = new StyleBoxFlat { BgColor = Colors.Transparent, BorderColor = Style.Ember, BorderWidthBottom = 2, ContentMarginLeft = 4, ContentMarginRight = 4, ContentMarginTop = 2, ContentMarginBottom = 2 };
            keep.AddThemeStyleboxOverride("hover", under);
            end.Add(keep);
        }
        v.AddChild(Kit.Head("Attributes", "hover: what a point gives", end.ToArray()));

        var line = Style.H(0);
        line.CustomMinimumSize = new Vector2(0, 70);
        cells.Clear();
        for (int i = 0; i < Attrs.Length; i++)
        {
            var (id, name, _) = Attrs[i];
            if (i > 0) line.AddChild(new LedgerRule());
            int now = Attr(ch, id), add = pending.GetValueOrDefault(id);
            var cell = new LedgerEntry(now + add, name, add) { SizeFlagsHorizontal = SizeFlags.ExpandFill };
            var attr = id;
            cell.CanTake = d => d == "coal" && Ch.Points - Spent > 0;
            cell.Take = _ => Put(attr);
            cell.GuiInput += e =>
            {
                if (e is not InputEventMouseButton { Pressed: true } mb) return;
                if (mb.ButtonIndex == MouseButton.Left) Put(attr);
                else if (mb.ButtonIndex == MouseButton.Right) Take(attr);
            };
            cell.MouseEntered += () => HoverAttr(attr, cell);
            cell.MouseExited += () => HoverAttr(null, null);
            Nav.Mark(cell, $"attr:{id}", () => Put(attr), () => Take(attr), null, () => HoverAttr(attr, cell), () => HoverAttr(null, null));
            cells[id] = cell;
            line.AddChild(cell);
        }
        if (ch.Points > 0)
        {
            var dish = new CoalDish(free);
            dishAt = dish;
            var cap = Style.Label(free == 0 ? "all given" : free == 1 ? "1 to spend" : $"{free} to spend", Style.UiBold, 13, free > 0 ? Kit.Dim : Kit.Faint, false, HorizontalAlignment.Center, false);
            var col = Style.V(0, dish, cap);
            col.SizeFlagsVertical = SizeFlags.ShrinkEnd;
            line.AddChild(Style.Gap(0));
            line.AddChild(new LedgerRule());
            line.AddChild(col);
        }
        else dishAt = null;
        v.AddChild(line);
        // A coal just given or taken back flies between the dish and the numeral once the line is laid out.
        if (flight is { } f && Time.GetTicksMsec() - f.At < 200) Callable.From(() => Fly(f.Attr, f.ToAttr)).CallDeferred();
        flight = null;
    }

    readonly Dictionary<string, LedgerEntry> cells = new();
    CoalDish? dishAt;
    static (string Attr, bool ToAttr, ulong At)? flight;

    /// <summary>A coal crossing between the dish and an attribute's foot, on a low arc, with its sound.</summary>
    void Fly(string attr, bool toAttr)
    {
        if (!cells.TryGetValue(attr, out var cell) || !IsInstanceValid(cell)) return;
        var at = cell.CoalAt;
        var from = dishAt != null && IsInstanceValid(dishAt) ? dishAt.GlobalPosition + new Vector2(42, 18) : at + new Vector2(300, 0);
        var (a, b) = toAttr ? (from, at) : (at, from);
        var coal = new Coal(5) { ZIndex = 45 };
        AddChild(coal);
        coal.GlobalPosition = a - coal.Size / 2;
        if (toAttr) cell.HideCoal(true);
        var tw = coal.CreateTween();
        tw.TweenMethod(Callable.From<float>(k =>
        {
            if (!IsInstanceValid(coal)) return;
            var p = a.Lerp(b, k) + new Vector2(0, -40 * Mathf.Sin(k * Mathf.Pi));
            coal.GlobalPosition = p - coal.Size / 2;
        }), 0f, 1f, 0.32).SetTrans(Tween.TransitionType.Sine).SetEase(Tween.EaseType.InOut);
        tw.TweenCallback(Callable.From(() =>
        {
            if (IsInstanceValid(cell)) cell.HideCoal(false);
            coal.QueueFree();
        }));
    }

    void Put(string attr)
    {
        if (Ch.Points - Spent <= 0) { Sound.Sfx.Deny(); return; }
        pending[attr] = pending.GetValueOrDefault(attr) + 1;
        flight = (attr, true, Time.GetTicksMsec());
        Sound.Sfx.Click();
        Refresh();
    }

    void Take(string attr)
    {
        if (pending.GetValueOrDefault(attr) <= 0) return;
        if (--pending[attr] == 0) pending.Remove(attr);
        flight = (attr, false, Time.GetTicksMsec());
        Sound.Sfx.Click();
        Refresh();
    }

    void Undo() { pending.Clear(); Sound.Sfx.Click(); Refresh(); }

    /// <summary>What was put in, kept: each point spent for good.</summary>
    void Keep()
    {
        var put = pending.ToList();
        pending.Clear();
        Sound.Sfx.Pick();
        G.Gear((j, b) => { foreach (var (attr, n) in put) for (int i = 0; i < n; i++) j.SpendPoint(attr, b); });
    }

    /// <summary>The survivor as they would be with what is pending, and one more point in `also`.</summary>
    CharacterData Would(string? also)
    {
        var c = Core.Json.Clone(Ch);
        foreach (var (attr, n) in pending.Append(also != null ? new KeyValuePair<string, int>(also, 1) : default))
            for (int i = 0; i < n; i++)
                switch (attr) { case "might": c.Attributes.Might++; break; case "finesse": c.Attributes.Finesse++; break; case "wits": c.Attributes.Wits++; break; case "resolve": c.Attributes.Resolve++; break; }
        return c;
    }

    void HoverAttr(string? attr, Control? over)
    {
        hovered = attr;
        ShowStanding();
        if (attr == null || over == null) { TipBeside(null, null, null, true, BookX); return; }
        var (_, name, text) = Attrs.First(a => a.Id == attr);
        var card = new PanelContainer { MouseFilter = MouseFilterEnum.Ignore };
        card.AddThemeStyleboxOverride("panel", new CardBox { Tier = Kit.HeadInk });
        card.CustomMinimumSize = new Vector2(300, 0);
        var c = Style.V(5, Style.Label(name, Style.TextBold, 19, Kit.Ink), Style.Label(text, Style.Ui, 15, Kit.Ink2, true));
        if (Ch.Points - Spent > 0)
        {
            // What the next point would change, in the standing's own words.
            var now = Character.Kit(Would(null)).Stats;
            var then = Character.Kit(Would(attr)).Stats;
            c.AddChild(Kit.RuleH());
            c.AddChild(Style.Label("One more point:", Style.TextItalic, 14, Kit.Dim));
            foreach (var l in Columns.SelectMany(col => col).SelectMany(gr => gr.Lines).Where(l => !l.Key.StartsWith("art:")))
            {
                if (Math.Abs(then.Get(l.Key) - now.Get(l.Key)) < 1e-6) continue;
                var nl = Style.Label(l.Name, Style.Ui, 15, Kit.Ink2);
                nl.SizeFlagsHorizontal = SizeFlags.ExpandFill;
                c.AddChild(Style.H(8, nl, Kit.Num(Change(l.Key, now.Get(l.Key), then.Get(l.Key)), 15, new Color("#ffb05a"))));
            }
        }
        card.AddChild(c);
        TipBeside(card, null, over, true, BookX);
    }

    /* ----------------------------------------------------------- traits -- */

    void Traits(VBoxContainer v, CharacterData ch)
    {
        v.AddChild(Kit.Head("Traits", "one of three at every second level, and some given for what you do"));
        var chosen = ch.Traits.Where(t => Callings.Trait(t)?.Source == TraitSource.Levelup).ToList();
        var track = new TraitTrack(ch, chosen, (id, over) => HoverTrait(id, over), () => HoverTrait(null, null));
        v.AddChild(track);
        var given = ch.Traits.Where(t => Callings.Trait(t)?.Source is TraitSource.World or TraitSource.Background).ToList();
        if (given.Count > 0)
        {
            var chips = Style.H(8, Style.Label("GIVEN", Style.UiHeavy, 12, Kit.Dim, false, HorizontalAlignment.Left, false));
            foreach (var t in given)
            {
                var chip = Kit.Chip(Callings.Trait(t)?.Name ?? t);
                var id = t;
                chip.MouseEntered += () => HoverTrait(id, chip);
                chip.MouseExited += () => HoverTrait(null, null);
                chips.AddChild(chip);
            }
            foreach (var c in chips.GetChildren().OfType<Control>()) c.SizeFlagsVertical = SizeFlags.ShrinkCenter;
            v.AddChild(chips);
        }
        if (ch.TraitPicks <= 0) return;
        // A trait to choose: the three on offer as type on the page, no boxes; each for good, so it
        // is taken by holding it until the ember runs the length of its name.
        var offers = Style.H(22);
        var picks = Offer(ch);
        for (int i = 0; i < picks.Count; i++)
        {
            if (i > 0) offers.AddChild(new LedgerRule());
            var def = Callings.Trait(picks[i])!;
            var id = picks[i];
            var w = new HeldWord(def.Name, def.Text, () => G.Gear((j, bt) => j.PickTrait(id, bt))) { SizeFlagsHorizontal = SizeFlags.ExpandFill };
            Nav.Mark(w, $"trait:{id}", w.Nudge);
            offers.AddChild(w);
        }
        v.AddChild(Style.Label($"Choose {(ch.TraitPicks == 1 ? "one" : ch.TraitPicks.ToString())}, holding it: each is for good.", Style.TextItalic, 14, Style.Ember));
        v.AddChild(offers);
    }

    void HoverTrait(string? id, Control? over)
    {
        if (id == null || over == null) { TipBeside(null, null, null, true, BookX); return; }
        var card = new PanelContainer { MouseFilter = MouseFilterEnum.Ignore };
        card.AddThemeStyleboxOverride("panel", new CardBox { Tier = Style.Ember });
        card.CustomMinimumSize = new Vector2(300, 0);
        if (id.StartsWith("level:"))
            card.AddChild(Style.V(4, Style.Label($"A trait at level {id[6..]}", Style.TextBold, 18, Kit.Ink),
                Style.Label("One of three, chosen when you reach it. Others are given for what you do.", Style.TextItalic, 14, Kit.Dim, true)));
        else
        {
            var def = Callings.Trait(id);
            card.AddChild(Style.V(4, Style.Label(def?.Name ?? id, Style.TextBold, 18, Kit.Ink), Style.Label(def?.Text ?? "", Style.Ui, 15, Kit.Ink2, true),
                Style.Label(def?.Source switch { TraitSource.World => "Given for a deed.", TraitSource.Background => "Given by your origin.", _ => "Chosen, for good." }, Style.TextItalic, 14, Kit.Dim)));
        }
        TipBeside(card, null, over, true, BookX);
    }

    /// <summary>Three traits to choose from, the same three until one is taken.</summary>
    static List<string> Offer(CharacterData ch)
    {
        var pool = Callings.LevelupTraits.Where(t => !ch.Traits.Contains(t)).ToList();
        int seed = ch.Level * 7 + ch.Traits.Count * 13;
        return pool.OrderBy(a => a.Length * seed % 17).Take(3).ToList();
    }

    /* --------------------------------------------------------- standing -- */

    void Standing(VBoxContainer v)
    {
        v.AddChild(Kit.Head("Standing", "hover a number: where it comes from"));
        var cols = Style.H(22);
        lines.Clear();
        arrows.Clear();
        var ch = Ch;
        foreach (var groups in Columns)
        {
            var col = Style.V(0);
            col.SizeFlagsHorizontal = SizeFlags.ExpandFill;
            col.SizeFlagsStretchRatio = 1;
            bool first = true;
            foreach (var (group, ls) in groups)
            {
                if (!first) col.AddChild(Style.Gap(10));
                first = false;
                col.AddChild(Style.Label(group.ToUpperInvariant(), Style.UiHeavy, 12, Kit.HeadInk, false, HorizontalAlignment.Left, false));
                col.AddChild(Style.Gap(3));
                foreach (var l in ls)
                {
                    string name = l.Key == "art:rank" ? Abilities.ById(ch.Ability).Name : l.Name;
                    var label = Style.Label(name, Style.Ui, 16, Kit.Ink2, false, HorizontalAlignment.Left, false);
                    label.SizeFlagsHorizontal = SizeFlags.ExpandFill;
                    label.ClipText = true;
                    var now = Kit.Num("", 16);
                    // While a coal is given: the number now, dimmed, then an ember arrow and what it will be.
                    var change = Kit.Num("", 16, new Color("#ffb05a"));
                    var arrow = new Arrow(Style.Ember) { Visible = false, SizeFlagsVertical = SizeFlags.ShrinkCenter };
                    lines[l.Key] = (now, change);
                    arrows[l.Key] = arrow;
                    var row = Style.H(4, label, now, arrow, change);
                    var holder = new PanelContainer { MouseFilter = MouseFilterEnum.Stop, CustomMinimumSize = new Vector2(0, 27) };
                    holder.AddThemeStyleboxOverride("panel", new LineUnder());
                    holder.AddChild(row);
                    var line = l;
                    if (!l.Key.StartsWith("art:"))
                    {
                        holder.MouseEntered += () => TipBeside(Breakdown(line), null, holder, true, BookX);
                        holder.MouseExited += () => TipBeside(null, null, null, true, BookX);
                        Nav.Mark(holder, $"stat:{l.Key}", null, focus: () => TipBeside(Breakdown(line), null, holder, true, BookX), blur: () => TipBeside(null, null, null, true, BookX));
                    }
                    col.AddChild(holder);
                }
            }
            cols.AddChild(col);
        }
        v.AddChild(cols);
    }

    /// <summary>The standing's numbers, and what the pending points (and the hovered one) change in them.</summary>
    void ShowStanding()
    {
        var ch = Ch;
        var kit = Character.Kit(ch).Stats;
        // While coals are given, every number they move shows what it will be, in the coals' ember,
        // until Keep or Undo (the owner: show "the projected stats when you place a point"). A hover
        // alone moves nothing here: its card says what one more point would give.
        var would = Spent > 0 ? Would(null) : null;
        StatBlock? then = would != null ? Character.Kit(would).Stats : null;
        foreach (var l in Columns.SelectMany(c => c).SelectMany(g => g.Lines))
        {
            if (!lines.TryGetValue(l.Key, out var at) || !IsInstanceValid(at.Now)) continue;
            bool moves = then != null && !l.Key.StartsWith("art:") && Math.Abs(then.Get(l.Key) - kit.Get(l.Key)) > 1e-6;
            at.Now.Text = l.Fmt(kit, ch);
            // A warding below nothing is a weakness: said in red.
            at.Now.AddThemeColorOverride("font_color", moves ? Kit.Dim : l.Key.StartsWith("resist.") && kit.GetRaw(l.Key) < -1e-6 ? Style.Bad : Kit.Ink);
            at.Change.Text = moves ? l.Fmt(then!, would!) : "";
            at.Change.Visible = moves;
            if (arrows.TryGetValue(l.Key, out var arrow)) arrow.Visible = moves;
        }
    }

    readonly Dictionary<string, Arrow> arrows = new();

    /// <summary>What a point would change, as the change itself (a tenth of a percent shows).</summary>
    static string Change(string key, double now, double then) => key switch
    {
        Stat.CritChance or Stat.Dodge => $"{(then - now) * 100:+0.0;-0.0}%",
        Stat.Cooldown => $"{(1 / then - 1 / now) * 100:+0.0;-0.0}%",
        Stat.CritDamage => $"{then - now:+0.00;-0.00}×",
        Stat.MaxHealth or Stat.Armor or Stat.MoveSpeed or Stat.Regen or Stat.PickupRadius or Stat.DashCharges => $"{then - now:+0.##;-0.##}",
        _ => $"{(then - now) * 100:+0.#;-0.#}%",
    };

    /// <summary>Where a number comes from: the calling's base, then each thing that moves it.</summary>
    Control Breakdown(Line l)
    {
        var ch = Ch;
        var kit = Character.Kit(ch).Stats;
        var key = l.Key;
        var card = new PanelContainer { MouseFilter = MouseFilterEnum.Ignore };
        card.AddThemeStyleboxOverride("panel", new CardBox { Tier = Kit.HeadInk });
        card.CustomMinimumSize = new Vector2(340, 0);
        var v = Style.V(4);
        card.AddChild(v);
        var nm = Style.Label(l.Name, Style.TextBold, 19, Kit.Ink);
        nm.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        v.AddChild(Style.H(10, nm, Kit.Num(l.Fmt(kit, ch), 17)));
        v.AddChild(Kit.RuleH());
        var bases = kit.GetBase();
        if (bases.TryGetValue(key, out var b0)) v.AddChild(Row("Your calling", key == Stat.MaxHealth && ch.Level > 1 ? $"{b0:0.##}  (with {ch.Level - 1} levels)" : $"{b0:0.##}"));
        int n = 0;
        foreach (var m in kit.List().Where(m => m.Stat == key))
        {
            n++;
            string what = m.Kind switch { ModKind.Flat => $"{m.Value:+0.##;-0.##}", ModKind.Inc => $"{m.Value * 100:+0.#;-0.#}%", _ => $"×{1 + m.Value:0.##}" };
            v.AddChild(Row(Source(m.Source, ch), what));
        }
        if (n == 0 && !bases.ContainsKey(key)) v.AddChild(Style.Label("Nothing changes it yet.", Style.TextItalic, 14, Kit.Dim));
        return card;

        static Control Row(string from, string what)
        {
            var f = Style.Label(from, Style.Ui, 15, Kit.Ink2);
            f.SizeFlagsHorizontal = SizeFlags.ExpandFill;
            return Style.H(10, f, Kit.Num(what, 15));
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

    /* ---------------------------------------------------------- calling -- */

    void Calling(VBoxContainer v, CharacterData ch, Archetype arch, Background back, List<string> knows)
    {
        v.AddChild(Kit.Head("Calling and origin"));
        var row = Style.H(22);
        // (four even columns across the panel's content, as the standing's above)
        const float ColW = (Overlay.BookW - 2 * Overlay.Margin - 3 * 22) / 4f;
        Control Col(string head, string name, string text, Color? nameCol = null)
        {
            var c = Style.V(2, Style.Label(head, Style.UiHeavy, 12, Kit.HeadInk, false, HorizontalAlignment.Left, false),
                Style.Label(Kit.Balance(name, Style.TextBold, 18, ColW), Style.TextBold, 18, nameCol ?? Kit.Ink, false, HorizontalAlignment.Left, true), Style.Label(Kit.Balance(text, Style.TextItalic, 14, ColW), Style.TextItalic, 14, Kit.Dim, false, HorizontalAlignment.Left, true));
            c.SizeFlagsHorizontal = SizeFlags.ExpandFill;
            return c;
        }
        row.AddChild(Col("CALLING", arch.Name, arch.Tagline));
        row.AddChild(Col("ORIGIN", back.Name, back.Summary));
        row.AddChild(Col("KNOWS", knows.Count == 0 ? "Little yet" : string.Join(", ", knows), knows.Count == 0 ? "Nothing others do not." : "It opens words and ways others miss."));
        // How they are: what ails or blesses them, with the days left.
        if (ch.Conditions.Count == 0) row.AddChild(Col("NOW", "Hale", "Nothing ails or blesses you."));
        else
        {
            var c = ch.Conditions[0];
            bool good = c.Id is ConditionId.Blessed or ConditionId.Rested or ConditionId.Warmed;
            var parts = Cond.GetValueOrDefault(c.Id, c.Id.ToString()).Split(':', 2);
            string more = ch.Conditions.Count > 1 ? $" And {ch.Conditions.Count - 1} more." : "";
            row.AddChild(Col("NOW", parts[0], $"{(parts.Length > 1 ? Style.Cap1(parts[1].Trim()) + ". " : "")}{c.Days} day{(c.Days == 1 ? "" : "s")} more.{more}", good ? Style.Good : Style.Bad));
        }
        v.AddChild(row);
    }

    Control Prompts()
    {
        bool pad = Controls.Instance.UsingPad;
        var items = new List<Control>
        {
            pad ? Kit.Prompt(Act.Up, "Move") : Kit.Prompt("Arrows", "Move"),
            Kit.Prompt(Act.Confirm, "Give a coal"),
            Kit.Prompt(Act.Alt, "Take it back"),
            pad ? Kit.Prompt(Act.TabNext, "Turn") : Kit.Prompt("[ ]", "Turn"),
            Kit.Prompt(Act.Cancel, Spent > 0 ? "Undo" : "Close"),
        };
        var p = Kit.Prompts(items.ToArray());
        p.CustomMinimumSize = new Vector2(0, 30);
        return p;
    }

    public override bool Key(Act a)
    {
        if (a == Act.Cancel && Spent > 0) { Undo(); return true; }
        if (a == Act.Alt2 && Spent > 0) { Keep(); return true; }
        return false;
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
/// An attribute on Self's ledger line: its numeral large and its name in small capitals on one
/// baseline, set on the page with no box. Given a coal, the numeral shows what it will be, lit
/// from within as iron in the fire, and the coal lies just under it until Keep or Undo.
/// </summary>
public partial class LedgerEntry : Control
{
    const float Base = 48, NumSize = 44, NameSize = 17;
    public Func<string, bool>? CanTake;
    public Action<string>? Take;
    readonly Label numeral;
    readonly List<Coal> coals = new();
    readonly float numW;

    public LedgerEntry(int value, string name, int given)
    {
        MouseFilter = MouseFilterEnum.Stop;
        MouseDefaultCursorShape = CursorShape.PointingHand;
        CustomMinimumSize = new Vector2(0, 70);
        bool lit = given > 0;
        var face = Style.Display;
        numW = face.GetStringSize($"{value}", HorizontalAlignment.Left, -1, (int)NumSize).X;
        if (lit)
        {
            // The fire's light behind the numeral it was given to.
            var halo = new TextureRect
            {
                Texture = UiArt.Art("coal/numeral_glow.png") ?? Halo, ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale,
                Size = new Vector2(numW + 44, 70), Position = new Vector2(-22, Base - 52), MouseFilter = MouseFilterEnum.Ignore,
                Modulate = Style.Ember with { A = 0.6f }, Material = new CanvasItemMaterial { BlendMode = CanvasItemMaterial.BlendModeEnum.Add },
            };
            AddChild(halo);
        }
        numeral = Style.Label($"{value}", face, (int)NumSize, lit ? new Color("#ffc47a") : Kit.Ink, false, HorizontalAlignment.Left, !lit);
        if (lit)
        {
            numeral.AddThemeColorOverride("font_shadow_color", Style.Ember with { A = 0.7f });
            numeral.AddThemeConstantOverride("shadow_outline_size", 12);
            numeral.AddThemeConstantOverride("shadow_offset_x", 0);
            numeral.AddThemeConstantOverride("shadow_offset_y", 0);
        }
        numeral.Position = new Vector2(0, Base - face.GetAscent((int)NumSize));
        AddChild(numeral);
        var nm = Style.Label(name.ToUpperInvariant(), Style.DisplayLight, (int)NameSize, lit ? new Color("#e8c496") : Kit.HeadInk, false, HorizontalAlignment.Left, false);
        nm.Position = new Vector2(numW + 12, Base - Style.DisplayLight.GetAscent((int)NameSize));
        AddChild(nm);
        // The coals it was given, lying just under the numeral, so the line's rhythm holds.
        for (int i = 0; i < given; i++)
        {
            var c = new Coal(31 + i, 1.05f);
            c.Position = new Vector2(numW / 2 - c.Size.X / 2 + (i - (given - 1) / 2f) * 15, Base + 2);
            coals.Add(c);
            AddChild(c);
        }
    }

    /// <summary>Where a coal given to it comes to rest, on the screen.</summary>
    public Vector2 CoalAt => GlobalPosition + new Vector2(numW / 2 + (coals.Count - 1) * 6.5f, Base + 2 + 8);

    /// <summary>The last coal hidden while one is flying in to take its place.</summary>
    public void HideCoal(bool hide) { if (coals.Count > 0) coals[^1].Visible = !hide; }

    static GradientTexture2D? halo;
    static GradientTexture2D Halo => halo ??= new GradientTexture2D
    {
        Width = 64, Height = 64, Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.5f, 0.55f), FillTo = new Vector2(1, 0.55f),
        Gradient = new Gradient { Colors = new[] { Colors.White, Colors.White with { A = 0.25f }, Colors.White with { A = 0 } }, Offsets = new[] { 0f, 0.45f, 1f } },
    };

    public override bool _CanDropData(Vector2 at, Variant data) => data.VariantType == Variant.Type.String && (CanTake?.Invoke(data.AsString()) ?? false);
    public override void _DropData(Vector2 at, Variant data) => Take?.Invoke(data.AsString());
}

/// <summary>
/// A choice for good set as type on the page (a trait on offer): its name in display type and the
/// line under it, no box. Hovered, an ember glow wakes under the name; held (the mouse, or A or Enter
/// with focus), the ember runs the name's length, and when it reaches the end the choice is made.
/// Let go early and it cools back (the rule for what cannot be undone: held, never asked twice).
/// </summary>
public partial class HeldWord : Control
{
    readonly Label name;
    readonly Action done;
    double p, flash;
    bool mouse, over, fired;

    public HeldWord(string title, string text, Action done, int size = 19, Color? ink = null)
    {
        this.done = done;
        MouseFilter = MouseFilterEnum.Stop;
        MouseDefaultCursorShape = CursorShape.PointingHand;
        name = size >= 18 ? Style.Label(title, Style.DisplayLight, size, ink ?? Style.EmberHi, false, HorizontalAlignment.Left, true)
            : Style.Label(title, Style.UiBold, size, ink ?? Style.EmberHi, false, HorizontalAlignment.Left, true);
        var body = Style.V(3, name);
        if (text != "") body.AddChild(Style.Label(text, Style.Ui, 14, Kit.Ink2, true));
        body.MouseFilter = MouseFilterEnum.Ignore;
        body.Position = new Vector2(0, 2);
        AddChild(body);
        Resized += () => body.Size = new Vector2(Size.X, 0);
        CustomMinimumSize = text != "" ? new Vector2(0, 78) : new Vector2(name.GetCombinedMinimumSize().X + 4, name.GetCombinedMinimumSize().Y + 10);
        MouseEntered += () => { over = true; Sound.Sfx.Hover(); };
        MouseExited += () => { over = false; mouse = false; };
        GuiInput += e => { if (e is InputEventMouseButton { ButtonIndex: MouseButton.Left } mb) mouse = mb.Pressed; };
    }

    /// <summary>A tap: the ember jumps a little and cools, as a hint that it must be held.</summary>
    public void Nudge() { if (!fired && p < 0.15) p = 0.15; }

    bool Held()
    {
        if (mouse) return true;
        for (Node? n = GetParent(); n != null; n = n.GetParent())
            if (n is Overlay o) return o.Focused(this) && Play.Controls.Instance.Held(Play.Act.Confirm);
        return false;
    }

    public override void _Process(double delta)
    {
        if (flash > 0)
        {
            flash -= delta;
            if (flash <= 0) { fired = true; done(); }
        }
        else if (Held() && !fired) { p = Math.Min(1, p + delta / HoldButton.Time); if (p >= 1) { flash = 0.15; Sound.Sfx.Pick(); } }
        else if (!Held()) { fired = false; p = Math.Max(0, p - delta / HoldButton.Drain); }
        QueueRedraw();
    }

    public override void _Draw()
    {
        float w = Math.Min(name.GetCombinedMinimumSize().X + 4, Size.X), y = name.Size.Y + 4;
        // the glow of a hover under the name, then the ember running along it as it is held
        if (over || p > 0) DrawRect(new Rect2(0, y, w, 1), Style.Ember with { A = 0.35f });
        if (p > 0) DrawRect(new Rect2(0, y - 0.5f, w * (float)Math.Min(1, p), 2.5f), (flash > 0 ? Style.EmberHi : Style.Ember) with { A = 0.95f });
    }
}

/// <summary>A fine upright rule between the ledger's entries, fading at both ends.</summary>
public partial class LedgerRule : Control
{
    public LedgerRule() { CustomMinimumSize = new Vector2(29, 60); MouseFilter = MouseFilterEnum.Ignore; SizeFlagsVertical = SizeFlags.ShrinkEnd; }

    public override void _Draw()
    {
        float x = 14, y0 = 8, y1 = Size.Y - 4, mid = (y0 + y1) / 2;
        var c = Kit.Rule.Lightened(0.1f);
        // (two halves, each fading toward its end)
        DrawPolygon(new[] { new Vector2(x - 0.5f, y0), new Vector2(x + 0.5f, y0), new Vector2(x + 0.5f, mid), new Vector2(x - 0.5f, mid) }, new[] { c with { A = 0 }, c with { A = 0 }, c, c });
        DrawPolygon(new[] { new Vector2(x - 0.5f, mid), new Vector2(x + 0.5f, mid), new Vector2(x + 0.5f, y1), new Vector2(x - 0.5f, y1) }, new[] { c, c, c with { A = 0 }, c with { A = 0 } });
    }
}

/// <summary>A line of a column with a thin rule under it, the numbers' only furniture.</summary>
public partial class LineUnder : StyleBox
{
    public override void _Draw(Rid ci, Rect2 r) =>
        RenderingServer.CanvasItemAddRect(ci, new Rect2(r.Position.X, r.End.Y - 1, r.Size.X, 1), Kit.Rule with { A = 0.75f });
}

/// <summary>An arrow drawn, pointing right (the faces have none): what a number would become.</summary>
public partial class Arrow : Control
{
    readonly Color colour;
    public Arrow(Color colour) { this.colour = colour; CustomMinimumSize = new Vector2(16, 12); MouseFilter = MouseFilterEnum.Ignore; }

    public override void _Draw()
    {
        DrawLine(new Vector2(1, 6), new Vector2(11, 6), colour, 2.2f, true);
        DrawColoredPolygon(new[] { new Vector2(15, 6), new Vector2(9, 1.5f), new Vector2(9, 10.5f) }, colour);
    }
}

/// <summary>
/// The traits as a track of levels (UI_RESEARCH 11): taken (a filled node, named), next (lit in
/// ember, with its level; "Choose" when a pick waits), later (small and dim, the level only).
/// Names sit below and above the line in turn, so neighbours never run into each other.
/// </summary>
public partial class TraitTrack : Control
{
    readonly List<(float X, int Level, string? Trait, int State)> nodes = new();
    readonly float top;

    public TraitTrack(CharacterData ch, List<string> chosen, Action<string, Control> hover, Action leave)
    {
        MouseFilter = MouseFilterEnum.Ignore;
        // Names go above the line too only once two are taken; until then the track keeps low.
        top = chosen.Count >= 2 ? 38 : 22;
        CustomMinimumSize = new Vector2(0, top + 40);
        SizeFlagsHorizontal = SizeFlags.ExpandFill;
        int next = ch.TraitPicks > 0 ? 2 * (chosen.Count + 1) : ch.Level % 2 == 0 ? ch.Level + 2 : ch.Level + 1;
        int i = 0;
        for (int lv = 2; lv <= Character.MaxLevel; lv += 2, i++)
        {
            string? t = i < chosen.Count ? chosen[i] : null;
            int state = t != null ? 0 : lv == next ? 1 : 2;
            nodes.Add((0, lv, t, state));
        }
        Resized += () => Lay(ch, hover, leave);
    }

    void Lay(CharacterData ch, Action<string, Control> hover, Action leave)
    {
        foreach (var c in GetChildren()) { RemoveChild(c); c.QueueFree(); }
        float x0 = 17, x1 = Size.X - 17, step = (x1 - x0) / Math.Max(1, nodes.Count - 1), y = top;
        for (int i = 0; i < nodes.Count; i++)
        {
            var (_, lv, t, state) = nodes[i];
            float x = x0 + i * step;
            nodes[i] = (x, lv, t, state);
            float r = state == 2 ? 6 : 17;
            var hit = new Control { Position = new Vector2(x - Math.Max(r, 12), y - Math.Max(r, 12)), Size = new Vector2(Math.Max(r, 12) * 2, Math.Max(r, 12) * 2), MouseFilter = MouseFilterEnum.Stop };
            string id = t ?? $"level:{lv}";
            hit.MouseEntered += () => hover(id, hit);
            hit.MouseExited += leave;
            AddChild(hit);
            if (state == 2)
            {
                AddChild(Centred(Style.Label($"{lv}", Style.UiBold, 12, Kit.Faint, false, HorizontalAlignment.Center, false), x, y + 10));
                continue;
            }
            string text = t != null ? Callings.Trait(t)?.Name ?? t : ch.TraitPicks > 0 ? "Choose" : "Next";
            var label = Style.Label(text, Style.UiBold, 14, state == 1 ? Style.Ember : Kit.Ink, false, HorizontalAlignment.Center, false);
            // Taken names alternate below and above the line; the next one is always below.
            bool above = state == 0 && i % 2 == 1;
            AddChild(Centred(label, x, above ? y - 38 : y + 21));
        }
        QueueRedraw();
    }

    static Control Centred(Label l, float x, float y)
    {
        var w = l.GetCombinedMinimumSize();
        // (centred under its node, but never past the column's edges)
        l.Position = new Vector2(Mathf.Max(0, x - w.X / 2), y);
        return l;
    }

    public override void _Draw()
    {
        if (nodes.Count == 0) return;
        float y = top;
        DrawLine(new Vector2(nodes[0].X, y), new Vector2(nodes[^1].X, y), Kit.Rule.Lightened(0.15f), 1.5f, true);
        var font = Style.Display;
        foreach (var (x, lv, t, state) in nodes)
        {
            string? art = state switch { 0 => "nodes/taken.png", 1 => "nodes/next.png", _ => "nodes/later.png" };
            if (UiArt.Art(art) is { } tex) DrawTexture(tex, new Vector2(x, y) - tex.GetSize() / 2);
            else if (state == 0)
            {
                DrawCircle(new Vector2(x, y), 17, new Color("#3a3128"));
                DrawArc(new Vector2(x, y), 17, 0, Mathf.Tau, 32, new Color("#c8b48a"), 2, true);
            }
            else if (state == 1)
            {
                DrawCircle(new Vector2(x, y), 22, new Color(1, 0.45f, 0.12f, 0.12f));
                DrawCircle(new Vector2(x, y), 17, new Color("#26180f"));
                DrawArc(new Vector2(x, y), 17, 0, Mathf.Tau, 32, Style.Ember, 2.5f, true);
            }
            else DrawCircle(new Vector2(x, y), 5, new Color("#4a464c"));
            if (state == 2) continue;
            string num = $"{lv}";
            var sz = font.GetStringSize(num, HorizontalAlignment.Left, -1, 15);
            DrawString(font, new Vector2(x - sz.X / 2, y + 5.5f), num, HorizontalAlignment.Left, -1, 15, state == 1 ? Style.EmberHi : Kit.Ink);
        }
    }
}
