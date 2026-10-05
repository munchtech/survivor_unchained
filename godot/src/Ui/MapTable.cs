using System;
using System.Linq;
using Godot;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.Ui;

/// <summary>The Wayfinder's table by the east gate: today's maps, three of them, each an ember arena
/// (a place, a people, a tier and the oaths it is sworn under), and the story's fights that were
/// lost, to be taken again (Maps/MapOffers.cs, Arena/Arena.cs). One fitted panel over the world
/// (it was an iron plate with the HUD showing round it): its title between the chains, the
/// table's two pages as tabs, and on it the Wayfinder's sheets of parchment lying a little askew,
/// as tall as their words (the atlas's last line was clipped under a fixed sheet). What is done
/// on a sheet is written on it, in the Wayfinder's ink, not pressed as a button.</summary>
public partial class MapTableScreen : Overlay
{
    public override string Kind => "maps";

    public MapTableScreen(Game g, string page = "nights") : base(g) { this.page = page; }

    static readonly Color Ink = new("#2e1d10"), InkSoft = new("#5a4126"), Asks = new("#8a2a18"), Gives = new("#2f5a22"), Answer = new("#4a3270");
    /// <summary>The ink of what is done on a sheet: a deep red, darker when the pointer is on it.</summary>
    static readonly Color Act_ = new("#7a1c10");

    /// <summary>Which of the table's two pages is open: tonight's maps (the nights), or the atlas
    /// (the charts and the places the road forgets), once the atlas is open.</summary>
    string page = "nights";
    string? chartUid;

    bool AtlasOpen => Atlas.IsOpen(G.Journey.World, G.Journey.Ch);

    public override bool Key(Act a)
    {
        // The table's two pages turn with LT and RT, as a screen's own pages do.
        if (a is Act.SubNext or Act.SubPrev && AtlasOpen)
        {
            page = page == "atlas" ? "nights" : "atlas";
            Sound.Sfx.Page();
            Refresh();
            return true;
        }
        return false;
    }

    protected override void Build()
    {
        var w = G.Journey.World;
        int won = (int)w.Fact("arena.best").Number;
        var offers = MapOffers.Today(w.Day, Math.Max(1, won), (int)w.Fact("map.drawn").Number);
        bool atlas = AtlasOpen;
        if (!atlas) page = "nights";
        HideHud();
        AddChild(Style.Scrim(G.CloseOverlay, 0.35f));
        var centre = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
        Style.Fill(centre);
        AddChild(centre);
        var panel = Style.Panel(Kit.Window(Margin + 6, Margin, Margin));
        panel.SelfModulate = Colors.White with { A = GroundAlpha };
        panel.MouseFilter = MouseFilterEnum.Stop;
        centre.AddChild(panel);
        var v = Style.V(Style.Gap4);
        panel.AddChild(v);

        // The head: the title between the chains on the panel's axis, Close in its corner.
        var title = new Title(page == "atlas" ? "The Wayfinder's Atlas" : "The Wayfinder's Table", 30);
        var head = new Control { CustomMinimumSize = new Vector2(0, title.CustomMinimumSize.Y), MouseFilter = MouseFilterEnum.Ignore };
        title.SetAnchorsPreset(LayoutPreset.FullRect);
        head.AddChild(title);
        var close = Nav.Skip(CloseButton("Esc", G.CloseOverlay));
        head.AddChild(close);
        close.Size = close.CustomMinimumSize;
        close.SetAnchorsAndOffsetsPreset(LayoutPreset.CenterRight, LayoutPresetMode.KeepSize);
        v.AddChild(head);
        if (atlas)
        {
            var tabs = Kit.Tabs(new[] { "Tonight's maps", "The atlas" }, page == "atlas" ? 1 : 0, k => { page = k == 1 ? "atlas" : "nights"; Refresh(); }, 16, 28,
                new[] { "", Atlas.Unspent(w) > 0 ? $"{Atlas.Unspent(w)} to spend" : "" });
            tabs.Alignment = BoxContainer.AlignmentMode.Center;
            v.AddChild(tabs);
        }
        v.AddChild(Style.Label(page == "atlas"
                ? "Charts to the places the road forgets. One ground each, with a ruler at its heart. You go in as you are, and what you bring out is yours."
                : $"Tonight's maps: each an ember arena, half an hour and what rules it at the end. {(won > 0 ? $"You have won tier {won}." : "You have won none yet.")} Spoils lean toward what answers the map.",
            Style.TextItalic, 16, Kit.Dim, true, HorizontalAlignment.Center));

        if (page == "atlas") { Atlas_(v); Foot(); return; }

        // The three sheets, a little askew as they lie, as tall as the tallest one's words.
        var row = Style.H(30);
        row.Alignment = BoxContainer.AlignmentMode.Center;
        float[] tilt = { -1.0f, 0.6f, -0.5f };
        for (int i = 0; i < offers.Count && i < 3; i++) row.AddChild(Sheet(offers[i], 452, tilt[i]));
        v.AddChild(row);

        // The story's lost fights, to be taken again, as a line under the sheets.
        if (w.Rematches.Count > 0)
        {
            v.AddChild(Kit.Head("Fights to take again"));
            var again = Style.H(36);
            foreach (var r in w.Rematches)
            {
                var spec = r;
                var line = Style.H(14, Style.V(0, Style.Label(r.Name, Style.UiBold, 17, Kit.Ink), Style.Label(r.Sub != "" ? r.Sub : $"Tier {r.Tier}", Style.TextItalic, 14, Kit.Dim)),
                    Nav.Id(Kit.Word("Take it again", () => G.Rematch(spec), Style.EmberHi, 16), $"again:{r.Name}"));
                again.AddChild(line);
            }
            v.AddChild(again);
        }
        Foot();
    }

