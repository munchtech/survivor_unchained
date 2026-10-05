using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Play;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Rpg;

namespace SurvivorUnchained.Ui;

/// <summary>
/// A Wayfinder's map over (Play/Zones/MapRun.cs), on its own page, of the night's result's
/// family but told for the build, not the hum (docs/EXPERIENCE_AUDIT.md, "A map's shape"): the
/// verdict and the chart it was; the time, the falls, the slain and the ground taken counting
/// up; then loot first, a find at a time, the best first (gear by rarity, the charts won, what
/// was carried out, the gold); and the atlas's line, the mark the map left on it.
/// </summary>
public partial class MapResultScreen : TellingScreen
{
    readonly MapResult r;
    readonly MapSpoils spoils;
    public override string Kind => "mapresult";
    public override bool Dismissable => false;

    /// <summary>A find laid out large: the cell's width, its tile, and how many to a row.</summary>
    const int Cell = 172, Big = 84, PerRow = 6;

    public MapResultScreen(Game g, MapResult result, MapSpoils spoils) : base(g) { r = result; this.spoils = spoils; }

    /// <summary>The best first: a Storied or Legendary piece, a set's, an Epic, a chart or a ruler's
    /// marked thing; then the rest by tier.</summary>
    static int Rank(ItemInstance it) => Drops.TierOf(it) switch
    {
        LootTier.Storied => 9, LootTier.Legendary => 8, LootTier.Set => 7, LootTier.Epic => 6, LootTier.Book or LootTier.Chart or LootTier.Quest => 5,
        LootTier.Rare => 3, LootTier.Uncommon => 2, LootTier.Common => 1, _ => 0,
    };

