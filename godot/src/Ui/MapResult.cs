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
/// up; then loot first, a find at a time, the best last (gear by rarity, the charts won, what
/// was carried out, the gold); and the atlas's line, the mark the map left on it.
/// </summary>
public partial class MapResultScreen : TellingScreen
{
    readonly MapResult r;
    readonly MapSpoils spoils;
    public override string Kind => "mapresult";
    public override bool Dismissable => false;

    public MapResultScreen(Game g, MapResult result, MapSpoils spoils) : base(g) { r = result; this.spoils = spoils; }

    /// <summary>
    /// One panel over the world, fitted (it was a page of two half-empty boxes): the verdict between
    /// the chains, the chart and who held it; the map's numbers as a ledger line; then what came out,
    /// the best first and named, so a map's dozen and more finds never bury the Epic under Commons
    /// (crafting's note at 1080), and the rest as tiles together in one beat; the atlas beside it.
    /// The way back is there from the first moment, and the whole telling is done in under six
    /// seconds (it ran past nine).
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

        var (left, right) = Columns(v, 430);
        // Beat two: what came out, the best first.
        left.AddChild(Kit.Head("What came out", $"{spoils.Gear.Count} piece{(spoils.Gear.Count == 1 ? "" : "s")}"));
        // The best first: a Legendary or Storied piece, a set's, an Epic, a ruler's marked thing; then the rest.
        static int Rank(ItemInstance it) => Drops.TierOf(it) switch
        {
            LootTier.Storied => 9, LootTier.Legendary => 8, LootTier.Set => 7, LootTier.Epic => 6, LootTier.Book or LootTier.Chart or LootTier.Quest => 5,
            LootTier.Rare => 3, LootTier.Uncommon => 2, LootTier.Common => 1, _ => 0,
        };
        var gear = spoils.Gear.OrderByDescending(Rank).ThenByDescending(Drops.LevelOf).ToList();
        var noted = gear.Where(it => Rank(it) >= 5).ToList();
        foreach (var it in noted)
        {
            var found = it;
            var col = ItemViews.ColourOf(it);
            var line = Style.H(12, FindTile(it, 48), Style.V(0, Style.Label(Inventory.Name(it), Style.TextBold, 18, col), Style.Label(ItemViews.KindLine(it), Style.Ui, 14, Kit.Dim)));
            foreach (var c in line.GetChildren().OfType<Control>()) c.SizeFlagsVertical = SizeFlags.ShrinkCenter;
            left.AddChild(Beat(line, cue, () => Sound.Sfx.Loot(true)));
            cue += 0.5;
        }
        var rest = gear.Except(noted).ToList();
        if (rest.Count > 0)
        {
            // (the rest together, in one beat: a dozen Commons told one by one was the slow part)
            var flow = new HFlowContainer { MouseFilter = MouseFilterEnum.Ignore };
            flow.AddThemeConstantOverride("h_separation", 8);
            flow.AddThemeConstantOverride("v_separation", 8);
            foreach (var it in rest) flow.AddChild(FindTile(it, 52));
            left.AddChild(Beat(flow, cue, () => Sound.Sfx.Loot(false)));
            cue += 0.45;
        }
        else if (gear.Count == 0) { left.AddChild(Beat(Style.Label("No gear came out of it.", Style.TextItalic, 15, Kit.Dim), cue)); cue += 0.3; }
        // Where the gathering at the end put what she did not walk over (docs/design/LOOT_DESIGN.md §6.2).
        var notes = new List<string>();
        if (spoils.Stored.Count > 0) notes.Add($"Your pack was full: Rook keeps {(spoils.Stored.Count == 1 ? "one of these" : $"{spoils.Stored.Count} of these")} for you.");
        if (r.Gathered is { Broken: > 0 } g) notes.Add($"Broken down: {g.Broken} {(g.Broken == 1 ? "thing" : "things")} for {Items.Several(Crafting.Iron, g.Iron)}{(g.Shards > 0 ? $" and {Items.Several(Crafting.Shard, g.Shards)}" : "")}.");
        if (notes.Count > 0) { left.AddChild(Beat(Style.Label(string.Join("  ", notes), Style.TextItalic, 15, Kit.Dim, true), cue)); cue += 0.25; }
        // What else came out sits under the atlas, so the two columns are of a height.
        if (spoils.Charts.Count > 0 || spoils.Materials.Count > 0 || r.Spilled.Count > 0 || spoils.Gold >= 1)
        {
            right.AddChild(Kit.Head("And besides"));
            foreach (var c in spoils.Charts) { right.AddChild(Beat(ChartFound(c), cue, () => Sound.Sfx.Loot(true))); cue += 0.45; }
            if (spoils.Materials.Count > 0 || r.Spilled.Count > 0) { right.AddChild(Beat(Haul(spoils.Materials, r.Spilled, "Carried out"), cue, () => Sound.Sfx.Loot())); cue += 0.4; }
            if (spoils.Gold >= 1) { right.AddChild(Beat(Line("coin", $"{spoils.Gold:N0} gold", Style.GoldHi), cue, Sound.Sfx.Gold)); cue += 0.35; }
            right.AddChild(Style.Gap(Style.Gap2));
        }