    /// <summary>The prompts under the panel, on the world.</summary>
    void Foot()
    {
        bool pad = Controls.Instance.UsingPad;
        PromptsOnWorld(pad
            ? Kit.Prompts(Kit.Prompt(Act.Left, "Choose"), Kit.Prompt(Act.Confirm, page == "atlas" ? "Choose" : "Enter the arena"), AtlasOpen ? Kit.Prompt(Act.SubNext, page == "atlas" ? "Tonight's maps" : "The atlas") : new Control(), Kit.Prompt(Act.Cancel, "Close"))
            : Kit.Prompts(Kit.Prompt("Click", page == "atlas" ? "Choose" : "Enter the arena"), Kit.Prompt("Esc", "Close")));
    }

    /// <summary>What is done on a sheet, written on it in the Wayfinder's red ink, darker under the pointer.</summary>
    static Button InkWord(string text, Action act, int size = 19)
    {
        var b = new Button { Text = text, FocusMode = FocusModeEnum.None, MouseDefaultCursorShape = CursorShape.PointingHand, Flat = true, Alignment = HorizontalAlignment.Left };
        Style.Font(b, Style.DisplayLight, size, Act_, false);
        b.AddThemeColorOverride("font_hover_color", new Color("#3a0a04"));
        b.AddThemeColorOverride("font_pressed_color", new Color("#3a0a04"));
        foreach (var s in new[] { "normal", "hover", "pressed", "focus" })
            b.AddThemeStyleboxOverride(s, new StyleBoxEmpty { ContentMarginLeft = 0, ContentMarginRight = 0, ContentMarginTop = 0, ContentMarginBottom = 2 });
        var under = new StyleBoxFlat { BgColor = Colors.Transparent, BorderColor = Act_, BorderWidthBottom = 1, ContentMarginBottom = 2 };
        b.AddThemeStyleboxOverride("hover", under);
        b.Pressed += act;
        b.SizeFlagsHorizontal = SizeFlags.ShrinkBegin;
        return b;
    }