    /// <summary>
    /// One panel over the world, fitted and centred, told down the page in registers rather than
    /// two columns (the experience director: the finds were 40 px tiles over a half-empty column):
    /// the verdict between the chains and the chart under it; the map's numbers as a ledger line;
    /// then what came out, laid out large as the best lay out a reward (D4, PoE2), each find named in
    /// its tier's colour and the best first, with what was carried out and the gold as one line under
    /// them; then the atlas across the panel. No column can run short. The way back is there from the
    /// first moment, and the telling is done in under six seconds.
    /// </summary>
    protected override void Build()
    {
        Retell();
        var people = MapOffers.People(r.Chart.People);
        var sworn = r.Chart.Rolled.Select(m => m.Name).ToList();
        var v = ResultPanel(r.Cleared ? "The map is cleared" : "The map closes", r.Cleared ? new Color("#ffe6b8") : Style.BloodHi,
            $"{r.Chart.Name}  ·  tier {r.Chart.Tier}, held by {people.Name}{(sworn.Count > 0 ? "  ·  " + string.Join(", ", sworn) : "")}");

        // Beat one: the map's numbers, counting up in turn.
        var stats = new List<(double, Func<double, string>, string, double, bool)> { (r.Seconds, Clock, r.Cleared ? "cleared in" : "held out", 0.3, r.Cleared) };
        double at = 0.55;
        // Falls are counted where a map allows more than one, or where she rose again and cleared it.
        if (MapRun.FallsAllowed > 1 || r.Falls > 0 && r.Cleared)
        {
            stats.Add((r.Falls, x => MapRun.FallsAllowed > 1 ? $"{x:0}/{MapRun.FallsAllowed}" : $"{x:0}", MapRun.FallsAllowed > 1 ? "falls" : "rose again", at, r.Falls < MapRun.FallsAllowed));
            at += 0.25;
        }
        stats.Add((r.Kills, x => $"{x:N0}", "slain", at, r.Cleared));
        stats.Add((r.PacksCleared, x => $"{x:0}/{r.Packs}", "packs broken", at + 0.25, r.Cleared));
        v.AddChild(Tally(stats.ToArray()));
        double cue = at + 0.25 + Count;

        // Beat two: what came out, the best first, a chart among them (it is the next map in hand).
        var finds = spoils.Gear.Concat(spoils.Charts).OrderByDescending(Rank).ThenByDescending(Drops.LevelOf).ToList();
        Register(v, "What came out", Counted(spoils.Gear.Count, spoils.Charts.Count));
        if (finds.Count == 0)
        {
            v.AddChild(Beat(Style.Label("No gear came out of it.", Style.TextItalic, 17, Kit.Dim, false, HorizontalAlignment.Center), cue));
            cue += 0.3;
        }
        else
        {
            // The best six named, one row; the rest as small tiles under them, told together (a dozen
            // Commons named one by one buried the Epic, told one by one were the slow part, and two
            // named rows ran the panel to the screen's edges at 1080).
            var big = finds.Take(PerRow).ToList();
            var rest = finds.Skip(PerRow).ToList();
            int per = PerRow;
            var block = Style.V(Style.Gap4);
            double together = cue + big.Count(f => Rank(f) >= 5) * 0.45;
            bool rung = false;
            for (int i = 0; i < big.Count; i += per)
            {
                var row = Style.H(Style.Gap3);
                row.Alignment = BoxContainer.AlignmentMode.Center;
                foreach (var it in big.Skip(i).Take(per))
                {
                    // The noted (an Epic and up, a chart) one at a time, each with its ring; the others
                    // together after them, with one sound between them.
                    bool noted = Rank(it) >= 5;
                    Action? sound = noted ? () => Sound.Sfx.Loot(true) : rung ? null : () => Sound.Sfx.Loot(false);
                    rung |= !noted;
                    row.AddChild(Beat(Find(it), noted ? cue : together, sound));
                    if (noted) cue += 0.45;
                }
                block.AddChild(row);
            }
            cue = together + (rung ? 0.4 : 0);
            if (rest.Count > 0)
            {
                var flow = new HFlowContainer { MouseFilter = MouseFilterEnum.Ignore, Alignment = FlowContainer.AlignmentMode.Center };
                flow.AddThemeConstantOverride("h_separation", 8);
                flow.AddThemeConstantOverride("v_separation", 8);
                foreach (var it in rest) flow.AddChild(FindTile(it, 52));
                block.AddChild(Beat(flow, cue, () => Sound.Sfx.Loot(false)));
                cue += 0.35;
            }
            v.AddChild(block);
        }
        // What was carried out, and the gold: one line of counted things under the finds.
        if (spoils.Materials.Count > 0 || r.Spilled.Count > 0 || spoils.Gold >= 1)
        {
            v.AddChild(Beat(HaulLine(), cue, () => { if (spoils.Materials.Count > 0) Sound.Sfx.Loot(); if (spoils.Gold >= 1) Sound.Sfx.Gold(); }));
            cue += 0.4;
        }
        // Where the gathering at the end put what she did not walk over (docs/design/LOOT_DESIGN.md §6.2).
        var notes = new List<string>();
        if (spoils.Stored.Count > 0) notes.Add($"Your pack was full: Rook keeps {(spoils.Stored.Count == 1 ? "one of these" : $"{spoils.Stored.Count} of these")} for you.");
        if (r.Gathered is { Broken: > 0 } g) notes.Add($"Broken down: {g.Broken} {(g.Broken == 1 ? "thing" : "things")} for {Items.Several(Crafting.Iron, g.Iron)}{(g.Shards > 0 ? $" and {Items.Several(Crafting.Shard, g.Shards)}" : "")}.");
        if (notes.Count > 0) { v.AddChild(Beat(Style.Label(string.Join("  ", notes), Style.TextItalic, 15, Kit.Dim, true, HorizontalAlignment.Center), cue)); cue += 0.25; }

        // Beat three: the atlas, across the panel, and the mark the map left on it.
        Register(v, "The atlas");
        var atlasLine = MapSpoils.AtlasLine(r.Chart, r.Cleared, r.FirstClear);
        var atlas = Style.V(Style.Gap3, Style.Label(atlasLine, Style.TextItalic, 17, r.FirstClear ? Style.EmberHi : r.Cleared ? Kit.Ink : Kit.Dim, true, HorizontalAlignment.Center));
        var grid = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
        grid.AddChild(AtlasGrid(G.Journey.World, r.Chart, across: true));
        atlas.AddChild(grid);
        v.AddChild(Beat(atlas, cue, r.FirstClear ? Sound.Sfx.Discovery : null));
        int unspent = Atlas.Unspent(G.Journey.World);
        if (unspent > 0) v.AddChild(Beat(Style.Label($"{unspent} point{(unspent == 1 ? "" : "s")} to spend on the atlas, at the Wayfinder's table.", Style.UiBold, 15, Style.EmberHi, true, HorizontalAlignment.Center), cue + 0.3));
        cue += 0.6;

        // Beat four: a line for how it went; the way back has been there all along.
        var after = r.Cleared ? "The Wayfinder will want it for her margins." : $"The chart is spent. {people.BossName} keeps the ground, for now.";
        v.AddChild(Kit.RuleH());
        v.AddChild(Beat(Style.Label(after, Style.TextItalic, 18, Kit.Ink2, true, HorizontalAlignment.Center), cue, Sound.Sfx.Page));
        v.AddChild(OnwardWord("Back to the Waystation", () => G.LeaveMap(r)));
    }

