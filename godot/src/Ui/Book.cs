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
/// Who the survivor has become (the web game's overlays/Sheet.tsx): level,
/// attributes to spend, traits chosen and earned, what they know, and what
/// ails them.
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

    public SheetScreen(Game g) : base(g) { }

    static int Attr(CharacterData ch, string id) => id switch { "might" => ch.Attributes.Might, "finesse" => ch.Attributes.Finesse, "wits" => ch.Attributes.Wits, _ => ch.Attributes.Resolve };

    protected override void Build()
    {
        var ch = G.Journey.Ch;
        var body = Frame(ch.Name, new Vector2(1240, 680), G.Key(Act.Character));
        var row = Style.H(28);
        body.AddChild(row);

        // Who they are.
        var left = Style.V(6);
        left.CustomMinimumSize = new Vector2(280, 0);
        left.AddChild(new Portrait(new Vector2I(260, 340)).Of(Loadouts.Of(ch)));
        left.AddChild(Style.Label($"Level {ch.Level} {Callings.Background(ch.Background).Name} {Callings.Archetype(ch.Archetype).Name}", Style.UiBold, Style.Small, Style.Ink, true));
        double need = Character.XpForLevel(ch.Level);
        // Experience in the day's cool colour, as the HUD's bar has it by day.
        left.AddChild(Bar(ch.Xp / need, $"{Math.Floor(ch.Xp)} / {need} to level {ch.Level + 1}", Style.Day));
        var ab = Abilities.ById(ch.Ability);
        var arts = Style.Button("", () => G.Open("arts"), false, true);
        var artRow = Style.H(6, Glyphs.Icon(ab.Icon, 18), Style.Label($"{ab.Name}  ·  rank {ArtBook.Rank(ch, ch.Ability)}", Style.UiBold, Style.Small, Style.GoldHi), Style.Key(G.Key(Act.Arts)));
        artRow.Position = new Vector2(8, 4);
        artRow.MouseFilter = MouseFilterEnum.Ignore;
        arts.AddChild(artRow);
        arts.CustomMinimumSize = new Vector2(260, 34);
        arts.TooltipText = "Your arts: the one in hand, its rank and facets";
        left.AddChild(arts);
        var knows = string.Join(", ", ch.Knowledge.Where(Know.ContainsKey).Select(k => Know[k]));
        left.AddChild(Style.Label($"Knows: {(knows == "" ? "little" : knows)}", Style.TextItalic, Style.Caption, Style.InkDim, true));
        row.AddChild(left);

        // Attributes and standing.
        var mid = Style.V(8);
        mid.CustomMinimumSize = new Vector2(420, 0);
        mid.AddChild(Style.H(8, Style.SubLabel("Attributes"), ch.Points > 0 ? Style.Label($"{ch.Points} to spend", Style.UiBold, Style.Caption, Style.EmberHi) : new Control()));
        foreach (var (id, name, text) in Attrs)
        {
            var r = Style.H(12);
            r.AddChild(Style.Label($"{Attr(ch, id)}", Style.Display, 26, Style.GoldHi));
            var words = Style.V(0, Style.Label(name, Style.UiBold, Style.Body, Style.Ink), Style.Label(text, Style.Ui, Style.Caption, Style.InkDim, true));
            words.SizeFlagsHorizontal = SizeFlags.ExpandFill;
            r.AddChild(words);
            if (ch.Points > 0) { var attr = id; r.AddChild(Nav.Id(Style.Button("+", () => G.Gear((j, b) => j.SpendPoint(attr, b)), true, true), $"attr:{attr}")); }
            mid.AddChild(r);
        }
        mid.AddChild(Style.Gap(8));
        mid.AddChild(Style.SubLabel("Standing"));
        mid.AddChild(InventoryScreen.Stats(ch));
        row.AddChild(mid);

        // Traits and conditions.
        var right = Style.V(8);
        right.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        right.AddChild(Style.H(8, Style.SubLabel("Traits"), ch.TraitPicks > 0 ? Style.Label($"choose {ch.TraitPicks}", Style.UiBold, Style.Caption, Style.EmberHi) : new Control()));
        if (ch.Traits.Count == 0 && ch.TraitPicks == 0) right.AddChild(Style.Label("None yet. Traits come with levels, and with what you do.", Style.TextItalic, Style.Caption, Style.InkDim, true));
        foreach (var t in ch.Traits)
        {
            var def = Callings.Trait(t);
            right.AddChild(Style.V(0, Style.Label((def?.Name ?? t) + (def?.Source == TraitSource.World ? " · earned" : ""), Style.UiBold, Style.Small, def?.Source == TraitSource.World ? Style.EmberHi : Style.GoldHi),
                Style.Label(def?.Text ?? "", Style.Ui, Style.Caption, Style.InkDim, true)));
        }
        if (ch.TraitPicks > 0)
            foreach (var t in Offer(ch))
            {
                var def = Callings.Trait(t)!;
                var b = Style.Button("", () => G.Gear((j, bt) => j.PickTrait(t, bt)));
                var inner = Style.V(0, Style.Label(def.Name, Style.UiBold, Style.Small, Style.GoldHi), Style.Label(def.Text, Style.Ui, Style.Caption, Style.Ink, true));
                inner.Position = new Vector2(12, 6);
                inner.Size = new Vector2(360, 52);
                inner.MouseFilter = MouseFilterEnum.Ignore;
                b.CustomMinimumSize = new Vector2(380, 66);
                Nav.Id(b, $"trait:{t}");
                b.AddChild(inner);
                right.AddChild(b);
            }
        if (ch.Conditions.Count > 0) { right.AddChild(Style.Gap(8)); right.AddChild(Style.SubLabel("Conditions")); }
        foreach (var c in ch.Conditions)
        {
            bool good = c.Id is ConditionId.Blessed or ConditionId.Rested or ConditionId.Warmed;
            right.AddChild(Style.H(6, Glyphs.Icon(good ? "sun" : "skull", 15, good ? Style.Good : Style.Bad), Style.Label($"{Cond.GetValueOrDefault(c.Id, c.Id.ToString())}  ·  {c.Days} day{(c.Days == 1 ? "" : "s")}", Style.UiBold, Style.Caption, good ? Style.Good : Style.Bad, true)));
        }
        row.AddChild(right);
        body.AddChild(new Control { SizeFlagsVertical = SizeFlags.ExpandFill, MouseFilter = MouseFilterEnum.Ignore });
        if (ch.Points > 0 || ch.TraitPicks > 0)
            body.AddChild(Controls.Instance.UsingPad ? Footer((Act.Confirm, ch.Points > 0 ? "Spend a point" : "Choose a trait"), (Act.TabNext, "Next page"), (Act.Cancel, "Close"))
                : MouseFooter(ch.Points > 0 ? "Click + to spend a point" : "Click a trait to take it"));
        else if (Controls.Instance.UsingPad) body.AddChild(Footer((Act.TabPrev, "Pack"), (Act.TabNext, "Arts"), (Act.Cancel, "Close")));
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
        if (a is Act.Up or Act.Down && tab != "quests" && page is { } sc && IsInstanceValid(sc))
        {
            Nav.KeyMode = true;
            sc.ScrollVertical += a == Act.Down ? 90 : -90;
            return true;
        }
        return false;
    }

    ScrollContainer? page;

    protected override void Build()
    {
        AddChild(Style.Scrim(G.CloseOverlay));
        var wrap = Style.Centered(Style.V(0), new Vector2(1240, 720));
        AddChild(wrap);
        BookTabs(new Vector2((1920 - 1240) / 2, (1080 - 720) / 2 - 46));
        // The journal's own sections: ribbons on the book's top edge, turned with LT and RT.
        var tabs = Style.H(4);
        bool pad = Controls.Instance.UsingPad;
        tabs.AddChild(pad ? Style.PadButton("LT") : Style.Key(G.Key(Act.SubPrev)));
        foreach (var (id, name) in Sections)
        {
            var b = Style.Button(name, () => { tab = id; Refresh(); }, tab == id);
            Nav.Skip(b);
            tabs.AddChild(b);
        }
        tabs.AddChild(pad ? Style.PadButton("RT") : Style.Key(G.Key(Act.SubNext)));
        var spacer = new Control { SizeFlagsHorizontal = SizeFlags.ExpandFill };
        tabs.AddChild(spacer);
        tabs.AddChild(Nav.Skip(CloseButton(G.Key(Act.Journal), G.CloseOverlay)));
        wrap.AddChild(tabs);
        var book = Style.Panel(Style.Paper(26));
        book.SizeFlagsVertical = SizeFlags.ExpandFill;
        wrap.AddChild(book);
        page = null;
        book.AddChild(tab switch { "people" => People(), "deeds" => Deeds(), "codex" => Codex(), _ => Quests() });
    }

    // Reading text on paper: body size, the ink of a hand that wrote it.
    static Label P(string text, int size = Style.Body, Font? font = null, Color? color = null) => Style.Label(text, font ?? Style.Text, size, color ?? Ink, true, HorizontalAlignment.Left, false);
    static Label H2(string text) => Style.Label(text, Style.Display, Style.Title, new Color("#3a2414"), true, HorizontalAlignment.Left, false);

    HBoxContainer Two(Control a, Control b)
    {
        var h = Style.H(30);
        a.SizeFlagsHorizontal = b.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        page = Style.Scroll(a);
        h.AddChild(page);
        h.AddChild(Style.Scroll(b));
        return h;
    }

    Control Quests()
    {
        var w = G.Journey.World;
        var list = w.Quests.Values.Where(q => q.Status != QuestStatus.Unknown && Lore.Quests.ContainsKey(q.Id)).ToList();
        quest ??= list.FirstOrDefault(q => q.Status == QuestStatus.Active)?.Id ?? list.FirstOrDefault()?.Id;
        var side = Style.V(4);
        side.CustomMinimumSize = new Vector2(300, 0);
        foreach (var (st, label) in new[] { (QuestStatus.Active, "Under way"), (QuestStatus.Resolved, "Done"), (QuestStatus.Failed, "Lost") })
        {
            var qs = list.Where(x => st == QuestStatus.Failed ? x.Status is QuestStatus.Failed or QuestStatus.Abandoned : x.Status == st).ToList();
            if (qs.Count == 0) continue;
            side.AddChild(Style.Label(label.ToUpperInvariant(), Style.UiHeavy, Style.Badge, InkSoft, false, HorizontalAlignment.Left, false));
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
        var h = Style.H(30);
        h.AddChild(Style.Scroll(side));
        side.SizeFlagsHorizontal = SizeFlags.Fill;
        h.GetChild<ScrollContainer>(0).CustomMinimumSize = new Vector2(310, 0);
        h.GetChild<ScrollContainer>(0).SizeFlagsHorizontal = SizeFlags.Fill;
        h.AddChild(Style.Scroll(page));
        return h;
    }

    static Control Feel(double v)
    {
        var p = new Control { CustomMinimumSize = new Vector2(120, 12), MouseFilter = MouseFilterEnum.Ignore };
        p.AddChild(new ColorRect { Color = new Color(0.35f, 0.25f, 0.12f, 0.35f), Position = new Vector2(0, 5), Size = new Vector2(120, 2) });
        p.AddChild(new ColorRect { Color = new Color(0.35f, 0.25f, 0.12f, 0.6f), Position = new Vector2(59, 2), Size = new Vector2(2, 8) });
        p.AddChild(new ColorRect { Color = v >= 0 ? new Color("#3a6a2a") : new Color("#8a2a1a"), Position = new Vector2((float)((v + 100) / 200 * 116), 1), Size = new Vector2(6, 10) });
        return p;
    }

    Control People()
    {
        var w = G.Journey.World;
        var ctx = G.Journey.Ctx;
        var met = Lore.Npcs.Values.Where(d => w.Npcs.TryGetValue(d.Id, out var s) && s.Flags.TryGetValue("met", out var m) && m.Truthy).ToList();
        var grid = new GridContainer { Columns = 2 };
        grid.AddThemeConstantOverride("h_separation", 34);
        grid.AddThemeConstantOverride("v_separation", 18);
        if (met.Count == 0) return Style.V(0, P("You have not met anyone yet. Those you speak with are written here, and how they feel about you.", Style.Body, Style.TextItalic, InkSoft));
        foreach (var d in met)
        {
            var s = w.Npcs[d.Id];
            var v = Style.V(3);
            v.CustomMinimumSize = new Vector2(540, 0);
            v.AddChild(Style.H(10, Style.Label(d.Name, Style.Display, 20, new Color("#3a2414"), false, HorizontalAlignment.Left, false),
                P(d.Role + (s.Alive ? "" : " · dead"), Style.Caption, Style.TextItalic, InkSoft), P(Rules.Attitude(s), Style.Caption, Style.TextBold, Red)));
            if (s.Alive && Lore.ConcernOf(d.Id, ctx) is string mind) v.AddChild(P(mind, Style.Small, Style.TextItalic));
            var axes = new GridContainer { Columns = 4 };
            axes.AddThemeConstantOverride("h_separation", 10);
            foreach (var (label, val) in new[] { ("Trust", s.Trust), ("Warmth", s.Affection), ("Respect", s.Respect), ("Fear", s.Fear) })
            {
                axes.AddChild(P(label, Style.Caption, Style.Ui, InkSoft));
                axes.AddChild(Feel(val));
            }
            v.AddChild(axes);
            var heard = s.Memories.Select(m => w.History.FirstOrDefault(h => h.Id == m)).Where(h => h != null).Select(h => h!.Text).ToList();
            if (heard.Count > 0) v.AddChild(P($"Knows that you {string.Join("; ", heard)}.", Style.Caption, Style.Text, InkSoft));
            grid.AddChild(v);
        }
        page = Style.Scroll(grid);
        return page;
    }

    Control Deeds()
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
        return Two(left, right);
    }

    Control Codex()
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
        var right = Style.V(8, H2("Discoveries"));
        foreach (var d in Discoveries.All)
        {
            bool found = w.Codex.Contains(d.Id);
            right.AddChild(Style.V(1, P(found ? d.Name : "Not yet found", Style.Body, Style.TextBold, found ? Ink : InkSoft), P(found ? d.Description : d.Hint, Style.Caption, Style.TextItalic, InkSoft)));
        }
        return Two(left, right);
    }
}