    /* -------------------------------------------------------- the atlas -- */

    /// <summary>
    /// The atlas page (docs/EXPERIENCE_AUDIT.md, "A map's shape"): three sheets on the table. The
    /// great atlas itself, the peoples by tier, each pair lit when its ruler falls; the chart in
    /// hand, its oaths read as what they ask and what they pay, and the way in; and the points
    /// the first clears gave, spent on the atlas's five biases. Made to look promising half-empty.
    /// </summary>
    void Atlas_(VBoxContainer page)
    {
        var w = G.Journey.World;
        var row = Style.H(30);
        row.Alignment = BoxContainer.AlignmentMode.Center;
        var (a, av) = Leaf(500, -0.6f);
        var (b, bv) = Leaf(500, 0.4f);
        var (c, cv) = Leaf(430, -0.5f);
        GreatAtlas(av, w);
        InHand(bv);
        Points(cv, w);
        row.AddChild(a);
        row.AddChild(b);
        row.AddChild(c);
        page.AddChild(row);
    }

    /// <summary>A sheet of the Wayfinder's paper on the table, a little askew, its shadow under it, as
    /// tall as the tallest sheet beside it; returns it and the column its words go in.</summary>
    static (Control Sheet, VBoxContainer Words) Leaf(float width, float tiltDeg)
    {
        var paper = Style.Panel(Style.Paper(30));
        paper.CustomMinimumSize = new Vector2(width, 0);
        // (each as tall as its own words: sheets lying on a table, not a row of equal boxes)
        paper.SizeFlagsVertical = SizeFlags.ShrinkBegin;
        paper.MouseFilter = MouseFilterEnum.Ignore;
        paper.RotationDegrees = tiltDeg;
        paper.Resized += () => paper.PivotOffset = paper.Size / 2;
        // Its shadow on the table, under it.
        var shadow = new Shadow { ShowBehindParent = true };
        paper.AddChild(shadow);
        var v = Style.V(8);
        paper.AddChild(v);
        return (paper, v);
    }

    /// <summary>A sheet's shadow, soft, a little down and to the right of it.</summary>
    partial class Shadow : Control
    {
        public Shadow() { MouseFilter = MouseFilterEnum.Ignore; TopLevel = false; }

        public override void _Draw()
        {
            // (drawn from the sheet's own corner: the sheet lays this out inside its margins)
            var s = GetParent<Control>().Size;
            for (int k = 5; k >= 1; k--)
                DrawRect(new Rect2(new Vector2(-k * 2 + 5, -k * 2 + 9) - Position, s + new Vector2(k * 4, k * 4)), new Color(0, 0, 0, 0.09f));
        }

        public override void _Process(double delta) => QueueRedraw();
    }

    static Label Ink_(string t, Font f, int size, Color? c = null, HorizontalAlignment align = HorizontalAlignment.Left) =>
        Style.Label(t, f, size, c ?? Ink, true, align, false);

    static Control Head(string kicker, string title) =>
        Style.V(2, Ink_(kicker.ToUpperInvariant(), Style.UiHeavy, Style.Badge, InkSoft), Ink_(title, Style.Display, 26));