    /// <summary>The head's count: "5 pieces and a chart", "a chart", "12 pieces and 2 charts".</summary>
    static string? Counted(int gear, int charts)
    {
        var parts = new List<string>();
        if (gear > 0) parts.Add($"{gear} piece{(gear == 1 ? "" : "s")}");
        if (charts > 0) parts.Add(charts == 1 ? "a chart" : $"{charts} charts");
        return parts.Count > 0 ? string.Join(" and ", parts) : null;
    }

    /// <summary>A find laid out large: its tile (its card beside it on hover); what it is in small
    /// capitals; then its name in its tier's colour, broken evenly over two lines at most. What it is
    /// sits above the name, so every cell's tile, kind and first line keep one grid however the names run.</summary>
    Control Find(ItemInstance it)
    {
        var tile = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
        tile.AddChild(FindTile(it, Big));
        // (a chart's own rarity names it, as on the Wayfinder's table)
        var ink = it.Chart is { } c ? Style.RarityOf(c.Rarity) : ItemViews.ColourOf(it);
        string kind = it.Chart is { } ch ? $"Tier {ch.Tier} chart" : ItemViews.KindLine(it).Split("  ·  ")[0];
        string name = it.Chart?.Name ?? Inventory.Name(it);
        // Two lines at most: a long name ("Searing Knucklebone Amulet of the First Spark") is set a size smaller.
        int size = 17;
        string lines = Kit.Balance(name, Style.TextBold, size, Cell - 12);
        if (lines.Count(x => x == '\n') > 1) lines = Kit.Balance(name, Style.TextBold, size = 15, Cell - 8);
        var title = Style.Label(lines, Style.TextBold, size, ink, false, HorizontalAlignment.Center);
        // (set close, as a name is: the font's own leading spread a two-line name like two names)
        title.AddThemeConstantOverride("line_spacing", -5);
        var cell = Style.V(2, tile, Style.Gap(6),
            Style.Label(kind.ToUpperInvariant(), Style.UiHeavy, 12, Kit.Dim, false, HorizontalAlignment.Center, false), title);
        cell.CustomMinimumSize = new Vector2(Cell, 0);
        return cell;
    }

    /// <summary>What was carried out and the gold, as one ledger line of counted things (their
    /// pictures and counts, no tiles: they are counted, not pieces); on a fall, what spilled after
    /// it, greyed, behind a fine rule.</summary>
    Control HaulLine()
    {
        var kept = spoils.Materials.Select(kv => Counted(kv.Key, kv.Value)).ToList();
        if (spoils.Gold >= 1) kept.Add(Sum(Glyphs.Icon("coin", 24, Style.GoldHi), $"{spoils.Gold:N0} gold", Style.GoldHi));
        return LedgerLine(kept, r.Spilled);
    }

