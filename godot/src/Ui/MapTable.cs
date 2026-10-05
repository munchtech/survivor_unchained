using System.Linq;
using Godot;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.Ui;

/// <summary>The Wayfinder's table by the east gate: today's maps, three of
/// them, each an ember arena (a place, a people, a tier and the oaths it is
/// sworn under), and the story's fights that were lost, to be taken again
/// (Maps/MapOffers.cs, Arena/Arena.cs). Drawn as what it is (docs/UI_DESIGN.md
/// 7.8): three map sheets in their wooden frames lying on the Wayfinder's
/// table, each lettered with its place and sealed with its oaths, the way in
/// at its foot.</summary>
public partial class MapTableScreen : Overlay
{
    public override string Kind => "maps";

    public MapTableScreen(Game g, string page = "nights") : base(g) { this.page = page; }

    static readonly Color Ink = new("#2e1d10"), InkSoft = new("#5a4126"), Asks = new("#8a2a18"), Gives = new("#2f5a22"), Answer = new("#4a3270");

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
        var offers = MapOffers.Today(w.Day, System.Math.Max(1, won), (int)w.Fact("map.drawn").Number);
        bool atlas = AtlasOpen;
        if (!atlas) page = "nights";
        bool again = page == "nights" && w.Rematches.Count > 0;
        AddChild(Style.Scrim(G.CloseOverlay, 0.62f));
        const float W = 1580;
        // (a sheet holds what the map pays and up to two oaths in full)
        float H = again ? 976 : 876;
        var at = new Vector2((1920 - W) / 2, (1080 - H) / 2);
        var plate = Style.Panel(Style.Plate(0));
        plate.Position = at;
        plate.Size = new Vector2(W, H);
        AddChild(plate);
        var table = new TableTop { Position = at + new Vector2(22, 92), Size = new Vector2(W - 44, H - 114) };
        AddChild(table);

        // The head: the table's name on its plaque, what the maps are, Close.
        var plaque = new Plaque(page == "atlas" ? "The Wayfinder's Atlas" : "The Wayfinder's Table", 30, 110);
        AddChild(plaque);
        plaque.Position = new Vector2((1920 - plaque.CustomMinimumSize.X) / 2, at.Y + 14);
        var sub = Style.Label(page == "atlas"
                ? "Charts to the places the road forgets. One ground each, with a ruler at its heart. You go in as you are, and what you bring out is yours."
                : $"Tonight's maps: each an ember arena, half an hour and what rules it at the end. {(won > 0 ? $"You have won tier {won}." : "You have won none yet.")} Spoils lean toward what answers the map.",
            Style.TextItalic, Style.Small, Style.InkDim, false, HorizontalAlignment.Center);
        sub.Position = at + new Vector2(0, 58);
        sub.Size = new Vector2(W, 22);
        AddChild(sub);
        var close = Nav.Skip(CloseButton("Esc", G.CloseOverlay));
        close.Position = at + new Vector2(W - 26 - close.CustomMinimumSize.X, 22);
        AddChild(close);
        if (atlas) Pages(at + new Vector2(28, 24));
        if (page == "atlas")
        {
            Atlas_(at + new Vector2(22, 92), new Vector2(W - 44, H - 114));
            if (Controls.Instance.UsingPad)
            {
                var af = Footer((Act.SubNext, "Tonight's maps"), (Act.Confirm, "Choose"), (Act.Cancel, "Close"));
                af.Position = new Vector2(0, at.Y + H + 12);
                af.Size = new Vector2(1920, 30);
                AddChild(af);
            }
            return;
        }

        // The three sheets, a little askew as they lie.
        float sheetW = 448, sheetH = 608, gap = (W - 44 - 3 * sheetW) / 4;
        float[] tilt = { -1.2f, 0.6f, -0.5f };
        for (int i = 0; i < offers.Count && i < 3; i++)
        {
            var o = offers[i];
            var pos = at + new Vector2(22 + gap + i * (sheetW + gap), 92 + 26);
            AddChild(Sheet(o, pos, new Vector2(sheetW, sheetH), tilt[i]));
            var pick = o;
            var enter = Nav.Id(Style.Button("Enter the arena", () => G.SetOut(pick), true), $"enter:{o.Spec.Name}");
            enter.CustomMinimumSize = new Vector2(240, 44);
            enter.Position = pos + new Vector2((sheetW - 240) / 2, sheetH + 22);
            AddChild(enter);
        }