        // Beat three: the atlas, and the mark the map left on it.
        right.AddChild(Kit.Head("The atlas"));
        var atlasLine = MapSpoils.AtlasLine(r.Chart, r.Cleared, r.FirstClear);
        right.AddChild(Beat(Style.Label(atlasLine, Style.TextItalic, 17, r.FirstClear ? Style.EmberHi : r.Cleared ? Kit.Ink : Kit.Dim, true), cue, r.FirstClear ? Sound.Sfx.Discovery : null));
        right.AddChild(Beat(AtlasGrid(G.Journey.World, r.Chart), cue + 0.2));
        int unspent = Atlas.Unspent(G.Journey.World);
        if (unspent > 0) right.AddChild(Beat(Style.Label($"{unspent} point{(unspent == 1 ? "" : "s")} to spend on the atlas, at the Wayfinder's table.", Style.UiBold, 15, Style.EmberHi, true), cue + 0.4));
        cue += 0.6;

        // Beat four: a line for how it went; the way back has been there all along.
        var after = r.Cleared ? "The Wayfinder will want it for her margins." : $"The chart is spent. {people.BossName} keeps the ground, for now.";
        v.AddChild(Kit.RuleH());
        v.AddChild(Beat(Style.Label(after, Style.TextItalic, 18, Kit.Ink2, true, HorizontalAlignment.Center), cue, Sound.Sfx.Page));
        v.AddChild(OnwardWord("Back to the Waystation", () => G.LeaveMap(r)));
    }

    /// <summary>A chart won: the next map in hand, its tier and who holds it, what it is sworn under.</summary>
    static Control ChartFound(ItemInstance it)
    {
        var c = it.Chart!;
        var col = Style.RarityOf(c.Rarity);
        var mods = c.Rolled.Select(m => m.Name).ToList();
        var words = Style.V(1, Style.Label(c.Name, Style.TextBold, Style.Body, col, true),
            Style.Label($"A chart: tier {c.Tier}, held by {MapOffers.People(c.People).Name}", Style.Ui, Style.Small, Style.Ink, true),
            Style.Label(mods.Count > 0 ? string.Join(", ", mods) : "Sworn under nothing", Style.TextItalic, Style.Caption, Style.InkDim, true));
        words.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        var mark = new Medallion(56, "", "map") { Ring = col, Ink = col.Lightened(0.3f), Core = new Color("#20160e") };
        var mc = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
        mc.AddChild(mark);
        return Style.H(12, mc, words);
    }

    /// <summary>The peoples against the tiers, a stone for each pair, lit where its ruler has fallen;
    /// the pair this map was, ringed. The beta shows the first tier and the next, still dark.</summary>
    public static Control AtlasGrid(World.WorldState w, Chart? here = null, bool paper = false)
    {
        // Up to the tier past the best (the next, dark, so the road shows), at most a window's worth.
        int last = Math.Clamp(Math.Max(Atlas.Best(w) + 1, here?.Tier ?? 1) + 1, 2, 16), span = paper ? 8 : 6, first = Math.Max(1, last - span + 1);
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