    /// <summary>The peoples against the tiers, a stone for each pair, lit where its ruler has fallen;
    /// the pair this map was, ringed. The beta shows the first tier and the next, still dark. Across
    /// (the result's page), the peoples head the columns and the tiers run down, so it lies wide and
    /// low under a centred line, its numerals mirrored by an empty column so the stones centre.</summary>
    public static Control AtlasGrid(World.WorldState w, Chart? here = null, bool paper = false, bool across = false)
    {
        // Up to the tier past the best (the next, dark, so the road shows), at most a window's worth.
        int last = Math.Clamp(Math.Max(Atlas.Best(w) + 1, here?.Tier ?? 1) + 1, 2, 16), span = paper ? 8 : 6, first = Math.Max(1, last - span + 1);
        if (across)
        {
            var g = new GridContainer { Columns = MapOffers.Peoples.Length + 2, MouseFilter = MouseFilterEnum.Ignore };
            g.AddThemeConstantOverride("h_separation", 36);
            g.AddThemeConstantOverride("v_separation", 4);
            Control Side() => new Control { CustomMinimumSize = new Vector2(28, 0), MouseFilter = MouseFilterEnum.Ignore };
            g.AddChild(Side());
            foreach (var p in MapOffers.Peoples) g.AddChild(Style.Label(Style.Cap1(p.Name), Style.UiBold, Style.Small, Style.Ink, false, HorizontalAlignment.Center));
            g.AddChild(Side());
            for (int t = first; t <= last; t++)
            {
                var n = Style.Label(Numeral(t), Style.DisplayLight, 14, Style.GoldDim, false, HorizontalAlignment.Right);
                n.VerticalAlignment = VerticalAlignment.Center;
                n.CustomMinimumSize = new Vector2(28, 0);
                g.AddChild(n);
                foreach (var p in MapOffers.Peoples) g.AddChild(new AtlasStone(Atlas.Done(w, p.Id, t), here != null && here.People == p.Id && here.Tier == t));
                g.AddChild(Side());
            }
            return g;
        }
        var grid = new GridContainer { Columns = last - first + 2, MouseFilter = MouseFilterEnum.Ignore };
        grid.AddThemeConstantOverride("h_separation", 10);
        grid.AddThemeConstantOverride("v_separation", 6);
        grid.AddChild(new Control { MouseFilter = MouseFilterEnum.Ignore });
        for (int t = first; t <= last; t++) grid.AddChild(Style.Label(Numeral(t), Style.DisplayLight, 14, paper ? new Color("#5a4126") : Style.GoldDim, false, HorizontalAlignment.Center, !paper));
        foreach (var p in MapOffers.Peoples)
        {
            var name = Style.Label(Style.Cap1(p.Name), Style.UiBold, Style.Small, paper ? new Color("#2e1d10") : Style.Ink, false, HorizontalAlignment.Left, !paper);
            name.CustomMinimumSize = new Vector2(150, 0);
            grid.AddChild(name);
            for (int t = first; t <= last; t++)
                grid.AddChild(new AtlasStone(Atlas.Done(w, p.Id, t), here != null && here.People == p.Id && here.Tier == t, paper));
        }
        return grid;
    }

    static readonly string[] Numerals = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII", "XIV", "XV", "XVI"];
    static string Numeral(int n) => n > 0 && n < Numerals.Length ? Numerals[n] : n.ToString();

    public override bool Key(Act a)
    {
        // The first press tells the rest at once; the next goes back to the Waystation.
        if (a is Act.Confirm or Act.Cancel && !Told) { told = true; return true; }
        if (a == Act.Confirm) { G.LeaveMap(r); return true; }
        return a is not (Act.Up or Act.Down or Act.Left or Act.Right);
    }
}

/// <summary>A pair of the atlas (a people at a tier): a dark stone, or one lit in ember where its
/// ruler has fallen; ringed in gold where the map just run was.</summary>
public partial class AtlasStone : Control
{
    readonly bool lit, here, paper;

    public AtlasStone(bool lit, bool here, bool paper = false)
    {
        this.lit = lit;
        this.here = here;
        this.paper = paper;
        CustomMinimumSize = new Vector2(30, 26);
        MouseFilter = MouseFilterEnum.Ignore;
    }

    public override void _Draw()
    {
        var c = Size / 2;
        Vector2[] Diamond(float r) => new[] { c + new Vector2(0, -r), c + new Vector2(r, 0), c + new Vector2(0, r), c + new Vector2(-r, 0) };
        if (lit)
        {
            DrawCircle(c, 11, Style.Ember with { A = 0.18f });
            DrawColoredPolygon(Diamond(7), Style.Ember);
            DrawColoredPolygon(Diamond(3.5f), Style.EmberHi);
        }
        else
        {
            // (on the atlas's paper, an empty pair is a ring of ink; on the dark page, a dark stone)
            DrawPolyline(Diamond(6).Append(c + new Vector2(0, -6)).ToArray(), paper ? new Color("#5a4126") with { A = 0.7f } : Style.GoldDim with { A = 0.6f }, paper ? 1.4f : 1, true);
        }
        if (here) DrawArc(c, 11, 0, Mathf.Tau, 28, paper ? new Color("#8a2a18") : Style.GoldHi, 1.5f, true);
    }
}