        // The story's lost fights, to be taken again, on a slab along the table's foot.
        if (again)
        {
            var row = Style.H(Style.Gap4, Style.Label("FIGHTS TO TAKE AGAIN", Style.UiHeavy, Style.Caption, Style.Gold));
            foreach (var r in w.Rematches)
            {
                var spec = r;
                row.AddChild(Style.H(10, Style.V(0, Style.Label(r.Name, Style.UiBold, 17, Style.GoldHi), Style.Label(r.Sub != "" ? r.Sub : $"Tier {r.Tier}", Style.TextItalic, 14, Style.InkDim)),
                    Style.Button("Take it again", () => G.Rematch(spec), false, true)));
            }
            var slab = Style.Panel(Style.Slab(12), row);
            slab.Position = at + new Vector2(60, H - 112);
            slab.Size = new Vector2(W - 120, 72);
            AddChild(slab);
        }
        if (Controls.Instance.UsingPad)
        {
            var f = Footer((Act.Left, "Choose a map"), (Act.Confirm, "Enter the arena"), (Act.Cancel, "Close"));
            f.Position = new Vector2(0, at.Y + H + 12);
            f.Size = new Vector2(1920, 30);
            AddChild(f);
        }
    }

    /// <summary>The table's two pages as tabs at the plate's head, LT and RT at their ends.</summary>
    void Pages(Vector2 pos)
    {
        bool pad = Controls.Instance.UsingPad;
        var bar = Style.H(Style.Gap1);
        bar.MouseFilter = MouseFilterEnum.Ignore;
        bar.AddChild(pad ? Style.PadButton("LT") : Style.Key(G.Key(Act.SubPrev)));
        foreach (var (id, name) in new[] { ("nights", "Tonight's maps"), ("atlas", "The atlas") })
        {
            bool on = page == id;
            var b = Style.Button("", () => { if (!on) { page = id; Sound.Sfx.Page(); Refresh(); } }, on, true);
            var row = Style.H(Style.Gap2, Style.Label(name, Style.UiBold, Style.Small, on ? Colors.White : Style.GoldHi));
            // A point to spend lights the atlas's tab with an ember.
            if (id == "atlas" && Atlas.Unspent(G.Journey.World) > 0)
            {
                var ember = new Control { CustomMinimumSize = new Vector2(10, 20), MouseFilter = MouseFilterEnum.Ignore };
                ember.AddChild(new ColorRect { Color = Style.Ember, Size = new Vector2(7, 7), Position = new Vector2(2, 7), Rotation = Mathf.Pi / 4, PivotOffset = new Vector2(3.5f, 3.5f), MouseFilter = MouseFilterEnum.Ignore });
                row.AddChild(ember);
            }
            row.MouseFilter = MouseFilterEnum.Ignore;
            row.Position = new Vector2(12, 6);
            b.AddChild(row);
            b.CustomMinimumSize = new Vector2(row.GetCombinedMinimumSize().X + 24, 36);
            if (on) b.AddThemeStyleboxOverride("normal", UiArt.Frame("tab_on", Style.Box(new Color("#3a2614"), Style.LineHi, 1, 4)));
            else if (UiArt.Has("tab")) b.AddThemeStyleboxOverride("normal", UiArt.Frame("tab", new StyleBoxEmpty()));
            bar.AddChild(Nav.Skip(b));
        }
        bar.AddChild(pad ? Style.PadButton("RT") : Style.Key(G.Key(Act.SubNext)));
        bar.Position = pos;
        AddChild(bar);
    }

    /* -------------------------------------------------------- the atlas -- */

    /// <summary>
    /// The atlas page (docs/EXPERIENCE_AUDIT.md, "A map's shape"): three sheets on the table. The
    /// great atlas itself, the peoples by tier, each pair lit when its ruler falls; the chart in
    /// hand, its oaths read as what they ask and what they pay, and the way in; and the points
    /// the first clears gave, spent on the atlas's five biases. Made to look promising half-empty:
    /// the beta has the first tier and a point.
    /// </summary>
    void Atlas_(Vector2 pos, Vector2 size)
    {
        var w = G.Journey.World;
        float h = size.Y - 52, y = pos.Y + 26;
        float[] widths = { 520, 520, 420 };
        float gap = (size.X - widths.Sum()) / 4, x = pos.X + gap;
        float[] tilt = { -0.7f, 0.4f, -0.5f };
        var sheets = new VBoxContainer[3];
        for (int i = 0; i < 3; i++)
        {
            var (holder, inner) = Leaf(new Vector2(x, y), new Vector2(widths[i], h), tilt[i]);
            AddChild(holder);
            sheets[i] = inner;
            x += widths[i] + gap;
        }
        GreatAtlas(sheets[0], w);
        InHand(sheets[1]);
        Points(sheets[2], w);
    }

    /// <summary>A sheet of the Wayfinder's paper on the table, a little askew, its shadow under it;
    /// returns the column its words go in.</summary>
    static (Control Holder, VBoxContainer Words) Leaf(Vector2 pos, Vector2 size, float tiltDeg)
    {
        var holder = new Control { Position = pos, Size = size, PivotOffset = size / 2, RotationDegrees = tiltDeg, MouseFilter = MouseFilterEnum.Ignore };
        for (int k = 5; k >= 1; k--)
            holder.AddChild(new ColorRect { Color = new Color(0, 0, 0, 0.1f), Position = new Vector2(-k * 2 + 5, -k * 2 + 9), Size = size + new Vector2(k * 4, k * 4), MouseFilter = MouseFilterEnum.Ignore });
        var paper = Style.Panel(Style.Paper(30));
        paper.Size = size;
        paper.MouseFilter = MouseFilterEnum.Ignore;
        holder.AddChild(paper);
        var v = Style.V(8);
        v.Position = new Vector2(32, 28);
        v.Size = size - new Vector2(64, 56);
        holder.AddChild(v);
        if (UiArt.Has("map_frame"))
        {
            var rim = new Panel { Size = size, MouseFilter = MouseFilterEnum.Ignore };
            rim.AddThemeStyleboxOverride("panel", UiArt.Frame("map_frame", new StyleBoxEmpty()));
            holder.AddChild(rim);
        }
        return (holder, v);
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
        v.AddChild(new Control { SizeFlagsVertical = SizeFlags.ExpandFill, MouseFilter = MouseFilterEnum.Ignore });
        var rose = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
        rose.AddChild(Glyphs.Icon("compass", 120, InkSoft with { A = 0.2f }));
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
        v.AddChild(new Control { SizeFlagsVertical = SizeFlags.ExpandFill, MouseFilter = MouseFilterEnum.Ignore });
        // The others carried, to choose among (the highest tier first).
        if (carried.Count > 1)
        {
            v.AddChild(Ink_("OTHER CHARTS CARRIED", Style.UiHeavy, Style.Badge, InkSoft));
            var row = new HFlowContainer { MouseFilter = MouseFilterEnum.Ignore };
            row.AddThemeConstantOverride("h_separation", 6);
            row.AddThemeConstantOverride("v_separation", 6);
            foreach (var other in carried.Where(o => o != chosen).Take(6))
            {
                var uid = other.Uid;
                var b = Nav.Id(Style.Button($"{other.Chart!.Name}  ·  {other.Chart.Tier}", () => { chartUid = uid; Sound.Sfx.Page(); Refresh(); }, false, true), $"chart:{uid}");
                b.TooltipText = Charts.Title(other.Chart);
                row.AddChild(b);
            }
            v.AddChild(row);
        }
        var go = Nav.Id(Style.Button("Set it on the table", () => SetOut(chosen.Uid), true), "chart:set");
        go.CustomMinimumSize = new Vector2(0, 44);
        // Worked first, if she will (crafting's, design 20.4): ink, burn and redraw, pin, scrape, annotate.
        if (SurvivorUnchained.Rpg.Crafting.Closed(SurvivorUnchained.Rpg.Crafting.Rules.Charts.Crafter, G.Journey.Ctx) == null)
        {
            string uid = chosen.Uid;
            var work = Nav.Id(Style.Button("Work it first", () => { ForgeScreen.PutDown = uid; Sound.Sfx.Page(); G.Open($"forge:{SurvivorUnchained.Rpg.Crafting.Rules.Charts.Crafter}"); }, false), "chart:work");
            work.CustomMinimumSize = new Vector2(0, 44);
            var both = Style.H(Style.Gap2, work, go);
            go.SizeFlagsHorizontal = SizeFlags.ExpandFill;
            v.AddChild(both);
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
                var raise = Nav.Id(Style.Button(r == 0 ? "Learn it" : "Deepen it", () => { if (Atlas.Raise(w, bias)) { Sound.Sfx.Discovery(); Refresh(); } }, true, true), $"bias:{id}");
                raise.SizeFlagsHorizontal = SizeFlags.ShrinkBegin;
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
                    follow.AddChild(Nav.Id(Style.Segment(Style.Cap1(p.Name), Atlas.Road(w) == pid, () => { Atlas.Follow(w, pid); Refresh(); }), $"road:{pid}"));
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
        v.AddChild(L($"Won, a tome to write one time in {System.Math.Round(1 / SurvivorUnchained.Arena.Arenas.TableTome)}; experience and gold for every minute held.", Style.TextItalic, Style.Caption, InkSoft));
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

    /// <summary>One map: a sheet of parchment in a wooden frame, lettered by the Wayfinder.</summary>
    Control Sheet(MapOffer o, Vector2 pos, Vector2 size, float tiltDeg)
    {
        var holder = new Control { Position = pos, Size = size, PivotOffset = size / 2, RotationDegrees = tiltDeg, MouseFilter = MouseFilterEnum.Ignore };
        // Its shadow on the table.
        for (int k = 5; k >= 1; k--)
            holder.AddChild(new ColorRect { Color = new Color(0, 0, 0, 0.1f), Position = new Vector2(-k * 2 + 5, -k * 2 + 9), Size = size + new Vector2(k * 4, k * 4), MouseFilter = MouseFilterEnum.Ignore });
        var paper = Style.Panel(Style.Paper(30));
        paper.Size = size;
        paper.MouseFilter = MouseFilterEnum.Ignore;
        holder.AddChild(paper);
        // The compass the Wayfinder draws on every sheet, faint in its corner.
        var rose = Glyphs.Icon("compass", 84, InkSoft with { A = 0.22f });
        rose.Position = new Vector2(size.X - 118, size.Y - 150);
        holder.AddChild(rose);
        var people = MapOffers.People(o.People);
        Label L(string t, Font f, int sz, Color c) => Style.Label(t, f, sz, c, true, HorizontalAlignment.Left, false);
        var v = Style.V(6,
            Style.H(8, Style.Label($"TIER {o.Spec.Tier}", Style.UiHeavy, Style.Caption, InkSoft, false, HorizontalAlignment.Left, false), Style.Gems(System.Math.Min(o.Spec.Tier - 1, 5), 6)),
            L(o.Spec.Name.ToUpperInvariant(), Style.Display, 30, Ink),
            L($"Held by {people.Name}; ruled at the end by {MapOffers.InSentence(people.BossName)}", Style.TextItalic, Style.Small, Ink));
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
        v.AddChild(new Control { SizeFlagsVertical = SizeFlags.ExpandFill, MouseFilter = MouseFilterEnum.Ignore });
        v.AddChild(L("Half an hour; the ember from nothing", Style.TextItalic, Style.Caption, InkSoft));
        v.Position = new Vector2(34, 30);
        v.Size = size - new Vector2(68, 60);
        holder.AddChild(v);
        // The frame it is pinned in (frames/map_frame.png), laid over the sheet's edge.
        if (UiArt.Has("map_frame"))
        {
            var rim = new Panel { Size = size, MouseFilter = MouseFilterEnum.Ignore };
            rim.AddThemeStyleboxOverride("panel", UiArt.Frame("map_frame", new StyleBoxEmpty()));
            holder.AddChild(rim);
        }
        return holder;
    }
}

/// <summary>The Wayfinder's table top: dark oiled wood, its grain running the length, lit from above.</summary>
public partial class TableTop : Control
{
    public TableTop() { MouseFilter = MouseFilterEnum.Ignore; }

    public override void _Draw()
    {
        var s = Size;
        var top = new Color("#3a2416");
        var foot = new Color("#1c1009");
        DrawPolygon(new[] { Vector2.Zero, new Vector2(s.X, 0), s, new Vector2(0, s.Y) }, new[] { top, top, foot, foot });
        // The grain: long faint strokes, fixed so it does not shimmer.
        var rng = new RandomNumberGenerator { Seed = 7 };
        for (int i = 0; i < 140; i++)
        {
            float y = rng.Randf() * s.Y, x0 = rng.Randf() * s.X * 0.6f, len = rng.RandfRange(s.X * 0.2f, s.X * 0.7f);
            float wob = rng.RandfRange(-3, 3);
            DrawLine(new Vector2(x0, y), new Vector2(Mathf.Min(s.X, x0 + len), y + wob), new Color(0, 0, 0, rng.RandfRange(0.06f, 0.16f)), rng.RandfRange(1, 2.5f), true);
        }
        for (int i = 0; i < 40; i++)
        {
            float y = rng.Randf() * s.Y, x0 = rng.Randf() * s.X;
            DrawLine(new Vector2(x0, y), new Vector2(Mathf.Min(s.X, x0 + rng.RandfRange(80, 400)), y + rng.RandfRange(-2, 2)), new Color(1, 0.8f, 0.55f, 0.05f), 1, true);
        }
        // The lamp's light pooled in the middle, the edges falling into shadow.
        for (int k = 0; k < 10; k++)
            DrawRect(new Rect2(new Vector2(k * 6, k * 6), s - new Vector2(k * 12, k * 12)), new Color(0, 0, 0, 0.05f), false, 6);
        DrawRect(new Rect2(Vector2.Zero, s), new Color(0, 0, 0, 0.6f), false, 2);
    }
}