    /// <summary>The great atlas: each people's ground at each tier, lit where its ruler fell.</summary>
    static void GreatAtlas(VBoxContainer v, SurvivorUnchained.World.WorldState w)
    {
        v.AddChild(Head("The great atlas", "The Places the Road Forgets"));
        v.AddChild(Ink_("Each people's ground, tier by tier. A ground is lit where its ruler has fallen, and the first fall there is a point to spend.", Style.TextItalic, Style.Small, InkSoft));
        v.AddChild(Style.Gap(Style.Gap2));
        var grid = MapResultScreen.AtlasGrid(w, null, true);
        grid.SizeFlagsHorizontal = SizeFlags.ShrinkCenter;
        v.AddChild(grid);
        v.AddChild(Style.Gap(Style.Gap2));
        int lit = MapOffers.Peoples.Sum(p => Enumerable.Range(1, 16).Count(t => Atlas.Done(w, p.Id, t)));
        int best = Atlas.Best(w), cleared = (int)w.Fact("atlas.cleared").Number;
        v.AddChild(Ink_(lit == 0 ? "Nothing is lit yet. Every people waits at the first tier." : $"{lit} lit  ·  the highest tier cleared: {best}  ·  {cleared} map{(cleared == 1 ? "" : "s")} cleared",
            Style.UiBold, Style.Small, Ink, HorizontalAlignment.Center));
        // What comes next, so the dark half reads as a road, not a lack.
        v.AddChild(Ink_("The next tier opens with the chart a ruler leaves: the first fall of each people at a tier always leaves one.",
            Style.TextItalic, Style.Caption, InkSoft, HorizontalAlignment.Center));
        var rose = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
        rose.AddChild(Glyphs.Icon("compass", 72, InkSoft with { A = 0.2f }));
        v.AddChild(rose);
    }

    /// <summary>The chart in hand: those carried, the one chosen read out (what each oath asks and
    /// pays), and the way in.</summary>
    void InHand(VBoxContainer v)
    {
        var carried = Charts.Carried(G.Journey.Ch);
        var chosen = carried.FirstOrDefault(c => c.Uid == chartUid) ?? carried.FirstOrDefault();
        v.AddChild(Head("The chart in hand", chosen?.Chart?.Name ?? "No chart"));
        if (chosen?.Chart is not { } c)
        {
            v.AddChild(Ink_("A map's ruler leaves the next chart when it falls, and now and then its keepers or its strongbox leave another.", Style.TextItalic, Style.Small, InkSoft));
            return;
        }
        var people = MapOffers.People(c.People);
        string fineness = c.Rarity switch { 2 => "A rare chart", 1 => "A fine chart", _ => "A plain chart" };
        v.AddChild(Ink_($"{fineness}, tier {c.Tier}: held by {people.Name}, ruled at its heart by {MapOffers.InSentence(people.BossName)}.", Style.TextItalic, Style.Small, Ink));
        var spec = c.Map;
        // (one fall ends a map unless she carries the rise, the owner's rule; more allowed, it says how many)
        int allowed = SurvivorUnchained.Play.Zones.MapRun.FallsAllowed;
        var falls = allowed > 1 ? $"{allowed} falls and it closes." : "Fall, and it closes, unless you carry Not Yet.";
        v.AddChild(Ink_($"Its ground: {spec.Clearings} clearings and {spec.AltarCount} altar{(spec.AltarCount == 1 ? "" : "s")} on a winding way. {falls}", Style.Text, Style.Caption, InkSoft));
        v.AddChild(Style.Rule());
        // What it is sworn under: prefixes ask more of the foe's side, suffixes of yours. Each pays.
        var pre = c.Rolled.Where(m => m.Prefix).ToList();
        var suf = c.Rolled.Where(m => !m.Prefix).ToList();
        if (pre.Count + suf.Count == 0) v.AddChild(Ink_("Sworn under nothing: plain ground, plain pay.", Style.TextItalic, Style.Small, InkSoft));
        if (pre.Count > 0) { v.AddChild(Ink_("SWORN FOR THE FOE", Style.UiHeavy, Style.Badge, Asks)); foreach (var m in pre) v.AddChild(Oath(m)); }
        if (suf.Count > 0) { v.AddChild(Ink_("SWORN AGAINST YOU", Style.UiHeavy, Style.Badge, Asks)); foreach (var m in suf) v.AddChild(Oath(m)); }
        if (pre.Count + suf.Count > 0)
            v.AddChild(Ink_($"In all it pays {Pct(c.Quantity - 1)} more found, {Pct(c.RarityBonus - 1)} finer, and packs {Pct(c.PackSize - 1)} larger.", Style.TextBold, Style.Small, Gives));
        // The others carried, to choose among (the highest tier first).
        if (carried.Count > 1)
        {
            v.AddChild(Ink_("OTHER CHARTS CARRIED", Style.UiHeavy, Style.Badge, InkSoft));
            var row = new HFlowContainer { MouseFilter = MouseFilterEnum.Ignore };
            row.AddThemeConstantOverride("h_separation", 18);
            row.AddThemeConstantOverride("v_separation", 4);
            foreach (var other in carried.Where(o => o != chosen).Take(6))
            {
                var uid = other.Uid;
                var b = Nav.Id(InkWord($"{other.Chart!.Name}, tier {other.Chart.Tier}", () => { chartUid = uid; Sound.Sfx.Page(); Refresh(); }, 15), $"chart:{uid}");
                b.TooltipText = Charts.Title(other.Chart);
                row.AddChild(b);
            }
            v.AddChild(row);
        }
        var go = Nav.Id(InkWord("Set it on the table", () => SetOut(chosen.Uid), 21), "chart:set");
        // Worked first, if she will (crafting's, design 20.4): ink, burn and redraw, pin, scrape, annotate.
        if (SurvivorUnchained.Rpg.Crafting.Closed(SurvivorUnchained.Rpg.Crafting.Rules.Charts.Crafter, G.Journey.Ctx) == null)
        {
            string uid = chosen.Uid;
            var work = Nav.Id(InkWord("Work it first", () => { ForgeScreen.PutDown = uid; Sound.Sfx.Page(); G.Open($"forge:{SurvivorUnchained.Rpg.Crafting.Rules.Charts.Crafter}"); }, 19), "chart:work");
            work.AddThemeColorOverride("font_color", InkSoft);
            v.AddChild(Style.H(28, go, work));
        }
        else v.AddChild(go);
        v.AddChild(Ink_("The chart is used up as its map opens.", Style.TextItalic, Style.Caption, InkSoft, HorizontalAlignment.Center));
    }

    static string Pct(double x) => $"{System.Math.Round(x * 100)}%";

    /// <summary>One oath of a chart, sealed in wax beside its terms: what it asks, what it pays.</summary>
    static Control Oath(ChartMod m)
    {
        var seal = new Panel { CustomMinimumSize = new Vector2(22, 22), MouseFilter = MouseFilterEnum.Ignore, SizeFlagsVertical = SizeFlags.ShrinkBegin };
        var wax = Style.Box(m.Prefix ? new Color("#8a1c14") : new Color("#3a2a5a"), m.Prefix ? new Color("#5a0e0a") : new Color("#221636"), 2, 11, 0);
        wax.ShadowColor = new Color(0, 0, 0, 0.35f); wax.ShadowSize = 3; wax.ShadowOffset = new Vector2(1, 2);
        seal.AddThemeStyleboxOverride("panel", wax);
        var pays = new System.Collections.Generic.List<string>();
        if (m.Quantity > 0) pays.Add($"{Pct(m.Quantity)} more found");
        if (m.Rarity > 0) pays.Add($"{Pct(m.Rarity)} finer");
        if (m.PackSize > 0) pays.Add($"packs {Pct(m.PackSize)} larger");
        var terms = Style.V(0, Ink_(m.Name, Style.TextBold, Style.Small), Ink_(m.Says, Style.Text, Style.Caption, Asks), Ink_($"Pays {string.Join(", ", pays)}", Style.Text, Style.Caption, Gives));
        terms.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        return Style.H(10, seal, terms);
    }

    void SetOut(string uid)
    {
        if (Charts.TakeOut(G.Journey.Ch, uid) is not { } chart) return;
        Sound.Sfx.Page();
        G.EnterMap(chart);
    }

    /// <summary>The points the first clears gave, and the five biases they buy, three ranks each.</summary>
    void Points(VBoxContainer v, SurvivorUnchained.World.WorldState w)
    {
        int unspent = Atlas.Unspent(w), points = Atlas.Points(w);
        v.AddChild(Head("The Wayfinder's margins", unspent > 0 ? $"{unspent} point{(unspent == 1 ? "" : "s")} to spend" : points > 0 ? "Every point spent" : "No points yet"));
        v.AddChild(Ink_("Each people's first fall at each tier is a point. Spent here, it bends what the maps give.", Style.TextItalic, Style.Caption, InkSoft));
        foreach (var (id, name, rank) in Atlas.Biases)
        {
            int r = Atlas.Rank(w, id);
            var pips = Style.H(3);
            for (int k = 0; k < Atlas.MaxRank; k++) pips.AddChild(new AtlasStone(k < r, false, true) { CustomMinimumSize = new Vector2(20, 20) });
            var top = Style.H(8, Ink_(name, Style.TextBold, Style.Small), new Control { SizeFlagsHorizontal = SizeFlags.ExpandFill, MouseFilter = MouseFilterEnum.Ignore }, pips);
            var block = Style.V(1, top, Ink_(rank, Style.Text, Style.Caption, InkSoft));
            if (unspent > 0 && r < Atlas.MaxRank)
            {
                var bias = id;
                var raise = Nav.Id(InkWord(r == 0 ? "Learn it" : "Deepen it", () => { if (Atlas.Raise(w, bias)) { Sound.Sfx.Discovery(); Refresh(); } }, 17), $"bias:{id}");
                block.AddChild(raise);
            }
            // The people's road needs a people to follow.
            if (id == Atlas.PeoplesRoad && r > 0)
            {
                var follow = new HFlowContainer { MouseFilter = MouseFilterEnum.Ignore };
                follow.AddThemeConstantOverride("h_separation", 4);
                foreach (var p in MapOffers.Peoples)
                {
                    var pid = p.Id;
                    var word = InkWord(Style.Cap1(p.Name), () => { Atlas.Follow(w, pid); Refresh(); }, 15);
                    // (the people followed is in full ink, the rest faint)
                    if (Atlas.Road(w) != pid) word.AddThemeColorOverride("font_color", InkSoft with { A = 0.7f });
                    follow.AddChild(Nav.Id(word, $"road:{pid}"));
                }
                block.AddChild(follow);
            }
            v.AddChild(block);
        }
    }

    /// <summary>What answers a people, as gear is named: "Wolfbane gear, or gear of the Wolf"
    /// (a prefix goes before "gear", a suffix after it).</summary>
    /// <summary>What a map pays, in the Wayfinder's hand: the things a night among that people leaves
    /// in the fist, drawn (ember shards, the people's own); the gear its spoils lean to, which is
    /// what answers them; and on a win, a tome one time in three.</summary>
    static Control Pays(MapOffer o, Denizens people)
    {
        Label L(string t, Font f, int sz, Color c) => Style.Label(t, f, sz, c, true, HorizontalAlignment.Left, false);
        var v = Style.V(4, Style.Label("WHAT IT PAYS", Style.UiHeavy, Style.Badge, InkSoft, false, HorizontalAlignment.Left, false));
        var things = Style.H(6);
        foreach (var m in SurvivorUnchained.Rpg.Crafting.NightMaterials(o.People).Take(4))
        {
            var def = SurvivorUnchained.Rpg.Items.Get(m);
            var cell = Style.V(0, ItemPhotos.Icon(def.Icon, 44, InkSoft), Style.Label(def.Plural ?? def.Name.ToLowerInvariant(), Style.Ui, 12, Ink, true, HorizontalAlignment.Center, false));
            cell.CustomMinimumSize = new Vector2(76, 0);
            cell.TooltipText = def.Description;
            things.AddChild(cell);
        }
        v.AddChild(things);
        // (the gear in a line: the names only, three at most; the bane in full is in the sub-title's words)
        var lean = MapOffers.Lean(o.Spec, o.People).Select(a => SurvivorUnchained.Rpg.Items.Affix(a)?.Name ?? a).Distinct().Take(3);
        v.AddChild(L($"Gear leaning to {string.Join(", ", lean)}", Style.TextItalic, Style.Caption, Answer));
        v.AddChild(L(Kit.Balance($"Won, a tome to write one time in {System.Math.Round(1 / SurvivorUnchained.Arena.Arenas.TableTome)}; experience and gold for every minute held.", Style.TextItalic, Style.Caption, 380), Style.TextItalic, Style.Caption, InkSoft));
        return v;
    }

    static string Bane(string[] lean)
    {
        var names = lean.Select(a => SurvivorUnchained.Rpg.Items.Affix(a)?.Name ?? a).ToList();
        var before = names.Where(n => !n.StartsWith("of ")).ToList();
        var parts = new System.Collections.Generic.List<string>();
        if (before.Count > 0) parts.Add(string.Join(" or ", before) + " gear");
        parts.AddRange(names.Where(n => n.StartsWith("of ")).Select(n => "gear " + n));
        return string.Join(", or ", parts);
    }


    /// <summary>One map: a sheet of parchment lettered by the Wayfinder, a little askew on the table,
    /// the way in written at its foot.</summary>
    Control Sheet(MapOffer o, float width, float tiltDeg)
    {
        var (sheet, v) = Leaf(width, tiltDeg);
        var people = MapOffers.People(o.People);
        Label L(string t, Font f, int sz, Color c) => Style.Label(t, f, sz, c, true, HorizontalAlignment.Left, false);
        v.AddChild(L($"TIER {o.Spec.Tier}", Style.UiHeavy, Style.Caption, InkSoft));
        v.AddChild(L(o.Spec.Name.ToUpperInvariant(), Style.Display, 30, Ink));
        v.AddChild(L($"Held by {people.Name}; ruled at the end by {MapOffers.InSentence(people.BossName)}", Style.TextItalic, Style.Small, Ink));
        // What it pays, before what it asks (the experience director's finding: the table said
        // nothing of it): what the night leaves in the fist, drawn; the gear it leans to; a tome's chance.
        v.AddChild(Pays(o, people));
        v.AddChild(Style.Rule());
        if (o.Spec.Oaths.Count == 0) v.AddChild(L("Sworn under no oath.", Style.TextItalic, Style.Small, InkSoft));
        foreach (var id in o.Spec.Oaths)
        {
            var oath = MapOffers.Oath(id);
            // Each oath sealed in wax beside its terms.
            var seal = new Panel { CustomMinimumSize = new Vector2(26, 26), MouseFilter = MouseFilterEnum.Ignore, SizeFlagsVertical = SizeFlags.ShrinkBegin };
            var wax = Style.Box(new Color("#8a1c14"), new Color("#5a0e0a"), 2, 13, 0);
            wax.ShadowColor = new Color(0, 0, 0, 0.35f); wax.ShadowSize = 3; wax.ShadowOffset = new Vector2(1, 2);
            seal.AddThemeStyleboxOverride("panel", wax);
            var terms = Style.V(1,
                L(oath.Name, Style.TextBold, Style.Small, Ink),
                L($"Asks: {oath.Asks}", Style.Text, Style.Caption, Asks),
                L($"Gives: {oath.Gives}", Style.Text, Style.Caption, Gives),
                L($"Answered by {oath.Answer}", Style.TextItalic, Style.Caption, Answer));
            terms.SizeFlagsHorizontal = SizeFlags.ExpandFill;
            v.AddChild(Style.H(10, seal, terms));
        }
        v.AddChild(Style.Gap(4));
        v.AddChild(L("Half an hour; the ember from nothing", Style.TextItalic, Style.Caption, InkSoft));
        var pick = o;
        v.AddChild(Nav.Id(InkWord("Enter the arena", () => G.SetOut(pick), 21), $"enter:{o.Spec.Name}"));
        return sheet;
    }
}
